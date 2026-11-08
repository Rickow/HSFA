#!/usr/bin/env python3
"""controle_anims.py (oracle, local) : contrôle IMAGE PAR IMAGE des animations extraites de l'ISO (donnees/
sfa2_anims.json) contre la chronologie MAME de sfa2u (mame/out_chrono/stgXX_chrono.txt, sonde lua/anim_sfa2.lua,
1 600 images par décor, caméra fixe). Méthode reprise de decors_sfa1/outils/controle_anims.py (copie : sfa1_ref/).
  1. objets (sprites, tuiles, palettes à table) : chaque pointeur de cadre de MAME est rapporté au cadre de l'ISO
     (même table, même animation, même rang) ; pour chaque passage COMPLET (entre deux changements) : durée observée
     (images) = durée ISO, et cadre suivant = successeur ISO (reprise comprise). Passages coupés par le gestionnaire
     (décision, pas manuel) : comptés à part.
  2. tuiles : à chaque image, les cases de tilemap du rectangle de l'objet / du canal (adresses calculées comme le
     moteur $18EDE / $18F3C / $18F9A) = bloc ISO du cadre courant (code VRAM, attribut) ;
     canaux sans objet ($6F462) : le contenu doit être un cadre de l'ISO et la suite des cadres doit suivre l'ISO.
  3. palettes : à chaque image, les couleurs (12 bits) de chaque destination = entrée ISO du cadre courant.
  4. rowscroll de Gen : chaque image = 24 paires de lignes tirées de la table de sinus de l'ISO, phase −$10 / image.
Écrit controle/controle_anims.tsv. Usage : controle_anims.py [donnees] [STG …]"""
import os, sys, json, collections
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
import arcade_anims as AA, analyse_chrono as AC, anims_observees as AO
DON = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else os.path.join(os.path.dirname(ICI), "donnees")
STGS = [x for x in sys.argv[1:] if not os.path.isdir(x)] or ["%02X" % s for s in range(0, 0x24, 2)]
A = json.load(open(os.path.join(DON, "sfa2_anims.json")))
CARTE = json.load(open(os.path.join(ICI, "carte_anims_ro2.json")))
TAB = {t["arcade"]: t for t in A["tables"].values()}

# ---- arcade -> ISO : cadre d'arcade -> (table ISO, anim, rang) ----
A2I = {}; A2M = collections.defaultdict(list)
RYTHME = {"A4A": 2}      # $6DC12 : le pas n'a lieu qu'une image sur deux (parité de $FF80B4 + $FF80B5)
for ra, t in TAB.items():
    r = int(ra[1:], 16); fs = AA.FS[t["moteur"]]
    for i, an in t["anims"].items():
        s, _ = AA.walk(r, int(i), fs)
        for k, fr in enumerate(s[:len(an["cadres"])]):
            A2I.setdefault((ra, fr[0]), (i, k)); A2M[(ra, fr[0])].append((i, k))
LISTES = {}
for la, l_ in A["listes_palette"].items():
    a = int(l_["arcade"][1:], 16); x = a
    for k, c in enumerate(l_["cadres"]):
        LISTES[(l_["arcade"], x)] = k; f = AA.D[x + 2]
        x = (AA.l(x + 8) & 0xFFFFFF) if f & 0x80 else x + 8

def suivant(an, k):
    n = len(an["cadres"])
    if an["cadres"][k]["drapeaux"] & 0x80 or k + 1 >= n:
        fin = an["fin"]
        return fin[1] if fin[0] == "boucle" else None
    return k + 1

