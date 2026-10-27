#!<workspace>/venv/bin/python3
"""trace_appels.py : COMPARATEUR AUTOMATIQUE DE TRACES D'APPELS entre la PSP (PPSSPP, vérité) et Upper MAX (MAME, fork cps2f).

Principe : le code MAX traduit garde les adresses PSP dans ses noms (psp_1c5228 = fonction PSP 0x1C5228 du module). On joue le même
coup des deux côtés (même perso, même adversaire, entrées scriptées) en journalisant chaque ENTRÉE de ces fonctions :
  - PSP  : patch du banc (trace.start) : image, pc, ra (appelant = ra - 8), a0-a3 ; points d'arrêt de journal, sans arrêt, déterministe ;
  - MAME : points d'arrêt du débogueur sur les labels psp_ (lua_mame/trace_appels.lua) : image, pc, d0, d1, a6, adresse de retour.
puis on aligne les deux suites de noms (difflib) et on rapporte la PREMIÈRE divergence avec 10 appels de contexte avant et après.

Usage :
  trace_appels.py scenarios                       liste des scénarios
  trace_appels.py compare <scénario> [--banc banc_max17] [--sortie dossier]
  trace_appels.py carte <banc>                    table label -> adresse 68K d'un banc ancien (par alignement avec banc_max17)
Bibliothèque : voir les fonctions trace_psp, trace_mame, aligner, rapport.
"""
import argparse, difflib, json, os, re, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
INTEG = "<workspace>/work/agent_integration_max"
SYMBOLES17 = INTEG + "/prep/symboles.json"          # == banc_max17 (même taille de code 93 614 o)
CODE_ORG, CODE_FIN = 0x3A0000, 0x3B7000
MAX_PSP = (0x1B0000, 0x1D9000)                      # modules MAX sur la PSP (VA de code)
BASE_PSP = 0x08804000
FENETRE = 330                                       # images comparées après le début des entrées
ROLE_PSP = {0x092E3EA0: "J1", 0x092E4338: "J2"}              # structures joueur PSP (table 0x213F88)
ROLE_MAME = {0xFF8400: "J1", 0xFF8800: "J2"}              # structures joueur Upper (A6 = objet courant)
BLOC, TOLERANCE = 8, 3                              # comparaison des autres objets par blocs de BLOC images, écart toléré < TOLERANCE appels par nom
ANCRE = 20                                          # longueur minimale de la plage commune qui sert d'ancre
AVANT = 3                                           # images de repos gardées avant

# ---------------------------------------------------------------------------------------------- scénarios
# Notation : (touches, images) ; AV/AR = avant/arrière, D = bas, U = haut, LP/MP/HP/LK/MK/HK. Les mêmes entrées des deux côtés.
SCENARIOS = {
    "ingrid_super": dict(
        description="Ingrid : marche, super 2xQCB+P (LP) contre Ken ; sur PSP, la touche LP appelle psp_1c5228 / cf5d8",
        perso="ingrid", upper="2e", adversaire="01",
        script=[("AV", 25), ("-", 5), ("D", 3), ("D+AR", 3), ("AR", 3), ("D", 3), ("D+AR", 3), ("AR", 3), ("AR+LP", 3), ("-", 290)]),
    "yun_qcbp": dict(
        description="Yun : QCB+P (onde de choc, projectile $2D) contre Ken ; divergence attendue en psp_1c19e0 avant le correctif",
        perso="yun", upper="2d", adversaire="01",
        script=[("-", 5), ("D", 3), ("D+AR", 3), ("AR+LP", 3), ("-", 300)]),
    "eagle_dp": dict(
        description="Eagle : marche puis DP+P contre Ken (témoin : doit rester sans divergence)",
        perso="eagle", upper="26", adversaire="01",
        script=[("AV", 25), ("-", 5), ("AV", 3), ("D", 3), ("D+AV+LP", 3), ("-", 120)]),
}
PSP_BTN = {"LP": "square", "MP": "triangle", "HP": "rtrigger", "LK": "cross", "MK": "circle", "HK": "ltrigger",
           "AV": "right", "AR": "left", "D": "down", "U": "up"}
