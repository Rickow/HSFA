#!/usr/bin/env python3
"""controle_anims.py DONNEES MAME [ORACLE] : contrôle des animations de décor extraites de l'ISO (donnees/sfa1_anims.json,
sfa1_decors.json) contre la chronologie MAME de sfa (mame/anim2.sh -> mame/out/stgXX_chrono.txt, 1 400 images).

  - temps en TICS logiques (le jeu fait 8 tics pour 7 images : lignes « c », 2 passes de boucle par tic) ;
  - objets (lignes « o ») : le cadre courant de chaque objet (pointeur arcade) est rapporté à la table de l'ISO par le
    parcours parallèle des tables arcade (ORACLE = programme sfa déchiffré, adresses seulement) ; contrôle : durée de
    chaque passage complet = durée de l'ISO, cadre suivant = suivant de l'ISO (ou reprise) ;
  - tuiles (classes $14, $2E) : à chaque image, les cases scroll2 du rectangle de l'objet = le bloc de l'ISO du cadre
    courant (code + $D400, attribut) ;
  - palettes (classe $33) : couleurs de la palette s2 14 (12 bits, la luminosité est celle du jeu) = source de l'ISO ;
  - foule de Charlie : registre Y de scroll2 = $300 − Y(ISO), changement tous les « période » tics ;
  - sprites : union (code + $400, palette, blocs) des descripteurs de l'ISO parcourus contre stgXX_obj.txt (sonde.lua).
Sortie : controle/controle_anims.tsv + résumé."""
import sys, os, json, struct, collections
DON, MAME = sys.argv[1], sys.argv[2]
ORA = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../etude_decors/sfa1/roms_dech")
A = json.load(open(os.path.join(DON, "sfa1_anims.json"))); DEC = json.load(open(os.path.join(DON, "sfa1_decors.json")))["decors"]
D = open(os.path.join(ORA, "donnees.bin"), "rb").read()
w = lambda x: struct.unpack_from(">H", D, x)[0]; l = lambda x: struct.unpack_from(">I", D, x)[0]
ARC = {"tuiles_s2": 0x11BCBA, "palettes": 0x444D4, "spr_ryu": 0x10F060, "spr_ken": 0x10F526, "spr_charlie": 0x10F69E,
       "spr_guy": 0x10FC44, "spr_birdie_rose": 0x110292, "spr_adon": 0x10FBDA, "spr_sodom": 0x10FC20}
# pointeur de cadre arcade -> (table, anim, indice) de l'ISO
P2I = {}
for nom, t in A["tables"].items():
    T = ARC[nom]
    for i, sq in t["anims"].items():
        a = T + w(T + 2 * int(i))
        for k, c in enumerate(sq["cadres"]):
            P2I.setdefault(a, (nom, i, k)); f = D[a + 2]; a += t["taille_cadre"]
            if f & 0x80: a = l(a)
lignes = []; bilan = collections.Counter()
def note(stg, quoi, ok, detail):
    r = "OK" if ok else ("NON CONTRÔLÉ" if ok is None else "ÉCART")
    lignes.append("%s\t%s\t%s\t%s" % (stg, quoi, r, detail)); bilan[r] += 1
    print("%s %-34s %-5s %s" % (stg, quoi, r, detail))

# sprites de palette >= 24 présents dans au moins 10 des 13 sondes = communs au jeu (pas des objets de décor)
_cnt = collections.Counter()
for _d in DEC:
    _f = os.path.join(MAME, "out", "stg%02X_obj.txt" % (2 * _d["decor"]))
    if os.path.exists(_f): _cnt.update({(int(v[0], 16), int(v[2], 16), int(v[3]), int(v[4])) for v in (x.split() for x in open(_f))})
