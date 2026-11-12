#!/usr/bin/env python3
"""cherche dans le code MAX et les talons ($370000-$3FFFFF) de deux constructions Upper MAX dont TOUT
a bougé (ex. b1_v161 contre x_dropsr : code décalé dès $4C5E, données +$2000) les adresses absolues IDENTIQUES des deux
côtés qui visent la zone déplacée : ce sont des adresses littérales non relogées (comme l'ancien JSR $1B6B6).
Usage : litteraux_figes.py maxA maxB [1re adresse déplacée, hex, défaut 4C5E]"""
import sys, os, struct
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
def image(d):
    b = bytearray()
    for n in PRG: b += open(os.path.join(d, "roms_ro5", "sfa3ud", n), "rb").read()
    b[0::2], b[1::2] = b[1::2], b[0::2]; return bytes(b)
A, B = image(sys.argv[1]), image(sys.argv[2]); lo = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x4C5E
n = 0
for k in range(0x370000, 0x3FFFFA, 2):
    op = struct.unpack_from(">H", A, k)[0]
    saut = op in (0x4EB9, 0x4EF9); lea = (op & 0xF1FF) == 0x41F9; imm = (op & 0xF1FF) in (0x203C, 0x207C) or op == 0x2F3C or op == 0x4879
    if not (saut or lea or imm): continue
    v = struct.unpack_from(">I", A, k + 2)[0]
    if not (lo <= v < 0x3A0000) or B[k:k + 6] != A[k:k + 6]: continue
    if not saut and v < 0xA1000 and v % 2: continue
    n += 1; print("$%06X : %04X %08X (%s) identique des deux côtés" % (k, op, v, "saut" if saut else "lea" if lea else "immédiat"))
print("# %d adresse(s) absolue(s) vers la zone déplacée [$%X, $3A0000) non relogée(s)" % (n, lo))