MAME_BTN = {"LP": "B1", "MP": "B2", "HP": "B3", "LK": "B4", "MK": "B5", "HK": "B6"}
PER = 360                                           # période de coup.lua : le coup démarre à l'image de combat c = PER


def script_psp(script):
    """-> liste (touches PSP 'a+b', images) utilisable par psp_debug.plan, J1 à gauche face à droite."""
    out = []
    for keys, n in script:
        k = "+".join(PSP_BTN[t] for t in keys.split("+") if t != "-")
        out.append((k or "-", n))
    return out


def script_mame(script):
    """-> chaîne COUP de lua/coup.lua (plages d'images dans la période) ; touches inchangées pour U/D/AV/AR."""
    t, parts = 0, []
    for keys, n in script:
        if keys != "-":
            parts.append("%s:%d-%d" % ("+".join(MAME_BTN.get(x, x) for x in keys.split("+")), t, t + n))
        t += n
    return ",".join(parts)


# ---------------------------------------------------------------------------------------------- symboles
def labels_psp(chemin=SYMBOLES17):
    """{nom: adresse 68K} des labels psp_<hexa> (fonctions PSP) de la construction courante (== banc_max17)."""
    S = json.load(open(chemin))["symboles"]
    return {k: v for k, v in S.items() if re.fullmatch(r"psp_[0-9a-f]+", k)}


def carte_ancien(banc, code_banc, labels17=None, code17=None):
    """Table label -> adresse 68K pour un banc ANCIEN, par alignement du code $3A0000-$3B7000 avec banc_max17 : chaque fonction est
    cherchée (ses 24 premiers octets) dans une fenêtre autour de la position attendue (décalage courant). Renvoie (carte, non_resolus)."""
    labels17 = labels17 or labels_psp()
    code17 = code17 or open(os.path.join(ICI, "run", "code17.bin"), "rb").read()
    tri = sorted(labels17.items(), key=lambda kv: kv[1])
    carte, perdus, dec = {}, [], 0
    for nom, a in tri:
        att = a - CODE_ORG + dec
        trouve = None
        for lg, fen in ((24, 700), (12, 1500), (6, 1500), (4, 600)):        # préfixes de plus en plus courts, plus près de la position attendue
            corps = code17[a - CODE_ORG:a - CODE_ORG + lg]
            best, i = 10 ** 9, code_banc.find(corps, max(0, att - fen), att + fen)
            while i != -1:
                if i % 2 == 0 and abs(i - att) < best:
                    best, trouve = abs(i - att), i
                i = code_banc.find(corps, i + 1, att + fen)
            if trouve is not None:
                break
        if trouve is None:
            perdus.append(nom)
        else:
            carte[nom] = CODE_ORG + trouve
            dec = trouve - (a - CODE_ORG)
    return carte, perdus


# ---------------------------------------------------------------------------------------------- côté PSP
def etat_combat_psp(b, perso, adversaire="ken", dossier=None):
    """Chemin d'un état « combat <perso> contre Ken, round commencé » (le crée au besoin depuis le démarrage)."""
    import scenarios_max as sc, sfa3max
    from psp_debug import plan
    f = os.path.join(dossier or os.path.join(ICI, "etats"), "combat_%s_%s.ppst" % (perso, adversaire))
    return f if os.path.exists(f) else None


def trace_psp(perso, script, labels=None, etat=None, cpu="jit"):
    """Joue `script` sur PPSSPP à partir de l'état de combat de `perso`, trace les entrées des fonctions psp_. Renvoie la liste des
    enregistrements {image, pc(VA), ra(VA), a0-a3} ; `debut` = image du 1er appui."""
    import scenarios_max as sc, sfa3max
    from psp_debug import Banc, plan
    labels = labels or labels_psp()
    vas = sorted(int(k[4:], 16) for k in labels)
    f = etat or os.path.join(ICI, "etats", "combat_%s_ken.ppst" % perso)
    with Banc.lancer(etat=f if os.path.exists(f) else None, cpu=cpu) as b:
        if not os.path.exists(f):
            sc.aller_entrainement(b, perso)
            b.images(480, entrees=plan([("-", 480)]))        # fin de l'annonce FIGHT
            b.etat_sauver(f)
        pl = [("-", 10)] + script_psp(script)
        n = sum(x[1] for x in pl)
        b.trace_demarrer([BASE_PSP + v for v in vas])
        b.images(n, entrees=plan(pl))
        tr = b.trace_lire()
        b.trace_arreter()
    for t in tr:
        t["pc"] -= BASE_PSP
        t["ra"] -= BASE_PSP
    return tr, 10


