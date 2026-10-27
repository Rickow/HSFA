#!<workspace>/venv/bin/python
"""Empreintes MFCC (12 kHz, silences rognes, CMN) des echantillons d'un catalogue + DTW (libdtw.so)."""
import os, sys, json, ctypes, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
D = "<workspace>/work/agent_son_hyper_rom"
_lib = ctypes.CDLL(os.path.join(D, "outils", "libdtw.so")); _lib.dtw.restype = ctypes.c_double
_lib.dtw.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

def norm(M):
    M = np.ascontiguousarray(M, dtype=np.float64)
    return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)

def dtw(A, B):
    return _lib.dtw(A.ctypes.data, A.shape[0], B.ctypes.data, B.shape[0], A.shape[1])

_cache = {}
def empreinte(jeu, ech):
    k = (jeu, ech)
    if k not in _cache:
        f = os.path.join(D, "wav", jeu, "ech_%s.wav" % ech)
        x, fr = audio.lit(f)
        y = audio.rogne(audio.reech(x, fr, 12000))
        _cache[k] = dict(m=norm(audio.mfcc(y, 12000)), x=y, duree=len(y) / 12000.0)
    return _cache[k]
