#!<workspace>/venv/bin/python3
"""(frame_data_max) DONNÉES D'IMAGES des persos MAX : PSP (oracle, SFA3 MAX) contre Upper MAX (copie figée), en TOURS DE JEU.

  fd.py psp <perso> <ism> [--refaire] [--filtre RE]  relevés PSP (cache psp_cache/<perso>_<ism>.json ; ne dépend pas du candidat)
  fd.py upper <candidat> <perso> <ism>               rejoue dans Upper (MAME) les entrées EFFECTIVES de la PSP -> essais/<cand>/<perso>_<ism>/
  fd.py mesure <candidat>                            mesures des deux côtés -> resultats/<cand>/frame_data_<perso>.tsv/.md + ecarts.tsv
Méthode et définitions : RAPPORT.md §1 (et mesure() ci-dessous)."""
import hashlib, json, os, re, subprocess, sys, time
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ICI, "outils"))
sys.path.insert(0, "<workspace>/work/banc_max_psp/psp")
sys.dont_write_bytecode = True
import coups as C

BC = "<workspace>/work/banc_coups"
LUA = os.path.join(BC, "lua", "banc_coups.lua")
FORK = "<workspace>/mame-fork/mame/cps2f"
EMPREINTE = "<workspace>/work/outils/empreinte"
LANCE_EMU = "<workspace>/work/outils/lance_emu"
ID_UPPER = {"eagle": 0x26, "maki": 0x27, "yun": 0x2D, "ingrid": 0x2E}
VERSION = "fd4"          # change => caches PSP invalidés


def essais_du_coup(c):
    return [(c["id"] + e, e) for e in c["essais"]]


def hcoup(c):
    return hashlib.md5((VERSION + json.dumps([c["s"], c["essais"], c["dists"], c["obs"]])).encode()).hexdigest()[:10]


def parse(s):
    import enreg
    return enreg.parse_script(s)


def nb_tours(s):
    return sum(n for _, n in parse(s))


def script_depuis_tours(eff):
    ordre = "UDFB123456S"
    jet, i = [], 0
    while i < len(eff):
        j = i
        while j < len(eff) and eff[j] == eff[i]:
            j += 1
        ks = sorted(eff[i], key=lambda x: ordre.index(x))
        jet.append("%d:%s" % (j - i, "+".join(ks) if ks else "N"))
        i = j
    while jet and jet[-1].endswith(":N"):
        jet.pop()
    return " ".join(jet) or "1:N"


# ============================================================================ PSP
def compact_psp(tours):
    """tour -> [e1, att (octet 1 du jeu de boîtes, hexa), pas1, cpt1, x1, y1, e2, vie2, x2, vie1]"""
    out = []
    for t in tours:
        a, b = t["j1"], t["j2"]
        out.append([a["e"], a["bx"][2:4], a["pas"], a["cpt"], round(a["x"], 2), round(a["y"], 2), b["e"], b["vie"], round(b["x"], 2), a["vie"]])
    return out


def pas_actif(tr, cat):
    m = mesure(tr, cat)
    i = next((i for i in range(m.get("i0", 0), len(tr)) if tr[i][1] not in ("00", "")), None)
    return tr[i][2] if i is not None else None


def contact(tr):
    """J2 a réagi (octet $5 = 2 : touché ou garde) ou perdu de la vie"""
    return any(x[6][2:4] == "02" for x in tr) or min(x[7] for x in tr) < 0x90


