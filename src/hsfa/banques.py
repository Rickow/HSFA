#!/usr/bin/env python3
"""BANQUES DE SPRITES DE L'ANTHOLOGY -> codes de tuiles CPS2 (HANDOFF §82).

Le moteur de sprites natif du portage lit, pour chaque objet, l'EMPLACEMENT de banque dans les bits 13-15
du mot Y (et non X : X >> 13 reste la priorite, 7 = objet ignore) et un numero de tuile LOCAL a la banque
(conteneur X_DATA charge dans l'emplacement). Pour le banc MAME (ROM graphique d'origine), chaque tuile de
banque est retrouvee par son CONTENU dans la ROM CPS2 : table locale -> code global (18 bits).

Sortie : work/mame/banques/f<N>.bin = u32 petit-boutiste par tuile locale (0xFFFFFFFF = vide ou absente),
plus une statistique de « continuite » (code(l+1) == code(l)+1 : les blocs multi-tuiles restent justes).
Usage : banques.py N [N...]   (python du venv : numpy)
"""
import os, sys, csv, struct
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import anthgfx, cps2rom

XDATA = os.environ.get("XDATA", "<workspace>/work/xdata/X_DATA.BIN")
MANIF = "<workspace>/anthology_extract/manifest.csv"
ROMDIR = "<workspace>/work/mame/roms/sfa3ud"
OUT = "<workspace>/work/mame/banques"
VIDE = 0xFFFFFFFF
# (HANDOFF §115) module : Upper (ro5) = groupe X_DATA decale (communs e351, decor e353, persos e355-e386, table
# perso -> banque 0x628320 sur 40 ID) ; tables ecrites dans work/mame_ro5/banques (toujours contre la ROM SFA3)
MODULE = os.environ.get("MODULE", "ro3")
MOD = {'ro3': dict(out=OUT, perso=0x59C0B0, n=0x20, commun=254, decor=256, n_site=2, b32=312),
       'ro5': dict(out="<workspace>/work/mame_ro5/banques", perso=0x628320, n=0x28, commun=351, decor=353,
                   n_site=3, b32=525),   # (HANDOFF §119) plan 32x32 d'Upper = e525 (e312 + 504 tuiles)
       # (agent_ro9, BANQUES-ET-MODES-ro9.md) Hyper : descripteur [[0x1DC040]] du vidage EE d'Hyper = communs e545
       # (emplacement 0), decor e546 (emplacement 1, MWo3), 32x32 e548 (emplacement 5) ; table perso -> banque 0x5AF1B0
       # u16 x 128 indexee par $102 (Upper 355-386, SFA1 208-220, SFA2 229-248) ; aucun chargeur natif d'animation
       'ro9': dict(out="<workspace>/work/mame_ro9/banques", perso=0x5AF1B0, n=0x80, commun=545, decor=546,
                   n_site=0, b32=548)}[MODULE]
OUT = MOD['out']

_INDEX = None
def index_rom():
    """contenu brut de chaque tuile 16x16 de la ROM -> premier code (dictionnaire d'octets)"""
    global _INDEX
    if _INDEX is None:
        roms = {s: open(os.path.join(ROMDIR, "sz3.%s" % s), "rb").read() for g in cps2rom.GROUPS for s in g}
        T = cps2rom.decode(roms)                       # (262144, 16, 16) valeurs brutes
        _INDEX = {}
        for c in range(len(T)):                        # contenu -> TOUS les codes (tuiles repetees)
            _INDEX.setdefault(T[c].tobytes(), []).append(c)
    return _INDEX

def fichier(n):
    man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(MANIF))}
    o, s = man[n]
    with open(XDATA, "rb") as f:
        f.seek(o); return f.read(s)

