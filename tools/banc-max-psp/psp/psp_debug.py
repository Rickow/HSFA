#!<workspace>/venv/bin/python3
"""psp_debug.py : PPSSPP comme oracle automatique (SFA3 MAX PSP), scriptable, SANS FENÊTRE.

Bibliothèque standard seule (client WebSocket intégré) : aucun paquet à installer dans le venv.

    from psp_debug import Banc
    with Banc.lancer(ISO, etat="run/etats/combat.ppst") as b:      # processus PPSSPPHeadless sans fenêtre
        r = b.images(120, entrees=plan([("right", 30), ("square", 2)]), sondes=[(adr, 0x40)])
        b.capture("coup.png")                                        # PNG 480x272
        print(b.registres()["pc"])

Voir PPSSPP-BANC.md (API complète, limites). Le binaire est le PPSSPPHeadless du banc (patch minimal
« frame.run / state.* / audio.record », voir patches/). Les images sont exactes et les entrées appliquées
sur le thread d'émulation : deux exécutions identiques donnent les mêmes relevés.
"""
import atexit
import base64
import json
import os
import signal
import socket
import struct
import subprocess
import time

ICI = os.path.dirname(os.path.abspath(__file__))
BINAIRE = os.path.join(ICI, "..", "build", "PPSSPPHeadless")
ISO_SFA3MAX_EU = "<workspace>/sfa3max-psp-widescreen/work/iso/src/EU_RETAIL.iso"   # md5 5f58de7e...

# Boutons PSP (mêmes bits que sceCtrl). « croix » = cross, etc.
BOUTONS = {
    "select": 0x0001, "start": 0x0008, "up": 0x0010, "right": 0x0020, "down": 0x0040, "left": 0x0080,
    "ltrigger": 0x0100, "rtrigger": 0x0200, "triangle": 0x1000, "circle": 0x2000, "cross": 0x4000, "square": 0x8000,
}
ALIAS = {"haut": "up", "bas": "down", "gauche": "left", "droite": "right", "l": "ltrigger", "r": "rtrigger",
         "carre": "square", "rond": "circle", "croix": "cross", "x": "cross", "o": "circle"}


def masque(boutons):
    """'right+square' | ['right','square'] | int | None/'-' -> masque de bits PSP."""
    if boutons is None or boutons == "-" or boutons == "":
        return 0
    if isinstance(boutons, int):
        return boutons
    if isinstance(boutons, str):
        boutons = boutons.replace(",", "+").split("+")
    m = 0
    for b in boutons:
        b = b.strip().lower()
        if b in ("", "-"):
            continue
        b = ALIAS.get(b, b)
        if b not in BOUTONS:
            raise ValueError("bouton inconnu : %r" % b)
        m |= BOUTONS[b]
    return m


def plan(etapes):
    """[(boutons, n_images), ...] -> liste de masques, un par image. Ex. plan([("right", 3), ("-", 2), ("square+down", 1)])"""
    out = []
    for e in etapes:
        b, n = e if isinstance(e, (tuple, list)) else (e, 1)
        out += [masque(b)] * int(n)
    return out


class ErreurBanc(RuntimeError):
    pass


