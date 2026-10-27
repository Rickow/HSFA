#!/usr/bin/env python3
"""
SFA Anthology (PS2, SLUS-21317) — Widescreen 16:9 patcher
==========================================================
Patche l'ISO USA de Street Fighter Alpha Anthology pour un rendu 16:9 natif
(render 448px, decor rempli des deux cotes, action/HUD centres) + deverrouille
SFA3 Upper et Hyper SFA (Select sur l'ecran de choix de version).

Usage :
    python sfa_anthology_ws_patcher.py "SOURCE.iso" ["DEST.iso"]

  - SOURCE = ISO USA (pristine ou deja unlock-patchee) ; jamais modifiee.
  - DEST   = ISO patchee (defaut : SOURCE + " [Widescreen]").

Contenu du patch (v10, 2026-07-12) :
  SLUS_213.17 (a plat dans l'ISO) :
    - S1 viewport : largeur playfield/render-target/centrage 384 -> 448 (3 mots).
  zb / e203 (overlay CPS2 commun, MWo3 dans X_DATA.BIN, base runtime 0x1c8000) :
    - unlock Upper/Hyper : 4x lbu -> ori v0,0xff (FUN_1c8e10).
    - ciel  (SCR1 8px)  : buffers templates reloges en RAM libre (0x1580000/0x15F0000),
      templates+drawers 49 -> 57 colonnes, lecture ring decalee -32px (2 caves).
    - sol   (SCR2 16px) : drawers 25 -> 29 colonnes, lecture ring -32px (2 caves),
      blit scanline rowscroll 384 -> 448 (TRXREG RRW).
    - cascade (SCR3 32px) : buffers reloges (0x1660000/0x1680000), templates+drawer
      13 -> 15 colonnes, lecture -32px (1 cave).
    - sprites/HUD/objets : +32px ecran (2 caves) = centrage type "PSP +48".
    - zb recompresse par parse optimal DP (round-trip verifie octet a octet).

Principe (modele "ring") : les tilemaps par couche sont des anneaux recomposes
autour de la camera avec ~60px de marge de chaque cote en 4:3. La vue 456px est
recentree dans cette fenetre (lecture -32px) et les sprites decales de +32px :
l'extension 64px se repartit 32px a gauche + 32px a droite.
"""
import struct, shutil, sys, os
from collections import defaultdict

# ---------------------------------------------------------------- MWo3 codec
def mwo3_decompress(src, max_out=0x2000000):
    out = bytearray(); i = 0; n = len(src); ctrl = 0; bit = 0
    while i + 1 < n:
        if bit == 0:
            ctrl = struct.unpack_from('<H', src, i)[0]; i += 2; bit = 0x8000
        if (ctrl & bit) == 0:
            out += src[i:i+2]; i += 2
        else:
            token = struct.unpack_from('<H', src, i)[0]; length = token >> 11
            if length == 0:
                length = struct.unpack_from('<H', src, i+2)[0]; offset = token; i += 4
            else:
                offset = token & 0x7ff; i += 2
            if offset == 0:
                if length == 0: break
                out += b'\x00\x00' * length
            else:
                p = len(out) - offset*2
                for _ in range(length):
                    out += out[p:p+2]; p += 2
        bit >>= 1
        if len(out) > max_out: break
    return bytes(out)

def mwo3_compress_opt(data):
    """Recompresseur a parse optimal (DP) — ~taille de l'encodeur original."""
    if len(data) & 1: data += b'\x00'
    W = len(data)//2; words = struct.unpack('<%dH' % W, data)
    maxlen = [0]*W; maxoff = [0]*W; pos_of = defaultdict(list)
    for i in range(W):
        best = 0; bo = 0
        for p in reversed(pos_of[words[i]]):
            off = i - p
            if off > 0x7ff: break
            L = 0
            while i+L < W and L < 0xffff and words[p+L] == words[i+L]: L += 1
            if L > best: best = L; bo = off
            if best >= 0xffff: break
        maxlen[i] = best; maxoff[i] = bo
        l = pos_of[words[i]]; l.append(i)
        if len(l) > 3000: del l[:-2000]
    INF = float('inf'); U = 16
    dp = [0.0]*(W+1); ch = [None]*(W+1)
    for i in range(W-1, -1, -1):
        best = INF; bc = None
        c = (U+1) + dp[i+1]
        if c < best: best = c; bc = ('L', 1)
        if words[i] == 0:
            z = 1
            while i+z < W and words[i+z] == 0 and z < 0xffff: z += 1
            c = (2*U+1) + dp[i+z]
            if c < best: best = c; bc = ('Z', z)
        ml = maxlen[i]
        if ml >= 2:
            cand = set(range(2, min(31, ml)+1))
            if ml > 31: cand.add(ml); cand.add(31)
            for L in cand:
                wc = U if L <= 0x1f else 2*U
                c = (wc+1) + dp[i+L]
                if c < best: best = c; bc = ('M', L)
        dp[i] = best; ch[i] = bc
    out = bytearray(); st = {'pos': 0, 'ctrl': 0, 'cbit': 0}
    def new_ctrl(): st['pos'] = len(out); out.extend(b'\x00\x00'); st['ctrl'] = 0; st['cbit'] = 0x8000
    def flush(): struct.pack_into('<H', out, st['pos'], st['ctrl'])
    new_ctrl(); i = 0
    while i < W:
        if st['cbit'] == 0: flush(); new_ctrl()
        k, L = ch[i]
        if k == 'L':
            st['cbit'] >>= 1; out += struct.pack('<H', words[i]); i += 1
        elif k == 'Z':
            st['ctrl'] |= st['cbit']; st['cbit'] >>= 1; out += struct.pack('<HH', 0, L); i += L
        else:
            st['ctrl'] |= st['cbit']; st['cbit'] >>= 1
            out += struct.pack('<H', (L << 11) | maxoff[i]) if L <= 0x1f else struct.pack('<HH', maxoff[i], L)
            i += L
    flush()
    if st['cbit'] == 0: new_ctrl()
    st['ctrl'] |= st['cbit']; flush(); out += struct.pack('<HH', 0, 0)
    return bytes(out)

