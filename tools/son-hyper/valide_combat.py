#!<workspace>/venv/bin/python
"""Validation en jeu : pour chaque commande de voix du journal (lua/redirection.lua), compare l'enregistrement du fork
(WAV 48 kHz, debut a l'image 1) a l'echantillon attendu (voix d'origine SFA1/SFA2 de la nouvelle commande) et a
l'echantillon SFA3 que le jeu aurait joue sans redirection : correlation normalisee maximale (recalage 0-250 ms,
canal gauche). Usage : valide_combat.py essais/<nom>.son essais/<nom>.wav [essais/<nom>_sans.wav] [roms_hyper] -> essais/<nom>_validation.tsv
et extrait d'ecoute essais/<nom>_voix.wav (chaque voix redirigee : 1,6 s autour de la commande)."""
import sys, os, json, wave
import numpy as np
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "<workspace>/work/agent_voix_max"); sys.path.insert(0, "<workspace>/work/agent_son_ro5/hybride")
import gen_voix_max as G
from gen_voix_max import reechantillonne
FPS = 59.6372
son, wv = sys.argv[1], sys.argv[2]
sans = sys.argv[3] if len(sys.argv) > 3 else None             # temoin : meme partie sans redirection
rom = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ICI, "roms_hyper")
def litw(f):
    w = wave.open(f); return w.getframerate(), w.getnchannels(), np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float).reshape(-1, w.getnchannels()) / 32768.0
SR, ch, rec = litw(wv)
rec0 = litw(sans)[2] if sans else None
z, q = G.lit_base(rom); p = G.pilote(z)
def ech_cmd(c):
    """premier echantillon joue par la commande c (entree resolue) -> PCM float, frequence"""
    r = p.resolution(c % 0xC00)
    if not r: return None
    e = [t for t in r if t[0] == "08"]
    if not e: return None
    ent = e[0][3]
    bank, deb, fin, prm = ent[0], int.from_bytes(ent[1:3], "little"), int.from_bytes(ent[5:7], "little"), ent[7]
    H = G.hauteurs(z); h = H[120 - prm] if 0 <= 120 - prm < 108 else 0x800
    b = bank << 16
    raw = q[b + deb: b + fin + 1] if fin >= deb else q[b + deb: b + 0x10000] + q[b: b + fin + 1]
    x = np.frombuffer(bytes(raw), np.int8).astype(float) / 128
    return x, G.QS_HZ * h / 4096
def score(seg, ref):
    best = 0.0
    if len(ref) < 64 or len(seg) < len(ref): return 0.0
    n = 1 << int(np.ceil(np.log2(len(seg) + len(ref))))
    c = np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(ref, n)), n)[:int(0.25 * SR)]
    e2 = np.concatenate([[0], np.cumsum(seg ** 2)])
    rn = np.linalg.norm(ref)
    for lag in np.argsort(-np.abs(c))[:20]:
        en = np.sqrt(e2[min(len(seg), lag + len(ref))] - e2[lag])
        best = max(best, abs(c[lag]) / (rn * en + 1e-12))
    return best
lignes = ["image\tcode_jeu\tcode_joue\tJ1\tJ2\tcorr_attendu\tcorr_SFA3\tverdict\ttemoin_corr_attendu\ttemoin_corr_SFA3"]
extraits = []
for l in open(son):
    if l.startswith("#"): continue
    f = l.split()
    img, c0, c1, j1, j2 = int(f[0]), int(f[2], 16), int(f[4], 16), f[6], f[8]
    voix = 0x300 <= c0 <= 0x6ff or 0x800 <= c0 <= 0xbff
    if not voix: continue
    t = (img - 1) / FPS
    seg = rec[int(t * SR):int((t + 1.6) * SR), 0]
    sc = {}
    for nom, c in (("joue", c1), ("sfa3", c0)):
        r = ech_cmd(c)
        sc[nom] = score(seg, reechantillonne(r[0], r[1], SR)) if r else 0.0
    if c1 != c0: verdict = "voix d'origine" if sc["joue"] > sc["sfa3"] + 0.05 else ("incertain" if sc["joue"] >= sc["sfa3"] else "ECHEC")
    else: verdict = "SFA3 (non redirige)"
    tm = ""
    if rec0 is not None:
        s0 = rec0[int(t * SR):int((t + 1.6) * SR), 0]
        r1, r0 = ech_cmd(c1), ech_cmd(c0)
        tm = "\t%.3f\t%.3f" % (score(s0, reechantillonne(r1[0], r1[1], SR)) if r1 else 0, score(s0, reechantillonne(r0[0], r0[1], SR)) if r0 else 0)
    lignes.append("%d\t%04X\t%04X\t%s\t%s\t%.3f\t%.3f\t%s%s" % (img, c0, c1, j1, j2, sc["joue"], sc["sfa3"], verdict, tm))
    if c1 != c0: extraits += [rec[int((t - 0.1) * SR):int((t + 1.5) * SR)], np.zeros((int(0.4 * SR), ch))]
base = os.path.splitext(son)[0]
open(base + "_validation.tsv", "w").write("\n".join(lignes) + "\n")
if extraits:
    y = np.clip(np.concatenate(extraits), -1, 1)
    o = wave.open(base + "_voix.wav", "wb"); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((y * 32767).astype("<i2").tobytes()); o.close()
from collections import Counter
print(Counter(l.split("\t")[7] for l in lignes[1:]))