def psp(perso, ism, refaire=False, filtre=None):
    import psp_fd as P
    cache = os.path.join(ICI, "psp_cache", "%s_%s.json" % (perso, ism))
    res = json.load(open(cache)) if os.path.exists(cache) and not refaire else {}
    todo = [c for c in C.pour_ism(perso, ism) if (not filtre or re.search(filtre, c["nom"])) and
            any(res.get(tid, {}).get("h") != hcoup(c) for tid, _ in essais_du_coup(c))]
    if not todo:
        return res
    b = P.ouvrir()
    etats = {g: P.etat_combat(b, perso, "ryu", ism, g) for g in ("ng", "ag")}

    def un(c, garde, dist):
        nonlocal b
        for essai in range(3):
            try:
                b.etat_charger(etats[garde]); b.pause()
                j1, j2 = P.S.adresses_joueurs(b)
                tours, images = P.jouer(b, j1, j2, parse(c["s"]), nb_tours(c["s"]) + c["obs"], dist=dist)
                eff = []
                for im in images:
                    eff += [frozenset(im["touches"])] * (im["e1"] - im["e0"])
                return dict(h=hcoup(c), dist=dist, garde=garde, script=script_depuis_tours(eff), tr=compact_psp(tours))
            except Exception as ex:
                print("  PSP %s : tentative %d : %r ; relance" % (c["id"], essai + 1, ex), flush=True)
                try:
                    b.arreter()
                except Exception:
                    pass
                b = P.ouvrir()
        raise RuntimeError("PSP bloquée sur %s" % c["id"])
    try:
        for n, c in enumerate(todo):
            t0 = time.time()
            if "w" in c["essais"]:
                res[c["id"] + "w"] = un(c, "ng", C.LOIN)
            dh = None
            if "h" in c["essais"]:
                ref = pas_actif(res[c["id"] + "w"]["tr"], c["cat"]) if "w" in c["essais"] and c["dists"] is C.NORMAUX_D else None
                repli = None
                for d in c["dists"]:
                    r = un(c, "ng", d)
                    r["contact"] = contact(r["tr"])
                    if r["contact"] and (ref is None or pas_actif(r["tr"], c["cat"]) == ref):
                        break
                    if r["contact"] and repli is None:
                        repli = r
                else:
                    if repli is not None:
                        r = repli
                        r["note"] = "animation différente de celle à vide à toutes les distances"
                res[c["id"] + "h"] = r
                dh = r["dist"]
            if "b" in c["essais"]:
                res[c["id"] + "b"] = un(c, "ag", dh or c["dists"][0])
            print("PSP %s %s %s %-40s %.1f s" % (perso, ism, c["id"], c["nom"], time.time() - t0), flush=True)
            if n % 5 == 4:
                json.dump(res, open(cache, "w"))
    finally:
        json.dump(res, open(cache, "w"))
        b.arreter()
    return res


