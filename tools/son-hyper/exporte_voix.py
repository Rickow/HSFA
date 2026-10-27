#!<workspace>/venv/bin/python
"""WAV d'ecoute des voix extraites (frequence d'origine, 8 bits -> 16 bits) : voix/<jeu>/<NN_perso>/<commande>.wav et un
fichier enchaine par perso voix/<jeu>/<NN_perso>.wav ; annonceur : SFA1 0x00E0-0x00F2 (attribution probable),
SFA2 0x00A1-0x00BE ; voix supplementaires SFA2 0x00C0-0x00D3 (Zangief, Gen, Dan, Dhalsim)."""
import os, sys, json, wave, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources, blocs, audio
from assigne import NOMS
D = blocs.D
def copie(jeu, c, e, dst):
    shutil.copy(os.path.join(D, "wav", jeu, "ech_%s.wav" % e), os.path.join(dst, "%04x.wav" % c))
def enchaine(fichiers, out):
    parts = []
    for f in fichiers:
        x, fr = audio.lit(f); parts += [audio.reech(x, fr, 24000), np.zeros(7200)]
    y = np.clip(np.concatenate(parts), -1, 1) if parts else np.zeros(1)
    w = wave.open(out, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((y * 32767).astype("<i2").tobytes()); w.close()
n = 0
for jeu in ("sfa1", "sfa2"):
    for b in range(0x11):
        src = sources.source(jeu, b)
        if not src: continue
        d = os.path.join(D, "voix", jeu, "%02x_%s" % (b, NOMS[b])); os.makedirs(d, exist_ok=True)
        for c, e, g in src: copie(jeu, c, e, d); n += 1
        enchaine([os.path.join(d, "%04x.wav" % c) for c, e, g in src], d + ".wav")
    C = blocs.cat(jeu)["commandes"]
    for nom, lo, hi in ((("annonceur_probable", 0xe0, 0xf2),) if jeu == "sfa1" else (("annonceur", 0xa1, 0xbe), ("voix_00C0-00D3", 0xc0, 0xd3))):
        d = os.path.join(D, "voix", jeu, nom); os.makedirs(d, exist_ok=True); L = []
        for c in range(lo, hi + 1):
            v = C.get("%04x" % c)
            if v and v["echantillons"]:
                for e in v["echantillons"][:1]: copie(jeu, c, e, d); L.append(os.path.join(d, "%04x.wav" % c)); n += 1
        enchaine(L, d + ".wav")
print(n, "WAV")
