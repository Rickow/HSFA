#!/usr/bin/env python3
"""ETAPE 6 : prototype de greffe. Routines d'Upper (defaut : recherche du prochain adversaire 0x250EF0 et ses appeles
absents d'Hyper 0x24F9D0, 0x24F020) -> zone Z80 d'Hyper ; tables A5 (etape 3) et donnees (etape 4) ; ecrit
  constructions/proto/ro9_augmente.bin   (module ro9 + greffe, en-tete inchange)
  constructions/proto/greffe_donnees.bin (bloc de donnees, exec GRF_X) + greffe_ptrs.txt (decalages des pointeurs de code)
  constructions/proto/greffe.json        (zone, blocs, relogements, rapport)
puis, avec --construire, lance l'assemblage a blanc (copie du traducteur, MODULE=ro9, TRAVAIL=constructions/proto/b9)."""
import os, sys, json, pickle, struct, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import greffe as GR
G = GR.G; P = os.path.join(G, 'constructions', 'proto')
GR5 = pickle.load(open(os.path.join(GR.EU, 'graphe_ro5.pkl'), 'rb'))

def main():
    rs = [int(x, 16) for x in os.environ.get("ROUTINES", "250EF0,24F9D0,24F020").split(',')]
    os.makedirs(P, exist_ok=True)
    R = pickle.load(open(os.path.join(G, 'donnees', 'relogement_a5.pkl'), 'rb'))['table']
    D = pickle.load(open(os.path.join(G, 'donnees', 'donnees_greffe.pkl'), 'rb'))
    vs = {v for r in rs for v in GR5['data'].get(r, ())}
    copie = [c for c in D['copie'] if c[0] in vs]; reutil = {v: w for v, w in D['reutil'].items() if v in vs}
    a5 = lambda d: (R.get(d, d) if d in R else d)
    g = GR.Greffe(rs, a5=a5)
    blob, ptr_code, plages = GR.bloc_donnees(g, reutil, copie)
    rap_donnees = {k: list(v) for k, v in g.rap.items()}; g.rap.clear()
    mod = g.module(open(os.environ.get("MODULE_SOURCE", "<workspace>/work/agent_son_hyper_rom/redirection_68k/ro9_usa_prog68k_son.bin"), "rb").read())
    open(os.path.join(P, 'ro9_augmente.bin'), 'wb').write(mod)
    open(os.path.join(P, 'greffe_donnees.bin'), 'wb').write(blob or b'\0\0\0\0')
    open(os.path.join(P, 'greffe_ptrs.txt'), 'w').write(''.join('%x\n' % o for o in ptr_code))
    h = lambda x: hex(x) if isinstance(x, int) else x
    rapport = {k: [[h(z) for z in e] for e in v] for k, v in g.rap.items()}
    json.dump(dict(routines=[hex(r) for r in rs], zone=[hex(g.g0), hex(g.fin)],
                   blocs=[[hex(a), hex(b), hex(n)] for a, b, n in g.place], donnees_copiees=[[hex(v), n] for v, n, _ in copie],
                   donnees_reutilisees={hex(v): hex(w) for v, w in reutil.items()}, bloc=hex(GR.GRF_X), taille_bloc=len(blob),
                   pointeurs_code=len(ptr_code), rapport=rapport, rapport_donnees={k: len(v) for k, v in rap_donnees.items()}),
              open(os.path.join(P, 'greffe.json'), 'w'), indent=1)
    print("greffe : %d routines, %d o de MIPS en [%#x, %#x) ; donnees : %d segments copies (%d o), %d reutilises, %d pointeurs de code" % (
        len(rs), g.fin - g.g0, g.g0, g.fin, len(copie), len(blob), len(reutil), len(ptr_code)))
    for k, v in g.rap.items(): print("  %-22s %d" % (k, len(v)))
    if '--construire' in sys.argv:
        env = dict(os.environ, MODULE='ro9', TRAVAIL=os.path.join(P, 'b9'), XDATA='<workspace>/work/xdata/X_DATA.BIN',
                   MODULE_FICHIER=os.path.join(P, 'ro9_augmente.bin'), GREFFE_C0='%x' % g.g0,
                   HSFA_SON_DONNEES='<workspace>/work/agent_son_hyper_rom/redirection_68k/donnees.bin',
                   HSFA_GREFFE_DONNEES=os.path.join(P, 'greffe_donnees.bin'), HSFA_GREFFE_X='%x' % GR.GRF_X,
                   HSFA_GREFFE_PTRS=os.path.join(P, 'greffe_ptrs.txt'))
        with open(os.path.join(P, 'construction.log'), 'w') as f:
            subprocess.run(['nice', '-n', '19', 'python3', 'mame_test.py'], cwd=os.path.join(G, 'untranspile'), env=env, stdout=f, stderr=subprocess.STDOUT)
        print(open(os.path.join(P, 'construction.log')).read().splitlines()[-1])

if __name__ == "__main__":
    main()
