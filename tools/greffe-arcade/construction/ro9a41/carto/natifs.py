#!/usr/bin/env python3
"""Surface native (critere natmiss, decoupage par cibles de jal comme hooks_fork.py) : appels du code RECOMPILE
vers le moteur PS2 (hors module) et vers les fonctions natives du module ; aides du recompilateur ; aiguillages
'sll 2' hors code natif. Par module. Sortie : natifs_<mod>.json (cible -> sites)."""
import os, json, collections
os.environ["GRAIN"] = "jal"
import commun as C

AIDES = {'ro3': [0x380360, 0x3806c0, 0x380a20, 0x380d00], 'ro5': [0x22b00, 0x22e60, 0x231c0, 0x234a0],
         'ro9': [0x22dc0, 0x23120, 0x23480, 0x23610]}          # fichier ; homologues etablis par points_entree.py

def main():
    allres = {}
    for mod in ('ro3', 'ro5', 'ro9'):
        e = C.header(mod)['code_end']; F = C.funcs(mod)
        nat = {}
        for a, b in F:
            s = C.seg(mod, a, b); n = C.is_native(s)
            # relais / fonctions vides : pas du C (meme regle que natmiss.native)
            nat[a] = n[0] and n[2] > 8
        sites = collections.defaultdict(list); sll2 = []; aides = collections.Counter()
        for a, b in F:
            if nat[a]: continue
            L = C.seg(mod, a, b)
            for i, x in enumerate(L):
                if x.m == 'jal':
                    t = x.tgt - C.BASE
                    if t in AIDES[mod]: aides[AIDES[mod].index(t)] += 1; continue
                    if t < 0 or t >= e: sites[('moteur PS2', t)].append(x.va)
                    elif nat.get(t): sites[('natif du module', t)].append(x.va)
                if x.m == 'sll' and x.sa == 2:
                    for y in L[i+1:i+8]:
                        if y.m in ('jr', 'jalr') and y.rs != 31:
                            if any(z.m == 'lw' for z in L[i+1:L.index(y)]): sll2.append(x.va)
                            break
        per = collections.Counter(k for k, _ in sites); nsites = collections.Counter()
        for (k, t), v in sites.items(): nsites[k] += len(v)
        print("%s : natives (fonctions jal-grain) %d (%d o) ; cibles appelees par le code recompile : %s ; sites : %s" % (
            mod, sum(nat.values()), sum(b - a for a, b in F if nat[a]), dict(per), dict(nsites)))
        print("     aides du recompilateur (movem_push, movem_pop, andi_ccr, abcd) : %s" % [aides[k] for k in range(4)])
        print("     aiguillages 'sll 2' dans le code recompile : %d  %s" % (len(sll2), ' '.join('%x' % v for v in sll2)))
        allres[mod] = {"%s %x" % (k, t): ["%x" % s for s in v] for (k, t), v in sites.items()}
        allres[mod + '_sll2'] = ['%x' % v for v in sll2]
    json.dump(allres, open(os.path.join(C.OUT, "natifs.json"), "w"), indent=0)
    # cibles moteur communes / propres
    tg = {m: {k.split()[-1] for k in allres[m] if k.startswith('moteur')} for m in ('ro3', 'ro5', 'ro9')}
    print("cibles moteur : ro9 %d, communes avec ro3 %d, avec ro5 %d ; propres a ro9 : %s" % (
        len(tg['ro9']), len(tg['ro9'] & tg['ro3']), len(tg['ro9'] & tg['ro5']), sorted(tg['ro9'] - tg['ro5'] - tg['ro3'])))
    print("cibles moteur de ro3 absentes de ro9 : %s" % sorted(tg['ro3'] - tg['ro9']))

if __name__ == "__main__":
    main()
