"""Tables d'animation PAR COUP côté PSP (équivalent de $2B0/$2B4/$2B8/$2BC du module, HSFA 0x48DA78).
Vérité de terrain : pour Ryu, script du module (suite de frames) -> mêmes frames côté PSP (frame_map) -> emplacement
du script PSP ; puis on cherche la table de l'entrée [6] dont l'entrée n donne cet emplacement."""
import os, sys, struct, collections
sys.path.insert(0, "../frames289"); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
from frame_map import build_map
MOD = open(os.environ["ANTHOLOGY_DIR"] + "/decompressed/ro3_usa_prog68k.bin", "rb").read()
X = 0x1F0000
L = lambda a: struct.unpack_from("<I", MOD, a)[0]
NOMS = ["$2B0", "$2B8", "$2B4", "$2BC"]
def mod_tables(cid):
    blk = L(0x48DA78 + 4*cid) - X; out = []
    for k in range(12):
        t = L(blk + 4*k) - X; offs, i, lim = [], 0, 1 << 30
        while t + 2*i < lim:
            o = struct.unpack_from("<H", MOD, t + 2*i)[0]
            if o == 0 or o % 2: break
            offs.append(t + o); lim = min(lim, t + o); i += 1
        out.append((t, offs))
    return out
def mod_script(a):
    fr = []
    for n in range(80):
        ctl, fp = struct.unpack_from("<2I", MOD, a + 20*n)
        fr.append(fp - X)
        if ctl & 0xC000: break                       # bit 15 (reprise) ou bit 14 (fin avec enchaînement)
    return fr
def psp_offsets(b6, r2p, frs):
    """emplacements dans [6] des scripts dont la suite de frames (champ 3 des pas de 10 o) vaut frs"""
    cands = [r2p.get(f) for f in frs]
    if None in cands: return None
    H = struct.unpack_from(f"<{len(b6)//2}H", b6); out = []
    for i in range(0, len(H) - 5*len(cands)):
        if all(H[i + 5*j + 2] == cands[j] for j in range(len(cands))) and H[i + 5*(len(cands)-1)] & 0x8000:
            out.append(2*i)
    return out

BASE = 0x208          # début des données de [6] : l'en-tête (67 u32) donne des décalages RELATIFS à BASE
NOMS_T = {3: "$2B0", 4: "$2B4", 5: "$2B8", 6: "$2BC"}      # S = &T[3] côté moteur PSP (objet + 0x1A0)
def entete(b6): return list(struct.unpack_from("<67I", b6, 0))
def script_psp(b6, v, nmax=80):
    """script de l'animation : pas de 10 o (durée | 0x8000/0x4000 si dernier, drapeau, frame, 1, index jeu de boîtes)
    à partir de BASE + 10 * v"""
    out, o = [], BASE + 10*v
    for n in range(nmax):
        if o + 10*n + 10 > len(b6): return None
        d, fl, fr, one, col = struct.unpack_from("<5H", b6, o + 10*n)
        # mot de contrôle du module = (drapeau << 16) | durée ; fin de script : bit 15 (dernier pas, reprise) ou
        # bit 14 (0x4001/0x4002 : fin avec enchaînement, frame = garde)
        out.append({"ctl": (fl << 16) | d, "flag": fl, "frame": fr, "one": one, "col": col})
        if d & 0xC000: return out
    return None
def tables_psp(b6):
    """-> {'$2B0': [n° de pas…], …} : tables u32 terminées par 0xFFFFFFFF, emplacements = T[3..6] + BASE"""
    T = entete(b6); out = {}
    for k, nom in NOMS_T.items():
        a = T[k] + BASE; vals = []; fin = T[k + 1] + BASE      # borne : début de la table suivante (Yun : pas de 0xFFFFFFFF)
        while a + 4 <= min(len(b6), fin):
            v = struct.unpack_from("<I", b6, a)[0]
            if v == 0xFFFFFFFF: break
            vals.append(v); a += 4
        out[nom] = vals
    out["_boites"] = T[7] + BASE
    return out

def animations(pl, remap=None):
    """tables par coup d'un perso PSP, au format du module : {table: [ {n, pas_psp, steps:[{ctl, frame, A, B, C}]} ]}
    (frame = index de frames.json, renuméroté pour Ingrid via remap ; ctl = mot de contrôle du module,
    (drapeau << 16) | durée, bits 15/14 = fin) ; reprise = index du pas où reprendre après un dernier pas à bit 15
    (écart signé en +6 du pas PSP, en pas : 0 = le dernier pas se répète)"""
    b6 = split(open(os.path.join(paths.pac_dir(), f"{pl}_e.pac"), "rb").read())[6][1]
    TP = tables_psp(b6); bx = TP["_boites"]; out = {}
    for nom in ("$2B0", "$2B4", "$2B8", "$2BC"):
        L = []
        for n, v in enumerate(TP[nom]):
            sc = script_psp(b6, v)
            steps = None; reprise = None
            if sc and sc[-1]["ctl"] & 0x8000:              # écart signé en +6 du dernier pas (validé : 166/166 vs module)
                last = BASE + 10 * v + 10 * (len(sc) - 1)
                reprise = len(sc) - 1 + struct.unpack_from("<h", b6, last + 6)[0]
            if sc:
                steps = []
                for st in sc:
                    a, b, c = struct.unpack_from("<3I", b6, bx + 12*st["col"]) if bx + 12*st["col"] + 12 <= len(b6) else (None,)*3
                    fr = remap.get(st["frame"], st["frame"]) if remap else st["frame"]
                    steps.append({"ctl": st["ctl"], "frame": fr, "A": a, "B": b, "C": c})
            L.append({"n": n, "pas_psp": v, "steps": steps, "reprise": reprise})
        out[nom] = L
    return out

# Yun : le gabarit de 39 mots que son init recopie dans objet+0x1A0 (EBOOT 0x2AD6DC) porte DÉJÀ les 4 tables
# (pointeurs relogés vers des tables de pointeurs de scripts, scripts dans l'EBOOT) ; chez les autres persos ces 4 mots
# sont à 0 et viennent de [6]. Jeux de boîtes de Yun : [6] + 0x208, 1 203 entrées de 12 o (jusqu'à T[3] + 0x208).
GABARIT_YUN = 0x2AD6DC
def animations_yun():
    from relocs import img
    from charcode2 import P
    b6 = split(open(os.path.join(paths.pac_dir(), "pl28_e.pac"), "rb").read())[6][1]
    bx, nbx = BASE, (entete(b6)[3] + BASE - BASE) // 12
    tabs = [P[GABARIT_YUN + 4*k] for k in range(4)]                  # $2B0, $2B4, $2B8, $2BC
    starts = sorted(tabs)
    out = {}
    for nom, t in zip(("$2B0", "$2B4", "$2B8", "$2BC"), tabs):
        L, a = [], t
        nxt = min([s for s in starts if s > t] + [t + 4*256])
        while a < nxt and a in P:
            s, steps = P[a], []; reprise = None
            for n in range(80):
                d, fl, fr, one, col = struct.unpack_from("<5H", img, s + 10*n)
                if d & 0x8000: reprise = n + struct.unpack_from("<h", img, s + 10*n + 6)[0]
                A, B, C = struct.unpack_from("<3I", b6, bx + 12*col) if col < nbx else (None,)*3
                steps.append({"ctl": (fl << 16) | d, "frame": fr, "A": A, "B": B, "C": C})
                if d & 0xC000: break
            else: steps = None
            L.append({"n": len(L), "eboot": s, "steps": steps, "reprise": reprise}); a += 4
        out[nom] = L
    return out