class _WS:
    """Client WebSocket minimal (RFC 6455), protocole debugger.ppsspp.org."""

    def __init__(self, port, hote="127.0.0.1", delai=120):
        self.k = socket.create_connection((hote, port), timeout=delai)
        self.k.settimeout(5)
        self.echeance = None
        cle = base64.b64encode(os.urandom(16)).decode()
        self.k.sendall(("GET /debugger HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
                        "Sec-WebSocket-Protocol: debugger.ppsspp.org\r\n\r\n" % (hote, port, cle)).encode())
        rep = b""
        while b"\r\n\r\n" not in rep:
            x = self.k.recv(4096)
            if not x:
                raise ConnectionError("connexion fermée pendant la poignée de main")
            rep += x
        if b" 101 " not in rep.split(b"\r\n")[0]:
            raise ConnectionError(rep[:200])
        self.tampon = rep.split(b"\r\n\r\n", 1)[1]

    def envoyer(self, texte):
        d = texte.encode()
        m = os.urandom(4)
        n = len(d)
        if n < 126:
            h = bytes([0x81, 0x80 | n])
        elif n < 65536:
            h = bytes([0x81, 0x80 | 126]) + struct.pack(">H", n)
        else:
            h = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", n)
        masq = bytes(b ^ m[i & 3] for i, b in enumerate(d)) if n < 4096 else _xor(d, m)
        self.k.sendall(h + m + masq)

    def _lire(self, n):
        while len(self.tampon) < n:
            if getattr(self, "echeance", None) and time.time() > self.echeance:
                raise TimeoutError("délai global dépassé (banc_max_psp : blocage du débogueur)")
            try:
                x = self.k.recv(1 << 20)
            except socket.timeout:
                continue
            if not x:
                raise ConnectionError("connexion fermée")
            self.tampon += x
        r, self.tampon = self.tampon[:n], self.tampon[n:]
        return r

    def _fragment(self):
        b0, b1 = self._lire(2)
        n = b1 & 0x7F
        if n == 126:
            n = struct.unpack(">H", self._lire(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self._lire(8))[0]
        m = self._lire(4) if b1 & 0x80 else None
        d = self._lire(n)
        if m:
            d = _xor(d, m)
        return bool(b0 & 0x80), b0 & 0x0F, d

    def message(self):
        """(opcode, octets) d'un message complet ; répond aux ping."""
        while True:
            fin, op, d = self._fragment()
            while not fin:
                fin, _, x = self._fragment()
                d += x
            if op == 9:   # ping
                self.k.sendall(bytes([0x8A, 0x80 | len(d)]) + b"\0\0\0\0" + d)
                continue
            return op, d

    def fermer(self):
        try:
            self.k.close()
        except OSError:
            pass


def _xor(d, m):
    # XOR par blocs via entiers : rapide sans numpy
    n = len(d)
    if n == 0:
        return b""
    k = (m * (n // 4 + 1))[:n]
    return (int.from_bytes(d, "little") ^ int.from_bytes(k, "little")).to_bytes(n, "little")


class Banc:
    """Pilote un PPSSPPHeadless (sans fenêtre) par le débogueur WebSocket."""

    # ------------------------------------------------------------------ cycle de vie
    def __init__(self, port, pid=None, journal=None):
        self.port = port
        self.pid = pid
        self.journal = journal
        self.ticket = 0
        self._natif = None          # True : binaire du banc (frame.run) ; False : fork local (runUntilTime)
        self.evenements = []        # événements non sollicités (cpu.stepping, cpu.resume, log...)
        self.ws = _WS(port)
        self._vivant = True
        self.req("version", name="psp_debug.py", version="1")

    @classmethod
    def lancer(cls, iso=ISO_SFA3MAX_EU, port=None, etat=None, cpu="jit", son=False, dossier=None,
               memstick=None, attente=120, binaire=BINAIRE, extra=(), persistant=False):
        """Démarre PPSSPPHeadless SANS FENÊTRE et connecte le client.

        - sans fenêtre : DISPLAY/WAYLAND_DISPLAY retirés, SDL_VIDEODRIVER=offscreen, rendu logiciel
          (--graphics=software), SDL_AUDIODRIVER=dummy ; le processus tourne sous nice -n 19 ;
        - le jeu démarre en PAUSE sur la première instruction (comportement de --debugger) ;
        - etat : fichier d'état (state.save) à charger juste après le démarrage ;
        - memstick : dossier de carte mémoire PROPRE AU BANC (défaut : run/memstick dans ce dossier) ;
        - cpu : 'jit' (défaut, ~4x plus rapide, mêmes résultats mesurés), 'interp', 'ir', 'jit-ir' ; son=True pour audio.record ;
        - persistant=True : le processus survit à ce script (PID dans run/banc_<port>.pid) ; on s'y reconnecte
          avec Banc.connecter(port) et on l'arrête avec Banc.arreter_pid(port).
        """
        dossier = dossier or os.path.join(ICI, "..", "run")
        os.makedirs(dossier, exist_ok=True)
        memstick = memstick or os.path.join(dossier, "memstick")
        os.makedirs(memstick, exist_ok=True)
        if port is None:
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            s.close()
        opt = {"interp": "-i", "jit": "-j", "ir": "--ir", "jit-ir": "--jit-ir"}[cpu]
        cmd = [binaire, "--debugger=%d" % port, "--graphics=software", opt, "--memstick=" + memstick]
        if son:
            cmd.append("--sound")
        cmd += list(extra) + [iso]
        env = {k: v for k, v in os.environ.items()
               if k not in ("DISPLAY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET", "XAUTHORITY")}
        env.update(SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy", HOME=dossier)
        jnl = os.path.join(dossier, "headless_%d.log" % port)
        f = open(jnl, "wb")
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, start_new_session=True,
                             preexec_fn=lambda: os.nice(19), cwd=dossier)
        f.close()
        t0 = time.time()
        b = None
        while time.time() - t0 < attente:
            if p.poll() is not None:
                raise ErreurBanc("PPSSPPHeadless s'est arrêté (voir %s)" % jnl)
            try:
                b = cls(port, pid=p.pid, journal=jnl)
                break
            except (ConnectionError, OSError):
                time.sleep(0.2)
        if b is None:
            os.kill(p.pid, signal.SIGKILL)
            raise ErreurBanc("débogueur injoignable (voir %s)" % jnl)
        b._proc = p
        if persistant:
            with open(os.path.join(dossier, "banc_%d.pid" % port), "w") as fp:
                fp.write("%d\n" % p.pid)
            b._proc = None
        else:
            atexit.register(b.arreter)
        b.attendre_jeu(attente)
        if etat:
            b.etat_charger(etat)
        return b

    @classmethod
    def connecter(cls, port):
        """Se connecte à un PPSSPPHeadless déjà lancé (sans en prendre la propriété)."""
        return cls(port)

    @staticmethod
    def arreter_pid(port, dossier=None):
        """Arrête un banc persistant d'après son fichier PID (SIGTERM puis SIGKILL), jamais par nom."""
        f = os.path.join(dossier or os.path.join(ICI, "..", "run"), "banc_%d.pid" % port)
        pid = int(open(f).read())
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(100):
                time.sleep(0.1)
                os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.remove(f)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.arreter()

    def arreter(self):
        """Arrête le processus qu'on a lancé (par PID, jamais par nom)."""
        if not self._vivant:
            return
        self._vivant = False
        self.ws.fermer()
        p = getattr(self, "_proc", None)
        if p is not None and p.poll() is None:
            try:
                os.kill(p.pid, signal.SIGTERM)
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    os.kill(p.pid, signal.SIGKILL)
                    p.wait(10)
            except ProcessLookupError:
                pass

    # ------------------------------------------------------------------ bas niveau
    def req(self, evenement, **kw):
        """Envoie une requête, renvoie la réponse (dict). Les événements non sollicités sont mis de côté."""
        self.ticket += 1
        t = self.ticket
        kw.update(event=evenement, ticket=t)
        # échéance globale (un débogueur bloqué n'envoie plus rien mais ne ferme pas la connexion) ; frame.run : 60 s + 0,15 s par image
        self.ws.echeance = time.time() + (60 + 0.15 * kw.get("frames", 0) if evenement == "frame.run" else 120)
        self.ws.envoyer(json.dumps(kw))
        while True:
            op, d = self.ws.message()
            if op == 8:
                raise ConnectionError("fermeture du débogueur")
            if op != 1:
                continue
            m = json.loads(d)
            if m.get("ticket") == t:
                if m.get("event") == "error":
                    raise ErreurBanc("%s : %s" % (evenement, m.get("message")))
                return m
            if "ticket" not in m:
                self.evenements.append(m)
                if len(self.evenements) > 5000:
                    del self.evenements[:2500]

    # ------------------------------------------------------------------ jeu / exécution
    def attendre_jeu(self, delai=120):
        t0 = time.time()
        while time.time() - t0 < delai:
            if self.req("game.status").get("game"):
                st = self.req("cpu.status")
                if st.get("stepping"):
                    return st
            time.sleep(0.2)
        raise ErreurBanc("le jeu n'a pas démarré")

    def statut(self):
        return self.req("cpu.status")

    def info(self):
        """Compteur d'images (vblank), cycles, état du coeur."""
        return self.req("banc.info")

    def pause(self, delai=30):
        if self.statut()["stepping"]:
            return
        self.req("cpu.stepping")
        t0 = time.time()
        while not self.statut()["stepping"]:
            if time.time() - t0 > delai:
                raise ErreurBanc("pause impossible")
            time.sleep(0.002)

    def reprendre(self):
        """Reprend en temps libre (non déterministe quant au nombre d'images). Préférer images()."""
        if self.statut()["stepping"]:
            self.req("cpu.resume")

    def en_pause(self):
        return self.statut()["stepping"]

    def images(self, n=1, entrees=None, sondes=None, delai=600):
        """Exécute EXACTEMENT n images (jusqu'au vblank suivant à chaque fois), le jeu étant en pause.

        entrees : liste de masques (voir plan()/masque()) appliqués AVANT chaque image ; si plus courte
                  que n le dernier est conservé ; None = boutons inchangés.
        sondes  : liste de (adresse, taille) lues à la FIN de chaque image, sur le thread d'émulation.
        Renvoie un dict : arret ('frames' ou 'break'), images (faites), vblank (compteur absolu), ticks, pc,
        raison (si arrêt sur point d'arrêt), releves : liste (une entrée par image) de tuples d'octets (une
        valeur par sonde). S'arrête avant la fin si un point d'arrêt se déclenche (arret == 'break').
        """
        sondes = [tuple(s) for s in (sondes or [])]
        if self._natif is None:
            try:
                self.req("banc.info")
                self._natif = True
            except ErreurBanc:
                self._natif = False
        if not self._natif:
            return self._images_fork(n, entrees, sondes)
        kw = dict(frames=int(n), timeout=int(delai))
        if entrees is not None:
            kw["inputs"] = [masque(m) for m in entrees]
        if sondes:
            kw["probes"] = [{"address": a, "size": t} for a, t in sondes]
        r = self.req("frame.run", **kw)
        sb = r["sampleBytes"]
        brut = base64.b64decode(r["samples"]) if sb else b""
        faites = r["framesDone"]
        releves = []
        for i in range(faites if sb else 0):
            blob = brut[i * sb:(i + 1) * sb]
            tup, o = [], 0
            for _, t in sondes:
                tup.append(blob[o:o + t])
                o += t
            releves.append(tuple(tup))
        return {"arret": r["stopped"], "images": faites, "vblank": r["vblank"], "ticks": r["ticks"], "pc": r["pc"],
                "raison": r.get("reason"), "adresse_liee": r.get("relatedAddress"), "releves": releves}

    def _images_fork(self, n, entrees, sondes, us=16683):
        """Repli pour le PPSSPP « fork local » (~/ppsspp-fork), qui n'a que cpu.runUntilTime : une tranche de
        16683 µs par image, boutons posés entre deux tranches, relevés par memory.read. Déterministe (mesuré) mais
        les tranches ne sont PAS alignées sur le vblank : les entrées n'arrivent pas à la même image qu'avec
        frame.run. Pas de state.save/load ni audio.record dans ce mode."""
        releves = []
        for k in range(n):
            if entrees:
                m = masque(entrees[min(k, len(entrees) - 1)])
                self.req("input.buttons.send", buttons={nom: bool(m & v) for nom, v in BOUTONS.items()})
            cible = self.req("cpu.runUntilTime", relativeUs=us)["targetUs"]
            while True:
                st = self.statut()
                if st["stepping"] and st["us"] >= cible - 1:
                    break
                time.sleep(0.0005)
            releves.append(tuple(self.lire(a, t) for a, t in sondes) if sondes else ())
        st = self.statut()
        return {"arret": "frames", "images": n, "vblank": None, "ticks": st.get("ticks"), "pc": st["pc"], "raison": None,
                "adresse_liee": None, "releves": releves if sondes else []}

    def avancer(self, n=1, entrees=None):
        """Raccourci : n images sans relevé."""
        return self.images(n, entrees=entrees)

    def jusqu_arret(self, max_images=3600, entrees=None):
        """Exécute jusqu'au prochain point d'arrêt (exécution ou mémoire) ou max_images images.
        Renvoie le dict d'images() + 'regs' (GPR + pc) si arrêt sur point d'arrêt."""
        r = self.images(max_images, entrees=entrees)
        if r["arret"] == "break":
            r["regs"] = self.registres()
        return r

    def lancer_libre(self):
        """Compat : reprend en libre puis attend un arrêt (point d'arrêt) ; non déterministe en images."""
        self.req("cpu.resume")

    def attendre_arret(self, delai=60):
        t0 = time.time()
        while not self.statut()["stepping"]:
            if time.time() - t0 > delai:
                raise ErreurBanc("pas d'arrêt dans le délai")
            time.sleep(0.005)
        return self.statut()

    # ------------------------------------------------------------------ mémoire / registres
    def lire(self, adresse, taille):
        """Lit la RAM PSP (adresses 0x08800000... ; le jeu doit être en pause)."""
        return base64.b64decode(self.req("memory.read", address=adresse, size=taille)["base64"])

    def lire8(self, a):
        return self.req("memory.read_u8", address=a)["value"]

    def lire16(self, a):
        return self.req("memory.read_u16", address=a)["value"]

    def lire32(self, a):
        return self.req("memory.read_u32", address=a)["value"]

    def ecrire(self, adresse, donnees):
        self.req("memory.write", address=adresse, base64=base64.b64encode(bytes(donnees)).decode())

    def ecrire32(self, a, v):
        self.req("memory.write_u32", address=a, value=v & 0xFFFFFFFF)

    def ecrire16(self, a, v):
        self.req("memory.write_u16", address=a, value=v & 0xFFFF)

    def ecrire8(self, a, v):
        self.req("memory.write_u8", address=a, value=v & 0xFF)

    def registres(self, tout=False):
        """Registres : dict nom -> valeur (GPR + pc, hi, lo ; tout=True ajoute FPU/VFPU sous forme de listes)."""
        r = self.req("cpu.getAllRegs")
        out = {}
        for cat in r["categories"]:
            if cat["id"] == 0 or tout:
                for nom, v in zip(cat["registerNames"], cat["uintValues"]):
                    out[nom if cat["id"] == 0 else "%s:%s" % (cat["name"], nom)] = v
        return out

    def desassembler(self, adresse, n=8):
        r = self.req("memory.disasm", address=adresse, count=n)
        return r.get("lines", r)

    def definir_registre(self, nom, valeur):
        self.req("cpu.setReg", name=nom, value=valeur & 0xFFFFFFFF)

    # ------------------------------------------------------------------ points d'arrêt
    def point_arret_exec(self, adresse, condition=None, actif=True):
        kw = dict(address=adresse, enabled=actif)
        if condition:
            kw["condition"] = condition
        self.req("cpu.breakpoint.add", **kw)

    def retirer_point_arret_exec(self, adresse):
        self.req("cpu.breakpoint.remove", address=adresse)

    def point_arret_mem(self, adresse, taille=4, lecture=False, ecriture=True, changement=False, condition=None):
        kw = dict(address=adresse, size=taille, enabled=True, read=lecture, write=ecriture, change=changement)
        if condition:
            kw["condition"] = condition
        self.req("memory.breakpoint.add", **kw)

    def retirer_point_arret_mem(self, adresse, taille=4):
        self.req("memory.breakpoint.remove", address=adresse, size=taille)

    def retirer_tous_points_arret(self):
        for bp in self.req("cpu.breakpoint.list")["breakpoints"]:
            self.req("cpu.breakpoint.remove", address=bp["address"])
        for bp in self.req("memory.breakpoint.list")["breakpoints"]:
            self.req("memory.breakpoint.remove", address=bp["address"], size=bp["size"])

    def pas(self, n=1):
        """Exécute n instructions (en pause), renvoie pc."""
        for _ in range(n):
            self.req("cpu.stepInto")
            t0 = time.time()
            while True:
                st = self.statut()
                if st["stepping"] and not self._etape_en_cours(st):
                    break
                if time.time() - t0 > 10:
                    raise ErreurBanc("cpu.stepInto sans arrêt")
                time.sleep(0.001)
        return self.statut()["pc"]

    def _etape_en_cours(self, st):
        return False

    # ------------------------------------------------------------------ états, captures, son
    def etat_sauver(self, chemin):
        """Écrit un état de sauvegarde (le jeu doit être en pause). Chemin absolu recommandé."""
        chemin = os.path.abspath(chemin)
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        r = self.req("state.save", path=chemin)
        if not r["ok"]:
            raise ErreurBanc("state.save : %s" % r["message"])
        return chemin

    def etat_charger(self, chemin):
        r = self.req("state.load", path=os.path.abspath(chemin))
        if not r["ok"]:
            raise ErreurBanc("state.load : %s" % r["message"])
        return r

    def capture(self, fichier=None):
        """Capture d'écran PNG 480x272 de l'image courante (le jeu doit être en pause). Renvoie les octets."""
        r = self.req("gpu.buffer.screenshot", type="uri")
        png = base64.b64decode(r["uri"].split(",", 1)[1])
        if fichier:
            os.makedirs(os.path.dirname(os.path.abspath(fichier)), exist_ok=True)
            with open(fichier, "wb") as f:
                f.write(png)
        return png

    def audio_debut(self, fichier_wav):
        """Démarre l'enregistrement WAV 44,1 kHz stéréo de la sortie émulée (lancer avec son=True)."""
        fichier_wav = os.path.abspath(fichier_wav)
        os.makedirs(os.path.dirname(fichier_wav), exist_ok=True)
        self.req("audio.record", path=fichier_wav)

    def audio_fin(self):
        self.req("audio.record", stop=True)

    def rtc_fixer(self, valeur):
        """Fixe l'heure de base du PSP émulé (secondes ; pour la reproductibilité de l'horloge temps réel)."""
        self.req("replay.time.set", value=int(valeur))

    def rtc_lire(self):
        return self.req("replay.time.get")["value"]

    def empreinte_ram(self, regions=((0x08800000, 0x01800000), (0x04000000, 0x00200000)), pas=0x400000):
        """md5 de la RAM utilisateur PSP (24 Mo) et de la VRAM (2 Mo) : empreinte complète de l'état (jeu en pause)."""
        import hashlib
        h = hashlib.md5()
        for debut, taille in regions:
            for o in range(0, taille, pas):
                h.update(self.lire(debut + o, min(pas, taille - o)))
        return h.hexdigest()

    # ------------------------------------------------------------------ trace d'appels (patch banc)
    def trace_demarrer(self, adresses, maxi=4000000):
        """Journalise chaque passage sur ces adresses PSP (entrées de fonctions) pendant les images() suivantes, sans arrêt.
        Chaque enregistrement : image (depuis cet appel), pc, ra (retour = appelant + 8), a0-a3, sp."""
        return self.req("trace.start", addresses=[int(a) for a in adresses], max=maxi)["count"]

    def trace_lire(self, vider=True):
        """Renvoie la liste des enregistrements {image, pc, ra, a0, a1, a2, a3, sp} (ordre d'exécution)."""
        import struct as _s
        r = self.req("trace.get", clear=vider)
        brut = base64.b64decode(r["records"]) if r["count"] else b""
        out = [dict(zip(("image", "pc", "ra", "a0", "a1", "a2", "a3", "sp"), _s.unpack_from("<8I", brut, 32 * i)))
               for i in range(r["count"])]
        if r["dropped"]:
            raise ErreurBanc("trace saturée : %d enregistrements perdus" % r["dropped"])
        return out

    def trace_arreter(self):
        self.req("trace.stop")

    def reinitialiser(self, pause=True):
        self.req("game.reset", **{"break": pause})


if __name__ == "__main__":
    import sys
    iso = sys.argv[1] if len(sys.argv) > 1 else ISO_SFA3MAX_EU
    with Banc.lancer(iso) as b:
        print(b.info())
        print(b.images(10))
        print(len(b.capture("/tmp/essai.png")), "octets PNG")
