#!<workspace>/venv/bin/python
"""Compare, son par son, l'enregistrement de reference (pilote d'origine au fork, QSound LLE) et le rejeu (2e QSound
HLE) : essais_rejeu/ref_<jeu>.wav/.txt contre rej_<jeu>.wav/.txt (outils/valide_rejeu.sh). Par commande : niveau
actif (dBFS), ecart de niveau, correlation de la forme d'onde (gauche et droite, decalage cherche a +-30 ms),
correlation des enveloppes RMS 10 ms. Ecrit essais_rejeu/validation_rejeu_<jeu>.tsv et affiche le bilan."""
import sys, os, wave
import numpy as np
E = "<workspace>/work/agent_son_hyper_rom/essais_rejeu"
FR = 59.637


def lit(f):
    w = wave.open(f); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2).astype(float) / 32768
    return sr, x


def cmds(f):
    return [(float(l.split()[1]), l.split()[2]) for l in open(f) if l.startswith("C ")]


def niveau(x):
    a = np.abs(x).max(1)
    s = a > 10 ** (-60 / 20)
    if not s.any(): return -180.0
    return 20 * np.log10(np.sqrt((x[s] ** 2).mean()) + 1e-12)


def corr_lag(a, b, lag):
    n = min(len(a), len(b))
    best = -2
    for k in range(-lag, lag + 1, 1):
        if k >= 0: u, v = a[k:n], b[:n - k]
        else: u, v = a[:n + k], b[-k:n]
        d = np.sqrt((u ** 2).sum() * (v ** 2).sum())
        if d > 0: best = max(best, float((u * v).sum() / d))
    return best


def env(x, sr):
    h = sr // 100
    m = (x ** 2).mean(1)
    n = len(m) // h
    return np.sqrt(m[:n * h].reshape(n, h).mean(1))


def main(jeu):
    sr, r = lit(os.path.join(E, "ref_%s.wav" % jeu)); _, t = lit(os.path.join(E, "rej_%s.wav" % jeu))
    cr, ct = cmds(os.path.join(E, "ref_%s.txt" % jeu)), cmds(os.path.join(E, "rej_%s.txt" % jeu))
    assert len(cr) == len(ct), (len(cr), len(ct))
    pas = (cr[1][0] - cr[0][0]) if len(cr) > 1 else 2.5
    lignes = ["commande\tcode_rejeu\tniveau_ref\tniveau_rejeu\tecart_dB\tcorr_G\tcorr_D\tcorr_env"]
    res = []
    for (t0, c), (t1, c2) in zip(cr, ct):
        a = r[int(t0 * sr):int((t0 + pas - 0.07) * sr)]
        b = t[int(t1 * sr):int((t1 + pas - 0.07) * sr)]
        na, nb = niveau(a), niveau(b)
        if na < -70:
            lignes.append("%s\t%s\t%.1f\t%.1f\t\t\t\t" % (c, c2, na, nb)); continue
        # decalage par l'enveloppe, puis correlation fine autour (ech. a 12 kHz pour la vitesse)
        ea, eb = env(a, sr), env(b, sr)
        n = min(len(ea), len(eb))
        ce = float(np.corrcoef(ea[:n], eb[:n])[0, 1]) if n > 3 and ea[:n].std() > 0 and eb[:n].std() > 0 else 0.0
        d = 4
        cg = corr_lag(a[::d, 0], b[::d, 0], int(0.03 * sr / d))
        cd = corr_lag(a[::d, 1], b[::d, 1], int(0.03 * sr / d))
        res.append((c, na, nb, nb - na, cg, cd, ce))
        lignes.append("%s\t%s\t%.1f\t%.1f\t%+.2f\t%.3f\t%.3f\t%.3f" % (c, c2, na, nb, nb - na, cg, cd, ce))
    open(os.path.join(E, "validation_rejeu_%s.tsv" % jeu), "w").write("\n".join(lignes) + "\n")
    R = np.array([x[1:] for x in res])
    print("%s : %d sons compares (%d silencieux en reference) ; ecart de niveau median %+.2f dB (p5 %+.2f, p95 %+.2f) ; "
          "corr G mediane %.3f (p5 %.3f) ; corr D mediane %.3f ; corr enveloppe mediane %.3f (p5 %.3f)" %
          (jeu, len(res), len(cr) - len(res), np.median(R[:, 2]), np.percentile(R[:, 2], 5), np.percentile(R[:, 2], 95),
           np.median(R[:, 3]), np.percentile(R[:, 3], 5), np.median(R[:, 4]), np.median(R[:, 5]), np.percentile(R[:, 5], 5)))
    mauvais = [x for x in res if x[6] < 0.9 or abs(x[3]) > 1.5]
    print("  a examiner (enveloppe < 0,9 ou ecart > 1,5 dB) : %d : %s" % (len(mauvais), " ".join(x[0] for x in mauvais[:40])))


if __name__ == "__main__":
    for j in sys.argv[1:] or ["sfa1", "sfa2"]: main(j)
