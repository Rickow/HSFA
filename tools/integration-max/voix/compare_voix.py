#!<workspace>/venv/bin/python
"""Compare chaque voix MAX jouee par le Z80/QSound (enregistrement voix.lua, 48 kHz stereo) a son WAV source PSP :
recalage par intercorrelation, correlation de la forme d'onde par canal (source reechantillonnee comme dans la ROM
puis a 48 kHz ; le canal droit du QSound est en opposition de phase), correlation de l'enveloppe RMS (10 ms),
derive de vitesse (decalages mesures en debut et en fin de voix), duree audible et niveau.
Ecrit aussi les WAV d'ecoute : ecoute/<perso>_qsound.wav (voix enchainees telles que jouees par le QSound) et
ecoute/<perso>_psp_puis_qsound.wav (pour chaque voix : source PSP, 0,3 s de silence, version QSound).
Usage : compare_voix.py journaux/cote1.txt journaux/cote1.wav [sortie.tsv]"""
import sys, os, json, wave
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from gen_voix_max import reechantillonne, lit_wav

jr, wv = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ICI, "validation_voix.tsv")
att = {int(v["cmd"], 16): v for v in json.load(open(os.path.join(ICI, "roms_voix/attribution.json")))}
att.update({int(v["cmd2"], 16): v for v in att.values()})
w = wave.open(wv); SR = w.getframerate(); ch = w.getnchannels()
rec = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float).reshape(-1, ch) / 32768.0
mono = rec.mean(1)
cmds = [(float(l.split()[1]), int(l.split()[2], 16)) for l in open(jr) if l.startswith("C ")]


def env(x, n=SR // 100):
    m = len(x) // n
    return np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1) + 1e-12)


def corr(a, b):
    m = min(len(a), len(b)); a = a[:m] - a[:m].mean(); b = b[:m] - b[:m].mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


lignes = ["cmd\tperso\tvoix\tduree_src_s\tduree_qs_s\tdecalage_ms\tcorr_onde_G\tcorr_onde_D\tcorr_enveloppe\tderive_vitesse_pct\tniveau_dBFS"]
par_perso = {}
res = []


def xc(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    return np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)[:len(a)]


for k, (t, c) in enumerate(cmds):
    v = att[c]
    t1 = cmds[k + 1][0] if k + 1 < len(cmds) else len(mono) / SR
    segst = rec[int(t * SR):int(t1 * SR)]
    seg = segst[:, 0]                       # canal gauche (le droit est en opposition de phase : sortie QSound)
    x, fr = lit_wav(v["wav"])
    # reference : source -> frequence QSound de l'echantillon (comme le generateur) -> 48 kHz
    xs = reechantillonne(x, fr, v["fr_qs"]) if abs(v["fr_qs"] - fr) > 0.5 else x
    ref = reechantillonne(xs, v["fr_qs"], SR)
    lag = int(np.argmax(np.abs(xc(seg, ref))))
    s = seg[lag:lag + len(ref)]; m = min(len(s), len(ref))
    co = abs(corr(s, ref))
    lagd = int(np.argmax(np.abs(xc(segst[:, 1], ref))))
    cod = abs(corr(segst[lagd:lagd + len(ref), 1], ref))
    ce = corr(env(s), env(ref[:m]))
    # derive de vitesse : decalage mesure sur la fenetre la plus energique de chaque moitie de la reference
    W = int(0.12 * SR); der = float("nan")
    if m > 4 * W:
        e = np.convolve(ref[:m] ** 2, np.ones(W), "valid")
        i1 = int(np.argmax(e[:m // 2 - W])); i2 = m // 2 + int(np.argmax(e[m // 2:m - W]))
        l1 = int(np.argmax(np.abs(xc(seg, ref[i1:i1 + W])))) - i1
        l2 = int(np.argmax(np.abs(xc(seg, ref[i2:i2 + W])))) - i2
        der = 100.0 * (l2 - l1) / (i2 - i1)
    a = np.abs(seg) > 10 ** (-50 / 20)
    dq = (np.nonzero(a)[0][-1] - np.nonzero(a)[0][0]) / SR if a.any() else 0
    niv = 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)
    res.append(dict(c=c, v=v, co=co, cod=cod, ce=ce, der=der, dq=dq, lag=lag, niv=niv))
    lignes.append("%04X\t%s\tv%02d\t%.3f\t%.3f\t%.1f\t%.3f\t%.3f\t%.3f\t%.4f\t%.1f" % (c, v["perso"], v["n"], len(x) / fr, dq,
                  1000 * lag / SR, co, cod, ce, der, niv))
    pp = par_perso.setdefault(v["perso"], ([], []))
    seg_ecoute = segst[lag:lag + len(ref) + int(0.05 * SR)]
    pp[0].append(seg_ecoute); pp[0].append(np.zeros((int(0.35 * SR), 2)))
    src48 = reechantillonne(x, fr, SR) * 0.5
    pp[1].extend([np.stack([src48, src48], 1), np.zeros((int(0.3 * SR), 2)), seg_ecoute, np.zeros((int(0.8 * SR), 2))])
open(out, "w").write("\n".join(lignes) + "\n")
os.makedirs(os.path.join(ICI, "ecoute"), exist_ok=True)
for perso, (q, pq) in par_perso.items():
    for nom, parts in (("%s_qsound.wav" % perso, q), ("%s_psp_puis_qsound.wav" % perso, pq)):
        y = np.concatenate(parts)
        with wave.open(os.path.join(ICI, "ecoute", nom), "wb") as o:
            o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
            o.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
co = np.array([r["co"] for r in res]); cod = np.array([r["cod"] for r in res]); ce = np.array([r["ce"] for r in res])
der = np.array([r["der"] for r in res if r["der"] == r["der"]])
print("%d voix : correlation forme d'onde G min %.3f mediane %.3f, D min %.3f ; enveloppe min %.3f mediane %.3f ; "
      "derive de vitesse %.3f %% a %.3f %% (%d voix assez longues)" % (len(res), co.min(), np.median(co), cod.min(), ce.min(),
      np.median(ce), der.min(), der.max(), len(der)))
for r in sorted(res, key=lambda r: r["co"])[:5]:
    print("  plus faibles : %04X %s v%02d onde %.3f enveloppe %.3f derive %.4f %%" % (r["c"], r["v"]["perso"], r["v"]["n"], r["co"], r["ce"], r["der"]))
print("niveau RMS (dBFS) : min %.1f mediane %.1f max %.1f" % (min(r["niv"] for r in res), np.median([r["niv"] for r in res]), max(r["niv"] for r in res)))
