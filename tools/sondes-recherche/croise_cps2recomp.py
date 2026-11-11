#!/usr/bin/env python3
"""Croise les adresses nommées dans games/sfa3 de cps2recomp (clone local, lecture seule) avec notre index.
Usage : python3 croise_cps2recomp.py SORTIE.tsv   (dépôt tiers attendu dans /home/user/tmcleroy/cps2recomp)
Voir docs/rapports/recherche/J-CROISEMENT-CPS2RECOMP-SFA3.md."""
import re,glob,csv,collections,sys
G='/home/user/tmcleroy/cps2recomp/games/sfa3/'
files=[G+'src/sfa3.h',G+'PROGRESS.md']+sorted(glob.glob(G+'src/*.cpp'))
pat=re.compile(r'(?<![0-9A-Fa-fx+$])(?:0x)?((?:FF[89A-F][0-9A-F]{3})|(?:0[0-3][0-9A-F]{4}))(?![0-9A-Fa-f])')
hits=collections.defaultdict(list)
for f in files:
    for n,l in enumerate(open(f,encoding='utf-8'),1):
        for m in pat.finditer(l):
            a=m.group(1).upper()
            if a in('FFFFFF','FF0000','FFFF00'):continue
            hits[a].append((f.split('/sfa3/')[1],n,l.strip()[:230]))
# notre index
ours={}
def norm(x):return int(x.replace('$',''),16)
rng=[]
for r in csv.DictReader(open('/home/user/SFA-Anthology-PS2-mods/re/connaissances/sfa3_arcade.tsv',encoding='utf-8'),delimiter='\t'):
    for part in [r['adresse']]+[p for p in re.findall(r'\$[0-9A-Fa-f]{4,6}',r.get('adresse_autres') or '')]:
        part=part.strip()
        if '-' in part:
            a,b=part.split('-'); rng.append((norm(a),norm(b),r['nom']))
        elif part.startswith('$'):
            ours.setdefault(norm(part),[]).append((r['nom'],r['genre'],r['confiance']))
# champs A5 arcade
for r in csv.DictReader(open('/home/user/SFA-Anthology-PS2-mods/re/connaissances/champs.tsv',encoding='utf-8'),delimiter='\t'):
    da=(r.get('decalage_arcade') or '').strip()
    if r['structure']=='A5' and da.startswith('+$'):
        ours.setdefault(0xFF8000+int(da[2:],16),[]).append((r['nom'],'champ:A5',r['confiance']))
    for m in re.finditer(r'(?:arcade|cps2|img):\$(FF[0-9A-Fa-f]{4})',r.get('decalage_autres') or ''):
        ours.setdefault(int(m.group(1),16),[]).append((r['nom'],'champ:'+r['structure'],r['confiance']))
out=csv.writer(open(sys.argv[1],'w',encoding='utf-8'),delimiter='\t')
out.writerow(['adresse','statut','notre_nom','occurrences','premier_contexte'])
st=collections.Counter()
for a in sorted(hits):
    v=int(a,16); o=ours.get(v)
    if o: s='connu'; nn='; '.join(sorted({x[0] for x in o}))
    else:
        inr=[n for lo,hi,n in rng if lo<=v<=hi]
        s='dans_une_zone' if inr else 'nouveau'; nn='; '.join(inr[:2])
    st[s]+=1
    h=hits[a]; out.writerow(['$'+a,s,nn,len(h),f"{h[0][0]}:{h[0][1]} {h[0][2]}"])
print(st, len(hits))
