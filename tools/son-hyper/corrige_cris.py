#!/usr/bin/env python3
"""Cris de degats et K.O. des versions ZERO / ZERO 2 / ALPHA d'Hyper : remplace, dans la section « cris par version »
de hsfa_rejeu_table.txt (codes $4000 + 8 v + n, cote 2 $4500 + 8 v + n, gen_redirection.py), les cris choisis par
ressemblance (correspondance.py) par ceux que l'arcade joue vraiment (cris_arcade.tsv, mesures du 2026-10-16).

  n = 0, 4 : K.O.  ;  n = 1, 2 : cri de degats  ;  n = 3 : SFA1 le meme, SFA2 le cri « fort »  ;  n = 5, 6 : inchanges.

Seules les versions deja redirigees (une ligne $4000 + 8 v existe) sont touchees : la table T_CRIS_V du programme
traduit ne change pas, aucune retraduction n'est necessaire. Idempotent.
  corrige_cris.py <hsfa_rejeu_table.txt> [sortie]      (sans sortie : ecrit en place)
  corrige_cris.py <sfa3hhsfa.zip> <sortie.zip>          (zip d'Hyper deja construit : seul le membre
                                                         hsfa_rejeu_table.txt change, les autres sont recopies tels quels)
"""
import os, re, sys, zipfile
ICI = os.path.dirname(os.path.abspath(__file__))
CB = {"sfa1": 0x2000, "sfa2": 0x3000}


def cote2(jeu, c):                       # = gen_rejeu.cote2 (copie : ce script ne depend que de la bibliotheque standard)
    if 0x100 <= c < 0x200: return c + 0x100
    if jeu == "sfa2" and 0x300 <= c < 0x380: return c + 0x80
    return c


def mesures():
    m = {}
    for l in open(os.path.join(ICI, "cris_arcade.tsv")):
        if l.startswith("#") or not l.strip(): continue
        jeu, base, nom, deg, fort, ko, src = l.rstrip("\n").split("\t")
        m[(jeu, int(base, 16))] = dict(nom=nom, deg=int(deg, 16), fort=int(fort, 16), ko=int(ko, 16), src=src)
    return m


def applique(lignes, journal=None):
    """lignes : contenu de la table (liste de str) -> nouvelle liste ; journal : liste ou ecrire les changements"""
    M = mesures()
    codes = {int(x.split()[1], 16) for x in lignes if x.startswith("CODE ")}
    ent = {}                                              # code $4xxx -> (indice de ligne, genre, cible)
    for i, x in enumerate(lignes):
        t = x.split()
        if len(t) == 3 and t[0] in ("REF", "ALIAS") and 0x4000 <= int(t[1], 16) < 0x4A00:
            ent[int(t[1], 16)] = (i, t[0], int(t[2], 16))
    # bloc du K.O. mesure -> perso (pour les versions dont toutes les lignes sont des REF)
    par_ko = {(j, v["ko"]): b for (j, b), v in M.items()}
    blocs = {}
    for (j, b), v in M.items(): blocs.setdefault(j, []).append((v["ko"], b))
    out = list(lignes)
    for v in range(128):
        nb = 0x4000 + 8 * v
        if nb not in ent: continue
        jeu = "sfa1" if 0x30 <= v < 0x40 else "sfa2" if 0x40 <= v < 0x80 else None
        if not jeu: continue
        base = None
        for n in range(7):                                # un ALIAS donne le perso : code SFA3 = $300 + $20 base + n
            e = ent.get(nb + n)
            if e and e[1] == "ALIAS" and 0x300 <= e[2] - n < 0x540 and (e[2] - n - 0x300) % 0x20 == 0:
                base = (e[2] - n - 0x300) // 0x20; break
        if base is None:                                  # sinon : le bloc de la cible du K.O. (REF)
            e = ent.get(nb)
            if e and e[1] == "REF":
                c = e[2] - CB[jeu]
                cand = [b for ko, b in sorted(blocs[jeu]) if ko >= c]
                if cand: base = cand[0]
        mes = M.get((jeu, base))
        if not mes: continue
        for n, c in ((0, mes["ko"]), (1, mes["deg"]), (2, mes["deg"]), (3, mes["fort"]), (4, mes["ko"])):
            for cote in (0, 0x500):
                k = nb + cote + n
                if k not in ent: continue
                cible = CB[jeu] + (cote2(jeu, c) if cote else c)
                if cible not in codes: continue
                i, genre, ancien = ent[k]
                nouveau = "REF %04X %04X" % (k, cible)
                if out[i] != nouveau:
                    if journal is not None:
                        journal.append("%02X %-8s n=%d cote %d : %s %04X -> REF %04X (%s)" %
                                       (v, mes["nom"], n, 2 if cote else 1, genre, ancien, cible, mes["src"]))
                    out[i] = nouveau
    return out


def main():
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
    j = []
    if src.lower().endswith(".zip"):
        if dst == src: raise SystemExit("zip : donner un fichier de sortie different")
        with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w") as zo:
            for info in zi.infolist():
                d = zi.read(info)
                if info.filename == "hsfa_rejeu_table.txt":
                    d = "\n".join(applique(d.decode().split("\n"), j)).encode()
                zo.writestr(info, d, compress_type=info.compress_type)
    else:
        L = open(src).read().split("\n")
        open(dst, "w").write("\n".join(applique(L, j)))
    for x in j: print(x)
    print("%d ligne(s) changee(s)" % len(j), file=sys.stderr)


if __name__ == "__main__":
    main()
