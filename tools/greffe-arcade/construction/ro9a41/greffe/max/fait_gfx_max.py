#!/usr/bin/env python3
"""(L2 des MAX dans la greffe, l2_max_greffe CONCEPTION §2.2, notes/S6 §2) fait_gfx_max.py : tuiles des persos MAX pour le
pilote sfa3hamhsfa (patch coeur 0033 : membre hsfa_gfx_max.bin en $5400000, code global $A8000 + rang).

  fait_gfx_max.py --fork CACHE/fork --gfx-upper mame_ro5/hsfa_gfx.bin --gfx-greffe mame_ro9/hsfa_gfx.bin
                  --persos 26[,27,2d,2e] --sortie <constr>/banques_hx --gfx-max <fichier>

Ecrit f38NN.bin (table code local -> code global du perso, u32 petit-boutiste), segments.tsv (5 lignes : eagle, maki, yun,
ingrid, commun_max ; octets de la REGION graphique, fin exclue ; perso absent = longueur nulle) et hsfa_gfx_max.bin
(0xC00000 o). Segments a debuts CALCULES (cumul des tailles arrondies a 64 Ko, ordre fixe), stockage tasse.
Regle (S6 §1.2) : un code < G_MAX (ROM SFA3, tuiles d'Upper) reste tel quel, mais la tuile d'Upper doit etre identique,
au meme code, dans hsfa_gfx.bin de la greffe (sinon arret) ; un code >= G_MAX est renumerote $A8000 + debut + rang de
1re apparition (bits 29-30 de miroir gardes). Pas 8 de L2 (--prep) : segment commun MAX = habillage (emplacement 1 : suite libre de plan2, plan_commun_max) et aperçus (emplacement 0 : f545 prolongée). Sans --prep : n'est pas
encore pose : sa ligne est vide. Aucune donnee de jeu dans le depot : l'outil lit le cache de la session MAX."""
import argparse, os, struct, sys
G_MAX = 0x4DAAB                 # 1er code des tuiles MAX dans le cache d'Upper MAX (max_cache.py)
BASE = 0xA8000                  # code global de $5400000 (patch 0033)
T = 128                         # octets par tuile (format interne)
ALIGN = 512                     # tuiles par 64 Ko
TAILLE = 0xC00000
ORDRE = (('eagle', 0x26, 'pl26'), ('maki', 0x27, 'pl27'), ('yun', 0x2d, 'pl28'), ('ingrid', 0x2e, 'pl29'))
BUDGET_PERSO = 3 << 20

