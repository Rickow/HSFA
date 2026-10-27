#!<workspace>/venv/bin/python3
"""banc_psp.py : MODE B du banc des coups. Rejoue le MÊME scénario d'entrées sur la PSP (PPSSPP, oracle) et sur un candidat Upper MAX (MAME),
compare image par image (rééchantillonné aux tours visibles de la PSP) et classe chaque coup IDENTIQUE / PROCHE / DIFFÉRENT.
Voir BANC-PSP.md.

Usage (voir banc_psp.sh) :
  banc_psp.sh <candidat> --perso Eagle --ism A [--adv ryu] [--tests palette|proches|speciaux|<fichier.tsv>] [--filtre texte]
  banc_psp.sh <candidat> --liste     # liste les scénarios

Un « test » = (id, nom, script en tours « n:TOUCHES », distance, observation). Le script est converti en entrées PSP image par image
(OU des touches des tours de l'image), puis les touches EFFECTIVES, tour par tour, sont rejouées dans Upper : même entrée des deux côtés.
"""
import argparse, collections, hashlib, json, os, re, struct, subprocess, sys, time

sys.dont_write_bytecode = True
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "psp"))
sys.path.insert(0, os.path.join(ICI, "outils"))
BC = "<workspace>/work/banc_coups"          # banc des coups (lecture seule)
sys.path.insert(0, os.path.join(BC, "outils"))

def _adapter_notation():
    """manips adaptées à la PSP : 4 tours par direction (3 images : la PSP lit les directions par image et 3 tours = 2,25 images), 360° avec les
    diagonales (la PSP ne reconnaît pas toujours F, B, H, D cardinaux) ; le banc des coups d'origine n'est pas modifié (patch en mémoire)"""
    import notation as NT
    NT.PAS = 4
    ancien = NT.motion
    def motion(m, charge=NT.CHARGE):
        m2 = m.strip()
        if m2 == "360°":
            return [(4, [d]) for d in ("F", "DF", "D", "DB", "B", "UB")] + [(1, ["U"])]
        if m2 == "720°":
            return [(3, ["1"])] + [(3, [d]) for d in NT.ROT8 + NT.ROT8[:-1]] + [(4, ["U"])]
        return ancien(m, charge)
    NT.motion = motion
    import palette
    palette.motion = motion


ID_UPPER = {"eagle": 0x26, "maki": 0x27, "yun": 0x2D, "ingrid": 0x2E, "ryu": 0x00, "ken": 0x01, "mika": 0x1A, "akuma": 0x02,
            "chun-li": 0x04, "zangief": 0x10}
NOM_PERSO = {"eagle": "Eagle", "maki": "Maki", "yun": "Yun", "ingrid": "Ingrid", "mika": "R. Mika", "ryu": "Ryu"}
LUA = os.path.join(BC, "lua", "banc_coups.lua")
EXTRA = os.path.join(ICI, "lua", "extra_psp.lua")
OBS_DEFAUT = 150
VERSION_PSP = "psp10"       # à changer quand enreg.py change (invalide les caches PSP)


# ====================================================================================== scénarios
def tests_palette(perso, ism):
    _adapter_notation()
    """palette générique du banc des coups (normaux, lancers, quarts, dragons, demi-cercles, charges, 360°, doubles quarts...)"""
    import palette
    out = []
    for k, (nom, s1, s2, dist, typ, obs) in enumerate(palette.essais(), 1):
        out.append(dict(id="P%d" % k, nom=nom, script=s1, dist=dist, type=typ, obs=int(obs or OBS_DEFAUT)))
    return out


def tests_tableau(jeu, perso_csv, ism):
    _adapter_notation()
    """lignes du tableau des coups (guide) pour le perso : coups de l'Anthology (Mika, natifs...)"""
    import plan as P
    from notation import variantes, NonTestable
    out = []
    for r in P.selection(jeu, perso_csv, ism):
        v = variantes(r, ism)
        if isinstance(v, NonTestable):
            continue
        for k, x in enumerate(v):
            out.append(dict(id="L%d.%d" % (r["_ligne"], k + 1), nom="%s : %s" % (r["nom_du_coup"], x.nom), script=x.seq1, dist=x.dist,
                            type=r["type"], obs=300 if r["type"] in ("super", "lancer", "special") else OBS_DEFAUT))
    return out


def tests_fichier(chemin):
    out = []
    for l in open(chemin, encoding="utf-8"):
        l = l.rstrip("\n")
        if not l or l.startswith("#"):
            continue
        f = l.split("\t")
        out.append(dict(id=f[0], nom=f[1], script=f[2], dist=int(f[3], 16), type=f[4] if len(f) > 4 else "", obs=int(f[5]) if len(f) > 5 and f[5] else OBS_DEFAUT,
                        script2=f[6] if len(f) > 6 else ""))
    return out


