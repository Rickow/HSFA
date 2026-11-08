#!/usr/bin/env python3
# compare_zips.py A B : deux sorties de construction (hsfa_build.py --sortie) : md5 des zips de même nom dans
#   A/archives et B/archives, puis membres qui changent (CRC, taille, date), apparaissent ou disparaissent.
#   (repris de l'outil de la version v159 du traducteur)
import hashlib, os, sys, zipfile
if len(sys.argv) != 3:
    sys.exit('usage : compare_zips.py SORTIE_A SORTIE_B   (dossiers contenant archives/*.zip)')
A, B = sys.argv[1], sys.argv[2]
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
for n in sorted(set(os.listdir(os.path.join(A, 'archives'))) | set(os.listdir(os.path.join(B, 'archives')))):
    if not n.endswith('.zip'): continue
    pa, pb = os.path.join(A, 'archives', n), os.path.join(B, 'archives', n)
    if not (os.path.exists(pa) and os.path.exists(pb)): print(n, 'absent d\'un côté'); continue
    ma, mb = md5(pa), md5(pb)
    print('%-20s A %s  B %s  %s' % (n, ma[:8], mb[:8], 'IDENTIQUE' if ma == mb else 'DIFFÈRE'))
    za, zb = zipfile.ZipFile(pa), zipfile.ZipFile(pb)
    ia = {i.filename: i for i in za.infolist()}; ib = {i.filename: i for i in zb.infolist()}
    for m in sorted(set(ia) | set(ib)):
        a, b = ia.get(m), ib.get(m)
        if a is None or b is None: print('   %-28s %s' % (m, 'NOUVEAU' if a is None else 'RETIRÉ')); continue
        if (a.CRC, a.file_size) != (b.CRC, b.file_size) or a.date_time != b.date_time:
            print('   %-28s CRC %08x → %08x  taille %d → %d' % (m, a.CRC, b.CRC, a.file_size, b.file_size))