# ---- adresses de tilemap (copie des boucles du moteur) ----
def cases(plan, x, y, nl, nc):
    """octets (relatifs à la base de la tilemap) des paires (code, attr), colonne par colonne"""
    out = []
    if plan == 2:
        d1 = (-y) & 0xFFFF; a2 = (((x & 0x3F0) << 2) + ((d1 & 0xF0) >> 2) + ((d1 & 0x300) << 4)) & 0xFFFF
        for c in range(nc):
            a1 = a2
            for r in range(nl):
                out.append(a1 & 0x3FFF); a1 += 4
                if a1 & 0x3F == 0: a1 -= 4; a1 = (a1 & 0xCFC3) | ((a1 + 0x1000) & 0x3000)
            a2 = (a2 & 0xF000) | ((a2 + 0x40) & 0xFFC)
    elif plan == 3:
        d1 = (-y) & 0xFFFF; a2 = ((x & 0x7E0) + ((d1 & 0xE0) >> 3) + ((d1 & 0x700) << 3)) & 0xFFFF
        for c in range(nc):
            a1 = a2
            for r in range(nl):
                out.append(a1 & 0x3FFF); a1 += 4
                if a1 & 0x1F == 0: a1 -= 4; a1 = (a1 & 0xC7E3) | ((a1 + 0x800) & 0x3800)
            a2 = (a2 & 0xF800) | ((a2 + 0x20) & 0x7FC)
    else:
        d1 = (~y) & 0xFFFF; a2 = (((x & 0x1F8) << 4) + ((d1 & 0xF8) >> 1) + ((d1 & 0x100) << 5)) & 0xFFFF
        for c in range(nc):
            a1 = a2
            for r in range(nl):
                out.append(a1 & 0x3FFF); a1 += 4
                if a1 & 0x7F == 0: a1 -= 4; a1 = (a1 & 0xDF83) | ((a1 + 0x2000) & 0x2000)
            a2 = (a2 & 0xE000) | ((a2 + 0x80) & 0x1FFC)
    return out
VR = {1: 0, 2: -0x5C00, 3: 0x900}
# scroll2 : le portage a renuméroté une partie des codes (−$63, −$20) : on compare les PIXELS (ISO : e227 élément
# code + $3600 ; MAME : ROM, tuile VRAM + $10000) ; scroll1 / scroll3 : codes identiques à l'arcade
import numpy as np
_RAW = np.load("<workspace>/work/carto_sfa2/gfx/sfa2_tiles_raw.npy", mmap_mode="r")
_e = np.fromfile(os.path.join(DON, "e227.bin"), np.uint8); _P8 = np.stack([_e & 0xF, _e >> 4], -1).reshape(-1)
_hm, _hi = {}, {}
def px_mame(v):
    if v not in _hm: _hm[v] = np.array(_RAW[v + 0x10000]).tobytes()
    return _hm[v]
def px_iso(c):
    if c not in _hi: _hi[c] = _P8[256 * (c + 0x3600):256 * (c + 0x3601)].tobytes()
    return _hi[c]
def meme(plan, vu, att):
    """vu : (code VRAM, attr) MAME ; att : (code ro2 du bloc, attr) ISO"""
    if vu[0] is None: return False
    if plan != 2: return vu == ((att[0] + VR[plan]) & 0xFFFF, att[1]) or (att[0] == 0x20 and vu[0] == (0x20 + VR[plan]) & 0xFFFF)
    if att[0] == 0x20: return vu[0] == (0x20 - 0x5C00) & 0xFFFF
    return vu[1] == att[1] and px_mame(vu[0]) == px_iso(att[0])

def attendu(plan, bl):
    return [((c + VR[plan]) & 0xFFFF, a) for c, a in bl["paires"]]