def table(n):
    buf = fichier(n)
    idx = index_rom()
    recs = anthgfx.records(buf)
    k16 = [r for r in recs if r[0] == 1]
    if not k16: return None, "pas de tuiles 16x16 : %s" % recs
    _, first, count, _ = k16[0]
    t = np.full(first + count, VIDE, np.uint32)
    cand = {}
    for k, m, px in anthgfx.tiles(buf):
        if k != 1 or px is None: continue
        c = idx.get(px.astype(np.uint8).tobytes())
        if c: cand[m] = c
    # parmi les codes de meme contenu, celui qui PROLONGE la suite (blocs multi-tuiles : code + x + 16y)
    prev = None
    for m in range(first, first + count):
        c = cand.get(m)
        if c is None: prev = None; continue
        if prev is not None and prev + 1 in c: v = prev + 1
        else:
            nxt = cand.get(m + 1)
            v = next((x for x in c if nxt and x + 1 in nxt), c[0])
        t[m] = v; prev = v
    return t, None

_INDEX32 = None
def table32(n):
    """conteneur de tuiles 32x32 (e312 : plan scroll3 du portage, emplacement 5) -> indice 32x32 dans la ROM
    (4 tuiles 16x16 consecutives = 64 lignes de 16 px). Ecrit f<N>.bin comme les banques 16x16."""
    global _INDEX32
    if _INDEX32 is None:
        roms = {s: open(os.path.join(ROMDIR, "sz3.%s" % s), "rb").read() for g in cps2rom.GROUPS for s in g}
        S = cps2rom.decode(roms).reshape(-1, 16)
        _INDEX32 = {}
        for m in range(S.shape[0] // 64):
            _INDEX32.setdefault(S[64*m:64*m+64].tobytes(), []).append(m)
    buf = fichier(n)
    k32 = [r for r in anthgfx.records(buf) if r[0] == 2]
    _, first, count, _ = k32[0]
    t = np.full(first + count, VIDE, np.uint32)
    for k, m, px in anthgfx.tiles(buf):
        if k == 2 and px is not None:
            c = _INDEX32.get(anthgfx.to_slots(2, px).astype(np.uint8).tobytes())
            if c: t[m] = c[0]
    return t

# (agent_build, 2026-10-10) HSFA_PLANS_FENETRE=1 : parmi les indices ROM de meme contenu, preferer ceux de la FENETRE
# que le banc honore (banc_plans.lua : plan1 = $20000-$2FFFF en unites 8x8, plan2 = $10000-$1FFFF ; hors fenetre, le
# banc affiche le code BRUT). Sans effet par defaut (tables identiques a l'octet). Utile quand la ROM graphique n'est
# pas celle de l'arcade (ROM reconstruite depuis l'ISO : tuiles de sprites du quart 0 rangees dans un autre ordre, la
# regle de continuite choisissait parfois une copie du quart 0, hors fenetre).
FENETRE = os.environ.get("HSFA_PLANS_FENETRE") == "1"

def plans256():
    """memoire de tuiles de DECOR du portage (e256 decompresse MWo3 = ctx+$34, lineaire 4 bpp) :
    scroll1 = tuiles 8x8 (indice m -> 0x20 o), scroll2 = tuiles 16x16 (indice c -> 0x80 o, 16 lignes de 16 px).
    Tables locale -> indice ROM (8x8 : unites de 8 lignes, moitie gauche ; 16x16) ; code MAME = indice - $20000
    (scroll1) ou - $10000 (scroll2). Ecrit plan1.bin et plan2.bin."""
    sys.path.insert(0, "<workspace>/anthology_extract")
    from mwo3_codec import decompress
    x = np.frombuffer(bytes(decompress(fichier(MOD['decor']))), np.uint8)
    px = np.stack([x & 0xF, x >> 4], -1).reshape(-1)
    roms = {s: open(os.path.join(ROMDIR, "sz3.%s" % s), "rb").read() for g in cps2rom.GROUPS for s in g}
    S = cps2rom.decode(roms).reshape(-1, 16)
    for nom, w, unite in (("plan1", 8, 8), ("plan2", 16, 16)):
        idx = {}
        for k in range(S.shape[0] // unite):
            blk = S[unite*k:unite*k+unite, :w]
            idx.setdefault(blk.tobytes(), []).append(k)
        n = len(px) // (w * w)
        t = np.full(n, VIDE, np.uint32); prev = None
        cand = [idx.get(px[m*w*w:(m+1)*w*w].reshape(w, w).astype(np.uint8).tobytes()) for m in range(n)]
        if FENETRE:                                    # candidats DANS la fenetre du plan d'abord (sinon tous)
            deb = 0x20000 if nom == "plan1" else 0x10000
            cand = [([y for y in c if deb <= y <= deb + 0xFFFF] or c) if c else c for c in cand]
        for m in range(n):
            c = cand[m]
            if not c: prev = None; continue
            if prev is not None and prev + 1 in c: v = prev + 1
            else:
                nxt = cand[m + 1] if m + 1 < n else None
                v = next((y for y in c if nxt and y + 1 in nxt), c[0])
            t[m] = v; prev = v
        t.astype('<u4').tofile(os.path.join(OUT, nom + ".bin"))
        print("%s : %d tuiles, %d trouvees" % (nom, n, int((t != VIDE).sum())))

def carte():
    """banques/carte.txt pour le banc Lua : 'perso id fichier' (table $59C0B0, emplacements 2/3 = J1/J2) et
    'anim ptr fichier' (pointeur $BE48 tel que rangé, moitiés échangées -> fichier graphique de la paire,
    emplacement 4). Rend la liste des fichiers de banque utiles."""
    import census, assets_natifs as AN
    buf = open(census.RO3, "rb").read(); B = 0x1F0000
    persos = [struct.unpack_from('<h', buf, MOD['perso'] - B + 2*i)[0] for i in range(MOD['n'])]
    _, va = AN.build(buf)
    paires = [struct.unpack_from('<hh', buf, AN.T_SITE - B + 4*i) for i in range(MOD['n_site'])] + \
             [struct.unpack_from('<hh', buf, AN.T_PERSO - B + 4*i) for i in range(AN.N_PERSO)]
    if AN.T_FIN:                                       # (HANDOFF §122) Upper : chargeur de fin (gfx 391-418)
        paires += [struct.unpack_from('<hh', buf, AN.T_FIN - B + 4*i) for i in range(AN.N_FIN)]
    lignes = ["perso %d %d" % (i, f) for i, f in enumerate(persos)]
    gfx = set()
    for g, a in paires:
        if g and a in va: lignes.append("anim %d %d" % (AN.swapped(va[a]), g)); gfx.add(g)
    open(os.path.join(OUT, "carte.txt"), "w").write("\n".join(lignes) + "\n")
    return sorted({MOD['commun']} | set(persos) | gfx)

def main():
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if args == ["plans"]: plans256(); return
    if args == ["tout"]: args = [str(n) for n in carte()]
    for a in args:
        n = int(a, 0)
        if n == MOD['b32']:                            # plan scroll3 (32x32) : toujours ecrit sous le nom f312.bin
            t = table32(n); t.astype('<u4').tofile(os.path.join(OUT, "f312.bin"))
            print("f312 (32x32, e%d) : %d tuiles, %d trouvees" % (n, len(t), int((t != VIDE).sum()))); continue
        t, err = table(n)
        if t is None: print("f%d : %s" % (n, err)); continue
        t.astype('<u4').tofile(os.path.join(OUT, "f%d.bin" % n))
        ok = t != VIDE
        suite = int(np.sum((t[1:] == t[:-1] + 1) & ok[1:] & ok[:-1]))
        print("f%d : %d tuiles, %d trouvees, %d vides/absentes, continuite %d/%d" %
              (n, len(t), int(ok.sum()), int((~ok).sum()), suite, int((ok[1:] & ok[:-1]).sum())))

if __name__ == "__main__":
    main()
