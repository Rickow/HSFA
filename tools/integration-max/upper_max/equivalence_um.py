#!/usr/bin/env python3
"""equivalence_um.py A B -- (script_uppermax) deux constructions d'Upper MAX (A = ROM graphique d'arcade, B = voie ISO
seule) affichent-elles les MÊMES tuiles ? D'après agent_build/iso_seule/equivalence.py (BUILD §5.4) : pour chaque table
du banc (local -> code), on compare le CONTENU 16×16 désigné, lu dans le zip produit (ROM sz3.13m-20m décodée pour les
codes < $40000, membre hsfa_gfx.bin pour $40000-$7FFFF), avec les règles du banc (tuile 16×16 ou absente ; plans :
fenêtre, sinon code brut). Tables : travail/mame_ro5um/banc/banques_hx (Upper + persos MAX) et travail/mame_ro5/banques_hx.
Ensuite : octets différents de hsfa_ext.bin, rapportés aux tuiles qu'ils désignent quand ce sont des codes."""
import os, sys, zipfile, numpy as np
U = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
import cps2rom
VIDE = 0xFFFFFFFF


def charge(build):
    z = os.path.join(build, "sfa3umhsfa.zip")                  # v0.1.11 : a la racine de la sortie ; avant : archives/
    z = zipfile.ZipFile(z if os.path.isfile(z) else os.path.join(build, "archives", "sfa3umhsfa.zip"))
    T = cps2rom.decode({s: z.read("sz3.%s" % s) for g in cps2rom.GROUPS for s in g})
    b0 = z.read("hsfa_gfx.bin"); b0 = b0[:len(b0) // 128 * 128]
    a = np.unpackbits(np.frombuffer(b0, np.uint8).reshape(-1, 16, 2, 4, 1), axis=-1)
    H = (a.astype(np.uint8) << np.arange(4, dtype=np.uint8).reshape(1, 1, 1, 4, 1)).sum(3).astype(np.uint8).reshape(-1, 16, 16)
    return T, H, z


def contenu(T, H, t):
    out = np.full((len(t), 16, 16), 255, np.uint8)
    ok = t != VIDE
    r = ok & (t < 0x40000); out[r] = T[t[r].astype(np.int64)]
    h = ok & (t >= 0x40000); hi = (t[h] - 0x40000).astype(np.int64)
    dedans = hi < len(H); tmp = np.full((int(h.sum()), 16, 16), 254, np.uint8); tmp[dedans] = H[hi[dedans]]; out[h] = tmp
    return out


def main():
    A, B = sys.argv[1], sys.argv[2]
    (TA, HA, ZA), (TB, HB, ZB) = charge(A), charge(B)
    SA, SB = TA.reshape(-1, 16), TB.reshape(-1, 16)
    for dossier in ("mame_ro5um/banc/banques_hx", "mame_ro5/banques_hx"):
        da, db = (os.path.join(x, "travail", dossier) for x in (A, B))
        res = dict(tables=0, entrees=0, codes_diff=0, egales=0, diff=0); ex = []
        for f in sorted(set(os.listdir(da)) | set(os.listdir(db))):
            if not f.endswith(".bin"): continue
            ta = np.fromfile(os.path.join(da, f), "<u4"); tb = np.fromfile(os.path.join(db, f), "<u4")
            if f == "plan2.bin":     # Upper : plans servis tels quels (HSFA_PLANS) ; table plan2 non affichée
                ex.append(("plan2.bin (non affichée)", "%d / %d entrées" % (len(ta), len(tb)))); continue
            assert len(ta) == len(tb), f
            res["tables"] += 1; res["entrees"] += len(ta); res["codes_diff"] += int((ta != tb).sum())
            if f in ("plan1.bin", "f312.bin"):
                unite, deb, dec = {"plan1.bin": (8, 0x20000, 0), "f312.bin": (64, 0x4000, 0xb00)}[f]
                cc = []
                for S_, t in ((SA, ta), (SB, tb)):
                    ok = (t != VIDE) & (t >= deb) & (t - deb <= 0xFFFF)
                    g = np.where(ok, t, ((np.arange(len(t)) + dec) & 0xFFFF) + deb).astype(np.int64)
                    cc.append(S_[g[:, None] * unite + np.arange(unite)[None, :]])
                eg = (cc[0] == cc[1]).all((1, 2))
            else:
                eg = (contenu(TA, HA, ta) == contenu(TB, HB, tb)).all((1, 2))
            res["egales"] += int(eg.sum()); res["diff"] += int((~eg).sum())
            if (~eg).any(): ex.append((f, int((~eg).sum())))
        print("%s : %s" % (dossier, res))
        if ex: print("   tables différentes :", ex[:40])
    # hsfa_ext.bin : mots différents
    ea, eb = np.frombuffer(ZA.read("hsfa_ext.bin"), ">u2"), np.frombuffer(ZB.read("hsfa_ext.bin"), ">u2")
    d = np.nonzero(ea != eb)[0]
    print("hsfa_ext.bin : %d mots différents ; plages (adresse 68K) :" % len(d))
    if len(d):
        cuts = np.nonzero(np.diff(d) > 8)[0]; starts = np.r_[d[0], d[cuts + 1]]; ends = np.r_[d[cuts], d[-1]]
        for s, e in zip(starts, ends):
            print("   $%06X-$%06X (%d mots) A %s / B %s" % (0xA00000 + 2 * s, 0xA00000 + 2 * e + 1, e - s + 1,
                  " ".join("%04x" % x for x in ea[s:min(e + 1, s + 6)]), " ".join("%04x" % x for x in eb[s:min(e + 1, s + 6)])))


if __name__ == "__main__":
    main()
