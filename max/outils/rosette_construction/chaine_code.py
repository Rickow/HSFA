"""CHAÎNE SPRITES -> ANIMATIONS -> SITES D'APPEL -> FONCTIONS (2026-10-11).
Relie la Rosette de construction (frames PSP = frames Upper au pixel près ; animation PSP (table, n) = animation
Upper (table, m), anims_map de plXX.json) à la Rosette du code (rosette_code/ : appels moteur et routines).
Un site PSP qui lance l'animation (T, n) et un site arcade qui lance (T, m) affichent LES MÊMES IMAGES : leurs routines
sont homologues. Contrairement à rosette.py (même n° supposé des deux côtés), le n° est ici vérifié par les images.
Lanceurs : arcade $2A708 ($2B0) / $2A710 ($2BC) / $2A758 ($2B4) / $2A75E ($2B8) ; PSP 0x5D63C / 0x5D674 / 0x5D6EC /
0x5D724 (api_moteur.json) ; n° = D0 (arcade), a1 (PSP, a0 = objet). Numérotation arcade = Upper pour les n° 0-75.
Usage : python chaine_code.py [n° perso hexa …]"""
import os, sys, json, collections
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "rosette_code"))
os.chdir(os.path.join(ICI, "..", "rosette_code"))
import rosette as RS
from appels import arcade_calls, psp_calls
import modules
ROS = os.path.expanduser("~/.cache/sfa3max/rosette")
LANCE_A = {0x2A708: "$2B0", 0x2A710: "$2BC", 0x2A758: "$2B4", 0x2A75E: "$2B8"}
LANCE_P = {0x5D63C: "$2B0", 0x5D674: "$2BC", 0x5D6EC: "$2B4", 0x5D724: "$2B8"}


def lanceurs_psp():
    """lanceurs PSP + relais appris (fonctions PSP appariées à un lanceur arcade : appris.json, api, moteur_max_auto)"""
    L = dict(LANCE_P); L[0xCFA6C] = "$2BC"
    ap = json.load(open("appris.json")).get("fonction", {})
    for f, a in ap.items():
        if int(a, 16) in LANCE_A: L[int(f, 16)] = LANCE_A[int(a, 16)]
    return L


def sites_psp(a0, e0, L):
    """{lanceur: [(site, args)]} y compris les appels INTERNES au module (relais propres au perso)"""
    from relocs import img
    from mips import decode
    ins = list(decode(img, a0, e0)); out = collections.defaultdict(list)
    for k, i in enumerate(ins):
        if i.m != "jal" or i.tgt not in L: continue
        args = {}
        for p in ins[max(0, k - 6): k + 2]:
            if p.m in ("ori", "addiu") and p.rs == 0 and 4 <= p.rt <= 7: args["a%d" % (p.rt - 4)] = p.imm
        out[i.tgt].append((i.va, args))
    return out


def chaine(c):
    amap = json.load(open(os.path.join(ROS, "pl%02x.json" % c)))["anims_map"]
    ent, lo, hi = RS.ARC_ENTRIES[c]
    A, seen, tables = arcade_calls(ent, lo, hi)
    a0, e0 = modules.module_bounds()[c]
    P, ins = psp_calls(a0, e0)
    afs = RS.arcade_routines(seen, tables, ent, A)
    # sites arcade par (table, n)
    sa = collections.defaultdict(list)
    for t, nom in LANCE_A.items():
        for site, args in A.get(t, []):
            if "d0" in args: sa[(nom, args["d0"])].append(site)
    votes = collections.Counter(); st = collections.Counter()
    LP = lanceurs_psp(); PS = sites_psp(a0, e0, LP)
    for t, nom in LP.items():
        for site, args in PS.get(t, []):
            n = args.get("a1")
            if n is None: st["site PSP sans n° constant"] += 1; continue
            m = amap.get(nom, {}).get(str(n))
            if m is None: st["animation PSP sans équivalent par les images"] += 1; continue
            st["renuméroté (n ≠ m)" if m != n else "même n°"] += 1
            cibles = sa.get((nom, m), [])
            if not cibles: st["aucun site arcade ne lance (T, m)"] += 1; continue
            fp = RS.psp_fstart(site)
            for s in cibles: votes[(afs(s), fp)] += 1.0 / len(cibles)
    # paires de routines (meilleur vote, exclusives)
    RP, ua, up = {}, set(), set()
    for (fa, fp), v in votes.most_common():
        if fa in ua or fp in up or v < 0.99: continue
        RP[fa] = (fp, round(v, 2)); ua.add(fa); up.add(fp)
    # comparaison avec la Rosette du code
    M, RPc, *_ = RS.run(c)
    accord = sum(1 for fa, (fp, _) in RP.items() if RPc.get(fa) == fp)
    conflit = [(hex(fa), hex(fp), hex(RPc[fa])) for fa, (fp, _) in RP.items() if fa in RPc and RPc[fa] != fp]
    nouveau = [(hex(fa), hex(fp)) for fa, (fp, _) in RP.items() if fa not in RPc and fp not in set(RPc.values())]
    return {"RP": {fa: fp for fa, (fp, _) in RP.items()}, "sites": dict(st), "paires": len(RP), "accord_rosette_code": accord, "conflits": conflit,
            "nouvelles": nouveau, "paires_rosette_code": len(RPc)}


if __name__ == "__main__":
    for c in [int(x, 16) for x in sys.argv[1:]] or [0]:
        if c not in RS.ARC_ENTRIES: print("pl%02x : pas de code propre en arcade (ignoré)" % c); continue
        r = chaine(c)
        print("pl%02x : sites %s" % (c, r["sites"]))
        print("   paires de routines par les images : %d ; d'accord avec la Rosette du code : %d / %d paires connues ; "
              "conflits %d ; nouvelles %d" % (r["paires"], r["accord_rosette_code"], r["paires_rosette_code"],
                                              len(r["conflits"]), len(r["nouvelles"])))
        if r["conflits"]: print("   conflits (arcade, PSP images, PSP rosette) :", r["conflits"][:8])