def praticable(t):
    """les conditions (G: garde, Y: décollage) et le J2 scripté ne sont pas rejoués (lecture d'états d'un seul côté)"""
    return not re.search(r"(^|\s)\d*[GY]:", t["script"]) and not re.search(r"(^|\s)\d*[GY]:", t.get("script2", ""))


# ====================================================================================== côté PSP
def hashtests(tests):
    return hashlib.md5((VERSION_PSP + json.dumps([(t["id"], t["script"], t.get("script2", ""), t["dist"], t["obs"]) for t in tests])).encode()).hexdigest()[:10]


def total_ticks(t):
    import enreg
    n = sum(k for _, k in enreg.parse_script(t["script"]))
    return n + t["obs"]


def psp_enregistre(perso, adv, ism, tests, dossier_cache, rejouer=False, x1rel=144):
    """renvoie {id: dict(frames=[...], upper_script=str, info)} ; mis en cache (JSON) : ne dépend que de la PSP."""
    import nav_banc as N, enreg, sfa3max as S
    os.makedirs(dossier_cache, exist_ok=True)
    cache = os.path.join(dossier_cache, "psp_%s_%s_%s%s.json" % (perso, adv, ism, "" if x1rel == 144 else "_x%d" % x1rel))
    tout = {}
    if os.path.exists(cache) and not rejouer:
        tout = json.load(open(cache)).get("res", {})
    res = {t["id"]: tout[t["id"]] for t in tests if t["id"] in tout and tout[t["id"]].get("h") == hashtests([t])}
    etat = os.path.join(ICI, "etats", "%s_%s_%s.ppst" % (perso, adv, ism))
    todo = [t for t in tests if t["id"] not in res]
    if not todo:
        return res
    b = N.ouvrir()
    try:
        if not os.path.exists(etat):
            j1, j2 = N.aller_combat(b, perso, adv, ism, "normal")
            b.images(200, entrees=[0] * 200)
            b.etat_sauver(etat)
        else:
            b.etat_charger(etat)
            j1, j2 = S.adresses_joueurs(b)
        for t in todo:
            for essai in range(3):
                try:
                    if os.environ.get("BANC_VERBEUX"):
                        print("  PSP %s %s" % (t["id"], t["nom"]), flush=True)
                    b.etat_charger(etat)
                    nt = total_ticks(t)
                    recs, info = enreg.jouer(b, j1, j2, enreg.parse_script(t["script"]), nt, x1=400.0 + x1rel, dist=t["dist"],
                                             script2=enreg.parse_script(t["script2"]) if t.get("script2") else None)
                    break
                except Exception as ex:           # blocage du débogueur (observé 1 fois en 1 000 essais) : on relance PPSSPP et on rejoue l'essai
                    print("  PSP : essai %s, tentative %d : %s ; relance" % (t["id"], essai + 1, repr(ex)[:120]), flush=True)
                    try:
                        b.arreter()
                    except Exception:
                        pass
                    b = N.ouvrir(etat=etat)
                    j1, j2 = S.adresses_joueurs(b)
            else:
                continue
            eff = enreg.tours_effectifs(recs)
            if len(res) % 10 == 9:                          # sauvegarde intermédiaire du cache
                tout.update(res)
                json.dump(dict(res=tout), open(cache, "w"))
            res[t["id"]] = dict(h=hashtests([t]), upper_script=script_depuis_tours(eff), base=_cf(info["base"]["j1"], info["base"]["j2"]),
                                frames=[dict(img=r["img"], T=r["T"], e0=r["e0"], e1=r["e1"], m=r["masque"], j1=_c(r["j1"]), j2=_c(r["j2"]),
                                             objs=[[o["cle"][0], o["cle"][1], o["hdr"], o["x"], o["y"]] for o in r["objs"]]) for r in recs],
                                pred_faux=info["pred_faux"])
    finally:
        b.arreter()
    tout.update(res)
    json.dump(dict(res=tout), open(cache, "w"))
    return res


def _c(c):
    return dict(etat=c["etat"], x=c["x"], y=c["y"], pas=c["pas"], vie=c["vie"])


def _cf(c1, c2):
    return dict(j1=_c(c1), j2=_c(c2))