# ---------------------------------------------------------------------------------------------- côté MAME (Upper MAX)
def trace_mame(banc, perso_upper, adversaire_upper, script, labels, sortie, nf=3500, dump_code=False):
    """Lance UNE instance MAME (nice, -video none, nvram/cfg propres, sans -state) sur `banc` avec des points d'arrêt de journal sur les
    labels. Renvoie (liste d'enregistrements {image, pc, d0, d1, a6, ret}, debut) ; `debut` = image du 1er appui (même repère)."""
    os.makedirs(sortie, exist_ok=True)
    jbp, jfr, jtxt = (os.path.join(sortie, x) for x in ("mame.jbp", "mame.fr", "mame.txt"))
    env = dict(os.environ)
    env.update(BPS=",".join("%x" % a for a in sorted(set(labels.values()))), JBP=jbp, JFR=jfr, JOURNAL="/dev/null",
               EXTRA="-debug -debugger none", LUA=os.path.join(ICI, "lua_mame", "trace_appels.lua"), ORIENT="1",
               PERSO=perso_upper, PERSO2=adversaire_upper, VS="1", MODE="1", NF=str(nf), PER=str(PER), DUREE="900", KO="999999",
               COUP=script_mame(script))
    if dump_code:
        env["DUMPCODE"] = os.path.join(sortie, "code.bin")
    subprocess.run([INTEG + "/lance_max.sh", INTEG + "/" + banc, jtxt], env=env, cwd=INTEG, stdout=subprocess.DEVNULL, check=True)
    if dump_code and nf < 1000:
        return [], 0
    # image du 1er appui : c == PER (coup.lua applique le script quand c % PER == 0, c > 120)
    f0 = None
    for l in open(jfr):
        _, fr, c = l.split()
        if int(c) == PER and f0 is None:
            f0 = int(fr)
    if f0 is None:
        raise RuntimeError("combat non atteint (pas de c == %d) : augmenter nf" % PER)
    rec = []
    for l in open(jbp):
        m = re.match(r"B (\d+) ([0-9a-f]+) f=(\d+) d0=([0-9a-f]+) d1=([0-9a-f]+) a6=([0-9a-f]+) r=([0-9a-f]+)", l)
        if m:
            tc, pc, fr, d0, d1, a6, r = m.groups()
            rec.append(dict(image=int(fr) - f0 + 10, pc=int(pc, 16), d0=int(d0, 16), d1=int(d1, 16), a6=int(a6, 16), ret=int(r, 16)))
    return rec, 10


# ---------------------------------------------------------------------------------------------- normalisation et alignement
def noms_par_adresse(labels):
    return {a: n for n, a in labels.items()}


def contenant(adr68, tri_adr, noms):
    """Nom du label psp_ qui contient une adresse 68K (dernier label <= adresse)."""
    import bisect
    i = bisect.bisect_right(tri_adr, adr68) - 1
    return noms[tri_adr[i]] if i >= 0 and adr68 - tri_adr[i] < 0x2000 else None


