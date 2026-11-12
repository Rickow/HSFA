#!/usr/bin/env python3
"""chaine_son.py -- ROM son d'Upper MAX (voix, cris, voix d'Ingrid, séquence $2C) depuis l'ISO PSP et la ROM son
hybride d'Upper (hsfa_build, étape son_upper). Enchaîne les outils des agents voix / son (état du lot 2b31) :
  1. max/outils/sons/voix_max.py      : voix des 4 persos (VAG des plXX_e.pac) -> R/converti/plXX/voix/vNN.wav
  2. max/outils/sons/banque_commune.py : se_mid.pac -> R/converti/sons_communs/ (séquences MIDI)
  3. extrait_psp.py                    : se_mid.pac, banques A / B / instruments -> OUT/communs/psp/*.wav, table43.json
  4. rend_seq.py                       : séquences $06 / $0D / $2C -> OUT/sequences/seq_XX.wav
  5. src/hsfa/table_son.py             : table des commandes son du module ro9 -> OUT/table_son_ro9.csv
  6. gen_voix_max.py                   : ROM hybride + voix -> OUT/roms_voix/ + commandes_voix_max.s
  7. gen_son_max.py                    : roms_voix + cris + voix d'Ingrid + $2C -> OUT/roms_son_max_pas/ + commandes_son_max.s

  python3 chaine_son.py --cache R --depot DEPOT --hybride ROMS_HYBRIDE --extract EXT --sortie OUT --equ DOSSIER
  R : cache MAX de regen_max.py (R/home = HOME des outils MAX, R/psp/pac, R/data/se_mid.pac)
Tout est déterministe ; les numéros de commandes sont figés dans les outils (ATTRIBUTION, CRIS, VOIX_INGRID) et
contrôlés par numeros_max.json (paires libres et commandes vues dans les trois jeux : numéros seulement)."""
import argparse, os, subprocess, sys, time

ICI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    for k in ("cache", "depot", "hybride", "extract", "sortie", "equ"): ap.add_argument("--" + k, required=True)
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    R, D, O = (os.path.abspath(x) for x in (a.cache, a.depot, a.sortie))
    for d in ("communs", "sequences", "journaux"): os.makedirs(os.path.join(O, d), exist_ok=True)
    SONS = os.path.join(D, "max", "outils", "sons"); SRC = os.path.join(D, "src", "hsfa")
    # (Windows : os.path.expanduser lit USERPROFILE, pas HOME)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HOME=os.path.join(R, "home"), USERPROFILE=os.path.join(R, "home"),
               SFA3MAX_CACHE=R,
               SFA3MAX_PAC_DIR=os.path.join(R, "psp", "pac"), HSFA_TOOLS_MAX=os.path.join(D, "tools", "max"),
               SON_MAX_OUTILS_SONS=SONS, SON_MAX_COMMUNS=os.path.join(O, "communs"),
               SON_MAX_SEQ=os.path.join(O, "sequences"), SON_MAX_SRC_HSFA=SRC, SON_MAX_HYBRIDE=os.path.abspath(a.hybride),
               SON_MAX_TABLE_PS2=os.path.join(O, "table_son_ro9.csv"), SON_MAX_VOIX=os.path.join(O, "roms_voix"),
               SON_MAX_NUMEROS=os.path.join(ICI, "numeros_max.json"), SON_MAX_EQU=os.path.abspath(a.equ))

    def etape(nom, cmd, cwd):
        t = time.time(); j = os.path.join(O, "journaux", nom + ".log")
        with open(j, "w") as f: r = subprocess.run([a.python] + cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
        der = (open(j, errors="replace").read().strip().splitlines() or [""])[-1]
        print("%s %s : code %d (%.0f s) %s" % (time.strftime("%H:%M:%S"), nom, r.returncode, time.time() - t, der[:110]), flush=True)
        if r.returncode: sys.exit("chaine_son : échec de %s (journal %s)" % (nom, j))

    etape("voix_max", ["voix_max.py", "pl26", "pl27", "pl28", "pl29"], SONS)
    etape("banque_commune", ["banque_commune.py"], SONS)
    etape("extrait_psp", [os.path.join(ICI, "extrait_psp.py")], O)
    etape("rend_seq", [os.path.join(ICI, "rend_seq.py")], O)
    code = ("import table_son as T\nT.DEC = %r\nd, p, tab, perso, ents, pt = T.charger('ro9')\n"
            "with open(%r, 'w') as f:\n    f.write('cmd,brut,genre,a,b,c,d\\n')\n"
            "    for c, e in enumerate(ents):\n        r = T.decode(e, pt); f.write('%%04X,%%s,%%s\\n' %% (c, e.hex(), ','.join(str(x) for x in r)))\n"
            % (os.path.join(os.path.abspath(a.extract), "decompressed", "%s_usa_prog68k.bin"), os.path.join(O, "table_son_ro9.csv")))
    etape("table_son_ro9", ["-c", code], SRC)
    etape("gen_voix_max", [os.path.join(ICI, "gen_voix_max.py"), os.path.join(O, "roms_voix")], O)
    etape("gen_son_max", [os.path.join(ICI, "gen_son_max.py"), os.path.join(O, "roms_son_max_pas")], O)


if __name__ == "__main__":
    main()