def script_depuis_tours(eff):
    """liste de frozenset (touches tenues à chaque tour) -> « n:K+K n:N ... » (jetons du banc des coups)"""
    ordre = "UDFB123456S"
    jet, i = [], 0
    while i < len(eff):
        j = i
        while j < len(eff) and eff[j] == eff[i]:
            j += 1
        ks = sorted(eff[i], key=lambda x: ordre.index(x))
        jet.append("%d:%s" % (j - i, "+".join(ks) if ks else "N"))
        i = j
    if jet and jet[-1].endswith(":N"):
        jet.pop()                       # l'attente finale est l'observation : pas dans la séquence
    return " ".join(jet) or "1:N"


# ====================================================================================== côté Upper
def upper_lance(cand, dossier, perso, adv, ism, tests, psp, scanobj=False, extra_env=()):
    """écrit le plan (touches effectives rejouées) et lance MAME ; renvoie le chemin du journal"""
    os.makedirs(dossier, exist_ok=True)
    plan = os.path.join(dossier, "plan.txt")
    with open(plan, "w") as f:
        for t in tests:
            p = psp.get(t["id"])
            if not p:
                continue
            nobs = t["obs"] + 40
            # « 1:N » en tête : le 1er jeton du banc des coups perd un tour (tt commence à 9, pas 8) ; avec lui, chaque jeton dure exactement n tours
            s2 = ("1:N " + t["script2"]) if t.get("script2") else ""
            f.write("T|%s|%x|90|1:N %s|%s|%d|%s\n" % (t["id"], t["dist"], re.sub(r"\s*\d+:N$", "", p["upper_script"]), s2, nobs, t["nom"].replace("|", "/")))
    env = ["PERSO=%02x" % ID_UPPER[perso], "PERSO2=%02x" % ID_UPPER[adv], "ISM=%s" % ism, "PLAN=" + plan,
           "LUA_EN_PLUS=" + EXTRA, "MAXDIR=" + cand] + (["SCANOBJ=1"] if scanobj else []) + list(extra_env)
    sub = dict(os.environ, MAXDIR=cand)
    subprocess.run([os.path.join(BC, "lance.sh"), dossier, "max", LUA] + env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=sub)
    return os.path.join(dossier, "log.txt")


def lit_upper(log):
    """{id: {'rows': {r: dict}, 'fin':..}} ; rows[r] : champs de la ligne F + y2 (ligne E) + objets Q"""
    R = collections.OrderedDict()
    for l in open(log, errors="replace"):
        t = l.split()
        if not t:
            continue
        if t[0] == "T":
            cur = R.setdefault(t[1], dict(rows={}, exc=None, objs=collections.defaultdict(list)))
        elif t[0] == "F" and t[1] in R:
            r = int(t[2])
            R[t[1]]["rows"][r] = dict(r=r, e1=t[3], e2=t[4], x1=int(t[5], 16), y1=int(t[6], 16), x2=int(t[7], 16), v2=int(t[8], 16), aa=int(t[9], 16),
                                      ptr=t[10], fp=t[11], jauge=int(t[12], 16), tours=int(t[14]), v1=int(t[15], 16))
        elif t[0] == "E" and t[1] in R:
            r = int(t[2])
            if r in R[t[1]]["rows"]:
                R[t[1]]["rows"][r]["y2"] = int(t[3], 16)
        elif t[0] == "Q" and t[1] in R:
            R[t[1]]["objs"][int(t[2])].append(dict(adr=t[3], b0=t[4], typ=t[5], etat=t[6], x=int(t[7], 16), y=int(t[8], 16)))
        elif t[0] == "X" and t[1] in R:
            R[t[1]]["exc"] = t[3]
    return R


# ====================================================================================== comparaison
def hexup(e):
    """état PSP (octets 4..7 en hexa) -> forme Upper : chaque octet ×2"""
    return "".join("%02x" % ((2 * int(e[i:i + 2], 16)) & 0xFF) for i in range(0, 8, 2))


def neutre_up(s):
    return s[0:4] == "0200" and s[4:6] in ("00", "02", "04")


def s16(v):
    return v - 0x10000 if v >= 0x8000 else v


TOL_PX = 2          # PROCHE : écart de position <= 2 px
TOL_TOURS = 1       # PROCHE : état identique à celui d'Upper un tour avant / après
DECALAGE_MAX = 16   # recherche d'un décalage global (tours)


def table_upper(u):
    rows = u["rows"]
    r8 = rows.get(8)
    if r8 is None:
        return None, None
    U = {}
    for r in sorted(rows):
        if r >= 8:
            U[rows[r]["tours"] - r8["tours"]] = rows[r]
    return U, r8


