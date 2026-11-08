"""(frame_data_max) Côté PSP : relevé TOUR PAR TOUR d'un essai (PPSSPP sans fenêtre, oracle).

La sonde de fin d'image ne voit que 3 tours sur 4 (4 tours pour 3 images). Ici on pose un point d'arrêt d'exécution à l'entrée de la
routine d'entrée des joueurs 0x55650 avec a0 = J2 : elle passe UNE fois par tour de jeu ; on y relève J1, J2 (et la boîte d'attaque
de J1 = octet 1 du jeu de boîtes pointé par J1 + 0x128) et on y écrit le mot d'entrée de J2 (garde scriptée), comme banc_psp.
Le relevé fait au passage du tour e+1 est l'état « après le tour e » (vérifié par outils/psp_fd.py verif : il égale la sonde de fin
d'image quand l'image se termine sur le tour e).
Modules PSP réutilisés en LECTURE : work/banc_max_psp/psp (psp_debug, enreg, sfa3max, nav_banc)."""
import os, struct, sys
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
sys.path.insert(0, "<workspace>/work/banc_max_psp/psp")
import psp_debug as PD, enreg as EN, sfa3max as S, nav_banc as NB

ETATS = os.path.join(ICI, "etats")
PC_J2 = EN.PC_ENTREE_J2
NJ = 0x180          # octets relevés par joueur (états, X, Y, pas, compteur, vie, +0x128, +0x152)


def ouvrir():
    d = os.path.join(ICI, "run", "w%d" % os.getpid())       # dossier PROPRE au processus (deux PPSSPP ne partagent jamais memstick)
    b = NB.ouvrir(etat=NB.ETAT_SELECTION, dossier=d)
    b.images(2, entrees=[0, 0])
    return b


GARDE_DROITE = {"ng": 1, "ag": 4}     # menu CPU OPTIONS > GUARD : AUTO (défaut) -> NO GUARD (1 droite) ... ALL GUARD (4 droites)


def etat_combat(b, perso, adv, ism, garde="ng"):
    """état PSP au combat (ENTRAÎNEMENT, vitesse NORMAL) avec l'option GUARD du mannequin : ng = NO GUARD (essais à vide et au contact),
    ag = ALL GUARD (essais en garde : le mannequin garde haut / bas tout seul)"""
    from psp_debug import plan
    base = os.path.join(ETATS, "%s_%s_%s.ppst" % (perso, adv, ism))
    if not os.path.exists(base):
        b.etat_charger(NB.ETAT_SELECTION)
        NB.aller_combat(b, perso, adv, ism, "normal")
        b.images(200, entrees=[0] * 200)
        b.etat_sauver(base)
    chemin = base[:-5] + "_%s.ppst" % garde
    if not os.path.exists(chemin):
        b.etat_charger(base)
        seq = [("start", 3), ("-", 40), ("down", 3), ("-", 12), ("down", 3), ("-", 12), ("cross", 3), ("-", 40), ("down", 3), ("-", 12)]
        seq += [("right", 3), ("-", 12)] * GARDE_DROITE[garde]
        seq += [("circle", 3), ("-", 40), ("up", 3), ("-", 12), ("up", 3), ("-", 12), ("cross", 3), ("-", 60), ("-", 200)]
        for t in seq:
            b.images(t[1], entrees=plan([t]))
        b.etat_sauver(chemin)
    return chemin


def joueur(blob, b, att=True):
    x, y = struct.unpack_from("<ii", blob, 0x10)
    d = dict(e="".join("%02x" % (2 * v & 0xFF) for v in blob[4:8]), eb=blob[4:8].hex(), x=x / 65536.0, y=y / 65536.0,
             pas=struct.unpack_from("<I", blob, 0x1C)[0], cpt=blob[0x4A],
             vie=struct.unpack_from("<H", blob, 0x70)[0], jb=struct.unpack_from("<I", blob, 0x128)[0])
    return d


def img1(b, n, **kw):
    """b.images avec reprise si le CPU n'est pas en pause (observé juste après un chargement d'état)"""
    try:
        return b.images(n, **kw)
    except PD.ErreurBanc as ex:
        if "paused" not in str(ex):
            raise
        b.pause()
        return b.images(n, **kw)


def neutre_e(e):
    return e[0:4] == "0200" and e[4:6] in ("00", "02", "04") and e[6:8] != "00"


def boite(b, jb):
    """octets 0-2 du jeu de boîtes (octet 1 = attaque) ; 0 si pointeur invalide"""
    if not (0x08800000 <= jb < 0x0A000000):
        return "000000"
    return b.lire(jb, int(os.environ.get("FD_NBX", "3"))).hex()


