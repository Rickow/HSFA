#!/usr/bin/env python3
"""controle_pos.py DONNEES MAME [ORACLE] [STG…] : POSITIONS des sprites de décor au pixel contre l'OBJ RAM de MAME
(sonde mame/obj.sh -> mame/out/stgXX[_combat]_pos.txt), et contrôles des objets $1F de Charlie (liste $1E).

Modèle (sfa : $11F36 -> $1225A, types de descripteur 0 $11F5E et 2 $11FEE), tout le reste vient de l'ISO :
  ancre : plan = $9(A6) (0 : écran ; 4/8/12 : $FF8200/$FF8280/$FF8300) ; X0 = X − plan.X + $40 − d0 (d0 : correction de
          rowscroll pour le plan 8 quand $F(A6) ≠ 0) ; Y0 = $100 − (Y − plan.Y) ;
  type 0 : attr = attr_desc ^ ($B << 5) ; flip X/Y de cet attribut -> dx = −dx − 16, dy = −dy − 16 ;
  type 2 : flip de l'objet seul ($B << 5) -> dx = −dx − 16·largeur, dy = −dy − 16·hauteur ; attr ^= $B << 5 (octet bas) ;
  palette : si $C(A6) bit 7, palette = (palette + $D(A6)) & $1F ;
  OBJ : x = (dx + X0) & $3FF | $8000, y = (dy + Y0) & $3FF | $2000, code = code_desc + $400.
Chaque objet dessiné doit avoir TOUTES ses entrées prédites dans l'OBJ de l'image (état de l'objet à l'image k, ou k − 1
quand il change dans l'image). Objets $1F : création (30 enregistrements ISO, X + caméra s2), vitesses ∈ tables de
saut de l'ISO, cadres = anims 5-7. Sprites de palette ≥ 24 sans objet : écrivain (PC) des lignes « w ».
Sortie : controle/controle_pos.tsv + résumé."""
import sys, os, json, struct, collections, glob, re
DON, MAME = sys.argv[1], sys.argv[2]
ORA = sys.argv[3] if len(sys.argv) > 3 and os.path.isdir(sys.argv[3]) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../etude_decors/sfa1/roms_dech")
FILTRE = [a.upper() for a in sys.argv[3:] if not os.path.isdir(a)]
A = json.load(open(os.path.join(DON, "sfa1_anims.json"))); DEC = json.load(open(os.path.join(DON, "sfa1_decors.json")))["decors"]
D = open(os.path.join(ORA, "donnees.bin"), "rb").read()
w = lambda x: struct.unpack_from(">H", D, x)[0]; l = lambda x: struct.unpack_from(">I", D, x)[0]
ARC = {"tuiles_s2": 0x11BCBA, "palettes": 0x444D4, "spr_ryu": 0x10F060, "spr_ken": 0x10F526, "spr_charlie": 0x10F69E,
       "spr_guy": 0x10FC44, "spr_birdie_rose": 0x110292, "spr_adon": 0x10FBDA, "spr_sodom": 0x10FC20}
P2I = {}
for nom, t in A["tables"].items():
    T = ARC[nom]
    for i, sq in t["anims"].items():
        a = T + w(T + 2 * int(i))
        for k, c in enumerate(sq["cadres"]):
            P2I.setdefault(a, (nom, i, k)); f = D[a + 2]; a += t["taille_cadre"]
            if f & 0x80: a = l(a)
PLAN = {4: 0, 8: 1, 12: 2}
CLASSES_SPR = (0x06, 0x11, 0x15, 0x16, 0x1F, 0x24)      # classes de décor dessinées par descripteur de sprites          # $122CC : 4 -> $FF8200 (s1), 8 -> $FF8280 (s2), 12 -> $FF8300 (s3)

def ancre(o, cam):
    """($1225A) X0, Y0 de l'objet"""
    if o["b9"] == 0: return o["X"] + 0x40, 0x100 - o["Y"]
    px, py = cam[PLAN[o["b9"]]]
    return o["X"] - px + 0x40 - o["d0"], 0x100 - (o["Y"] - py)

