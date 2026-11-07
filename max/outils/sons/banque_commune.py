"""Banque commune PSP se_mid.pac (2026-10-07) : section 0 = PPHD (table PPVA des échantillons), section 1 = données
ADPCM, sections 2.. = séquences MIDI (« MThd », un bruitage chacune). Sorties : ~/.cache/sfa3max/converti/sons_communs/
eNN.wav (échantillons), sNN.mid (séquences), banque.json. Les codes PSP < $200 de 0x78408 visent cette banque."""
import os, sys, struct, json, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
from voix_max import vag
src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.cache/sfa3max/data/se_mid.pac")
b = [s[1] if isinstance(s, tuple) else s for s in split(open(src, "rb").read())]
h, data = b[0], b[1]
va = h.find(b"PPVA"); n = struct.unpack_from("<I", h, va + 0x14)[0] + 1
d = os.path.expanduser("~/.cache/sfa3max/converti/sons_communs"); os.makedirs(d, exist_ok=True)
info = {"echantillons": [], "sequences": []}
for k in range(n):
    off, fr, taille, m1 = struct.unpack_from("<IIIi", h, va + 0x20 + 16 * k)
    if off == 0xFFFFFFFF or off + taille > len(data): info["echantillons"].append({"n": k, "vide": True}); continue
    pcm = vag(data[off:off + taille])
    with wave.open(os.path.join(d, "e%02d.wav" % k), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(fr); w.writeframes(struct.pack("<%dh" % len(pcm), *pcm))
    info["echantillons"].append({"n": k, "frequence": fr, "duree_s": round(len(pcm) / fr, 3)})
for k, s in enumerate(b[2:]):
    if s[:4] == b"MThd": open(os.path.join(d, "s%02d.mid" % k), "wb").write(s); info["sequences"].append({"n": k, "octets": len(s)})
json.dump(info, open(os.path.join(d, "banque.json"), "w"), indent=0)
print(sum(1 for e in info["echantillons"] if not e.get("vide")), "échantillons,", len(info["sequences"]), "séquences ->", d)