def normaliser(rec_psp, rec_mame, labels):
    """Deux suites de dicts {image, nom, appelant, args} sur le MÊME critère : fonction du module MAX (VA dans MAX_PSP) ou appelée depuis
    le module MAX. Fenêtre : de debut-AVANT à debut+FENETRE."""
    import bisect
    va_de = {n: int(n[4:], 16) for n in labels}
    noms = noms_par_adresse(labels)
    tri = sorted(noms)
    dans = lambda va: MAX_PSP[0] <= va < MAX_PSP[1]
    A, B = [], []
    for t in rec_psp:
        appelant = t["ra"] - 8
        if dans(t["pc"]) or dans(appelant):
            A.append(dict(image=t["image"], nom="psp_%x" % t["pc"], module=dans(t["pc"]), role=ROLE_PSP.get(t["a0"], "autre"), appelant="psp_%x" % appelant if dans(appelant) else "%x" % appelant,
                          args="a0=%08x a1=%08x a2=%08x a3=%08x" % (t["a0"], t["a1"], t["a2"], t["a3"])))
    for t in rec_mame:
        nom = noms.get(t["pc"])
        if nom is None:
            continue
        cont = contenant(t["ret"], tri, noms)
        ap = va_de.get(cont, 0) if cont else 0
        if dans(va_de[nom]) or dans(ap):
            B.append(dict(image=t["image"], nom=nom, module=dans(va_de[nom]), role=ROLE_MAME.get(t["a6"] & 0xFFFFFF, "autre"), appelant=cont or "%x" % t["ret"],
                          args="d0=%x d1=%x a6=%x ret=%x" % (t["d0"], t["d1"], t["a6"], t["ret"])))
    return A, B


def fenetre(L, debut, avant=AVANT, longueur=FENETRE):
    return [x for x in L if debut - avant <= x["image"] < debut + longueur]


def ecart(a, b):
    """Écart significatif entre deux comptes d'appels d'un même nom sur un bloc : au moins TOLERANCE d'écart ET rapport > 1,5
    (les objets mis à jour 1 à 2 fois par image, selon la phase, ne comptent pas)."""
    return abs(a - b) >= TOLERANCE and max(a, b) > 1.5 * min(a, b)


def _mod(L, role=None, exclure=None):
    return [x for x in L if x["module"] and (role is None or x["role"] == role) and (exclure is None or x["role"] != exclure)]


