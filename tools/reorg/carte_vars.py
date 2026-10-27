#!/usr/bin/env python3
"""CARTE DES VARIABLES pour la comparaison de RAM (ETAPE A). Ecrit ../vars.json :
  trad_a5  : {"adresse_trad/T": nb}   acces A5 de la traduction (carte_image.txt figee), T = B|W|L
  trad_a6  : {"deplacement/T": nb}    champs A6 < $400 (structures joueur)
  arc_a5, arc_a6 : idem pour l'arcade (agent_couverture/arc_insn.pkl : code arcade atteint)
  pour chaque variable de la traduction, adresse arcade selon :
    'recette' : octet XOR 1, mot et long meme adresse, zone basse relogee (agent_symboles/_cache/reloc_a5.pkl)
    'paires'  : vote sur les instructions alignees (agent_symboles/_cache/paires_a5.json, A5_taille / A6_taille)
    'type'    : modele type (scripts/untranspile/typed_rule.py, acces MIPS de ro3)"""
import os, re, sys, json, pickle, collections
A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = "<workspace>/scripts/untranspile"; sys.path.insert(0, U)
SYM = "<workspace>/work/agent_symboles/_cache"
RX = re.compile(r"\$([0-9a-f]{1,4})\((A5|A6)\)")
def taille(op):
    op = op.upper()
    if op.endswith(".B"): return "B"
    if op.endswith(".L"): return "L"
    if op.endswith(".W"): return "W"
    if op[:4] in ("BTST", "BSET", "BCLR", "BCHG") or (op.startswith("S") and len(op) <= 3 and op not in ("SUB", "SWAP")): return "B"
    if op in ("LEA", "PEA"): return None
    return "W"
def s16(d): return d - 0x10000 if d & 0x8000 else d

def trad():
    a5, a6 = collections.Counter(), collections.Counter()
    for l in open(os.path.join(A, "carte_image.txt")):
        mn = l.rstrip("\n").split(" ", 2)[2]
        for ins in mn.split(";"):
            ins = ins.strip()
            if not ins or ins.startswith("["): continue
            op = ins.split()[0]; t = taille(op)
            if t is None: continue
            for d, r in RX.findall(ins):
                d = int(d, 16)
                if r == "A5": a5["%06x/%s" % (0xFF8000 + s16(d), t)] += 1
                elif d < 0x400: a6["%03x/%s" % (d, t)] += 1
    return a5, a6

RXA = re.compile(r"\((-?)\$([0-9a-f]+),\s*(A5|A6)\)")
def arcade():
    ins = pickle.load(open("<workspace>/work/agent_couverture/arc_insn.pkl", "rb"))
    a5, a6 = collections.Counter(), collections.Counter()
    for ad, (n, mn, ops) in ins.items():
        t = taille(mn)
        if t is None: continue
        for sg, d, r in RXA.findall(ops):
            d = int(d, 16) * (-1 if sg else 1)
            if r == "A5": a5["%06x/%s" % (0xFF8000 + d, t)] += 1
            elif 0 <= d < 0x400: a6["%03x/%s" % (d, t)] += 1
        for d, r in re.findall(r"\(\$([0-9a-f]+)\)?\b", ""): pass
    return a5, a6

def main():
    ta5, ta6 = trad(); aa5, aa6 = arcade()
    reloc = pickle.load(open(os.path.join(SYM, "reloc_a5.pkl"), "rb"))
    PA = json.load(open(os.path.join(SYM, "paires_a5.json")))
    import verify, typed_rule
    from layout_rule import access_stats
    acc = access_stats(open(verify.RO3, "rb").read())
    def recette(reg, t, T):
        """adresse (A5 : absolue ; A6 : deplacement) arcade selon la recette + relocation de la zone basse"""
        if reg == 5:
            d = (t - 0xFF8000) & 0xffff
            for lo, hi, add in reloc:
                if lo <= d <= hi:
                    if T == "B" and add % 2 == 0: return 0xFF8000 + s16(((d ^ 1) + add) & 0xffff)   # octet : XOR 1 puis delta
                    return 0xFF8000 + s16((d + add) & 0xffff)
        return t ^ 1 if T == "B" else t
    def paires(reg, t, T):
        d = ((t - 0xFF8000) & 0xffff) if reg == 5 else t
        e = PA["A%d_taille" % reg].get("%04x/%s" % (d, T))
        if not e: return None, 0
        best = max(e, key=lambda x: x[1])
        v = int(best[0], 16)
        return (0xFF8000 + s16(v) if reg == 5 else v), best[1]
    def type_(reg, t, T):
        d = ((t - 0xFF8000) & 0xffff) if reg == 5 else t
        h = d ^ 1 if T == "B" else d                 # deplacement hote PS2 (recette inverse)
        a = (h + typed_rule.predict_typed(acc, reg, T, h)) & 0xffff
        return 0xFF8000 + s16(a) if reg == 5 else a
    out = {"trad_a5": dict(ta5), "trad_a6": dict(ta6), "arc_a5": dict(aa5), "arc_a6": dict(aa6), "var_a5": {}, "var_a6": {}}
    for reg, src, key in ((5, ta5, "var_a5"), (6, ta6, "var_a6")):
        for k, n in src.items():
            t, T = k.split("/"); t = int(t, 16)
            p, votes = paires(reg, t, T)
            out[key][k] = {"n": n, "recette": recette(reg, t, T), "paires": p, "votes": votes, "type": type_(reg, t, T)}
    json.dump(out, open(os.path.join(A, "vars.json"), "w"), indent=0)
    print("trad : A5 %d variables (adresse/taille), A6 %d champs ; arcade : A5 %d, A6 %d" % (len(ta5), len(ta6), len(aa5), len(aa6)))
    for key in ("var_a5", "var_a6"):
        V = out[key].values()
        print(key, "avec vote :", sum(1 for v in V if v["paires"] is not None),
              "vote = recette :", sum(1 for v in V if v["paires"] == v["recette"]),
              "vote = type :", sum(1 for v in V if v["paires"] == v["type"]),
              "recette = type :", sum(1 for v in V if v["recette"] == v["type"]), "/", len(V))

if __name__ == "__main__":
    main()
