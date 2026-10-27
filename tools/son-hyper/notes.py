#!/usr/bin/env python3
"""Journal d'injection (C t code / Q t valeur registre) -> notes jouees par commande.
QSound : voie v = registres v*8+0..7 (1 debut, 2 hauteur, 3 phase = depart de la note, 4 longueur de boucle, 5 fin,
6 volume) ; la banque de la voie v est dans le registre ((v-1)&15)*8 (registre « 0 » de la voie precedente).
Une note = ecriture de la phase (registre v*8+3). Hauteur retenue = premiere hauteur non nulle ecrite apres la note.
Usage (module) : notes(journal) -> {code: [dict(t, v, banque, debut, fin, boucle, hauteur, vol, duree)]}"""
import sys, json

def notes(path):
    res, cur, regs, ouvertes = {}, None, {}, {}
    t0 = 0
    for l in open(path):
        p = l.split()
        if not p: continue
        if p[0] == 'C':
            cur = int(p[2], 16); res[cur] = []; t0 = float(p[1]); ouvertes = {}
            continue
        if p[0] != 'Q' or cur is None: continue
        t, val, r = float(p[1]) - t0, int(p[3], 16), int(p[2], 16)
        if r >= 0x80: continue
        regs[r] = val
        v, k = r >> 3, r & 7
        if k == 3:
            n = dict(t=round(t, 4), v=v, banque=regs.get(((v - 1) & 15) * 8, 0) & 0x7fff, debut=regs.get(v * 8 + 1, 0),
                     fin=regs.get(v * 8 + 5, 0), boucle=regs.get(v * 8 + 4, 0), hauteur=regs.get(v * 8 + 2, 0),
                     vol=regs.get(v * 8 + 6, 0), duree=None)
            res[cur].append(n); ouvertes[v] = n
        elif k == 2 and v in ouvertes:
            n = ouvertes[v]
            if val and not n.get('h_fixe'):
                n['hauteur'] = val; n['h_fixe'] = True
            if val == 0 and n['duree'] is None and n.get('h_fixe'):
                n['duree'] = round(t - n['t'], 4)
        elif k == 6 and v in ouvertes and val:
            ouvertes[v]['vol'] = max(ouvertes[v]['vol'], val)
    for c in res:
        for n in res[c]: n.pop('h_fixe', None)
    return res

if __name__ == '__main__':
    r = notes(sys.argv[1])
    for c, L in r.items():
        print('%04x %d %s' % (c, len(L), ' | '.join('v%d b%02x %04x-%04x bcl%04x h%04x t%.2f' % (n['v'], n['banque'] & 0xff,
              n['debut'], n['fin'], n['boucle'], n['hauteur'], n['t']) for n in L[:6])))