def compare(t, p, u):
    """p = résultat PSP (frames, base) ; u = journal Upper de l'essai. Renvoie dict(verdict, detail, ...)."""
    U, r8 = table_upper(u)
    if U is None:
        return dict(verdict="NC", detail="journal Upper absent ou incomplet")
    emax = max(U)
    def ua(e):
        e = max(0, min(e, emax))
        while e not in U and e > 0:
            e -= 1
        return U.get(e, r8)
    b1, b2 = p["base"]["j1"], p["base"]["j2"]
    ux1, ux2 = r8["x1"], r8["x2"]
    frames = [f for f in p["frames"] if f["e1"] <= emax - DECALAGE_MAX]
    # la PSP en ENTRAINEMENT rend la vie quand rien ne touche pendant ~1 s : on s'arrête à la première hausse de vie
    e_lim = 10 ** 9
    for f0, f1 in zip(frames, frames[1:]):
        if f1["j2"]["vie"] > f0["j2"]["vie"]:          # la vie de J1 est rendue tout de suite (entraînement) : on ne s'en sert pas
            e_lim = f1["e0"]
            break
    frames = [f for f in frames if f["e1"] < e_lim]

    def champs(f, a):
        s1p, s2p = hexup(f["j1"]["etat"]), hexup(f["j2"]["etat"])
        return [("etat J1", s1p, a["e1"]), ("etat J2", s2p, a["e2"]),
                ("dX J1", int(f["j1"]["x"] - b1["x"]), s16(a["x1"] - ux1)), ("Y J1", int(f["j1"]["y"]), s16(a["y1"])),
                ("dX J2", int(f["j2"]["x"] - b2["x"]), s16(a["x2"] - ux2)), ("Y J2", int(f["j2"]["y"]), s16(a.get("y2", 0xFFFF))),
                ("vie J2", f["j2"]["vie"], a["v2"])]

    def ecarts(s, e_from=0):
        """(exact, strict) pour un décalage s : PSP(e) contre Upper(e + s)"""
        ex, st = [], []
        for f in frames:
            e = f["e1"]
            if e < e_from:
                continue
            a = ua(e + s)
            for nom, vp, vu in champs(f, a):
                if vp == vu:
                    continue
                ex.append((e, nom, vp, vu))
                ok = False
                for d in (-TOL_TOURS, TOL_TOURS):
                    vv = [x for x in champs(f, ua(e + s + d)) if x[0] == nom][0][2]
                    if vv == vp:
                        ok = True
                if not ok and not nom.startswith(("etat", "vie")) and abs(vp - vu) <= TOL_PX:
                    ok = True
                if not ok and nom.startswith("etat") and (str(vp).endswith("00") or str(vu).endswith("00")):
                    # état d'initialisation ($7 = 00) vu une image d'un côté seulement : transitoire (comme dans journal.py du banc des coups)
                    ok = str(vp)[:6] == str(vu)[:6]
                if not ok:
                    st.append((e, nom, vp, vu))
        return ex, st

    if t.get("type") in ("special", "super", "lancer"):
        # le coup « sort » s'il atteint un état de spécial / super ($6 = 0e / 10) ou de prise ($5 = 04), ou s'il blesse J2
        def classe(e):
            return e[2:4] == "04" or e[4:6] in ("0e", "10")
        sort_p = any(classe(hexup(f["j1"]["etat"])) for f in frames) or any(f["j2"]["vie"] < 0x90 for f in frames)
        sort_u = any(classe(ua(f["e1"])["e1"]) for f in frames) or any(ua(f["e1"])["v2"] < 0x90 for f in frames)
    else:
        sort_p = any(not neutre_up(hexup(f["j1"]["etat"])) for f in frames)
        sort_u = any(not neutre_up(ua(f["e1"])["e1"]) for f in frames)
    lim = max([f["e1"] for f in frames] or [0])          # même fenêtre de tours des deux côtés pour les dégâts
    deg_p = 0x90 - min([f["j2"]["vie"] for f in frames] or [0x90])
    deg_u = 0x90 - min([ua(e)["v2"] for e in range(0, min(lim, emax) + 1)] or [0x90])
    # dégâts reçus par J1 : la PSP lui rend la vie aussitôt (entraînement) ; on garde la plus basse valeur vue (peut être masquée) : indicatif, jamais décisif
    deg1_p = 0x90 - min([f["j1"]["vie"] for f in frames] or [0x90])
    deg1_u = 0x90 - min([ua(e)["v1"] for e in range(0, min(lim, emax) + 1)] or [0x90])
    if t.get("script2"):
        deg1_p = deg1_u = 0           # J1 touché par un J2 scripté : seuls les états et positions comptent
    ex, st = ecarts(0)
    # écarts de position maximaux (J1, J2) sur la fenêtre comparée, au même tour
    emx = {"dX J1": 0, "dX J2": 0, "Y J1": 0, "Y J2": 0}
    for e, nom, vp, vu in ex:
        if nom in emx:
            emx[nom] = max(emx[nom], abs(vp - vu))
    res = dict(sort_psp=sort_p, sort_upper=sort_u, deg_psp=deg_p, deg_upper=deg_u, deg1_psp=deg1_p, deg1_upper=deg1_u,
               n_exact=len(ex), n_strict=len(st), exc=u.get("exc"), ecart_x1=emx["dX J1"], ecart_x2=emx["dX J2"], ecart_y2=emx["Y J2"], decalage="", e_lim=e_lim if e_lim < 10 ** 8 else "")
    pre = "" if e_lim > 10 ** 8 else " [vie rendue par l'entraînement PSP au tour %d : comparaison arrêtée]" % e_lim
    if u.get("exc"):
        res.update(verdict="DIFFÉRENT", detail="exception Upper pc=%s" % u["exc"])
    elif sort_p != sort_u:
        res.update(verdict="DIFFÉRENT", detail=("le coup sort sur PSP mais PAS dans Upper" if sort_p else "le coup sort dans Upper mais PAS sur PSP (manip à adapter ?)"))
    elif not sort_p and not sort_u:
        res.update(verdict="NC", detail="rien ne sort des deux côtés (manip / condition à revoir)")
    elif not ex and deg_p == deg_u and deg1_p == deg1_u:
        res.update(verdict="IDENTIQUE", detail="%d images comparées%s" % (len(frames), pre))
    elif not st and deg_p == deg_u and deg1_p == deg1_u:
        res.update(verdict="PROCHE", detail="%d écarts de ±%d px / ±%d tour ; 1er %s%s" % (len(ex), TOL_PX, TOL_TOURS, fmt(ex[:1]), pre))
    else:
        premier = (st or ex or [(0, "dégâts", deg_p, deg_u)])[0]
        # décalage global à partir de la 1re divergence ?
        meilleur = None
        for sh in sorted(range(-DECALAGE_MAX, DECALAGE_MAX + 1), key=abs):
            if sh == 0:
                continue
            exs, sts = ecarts(sh, premier[0] - 1)
            if not sts and (meilleur is None):
                meilleur = sh
        degok = deg_p == deg_u and deg1_p == deg1_u
        # mur : la largeur de scène n'est pas la même (PSP 480 px de large, Upper 384) ; une divergence de position d'un joueur près d'un bord n'est pas un défaut de coup
        mur = False
        if premier[1].startswith("dX"):
            fr = [f for f in frames if f["e1"] == premier[0]]
            if fr:
                jj = "j1" if "J1" in premier[1] else "j2"
                rel = fr[0][jj]["x"] - (400.0)
                mur = rel < 110 or rel > 480
        if mur and degok:
            res.update(verdict="MUR", detail="divergence de position près d'un bord de scène (largeur de scène PSP / Upper différente) ; 1re : %s%s" % (fmt([premier]), pre))
        elif meilleur is not None and degok:
            res.update(verdict="DÉCALÉ", decalage=meilleur,
                       detail="même suite mais PSP(tour e) = Upper(tour e%+d) à partir du tour %d (%s)%s" % (meilleur, premier[0], fmt([premier]), pre))
        elif not degok:
            res.update(verdict="DIFFÉRENT", detail="dégâts J2 PSP %d / Upper %d (J1 : %d / %d) ; 1re divergence %s%s" % (deg_p, deg_u, deg1_p, deg1_u, fmt([premier]), pre))
        else:
            res.update(verdict="DIFFÉRENT", detail="%d images divergentes ; 1re : %s%s" % (len(st), fmt([premier]), pre))
    return res


