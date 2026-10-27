#!/usr/bin/env python3
"""Symboles AUTOMATIQUES tirés du code (aucun nom inventé : noms génériques + rôle structurel) :
 - fonctions arcade : cibles d'appel JSR/BSR dont le site ou la cible est du code aligné ;
 - points d'entrée des tâches (appels du noyau $1302 = TRAP #0 avec A0 = entrée, D0 = emplacement) ;
 - aiguillages Capcom MOVE.W T(PC,Dn),Dm ; JMP/JSR T(PC,Dm) (HANDOFF §15) et leurs gestionnaires.
Sortie : _cache/auto.json"""
import sys, os, re, json, struct, collections, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desasm as D, trois
ICI = os.path.dirname(os.path.abspath(__file__))
CA = os.path.join(ICI, '..', '_cache')
ROM = '<workspace>/work/cps2/sfa3ud_prog.bin'
R_PCIX = re.compile(r'^\((-?)\$([0-9a-f]+),PC,(D[0-7])\.w\)')

def s16(v): return v - 0x10000 if v >= 0x8000 else v

def main():
    A = D.desasm(ROM, 0, 0, 0x100000, 'arc')
    rom = open(ROM, 'rb').read()
    X = trois.Trois()
    idx = {a: k for k, (a, *_r) in enumerate(A)}
    code = set(X.a2t)                       # instructions arcade alignées = code sûr
    appels = collections.defaultdict(list)
    for a, n, mn, ops in A:
        if mn in ('jsr', 'bsr', 'jmp', 'bra'):
            mm = re.match(r'^\$([0-9a-f]+)(\.l)?$', ops)
            if mm:
                t = int(mm.group(1), 16)
                appels[t].append((a, mn))
    fonctions = {}
    for t, sites in appels.items():
        if t >= 0x100000 or t not in idx: continue
        js = [s for s, mn in sites if mn in ('jsr', 'bsr')]
        if not js: continue
        if t in code or any(s in code for s in js):
            fonctions[t] = {'appels': len(js), 'sauts': len(sites) - len(js)}
    # tâches
    taches = {}
    for k, (a, n, mn, ops) in enumerate(A):
        if mn == 'jsr' and ops == '$1302.l':
            ent = slot = None
            for q in range(k-1, k-6, -1):
                b = A[q]; mm = None
                if b[2] in ('movea.l', 'lea'):
                    mm = re.match(r'#?\$([0-9a-f]+)(?:\.l)?, A0$', b[3])
                    if b[2] == 'lea' and not mm:
                        m2 = re.match(r'\(\$([0-9a-f]+),PC\), A0', b[3])
                        if m2: mm = m2
                if mm and ent is None: ent = int(mm.group(1), 16)
                if b[2] in ('move.w', 'moveq') and b[3].endswith('D0') and slot is None:
                    m3 = re.match(r'#\$([0-9a-f]+)', b[3]); slot = int(m3.group(1), 16) if m3 else None
            if ent is not None:
                taches.setdefault(ent, {'emplacements': set(), 'sites': []})
                taches[ent]['emplacements'].add(slot); taches[ent]['sites'].append(a)
    for v in taches.values(): v['emplacements'] = sorted(x for x in v['emplacements'] if x is not None)
    # aiguillages
    aig = []
    for k in range(1, len(A)):
        a, n, mn, ops = A[k]
        if mn not in ('jmp', 'jsr'): continue
        m1 = R_PCIX.match(ops)
        if not m1: continue
        p = A[k-1]
        if p[2] != 'move.w': continue
        m0 = R_PCIX.match(p[3])
        if not m0 or not p[3].endswith(', ' + m1.group(3)): continue
        d0 = int(m0.group(2), 16) * (-1 if m0.group(1) else 1)
        d1 = int(m1.group(2), 16) * (-1 if m1.group(1) else 1)
        tb0 = p[0] + 2 + d0; tb1 = a + 2 + d1
        if tb0 != tb1: continue
        tb = tb0
        # sélecteur : chargement de l'index juste avant
        sel = None
        for q in range(k-2, max(0, k-5), -1):
            b = A[q]
            if b[3].endswith(', ' + m0.group(3)) and b[2].startswith('move'):
                sel = (b[2], b[3].rsplit(',', 1)[0].strip()); break
        ents = []; lim = None
        for i in range(256):
            o = tb + 2 * i
            if lim is not None and o >= lim: break
            if o + 2 > len(rom): break
            off = s16(struct.unpack_from('>H', rom, o)[0])
            tgt = tb + off
            if off & 1 or not (0 <= tgt < 0x100000) or tgt == o: break
            if tgt not in idx: break
            ents.append(tgt)
            if tgt > tb: lim = tgt if lim is None else min(lim, tgt)
        if not ents: continue
        aig.append({'table': tb, 'site': a, 'appel': mn == 'jsr', 'selecteur': sel, 'cas': ents,
                    'aligne': a in code})
    json.dump({'fonctions': {str(k): v for k, v in fonctions.items()},
               'taches': {str(k): v for k, v in taches.items()}, 'aiguillages': aig},
              open(os.path.join(CA, 'auto.json'), 'w'))
    print('fonctions arcade appelées (code vérifié) :', len(fonctions))
    print('tâches :', {hex(k): v['emplacements'] for k, v in taches.items()})
    print('aiguillages :', len(aig), 'dont sur code aligné', sum(1 for x in aig if x['aligne']),
          '; cas :', sum(len(x['cas']) for x in aig))

if __name__ == '__main__':
    main()
