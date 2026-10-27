#!/usr/bin/env python3
"""Chaines Shift-JIS (pleine chasse, textes des menus ajoutes par le portage) -> sjis_<mod>.txt, converties NFKC."""
import sys, re, unicodedata
sys.path.insert(0, '.')
import commun as C
for m in sys.argv[1:] or ['b','ro1','ro2','ro3','ro4','ro5','ro6','ro7','ro8','ro9']:
    d = C.load(m); out = []
    for mo in re.finditer(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]){3,}', d):
        s = mo.group()
        if not re.search(rb'[\x81-\x9f\xe0-\xef]', s): continue
        try: t = s.decode('shift_jis')
        except Exception: continue
        n = sum(1 for c in t if ord(c) > 0x7f)
        if n < 2: continue
        out.append('%07x %s' % (mo.start(), unicodedata.normalize('NFKC', t)))
    open('sjis_%s.txt' % m, 'w').write('\n'.join(out) + '\n')
    print(m, len(out))
