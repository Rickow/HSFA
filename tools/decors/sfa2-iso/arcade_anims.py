#!/usr/bin/env python3
"""arcade_anims.py (côté ORACLE, local) : lecture des tables d'animation du programme arcade sfa2u (vidé par MAME,
carto_sfa2/dump/sfa2u). Repère toutes les racines de tables passées aux moteurs génériques d'animation (init sprites
$18CCE, palettes $18D00, tuiles s1 $18D84 / s2 $18E02 / s3 $18E7E) dans le désassemblage, parcourt leurs animations et
construit l'index « adresse de cadre -> (racine, animation, n° de cadre) ». Aucune donnée écrite hors de outils/ :
ce module ne sert qu'à localiser (adresses) et à contrôler.
Format (lu dans le code 68K, RAPPORT §5) : table = décalages (mots) relatifs à la racine, un par animation ; cadre =
+0 durée en tics (mot), +2 drapeaux (bit 7 : fin, le long qui suit le cadre = adresse de reprise), +4 pointeur ;
taille 16 o (sprites, tuiles ; tuiles : +$C décalage X, +$E décalage Y) ou 8 o (palettes)."""
import re, struct, os, sys, json, collections
DUMP = os.environ.get("SFA2U", "<workspace>/work/carto_sfa2/dump/sfa2u")
D = open(os.path.join(DUMP, "prog_donnees.bin"), "rb").read()
O = open(os.path.join(DUMP, "prog_opcodes.bin"), "rb").read()
w = lambda a, B=D: struct.unpack_from(">H", B, a)[0]
sw = lambda a, B=D: struct.unpack_from(">h", B, a)[0]
l = lambda a, B=D: struct.unpack_from(">I", B, a)[0]
ENGINES = {0x18CCE: "sprite", 0x18D00: "palette", 0x18D84: "tuiles_s1", 0x18E02: "tuiles_s2", 0x18E7E: "tuiles_s3"}
FS = {"sprite": 16, "palette": 8, "tuiles_s1": 16, "tuiles_s2": 16, "tuiles_s3": 16}
BANQUES_PAL = [0x29C100, 0x2A8A20, 0x2A97E0, 0x2AB6E0]   # table $18D58 (sélecteur 0/4/8/12)

def walk(T, i, fs):
    """cadres de l'animation i de la racine T : [(adresse, durée, drapeaux, pointeur)], indice de reprise"""
    a = T + w(T + 2 * i); seq = []; vus = {}
    for _ in range(4096):
        if a in vus: return seq, vus[a]
        if a < 0 or a + fs > len(D): return None, None
        vus[a] = len(seq); f = D[a + 2]; seq.append((a, w(a), f, l(a + 4) & 0xFFFFFF)); a += fs
        if w(a - fs) == 0: return seq, -1          # durée 0 : cadre tenu indéfiniment (65 536 tics)
        if f & 0x80:
            a = l(a) & 0xFFFFFF
            return seq, vus.get(a)
    return None, None

def anims_valides(T, fs, maxi=256):
    """animations : décalages pairs > 0 jusqu'au début des données (plus petit décalage) ; on garde celles dont le
    parcours se referme (boucle, ou cadre de durée 0)"""
    n = 0; mini = 1 << 30; ok = []
    while n < maxi and 2 * n < mini:
        o = w(T + 2 * n)
        if o == 0 or o & 1 or o > 0x8000: n += 1; continue
        mini = min(mini, o)
        s, b = walk(T, n, fs)
        if s is not None: ok.append(n)          # b = None : reprise dans une autre animation de la table
        n += 1
    return ok

def racines_statiques(dasm=os.path.join(DUMP, "dasm.txt")):
    """{racine: (moteur, [sites d'appel])} : lea/movea absolus ou PC-relatifs juste avant un appel d'init"""
    L = open(dasm).read().split("\n"); R = collections.defaultdict(lambda: [None, []])
    for i, li in enumerate(L):
        m = re.search(r"(jmp|jsr)\s+\$(18cce|18d00|18d84|18e02|18e7e)\.l", li)
        if not m: continue
        eng = ENGINES[int(m.group(2), 16)]
        for j in range(i - 1, i - 15, -1):
            mm = re.search(r"lea\s+\$([0-9a-f]+)\.l, A0", L[j]) or re.search(r"movea\.l\s+#\$([0-9a-f]+), A0", L[j]) \
                or re.search(r"lea\s+\(\$([0-9a-f]+),PC\), A0", L[j])
            if mm:
                r = int(mm.group(1), 16); R[r][0] = eng; R[r][1].append(int(li[:6], 16)); break
            if re.search(r"\b(rts|bra|jmp)\b", L[j]): break
    return R

# tables indirectes lues dans le code (PC-relatives, espace opcodes)
def racines_indirectes():
    R = {}
    # classe 0 (pool A) : longs (anim << 24 | racine) en $5B3EE, sous-type = indice
    for s in range(40):
        v = l(0x5B3EE + 4 * s, O); r = v & 0xFFFFFF
        if not (0x200000 <= r < 0x300000): break
        R.setdefault(r, ("sprite", "classe 0 s%d anim %d" % (s, v >> 24)))
    # classe 1 : tuiles s1 / s2 / s3 ($5B4E2, sélecteur +$E = 4/8/12)
    for k, e in enumerate(("tuiles_s1", "tuiles_s2", "tuiles_s3")):
        R[l(0x5B4E2 + 4 * k, O)] = (e, "classe 1, +$E = %d" % (4 * k + 4))
    return R

def index_cadres(racines):
    """{adresse de cadre: (racine, anim, n°)} pour toutes les racines {r: moteur}"""
    I = {}; info = {}
    for r, eng in racines.items():
        fs = FS[eng]; A = anims_valides(r, fs); info[r] = (eng, len(A))
        for i in A:
            s, b = walk(r, i, fs)
            for k, fr in enumerate(s): I.setdefault(fr[0], (r, i, k))
    return I, info

def bloc_tuiles(p):
    """bloc de tuiles : mot ignoré, lignes - 1, colonnes - 1, puis (code, attr) colonne par colonne"""
    nl, nc = w(p + 2) + 1, w(p + 4) + 1
    return dict(lignes=nl, colonnes=nc, mot0=w(p), paires=[(w(p + 6 + 4 * k), w(p + 8 + 4 * k)) for k in range(nl * nc)])

def entrees_palette(p):
    """entrées de 6 o : destination ($90C000 + d), banque (0/4/8/12, table $18D58), source (& $FFE0 dans la banque ;
    bit 0 = DERNIÈRE entrée : « btst #0 ; beq » en $18D50) ; 16 couleurs copiées, luminosité de la destination gardée"""
    E = []
    for _ in range(64):
        d, b, s = w(p), w(p + 2), w(p + 4); E.append((d, b, s)); p += 6
        if s & 1: return E
    return E

if __name__ == "__main__":
    S = racines_statiques(); I = racines_indirectes()
    tout = {r: v[0] for r, v in S.items()}
    for r, (e, _) in I.items(): tout.setdefault(r, e)
    idx, info = index_cadres(tout)
    print(len(tout), "racines,", len(idx), "cadres")
    for r in sorted(info): print("$%06X %-10s %3d anims  appels %s" % (r, info[r][0], info[r][1], " ".join("$%X" % x for x in S.get(r, [None, []])[1][:6])))