def jouer(b, j1, j2, script, total, x1=544.0, dist=0x40, script2=None, objets=False, arret=12):
    """Joue script (liste (touches, n)) ; renvoie (tours, images) :
    tours[k] = relevé au passage du tour k+1 dans 0x55650(J2) = état après le tour k (k = 0 : avant le 1er tour joué) ;
    images = sondes de fin d'image (contrôle) avec leurs tours e0..e1."""
    b.ecrire32(j1 + 0x10, int(x1 * 65536)); b.ecrire32(j2 + 0x10, int((x1 + dist) * 65536))
    b.ecrire16(j1 + 0x70, 0x90); b.ecrire16(j2 + 0x70, 0x90)
    sondes = [(j1, NJ), (j2, NJ), (EN.ADR_TOURS, 2)]
    inc, T = [], None
    for _ in range(EN.LEAD):
        r = img1(b, 1, entrees=[0], sondes=sondes)
        t = struct.unpack("<H", r["releves"][0][2])[0]
        if T is not None:
            inc.append((t - T) & 0xFFFF)
        T = t
    T0 = T
    nscript = sum(n for _, n in script) + (sum(n for _, n in script2) if script2 else 0) * 0
    K = EN.tours_par_tick(script, total + 4)
    K2 = EN.tours_par_tick(script2, total + 4) if script2 else [frozenset()] * (total + 4)
    # un passage par joueur et par tour, au DÉBUT du traitement de ce joueur : on relève chaque joueur à son propre passage
    # (état « après le tour k » pour lui) ; J2 reçoit son mot d'entrée à son passage (script2, sinon rien : mannequin du menu)
    b.point_arret_exec(PC_J2, condition="a0 == 0x%x || a0 == 0x%x" % (j1, j2))
    tours, images, e = [], [], 0
    S1, S2 = {}, {}
    droite = True
    try:
        while e < total:
            touches = K[e]
            m = EN.masque_psp(touches, droite)
            hits = 0
            while True:
                r = img1(b, 1, entrees=[m], sondes=sondes)
                if r["arret"] != "break":
                    break
                a0 = b.req("cpu.getReg", name="a0")["uintValue"]
                tc = struct.unpack("<H", b.lire(EN.ADR_TOURS, 2))[0]
                if a0 == j1:
                    if tc not in S1:
                        p1 = joueur(b.lire(j1, NJ), b)
                        p1["bx"] = boite(b, p1["jb"])
                        S1[tc] = p1
                elif a0 == j2:
                    if tc not in S2:
                        p2 = joueur(b.lire(j2, NJ), b)
                        p2["bx"] = boite(b, p2["jb"])
                        p2["rec"] = dict(T=tc, obj=objets_actifs(b)) if objets else dict(T=tc)
                        S2[tc] = p2
                        hits += 1
                    if script2:
                        w = EN.mot_entree(K2[min(len(S2) - 1, len(K2) - 1)], not droite)
                        b.ecrire16(j2 + 0x2F0, w); b.ecrire16(j2 + 0x2FC, w)
                else:
                    raise RuntimeError("arrêt inattendu a0=%x" % a0)
                if hits > 8:
                    raise RuntimeError("trop de tours dans une image")
            rel = r["releves"][0]
            t = struct.unpack("<H", rel[2])[0]
            dd = (t - T) & 0xFFFF
            T = t
            f1, f2 = joueur(rel[0], b), joueur(rel[1], b)
            droite = f1["x"] <= f2["x"]
            images.append(dict(e0=e, e1=e + dd, touches=sorted(touches), j1=f1, j2=f2))
            e += dd
            # arrêt anticipé : script fini et les deux joueurs au neutre (au sol) depuis `arret` tours (le reste n'apporte rien)
            if arret and e > nscript + arret and len(S1) > arret and len(S2) > arret:
                d1 = list(S1.values())[-arret:]; d2 = list(S2.values())[-arret:]
                if all(neutre_e(x["e"]) and x["y"] <= 40 for x in d1 + d2):
                    break
    finally:
        b.retirer_tous_points_arret()
    # tours relevés des deux côtés, dans l'ordre du compteur de tours (un tour sans passage d'un joueur, ex. prise : on reprend le précédent)
    cles = sorted(set(S1) | set(S2), key=lambda t: (t - T0) & 0xFFFF)
    d1 = d2 = None
    for k, tc in enumerate(cles):
        d1 = S1.get(tc, d1); d2 = S2.get(tc, d2)
        if d1 is None or d2 is None:
            continue
        rec = dict(T=tc, k=len(tours), j1=d1, j2={x: v for x, v in d2.items() if x != "rec"})
        tours.append(rec)
    return tours, images


# objets PSP : on cherche, dans les réservoirs, les objets actifs dont le jeu de boîtes (+0x128) a un octet d'attaque non nul
POOLS = [(0x09510F28, 24, 0xC0)]


def objets_actifs(b):
    out = []
    blob = b.lire(EN.POOLS_DEB, EN.POOLS_LONG)
    for base, n in EN.POOLS:
        for i in range(n):
            o = blob[base - EN.POOLS_DEB + i * EN.TAILLE_OBJ: base - EN.POOLS_DEB + (i + 1) * EN.TAILLE_OBJ]
            if o[0]:
                out.append((base, i, o[:4].hex(), struct.unpack_from("<i", o, 0x10)[0] >> 16))
    return out
