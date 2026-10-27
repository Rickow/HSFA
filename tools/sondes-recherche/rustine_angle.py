#!/usr/bin/env python3
"""rustine_angle.py ZIP_HYPER ZIP_SORTIE [GROUPES] : ESSAI (pas un correctif livrable) des pertes de traduction de D-SONDES §4
dans une COPIE de l'archive d'Hyper, pour prouver la cause au banc. Les adresses valent pour l'archive du 2026-10-11
(image programme md5 366f4ba1ea66f0093ef4c29ab049460c) ; chaque site est verifie octet par octet avant d'etre ecrit.

Groupes (separes par des virgules, defaut : tout) :
  roxr  fonction d'angle de Cammy ($4BA8E = arcade $5DAEE) : les 4 « JSR $104E » (aide ROXR du recompilateur, traduite en
        talon vide) redeviennent ROXR.B #1,D6
  exg   meme fonction : « MOVE.L D3,D2 ; MOVE.L D2,D3 » -> EXG D2,D3
  bclr  meme fonction : « ANDI.L #-2,D6 ; BTST #0,D6 » (teste apres effacement) -> BCLR #0,D6
  autres  les autres EXG perdus d'Hyper : $45AC4 (arcade $5850C), $78546 / $7854E (arcade $187DC), $78588 (arcade $18822)
L'image 68K est rangee dans sz3ud.03c .. sz3.10b, 512 Ko chacun, octets echanges par mot."""
import sys, zipfile
NOP = '4e71'
SITES = {
    'roxr': [(a, '4eb90000104e', 'e216' + NOP * 2) for a in (0x4baac, 0x4bacc, 0x4bae6, 0x4bb38)],
    'exg': [(0x4bae2, '24032602', 'c543' + NOP)],
    'bclr': [(0x4bb18, '0286fffffffe08060000', '08860000' + NOP * 3)],
    'autres': [(0x45ac4, '22002001', 'c141' + NOP), (0x78546, '24012202', 'c342' + NOP),
               (0x7854e, '22002001', 'c141' + NOP), (0x78588, '20012200', 'c141' + NOP)],
}
FICHIERS = ['sz3ud.03c', 'sz3ud.04c', 'sz3.05c', 'sz3.06c', 'sz3.07c', 'sz3.08c', 'sz3.09c', 'sz3.10b']

def main():
    src, dst = sys.argv[1], sys.argv[2]
    groupes = sys.argv[3].split(',') if len(sys.argv) > 3 else list(SITES)
    z = zipfile.ZipFile(src); fich = {n: bytearray(z.read(n)) for n in z.namelist()}
    for g in groupes:
        for a, avant, apres in SITES[g]:
            b = fich[FICHIERS[a // 0x80000]]; o = a % 0x80000
            avant, apres = bytes.fromhex(avant), bytes.fromhex(apres)
            lu = bytes(b[(o + i) ^ 1] for i in range(len(avant)))
            if lu != avant: sys.exit(f'${a:06x} : {lu.hex()} au lieu de {avant.hex()} (autre construction ?)')
            for i, x in enumerate(apres): b[(o + i) ^ 1] = x
            print(f'{g:6s} ${a:06x} : {avant.hex()} -> {apres.hex()}')
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_STORED) as out:
        for n in z.namelist(): out.writestr(z.getinfo(n), bytes(fich[n]))

if __name__ == '__main__':
    main()