# ---------------------------------------------------------------- constantes
SLUS_ISO   = 0x13e000        # SLUS_213.17 dans l'ISO (LBA 636)
XDATA_ISO  = 0x9f738000      # X_DATA.BIN dans l'ISO (LBA 1306224)
E203_IDX   = 203             # entree AFS du zb (b_usa.bin)
E203_SLOT  = 43008           # espace jusqu'a e204
ZB_BASE    = 0x1c8000        # base runtime du zb decompresse

# S1 : (fileoff SLUS, vanilla, patche)
S1 = [(0x4ae28, 0x24080180, 0x240801c0),
      (0x4b270, 0x24080180, 0x240801c0),
      (0x4b2a0, 0x24070180, 0x240701c0)]

# zb : va -> (vanilla, patche). vanilla=None => zone cave (zeros attendus).
ZB = {
    # unlock Upper/Hyper (tolere l'ISO All-Unlocked deja patchee)
    0x1c8e58: (0x904200dc, 0x340200ff), 0x1c8e74: (0x904200dc, 0x340200ff),
    0x1c8e90: (0x904200dc, 0x340200ff), 0x1c8eac: (0x904200dc, 0x340200ff),
    # ciel 8px : reloc buffers + templates/counts 57 + intercepts vers caves
    0x1dbcf0: (0x01da4010, 0x01580000), 0x1dbcf4: (0x01eb4010, 0x015F0000),
    0x1d17b0: (0x2e820031, 0x2e820039),
    0x1d19b0: (0x2aa30031, 0x2aa30039), 0x1d1b9c: (0x2a830031, 0x2a830039),
    0x1d18ec: (0x8C5400D4, 0x08075FA4), 0x1d1a84: (0x8C5300D4, 0x08075FAC),
    # sol 16px : counts 29 + intercepts + blit scanline 448
    0x1d1f7c: (0x2aa30019, 0x2aa3001d), 0x1d2140: (0x2a830019, 0x2a83001d),
    0x1d223c: (0x2a830019, 0x2a83001d),
    0x1d1f2c: (0x8C5400D8, 0x08075FB4), 0x1d20e4: (0x8C5300D8, 0x08075FBC),
    0x1d38d4: (0x240E0180, 0x240E01C0),
    # cascade 32px : reloc + templates/drawer 15 + intercept
    0x1dbd00: (0x01e32430, 0x01660000), 0x1dbd04: (0x01f42430, 0x01680000),
    0x1d2360: (0x2e82000d, 0x2e82000f), 0x1d2774: (0x2a83000d, 0x2a83000f),
    0x1d2644: (0x8C5300DC, 0x08075FC4),
    # sprites/objets +32px ecran
    0x1d292c: (0x308403FF, 0x08075FCC), 0x1d2ef8: (0x30C303FF, 0x08075FD4),
}
CAVES = {
    0x1d7e90: [0x8C5400D4, 0x2694FFE0, 0x329401FF, 0x0807463D, 0],  # ciel drawer 1 : X-32 &0x1ff
    0x1d7eb0: [0x8C5300D4, 0x2673FFE0, 0x327301FF, 0x080746A3, 0],  # ciel drawer 2
    0x1d7ed0: [0x8C5400D8, 0x2694FFE0, 0x329403FF, 0x080747CD, 0],  # sol plain : X-32 &0x3ff
    0x1d7ef0: [0x8C5300D8, 0x2673FFE0, 0x327303FF, 0x0807483B, 0],  # sol variante
    0x1d7f10: [0x8C5300DC, 0x2673FFE0, 0x08074993, 0],              # cascade : X-32
    0x1d7f30: [0x308403FF, 0x24840020, 0x08074A4D, 0],              # persos/HUD : X+32
    0x1d7f50: [0x30C303FF, 0x24630020, 0x08074BC0, 0],              # objets : X+32
}

