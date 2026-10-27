#!<workspace>/venv/bin/python
"""Validation EN JEU du rejeu : pour chaque son rejoue (journal HSFA_REJEU_LOG du fork : « t_us CODE -> jeu SRC ... »),
compare l'enregistrement de la partie (WAV commence a l'image 1) au son de reference de la commande source (pilote
d'origine, essais_rejeu/ref_<jeu>.wav, outils/valide_rejeu.sh) : correlation de la forme d'onde (canal gauche, decalage
cherche de -20 a +120 ms) et de l'enveloppe. Le temoin (meme partie sans redirection) donne la meme mesure au meme
instant. Usage : valide_rejeu_jeu.py <journal .rejeu> <wav> [wav temoin] -> <journal>_validation.tsv"""
import sys, os, re, wave
import numpy as np
E = "<workspace>/work/agent_son_hyper_rom/essais_rejeu"
T_IMG1 = 1 / 59.6372


def lit(f):
    w = wave.open(f); sr = w.getframerate()
    return sr, np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2).astype(float) / 32768


REF = {}
def ref(jeu, src):
    if jeu not in REF:
        sr, x = lit(os.path.join(E, "ref_%s.wav" % jeu))
        cs = {l.split()[2]: float(l.split()[1]) for l in open(os.path.join(E, "ref_%s.txt" % jeu)) if l.startswith("C ")}
        REF[jeu] = (sr, x, cs)
    sr, x, cs = REF[jeu]
    t = cs.get("%04x" % src)
    if t is None: return None
    seg = x[int(t * sr):int((t + 1.6) * sr), 0]
    nz = np.nonzero(np.abs(seg) > 1e-3)[0]
    return seg[nz[0]:nz[-1] + 1] if len(nz) else None


def mesure(rec, sr, t, r):
    a = rec[max(0, int((t - 0.02) * sr)):int((t + 0.12) * sr) + len(r), 0]
    n = 1 << int(np.ceil(np.log2(len(a) + len(r))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(r, n)), n)[:len(a) - len(r) + 1]
    e = np.concatenate([[0], np.cumsum(a ** 2)])
    en = np.sqrt((e[len(r):len(a) + 1] - e[:len(a) - len(r) + 1]) * (r ** 2).sum()) + 1e-12
    k = int(np.argmax(c / en))
    return float(c[k] / en[k]), (k / sr) - 0.02


def main():
    log, wv = sys.argv[1], sys.argv[2]
    tem = sys.argv[3] if len(sys.argv) > 3 else None
    sr, rec = lit(wv)
    rec0 = lit(tem)[1] if tem else None
    out = ["t_s\tcode\tjeu\tsource\tcorr\tdecalage_ms\tcorr_temoin"]
    res = []
    for l in open(log):
        m = re.match(r"(\d+) ([0-9A-F]{4}) -> (sfa\d) ([0-9A-F]{4})", l)
        if not m: continue
        t = int(m.group(1)) / 1e6 - T_IMG1
        r = ref(m.group(3), int(m.group(4), 16))
        if r is None or t + 1.7 > len(rec) / sr: continue
        c, dk = mesure(rec, sr, t, r)
        c0 = mesure(rec0, sr, t, r)[0] if rec0 is not None and t + 1.7 < len(rec0) / sr else float("nan")
        res.append((c, c0)); out.append("%.3f\t%s\t%s\t%s\t%.3f\t%.1f\t%.3f" % (t, m.group(2), m.group(3), m.group(4), c, dk * 1e3, c0))
    open(log.replace(".rejeu", "") + "_validation.tsv", "w").write("\n".join(out) + "\n")
    R = np.array(res)
    if len(R):
        print("%d sons rejoues mesures : correlation avec la reference mediane %.3f (min %.3f) ; temoin %s" %
              (len(R), np.median(R[:, 0]), R[:, 0].min(), "mediane %.3f (max %.3f)" % (np.nanmedian(R[:, 1]), np.nanmax(R[:, 1])) if tem else "-"))


if __name__ == "__main__":
    main()