class Etat:
    """tilemaps, palettes, rowscroll reconstitués image par image à partir des deltas"""
    def __init__(s, E):
        s.ev = collections.defaultdict(list)
        for k, n, i, v in E["t"]: s.ev[int(k)].append(("t", int(n), int(i), int(v, 16)))
        for k, i, v in E["p"]: s.ev[int(k)].append(("p", 0, int(i), int(v, 16)))
        for k, i, v in E["l"]: s.ev[int(k)].append(("l", 0, int(i), int(v, 16)))
        s.T = {1: {}, 2: {}, 3: {}}; s.P = {}; s.L = {}
        s.images = sorted({int(e[0]) for e in E["c"]})
    def avance(s, k):
        for g, n, i, v in s.ev.get(k, ()):
            if g == "t": s.T[n][i] = v
            elif g == "p": s.P[i] = v
            else: s.L[i] = v
    def lit(s, plan, adrs):
        return [(s.T[plan].get(a // 2), s.T[plan].get(a // 2 + 1)) for a in adrs]

COUV = collections.defaultdict(set)
tenus = collections.Counter(); coupes = collections.Counter(); unites = collections.defaultdict(collections.Counter)
def controle(stg, res, det):
    E = AC.lit(stg); S = Etat(E); objs = collections.defaultdict(list)
    for k, pool, slot, act, cls, sub, fr, dur, x, y in E["o"]:
        objs[(pool, int(slot))].append((int(k), int(cls, 16), int(sub, 16), int(fr, 16) & 0xFFFFFF, int(x, 16), int(y, 16)))
    k0, k1 = S.images[0], S.images[-1]
    cum = {}; tot_t = 0
    for kk, n in E["c"]: tot_t += int(n); cum[int(kk)] = tot_t        # tics cumulés à la fin de l'image
    # objets du décor de ce STG : enregistrements (pour le plan des objets de classe 1)
    D = json.load(open(os.path.join(DON, "sfa2_decors.json")))["decors"][int(stg, 16) // 2]
    plans = {(o["x"], o["y"], o["routine"]): bytes.fromhex(o["brut"])[9] for o in D["objets"]}
    suivis = []   # (genre, clé, table ISO, anim, liste [(k, rang)], extra)
    objs_fr = {}
    for (pool, slot), L in objs.items():
        cls, sub = L[0][1], L[0][2]
        cle = "%s%02X" % (pool, cls)
        if (pool == "A" and "%02x" % cls in AO.HORS) or (pool == "C" and cls in (0, 0x0E)): continue
        if cle == "A01":
            ra = None; x0, y0 = L[0][4], L[0][5]
            cands = [(abs(ox - x0) + abs(oy - y0), pl) for (ox, oy, rt), pl in plans.items() if rt == "$01%02X" % sub]
            if cands: ra = {4: "$23EFAE", 8: "$23F110", 12: "$243910"}.get(min(cands)[1])
            if ra is None:          # objet de classe 1 créé par un autre : table d'après le cadre
                ra = next((r for r in ("$23F110", "$243910", "$23EFAE") if (r, L[0][3]) in A2I), None)
        elif cle == "A02": ra = "$05B54E"
        elif cle == "A55": ra = "$06EA6A"
        elif cle == "A53": ra = "$06E920"
        elif cle == "A3F": ra = "$23EFAE"
        elif cle in ("A5D", "A4C", "A49", "A5F"):        # canaux / couleurs directes / fixe : contrôlés autrement ou non décodés
            res["objet_sans_cadre_%s" % cle] += 1; continue
        else:
            r = AO.racine(pool, cls, sub); ra = "$%06X" % r if r else None
        if ra not in TAB: res["objet_sans_table"] += 1; det.append("%s %s%d %s.%02X : pas de table ISO" % (stg, pool, slot, cle, sub)); continue
        seq = []
        for (k, c, sb, fr, x, y) in L:
            m = A2I.get((ra, fr))
            if m is None: seq.append((k, None, None, x, y)); continue
            seq.append((k, m[0], m[1], x, y))
        suivis.append((cle, "%s%d" % (pool, slot), ra, seq)); objs_fr["%s%d" % (pool, slot)] = [(k, fr) for (k, c, sb, fr, x, y) in L]
    # 1. chronologie des cadres
    for cle, nom, ra, seq in suivis:
        t = TAB[ra]
        for kk, fr in objs_fr[nom]:
            for ia, ka in A2M.get((ra, fr), ()): COUV[(ra, ia)].add(ka)
        for (k, i, r, x, y), (k2, i2, r2, x2, y2) in zip(seq, seq[1:]):
            if k == k0: res["passage_debut_fenetre"] += 1; continue      # 1er état : passage commencé avant la fenêtre
            if i is None or i2 is None:
                fx = [x for x in objs_fr[nom] if x[0] in (k, k2)]
                if any(AA.l(0x215240 + 0, AA.D) is not None and 0x215240 <= f < 0x21B7B6 for _, f in fx):
                    res["cadre_table_commune_215240"] += 1; continue      # effets communs (aussi utilisés hors décor)
                res["cadre_hors_iso"] += 1
                if res["cadre_hors_iso"] < 40: det.append("%s %s %s %s : cadre hors table ISO" % (stg, nom, cle, ra))
                continue
            vu = k2 - k; m = RYTHME.get(cle, 1)
            fr1 = [x for x in objs_fr[nom] if x[0] == k][0][1]; fr2 = [x for x in objs_fr[nom] if x[0] == k2][0][1]
            poss = A2M[(ra, fr1)]; poss2 = {(a, b) for a, b in A2M[(ra, fr2)]}
            ok_suiv = any((ia, suivant(t["anims"][ia], ka)) in poss2 for ia, ka in poss)
            durs = {t["anims"][ia]["cadres"][ka]["duree"] for ia, ka in poss}
            vt = cum.get(k2, 0) - cum.get(k, 0)
            if ok_suiv and vu in {m * d for d in durs}: res["passage_ok"] += 1; unites[cle]["images"] += 1
            elif ok_suiv and vt in {m * d for d in durs}: res["passage_ok_tics"] += 1; unites[cle]["tics"] += 1
            elif cle in ("A4E",): res["passage_manuel"] += 1               # Ryu : pas fait par le gestionnaire
            elif not ok_suiv and i2 != i: res["changement_anim"] += 1       # décision du gestionnaire (autre animation)
            elif not ok_suiv and any(kb <= 1 for _, kb in poss2): res["relance_gestionnaire"] += 1   # animation relancée (cadre 0 ou 1)
            elif any(t["anims"][ia]["cadres"][ka]["drapeaux"] & 0x80 or suivant(t["anims"][ia], ka) is None for ia, ka in poss) and vu >= min(durs):
                res["passage_fin_gestionnaire"] += 1                          # fin d'animation : le gestionnaire relance / enchaîne
            elif ok_suiv:            # bon cadre suivant, durée propre au gestionnaire (pas par tic, une image sur deux, pause…)
                res["ordre_ok_rythme_gestionnaire"] += 1; coupes[(stg, cle)] += 1
                if coupes[(stg, cle)] <= 2: det.append("rythme %s %s %s %s/%s/%d durée ISO %s vue %d images %d tics" % (stg, nom, cle, ra, i, r, sorted(durs), vu, vt))
            elif vu < m * min(durs): res["passage_coupe"] += 1                # coupé par une décision du gestionnaire
            else:
                res["passage_ko"] += 1; det.append("%s %s %s %s/%s/%d durée ISO %s vue %d suivant ISO %s vu %s" % (stg, nom, cle, ra, i, r, sorted(durs), vu, suivant(t["anims"][i], r), r2))
    # 2. et 3. contenu image par image (tuiles des objets de classe 1, couleurs des objets de palette)
    pal_obj = [(cle, nom, ra, seq) for cle, nom, ra, seq in suivis if TAB[ra]["moteur"] == "palette"]
    til_obj = [(cle, nom, ra, seq) for cle, nom, ra, seq in suivis if TAB[ra]["moteur"].startswith("tuiles")]
    # canaux de tuiles s2 et listes de palettes (sans pointeur de cadre dans le journal)
    canaux = []
    for kc, c in A["canaux_s2"].items():
        if not c.get("canaux") or "si (" in c["role"]: continue
        cl = {"$3C": "0E", "$42": "20", "$5D": "1C", "$6B": "18"}[c["role"].split()[1]]
        if cl == stg:
            for ch in c["canaux"]: canaux.append((str(ch["anim"]), ch["x"], ch["y"]))
    if stg == "1A": canaux.append(("13", 0x1F0, 0x80))       # Sakura $6A : immédiats du code ($71044)
    LISTES_STG = {"06": ["$06D6C2", "$06D706", "$06D71A", "$06D80E", "$06D932", "$06D956", "$06D68A", "$06D69E"],
                  "20": ["$06C868", "$06C89C", "$06C8D0", "$06FA16", "$071580"], "1A": ["$07113C"]}.get(stg, [])
    lst = [l_ for l_ in A["listes_palette"].values() if l_["arcade"] in LISTES_STG]
    # destinations écrites par une seule liste du décor (les autres sont partagées : dernier écrivain inconnu)
    dl = {l_["arcade"]: {e["dest"] for c in l_["cadres"] for e in A["entrees_palette"][c["ptr"]]} for l_ in lst}
    excl = {a: {d for d in ds if all(d not in dl[b] for b in dl if b != a)} for a, ds in dl.items()}
    vu_can = collections.defaultdict(list); vu_lst = collections.defaultdict(list)
    cur = {nom: None for _, nom, _, _ in suivis}; pos = {}
    idx_seq = {nom: 0 for _, nom, _, _ in suivis}
    an_s2 = TAB["$23F110"]["anims"]
    for k in range(k0, k1 + 1):
        S.avance(k)
        for cle, nom, ra, seq in til_obj + pal_obj:
            j = idx_seq[nom]
            while j + 1 < len(seq) and seq[j + 1][0] <= k: j += 1
            idx_seq[nom] = j
            if seq[j][0] > k or seq[j][1] is None: continue
            _, i, r, x, y = seq[j]; c = TAB[ra]["anims"][i]["cadres"][r]
            if TAB[ra]["moteur"].startswith("tuiles"):
                pl = int(TAB[ra]["moteur"][-1]); bl = A["blocs"][c["ptr"]]
                adr = cases(pl, (x + c["dx"]) & 0xFFFF, (y + c["dy"]) & 0xFFFF, bl["lignes"], bl["colonnes"])
                if k == seq[j][0]: continue        # l'image du changement : écriture pendant l'image (registres t−1)
                vu = S.lit(pl, adr)
                ok = all(meme(pl, v, tuple(a)) for v, a in zip(vu, bl["paires"]))
                res["tuiles_image_ok" if ok else "tuiles_image_ko"] += 1
                if not ok and res["tuiles_image_ko"] < 20: det.append("%s %s image %d %s/%s/%d tuiles ≠" % (stg, nom, k, ra, i, r))
            else:
                if k == seq[j][0]: continue
                ent = A["entrees_palette"][c["ptr"]]; ok = True
                for e in ent:
                    base = e["dest"] // 2
                    if base >= 0x700: continue
                    for q in range(15):
                        v = S.P.get(base + q)
                        if v is not None and (v & 0xFFF) != (e["couleurs"][q] & 0xFFF): ok = False
                res["palette_image_ok" if ok else "palette_image_ko"] += 1
                if not ok and res["palette_image_ko"] < 20: det.append("%s %s image %d %s/%s/%d couleurs ≠" % (stg, nom, k, ra, i, r))
        for (ai, x, y) in canaux:
            an = an_s2[ai]; trouve = None
            for r, c in enumerate(an["cadres"]):
                bl = A["blocs"][c["ptr"]]
                if all(meme(2, v, tuple(a)) for v, a in zip(S.lit(2, cases(2, x, y, bl["lignes"], bl["colonnes"])), bl["paires"])): trouve = r; break
            vu_can[(ai, x, y)].append((k, trouve))
        for l_ in lst:
            trouve = None
            for r, c in enumerate(l_["cadres"]):
                if all(all(S.P.get(e["dest"] // 2 + q) is not None and (S.P[e["dest"] // 2 + q] & 0xFFF) == (e["couleurs"][q] & 0xFFF)
                           for q in range(15)) for e in A["entrees_palette"][c["ptr"]] if e["dest"] in excl[l_["arcade"]]):
                    trouve = r; break
            vu_lst[l_["arcade"]].append((k, trouve))
    # suites de cadres des canaux et des listes : contenu reconnu à chaque image (cadres de contenu identique
    # confondus : identifiant = 1er cadre de même contenu), puis la suite des passages complets (contenu, durée) doit
    # se retrouver telle quelle dans la suite jouée par l'ISO (cadres de même contenu consécutifs fusionnés)
    for nomg, V, src in (("canal_s2", vu_can, lambda key: an_s2[key[0]]),
                         ("liste_pal", vu_lst, lambda key: next(l_ for l_ in lst if l_["arcade"] == key))):
        for key, L in V.items():
            an = src(key); nonvu = sum(1 for _, r in L if r is None)
            res[nomg + "_images_reconnues"] += len(L) - nonvu; res[nomg + "_images_non_reconnues"] += nonvu
            if nonvu: det.append("%s %s %s : %d images sur %d sans cadre ISO reconnu" % (stg, nomg, key, nonvu, len(L)))
            if nomg == "liste_pal" and key == "$07113C":       # Sakura : la liste avance avec le canal de tuiles ($71112)
                ch = [r for _, r in vu_can[("13", 0x1F0, 0x80)]]; li = [r for _, r in L]
                chg_c = {j for j in range(1, len(ch)) if ch[j] != ch[j - 1]}; chg_l = {j for j in range(1, len(li)) if li[j] != li[j - 1]}
                res["liste_pal_synchro_ok" if chg_l <= chg_c else "liste_pal_synchro_ko"] += 1
                det.append("1A liste $07113C : %d changements, tous au même instant qu'un changement du canal s2 : %s" % (len(chg_l), chg_l <= chg_c))
                continue
            canon = {}
            for r, c in enumerate(an["cadres"]):
                cle_c = json.dumps(A["blocs"][c["ptr"]] if nomg == "canal_s2" else [e["couleurs"][:15] + [e["dest"]] for e in A["entrees_palette"][c["ptr"]] if e["dest"] in excl[key]])
                canon.setdefault(cle_c, r); canon[r] = canon[cle_c]
            jeu = []; r = 0; n = 0
            while n < 6000 and r is not None:
                d = an["cadres"][r]["duree"] or 99999; cr = canon[r]
                if jeu and jeu[-1][0] == cr: jeu[-1][1] += d
                else: jeu.append([cr, d])
                n += d; r = suivant(an, r)
            runs = []
            for k, r in L:
                cr = canon.get(r) if r is not None else None
                if runs and runs[-1][0] == cr: runs[-1][1] += 1
                else: runs.append([cr, 1])
            inter = runs[1:-1]
            if not inter: res[nomg + "_sans_passage_complet"] += 1; continue
            ok = any(all(j0 + j < len(jeu) and jeu[j0 + j] == inter[j] for j in range(len(inter))) for j0 in range(len(jeu)))
            if ok: res[nomg + "_suite_ok"] += 1; res[nomg + "_passage_ok"] += len(inter)
            else:
                # passages pris un à un (le gestionnaire peut suspendre le canal)
                bons = sum(1 for (c1, n1) in inter if [c1, n1] in jeu)
                res[nomg + "_passage_ok"] += bons; res[nomg + "_passage_ko"] += len(inter) - bons
                det.append("%s %s %s : suite non retrouvée telle quelle ; %d passages sur %d identiques à un passage ISO ; vus %s… ISO %s…" % (
                    stg, nomg, key, bons, len(inter), inter[:8], jeu[:8]))
    # 4. Gen : rowscroll = sinus de l'ISO ($1DD48 : lignes c−1−j et c+j reçoivent (sin[(ph + $A0·j) & $1FE] >> 12) + $C0)
    if stg == "22":
        sin = A["sinus_gen"]["valeurs"]; S2 = Etat(E); lignes = sorted({int(i) for kk, i, vv in E["l"] if int(kk) > k0 + 1})
        c = lignes[0] + 24 if lignes else None; ok = ko = 0; ph_prec = None; pas = collections.Counter()
        PRED = {ph: [((sin[((ph + 0xA0 * j) & 0x1FE) // 2] >> 12) + 0xC0) & 0xFFFF for j in range(24)] for ph in range(0, 0x200, 2)}
        for k in range(k0, k1 + 1):
            S2.avance(k)
            if k < k0 + 2 or c is None: continue
            haut = [S2.L.get(c + j) for j in range(24)]; bas = [S2.L.get(c - 1 - j) for j in range(24)]
            phs = [ph for ph, p in PRED.items() if p == haut and p == bas]
            if phs:
                ok += 1
                if ph_prec is not None: pas[min(((p - ph_prec) & 0x1FF) for p in phs)] += 1
                ph_prec = phs[0]
            else: ko += 1
        res["gen_sinus_image_ok"] += ok; res["gen_sinus_image_ko"] += ko
        det.append("22 sinus de Gen : ligne centrale %s ; %d images expliquées par la table de l'ISO, %d non ; pas de phase "
                   "(compatibles) %s" % (c, ok, ko, dict(pas.most_common(4))))

if __name__ == "__main__":
    res = collections.Counter(); det = []; par = {}
    for stg in STGS:
        avant = collections.Counter(res); controle(stg, res, det)
        par[stg] = {k: v - avant.get(k, 0) for k, v in res.items() if v - avant.get(k, 0)}
        print(stg, par[stg])
    os.makedirs(os.path.join(os.path.dirname(ICI), "controle"), exist_ok=True)
    with open(os.path.join(os.path.dirname(ICI), "controle", "controle_anims.tsv"), "w") as f:
        f.write("décor\tcontrôle\tnombre\n")
        for stg, d in par.items():
            for k, v in sorted(d.items()): f.write("$%s\t%s\t%d\n" % (stg, k, v))
        f.write("# total\n"); [f.write("tous\t%s\t%d\n" % kv) for kv in sorted(res.items())]
        f.write("# unité des durées par classe (passages complets conformes : en images / en tics)\n")
        [f.write("classe\t%s\timages %d / tics %d\n" % (k, v["images"], v["tics"])) for k, v in sorted(unites.items())]
        f.write("# passages à l'ordre conforme mais au rythme propre au gestionnaire\n"); [f.write("rythme\t%s %s\t%d\n" % (a, b, n)) for (a, b), n in sorted(coupes.items())]
        f.write("# détails\n"); [f.write(x + "\n") for x in det]
    # couverture : animations vues sous MAME, cycle complet = tous les cadres de l'animation vus
    compl = sum(1 for (ra, ia), v in COUV.items() if len(v) >= len(TAB[ra]["anims"][ia]["cadres"]))
    print("couverture des objets : %d animations vues, %d en cycle complet" % (len(COUV), compl))
    with open(os.path.join(os.path.dirname(ICI), "controle", "controle_anims.tsv"), "a") as f:
        f.write("# couverture (animations à objet) : table/anim\tcadres vus / cadres\n")
        for (ra, ia), v in sorted(COUV.items()): f.write("%s/%s\t%d / %d\n" % (ra, ia, len(v), len(TAB[ra]["anims"][ia]["cadres"])))
    print("TOTAL", dict(res)); print("rythme propre au gestionnaire (ordre conforme) :", dict(coupes)); print("unité des durées par classe (passages conformes) :", {k: dict(v) for k, v in sorted(unites.items())}); print("\n".join(det[:60]))
