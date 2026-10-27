"""Décodeur de tuiles SFA3 MAX PSP : portage exact de FUN_000ceb6c (EBOOT EU).
Sortie : 0x80 octets = tuile 16x16 en 4bpp (nibble bas = pixel gauche), écrite avec un
pas de ligne de 32 octets (texture de 64 px de large) ; on la rend ici en linéaire 8 o/ligne."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

_b = open(paths.eboot(), "rb").read()
DIST = _b[0x74+0x23a600:0x74+0x23a680]
STEP = _b[0x74+0x23a680:0x74+0x23a688]

def decode(src, si=0):
    """-> (tuile 0x80 octets linéaire, octets consommés) ; None si flux invalide."""
    out = bytearray(40 * 32)            # tampon au pas de 32 ; la dernière copie peut déborder
    a1, written, bits, ctrl, start = 0, 0, 0, 0, si
    try:
        while written < 0x80:
            cur = src[si]; si += 1
            if bits == 0:
                ctrl = cur; cur = src[si]; si += 1; bits = 8
            if ctrl & 1 == 0:                               # littéral
                out[a1] = cur; a1 += STEP[a1 & 7]; written += 1
            else:
                hi, cnt = cur >> 4, cur & 0xF
                if hi == 0:                                 # remplissage : cnt+1 fois l'octet suivant
                    val = src[si]; si += 1
                    for _ in range(cnt + 1):
                        out[a1] = val; a1 += STEP[a1 & 7]
                    written += cnt + 1
                else:                                       # copie arrière
                    v1 = a1 - DIST[((a1 & 7) << 4) + hi]
                    if v1 < 0: return None, si - start
                    for _ in range(cnt):
                        out[a1] = out[v1]; a1 += STEP[a1 & 7]; v1 += STEP[v1 & 7]
                    written += cnt
            ctrl >>= 1; bits -= 1
    except IndexError:
        return None, si - start
    return bytes(b for r in range(16) for b in out[r*32:r*32+8]), si - start

def tiles(gfx):
    """Entrée [1] d'un plXX : table d'offsets u32 puis flux compressés."""
    import struct
    n = struct.unpack_from("<I", gfx, 0)[0] // 4
    offs = list(struct.unpack_from(f"<{n}I", gfx, 0)) + [len(gfx)]
    return [(offs[i], offs[i+1] - offs[i]) for i in range(n)]