# ============================================================================ Upper
def upper(cand, perso, ism):
    cache = os.path.join(ICI, "psp_cache", "%s_%s.json" % (perso, ism))
    res = json.load(open(cache))
    nom_c = os.path.basename(os.path.normpath(cand))
    d = os.path.join(ICI, "essais", nom_c, "%s_%s" % (perso, ism))
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, "plan.txt")
    coups = {c["id"]: c for c in C.pour_ism(perso, ism)}
    with open(plan, "w") as f:
        for tid in sorted(res):
            r = res[tid]
            c = coups.get(tid[:-1])
            if not c or (os.environ.get("FD_FILTRE") and not re.search(os.environ["FD_FILTRE"], tid)):
                continue
            s2 = ""
            if tid.endswith("b"):
                eff = parse(r["script"])
                k, press = 0, 0
                for ks, n in eff:
                    if any(x in "123456" for x in ks):
                        press = k
                        break
                    k += n
                # deux postures : « b » debout (arrière), « c » accroupie (bas-arrière) ; la mesure garde celle qui pare comme la PSP
                # (le mannequin ALL GUARD choisit seul : debout contre les coups moyens, accroupi contre les coups bas)
                nobs = len(r["tr"]) - nb_tours(r["script"]) + 40
                for suf, g2 in (("b", "B"), ("c", "D+B")):
                    s2 = ("1:N %d:N %d:%s" % (press, len(r["tr"]), g2)) if press else "1:N %d:%s" % (len(r["tr"]), g2)
                    f.write("T|%s|%x|90|1:N %s|%s|%d|%s\n" % (tid[:-1] + suf, r["dist"], r["script"], s2, nobs, c["nom"].replace("|", "/")))
                continue
            nobs = len(r["tr"]) - nb_tours(r["script"]) + 40
            f.write("T|%s|%x|90|1:N %s|%s|%d|%s\n" % (tid, r["dist"], r["script"], s2, nobs, c["nom"].replace("|", "/")))
    M = os.path.abspath(cand)
    lua_tours = os.path.join(ICI, "lua", "tours.lua")
    # empreinte : (1) ce que la commande MAME charge = la copie demandée (contrôle de la copie contre son MD5_COPIE) ;
    # (2) preuve interne : CRC32 de la ROM programme vue par le 68000 (empreinte.lua, avant le script du banc)
    jeu = [FORK, "sfa3hx", "-rompath", os.path.join(M, "roms_fork")]
    envE = dict(os.environ, BANC_DIR=M + "/", HSFA_EXT=M, ATTENDU_REF=M)
    e = subprocess.run([sys.executable, "-I", EMPREINTE + ".py", "commande", "--sortie", os.path.join(d, "empreinte.txt"), "--"] + jeu,
                       env=envE, cwd="<workspace>/work/mame", stdout=subprocess.PIPE, text=True)
    if e.returncode != 0:
        raise SystemExit("ARRÊT : empreinte de %s différente de l'attendu (code %d) : %s" % (nom_c, e.returncode, e.stdout))
    crc = subprocess.run([sys.executable, "-I", EMPREINTE + ".py", "crc", "--"] + jeu, env=envE, cwd="<workspace>/work/mame",
                         stdout=subprocess.PIPE, text=True, check=True).stdout.split()[-1]
    env = ["PERSO=%02x" % ID_UPPER[perso], "PERSO2=00", "ISM=%s" % ism, "PLAN=" + plan, "MAXDIR=" + M, "DELAI=5000",
           "EMPREINTE_SUITE=" + LUA, "EMPREINTE_CRC=" + crc, "EMPREINTE_LUA_OUT=" + os.path.join(d, "empreinte.txt"),
           "LUA_EN_PLUS=" + lua_tours]
    t0 = time.time()
    # lance_emu (registre commun, places globales, étiquette frame_data) -> lance.sh du banc des coups (MAME sans -state)
    subprocess.run([LANCE_EMU, "--agent", os.environ.get("HSFA_AGENT", "frame_data"), "--generique", "--",
                    os.path.join(BC, "lance.sh"), d, "max", EMPREINTE + ".lua"] + env, check=False, stdout=subprocess.DEVNULL)
    emp = open(os.path.join(d, "empreinte.txt")).read()
    if "EMPREINTE_LUA OK" not in emp:
        raise SystemExit("ARRÊT : preuve interne d'empreinte absente ou fausse pour %s %s %s (%s)" % (nom_c, perso, ism, d))
    print("Upper %s %s %s : %.0f s, %s ; %s" % (nom_c, perso, ism, time.time() - t0, open(os.path.join(d, "log.txt")).readline().strip(),
                                              emp.split("\n")[0][2:40]), flush=True)


MESURE = os.environ.get("FD_MESURE", "tours")     # « tours » (défaut) | « images » (images brutes, ancien mode, pour comparer)
SOURCE = {}                                         # log -> « G » (relevé par tour, lua/tours.lua) | « F-lag » (repli R33) | « F »


