#!/usr/bin/env python3
"""Banque commune PSP se_mid.pac, sections au-dela de celles de banque_commune.py (session MAX, lecture seule) :
  0 PPHD + 1 ADPCM (18 echantillons d'instruments) + 2..40 sequences MIDI (39) ;
  41 PPHD + 42 ADPCM (banque A, 104 echantillons) + 43 TABLE DE SONS (64 entrees de 16 o : codes PSP $00-$3F) ;
  44 PPHD + 45 ADPCM (banque B, 21 echantillons) + 46 table (80 entrees, systeme).
Entree de table (8 mots LE) : mot 0 = type ($100 : sequence MIDI n = mot 2 ; 0 : echantillon, mot 2 = banque<<8 | n,
banque 0 = A, 1 = B, 2 = instruments ; -1 : muet ; 2 : autre), mot 1 = priorite, mot 3 = volume ?, mot 4 = reglage.
Sorties : communs/psp/A_nnn.wav, B_nnn.wav, table43.json."""
import os, sys, struct, wave, json
sys.path.insert(0, os.environ.get("HSFA_TOOLS_MAX", "tools/max"))
sys.path.insert(0, os.environ.get("SON_MAX_OUTILS_SONS", os.path.dirname(os.path.abspath(__file__))))   # voix_max.py (max/outils/sons)
from plpac import split
from voix_max import vag
ICI = os.path.dirname(os.path.abspath(__file__))
S = [s[1] if isinstance(s, tuple) else s for s in split(open(os.path.expanduser("~/.cache/sfa3max/data/se_mid.pac"), "rb").read())]
COM = os.environ.get("SON_MAX_COMMUNS", ICI)            # (script_uppermax) dossier « communs »
out = os.path.join(COM, "psp"); os.makedirs(out, exist_ok=True)
def banque(h, data, nom):
    va = h.find(b"PPVA"); n = struct.unpack_from("<I", h, va + 0x14)[0] + 1
    info = []
    for k in range(n):
        off, fr, taille, m1 = struct.unpack_from("<IIIi", h, va + 0x20 + 16 * k)
        if off == 0xFFFFFFFF or off + taille > len(data): info.append(None); continue
        pcm = vag(data[off:off + taille])
        with wave.open(os.path.join(out, "%s_%03d.wav" % (nom, k)), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(fr); w.writeframes(struct.pack("<%dh" % len(pcm), *pcm))
        info.append({"frequence": fr, "duree_s": round(len(pcm) / fr, 3)})
    return info
A = banque(S[41], S[42], "A"); B = banque(S[44], S[45], "B"); I = banque(S[0], S[1], "I")
tab = []
for n in range(64):
    e = struct.unpack_from("<8h", S[43], 16 * n)
    tab.append({"code": n, "mots": e})
json.dump({"A": A, "B": B, "I": I, "table43": tab}, open(os.path.join(COM, "table43.json"), "w"), indent=0)
print("A", sum(1 for x in A if x), "B", sum(1 for x in B if x), "instruments", sum(1 for x in I if x))
