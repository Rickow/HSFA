"""Scripts d'IA des persos MAX : PSP -> format d'Upper (2026-10-27, N19 de work/echanges/MAX.md, max/notes/ia-psp-arcade.md).
L'interpréteur IA de la PSP est celui de l'arcade (version Upper) : on CONVERTIT les scripts, sans nouveau code.
PSP : gabarit du perso (39 mots, recopié en objet + 0x1A0) ; mots 12-15 = les 4 tables de scripts (créneaux +0x200-0x20C) :
  w12 : 4 pointeurs de script                       <-> Upper T0 0x74C0D8[id] : 4 décalages (mots) + scripts
  w13 : 4 paires (table d'aléa, table de scripts)   <-> Upper T1 0x74C178[id] : 4 décalages -> sous-blocs
  w14 : n paires, selon l'adversaire                 <-> Upper T2 0x74C218[id] : n décalages -> sous-blocs
  w15 : 8 pointeurs de script                       <-> Upper T3 0x74C2B8[id] : 8 décalages + scripts
Sous-bloc d'Upper : 0x60 octets d'aléa (tels quels, comme la PSP), puis un décalage (mot, relatif au sous-bloc) par script
(nombre = plus grand octet d'aléa + 1), puis les scripts. Décalages d'un bloc / sous-bloc : relatifs à son début.
Mots de script : PSP 0xCCSS -> Upper (2c)<<8 | 2s (c = CC & 0xF), FFss -> FF(2s), 7600/7601/7602 -> 0C00/0C02/0C04,
condition k du SI -> 2k, en-tête de script 0/1/2 -> 0/2/4 ; opérandes inchangés (nombre par commande : ia-psp-arcade.md).
Contrôle : --natifs convertit les 29 natifs de la PSP et compare octet à octet aux blocs d'Upper (ro5_usa_prog68k.bin).
Sortie : <racine SFA3MAX_CACHE>/converti/ia/ia_max.s — DISPOSITION IMAGE (mots tels quels ; tables d'aléa en dc.b dans
l'ordre des octets de la PSP, comme les tables natives d'Upper) ; étiquettes IA_T0_26 … IA_T3_2E à poser en T0-T3[id].
Usage : python ia_max.py [--natifs]"""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
VA, RB = 0x74, 0x1F0000
MAX = [("Eagle", 0x26, 0x2A3198), ("Maki", 0x27, 0x2A6268), ("Yun", 0x2D, 0x2AD6DC), ("Ingrid", 0x2E, 0x2B1EE0)]
T_UPPER = (0x74C0D8, 0x74C178, 0x74C218, 0x74C2B8)
# opérandes (mots) par commande, d'après ia-psp-arcade.md §3 / §4
OP_CLASSE0 = [1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 2, 2, 0, 0, 0, 0, 0]
OP_CLASSE1 = [1, 1, 1, 1, 1, 2, 2, 2]
OP_COND = [1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
OP_CLASSE9 = [2, 2, 0, 0]
DOUBLE_OPS = {0x0501, 0x0B00, 0x0203}   # 1er opérande = paire d'indices : chaque octet × 2 (relevé sur les natifs ;
                                        # 0500, 0200 : inchangés)


class Erreur(Exception): pass


def convertir_script(W):
    """W = mots PSP d'un script (en-tête compris) -> mots Upper"""
    if not W: return []
    if W[0] > 2: raise Erreur("en-tête %04x" % W[0])
    out = [2 * W[0]]; i = 1
    while i < len(W):
        w = W[i]; hi, s = w >> 8, w & 0xFF; c = hi & 0xF; i += 1
        if hi == 0xFF: out.append(0xFF00 | 2 * s); continue
        if w in (0x7600, 0x7601, 0x7602):
            out.append(0x0C00 + 2 * (w - 0x7600))
            if w == 0x7600:
                k = W[i]; i += 1
                if k >= len(OP_COND): raise Erreur("condition %d" % k)
                out.append(2 * k); n = OP_COND[k]; out += W[i:i + n]; i += n
            continue
        n = {0: lambda: OP_CLASSE0[s], 1: lambda: OP_CLASSE1[s], 2: lambda: 3, 3: lambda: 1, 4: lambda: 1, 5: lambda: 1,
             7: lambda: 0, 8: lambda: 0, 9: lambda: OP_CLASSE9[s], 0xB: lambda: 1}.get(c)
        if n is None or (c in (0, 1, 9) and s >= {0: 21, 1: 8, 9: 4}[c]): raise Erreur("commande %04x" % w)
        n = n()
        out.append(((2 * c) << 8) | (2 * s & 0xFF)); ops = W[i:i + n]; i += n
        if w in DOUBLE_OPS and ops: ops = [((2 * (ops[0] >> 8) & 0xFF) << 8) | (2 * ops[0] & 0xFF)] + ops[1:]
        out += ops
    if i != len(W): raise Erreur("débordement")
    return out


class Perso:
    def __init__(s, E, g):
        s.E = E; u = lambda o: struct.unpack_from("<I", E, VA + o)[0]; s.u = u
        s.w = [u(g + 4 * k) for k in (12, 13, 14, 15)]
        s.t0 = [u(s.w[0] + 4 * i) for i in range(4)]
        s.t3 = []                                    # jusqu'à 8 pointeurs valides (certains natifs en ont moins)
        for i in range(8):
            v = u(s.w[3] + 4 * i)
            if not (0x200000 < v < 0x2C0000 and v % 2 == 0): break
            s.t3.append(v)
        npaires = (s.w[3] - s.w[2]) // 8 if 0 < s.w[3] - s.w[2] <= 8 * 16 else None
        if npaires is None: raise Erreur("w14 : nombre de paires indéterminé")
        s.t1 = [s.paire(s.w[1] + 8 * i) for i in range(4)]
        s.t2 = [s.paire(s.w[2] + 8 * i) for i in range(npaires)]
        # bornes des scripts : débuts connus + adresses des tables (les scripts sont rangés bout à bout)
        debuts = set(s.t0) | set(s.t3) | {p for _, _, sc in s.t1 + s.t2 for p in sc}
        tables = {s.w[0], s.w[3], s.w[1], s.w[2]} | {a for r, t, _ in s.t1 + s.t2 for a in (r, t)}
        s.bornes = sorted(debuts | tables)
    def paire(s, a):
        r, t = s.u(a), s.u(a + 4)
        alea = s.E[VA + r:VA + r + 0x60]; n = max(alea) + 1
        return r, t, [s.u(t + 4 * i) for i in range(n)]
    def mots(s, p):
        fin = next(b for b in s.bornes if b > p)
        return list(struct.unpack_from("<%dH" % ((fin - p) // 2), s.E, VA + p))


def bloc_scripts(P, ptrs, base_tete):
    """décalages + scripts (dédoublonnés), décalages relatifs au début du bloc (base_tete = octets avant les décalages)"""
    uniq = list(dict.fromkeys(ptrs)); code = {p: convertir_script(P.mots(p)) for p in uniq}
    off, pos = {}, base_tete + 2 * len(ptrs)
    for p in uniq: off[p] = pos; pos += 2 * len(code[p])
    return [off[p] for p in ptrs], [w for p in uniq for w in code[p]]


def tables_upper(P):
    """-> 4 blocs, chacun = liste d'éléments ('w', mot) / ('b', octets)"""
    o, sc = bloc_scripts(P, P.t0, 0); T0 = [("w", x) for x in o + sc]
    o, sc = bloc_scripts(P, P.t3, 0); T3 = [("w", x) for x in o + sc]
    def bloc_paires(paires):
        subs = []
        for r, t, ptrs in paires:
            o, sc = bloc_scripts(P, ptrs, 0x60)
            subs.append([("b", P.E[VA + r:VA + r + 0x60])] + [("w", x) for x in o + sc])
        taille = lambda b: sum(2 if k == "w" else len(v) for k, v in b)
        pos = 2 * len(subs); offs = []
        for b in subs: offs.append(pos); pos += taille(b)
        return [("w", x) for x in offs] + [e for b in subs for e in b]
    return [T0, bloc_paires(P.t1), bloc_paires(P.t2), T3]


def octets_image(bloc):
    """représentation du fichier d'Upper : mots petit-boutistes, octets d'aléa tels quels"""
    return b"".join(struct.pack("<H", v) if k == "w" else v for k, v in bloc)


def controle_natifs(E):
    """compare le CONTENU atteint par chaque entrée (scripts convertis, tables d'aléa) aux tables natives d'Upper ;
    la mise en page peut différer (Upper partage des scripts entre sous-blocs)"""
    UP = open(os.path.join(paths.anthology(), "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
    uw = lambda a: struct.unpack_from("<H", UP, a - RB)[0]
    ul = lambda a: (uw(a + 2) << 16) | uw(a)
    def entrees(P, idn):
        """-> [(table d'aléa PSP ou None, alea Upper, [(script PSP, adresse Upper)])] pour T0-T3"""
        out = []
        for k in range(4):
            base = ul(T_UPPER[k] + 4 * idn)
            if k in (0, 3):
                ptrs = P.t0 if k == 0 else P.t3
                out.append((None, None, [(p, base + uw(base + 2 * i)) for i, p in enumerate(ptrs)]))
            else:
                for j, (r, t, ptrs) in enumerate(P.t1 if k == 1 else P.t2):
                    S = base + uw(base + 2 * j)
                    out.append((E[VA + r:VA + r + 0x60], UP[S - RB:S - RB + 0x60],
                                [(p, S + uw(S + 0x60 + 2 * i)) for i, p in enumerate(ptrs)]))
        return out
    def ecarts(P, idn):
        n = 0
        for ra, ru, scr in entrees(P, idn):
            if ra is not None and ra != ru: n += 1
            for p, a in scr:
                C = convertir_script(P.mots(p))
                if [uw(a + 2 * i) for i in range(len(C))] != C: n += 1
        return n
    gab = [a for a in range(0x200000, 0x2C0000, 4) if struct.unpack_from("<I", E, VA + a + 124)[0] == 0x5AEFC
           and all(0x200000 < struct.unpack_from("<I", E, VA + a + o)[0] < 0x2C0000 for o in (48, 52))]
    gab = [g for g in gab if g not in [m[2] for m in MAX]]
    ok = 0
    for g in gab:
        try:
            P = Perso(E, g); res = []
            for idn in range(0x26):
                try: res.append((ecarts(P, idn), idn))
                except Exception: pass
            n, idn = min(res)
        except (Erreur, struct.error, StopIteration, ValueError) as x: print("  gabarit 0x%06X : %s" % (g, x)); continue
        ok += n == 0
        print("  gabarit 0x%06X = ID $%02X : %s" % (g, idn, "IDENTIQUE" if n == 0 else "%d entrées / scripts différents" % n))
    print("natifs identiques en contenu : %d / %d" % (ok, len(gab)))


def main():
    E = open(paths.eboot(), "rb").read()
    if "--natifs" in sys.argv: return controle_natifs(E)
    L = ["; scripts d'IA des persos MAX au format d'Upper (tables T0 0x74C0D8, T1 0x74C178, T2 0x74C218, T3 0x74C2B8, par ID)",
         "; généré par max/outils/convert/ia_max.py depuis les scripts PSP (gabarit, mots 12-15) — DISPOSITION IMAGE :",
         "; mots tels quels ; tables d'aléa (dc.b) dans l'ordre des octets de la PSP, comme les tables natives d'Upper", ""]
    for nom, uid, g in MAX:
        P = Perso(E, g)
        L.append("; ---- %s (ID Upper $%02X ; gabarit PSP 0x%06X ; T2 : %d entrées selon l'adversaire)" % (nom, uid, g, len(P.t2)))
        for k, bloc in enumerate(tables_upper(P)):
            L += ["        even", "IA_T%d_%02X:" % (k, uid)]
            mots = []
            def vider():
                for i in range(0, len(mots), 12): L.append("        dc.w    " + ", ".join("$%04X" % x for x in mots[i:i + 12]))
                mots.clear()
            for t, v in bloc:
                if t == "w": mots.append(v)
                else:
                    vider()
                    for i in range(0, len(v), 16): L.append("        dc.b    " + ", ".join("$%02X" % x for x in v[i:i + 16]))
            vider()
        L.append("")
    d = os.path.join(paths.CACHE, "converti", "ia"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "ia_max.s"), "w").write("\n".join(L))
    print("écrit", os.path.join(d, "ia_max.s"))


if __name__ == "__main__":
    main()
