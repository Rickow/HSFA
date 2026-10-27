#!<workspace>/venv/bin/python
"""Validation des nouvelles commandes de roms_hyper (injection outils/injection.lua, journal + WAV 48 kHz stereo) :
  - registres : la note jouee lit bien l'entree attribuee (banque, debut, fin, hauteur) ;
  - son : correlation (canal gauche, recalage libre) entre l'enregistrement et l'echantillon d'ORIGINE (image QSound du
    jeu source, a sa frequence d'origine, ramene a 48 kHz) ; niveau RMS actif.
Usage : valide_nouvelles.py journaux/nouvelles.txt journaux/nouvelles.wav [roms_hyper] -> validation_nouvelles.tsv
Ecrit aussi ecoute/<jeu>_<perso>_origine_puis_fork.wav (pour chaque voix : origine, 0,3 s, enregistrement du fork)."""
import sys, os, json, wave
import numpy as np
ICI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ICI, "outils")); sys.path.insert(0, "<workspace>/work/agent_voix_max")
from notes import notes
from gen_voix_max import reechantillonne
import audio
jr, wv = sys.argv[1], sys.argv[2]
rom = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ICI, "roms_hyper")
A = json.load(open(os.path.join(rom, "attribution.json")))
par_cmd = {}
for v in A["voix"]:
    for c in v.get("commandes", []): par_cmd[int(c, 16)] = v
corr_de = {}
for r in A["correspondance"]:
    if r.get("nouvelle"): corr_de.setdefault(int(r["nouvelle"], 16), r)
w = wave.open(wv); SR = w.getframerate(); ch = w.getnchannels()
rec = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float).reshape(-1, ch) / 32768.0
N = notes(jr)
cmds = [(float(l.split()[1]), int(l.split()[2], 16)) for l in open(jr) if l.startswith("C ")]
qs = {}
def src_pcm(jeu, ech):
    if jeu not in qs: qs[jeu] = (open(os.path.join(ICI, "src", jeu + "_qs.bin"), "rb").read(), json.load(open(os.path.join(ICI, "catalogue", jeu + ".json")))["echantillons"])
    q, E = qs[jeu]; e = E[ech]; b = e["banque"] << 16
    raw = q[b + e["debut"]: b + e["fin"] + 1] if e["fin"] >= e["debut"] else q[b + e["debut"]: b + 0x10000] + q[b: b + e["fin"] + 1]
    return np.frombuffer(raw, np.int8).astype(float) / 128.0, e["hz"]
def xc(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    return np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)[:len(a)]
lignes = ["cmd\tjeu\tperso\tcode_source\tregistres\tcorr_origine\tniveau_dBFS\tduree_s"]
ecoute = {}
okr = okc = 0
for k, (t, c) in enumerate(cmds):
    v = par_cmd[c]; r = corr_de.get(c, {})
    ent = bytes.fromhex(v["entree"])
    bank, deb, bcl, fin, prm = ent[0], int.from_bytes(ent[1:3], "little"), int.from_bytes(ent[3:5], "little"), int.from_bytes(ent[5:7], "little"), ent[7]
    L = N.get(c, [])
    regs_ok = bool(L) and all((n["banque"] & 0xff) == bank and n["debut"] == deb and n["fin"] == fin for n in L)
    okr += regs_ok
    t1 = cmds[k + 1][0] if k + 1 < len(cmds) else len(rec) / SR
    seg = rec[int(t * SR):int(t1 * SR), 0]
    x, fr = src_pcm(v["jeu"], v["ech"])
    nz = np.where(np.abs(x * 128) > 2)[0]                     # memes silences retires que gen_son_hyper.py
    if len(nz): x = x[max(0, nz[0] - 8): nz[-1] + 9]
    ref = reechantillonne(x, fr, SR)
    lag = int(np.argmax(np.abs(xc(seg, ref))))
    s = seg[lag:lag + len(ref)]; m = min(len(s), len(ref))
    a, b = s[:m] - s[:m].mean(), ref[:m] - ref[:m].mean()
    co = float(abs((a * b).sum()) / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-12))
    okc += co >= 0.8
    act = seg[np.abs(seg) > 0.03 * (np.abs(seg).max() + 1e-9)]
    lv = 20 * np.log10(np.sqrt(np.mean(act ** 2)) + 1e-12) if len(act) else -99
    lignes.append("%04X\t%s\t%s\t%s\t%s\t%.3f\t%.1f\t%.2f" % (c, v["jeu"].upper(), r.get("perso", "?"), v["src"].upper(),
                  "ok" if regs_ok else "ECART", co, lv, len(ref) / SR))
    cle = "%s_%s" % (v["jeu"], r.get("perso", "x"))
    sil = np.zeros(int(0.3 * SR))
    ecoute.setdefault(cle, []).extend([ref * 0.5, sil, s[:m] if m else sil, sil, sil])
open(os.path.join(ICI, "validation_nouvelles.tsv"), "w").write("\n".join(lignes) + "\n")
os.makedirs(os.path.join(ICI, "ecoute"), exist_ok=True)
for cle, parts in ecoute.items():
    y = np.clip(np.concatenate(parts), -1, 1)
    f = wave.open(os.path.join(ICI, "ecoute", "%s_origine_puis_fork.wav" % cle.replace(" ", "")), "wb")
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((y * 32767).astype("<i2").tobytes()); f.close()
cs = [float(l.split("\t")[5]) for l in lignes[1:]]
print("commandes : %d ; registres conformes : %d ; correlation >= 0,8 : %d ; mediane %.3f ; min %.3f"
      % (len(cmds), okr, okc, float(np.median(cs)), min(cs)))
