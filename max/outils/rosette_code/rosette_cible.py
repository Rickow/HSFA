"""Rosette CIBLÉE (idée utilisateur, 2026-10-07) : pour chaque fonction moteur PSP restant à écrire, retrouver son
équivalent arcade chez les persos de SFA3 (Ryu en tête) : dans chaque paire de routines appariées (rosette.run, graine =
équivalences déjà connues), un appel PSP à la fonction X est encadré par deux appels connus (repères) ; on relève ce que
fait l'arcade entre les deux repères correspondants : un appel (candidat) ou rien (code en ligne : fenêtre à lire).
Sortie : rosette_cible.json {X: {"candidats": {cible arcade: votes}, "en_ligne": n, "fenetres": [(perso, a0, a1, psp)]}}"""
import json, collections, sys
import rosette
from traduire import API
J = json.load(open("api_a_fournir.json"))
CIBLES = {int(f["psp"], 16) for f in J if not f["auto"] and not f["main"]}
seed = {a: p for p, a in API.items()}
res = {x: {"candidats": collections.Counter(), "en_ligne": 0, "fenetres": []} for x in CIBLES}
for c in sorted(rosette.ARC_ENTRIES):
    if c in (0x11, 0x13, 0x1f): continue
    try: M, RP, A, P, SA, SP = rosette.run(c, seed)
    except Exception as e: print("perso %02x : %s" % (c, e)); continue
    for fa, fp in RP.items():
        sp, sa = SP.get(fp, []), SA.get(fa, [])
        if not any(t in CIBLES for _, t, _ in sp): continue
        al = rosette.align(sa, sp, M); ap = {y[0]: x for x, y in al}          # site PSP apparié -> entrée arcade
        for k, (site, t, args) in enumerate(sp):
            if t not in CIBLES: continue
            prev = next((sp[j] for j in range(k - 1, -1, -1) if sp[j][0] in ap), None)
            nxt = next((sp[j] for j in range(k + 1, len(sp)) if sp[j][0] in ap), None)
            a0 = ap[prev[0]][0] if prev else fa
            a1 = ap[nxt[0]][0] if nxt else a0 + 0x80
            dans = [x for x in sa if a0 < x[0] < a1]
            if dans:
                for x in dans: res[t]["candidats"]["%06x" % x[1]] += 1
            else: res[t]["en_ligne"] += 1
            res[t]["fenetres"].append((c, "%06x" % a0, "%06x" % a1, "%06x" % site))
    print("perso %02x : %d routines appariées" % (c, len(RP)), file=sys.stderr)
out = {"%x" % x: {"candidats": dict(v["candidats"].most_common(6)), "en_ligne": v["en_ligne"], "fenetres": v["fenetres"][:12]} for x, v in res.items()}
json.dump(out, open("rosette_cible.json", "w"), indent=1)
for x, v in sorted(out.items(), key=lambda kv: -sum(kv[1]["candidats"].values()) - kv[1]["en_ligne"]):
    print("%6s  candidats %s  en ligne %d  sites %d" % (x, v["candidats"], v["en_ligne"], len(res[int(x, 16)]["fenetres"])))