def demandes_hex(persos): return ['%02x' % int(p_, 16) for p_ in persos.split(',') if p_]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fork', required=True); ap.add_argument('--gfx-upper', required=True)
    ap.add_argument('--gfx-greffe', required=True); ap.add_argument('--persos', default='26')
    ap.add_argument('--sortie', required=True); ap.add_argument('--gfx-max', required=True)
    ap.add_argument('--prep', default=None)    # (pas 8) préparation MAX : max_plus.json / max_plus_gfx.bin -> habillage (plan2) et aperçus (f545)
    ap.add_argument('--commun0', default='545')   # banque commune d'Hyper (emplacement 0) : prolongée pour les aperçus
    a = ap.parse_args()
    demandes = {int(p_, 16) for p_ in a.persos.split(',') if p_}
    assert demandes <= {i for _, i, _ in ORDRE}, 'persos inconnus : %s' % a.persos
    src = open(os.path.join(a.fork, 'max_gfx.bin'), 'rb').read()
    up = open(a.gfx_upper, 'rb').read(); gr = open(a.gfx_greffe, 'rb').read()
    def tuile_max(g): b = src[(g - G_MAX) * T:(g - G_MAX + 1) * T]; assert len(b) == T, hex(g); return b
    membre = bytearray(); lignes = []; avant = 0
    for nom, ident, suf in ORDRE:
        debut = len(membre) // T
        if ident not in demandes:
            lignes.append((nom, '-', debut, debut)); continue
        tab = list(struct.unpack('<%dI' % (os.path.getsize(os.path.join(a.fork, suf + '_hx.bin')) // 4),
                                 open(os.path.join(a.fork, suf + '_hx.bin'), 'rb').read()))
        rang = {}
        for i, v in enumerate(tab):
            if v == 0xFFFFFFFF: continue
            fl, g = v & 0x60000000, v & 0xFFFFF
            assert v & ~0x600FFFFF == 0, 'f%d : code %08x inattendu' % (3800 + ident, v)
            if g < G_MAX:
                if g >= 0x40000:                      # tuile d'Upper reprise : meme tuile, meme code, dans la greffe
                    o = (g - 0x40000) * T
                    assert up[o:o + T] == gr[o:o + T] and len(gr) >= o + T, 'f%d : tuile d\'Upper %x differente dans la greffe' % (3800 + ident, g)
                    avant += 1
                continue
            if g not in rang: rang[g] = len(rang); membre += tuile_max(g)
            tab[i] = fl | (BASE + debut + rang[g])
        assert len(rang) * T <= BUDGET_PERSO and len(tab) <= 65536, '%s : %d tuiles (budget M5)' % (nom, len(rang))
        if ident == 0x26: assert all(g - G_MAX == r for g, r in rang.items()), 'eagle : rang != code - G_MAX (S6 §1.2)'
        open(os.path.join(a.sortie, 'f%d.bin' % (3800 + ident)), 'wb').write(struct.pack('<%dI' % len(tab), *tab))
        membre += bytes((-len(membre)) % (ALIGN * T))
        lignes.append((nom, 'f%d' % (3800 + ident), debut, len(membre) // T))
        print('fait_gfx_max : %s f%d : %d codes, %d tuiles MAX -> $%X-$%X' % (nom, 3800 + ident, len(tab), len(rang), BASE + debut, BASE + debut + len(rang) - 1))
    d5 = len(membre) // T
    if a.prep:                                     # (L2, pas 8) segment commun MAX : habillage (plan2) et aperçus (f545)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import plan_commun_max as PC
        G0 = G_MAX + os.path.getsize(os.path.join(a.fork, 'max_gfx.bin')) // T
        G_PLUS = G0 + os.path.getsize(os.path.join(a.fork, 'max_portraits_gfx.bin')) // T
        import json
        assert json.load(open(os.path.join(a.prep, 'max_plus.json'), encoding="utf-8"))['G_PLUS'] == G_PLUS, 'max_plus.json : G_PLUS d\'un autre cache'
        plus = open(os.path.join(a.prep, 'max_plus_gfx.bin'), 'rb').read()
        port = open(os.path.join(a.fork, 'max_portraits_gfx.bin'), 'rb').read()
        pl = PC.plan(len(port) // T, len(plus) // T)
        # habillage (portraits, noms, HUD) : EMPLACEMENT 1, suite libre de plan2 (plan_commun_max) : entrées remplacées par
        # les tuiles MAX rangées dans le segment commun ; les entrées d'avant (tuiles des plans d'Upper, jamais employées
        # par des objets : recensement) sont contrôlées contiguës
        fp = os.path.join(a.sortie, 'plan2.bin')
        if os.path.islink(fp):
            d_ = open(fp, 'rb').read(); os.remove(fp); open(fp, 'wb').write(d_)   # copie propre (jamais écrire dans la cible d'un lien)
        p2 = list(struct.unpack('<%dI' % (os.path.getsize(fp) // 4), open(fp, 'rb').read()))
        assert len(p2) == 0x10000, 'plan2.bin : %d entrées (65 536 attendues)' % len(p2)
        av = p2[PC.P2_BASE:PC.P2_BASE + len(pl)]
        assert all(av[k] == av[0] + k for k in range(len(av))), 'plan2 : la suite $%X- n\'est pas celle attendue' % PC.P2_BASE
        for rang, (loc, src_, k) in enumerate(pl):
            b_ = plus if src_ == 'plus' else port
            t_ = b_[k * T:(k + 1) * T]; assert len(t_) == T, '%s : tuile %d absente' % (src_, k)
            p2[loc] = BASE + len(membre) // T; membre += t_
        open(fp, 'wb').write(struct.pack('<%dI' % len(p2), *p2))
        print('fait_gfx_max : plan2 : %d entrées $%X-$%X -> tuiles MAX (avant : $%X-$%X)' % (len(pl), PC.P2_BASE, PC.P2_BASE + len(pl) - 1, av[0], av[-1]))
        # aperçus de sélection (emplacement 0, comme Upper MAX) : banque commune f<commun d'Hyper> PROLONGÉE aux codes locaux
        # de hud_apercu_max ($7000+) ; tuiles à la suite dans le segment commun ; codes natifs (< longueur d'origine) intacts
        HP = json.load(open(os.path.join(a.prep, 'max_plus.json'), encoding="utf-8"))
        fc = os.path.join(a.sortie, 'f%s.bin' % a.commun0)
        if os.path.islink(fc):
            d_ = open(fc, 'rb').read(); os.remove(fc); open(fc, 'wb').write(d_)
        t0 = list(struct.unpack('<%dI' % (os.path.getsize(fc) // 4), open(fc, 'rb').read()))
        n0 = len(t0); seg = len(membre) // T
        for pid in sorted(HP['apercu']):
            A_ = HP['apercu'][pid]
            assert A_['local'] >= n0 and A_['local'] + A_['n'] <= 0x10000, 'aperçu %s : codes $%x-$%x' % (pid, A_['local'], A_['local'] + A_['n'])
            if len(t0) < A_['local'] + A_['n']: t0 += [0xFFFFFFFF] * (A_['local'] + A_['n'] - len(t0))
            for j in range(A_['n']):
                k = A_['g'] - G_PLUS + j; t_ = plus[k * T:(k + 1) * T]; assert len(t_) == T
                t0[A_['local'] + j] = BASE + len(membre) // T; membre += t_
        open(fc, 'wb').write(struct.pack('<%dI' % len(t0), *t0))
        membre += bytes((-len(membre)) % (ALIGN * T))
        lignes.append(('commun_max', 'plan2,f%s' % a.commun0, d5, len(membre) // T))
        print('fait_gfx_max : f%s prolongée de %d à %d entrées (aperçus de sélection, tuiles $%X-)' % (a.commun0, n0, len(t0), BASE + seg))
    else: lignes.append(('commun_max', '-', d5, d5))
    assert len(membre) <= TAILLE, 'hsfa_gfx_max.bin : %x o > %x' % (len(membre), TAILLE)
    open(a.gfx_max, 'wb').write(bytes(membre) + bytes(TAILLE - len(membre)))
    with open(os.path.join(a.sortie, 'segments.tsv'), 'w', encoding="utf-8") as f:
        f.write('# nom\ttables\tdebut\tfin        (octets de la region graphique, fin exclue)\n')
        for nom, t, d, e in lignes: f.write('%s\t%s\t%X\t%X\n' % (nom, t, 0x5400000 + d * T, 0x5400000 + e * T))
    print('fait_gfx_max : membre %d o utiles / %d ; %d tuile(s) d\'Upper reprises controlees' % (len(membre), TAILLE, avant))

if __name__ == '__main__': main()