def predit(o, cam, a0=None):
    """entrées OBJ (x, y, code, attr) prédites depuis l'ISO pour l'objet o (ligne « a ») ; None si pas de descripteur"""
    if o["ptr"] not in P2I: return None
    nom, i, kk = P2I[o["ptr"]]
    if not nom.startswith("spr_"): return None
    e = A["descripteurs"][A["tables"][nom]["anims"][i]["cadres"][kk]["ptr"]]
    X0, Y0 = a0 if a0 else ancre(o, cam)
    fl = (o["bb"] << 5) & 0xFF; R = []
    for code, at, (dx, dy) in zip(e["codes"], e["attrs"], e["xy"]):
        if e["type"] == 0:
            d3 = at ^ fl
            if d3 & 0x40: dy = -dy - 16
            if d3 & 0x20: dx = -dx - 16
        else:
            d3 = at ^ fl; hb = at >> 8
            if fl & 0x40: dy = -dy - ((hb & 0xF0) + 0x10)
            if fl & 0x20: dx = -dx - ((hb & 0xF) + 1) * 16
        if o["bc"] & 0x80: d3 = (d3 & 0xFF60) | ((d3 + o["bd"]) & 0x1F)
        R.append((((dx + X0) & 0x3FF) | 0x8000, ((dy + Y0) & 0x3FF) | 0x2000, (code + 0x400) & 0xFFFF, d3 & 0xFFFF))
    return (nom, i, kk), R

lignes = []; bilan = collections.Counter()
def note(stg, quoi, ok, detail):
    r = "OK" if ok else ("NON CONTRÔLÉ" if ok is None else "ÉCART")
    lignes.append("%s\t%s\t%s\t%s" % (stg, quoi, r, detail)); bilan[r] += 1
    print("%s %-36s %-5s %s" % (stg, quoi, r, detail))

def lit(fn):
    F = {}; OB = collections.defaultdict(dict); S = collections.defaultdict(list); W = []; DS = collections.defaultdict(list)
    for x in open(fn):
        v = x.split(); k = int(v[1])
        if v[0] == "f":
            h = [int(t, 16) for t in v[2:8]]
            F[k] = dict(cam=[(h[4], h[5]), (h[0], h[1]), (h[2], h[3])], e07=int(v[8], 16), e1c=int(v[9], 16))
        elif v[0] == "a":
            OB[k][int(v[2])] = dict(cl=int(v[3], 16), ss=int(v[4], 16), et=int(v[5], 16), ptr=int(v[6], 16), X=int(v[7], 16),
                                    Y=int(v[8], 16), b9=int(v[9], 16), bb=int(v[10], 16), bc=int(v[11], 16), bd=int(v[12], 16),
                                    bf=int(v[13], 16), d0=int(v[14]), vx=int(v[15], 16), vy=int(v[16], 16), att=int(v[17], 16),
                                    ba=int(v[18], 16), anim=int(v[19], 16))
        elif v[0] == "d":
            h = [int(t, 16) for t in v[14:20]]
            # le dessin a lieu PENDANT l'image suivante (k = dernière image finie dans la sonde) : son OBJ est celui de k + 1
            d4 = int(v[21], 16); ent = v[22] if len(v) > 22 else ""
            DS[k + 1].append(dict(fente=int(v[2]), cl=int(v[3], 16), ss=int(v[4], 16), ptr=int(v[5], 16), X=int(v[6], 16), Y=int(v[7], 16),
                              b9=int(v[8], 16), bb=int(v[9], 16), bc=int(v[10], 16), bd=int(v[11], 16), bf=int(v[12], 16),
                              d0=int(v[13]), cam=[(h[0], h[1]), (h[2], h[3]), (h[4], h[5])], X0=d4 & 0xFFFF, Y0=d4 >> 16,
                              recouvert=ent.startswith("X"),
                              ent=[tuple(int(t, 16) for t in e.split(",")) for e in ent.lstrip("X").split(";") if e]))
        elif v[0] == "s": S[k].append((int(v[4], 16), int(v[5], 16), int(v[6], 16), int(v[7], 16)))
        elif v[0] == "w": W.append((k, int(v[2], 16), int(v[4], 16), int(v[5], 16), int(v[6], 16) & 0x1F))
    return F, OB, S, W, DS