def fmt(l):
    if not l:
        return "-"
    e, nom, vp, vu = l[0]
    return "tour %d %s : PSP %s / Upper %s" % (e, nom, vp, vu)


# ====================================================================================== objets (effets d'impact, projectiles, étincelles)
def pistes_psp(p):
    """pistes d'objets PSP : liste de dict(cle=(pool, idx), typ=octet de type, debut, fin, traj=[(tour, x rel. J1 départ, y, x rel. J2 courant, y rel. J2)]).
    Une piste = un emplacement actif sans interruption, avec le même octet de type ; objets nouveaux ou changés par rapport à l'attente."""
    b1 = p["base"]["j1"]["x"]
    courant, pistes = {}, []
    for i, f in enumerate(p["frames"]):
        vus = set()
        for pool, idx, hdr, x, y in f.get("objs", []):
            k = (pool, idx)
            vus.add(k)
            typ = hdr[4:6]
            t = courant.get(k)
            if t is None or t["typ"] != typ or t["dernier"] != i - 1:
                t = dict(cle=k, typ=typ, traj=[], dernier=i)
                courant[k] = t
                pistes.append(t)
            t["dernier"] = i
            t["traj"].append((f["e1"], int(x - b1), int(y), int(x - f["j2"]["x"]), int(y - f["j2"]["y"])))
    return pistes