def traces_upper(log, mode=None):
    """id -> liste de tours [e1, att, ptr, d1, x1, y1, e2, vie2, x2, vie1, lag] ; + exceptions.
    lag = images de RALENTISSEMENT du 68000 (image sans tour de jeu : $FF851C non écrit) rattachées à cette ligne.
    mode « tours » : lignes G (relevé au début de chaque tour, lua/tours.lua) ; lag = images sans tour entre ce tour et le
      précédent. Journal sans lignes G (essais d'avant le 03/11) : lignes F en sautant les images sans tour (méthode R33 ;
      une prise de vue au milieu d'un tour ralenti peut rester, cf. RAPPORT §1.6).
    mode « images » : lignes F (une par image, fin d'image), ancien mode ; lag = 1 sur l'image sans tour."""
    mode = mode or MESURE
    T, X, F, G = {}, {}, {}, {}
    for l in open(log, errors="replace"):
        t = l.split()
        if not t:
            continue
        if t[0] == "F" and int(t[2]) >= 7:
            fp = t[11]
            y = int(t[6], 16)
            y = y - 0x10000 if y >= 0x8000 else y
            F.setdefault(t[1], []).append((int(t[2]), int(t[14]), [t[3], fp[10:12], t[10], int(t[16], 16), int(t[5], 16), y, t[4],
                                                                    int(t[8], 16), int(t[7], 16), int(t[15], 16)]))
        elif t[0] == "G" and len(t) >= 14 and int(t[2]) >= 7:
            # G id r k e1 e2 x1 y1 x2 vie2 ptr att vie1 d1
            y = int(t[7], 16)
            y = y - 0x10000 if y >= 0x8000 else y
            G.setdefault(t[1], []).append((int(t[2]), [t[4], t[11], t[10], int(t[13], 16), int(t[6], 16), y, t[5], int(t[9], 16),
                                                       int(t[8], 16), int(t[12], 16)]))
        elif t[0] == "X":
            X[t[1]] = t[3]
    for i, fl in F.items():
        # image sans tour : compteur de tours inchangé depuis l'image précédente
        lagimg = [k > 0 and fl[k][1] == fl[k - 1][1] for k in range(len(fl))]
        rimg = {fl[k][0]: lagimg[k] for k in range(len(fl))}
        if mode == "images":
            T[i] = [row + [int(lg)] for (r, _, row), lg in zip(fl, lagimg) if r >= 8]
            SOURCE[log] = "F"
        elif i in G:
            # ligne G émise pendant l'image r+1 (BANC_R = r) ; on ne garde que les images de l'essai (ligne F r+1 présente)
            gl = [(r, row) for r, row in G[i] if r + 1 in rimg]
            out, prev = [], None
            for r, row in gl:
                img = r + 1
                lag = 0 if prev is None else sum(1 for q in range(prev + 1, img) if rimg.get(q))
                prev = img
                if r >= 8:
                    out.append(row + [lag])
            T[i] = out
            SOURCE[log] = "G"
        else:
            out, lag = [], 0
            for (r, _, row), lg in zip(fl, lagimg):
                if lg:
                    lag += 1
                    continue
                if r >= 8:
                    out.append(row + [lag])
                lag = 0
            T[i] = out
            SOURCE[log] = "F-lag"
    return T, X


# ============================================================================ mesure (commune aux deux machines)
def libre(e):
    return e[0:4] == "0200" and e[4:6] in ("00", "02", "04")


def neutre(e):
    """retour au neutre : 1er tour en état libre ($5 = 0, $6 = 0 / 2 / 4), y compris le tour d'initialisation ($7 = 0) : sans cela la garde
    accroupie (Upper) et la garde debout (mannequin PSP) ne reviennent pas par le même état d'initialisation (1 tour d'écart artificiel)"""
    return libre(e)


def neutre2(e):
    """J2 : neutre, ou garde de proximité ($6 = $0C, pose de garde quand J1 attaque près de lui : J2 peut agir)"""
    return e[0:4] == "0200" and e[4:6] in ("00", "02", "04", "0c")