DEST = None
def fail(msg):
    print('ERREUR : ' + msg)
    if DEST and os.path.exists(DEST):          # pas de copie a moitie patchee
        os.remove(DEST); print('(copie supprimee : %s)' % DEST)
    sys.exit(1)

def main():
    global DEST
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + ' [Widescreen].iso'
    if not os.path.isfile(src): fail('source introuvable : ' + src)
    if os.path.exists(dst) and os.path.samefile(src, dst): fail('DEST doit differer de SOURCE')
    print('Copie de l\'ISO (~1-2 min)...')
    shutil.copy2(src, dst); DEST = dst
    f = open(dst, 'r+b')

    # --- sanity : SLUS ELF + X_DATA AFS
    f.seek(SLUS_ISO)
    if f.read(4) != b'\x7fELF': fail('SLUS_213.17 introuvable a 0x%x (mauvaise ISO ?)' % SLUS_ISO)
    f.seek(XDATA_ISO)
    if f.read(4) != b'AFS\x00': fail('X_DATA.BIN introuvable a 0x%x (mauvaise ISO ?)' % XDATA_ISO)

    # --- S1 (SLUS)
    for fo, old, new in S1:
        f.seek(SLUS_ISO + fo); cur = struct.unpack('<I', f.read(4))[0]
        if cur == new:
            print('  S1 @%06x deja patche' % fo); continue
        if cur != old: fail('S1 @%06x = %08x (attendu %08x)' % (fo, cur, old))
        f.seek(SLUS_ISO + fo); f.write(struct.pack('<I', new))
    print('S1 viewport 448 : OK')

    # --- zb (e203)
    f.seek(XDATA_ISO + 8 + 8*E203_IDX); e_off, e_size = struct.unpack('<II', f.read(8))
    f.seek(XDATA_ISO + e_off); comp = f.read(e_size)
    D = bytearray(mwo3_decompress(comp))
    if len(D) != 0x13e80: fail('zb decompresse = 0x%x octets (attendu 0x13e80)' % len(D))

    for va, (old, new) in sorted(ZB.items()):
        cur = struct.unpack_from('<I', D, va - ZB_BASE)[0]
        if cur == new: continue
        if cur != old: fail('zb @%08x = %08x (attendu %08x)' % (va, cur, old))
        struct.pack_into('<I', D, va - ZB_BASE, new)
    for base, ws in CAVES.items():
        for i, v in enumerate(ws):
            off = base + i*4 - ZB_BASE
            cur = struct.unpack_from('<I', D, off)[0]
            if cur not in (0, v): fail('cave @%08x = %08x (zone non libre ?)' % (base + i*4, cur))
            struct.pack_into('<I', D, off, v)
    print('zb patche (unlock + widescreen v10)')

    C = mwo3_compress_opt(bytes(D))
    if mwo3_decompress(C) != bytes(D): fail('round-trip compression KO')
    if len(C) > E203_SLOT: fail('zb recompresse %d > slot %d' % (len(C), E203_SLOT))
    print('zb recompresse : %d octets (slot %d, marge %d), round-trip OK' % (len(C), E203_SLOT, E203_SLOT - len(C)))

    f.seek(XDATA_ISO + e_off); f.write(C)
    if len(C) < e_size:  # nettoie la fin de l'ancien flux
        f.write(b'\x00' * (e_size - len(C)))
    f.seek(XDATA_ISO + 8 + 8*E203_IDX + 4); f.write(struct.pack('<I', len(C)))
    f.flush()

    # --- verification finale par relecture
    f.seek(XDATA_ISO + 8 + 8*E203_IDX); _, sz2 = struct.unpack('<II', f.read(8))
    f.seek(XDATA_ISO + e_off); D2 = mwo3_decompress(f.read(sz2))
    if D2 != bytes(D): fail('verification finale KO')
    f.close()
    print('\nOK -> ' + dst)
    print('16:9 : regler PCSX2 (ou la console) sur aspect 16:9. Upper/Hyper : Select sur l\'ecran de version.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, struct.error, IndexError, ValueError) as e:   # ISO inattendue (flux MWo3 illisible...)
        fail('ISO non reconnue ou illisible (%s: %s)' % (type(e).__name__, e))
