"""Arbitrage des CONFLITS de routines entre la chaîne images -> code (chaine_code.py) et la Rosette du code (2026-10-11).
Méthode HSFA (METHODES-TRADUCTEUR-POUR-PSP.md) : ORACLE STATIQUE + TÉMOIN ALÉATOIRE. Pour chaque routine arcade en
conflit, les deux routines PSP candidates sont traduites (traduire.py), normalisées et alignées (LCS) sur la routine
arcade (evaluer.py : score = 2 × LCS / (n68K + ntraduit)) ; le témoin = mêmes scores pour des routines PSP du même perso
tirées au hasard. Un candidat l'emporte s'il dépasse nettement le témoin (max du témoin + 0,10) ET l'autre candidat.
Usage : python conflits.py [n° perso hexa …]"""
import os, sys, random, collections
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); sys.path.insert(0, os.path.join(ICI, "..", "rosette_code"))
os.chdir(os.path.join(ICI, "..", "rosette_code"))
import chaine_code as CC
import evaluer as EV
from traduire import traduire


def score(fa, fp, _c={}):
    k = (fa, fp)
    if k not in _c:
        try: _c[k] = 2 * EV.lcs(EV.norm_arc(fa), EV.norm_tr(traduire(fp))) / max(1, len(EV.norm_arc(fa)) + len(EV.norm_tr(traduire(fp))))
        except Exception: _c[k] = None
    return _c[k]


def arbitrer(c, n_temoin=12, graine=1):
    r = CC.chaine(c); out = []
    import rosette as RS
    _, _, _, _, _, SP = RS.run(c)
    pool = sorted(SP); rnd = random.Random(graine)
    for fa, fp_img, fp_ros in r["conflits"]:
        fa, fi, fr = int(fa, 16), int(fp_img, 16), int(fp_ros, 16)
        si, sr = score(fa, fi), score(fa, fr)
        tem = [score(fa, x) for x in rnd.sample(pool, min(n_temoin, len(pool))) if x not in (fi, fr)]
        tem = [x for x in tem if x is not None]; tmax = max(tem) if tem else 0
        if si is None or sr is None: v = "traduction impossible"
        elif si >= tmax + 0.10 and si > sr + 0.05: v = "IMAGES"
        elif sr >= tmax + 0.10 and sr > si + 0.05: v = "ROSETTE DU CODE"
        else: v = "indécis"
        out.append((hex(fa), hex(fi), si and round(si, 2), hex(fr), sr and round(sr, 2), round(tmax, 2), v))
    return out


if __name__ == "__main__":
    bilan = collections.Counter()
    for c in [int(x, 16) for x in sys.argv[1:]] or [0]:
        if c not in CC.RS.ARC_ENTRIES: continue
        for l in arbitrer(c):
            bilan[l[-1]] += 1
            print("pl%02x arcade %s : images %s (%s) | rosette %s (%s) | témoin max %s -> %s" % ((c,) + l))
    print("bilan :", dict(bilan))
