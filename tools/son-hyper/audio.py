#!<workspace>/venv/bin/python
"""Outils audio (numpy seul) : lecture WAV, reechantillonnage, MFCC, DTW, correlation de forme d'onde."""
import wave, numpy as np

def lit(f):
    w = wave.open(f); n = w.getnframes(); sw = w.getsampwidth(); ch = w.getnchannels(); fr = w.getframerate()
    x = np.frombuffer(w.readframes(n), "<i2" if sw == 2 else np.uint8).astype(float)
    if sw == 1: x = x - 128
    x = x.reshape(-1, ch).mean(axis=1) / (32768.0 if sw == 2 else 128.0)
    return x, fr

def reech(x, fr, fo):
    """reechantillonnage par FFT (bande limitee)"""
    if fr == fo or len(x) == 0: return x.copy()
    n = int(round(len(x) * fo / fr))
    X = np.fft.rfft(x); m = n // 2 + 1
    Y = np.zeros(m, complex); k = min(m, len(X)); Y[:k] = X[:k]
    return np.fft.irfft(Y, n) * (n / len(x))

def rogne(x, seuil=0.02):
    """retire les silences de debut et de fin (enveloppe 5 ms)"""
    if len(x) == 0: return x
    a = np.abs(x); s = seuil * a.max()
    i = np.where(a > s)[0]
    return x[i[0]:i[-1] + 1] if len(i) else x

def mel_banc(nfft, fr, nb=26, fmin=80, fmax=None):
    fmax = fmax or fr / 2
    m = lambda f: 2595 * np.log10(1 + f / 700.0); im = lambda q: 700 * (10 ** (q / 2595.0) - 1)
    pts = im(np.linspace(m(fmin), m(fmax), nb + 2)); b = np.floor((nfft + 1) * pts / fr).astype(int)
    H = np.zeros((nb, nfft // 2 + 1))
    for i in range(nb):
        a, c, d = b[i], b[i + 1], b[i + 2]
        for k in range(a, c): H[i, k] = (k - a) / max(1, c - a)
        for k in range(c, d): H[i, k] = (d - k) / max(1, d - c)
    return H

_H = {}
def mfcc(x, fr=12000, nc=13, nb=26):
    win, hop = int(0.025 * fr), int(0.010 * fr); nfft = 512
    if len(x) < win: x = np.concatenate([x, np.zeros(win - len(x))])
    n = 1 + (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    F = x[idx] * np.hamming(win)
    P = np.abs(np.fft.rfft(F, nfft)) ** 2
    if (nfft, fr, nb) not in _H: _H[(nfft, fr, nb)] = mel_banc(nfft, fr, nb)
    E = np.log(P @ _H[(nfft, fr, nb)].T + 1e-10)
    k = np.arange(nb); D = np.cos(np.pi / nb * (k[None, :] + 0.5) * np.arange(nc)[:, None])
    C = E @ D.T
    C = C[:, 1:]                       # sans c0 (niveau)
    return C - C.mean(axis=0)          # CMN

def dtw(A, B):
    """distance DTW normalisee (cosinus), bande libre"""
    An = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9); Bn = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-9)
    C = 1 - An @ Bn.T
    n, m = C.shape
    D = np.full((n + 1, m + 1), np.inf); D[0, 0] = 0
    for i in range(1, n + 1):
        Di, Dp, ci = D[i], D[i - 1], C[i - 1]
        for j in range(1, m + 1):
            Di[j] = ci[j - 1] + min(Dp[j], Di[j - 1], Dp[j - 1])
    return D[n, m] / (n + m)

def xcorr_max(a, b):
    """correlation normalisee maximale entre deux formes d'onde (meme frequence), decalage libre"""
    if len(a) == 0 or len(b) == 0: return 0.0
    n = len(a) + len(b)
    N = 1 << (n - 1).bit_length()
    A = np.fft.rfft(a - a.mean(), N); B = np.fft.rfft(b - b.mean(), N)
    c = np.fft.irfft(A * np.conj(B), N)
    return float(np.abs(c).max() / (np.linalg.norm(a - a.mean()) * np.linalg.norm(b - b.mean()) + 1e-12))
