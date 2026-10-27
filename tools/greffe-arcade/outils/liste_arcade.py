#!/usr/bin/env python3
"""ETAPE 2 : routines d'Upper EXECUTEES EN ARCADE ET JAMAIS EN VERSUS (traces opcodes du fork, constructions figees
fige/ro5), croisees avec la presence dans Hyper (couverture K=12 de l'etude, partenaire inverse_ro5) et avec
l'execution d'Hyper (traces h_versus / h_training sur fige/ro9).
Sorties : donnees/liste_arcade.tsv (une ligne par routine Arcade seule), donnees/liste_arcade.pkl, resume a l'ecran."""
import os, sys, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import couverture as CV
G = CV.G; EU = "<workspace>/work/etude_upper_hyper"
INV = pickle.load(open(os.path.join(EU, "inverse_ro5.pkl"), "rb"))
CK = pickle.load(open(os.path.join(EU, "couv_k.pkl"), "rb"))
A5 = pickle.load(open(os.path.join(EU, "a5.pkl"), "rb")); D5, D9 = A5['D5'], A5['D9']
ARC = [x for x in ('gagne00', 'gagne04', 'gagne02', 'perdu00', 'perdu_go') if os.path.exists(os.path.join(G, 'traces', x, 'couv.txt'))]
VS = [x for x in ('versus',) if os.path.exists(os.path.join(G, 'traces', x, 'couv.txt'))]
H9 = [x for x in ('h_versus', 'h_training') if os.path.exists(os.path.join(G, 'traces', x, 'couv.txt'))]
SCENE = {'0002': 'selection', '0004': 'VS/combat/entre-combats', '0006': 'continue', '0008': 'game over / apres fin',
         '000a': 'fin + generique', '000c': 'sortie', '000e': 'resultat VERSUS', '0000': 'init'}

def scene_de(nom):
    p = nom.split()
    if len(p) < 4: return '?'
    if p[0] != '0002': return 'hors partie (A5+0=%s)' % p[0]
    s = SCENE.get(p[1], p[1])
    if p[1] == '0004': s += ' [A5+8=%s]' % p[2]
    return s

def main():
    run = {}
    for t in ARC + VS: run[t] = CV.charge('ro5', t)
    for t in H9: run[t] = CV.charge('ro9', t)
    exA = collections.defaultdict(dict); exV = set(); exH = set()
    for t in ARC:
        for r, e in run[t][0].items(): exA[r][t] = e
    for t in VS: exV |= set(run[t][0])
    for t in H9: exH |= set(run[t][0])
    courtesA = set().union(*(set(run[t][1]) for t in ARC)) if ARC else set()
    seul = dict(exA)                                    # toutes les routines vues en Arcade ; drapeau 'vs' ci-dessous
    BA = pickle.load(open(os.path.join(EU, "bilan_absent.pkl"), "rb"))
    def etat(r):
        c = CK.get(r, 1.0); return 'absent' if c < 0.5 else ('modifie' if c < 0.9 else 'present')
    par_r = collections.defaultdict(set)
    for d in set(D5) - set(D9):
        for r in D5[d]['routines']: par_r[r].add(d)
    lignes = []
    for r in sorted(seul):
        i = INV.get(r, {}); d = seul[r]
        scenes = collections.Counter()
        for t, e in d.items():
            for nom in e['etats']: scenes[scene_de(nom)] += 1
        k0 = min(e['k0'] for e in d.values())
        p = i.get('partenaire')
        z = BA['zone'].get(r, '?'); e_ = etat(r); vs = r in exV; d = seul[r]
        if i.get('nat'): dec = 'natif'
        elif e_ == 'present' and i.get('classe') in ('identique', 'identique 68K', 'deplacements'): dec = 'REUTILISER'
        elif (z.startswith('code des persos') or z.startswith('moteur de combat')) and not any(
                not sc.startswith(('VS/combat/entre-combats [A5+8=0006]', 'hors partie')) for sc in
                {scene_de(n) for e in d.values() for n in e['etats']}): dec = 'garder Hyper (moteur/persos)'
        elif e_ == 'present': dec = 'REUTILISER (homologue a verifier)'
        elif i.get('partenaire') in exH and i.get('classe') in ('quasi identique (>=90 %)', 'modifiee (70-90 %)'): dec = 'garder Hyper (homologue proche execute par Hyper)'
        else:
            hc = any(not sc.startswith('VS/combat/entre-combats [A5+8=0006]') for sc in
                     {scene_de(n) for e in d.values() for n in e['etats']})
            dec = ('GREFFER' if not vs else 'GREFFER (variante Arcade, partagee avec VERSUS dans Upper)') + \
                  ('' if hc else ' [combat seul]')
        lignes.append(dict(r=r, vs=vs, zone=z, decision=dec, taille=i.get('taille', 0), n68=i.get('n68', 0), couv=CK.get(r, 1.0), etat=etat(r),
                           classe=i.get('classe', '?'), nat=i.get('nat'), part=p, part_vivant=(p in exH) if p else None,
                           runs=sorted(d), scenes=sorted(scenes), k0=k0, a5=sorted(par_r.get(r, ()))))
    pickle.dump(dict(lignes=lignes, exA=set(exA), exV=exV, exH=exH, courtesA=courtesA, runs=ARC + VS + H9),
                open(os.path.join(G, 'donnees', 'liste_arcade.pkl'), 'wb'))
    with open(os.path.join(G, 'donnees', 'liste_arcade.tsv'), 'w') as f:
        f.write("va_ro5\tvu_en_VERSUS\tzone_arcade\tdecision\ttaille_mips\tn68\tcouv_K12\tetat_dans_ro9\tclasse\tpartenaire_ro9\tpartenaire_execute_hyper\t"
                "parties\tpremiere_image\tscenes\tvars_A5_propres_upper\n")
        for L in lignes:
            f.write("0x%X\t%s\t%s\t%s\t%d\t%d\t%.2f\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\n" % (
                L['r'], 'oui' if L['vs'] else 'non', L['zone'], L['decision'], L['taille'], L['n68'], L['couv'], L['etat'], L['classe'],
                ('0x%X' % L['part']) if L['part'] else '', {True: 'oui', False: 'non', None: ''}[L['part_vivant']],
                ','.join(L['runs']), L['k0'], ' | '.join(L['scenes']), ' '.join('$%04X' % x for x in L['a5'])))
    # resume
    print("traces Arcade %s ; VERSUS %s ; Hyper %s" % (ARC, VS, H9))
    print("routines executees : Arcade %d, VERSUS %d ; Arcade seules %d (+ %d courtes indecidables)" % (
        len(exA), len(exV), len(set(exA) - exV), len(courtesA - set(exA) - exV)))
    for titre, sel in (("ARCADE SEULES (jamais en VERSUS)", lambda L: not L['vs']), ("vues aussi en VERSUS", lambda L: L['vs'])):
        print(titre)
        tot = collections.Counter(); n = collections.Counter(); i68 = collections.Counter()
        for L in lignes:
            if not sel(L): continue
            k = (L['decision'], L['etat'] if not L['nat'] else '')
            tot[k] += L['taille']; n[k] += 1; i68[k] += L['n68']
        for k in sorted(n):
            print("  %-62s %-8s %4d routines %7d o MIPS (%6.1f Ko) %5d instr. 68K" % (k[0], k[1], n[k], tot[k], tot[k] / 1024, i68[k]))

if __name__ == "__main__":
    main()