COMMUNS = {k for k, n in _cnt.items() if n >= 10}
TOUS = {(c + 0x400) & 0xFFFF for e in A["descripteurs"].values() for c in e["codes"]}
for d in DEC:
    stg = "%02X" % (2 * d["decor"]); fn = os.path.join(MAME, "out", "stg%s_chrono.txt" % stg)
    if not os.path.exists(fn) or not d["objets"]: continue
    O = collections.defaultdict(list); T = {}; PAL = {}; R = []; tic = {}; cum = 0; K = []
    ev = collections.defaultdict(list)
    for x in open(fn):
        v = x.split()
        if v[0] == "c": cum += int(v[2]) // 2; tic[int(v[1])] = cum; K.append(int(v[1]))
        elif v[0] == "o": O[int(v[2])].append((int(v[1]), int(v[4], 16), int(v[5], 16), int(v[7], 16), int(v[8], 16)))
        else: ev[int(v[1])].append(v)
    # 1. chronologie des objets
    for s, L in O.items():
        cl = L[0][1]; vus = 0; ec = []; seq = []
        for j in range(len(L)):
            k, c, ss, p, X = L[j]
            if p not in P2I: continue
            nom, i, kk = P2I[p]
            if seq and seq[-1][1:] == (nom, i, kk): continue        # même cadre (changement d'état seul)
            seq.append((k, nom, i, kk))
        # instant d'un changement vu à l'image k : un tic de ]tic[k-1], tic[k]] (2 tics dans 1 image sur 7) -> intervalle
        lo = lambda k: tic.get(k - 1, tic[k] - 1) + 1
        decision = cl in (0x11, 0x15, 0x16)     # ces gestionnaires rechoisissent l'anim sur le cadre marqué (1 tic)
        for j in range(1, len(seq) - 1):
            k0, nom, i, kk = seq[j]; k1 = seq[j + 1][0]; sq = A["tables"][nom]["anims"][i]; cd = sq["cadres"][kk]
            att = cd["duree"]; nxt = kk + 1 if kk + 1 < len(sq["cadres"]) else sq["reprise"]
            dmin, dmax = lo(k1) - tic[k0], tic[k1] - lo(k0)
            if decision and cd["drap"] & 0x80:
                if not (dmin <= 1 <= dmax): ec.append("décision %s/%s/%d %d-%d tics" % (nom, i, kk, dmin, dmax))
            elif seq[j + 1][1:] != (nom, i, nxt):
                if not decision: ec.append("suite %s/%s/%d->%s" % (nom, i, kk, seq[j + 1][1:]))
            elif cl == 0x15 and kk == 0 and j > 0 and A["tables"][seq[j - 1][1]]["anims"][seq[j - 1][2]]["cadres"][seq[j - 1][3]]["drap"] & 0x80:
                # $15 : décision PUIS pas d'animation dans le même tic -> 1er cadre de la nouvelle anim vu durée − 1
                if not (dmin <= att - 1 <= dmax): ec.append("après décision %s/%s/%d %d-%d≠%d−1" % (nom, i, kk, dmin, dmax, att))
            elif not (dmin <= att <= dmax): ec.append("durée %s/%s/%d %d-%d≠%d" % (nom, i, kk, dmin, dmax, att))
            vus += 1
        # cumul : du 2e au dernier changement d'une même suite ininterrompue, somme des durées de l'ISO = tics mesurés (±1)
        if not decision and len(seq) > 3:
            tot = sum(A["tables"][n]["anims"][i]["cadres"][kk]["duree"] for (_, n, i, kk) in seq[1:-1])
            if not (lo(seq[-1][0]) - tic[seq[1][0]] <= tot <= tic[seq[-1][0]] - lo(seq[1][0])):
                ec.append("cumul %d tics ≠ %d-%d" % (tot, lo(seq[-1][0]) - tic[seq[1][0]], tic[seq[-1][0]] - lo(seq[1][0])))
        if len(seq) == 1:                      # cadre fixe (durée $FFF) : tenu toute la fenêtre
            _, n, i, kk = seq[0]; d0 = A["tables"][n]["anims"][i]["cadres"][kk]["duree"]
            if d0 >= tic[K[-1]] - tic[K[0]]: vus = 1
            else: ec.append("cadre fixe %d tics < fenêtre" % d0)
        anims = sorted({(n, i) for _, n, i, _ in seq})
        if not seq:
            note(stg, "objet $%02X%02X (fente %d)" % (cl, L[0][2], s), None, "sans cadre d'animation (créateur) : NON CONTRÔLÉ"); continue
        note(stg, "objet $%02X%02X (fente %d)" % (cl, L[0][2], s), not ec and vus > 0,
             "%d passages contrôlés, anims %s %s" % (vus, anims, "; ".join(ec[:3])))
    # 2. états tilemap / palettes / registres, image par image
    tm = {}; pal = {}; reg = None; fautes = collections.Counter(); compte = collections.Counter(); runs = []
    cur = {s: None for s in O}; idx = {s: 0 for s in O}
    objs_t = [(s, L) for s, L in O.items() if L[0][1] in (0x14, 0x2E)]
    objs_p = [(s, L) for s, L in O.items() if L[0][1] == 0x33]
    rec = {int(o["routine"][1:], 16): o for o in d["objets"]}
    for k in K:
        for v in ev[k]:
            if v[0] == "t": tm[int(v[2])] = int(v[3], 16)
            elif v[0] == "p": pal[int(v[2])] = int(v[3], 16)
            elif v[0] == "r":
                y = int(v[2], 16)
                if reg is not None: runs.append((k, y))
                reg = y
        for s in O:
            while idx[s] < len(O[s]) and O[s][idx[s]][0] <= k: cur[s] = O[s][idx[s]]; idx[s] += 1
        for s, L in objs_t:
            c = cur[s]
            if not c or c[3] not in P2I: continue
            nom, i, kk = P2I[c[3]]; b = A["blocs_tuiles"][A["tables"][nom]["anims"][i]["cadres"][kk]["ptr"]]
            o = rec[(c[1] << 8) | c[2]]; X = c[4]; bon = None
            for Y in ((o["y"] + 0x200,) if (c[1], i) == (0x2E, "6") else (o["y"],)):   # $2E anim 6 ($190(A5) ≠ 0) : Y + $200
                r0, c0 = ((-Y) >> 4) & 0x3F, (X >> 4) & 0x3F; ok = True
                for cc in range(b["colonnes"]):
                    for r in range(b["lignes"]):
                        q = cc * b["lignes"] + r; row = (r0 + r) & 0x3F; col = (c0 + cc) & 0x3F
                        ti = (row & 0xF) + (col << 4) + ((row & 0x30) << 6)
                        if (tm.get(2 * ti), tm.get(2 * ti + 1)) != ((b["codes"][q] + 0xD400) & 0xFFFF, b["attrs"][q]): ok = False
                if ok: bon = Y; break
            compte["tuiles %d" % s] += 1
            if bon is None: fautes["tuiles %d" % s] += 1
            elif bon != o["y"]: compte["tuiles %d Y+$200" % s] += 1
        for s, L in objs_p:
            c = cur[s]
            if not c or c[3] not in P2I: continue
            nom, i, kk = P2I[c[3]]
            for e in A["palettes"][A["tables"][nom]["anims"][i]["cadres"][kk]["ptr"]]:
                base = (int(e["dest"][1:], 16) - 0x800) // 2
                got = [pal.get(base + j, 0) & 0xFFF for j in range(16)]
                compte["palette %d" % s] += 1
                if got != [x & 0xFFF for x in e["couleurs"]]: fautes["palette %d" % s] += 1
    for s, L in objs_t:
        n = compte["tuiles %d" % s]
        note(stg, "tuiles $%02X%02X" % (L[0][1], L[0][2]), n > 0 and fautes["tuiles %d" % s] == 0,
             "%d images, %d écarts, Y+$200 sur %d" % (n, fautes["tuiles %d" % s], compte["tuiles %d Y+$200" % s]))
    for s, L in objs_p:
        n = compte["palette %d" % s]
        note(stg, "palette $%02X%02X" % (L[0][1], L[0][2]), n > 0 and fautes["palette %d" % s] == 0, "%d images, %d écarts" % (n, fautes["palette %d" % s]))
    if d["gest_s2"]["mode"] == "charlie":
        fo = A["foule_charlie"]; ok = True; nr = 0
        for j in range(1, len(runs)):
            # registre CPS-A vu à l'image k = état logique de l'image k − 1 (recopie des registres à la vblank suivante)
            k1, k0 = runs[j][0] - 1, runs[j - 1][0] - 1
            dmin = tic[k1 - 1] + 1 - tic[k0]; dmax = tic[k1] - tic[k0 - 1] - 1; nr += 1
            att = (-fo["y"][(fo["y"].index((-runs[j - 1][1]) & 0x3FF) + 1) % 4]) & 0x3FF   # registre = −Y (caméra Y 0)
            if not (dmin <= fo["periode"] <= dmax) or runs[j][1] != att:
                if ok: print("  foule : 1er écart image %d : %d-%d tics, Y %03X attendu %03X" % (runs[j][0], dmin, dmax, runs[j][1], att))
                ok = False
        note(stg, "foule (Y de scroll2)", ok and nr > 0, "%d changements, période %d tics, Y %s" % (nr, fo["periode"], fo["y"]))
    # 3. sprites : union des descripteurs parcourus contre la sonde
    fo = os.path.join(MAME, "out", "stg%s_obj.txt" % stg)
    # (table, anim, décalage de palette) : la classe $15 met $C(A6) = $FF -> palette + $D(A6) (= octet $C de l'enregistrement)
    vus = {(o["anim"]["table"], str(i), int(o["brut"][24:26], 16) if o["routine"].startswith("$15") else 0)
           for o in d["objets"] if o["anim"]["table"] and o["anim"]["table"].startswith("spr_") for i in o["anim"]["anims"]}
    if any(o["routine"].startswith("$1E") for o in d["objets"]): vus |= {("spr_charlie", str(i), 0) for i in (5, 6, 7)}
    if vus and os.path.exists(fo):
        iso = set()
        for nom, i, dp in vus:
            for c in A["tables"][nom]["anims"][i]["cadres"]:
                e = A["descripteurs"][c["ptr"]]
                for code, at in zip(e["codes"], e["attrs"]):
                    iso.add(((code + 0x400) & 0xFFFF, (at + dp) & 0x1F, ((at >> 8) & 0xF) + 1, ((at >> 12) & 0xF) + 1))
        mame = {(int(v[0], 16), int(v[2], 16), int(v[3]), int(v[4])) for v in (x.split() for x in open(fo))}
        mame_d = {m for m in mame if m[1] >= 24} - COMMUNS
        hors = {m for m in mame_d - iso if m[0] not in TOUS}     # code absent de TOUTES les tables de décor
        note(stg, "sprites (codes, palettes, blocs)", (mame_d - hors) <= iso,
             "MAME %d / ISO %d ; MAME hors ISO %d ; ISO non vus %d ; sprites pal ≥ 24 étrangers aux tables de décor : %d %s"
             % (len(mame_d - hors), len(iso), len(mame_d - hors - iso), len(iso - mame_d), len(hors),
                " ".join("%04X/p%d" % (m[0], m[1]) for m in sorted(hors))))
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle"), exist_ok=True)
open(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle", "controle_anims.tsv"), "w").write(
    "decor\tcontrole\tresultat\tdetail\n" + "\n".join(lignes) + "\n")
print("BILAN : " + ", ".join("%s %d" % kv for kv in sorted(bilan.items())))
