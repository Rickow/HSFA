#!/usr/bin/env python3
"""Conversions ponctuelles entre les trois espaces (mips fichier / traduit / arcade)."""
import sys, os, pickle, bisect, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fonctions as F
ICI = os.path.dirname(os.path.abspath(__file__))
CA = os.path.join(ICI, '..', '_cache')

class Trois:
    def __init__(s):
        s.C = F.carte()
        s.m = pickle.load(open(os.path.join(CA, 'alignement.pkl'), 'rb'))
        s.va2t = {}
        for t, va, _ in s.C: s.va2t.setdefault(va, t)
        s.vas = sorted(s.va2t)
        s.t2va = {}
        for t, va, _ in s.C: s.t2va.setdefault(t, va)
        s.ts = sorted(s.t2va)
        s.a2t = {}
        for t, (a, k) in s.m.items(): s.a2t.setdefault(a, t)
        s.as_ = sorted(s.a2t)
    def mips_vers_trad(s, va, tol=0x40):
        """va fichier -> 1re instruction traduite de va >= va (à tol près)"""
        i = bisect.bisect_left(s.vas, va)
        if i < len(s.vas) and s.vas[i] - va <= tol: return s.va2t[s.vas[i]], s.vas[i] - va
        return None, None
    def trad_vers_mips(s, t):
        i = bisect.bisect_right(s.ts, t) - 1
        return (s.t2va[s.ts[i]], t - s.ts[i]) if i >= 0 else (None, None)
    def trad_vers_arcade(s, t, tol=0):
        """adresse traduite -> arcade ; tol > 0 : instruction alignée suivante à tol octets près"""
        if t in s.m: return s.m[t][0], 0
        if tol:
            ks = sorted(s.m) if not hasattr(s, '_ks') else s._ks
            s._ks = ks
            i = bisect.bisect_left(ks, t)
            if i < len(ks) and ks[i] - t <= tol: return s.m[ks[i]][0] - (ks[i] - t), ks[i] - t
        return None, None
    def arcade_vers_trad(s, a, tol=0):
        if a in s.a2t: return s.a2t[a], 0
        if tol:
            i = bisect.bisect_left(s.as_, a)
            if i < len(s.as_) and s.as_[i] - a <= tol: return s.a2t[s.as_[i]] - (s.as_[i] - a), s.as_[i] - a
        return None, None

if __name__ == '__main__':
    X = Trois()
    for arg in sys.argv[1:]:
        esp, v = arg.split('=')
        v = int(v, 16)
        if esp == 'mips':
            t, d = X.mips_vers_trad(v); a = X.trad_vers_arcade(t, 16) if t is not None else None
            print('mips %x -> trad %s (+%s) -> arcade %s' % (v, t and hex(t), d, a and a[0] is not None and hex(a[0])))
        elif esp == 'arcade':
            t, d = X.arcade_vers_trad(v, 16); va = X.trad_vers_mips(t) if t is not None else None
            print('arcade %x -> trad %s -> mips %s' % (v, t and hex(t), va and hex(va[0])))
        elif esp == 'trad':
            print('trad %x -> mips %s arcade %s' % (v, X.trad_vers_mips(v), X.trad_vers_arcade(v, 16)))
