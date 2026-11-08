#!/usr/bin/env python3
"""Traduction 68K (mode 'hote', traducteur existant importe en lecture) de chaque fonction d'un module,
mise en cache : sert a comparer les modules au niveau 68K (insensible a la version du recompilateur, §52).
Usage : nice -n 19 python3 tr68k.py ro9 [ro5 ro3]"""
import sys, os, pickle, time
import commun as C
os.environ.setdefault("MEMMODE", "hote")
import translate as T

def run(mod):
    buf = C.load(mod); out = {}
    t0 = time.time(); err = 0
    F = C.funcs(mod)
    for k, (a, b) in enumerate(F):
        try:
            o, _ = T.translate(buf, a, b)
            # (va, mnemonique, mots) -> on garde le PREMIER mot (opcode) et le mnemonique sans annotation
            out[a] = [(va, (ws[0] if ws else None), mn.split('  [')[0]) for va, mn, ws in o]
        except Exception as e:
            out[a] = None; err += 1
        if k % 500 == 0: print(mod, k, len(F), "%.0fs" % (time.time()-t0), flush=True)
    pickle.dump(out, open(os.path.join(C.OUT, "tr68k_%s%s.pkl" % (mod, C.SUF)), "wb"))
    print(mod, "fonctions", len(F), "erreurs", err, "%.0fs" % (time.time()-t0))

if __name__ == "__main__":
    for m in sys.argv[1:]: run(m)
