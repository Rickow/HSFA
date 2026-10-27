#!/usr/bin/env python3
"""Prepare le dossier des modules pour la construction d'Hyper avec la redirection des voix (SON-HYPER-ROM.md §13),
c.-a-d. ce que scripts/validation/valide_tout.sh lit dans $HSFA_WORKSPACE/work/modules_son :
  - un lien vers chaque module extrait (<extrait>/*_prog68k.bin), sauf ro9 ;
  - ro9_usa_prog68k.bin = module ro9 extrait + correctif_module_ro9.tsv (70 mots, chaque ancien mot controle) ;
  - son_donnees_ro9.bin = bloc de donnees de la redirection (sortie redirection_68k/donnees.bin de gen_redirection.py).

  prepare_modules_son.py <dossier des modules extraits> <donnees.bin> <sortie>

Aucune donnee de jeu n'est dans le depot : les modules viennent de l'ISO de l'utilisateur (tools/extraction/).
Controle (2026-10-24) : module ro9 corrige md5 dcda2bbac9751efa89122cb2f1cd0457 (GREFFE-ETAPE2.md, table des sources).
"""
import os, shutil, struct, sys
ICI = os.path.dirname(os.path.abspath(__file__))

def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, donnees, out = sys.argv[1:]
    os.makedirs(out, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if not f.endswith("_prog68k.bin") or f.startswith("ro9_"):
            continue
        d = os.path.join(out, f)
        if os.path.lexists(d):
            os.remove(d)
        os.symlink(os.path.abspath(os.path.join(src, f)), d)
    m = bytearray(open(os.path.join(src, "ro9_usa_prog68k.bin"), "rb").read())
    n = 0
    tsv = os.environ.get("CORRECTIF", os.path.join(ICI, "correctif_module_ro9.tsv"))
    for l in open(tsv, encoding="utf-8"):
        c = l.rstrip("\n").split("\t")
        if not c[0] or c[0].startswith("decalage"):
            continue
        o, ancien, nouveau = int(c[0], 16), int(c[1], 16), int(c[2], 16)
        (mot,) = struct.unpack_from("<I", m, o)          # mots MIPS petit-boutistes
        if mot != ancien:
            sys.exit("module inattendu en %06X : %08X au lieu de %08X (autre version du module ?)" % (o, mot, ancien))
        struct.pack_into("<I", m, o, nouveau)
        n += 1
    open(os.path.join(out, "ro9_usa_prog68k.bin"), "wb").write(m)
    shutil.copyfile(donnees, os.path.join(out, "son_donnees_ro9.bin"))
    print("%d mots corriges ; %s" % (n, out))

if __name__ == "__main__":
    main()
