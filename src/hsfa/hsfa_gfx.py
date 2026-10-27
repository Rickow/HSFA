#!/usr/bin/env python3
"""(HANDOFF §116) ROM GRAPHIQUE ETENDUE du banc MAME derive (jeu sfa3hx, mame-fork) : les tuiles 16x16 des banques
du module ABSENTES de la ROM graphique de SFA3 (persos d'Upper, retouches...) sont dedoublonnees, numerotees a partir
du code $40000 (octet $2000000 de la region) et ecrites au FORMAT INTERNE de MAME (apres 'unshuffle', 128 octets par
tuile : ligne r = 8 octets, pixels 0-7 puis 8-15 ; 4 octets par groupe = plans du bit 0 au bit 3 ; pixel x au bit 7-x).
Les tables du banc (banques/f<N>.bin : local -> code) recoivent les nouveaux codes.

Usage : MODULE=ro5 hsfa_gfx.py [N...]   (defaut : banques de carte.txt)   -> <travail>/hsfa_gfx.bin, tables dans <banques>_hx/
IDEMPOTENT : chaque table etendue est recalculee depuis la table d'ORIGINE (<banques>/f<N>.bin), jamais depuis
<banques>_hx/ (deja completee par une execution precedente : relance, il n'y trouvait plus de tuile absente et
recrivait un hsfa_gfx.bin VIDE).
Verification de l'encodage : hsfa_gfx.py --verif <fichier de vidage de la region MAME> (tuiles SFA3)."""
import os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import banques, anthgfx, profils

EXT0 = 0x40000                      # premier code de la ROM etendue (region $2000000)
VIDE = banques.VIDE

def encode(px):
    """tuile 16x16 (valeurs 0-15) -> 128 octets au format interne de MAME"""
    px = np.asarray(px, np.uint8).reshape(16, 16)
    out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8*h:8*h+8]                       # (16 lignes, 8 pixels)
        for b in range(4):                           # octet b = bit b de la valeur du pixel
            bits = (blk >> b) & 1
            out[:, h, b] = np.packbits(bits, axis=1)[:, 0]   # pixel 0 = bit de poids fort
    return out.tobytes()

def verif(dump):
    """compare l'encodage de tuiles SFA3 (cps2rom.decode) au vidage de la region 'gfx' de MAME"""
    import cps2rom
    roms = {s: open(os.path.join(banques.ROMDIR, "sz3.%s" % s), "rb").read() for g in cps2rom.GROUPS for s in g}
    T = cps2rom.decode(roms)
    d = open(dump, "rb").read()
    ok = 0; n = 0
    for c in range(0, min(len(T), len(d) // 128), 997):
        n += 1; ok += encode(T[c]) == d[128*c:128*c+128]
    print("encodage : %d/%d tuiles identiques au vidage MAME" % (ok, n))

def main():
    if sys.argv[1:2] == ["--verif"]: verif(sys.argv[2]); return
    W = profils.P['travail']
    # tables etendues dans un dossier a part (les tables d'origine restent valables pour MAME stock)
    import shutil
    OUT = banques.OUT.rstrip('/') + '_hx'
    # (idempotence) <banques>_hx = copie FRAICHE de <banques> a chaque execution (carte.txt, plan1, f312... a jour si
    # banques.py a ete relance), sauf plan2.bin deja ecrite par hsfa_plans.py ; les tables f<N> sont recalculees ci-dessous
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(banques.OUT)):
        if f == "plan2.bin" and os.path.exists(os.path.join(OUT, f)): continue
        if os.path.isfile(os.path.join(banques.OUT, f)): shutil.copyfile(os.path.join(banques.OUT, f), os.path.join(OUT, f))
    noms = [int(a) for a in sys.argv[1:]] or banques.carte()
    idx = banques.index_rom()
    neuf = {}                                        # contenu -> code etendu
    blob = bytearray()
    base = os.environ.get("HSFA_GFX_BASE")           # (agent_ro9) ROM etendue existante (ex. celle d'Upper) reprise EN TETE :
    if base:                                         # ses tuiles gardent leurs codes, seules les absentes sont ajoutees apres
        b0 = open(base, "rb").read(); b0 = b0[:len(b0) // 128 * 128]
        a = np.unpackbits(np.frombuffer(b0, np.uint8).reshape(-1, 16, 2, 4, 1), axis=-1)   # (N, ligne, moitie, plan, pixel)
        px0 = (a.astype(np.uint8) << np.arange(4, dtype=np.uint8).reshape(1, 1, 1, 4, 1)).sum(3).astype(np.uint8).reshape(-1, 16, 16)
        for k in range(len(px0)): neuf.setdefault(px0[k].tobytes(), EXT0 + k)
        assert all(encode(px0[k]) == b0[128*k:128*k+128] for k in range(0, len(px0), 997)), "decodage de HSFA_GFX_BASE"
        blob += b0; n0 = len(px0)
        print("HSFA_GFX_BASE : %d tuiles reprises (codes $%x-$%x)" % (n0, EXT0, EXT0 + n0 - 1))
    for n in noms:
        src = os.path.join(banques.OUT, "f%d.bin" % n)          # table d'origine (banques.py), pas celle de _hx
        p = os.path.join(OUT, "f%d.bin" % n)
        if not os.path.exists(src): continue
        t = np.fromfile(src, '<u4').copy()
        buf = banques.fichier(n); ajout = 0
        for k, m, px in anthgfx.tiles(buf):
            if k != 1 or px is None or m >= len(t) or t[m] != VIDE: continue
            cle = px.astype(np.uint8).tobytes()
            if cle in idx: t[m] = idx[cle][0]; continue
            if not np.any(px): continue               # tuile vide : rien a afficher
            if cle not in neuf:
                neuf[cle] = EXT0 + len(blob) // 128; blob += encode(px)   # (= EXT0 + len(neuf) sans HSFA_GFX_BASE)
            t[m] = neuf[cle]; ajout += 1
        t.astype('<u4').tofile(p)
        if ajout: print("f%d : %d tuiles vers la ROM etendue" % (n, ajout))
    open(os.path.join(W, "hsfa_gfx.bin"), "wb").write(blob)
    print("ROM etendue : %d tuiles uniques, %.2f Mo (place : %.0f Mo)" % (len(neuf), len(blob) / 2**20, 96))
    if len(blob) > 0x1000000: print("ATTENTION : plus de 16 Mo -> chevauche hsfa_plans.bin en $3000000 (deplacer les plans)")   # (agent_ro9)

if __name__ == "__main__":
    main()
