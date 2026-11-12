#!/usr/bin/env python3
"""interrupteurs_bilan.py RESULTS_FILE CONSTR_DIR [module] -- digests the results file written by interrupteurs.sh
(or interrupteurs_liste.sh): for each trial, identical to the reference or not (md5 of all the ROMs + external
blocks), failure, and the build.log lines that differ from the reference (counters). For the differing trials: number
of map lines that differ OUTSIDE addresses (text only). CONSTR_DIR = folder holding <module>_<name>/ (build.log,
carte_image.txt) and <module>_ref/. Review E8 (switches: "=0 gives a byte-identical ROM"; dead switches).
Read-only, static; output on stdout. Tool of the translator review (11/11/2026, docs/rapports/reviews/)."""
import sys, re, os, difflib, collections
if len(sys.argv)<3: sys.exit(__doc__)
RES=sys.argv[1]; CONSTR=sys.argv[2]; M=sys.argv[3] if len(sys.argv)>3 else 'ro3'
L=[l.rstrip('\n') for l in open(RES,encoding='utf-8',errors='replace') if '|' in l]
def log(n):
    p=os.path.join(CONSTR,'%s_%s'%(M,n),'build.log')
    if not os.path.exists(p): return []
    with open(p,encoding='utf-8',errors='replace') as h:
        return [re.sub(r'\$[0-9a-f]+|mips [0-9a-f]+|->[0-9a-f]+','@',x) for x in h.read().splitlines()]
def textes(n):
    p=os.path.join(CONSTR,'%s_%s'%(M,n),'carte_image.txt')
    c=collections.Counter()
    if not os.path.exists(p): return c
    for l in open(p,encoding='utf-8',errors='replace'):
        q=l.rstrip('\n').split(' ',2)
        if len(q)==3:
            t=re.sub(r'\$[0-9a-f]{5,8}\.L|\(cible [0-9a-f]+\)|T_[0-9a-f]{6}|\[mips [0-9a-f]+\]|\[PS2 [0-9a-f]+\]|\[cible[^\]]*\]|CODE_[0-9a-f_A-Z]+','@',q[2])
            c[(q[1],t)]+=1
    return c
ref=None; R=log('ref'); TR=None
for l in L:
    p=[x.strip() for x in l.split('|')]
    var=p[0] or 'ref'; f=p[1].split()
    nom=f[0][len(M)+1:]; code=f[1]; md=f[2] if len(f)>2 else '-'; ext=p[2]
    if nom=='ref': ref=(md,ext); TR=textes('ref'); print("reference %s %s"%(md,ext)); continue
    lg=log(nom)
    dl=[x for x in difflib.unified_diff(R,lg,lineterm='',n=0) if x[:1] in '+-' and x[:3] not in ('+++','---')]
    if code!='code=0':
        print("%-22s ECHEC  %s"%(var,(lg[-1] if lg else '')[:110])); continue
    if (md,ext)==ref:
        print("%-22s IDENTIQUE  journal : %s"%(var,' / '.join(x[:90] for x in dl[:6]) if dl else 'identique'))
    else:
        t=textes(nom); d=sum(((TR-t)+(t-TR)).values())
        print("%-22s different  lignes de carte (texte) : %-6d journal : %s"%(var,d,' / '.join(x[:80] for x in dl[:4])))
