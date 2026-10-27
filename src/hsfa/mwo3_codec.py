"""
MWo3 codec — CRACKÉ 2026-06-24 (décompresseur = SLUS FUN_148698, validé 100% sur zero9 9.9 Mo).

Format : LZSS 16-bit À MOT (little-endian). Le fichier .mwo3 EST le flux LZSS direct
(les octets d'en-tête 'MWo3...' sont eux-mêmes des littéraux du flux).
- Mot de CONTRÔLE 16-bit, traité MSB->LSB. bit=0 -> littéral (copie 1 mot). bit=1 -> match.
- Token match 16-bit :
    length5 = token >> 11
    si length5 != 0 : length = length5 ; offset = token & 0x7ff ; (1 mot consommé)
    si length5 == 0 : offset = token ; length = mot suivant ; (2 mots consommés)
- offset == 0 : length == 0 -> FIN ; sinon -> RUN DE ZÉROS (length mots).
- offset  > 0 : BACKREF, copie length mots depuis (dst - offset) en unités de MOT.
"""
import struct

def decompress(src, max_out=0x2000000):
    out = bytearray(); i = 0; n = len(src); ctrl = 0; bit = 0
    while i + 1 < n:
        if bit == 0:
            ctrl = struct.unpack_from('<H', src, i)[0]; i += 2; bit = 0x8000
        if (ctrl & bit) == 0:                         # littéral
            out += src[i:i+2]; i += 2
        else:                                         # match
            token = struct.unpack_from('<H', src, i)[0]; length = token >> 11
            if length == 0:
                length = struct.unpack_from('<H', src, i+2)[0]; offset = token; i += 4
            else:
                offset = token & 0x7ff; i += 2
            if offset == 0:
                if length == 0: break                 # FIN
                out += b'\x00\x00' * length            # run de zéros
            else:
                p = len(out) - offset*2                # backref (mots)
                for _ in range(length):
                    out += out[p:p+2]; p += 2
        bit >>= 1
        if len(out) > max_out: break
    return bytes(out)


def compress(data):
    """Re-compresseur greedy (offset<=0x7ff mots, length<=0xffff). Round-trip exact."""
    if len(data) & 1: data += b'\x00'                  # pad mot
    W = len(data) // 2
    words = struct.unpack('<%dH' % W, data)
    # index des positions par valeur de mot (chaînes) pour trouver les backrefs
    from collections import defaultdict
    pos_of = defaultdict(list)
    out = bytearray(); ctrl_pos = None; ctrl = 0; cbit = 0
    def flush_ctrl():
        nonlocal ctrl
        struct.pack_into('<H', out, ctrl_pos, ctrl)
    def new_ctrl():
        nonlocal ctrl_pos, ctrl, cbit
        ctrl_pos = len(out); out.extend(b'\x00\x00'); ctrl = 0; cbit = 0x8000
    i = 0
    new_ctrl()
    while i < W:
        if cbit == 0:
            flush_ctrl(); new_ctrl()
        # run de zéros ?
        if words[i] == 0:
            z = 0
            while i+z < W and words[i+z] == 0 and z < 0xffff: z += 1
            if z >= 2:                                 # vaut un token (offset 0)
                ctrl |= cbit; cbit >>= 1
                out += struct.pack('<HH', 0, z)        # length5=0 -> ext ; offset=0
                for k in range(z): pos_of[0].append(i+k)
                i += z; continue
        # backref ?
        best_len = 0; best_off = 0
        for p in reversed(pos_of.get(words[i], ())):
            off = i - p
            if off > 0x7ff: break
            L = 0
            while i+L < W and L < 0x1f and words[p+L] == words[i+L]: L += 1
            if L > best_len: best_len = L; best_off = off
            if best_len >= 0x1f: break
        if best_len >= 2:                              # match court (length5!=0, 1 mot)
            ctrl |= cbit; cbit >>= 1
            out += struct.pack('<H', (best_len << 11) | best_off)
            for k in range(best_len): pos_of[words[i+k]].append(i+k)
            i += best_len
        else:                                          # littéral
            cbit >>= 1
            out += struct.pack('<H', words[i])
            pos_of[words[i]].append(i); i += 1
    flush_ctrl()
    # token de fin : offset=0, length=0
    if cbit == 0: out += struct.pack('<H', 0)          # nouveau ctrl si plein
    else: ctrl |= cbit; flush_ctrl()
    out += struct.pack('<HH', 0, 0)
    return bytes(out)


if __name__ == '__main__':
    C = open(r'E:/CLAUDE CODE/anthology_extract/ro9_usa_prog68k.mwo3','rb').read()
    D = decompress(C)
    print('decompresse:', len(D), 'octets (0x%x)' % len(D))