def pistes_upper(u, U, r8):
    """pistes Upper (même forme) : objets des zones scannées, absents à la ligne 8 ou changés ; typ = 1er octet du type ($2)"""
    base = {(o["adr"], o["b0"], o["typ"]) for o in u["objs"].get(8, [])}
    tours = {r: rr["tours"] - r8["tours"] for r, rr in u["rows"].items() if r >= 8}
    courant, pistes = {}, []
    for r in sorted(u["objs"]):
        if r < 8:
            continue
        row = u["rows"].get(r)
        if row is None:
            continue
        for o in u["objs"][r]:
            if (o["adr"], o["b0"], o["typ"]) in base:
                continue
            k = o["adr"]
            typ = o["typ"][:2]
            t = courant.get(k)
            if t is None or t["typ"] != typ or t["dernier"] != r - 1:
                t = dict(cle=(k,), typ=typ, traj=[], dernier=r)
                courant[k] = t
                pistes.append(t)
            t["dernier"] = r
            t["traj"].append((tours[r], s16(o["x"] - r8["x1"]), s16(o["y"]), s16(o["x"] - row["x2"]), s16(o["y"]) - s16(row.get("y2", 0))))
    return pistes


def resume_pistes(P):
    out = []
    for t in P:
        v = t["traj"]
        out.append(dict(cle=t["cle"], typ=t["typ"], debut=v[0][0], fin=v[-1][0], x0=v[0][1], y0=v[0][2], xv=v[0][3], yv=v[0][4], n=len(v), traj=v))
    return sorted(out, key=lambda d: d["debut"])