def s32(v): return v - (1 << 32) if v & 0x80000000 else v
SAUTS = A.get("sauts_1f")
fichiers = sorted(glob.glob(os.path.join(MAME, "out", "stg*_pos.txt")))
etrangers = collections.defaultdict(set)
for fn in fichiers:
    nomf = os.path.basename(fn)[3:-8]; stg = nomf[:2]
    if FILTRE and stg not in FILTRE and nomf.upper() not in FILTRE: continue
    F, OB, S, W, DS = lit(fn)
    K = sorted(F)
    # positions : chaque DESSIN d'un objet de décor (ligne « d » : état de l'objet et des plans à l'instant où le jeu écrit
    # ses entrées, ancre D4 calculée par $1225A, entrées réellement écrites dans l'OBJ) :
    #   (1) disposition : entrées écrites = descripteur de l'ISO posé à l'ancre du jeu, au pixel, dans l'ordre ;
    #   (2) ancre : Y0 = $100 − (Y − plan.Y) ; X0 = X − plan.X + $40 − d0 (d0 = correction de rowscroll lue par la sonde).
    par = collections.Counter(); ec = collections.Counter(); ex = {}; pixels = collections.Counter(); anc = collections.Counter()
    anc_ec = collections.Counter(); anc_ex = {}; rec = collections.Counter()
    cams = collections.defaultdict(set); vivants = collections.Counter()
    for k in K:
        vus = set(); ecrits = set()
        for o in DS.get(k, []):
            if o["cl"] not in CLASSES_SPR: continue
            cle = "$%02X%02X" % (o["cl"], o["ss"]) if o["cl"] != 0x1F else "$1F (liste $1E)"
            vus.add(o["fente"])
            if o["recouvert"]: rec[cle] += 1; continue
            p = predit(o, o["cam"], (o["X0"], o["Y0"]))
            if p is None: ec[cle] += 1; ex.setdefault(cle, "image %d : cadre %06X hors des tables de l'ISO" % (k, o["ptr"])); continue
            ecrits |= set(o["ent"])
            if p[1] == o["ent"]:
                par[cle] += 1; pixels[cle] += len(p[1]); cams[cle].add(o["cam"][1][0])
            else:
                ec[cle] += 1
                ex.setdefault(cle, "image %d %s : ISO %s / OBJ %s" % (k, p[0], ["%04X,%04X,%04X,%04X" % e for e in p[1][:2]], ["%04X,%04X,%04X,%04X" % e for e in o["ent"][:2]]))
            X0, Y0 = ancre(o, o["cam"])
            if ((X0 - o["X0"]) & 0xFFFF, (Y0 - o["Y0"]) & 0xFFFF) == (0, 0): anc[cle] += 1
            else:
                anc_ec[cle] += 1
                anc_ex.setdefault(cle, "image %d : formule (%X, %X) / jeu (%X, %X), d0 sonde %d" % (k, X0 & 0xFFFF, Y0 & 0xFFFF, o["X0"], o["Y0"], o["d0"]))
        for s, o in OB[k].items():
            if o["cl"] in CLASSES_SPR and o["et"] and s not in vus:
                vivants["$%02X%02X" % (o["cl"], o["ss"]) if o["cl"] != 0x1F else "$1F (liste $1E)"] += 1
        for e in S.get(k, []):
            if e not in ecrits: etrangers[stg].add((e[2], e[3] & 0x1F))
    for cle in sorted(set(par) | set(ec)):
        n, m = par[cle], ec[cle]
        note(nomf, "positions %s" % cle, m == 0 and n > 0,
             "%d dessins identiques au pixel (%d entrées OBJ), %d écarts%s ; ancre = formule %d / %d%s ; caméra s2 X %s ; "
             "dessins recouverts dans l'image %d ; images où l'objet existe sans être dessiné : %d"
             % (n, pixels[cle], m, (" (" + ex[cle] + ")") if m else "", anc[cle], anc[cle] + anc_ec[cle],
                (" (" + anc_ex[cle] + ")") if anc_ec[cle] else "",
                ("%03X-%03X" % (min(cams[cle]), max(cams[cle]))) if cams[cle] else "-", rec[cle], vivants[cle]))
    # objets $1F de Charlie (liste $1E)
    cr = {}
    for k in K:
        for s, o in OB[k].items():
            if o["cl"] == 0x1F and s not in cr: cr[s] = (k, o)
    if cr:
        liste = [bytes.fromhex(h) for h in A["liste_1e"]]
        k0 = min(k for k, _ in cr.values())
        cam = F[k0 - 1]["cam"][1][0] if k0 - 1 in F else F[k0]["cam"][1][0]
        att = collections.Counter((struct.unpack_from(">H", r, 0)[0] + cam, struct.unpack_from(">H", r, 2)[0], r[5], r[8], r[9],
                                   struct.unpack_from(">H", r, 12)[0]) for r in liste)
        # $41C5E : création dans l'ordre de la liste, arrêt à la 1re fente refusée par $163B8 (pool 1 plein)
        att = collections.Counter((struct.unpack_from(">H", r, 0)[0] + cam, struct.unpack_from(">H", r, 2)[0], r[5], r[8], r[9],
                                   struct.unpack_from(">H", r, 12)[0], struct.unpack_from(">H", r, 10)[0]) for r in liste[:len(cr)])
        vu = collections.Counter((o["X"], o["Y"], o["ss"], o["bb"], o["b9"], o["anim"], o["att"]) for k, o in cr.values())
        libres = 32 - len([s for s, o in OB[k0 - 1].items()]) if k0 - 1 in OB else None
        ok = vu == att and all(k == k0 for k, _ in cr.values())
        note(nomf, "création des $1F (liste $1E)", ok, "%d objets créés à l'image %d (drapeaux $2E07=%d $2E1C=%d), = les %d premiers des %d de l'ISO "
             "(pool 1 : %s fentes libres avant) ; X = X(ISO) + caméra s2 %03X ; (X, Y, sous-type, $B, $9, anim, attente) %s"
             % (len(cr), k0, F[k0]["e07"], F[k0]["e1c"], len(cr), len(liste), libres, cam, "identiques" if vu == att else "DIFFÉRENTS"))
        # vitesses et cadres
        if SAUTS:
            okv = collections.Counter(); badv = []
            for k in K:
                for s, o in OB[k].items():
                    if o["cl"] != 0x1F or o["et"] < 2: continue   # état 0 (attente) : vitesses non initialisées
                    vx, vy = s32(o["vx"]), s32(o["vy"])
                    if o["ss"] in (0, 1):
                        # 1er saut (A, gravité commune) ou 2e saut (C, gravité de l'entrée) ; vy décroît de la gravité à
                        # chaque tic ; vx = ± vx(table) ($B = 0 : négatif)
                        T = [dict(e, gravite=SAUTS["gravite"]) for e in SAUTS["A"][str(o["ss"])]] + SAUTS["C"][str(o["ss"])]
                        bon = any((vx == (e["vx"] if o["bb"] else -e["vx"])) and (e["vy"] - vy) % (-e["gravite"]) == 0 and vy <= e["vy"] for e in T)
                    else:
                        T = SAUTS["B"]
                        bon = any(vx == e["vx"] and vy == e["vy"] for e in T)      # $30/$34 tenus (déplacement calculé à part)
                    okv[bon] += 1
                    if not bon and len(badv) < 3: badv.append("img %d fente %d ss %d vx %X vy %X" % (k, s, o["ss"], vx, vy))
            note(nomf, "vitesses des $1F (tables de saut)", okv[False] == 0 and okv[True] > 0,
                 "%d images d'objet en vol conformes à l'ISO, %d non %s" % (okv[True], okv[False], "; ".join(badv)))
        cad = collections.Counter(); hors = []
        for k in K:
            for s, o in OB[k].items():
                if o["cl"] != 0x1F or o["et"] < 2: continue          # état 0 : attente, pointeur de cadre non initialisé
                p = P2I.get(o["ptr"])
                okc = p is not None and p[0] == "spr_charlie" and p[1] == str(5 + o["ss"])     # $26 (anim) est écrasé par le moteur ($24.l)
                cad[okc] += 1
                if not okc and len(hors) < 3: hors.append("img %d fente %d ptr %06X" % (k, s, o["ptr"]))
        note(nomf, "cadres des $1F = anim 5 + sous-type (ISO)", cad[False] == 0 and cad[True] > 0,
             "%d images d'objet, %d hors table %s" % (cad[True], cad[False], "; ".join(hors)))
    # écrivains des sprites de palette ≥ 24 qui ne viennent d'aucun objet de décor
    if W:
        pcs = collections.defaultdict(set)
        for k, pc, cl, code, pal in W: pcs[pc].add((code, pal))
        txt = " ; ".join("$%06X : %d (code, pal) dont pal %s" % (pc, len(v), sorted({p for _, p in v})) for pc, v in sorted(pcs.items()))
        note(nomf, "écrivains OBJ pal ≥ 24", None, txt)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle"), exist_ok=True)
open(os.path.join(os.path.dirname(os.path.abspath(DON)), "controle", "controle_pos.tsv"), "w").write(
    "decor\tcontrole\tresultat\tdetail\n" + "\n".join(lignes) + "\n")
print("BILAN : " + ", ".join("%s %d" % kv for kv in sorted(bilan.items())))