def analyser(A, B):
    """Compare A (PSP) et B (Upper). Les objets sont comparés SÉPARÉMENT (l'ordre des objets dans une image diffère entre PSP et Upper) :
    1. suite d'appels du joueur 1 (PSP a0 = structure J1, Upper A6 = $FF8400), alignement difflib ordre strict ;
    2. autres objets (projectiles, effets, J2) : multiensemble de noms par image, comparé avec le décalage d'images trouvé en 1.
    Renvoie un dict : delta, d1 (divergence J1 : (i, j, tag, i2, j2) indices dans A1/B1 ou None), d2 (première image PSP où les
    multiensembles diffèrent ou None), A1, B1."""
    A1, B1 = _mod(A, "J1"), _mod(B, "J1")
    sm = difflib.SequenceMatcher(None, [x["nom"] for x in A1], [x["nom"] for x in B1], autojunk=False)
    ops = sm.get_opcodes()
    ancre = next((n for n, o in enumerate(ops) if o[0] == "equal" and o[2] - o[1] >= ANCRE), None)
    d1, delta = None, 0
    if ancre is not None:
        o = ops[ancre]
        ecarts = sorted(B1[o[3] + k]["image"] - A1[o[1] + k]["image"] for k in range(o[2] - o[1]))
        delta = ecarts[len(ecarts) // 2]
        for tag, i1, i2, j1, j2 in ops[ancre + 1:]:
            if tag != "equal" and i2 < len(A1) and j2 < len(B1):    # écart de fin de fenêtre = artefact
                d1 = (i1, j1, tag, i2, j2)
                break
    # autres objets, par image
    import collections
    ca, cb = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for x in _mod(A, exclure="J1"):
        ca[x["image"]][x["nom"]] += 1
    for x in _mod(B, exclure="J1"):
        cb[x["image"]][x["nom"]] += 1
    d2 = None
    if ancre is not None:
        i0 = A1[ops[ancre][1]]["image"]
        fin = min(max(ca, default=0), max(cb, default=0) - delta) - 4
        for k in range(i0, fin - BLOC, BLOC):
            sa_ = sum((ca[q] for q in range(k, k + BLOC)), collections.Counter())
            sb_ = sum((cb[q + delta] for q in range(k, k + BLOC)), collections.Counter())
            if any(ecart(sa_[n], sb_[n]) for n in set(sa_) | set(sb_)):
                d2 = k
                break
    return dict(delta=delta, d1=d1, d2=d2, A1=A1, B1=B1, ca=ca, cb=cb)


def ecarts_par_nom(A, B, delta):
    """Pour chaque nom de fonction du module (tous objets confondus), comparaison par blocs de BLOC images (Upper décalé de `delta`) :
    renvoie {nom: (première image PSP du bloc en écart, nb d'appels PSP dans ce bloc, nb Upper)} pour les noms en écart significatif."""
    import collections
    ca, cb = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for x in _mod(A):
        ca[x["image"]][x["nom"]] += 1
    for x in _mod(B):
        cb[x["image"] - delta][x["nom"]] += 1
    if not ca:
        return {}
    i0, fin = min(ca), min(max(ca), max(cb, default=0)) - 4
    res = {}
    for k in range(i0, fin - BLOC, BLOC):
        sa_ = sum((ca[q] for q in range(k, k + BLOC)), collections.Counter())
        sb_ = sum((cb[q] for q in range(k, k + BLOC)), collections.Counter())
        for n in set(sa_) | set(sb_):
            if n not in res and ecart(sa_[n], sb_[n]):
                res[n] = (k, sa_[n], sb_[n])
    return res


def section_nouveaux(ec, ec_ref, banc, ref):
    """Texte : écarts par nom absents de la référence (= régressions propres à ce banc), triés par image."""
    L = []
    nouveaux = {n: v for n, v in ec.items() if n not in ec_ref}
    L += ["", "## Écarts propres à %s (absents de la référence %s), par image PSP croissante" % (banc, ref)]
    if not nouveaux:
        L.append("Aucun : même comportement que la référence.")
    else:
        L.append("| image PSP | fonction | appels PSP / Upper sur 8 images |")
        L.append("|---|---|---|")
        for n, (k, a, b) in sorted(nouveaux.items(), key=lambda kv: kv[1][0]):
            L.append("| %d | **%s** | %d / %d |" % (k, n, a, b))
    return L


def _lignes_ctx(S, k, contexte):
    out = ["```"]
    for q in range(max(0, k - contexte), min(len(S), k + contexte + 1)):
        x = S[q]
        out.append("%s image %4d  %-12s <- %-12s %s" % (">" if q == k else " ", x["image"], x["nom"], x["appelant"], x["args"]))
    out.append("```")
    return out


def rapport(A, B, res, contexte=10, titre="", nouveaux=None):
    """Rapport : première divergence (fonction, image, arguments, appelant), contexte de 10 appels avant / après, de chaque côté."""
    L = ["# Rapport de divergence de traces d'appels PSP / Upper MAX %s" % titre, ""]
    nA, nB = len(_mod(A)), len(_mod(B))
    L.append("Appels du module MAX comparés : PSP %d, Upper %d (J1 : %d / %d ; totaux avec aides moteur : %d / %d)." % (
        nA, nB, len(res["A1"]), len(res["B1"]), len(A), len(B)))
    L.append("Décalage d'images Upper - PSP mesuré sur les appels du joueur 1 : %+d." % res["delta"])
    import collections
    ca = collections.Counter(x["nom"] for x in A if x["module"])
    cb = collections.Counter(x["nom"] for x in B if x["module"])
    sa = {k: v for k, v in ca.items() if k not in cb}
    sb = {k: v for k, v in cb.items() if k not in ca}
    L.append("Fonctions du module appelées d'UN SEUL côté sur la fenêtre : PSP seulement %s ; Upper seulement %s." % (
        ", ".join("%s x%d" % kv for kv in sorted(sa.items())) or "aucune", ", ".join("%s x%d" % kv for kv in sorted(sb.items())) or "aucune"))
    d1, d2, delta = res["d1"], res["d2"], res["delta"]
    if nouveaux:
        L += nouveaux
    if d1 is None and d2 is None:
        L += ["", "**Aucune divergence d'ordre ni d'objet** : la suite d'appels du joueur 1 est identique et les autres objets sont appelés les mêmes fois par image."
              + (" Les écarts de comptage par nom listés ci-dessus restent à examiner." if nouveaux else "")]
        return "\n".join(L) + "\n"
    A1, B1 = res["A1"], res["B1"]
    img1 = A1[d1[0]]["image"] if d1 and d1[0] < len(A1) else 10 ** 9
    img2 = d2 if d2 is not None else 10 ** 9
    L.append("")
    L.append("**Première divergence : %s, image PSP %d.**" % ("joueur 1" if img1 <= img2 else "autres objets", min(img1, img2)))
    if d1:
        i, j, tag, i2, j2 = d1
        nature = {"replace": "appel différent", "delete": "appel présent sur la PSP et ABSENT dans Upper", "insert": "appel présent dans Upper et ABSENT sur la PSP"}[tag]
        pa, pb = (A1[i] if i < len(A1) else None), (B1[j] if j < len(B1) else None)
        fmt = lambda x: "image %d, appel de **%s** (appelant %s ; %s)" % (x["image"], x["nom"], x["appelant"], x["args"])
        L += ["", "## Joueur 1 : %s (image PSP %d)" % (nature, img1), "- PSP    : " + (fmt(pa) if pa else "fin de la suite"),
              "- Upper  : " + (fmt(pb) if pb else "fin de la suite")]
        if tag == "replace" and pa and pb:
            L.append("- La PSP appelle `%s` là où Upper appelle `%s` (même appelant ? %s)." % (pa["nom"], pb["nom"], "oui" if pa["appelant"] == pb["appelant"] else "non"))
        L += ["", "### Contexte PSP (joueur 1) : 10 appels avant, 10 après ; > = premier appel divergent"] + _lignes_ctx(A1, min(i, len(A1) - 1), contexte)
        L += ["", "### Contexte Upper MAX (joueur 1)"] + _lignes_ctx(B1, min(j, len(B1) - 1), contexte)
    if d2 is not None:
        k = d2
        L += ["", "## Autres objets (projectiles, effets, J2) : appels différents sur les images PSP %d à %d (Upper %d à %d)" % (k, k + BLOC - 1, k + delta, k + delta + BLOC - 1)]
        diff = []
        sa_ = sum((res["ca"][q] for q in range(k, k + BLOC)), collections.Counter())
        sb_ = sum((res["cb"][q + delta] for q in range(k, k + BLOC)), collections.Counter())
        for nom in sorted(set(sa_) | set(sb_)):
            if ecart(sa_[nom], sb_[nom]):
                diff.append((nom, sa_[nom], sb_[nom]))
        L.append("Écarts de comptage (PSP / Upper) : " + ", ".join("%s %d/%d" % d for d in diff))
        noms = {d[0] for d in diff}
        for cote, S, im in (("PSP", A, k), ("Upper MAX", B, k + delta)):
            sel = [x for x in S if x["module"] and x["role"] != "J1" and x["nom"] in noms and im <= x["image"] < im + BLOC]
            L += ["", "### Appels concernés côté %s, images %d à %d (les 12 premiers)" % (cote, im, im + BLOC - 1), "```"]
            for x in sel[:12]:
                L.append("  image %4d  %-12s <- %-12s %s" % (x["image"], x["nom"], x["appelant"], x["args"]))
            L.append("```")
        # l'image précédente, pour voir qui a créé / retiré l'objet
        L += ["", "Lecture : un nom présent d'un côté et absent (ou nettement moins fréquent) de l'autre sur plusieurs images = objet retiré trop tôt / jamais créé / mis à jour par une autre routine."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------- orchestration
def comparer(nom, banc="banc_max17", sortie=None, nf=3500, labels=None, code_banc=None, ignorer=(), alias=None, connues=True, reference="banc_max17"):
    sc = SCENARIOS[nom]
    sortie = sortie or os.path.join(ICI, "run", "trace_%s_%s" % (nom, banc))
    os.makedirs(sortie, exist_ok=True)
    labels17 = labels_psp()
    lab = labels
    if lab is None:
        if banc == "banc_max17":
            lab = labels17
        else:
            # banc ancien : code des deux bancs relevé par MAME, puis carte par alignement
            cb = os.path.join(ICI, "run", "code_%s.bin" % banc)
            if not os.path.exists(cb):
                trace_mame(banc, sc["upper"], sc["adversaire"], [("-", 1)], {"x": 0x3A0000}, os.path.join(sortie, "dump"), nf=600, dump_code=True)
                os.replace(os.path.join(sortie, "dump", "code.bin"), cb)
            carte, perdus = carte_ancien(banc, open(cb, "rb").read(), labels17)
            print("%s : %d labels retrouvés, %d non résolus" % (banc, len(carte), len(perdus)))
            lab = carte
    rmame, d_mame = trace_mame(banc, sc["upper"], sc["adversaire"], sc["script"], lab, os.path.join(sortie, "mame"), nf=nf)
    rpsp, d_psp = trace_psp(sc["perso"], sc["script"], labels17)
    # la PSP est tracée sur toutes les fonctions du banc de référence, Upper sur celles du banc testé : on restreint la PSP à ce dernier
    noms17 = {a: n for n, a in labels17.items()}
    garde = {int(n[4:], 16) for n in lab}
    rpsp = [t for t in rpsp if t["pc"] in garde]
    A, B = normaliser(rpsp, rmame, lab)
    A, B = fenetre(A, d_psp), fenetre(B, d_mame)
    if connues:
        eq = json.load(open(os.path.join(ICI, "equivalences_connues.json")))
        ignorer = set(ignorer) | set(eq["ignorer"]["noms"])
        alias = dict(eq["alias"]["paires"], **(alias or {}))
    for x in (alias and A or []):
        x["nom"] = alias.get(x["nom"], x["nom"])
    for x in (alias and B or []):
        x["nom"] = alias.get(x["nom"], x["nom"])
    if ignorer:   # fonctions connues pour être traduites autrement (équivalences) : retirées des deux suites
        A = [x for x in A if x["nom"] not in ignorer]
        B = [x for x in B if x["nom"] not in ignorer]
    res = analyser(A, B)
    div = res["d1"] if res["d1"] is not None else res["d2"]
    ec = ecarts_par_nom(A, B, res["delta"])
    nouveaux = None
    fref = os.path.join(ICI, "run", "trace_%s_%s" % (nom, reference), "traces.json")
    if banc != reference and os.path.exists(fref):
        r = json.load(open(fref))
        ec_ref = ecarts_par_nom(r["psp"], r["upper"], analyser(r["psp"], r["upper"])["delta"])
        nouveaux = section_nouveaux(ec, ec_ref, banc, reference)
    elif banc == reference and ec:
        nouveaux = ["", "## Écarts structurels de la référence %s (à expliquer ou à ajouter à equivalences_connues.json)" % banc] + [
            "- image %d : **%s** %d / %d" % (k, n, a, b) for n, (k, a, b) in sorted(ec.items(), key=lambda kv: kv[1][0])]
    txt = rapport(A, B, res, titre="— %s sur %s" % (nom, banc), nouveaux=nouveaux)
    open(os.path.join(sortie, "rapport.md"), "w").write(txt)
    json.dump({"psp": A, "upper": B}, open(os.path.join(sortie, "traces.json"), "w"))
    return txt, div


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["scenarios", "compare"])
    ap.add_argument("scenario", nargs="?")
    ap.add_argument("--banc", default="banc_max17")
    ap.add_argument("--sortie")
    ap.add_argument("--nf", type=int, default=3500)
    ap.add_argument("--reference", default="banc_max17", help="banc de référence (corrigé) dont les écarts sont retirés")
    ap.add_argument("--brut", action="store_true", help="n'applique pas equivalences_connues.json")
    ap.add_argument("--alias", default="", help="équivalences a=b,c=d (le nom a est remplacé par b des deux côtés)")
    ap.add_argument("--ignorer", default="", help="noms psp_xxxxxx séparés par des virgules, retirés des deux suites")
    a = ap.parse_args()
    if a.cmd == "scenarios":
        for k, v in SCENARIOS.items():
            print("%-14s %s" % (k, v["description"]))
    else:
        txt, div = comparer(a.scenario, a.banc, a.sortie, a.nf, ignorer=set(x for x in a.ignorer.split(',') if x),
                         alias=dict(kv.split('=') for kv in a.alias.split(',') if kv), connues=not a.brut, reference=a.reference)
        print(txt)
        sys.exit(0 if div is None else 1)