def compare_objets(p, u, tol_x=3, tol_t=3):
    """apparie les pistes PSP et Upper par instant de création (±tol_t tours) puis position relative à la VICTIME (J2) ;
    renvoie (texte, n_psp, n_upper, n_apparies, ecart_max)"""
    U, r8 = table_upper(u)
    if U is None:
        return "", 0, 0, 0, 0, dict(psp=0, upper=0, appariees=0, ecart_pos=0, ecart_t=0)
    A, B = resume_pistes(pistes_psp(p)), resume_pistes(pistes_upper(u, U, r8))
    # la PSP double certains objets (même type, même instant, même position : calque + objet) : on les fusionne
    vus, A2 = set(), []
    for a in A:
        k = (a["typ"], a["debut"], a["xv"] // 2, a["yv"] // 2)
        if k not in vus:
            vus.add(k)
            A2.append(a)
    A = A2
    lim = max([f["e1"] for f in p["frames"]] or [0])
    B = [b for b in B if b["debut"] <= lim]
    # appariement glouton global : coût = écart de temps ×10 + écart de position relative à la victime
    paires = []
    for i, a in enumerate(A):
        for j, b in enumerate(B):
            if abs(b["debut"] - a["debut"]) <= tol_t and (a["typ"] == "04") == (b["typ"] == "04"):
                paires.append((abs(b["debut"] - a["debut"]) * 10 + abs(b["xv"] - a["xv"]) + abs(b["yv"] - a["yv"]), i, j))
    paires.sort()
    appA, appB = {}, {}
    for c, i, j in paires:
        if i not in appA and j not in appB:
            appA[i], appB[j] = j, i
    lignes, ecart, n_ap = [], 0, 0
    evts = []
    for i, a in enumerate(A):
        sig = "pool@%x#%d type %s" % (a["cle"][0], a["cle"][1], a["typ"])
        if i in appA:
            b = B[appA[i]]
            n_ap += 1
            dx, dy = b["xv"] - a["xv"], b["yv"] - a["yv"]
            ecart = max(ecart, abs(dx), abs(dy))
            evts.append((a["debut"], "  PSP %s t%d-%d (vs J2 %+d,%+d) <-> Upper %s %s t%d-%d (vs J2 %+d,%+d) : ecart %+d,%+d%s" % (
                sig, a["debut"], a["fin"], a["xv"], a["yv"], b["cle"][0], b["typ"], b["debut"], b["fin"], b["xv"], b["yv"], dx, dy,
                "   <<<" if abs(dx) > tol_x or abs(dy) > tol_x else "")))
        else:
            evts.append((a["debut"], "  PSP %s t%d-%d (vs J2 %+d,%+d) : SANS EQUIVALENT Upper" % (sig, a["debut"], a["fin"], a["xv"], a["yv"])))
    for j, b in enumerate(B):
        if j not in appB:
            evts.append((b["debut"], "  Upper %s type %s t%d-%d (vs J2 %+d,%+d) : SANS EQUIVALENT PSP" % (b["cle"][0], b["typ"], b["debut"], b["fin"], b["xv"], b["yv"])))
    lignes = [t for _, t in sorted(evts, key=lambda x: x[0])]
    # étincelles d'impact (type 04) : nombre, appariées, écart de position / d'instant
    spA = [i for i, a in enumerate(A) if a["typ"] == "04"]
    spB = [j for j, b in enumerate(B) if b["typ"] == "04"]
    sp_ap = [(A[i], B[appA[i]]) for i in spA if i in appA]
    sp = dict(psp=len(spA), upper=len(spB), appariees=len(sp_ap),
              ecart_pos=max([max(abs(b["xv"] - a["xv"]), abs(b["yv"] - a["yv"])) for a, b in sp_ap] or [0]),
              ecart_t=max([abs(b["debut"] - a["debut"]) for a, b in sp_ap] or [0]))
    return "\n".join(lignes), len(A), len(B), n_ap, ecart, sp


def detail(p, u, plage=(0, 60)):
    """tableau image par image PSP | Upper (même tour) pour lire une divergence"""
    rows = u["rows"]; r8 = rows[8]
    U = {rows[r]["tours"] - r8["tours"]: rows[r] for r in sorted(rows) if r >= 8}
    b1, b2 = p["base"]["j1"], p["base"]["j2"]
    out = ["img tour(PSP e0-e1) touches | PSP: J1 etat dX Y pas | J2 etat dX Y vie || Upper: J1 etat dX Y | J2 etat dX Y vie"]
    for f in p["frames"]:
        if f["e1"] > plage[1]:
            break
        if f["e1"] < plage[0]:
            continue
        a = U.get(f["e1"]) or {}
        def g(k, d=None):
            return a.get(k, d)
        out.append("%3d %3d-%3d | %s %3d %3d %08x | %s %3d %3d %3d || %s %3d %3d | %s %3d %3d %3d%s" % (
            f["img"], f["e0"], f["e1"], hexup(f["j1"]["etat"]), f["j1"]["x"] - b1["x"], f["j1"]["y"], f["j1"]["pas"],
            hexup(f["j2"]["etat"]), f["j2"]["x"] - b2["x"], f["j2"]["y"], f["j2"]["vie"],
            g("e1", "-"), s16(g("x1", 0) - r8["x1"]), g("y1", 0), g("e2", "-"), s16(g("x2", 0) - r8["x2"]), g("y2", -1), g("v2", 0),
            "" if (hexup(f["j1"]["etat"]) == g("e1") and hexup(f["j2"]["etat"]) == g("e2") and int(f["j1"]["x"] - b1["x"]) == s16(g("x1", 0) - r8["x1"])
                   and int(f["j2"]["x"] - b2["x"]) == s16(g("x2", 0) - r8["x2"]) and int(f["j2"]["y"]) == s16(g("y2", 0xFFFF)) and f["j2"]["vie"] == g("v2", 0)) else "   <<"))
    return "\n".join(out)


# ====================================================================================== programme principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidat", help="dossier candidat (copie figée d'une construction MAX, comme banc_coups/max15)")
    ap.add_argument("--perso", default="Eagle")
    ap.add_argument("--adv", default="ryu")
    ap.add_argument("--ism", default="A")
    ap.add_argument("--tests", default="palette", help="palette | tableau | <fichier.tsv>")
    ap.add_argument("--filtre", help="expression régulière sur le nom du coup")
    ap.add_argument("--rejouer-psp", action="store_true")
    ap.add_argument("--recompare", action="store_true", help="réutilise le journal Upper existant (pas de MAME)")
    ap.add_argument("--sans-upper", action="store_true", help="relevés PSP seuls")
    ap.add_argument("--scanobj", action="store_true", help="journal des objets Upper de $FF8C00 à $FFC000")
    ap.add_argument("--x1", type=int, default=144, help="distance de J1 au mur gauche (144 = départ naturel ; 300 = centre, évite les murs)")
    ap.add_argument("--nom-sortie")
    ap.add_argument("--detail", help="id d'un essai : tableau image par image PSP | Upper")
    ap.add_argument("--plage", default="0-60", help="tours affichés par --detail (a-b)")
    a = ap.parse_args()
    cand = os.path.abspath(a.candidat)
    etiquette = os.path.basename(cand.rstrip("/"))
    perso, adv = a.perso.lower(), a.adv.lower()
    if a.tests == "palette":
        tests = tests_palette(perso, a.ism)
    elif a.tests == "tableau":
        tests = tests_tableau("Street Fighter Alpha 3", NOM_PERSO[perso], a.ism)
    else:
        tests = tests_fichier(a.tests)
    if a.filtre:
        tests = [t for t in tests if re.search(a.filtre, t["nom"])]
    sans = [t for t in tests if not praticable(t)]
    tests = [t for t in tests if praticable(t)]
    print("%d essais (%d non rejouables : conditions)" % (len(tests), len(sans)), flush=True)
    nom = a.nom_sortie or "%s_%s_%s" % (perso, adv, a.ism)
    cache = os.path.join(ICI, "essais", "psp")
    t0 = time.time()
    psp = psp_enregistre(perso, adv, a.ism, tests, cache, a.rejouer_psp, a.x1)
    print("PSP : %d essais en %.0f s" % (len(psp), time.time() - t0), flush=True)
    if a.sans_upper:
        return
    rep = os.path.join(ICI, "essais", etiquette, nom)
    t0 = time.time()
    log = os.path.join(rep, "log.txt") if a.recompare else upper_lance(cand, rep, perso, adv, a.ism, tests, psp, a.scanobj, ["X1REL=%d" % a.x1])
    print("Upper : %.0f s" % (time.time() - t0), flush=True)
    U = lit_upper(log)
    sortie = os.path.join(ICI, "resultats", etiquette)
    os.makedirs(sortie, exist_ok=True)
    cnt = collections.Counter()
    spk_all = {}
    with open(os.path.join(sortie, "%s.tsv" % nom), "w") as f, open(os.path.join(sortie, "%s_objets.txt" % nom), "w") as objf:
        f.write("id\tperso\tadv\tism\ttype\tcoup\tverdict\tdetail\tdeg_psp\tdeg_upper\tsort_psp\tsort_upper\tn_exact\tn_strict\tecart_x1\tecart_x2\tecart_y2\tetincelles_psp\tetincelles_upper\tetincelles_ecart_px\tetincelles_ecart_tours\n")
        for t in tests:
            u = U.get(t["id"])
            if u is not None and psp.get(t["id"]):
                try:
                    txt, na, nb, nap, ec, spk = compare_objets(psp[t["id"]], u)
                except Exception as ex:
                    txt, na, nb, nap, ec, spk = "erreur objets %s" % ex, 0, 0, 0, 0, dict(psp=0, upper=0, appariees=0, ecart_pos=0, ecart_t=0)
                objf.write("== %s %s\n  objets PSP %d / Upper %d / apparies %d / ecart max %d px\n  etincelles (type 04) PSP %d / Upper %d / appariees %d / ecart max %d px, %d tours\n%s\n" % (
                    t["id"], t["nom"], na, nb, nap, ec, spk["psp"], spk["upper"], spk["appariees"], spk["ecart_pos"], spk["ecart_t"], txt))
                spk_all[t["id"]] = spk
            if a.detail == t["id"] and u:
                print(t["nom"], "\nscript effectif :", psp[t["id"]]["upper_script"]); print(detail(psp[t["id"]], u, tuple(int(x) for x in a.plage.split("-"))))
            if u is None:
                r = dict(verdict="NC", detail="absent du journal Upper")
            else:
                r = compare(t, psp[t["id"]], u)
            cnt[r["verdict"]] += 1
            f.write("\t".join(str(x) for x in [t["id"], perso, adv, a.ism, t["type"], t["nom"], r["verdict"], r["detail"], r.get("deg_psp", ""),
                                               r.get("deg_upper", ""), r.get("sort_psp", ""), r.get("sort_upper", ""), r.get("n_exact", ""), r.get("n_strict", ""), r.get("ecart_x1", ""), r.get("ecart_x2", ""), r.get("ecart_y2", ""),
                                               spk_all.get(t["id"], {}).get("psp", ""), spk_all.get(t["id"], {}).get("upper", ""), spk_all.get(t["id"], {}).get("ecart_pos", ""), spk_all.get(t["id"], {}).get("ecart_t", "")]) + "\n")
    print(dict(cnt))


if __name__ == "__main__":
    main()
