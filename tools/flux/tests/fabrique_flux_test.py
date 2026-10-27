#!/usr/bin/env python3
"""Flux de test pour test_flux_vorbis.cpp (aucune donnee de jeu) : signal synthetique 48 kHz stereo de 20 s, encode par
ffmpeg en ADX et en Ogg Vorbis, reunis dans un AFS comme hsfa_flux.bin, avec une table.

  entree 0 : vide (flux absent du paquet -> repli QSound)      code 0044
  entree 1 : ADX (sans boucle)                                   code 0041
  entree 2 : Ogg Vorbis, boucle LOOPSTART=96000 LOOPEND=720000   code 0042
  entree 3 : Ogg Vorbis, sans boucle                             code 0043
Usage : fabrique_flux_test.py dossier_sortie     (ecrit source.raw, test.afs, table.txt)
"""
import math, os, struct, subprocess, sys

D = sys.argv[1]; os.makedirs(D, exist_ok=True)
N, F = 20 * 48000, 48000
pcm = bytearray()
for i in range(N):
    t = i / F
    note = 220 * 2 ** (int(t * 4) % 8 / 12)
    g = 0.25 * math.sin(2 * math.pi * note * t) + 0.12 * math.sin(2 * math.pi * 3 * note * t + 1)
    d = 0.2 * math.sin(2 * math.pi * 330 * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 0.5 * t))
    pcm += struct.pack("<hh", int(32767 * (g + 0.3 * d)), int(32767 * (0.7 * g + d)))
src = os.path.join(D, "source.raw"); open(src, "wb").write(pcm)
def ff(*a):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", src] + list(a),
                   check=True)
ff("-c:a", "adpcm_adx", "-f", "adx", os.path.join(D, "e1.adx"))
ff("-c:a", "libvorbis", "-q:a", "2", "-metadata", "LOOPSTART=96000", "-metadata", "LOOPEND=720000", os.path.join(D, "e2.ogg"))
ff("-c:a", "libvorbis", "-q:a", "2", os.path.join(D, "e3.ogg"))
ent = [b"", open(os.path.join(D, "e1.adx"), "rb").read(), open(os.path.join(D, "e2.ogg"), "rb").read(),
       open(os.path.join(D, "e3.ogg"), "rb").read()]
o = 2048; tab = []; corps = b""
for e in ent:
    if not e: tab.append((0, 0)); continue
    tab.append((o, len(e))); pad = e + bytes((-len(e)) % 2048); corps += pad; o += len(pad)
tete = b"AFS\0" + struct.pack("<I", len(ent)) + b"".join(struct.pack("<II", *t) for t in tab)
open(os.path.join(D, "test.afs"), "wb").write(tete + bytes(2048 - len(tete)) + corps)
open(os.path.join(D, "table.txt"), "w").write("# test\n0041 1 127 -\n0042 2 127 -\n0043 3 127 -\n0044 0 127 -\n")
print("flux de test :", [len(e) for e in ent], "octets")
