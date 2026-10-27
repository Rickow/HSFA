#!/usr/bin/env python3
"""Décompresseur LZ du moteur (portage exact de FUN_00148778).
Format : byte de contrôle (MSB->LSB, 8 tokens). bit=0 -> littéral ;
bit=1 -> back-ref : offset=(b>>4)+1, longueur=(b&0xf)+2."""

def decompress(src: bytes, si: int, out_len: int) -> bytes:
    dst = bytearray()
    ctrl = 0
    mask = 0
    while len(dst) < out_len:
        if mask == 0:
            ctrl = src[si]; si += 1
            mask = 0x80
        b = src[si]; si += 1
        if (ctrl & mask) == 0:
            dst.append(b)                      # littéral
        else:
            off = (b >> 4) + 1
            n = (b & 0xf) + 2                  # 1 initial + (uVar3+1)
            p = len(dst) - off
            for _ in range(n):
                dst.append(dst[p]); p += 1
        mask >>= 1
    return bytes(dst[:out_len])