def mesure(tr, cat):
    """tr = liste de tours [e1, att, pas, cpt, x1, y1, e2, vie2, x2, vie1].
    Tours « qui avancent » (J1) : pas ou compteur de durée du pas changés (les tours gelés de l'arrêt sur coup ne comptent pas).
    début i0 = 1er tour hors des états libres (sol) / 1er changement d'état après le décollage (saut) ;
    démarrage = tours qui avancent de i0 à la 1re boîte d'attaque (exclue) ; actifs = tours qui avancent avec boîte d'attaque ;
    récupération = tours qui avancent après la dernière boîte jusqu'au retour au neutre (exclu) ; total = de i0 au neutre.
    retour J2 = 1er tour neutre de J2 après sa 1re réaction ; avantage = retour J2 - retour J1 (tours bruts).
    Neutre = état libre ($5 = 0, $6 = 0 / 2 / 4, J2 aussi $0C garde de proximité), tour d'initialisation compris, TENU 3 tours
    (un état libre fugitif entre deux touches d'un super n'est pas un retour au neutre)."""
    m = {}
    if not tr:
        return m
    n = len(tr)
    av = [i == 0 or tr[i][2] != tr[i - 1][2] or tr[i][3] != tr[i - 1][3] for i in range(n)]
    att = [x[1] not in ("00", "") for x in tr]
    if cat == "saut":
        ia = next((i for i in range(n) if tr[i][5] > 40), None)
        if ia is None:
            return m
        i0 = next((i for i in range(ia + 2, n) if tr[i][0] != tr[i - 1][0] and tr[i][5] > 40), None)
    else:
        i0 = next((i for i in range(n) if not libre(tr[i][0])), None)
    if i0 is None:
        return m
    m["i0"] = i0
    sp = next((i for i in range(i0, n) if tr[i][0][4:6] in ("0e", "10")), None)
    if sp is not None and sp > i0 and cat in ("special", "super"):
        m["pre_special"] = sum(1 for i in range(i0, sp) if av[i])
    fin = next((i for i in range(i0 + 1, n) if all(neutre(tr[j][0]) for j in range(i, min(n, i + 3))) and (cat != "saut" or tr[i][5] <= 40)), None)
    lim = fin if fin is not None else n
    act = [i for i in range(i0, lim) if att[i] and av[i]]
    if act:
        m["demarrage"] = sum(1 for i in range(i0, act[0]) if av[i])
        m["actif"] = len(act)
        # morceaux actifs et trous (en tours qui avancent)
        seg, trous, cur, gap = [], [], 0, 0
        prev = None
        for i in range(act[0], act[-1] + 1):
            if not av[i]:
                continue
            if att[i]:
                if prev is False:
                    trous.append(gap); seg.append(cur); cur = 0
                cur += 1; gap = 0; prev = True
            else:
                gap += 1; prev = False
        seg.append(cur)
        m["morceaux"] = ",".join("%d" % s if k == 0 else "(%d) %d" % (trous[k - 1], s) for k, s in enumerate(seg))
        if fin is not None:
            m["recuperation"] = sum(1 for i in range(act[-1] + 1, fin) if av[i])
    if fin is not None:
        m["total"] = sum(1 for i in range(i0, fin) if av[i])
        m["retour1"] = fin
    m["degats"] = 0x90 - min(x[7] for x in tr)
    m["touches"] = sum(1 for i in range(1, n) if tr[i][7] < tr[i - 1][7])
    j0 = next((i for i in range(n) if tr[i][6][2:4] == "02"), None)
    if j0 is not None:
        m["contact"] = j0 - i0
        j1 = next((i for i in range(j0, n) if all(neutre2(tr[j][6]) for j in range(i, min(n, i + 3)))), None)
        if j1 is not None and fin is not None:
            m["avantage"] = j1 - fin
            m["chute"] = any(x[6][2:6] in ("0202", "0204", "0206") for x in tr[j0:j1]) and m["avantage"] > 30
    m["dx2"] = round(tr[min(n - 1, (j0 if j0 is not None else i0))][8] - tr[0][8], 1)
    # images de ralentissement (Upper) rattachées aux tours du relevé : de i0 (exclu) au dernier retour au neutre (J1 ou J2)
    if len(tr[0]) > 10:
        f2 = n - 1 if fin is None else fin + max(0, m.get("avantage", 0))
        m["ralentis"] = sum(tr[i][10] for i in range(i0 + 1, min(n, f2 + 1)))
    return m


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "psp":
        f = a[a.index("--filtre") + 1] if "--filtre" in a else None
        psp(a[1], a[2], refaire="--refaire" in a, filtre=f)
    elif a[0] == "upper":
        upper(a[1], a[2], a[3])
    elif a[0] == "mesure":
        # fd.py mesure <candidat> [--images] : --images = ancien mode (images brutes), écrit dans resultats/<cand>/images/
        import tableaux
        if "--images" in a:
            MESURE = "images"
        tableaux.tout(a[1], MESURE)
