"""lz148778 (portage HSFA) avec retour du nombre d'octets consommés."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

def decompress(src, si, out_len):
    start, dst, ctrl, mask = si, bytearray(), 0, 0
    while len(dst) < out_len:
        if mask == 0:
            if si >= len(src): return None, si - start
            ctrl = src[si]; si += 1; mask = 0x80
        if si >= len(src): return None, si - start
        b = src[si]; si += 1
        if ctrl & mask == 0: dst.append(b)
        else:
            off, n = (b >> 4) + 1, (b & 0xF) + 2
            p = len(dst) - off
            if p < 0: return None, si - start
            for _ in range(n): dst.append(dst[p]); p += 1
        mask >>= 1
    return bytes(dst[:out_len]), si - start
