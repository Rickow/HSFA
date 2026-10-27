#!<workspace>/venv/bin/python
"""Verification statique des donnees de la redirection par le programme traduit (redirection_68k/, gen_redirection.py)
contre la correspondance et la table de rejeu : simule la routine « voix par pas » ($08BCCE / $06C192 : mot 0 ou mot 1 de
[$E6 + 8 index], + $500 cote 2), la routine des cris ($08C2AE corrigee : T_CRIS_V[$102] + n, sinon chemin d'origine) et
celle de $08C274 (T_V2_V), puis resout chaque code obtenu dans hsfa_rejeu_table.txt (CODE / REF / ALIAS) et le compare
au son attendu (commande source cote 1 ou cote 2, ou code SFA3 d'origine)."""
import os, sys, json, struct, csv
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ICI)
import gen_redirection as GR
from gen_rejeu import cote2
MOD = GR.MOD; B = GR.B


def table_rejeu():
    code, ref, alias = {}, {}, {}
    for l in open(os.path.join(ICI, "rejeu", "hsfa_rejeu_table.txt")):
        t = l.split()
        if not t: continue
        if t[0] == "CODE": code[int(t[1], 16)] = (t[2], int(t[3], 16))
        elif t[0] == "REF": ref[int(t[1], 16)] = int(t[2], 16)
        elif t[0] == "ALIAS": alias[int(t[1], 16)] = int(t[2], 16)
    def resout(c):
        if c in alias: return ("Z80", alias[c])
        k = 0
        while c in ref and k < 4: c = ref[c]; k += 1
        if c in code: return code[c]
        if c < 0xC00: return ("Z80", c)
        return None
    return resout


def main():
    d = open(MOD, "rb").read()
    w = lambda a: struct.unpack_from("<H", d, a - B)[0]
    blob = open(os.path.join(ICI, "redirection_68k", "donnees.bin"), "rb").read()
    J = json.load(open(os.path.join(ICI, "redirection_68k", "donnees.json")))
    base = int(J["base_exec"], 16)
    corr = json.load(open(os.path.join(ICI, "catalogue", "correspondance.json")))
    resout = table_rejeu()
    T90 = [w(0x5C9A90 + 2 * i) for i in range(40)]; T40 = [w(0x5C9A40 + 2 * i) for i in range(40)]
    cris_v = struct.unpack_from("<128H", blob, 0); v2_v = struct.unpack_from("<128H", blob, 0x100)
    err, nb = [], dict(pas=0, cris=0, v2=0, cote2=0)
    def attendu(jeu, M, c, cote):
        if c in M:
            src = M[c] - GR.CB[jeu]
            return (jeu, src if cote == 1 else cote2(jeu, src))
        return ("Z80", c if cote == 1 else c + 0x500)
    def obtenu(code, cote):
        return resout(code if cote == 1 else code + 0x500)
    for k, iv in J["versions"].items():
        v = int(k, 16); jeu = iv["jeu"]; b = iv["base"]
        M = {int(r["code"], 16): GR.CB[jeu] + int(r["src"], 16) for r in corr
             if r["jeu"] == jeu and r["base"] == b and r["decision"] in ("voix", "cri", "ko")}
        p = int(iv["table_origine"], 16)
        if "table" in iv:
            o = 0x200 + 8 * GR.NENT * iv["table"]
            for e in range(GR.NENT):
                for m in (0, 1):
                    co = struct.unpack_from("<H", d, p - B + 8 * e + 2 * m)[0]
                    cn = struct.unpack_from("<H", blob, o + 8 * e + 2 * m)[0]
                    if e >= iv["entrees"] or co == 0 or not (0x200 <= co <= 0x6FF):
                        if cn != co: err.append("%s table entree %d mot %d modifiee hors table" % (k, e, m))
                        continue
                    for cote in (1, 2):
                        if obtenu(cn, cote) != attendu(jeu, M, co, cote): err.append("%s pas %d.%d %04X cote %d : %s / %s" % (k, e, m, co, cote, obtenu(cn, cote), attendu(jeu, M, co, cote)))
                        else: nb["pas" if cote == 1 else "cote2"] += 1
                for x in (2, 3):
                    if struct.unpack_from("<H", blob, o + 8 * e + 2 * x)[0] != struct.unpack_from("<H", d, p - B + 8 * e + 2 * x)[0]:
                        err.append("%s entree %d mot %d" % (k, e, x))
        bc = T90[38] if v == 0x7E else T90[b]
        for n in (0, 1, 2, 3, 4, 6):
            c = cris_v[v] + n
            for cote in (1, 2):
                if obtenu(c, cote) != attendu(jeu, M, bc + n, cote): err.append("%s cri n=%d cote %d : %s / %s" % (k, n, cote, obtenu(c, cote), attendu(jeu, M, bc + n, cote)))
                else: nb["cris"] += 1
        c2 = T40[38] if v == 0x7E else T40[b]
        c = v2_v[v]
        for cote in (1, 2):
            if obtenu(c, cote) != attendu(jeu, M, c2, cote): err.append("%s $08C274 cote %d" % (k, cote))
            else: nb["v2"] += 1
    ids = list(csv.DictReader(open("<workspace>/work/agent_hyper_index/ids_102.tsv"), delimiter="\t"))
    for row in ids:                      # versions non redirigees : valeurs d'origine (correctif MIPS sans repli)
        v = int(row["id"][1:], 16)
        if "%02X" % v in J["versions"]: continue
        bb = int(row["base"][1:], 16) if row["base"].startswith("$") else 0
        if cris_v[v] != (T90[38] if v == 0x7E else T90[bb]) or v2_v[v] != (T40[38] if v == 0x7E else T40[bb]):
            err.append("%02X : valeur d'origine attendue" % v)
        else: nb["origine"] = nb.get("origine", 0) + 1
    print("controles conformes :", nb, "; erreurs :", len(err))
    for e in err[:30]: print("  ", e)
    return not err


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
