"""Scripts de fin : lecture du format ARCADE (ROM sfa3ud, mots gros-boutistes) et PSP (endXX_e.pac, entrée 0x20000,
mots petit-boutistes). Instruction = [attente][opword][args], nb d'args = opword & 0xF ; classe = (opword >> 4) & 7 ;
classe 0 : sous-opcode = (opword >> 8) & 0xF (quartet haut de l'octet haut -> -$5103(A5)).
Usage : python3 script_fin.py arcade <n° fin hex> | psp <XX>"""
import sys, os, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
ROMD = os.path.expanduser("~/.cache/sfa3max/sfa3ud_donnees.bin")
SRC = os.path.expanduser("~/.cache/sfa3max/data/textes")
T_SCRIPTS = 0x26DCC

NOMS0 = {0x0: "fin?", 0x1: "scene", 0x2: "op2", 0x3: "op3", 0x4: "op4", 0x5: "op5", 0x6: "plans", 0x7: "op7",
         0x8: "op8", 0x9: "palettes", 0xA: "opA", 0xB: "opB"}


def lire(W, maxn=100000):
    out = []; i = 0
    while i + 1 < len(W) and len(out) < maxn:
        att, op = W[i], W[i + 1]; n = op & 0xF
        out.append((i * 2, att, op, tuple(W[i + 2:i + 2 + n]))); i += 2 + n
    return out


def nom(op):
    cl = (op >> 4) & 7
    if cl == 0: return NOMS0.get((op >> 8) & 0xF, "?")
    if op & 0xFF == 0x34: return "texte"
    return "cl%d" % cl


def arcade(fin, nmots=6000):
    b = open(ROMD, "rb").read()
    a = struct.unpack_from(">I", b, T_SCRIPTS + 4 * fin)[0]
    return a, lire(struct.unpack_from(">%dH" % nmots, b, a))


def psp(n):
    from plpac import split
    E = split(open(os.path.join(SRC, "end%s_e.pac" % n), "rb").read())
    s = [d for t, d in E if t == 0x20000][0]
    return lire(struct.unpack("<%dH" % (len(s) // 2), s))


if __name__ == "__main__":
    if sys.argv[1] == "arcade":
        a, ins = arcade(int(sys.argv[2], 16)); print("script en $%06X" % a)
    else:
        a, ins = 0, psp(sys.argv[2])
    for off, att, op, args in ins:
        print("%06x att=%04x op=%04x %-8s %s" % (a + off, att, op, nom(op), " ".join("%04x" % x for x in args)))
