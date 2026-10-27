#!/usr/bin/env python3
"""
unlock_patcher.py — applique UNIQUEMENT le all-unlock (Upper/Hyper + roster) à une ISO
SFA Anthology, EN PLACE. Aucune modif widescreen. Dérivé de sfa_anthology_ws_patcher.py
(mêmes 4 patchs unlock, même pipeline zb/MWo3), codec inliné.

All-unlock = dans le zb (e203, MWo3) : 4x  lbu v0,0xdc(v0) (0x904200dc) -> ori v0,0,0xff
(0x340200ff) @ 0x1c8e58/74/90/ac  => l'octet d'unlock lu vaut toujours 0xff (tout débloqué,
sans carte mémoire).

Usage : python unlock_patcher.py <iso_a_patcher_en_place>
"""
import struct, sys, os
from collections import defaultdict

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

XDATA_ISO = 0x9f738000
SLUS_ISO  = 0x13e000
E203_IDX  = 203
E203_SLOT = 43008
ZB_BASE   = 0x1c8000
UNLOCK = {0x1c8e58: (0x904200dc, 0x340200ff), 0x1c8e74: (0x904200dc, 0x340200ff),
          0x1c8e90: (0x904200dc, 0x340200ff), 0x1c8eac: (0x904200dc, 0x340200ff)}

def fail(m): print('ERREUR :', m); sys.exit(1)

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(0)
    iso = sys.argv[1]
    if not os.path.isfile(iso): fail('introuvable : ' + iso)
    f = open(iso, 'r+b')
    f.seek(SLUS_ISO)
    if f.read(4) != b'\x7fELF': fail('SLUS introuvable @0x%x (mauvaise ISO ?)' % SLUS_ISO)
    f.seek(XDATA_ISO)
    if f.read(4) != b'AFS\x00': fail('X_DATA introuvable @0x%x' % XDATA_ISO)
    f.seek(XDATA_ISO + 8 + 8*E203_IDX); e_off, e_size = struct.unpack('<II', f.read(8))
    f.seek(XDATA_ISO + e_off); comp = f.read(e_size)
    D = bytearray(mwo3_decompress(comp))
    if len(D) != 0x13e80: fail('zb decompresse = 0x%x (attendu 0x13e80)' % len(D))
    done = 0
    for va, (old, new) in sorted(UNLOCK.items()):
        cur = struct.unpack_from('<I', D, va - ZB_BASE)[0]
        if cur == new: print('  unlock @%08x deja patche' % va); continue
        if cur != old: fail('unlock @%08x = %08x (attendu %08x)' % (va, cur, old))
        struct.pack_into('<I', D, va - ZB_BASE, new); done += 1
    print('unlock : %d/%d patchs appliques' % (done, len(UNLOCK)))
    C = mwo3_compress_opt(bytes(D))
    if mwo3_decompress(C) != bytes(D): fail('round-trip compression KO')
    if len(C) > E203_SLOT: fail('zb recompresse %d > slot %d' % (len(C), E203_SLOT))
    f.seek(XDATA_ISO + e_off); f.write(C)
    if len(C) < e_size: f.write(b'\x00' * (e_size - len(C)))
    f.seek(XDATA_ISO + 8 + 8*E203_IDX + 4); f.write(struct.pack('<I', len(C))); f.flush()
    # verification par relecture
    f.seek(XDATA_ISO + 8 + 8*E203_IDX); _, sz2 = struct.unpack('<II', f.read(8))
    f.seek(XDATA_ISO + e_off); D2 = bytearray(mwo3_decompress(f.read(sz2)))
    ok = all(struct.unpack_from('<I', D2, va - ZB_BASE)[0] == new for va, (_, new) in UNLOCK.items())
    f.close()
    print('recompresse %d o (slot %d, marge %d) ; relecture unlock %s'
          % (len(C), E203_SLOT, E203_SLOT - len(C), 'OK' if ok and D2 == D else 'KO'))
    if not (ok and D2 == D): fail('verification finale KO')
    print('\nOK (all-unlock, PAS de widescreen) -> ' + iso)

if __name__ == '__main__':
    main()
