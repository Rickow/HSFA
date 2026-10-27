#!/usr/bin/env python3
"""Assembleur 68000 de la sortie du traducteur, avec PLACEMENT ITERATIF.

L'ancienne version inserait les mots d'extension des branchements longs APRES le
placement, sans recalculer les offsets : tout branchement situe apres le premier
branchement long etait faux. Celle-ci fait une vraie relaxation :

  1. chaque element a une taille qui depend de choix (branchement court/long, ...) ;
  2. on place avec des choix optimistes, on verifie, on allonge ce qui ne tient pas ;
  3. on recommence jusqu'a stabilite ; puis on emet les mots.

Choix laisses a l'assembleur (le traducteur ne peut pas les faire) :
  - appel terminal (JMP) : cible DANS l'unite -> BRA (court/long), ou RIEN si c'est
    l'instruction suivante (l'original 'enchainait' dans 18 % des cas) ; sinon JMP.L
  - appel (JSR) : cible dans l'unite -> BSR, sinon JSR.L
  - aiguillage 'JMP T(PC,Dn.W)' : la table est emise JUSTE APRES le JMP (forme de la ROM,
    97 % : 323b 0006 4efb 1002), entrees = dc.w cible - table
Libelles : une cible MIPS designe la premiere instruction 68K emise a partir d'elle.
"""
import sys, re, struct, bisect, os
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
import translate as T

RX_CIBLE = re.compile(r'\(cible ([0-9a-f]+)\)')
RX_MIPS  = re.compile(r'\[mips ([0-9a-f]+)\]|\[cible ([0-9a-f]+)')

class Item:
    __slots__=('va','mn','ws','kind','tgt','cond','table','choice','off','ext','hosted','data','dhost','host','esz','areg','nofix')
    def __init__(s, va, mn, ws):
        s.va=va; s.mn=mn; s.ws=list(ws); s.kind='fixed'; s.tgt=None; s.cond=None; s.nofix=False
        s.table=None; s.choice=None; s.off=0; s.ext=None; s.hosted=None; s.data=None; s.dhost=[]; s.host=None

def classify(items, buf):
    out=[]
    for va,mn,ws in items:
        it=Item(va,mn,ws)
        if not ws:
            continue                                   # entree de traitement (0 mot)
        w=ws[0]
        m=RX_CIBLE.search(mn)
        if (w&0xf000)==0x6000 and (w&0xff)==0 and len(ws)==1 and m:
            it.kind='bcc'; it.cond=w&0x0f00; it.tgt=int(m.group(1),16)
        elif w in (0x4eb9,0x4ef9) and len(ws)==3:
            mm=RX_MIPS.search(mn)
            if mm:
                it.kind='call' if w==0x4eb9 else 'jump'
                it.tgt=int(mm.group(1) or mm.group(2),16) - T.RUNTIME_BASE   # -> offset fichier MIPS
        elif w in (0x4efb,0x4ebb) and 'T_' in mn:
            it.kind='switch'; it.table=int(mn.split('T_')[1][:6],16)
            # sans 'MOVE.W T(PC,Dn),Dm' devant : forme d'origine JSR/JMP T(PC,Dn) sur une table de BRA.S
            # (HANDOFF §75) la lecture peut preceder de quelques instructions (ex. mips 0x7baac :
            # MOVE.W T(PC,D0),D1 ; MOVE.B 1(A0),D0 ; ADDQ.W #2,A0 ; JSR T(PC,D1)) : on remonte jusqu'a 4
            lu=any(o.mn.startswith('MOVE.W T_%06x'%it.table) for o in out[-4:])
            if not lu: BRAS_TABLES.add(it.table)
        elif (w&0xfff8)==0x51c8 and len(ws)==2 and m:
            it.kind='bcc'; it.cond=None; it.tgt=int(m.group(1),16); it.choice='dbcc'   # DBRA
        elif 'CODE_' in mn:
            # pointeur de code : LEA CODE_x,An / MOVE.L #CODE_x,d(An) -> mots 1-2 = NOTRE adresse
            it.kind='codeptr'; it.tgt=int(mn.split('CODE_')[1][:7],16); it.choice='_ECH' in mn
        elif (w & 0xf1ff)==0x303b and 'T_' in mn and int(mn.split('T_')[1][:6],16) in T.TABLES:
            it.kind='tblref'; it.table=int(mn.split('T_')[1][:6],16)   # MOVE.W T(PC,Dn.W),Dm (aiguillage)
        elif (w&0x3f)==0x3b and 'T_' in mn and w not in (0x4efb,0x4ebb):
            # MOVE.x T(PC,Dn),<dst> : table de DONNEES hebergee JUSTE APRES l'instruction, sautee par un BRA
            it.kind='dtab'; it.table=int(mn.split('T_')[1][:6],16)
            esz={'B':1,'W':2,'L':4}.get(re.search(r'\b(?:MOVE|ADD|SUB|AND|OR)\.(\w)',mn).group(1) if re.search(r'\b(?:MOVE|ADD|SUB|AND|OR)\.(\w)',mn) else 'W',2)
            it.data=table_bytes(buf, it.table, esz); it.esz=esz
            # FORME ABSOLUE (HANDOFF §63) : la table est lue DIRECTEMENT dans l'image des donnees du module
            # (MOVE.L An,-(SP) ; LEA donnees.L,An ; MOVE.x 0(An,Xi),<dst> ; MOVEA.L (SP)+,An). Les copies
            # hebergees s'arretaient a la reference suivante : fausses pour les tableaux de STRUCTURES
            # (champs +0/+2/+4/+6 references separement, pas de 8 : la copie du champ +2 faisait 2 octets).
            used={int(x) for x in re.findall(r'\bA([0-7])\b', mn)}
            free=[r for r in (0,1,2,3,4) if r not in used]
            if DTAB_ABS and free and 'SP' not in mn and T.addr_to_68k(it.table) is not None:
                it.choice='abs'; it.areg=free[0]
        elif (w & 0xf1ff)==0x303b and 'T_' in mn:
            it.kind='tblref'; it.table=int(mn.split('T_')[1][:6],16)   # MOVE.W T(PC,Dn.W),Dm
        out.append(it)
    # 2) Bcc qui SAUTE PAR-DESSUS un saut inconditionnel = branchement long inverse du
    #    recompilateur ('bne +2 ; j loin') : on refusionne en B(cond inverse) loin
    #    (ROM : 6744 = BEQ loin, la ou l'on produisait 6602 602c)
    merged=[]; k=0
    ovas=[o.va for o in out]
    # (HANDOFF §91) un saut qui est lui-meme CIBLE d'un autre branchement ne peut pas etre absorbe dans la fusion :
    # sa cible se resoudrait sur l'element suivant (Gen, mips 0x341358 : 'BCS atterrissage' devenu 'BCS en l'air')
    cibles={bisect.bisect_left(ovas, o.tgt) for o in out if o.kind in ('bcc','jump','call') and o.tgt is not None}
    while k < len(out):
        it=out[k]
        # la cible designe la PREMIERE instruction emise a partir d'elle (comme les libelles)
        if (it.kind=='bcc' and k+2 < len(out) and out[k+1].kind=='jump' and (k+1) not in cibles
                and it.tgt is not None and bisect.bisect_left(ovas, it.tgt)==k+2):
            j=out[k+1]; it.cond=it.cond ^ 0x0100; it.tgt=j.tgt; it.mn=it.mn+"  [fusionne avec le saut]"
            merged.append(it); k+=2; continue
        merged.append(it); k+=1
    out=merged
    # 3) ou poser chaque table d'aiguillage : apres le JMP (terminal) ; apres la prochaine
    #    rupture (saut, RTS) pour un JSR par table
    for k,it in enumerate(out):
        if it.kind!='switch': continue
        host=it
        if it.ws[0]==0x4ebb:
            for h in out[k+1:k+8]:
                if h.kind=='jump' or (h.ws and h.ws[0]==0x4e75) or (h.kind=='bcc' and h.cond==0):
                    if h.hosted is None or h.hosted==it.table: host=h   # un hote = une seule table
                    break
            if host is it: it.choice='skip'    # pas de rupture proche : table juste apres, sautee par un BRA
        it.host=host
        host.hosted=it.table
    # tables de DONNEES : comme Capcom, apres la prochaine rupture si elle est a portee (d8)
    for k,it in enumerate(out):
        if it.kind!='dtab' or it.choice=='abs': continue
        it.choice='inline'
        for h in out[k+1:k+24]:
            if h.kind=='jump' or (h.ws and h.ws[0]==0x4e75) or (h.kind=='bcc' and h.cond==0):
                it.choice='host'; it.host=h; h.dhost.append(it); break
    return out

def table_bytes(buf, tbl, esz, cap=0x400):
    """contenu d'une table de donnees (adresse d'execution tbl), borne par la table suivante referencee
    par le code. Mode cps2 : octets tels quels (lus par octet), mots/longs en mots gros-boutistes."""
    refs=T.data_refs(buf); k=bisect.bisect_right(refs, tbl)
    lim=refs[k] if k < len(refs) else tbl+cap
    n=max(esz, min(lim-tbl, cap)); n-= n % esz
    o=tbl-T.RUNTIME_BASE; d=buf[o:o+n]
    if len(d)%2: d=d+b'\0'
    if esz==1 or T.MEMMODE!='cps2': return d if esz==1 else bytes(b for i in range(0,len(d),2) for b in (d[i+1],d[i]))
    return bytes(b for i in range(0,len(d),2) for b in (d[i+1],d[i]))

DTAB_ABS = os.environ.get("DTAB", "abs") == "abs"   # tables de donnees : lecture directe dans l'image
BRAS_TABLES=set()          # tables d'aiguillage en forme 'table de BRA.S' (entree k : BRA.S -> JMP abs.L k)
FAR_ENT={}                 # (HANDOFF §93) table -> entrees hors de portee 16 bits : tremplins JMP abs.L apres la table
def table_size(tbl):
    n=len(T.TABLES.get(tbl,[]))
    return 8*n if tbl in BRAS_TABLES else 2*n + 6*len(FAR_ENT.get(tbl,()))

def dtab_fix(it):
    """MOVEA.L T(PC,Xi),An lu dans une table de POINTEURS : routine de conversion (T.DPTR_FIX) ou None"""
    if (it.ws[0] & 0xf1c0)!=0x2040 or it.nofix: return None     # nofix : table de code relogee (etape B)
    return T.DPTR_FIX.get((it.ws[0]>>9)&7)

def base_size(it):
    k=it.kind
    if k=='bcc':
        if it.choice=='far': return 6 if it.cond==0 else 8     # (HANDOFF §70) B!cc.S +6 ; JMP abs.L
        return 4 if it.choice=='dbcc' else (2 if it.choice=='short' else 4)
    if k=='call':  return {'bsr_s':2,'bsr_l':4}.get(it.choice,6)
    if k=='jump':  return {'none':0,'bra_s':2,'bra_l':4}.get(it.choice,6)
    if k=='switch' and it.choice=='skip':
        return 4 + (2 if table_size(it.table)<=126 else 4)      # JSR T(PC,Dn) ; BRA par-dessus la table
    if k in ('switch','tblref'): return 4
    if k=='codeptr': return 2*len(it.ws)
    if k=='dtab':
        if it.choice=='abs' and it.nofix=='natif': return 10      # LEA table.L,An ; MOVEA.L 0(An,Xi),An (etape B)
        if it.choice=='abs':
            extra = 12 if (it.esz==1 and T.MEMMODE=='cps2') else 0     # (HANDOFF §80) octet : adresse exacte
            return 2 + 6 + 2*len(it.ws) + 2 + extra + (4 if dtab_fix(it) is not None else 0)
        if it.choice=='host': return 2*len(it.ws)
        return 2*len(it.ws) + (2 if len(it.data)<=126 else 4) + len(it.data)
    return 2*len(it.ws)

def size(it):
    """taille de l'element + celle des tables (aiguillage, donnees) qu'il HEBERGE eventuellement"""
    return (base_size(it) + (table_size(it.hosted) if it.hosted is not None else 0)
            + sum(len(d.data) for d in it.dhost if d.choice=='host'))

def dtab_start(d):
    """adresse de la table hebergee de l'element dtab d (apres son hote et ce qui le precede)"""
    h=d.host; a=h.off+base_size(h)+(table_size(h.hosted) if h.hosted is not None else 0)
    for x in h.dhost:
        if x is d: return a
        if x.choice=='host': a+=len(x.data)
    return None

# (ETAPE B, work/agent_reorg_B/ETAPE-B.md) RELOGEMENT DES POINTEURS DE CODE. Les sauts indirects 'JSR/JMP (An)' de la
# traduction convertissent l'adresse PS2 a l'usage (talon $3FF000 + hachage $3C0000, HANDOFF §76/§98), apres le talon
# de donnees $400 du MOVEA qui l'a lue (§63), qui la laisse. Aux sites dont TOUTES les definitions de An sont des
# lectures dans des tables de pointeurs de code (MOVEA.L T(PC,Dn),An ; ou LEA table.L,Ab [; LEA autre,Ab] ;
# MOVEA.L 0(Ab,Dn.W),An), les cases de ces tables sont relogees a l'assemblage (mame_test.py : etiquette 68K = ce que
# rendrait le talon a l'execution, meme table d'adresses) et le site devient 'JSR/JMP (An)' direct, sans les deux talons.
# Etendue d'une table : de son debut a la table suivante referencee par le code (data_refs), toutes les cases etant des
# debuts de fonction connus (cles du talon) ou 0 ; sinon la table et ses sites sont laisses tels quels.
# RELOGE_CODE=0 (defaut) : octets identiques ; =1 : relogement ; =2 : controle (tables relogees et talons de donnees
# retires, mais talon de code garde aux sites liberes : le journal des talons y voit les valeurs).
RELOGE_CODE = int(os.environ.get("RELOGE_CODE", "1") or "0")   # (§148) defaut 1 : etape B validee
T.RELOGE_TABLES = {}; T.RELOGE_SITES = []; T.RELOGE_NATIF_TABLES = set()
if not hasattr(T, 'RELOGE_KEYS'): T.RELOGE_KEYS = None   # cles du talon de code (mame_test.py)
RX_P1 = re.compile(r'^MOVEA\.L T_([0-9a-f]{6})\(PC,D\d\.W\),A(\d)')
RX_P2 = re.compile(r'^MOVEA\.L (-?\d+)\(A(\d),D\d\.[WL]\),A(\d)')
RX_LEA = re.compile(r'^LEA \$[0-9a-f]+\.L,A(\d)  \[PS2 ([0-9a-f]+)\]$')
def _areg_cite(mn, r): return re.search(r'(?<![0-9A-Za-z_])A%d(?![0-9])' % r, mn) is not None

def reloge_code(its, buf):
    """(ETAPE B) sites 'JSR CCONV_An ; JSR/JMP (An)' dont An vient seulement de tables de code : liberes.
    Remplit T.RELOGE_TABLES {debut PS2: fin PS2} et T.RELOGE_SITES ; modifie les elements en place."""
    import struct as _st
    T.RELOGE_TABLES.clear(); del T.RELOGE_SITES[:]; T.RELOGE_NATIF_TABLES.clear()
    T.RELOGE_RAM_TABLES.clear(); del T.RELOGE_RAM_SITES[:]
    keys=T.RELOGE_KEYS; refs=T.data_refs(buf)
    vas=[it.va for it in its]
    def idx(va): return bisect.bisect_left(vas, va)
    src={}                                                 # indice cible -> indices des branchements qui y vont
    for i,it in enumerate(its):
        if it.tgt is not None and it.kind in ('bcc','jump','call','codeptr'): src.setdefault(idx(it.tgt),[]).append(i)
    # debuts de fonction (appels indirects) : entrees inconnues. Les cles venues des DONNEES (critere 'prologue' de
    # mame_test.py : un long des donnees qui vise 'lui rX,$7000' ou 'jr ra') sont souvent des valeurs fortuites au milieu
    # d'une fonction (ex. Upper 0x2E00DC) : comptees seulement si l'instruction a k-8 termine une fonction (jr/j/b) ou si
    # k-8 et k-4 sont des nop de bourrage. Les cibles de jal et les debuts connus du traducteur comptent toujours.
    from mips import decode as _dec
    def _fin(k):
        a=k-T.RUNTIME_BASE
        if a<8: return True
        x8,x4=list(_dec(buf, a-8, a))
        if x8.m in ('jr','j') or (x8.m=='beq' and x8.rs==0 and x8.rt==0): return True
        w8,w4=_st.unpack_from('<II', buf, a-8)
        return w8==0 and w4==0
    sur=set(T._CODE_STARTS.get('set') or ()) | {it.tgt+T.RUNTIME_BASE for it in its if it.kind in ('call','jump') and it.tgt is not None}
    entree={idx(k-T.RUNTIME_BASE) for k in keys if k in sur or _fin(k)}
    for tb,ents in T.TABLES.items():                       # cibles des aiguillages
        for e in ents:
            if e: entree.add(idx(e-T.RUNTIME_BASE))
    def suit(it):                                          # l'element precedent peut-il tomber dans le suivant ?
        w=it.ws
        if it.kind=='jump' or (it.kind=='bcc' and it.cond==0 and it.choice!='dbcc'): return False
        if w and (w[-1] in (0x4e75,0x4e73) or (w[-1] & 0xfff8)==0x4ed0 or (len(w)>=3 and w[-3]==0x4ef9)): return False
        if it.kind=='switch' and w[0]==0x4efb: return False
        return True
    def ecrit(it, r):                                      # True / False / None (inconnu)
        if it.kind in ('call','switch') or it.hosted is not None: return None
        if not _areg_cite(it.mn, r):
            if any(w in (0x4eb9,0x4eb8) for w in it.ws) and 'CONV' not in it.mn: return None
            return False
        return 'def'
    def defs(u, r, prof=14):
        """elements qui definissent Ar a l'entree de u (None si inconnu : entree externe, effet incertain, trop loin)"""
        res=set(); vu=set(); pile=[u]
        while pile:
            i=pile.pop()
            if i in entree: return None
            ps=list(src.get(i,()))
            if i>0 and suit(its[i-1]): ps.append(i-1)
            if not ps: return None
            for p in ps:
                if p<u-prof or p>=u: return None
                if p in vu: continue
                vu.add(p); e=ecrit(its[p], r)
                if e is None: return None
                if e: res.add(p)
                else: pile.append(p)
        return res
    def etendue(p):                                        # table de code pure [p, fin) ou None
        k=bisect.bisect_right(refs, p); fin=refs[k] if k<len(refs) else None
        if fin is None or not (T.CODE_END_RT<=p<fin<=T.DATA_END_RT) or (fin-p)%4 or fin-p>0x1000: return None
        vals=[_st.unpack_from('<I', buf, p-T.RUNTIME_BASE+4*j)[0] for j in range((fin-p)//4)]
        if not all(v==0 or v in keys for v in vals) or not any(vals): return None
        return fin
    nlib=0; libres=[]
    for u,it in enumerate(its):
        w=it.ws
        if len(w)!=4 or w[0]!=0x4eb9 or (w[3]&0xfff8) not in (0x4e90,0x4ed0): continue
        n=w[3]&7
        if ((w[1]<<16)|w[2])!=T.CODE_CONV.get(n): continue
        D=defs(u, n)
        dbg=os.environ.get("RELOGE_DEBUG")=="1"
        if not D:
            if dbg: print("etape B : site %x (%s) : definitions de A%d inconnues" % (it.va, it.mn, n))
            continue
        tables=set(); ecrivains=[]; leas=set(); ok=True
        for d in sorted(D):
            x=its[d]; m1=RX_P1.match(x.mn); m2=RX_P2.match(x.mn)
            if m1 and int(m1.group(2))==n and x.kind=='dtab' and x.choice=='abs' and (x.ws[0]&0xf1c0)==0x2040 \
               and ((x.ws[0]>>9)&7)==n:
                tables.add(int(m1.group(1),16)); ecrivains.append(('p1',d))
            elif m2 and int(m2.group(3))==n and int(m2.group(1))==0 and (x.ws[0]&0xf1c0)==0x2040 and ((x.ws[0]>>9)&7)==n \
                 and x.ws[-2:]==[0x4eb8, T.DPTR_FIX.get(n)]:
                b=int(m2.group(2)); B=defs(d, b)
                if not B: ok=False; break
                for e in B:
                    ml=RX_LEA.match(its[e].mn)
                    if not ml or int(ml.group(1))!=b: ok=False; break
                    tables.add(int(ml.group(2),16)); leas.add(e)
                ecrivains.append(('p2',d) if b==n else ('p2b',d))
            else: ok=False
            if not ok: break
        if not ok or not tables:
            if dbg: print("etape B : site %x : definition non reconnue (%s)" % (it.va, '; '.join(its[d].mn for d in sorted(D))))
            continue
        fins={p: etendue(p) for p in tables}
        if not all(fins.values()):
            if dbg: print("etape B : site %x : table(s) %s non pure(s)" % (it.va, ','.join('%x' % p for p,f in fins.items() if not f)))
            continue
        for p,f in fins.items(): T.RELOGE_TABLES[p]=f
        libres.append((ecrivains, tables, leas))
        for k_,d in ecrivains:
            x=its[d]
            if k_=='p1': x.nofix=True
            elif x.ws[-2:]==[0x4eb8, T.DPTR_FIX.get(n)]: x.ws=x.ws[:-2]
            if 'etape B :' not in x.mn: x.mn=x.mn.replace(' ; JSR CONV_A%d'%n,'')+'  [etape B : table de code relogee, sans talon]'
        if RELOGE_CODE==1:
            it.ws=[w[3]]; it.mn=it.mn+'  [etape B : direct, tables %s]'%','.join('%06x'%p for p in sorted(tables))
        else: it.mn=it.mn+'  [etape B controle : talon de code garde, tables %s]'%','.join('%06x'%p for p in sorted(tables))
        T.RELOGE_SITES.append((it.va, n, sorted(tables))); nlib+=1
    if RELOGE_RAM:                                         # (amorce de l'etape C) tables de pointeurs RAM PS2
        R=T.RAM_HI<<16; vus={}
        for d,x in enumerate(its):
            m1=RX_P1.match(x.mn)
            if not (m1 and x.kind=='dtab' and x.choice=='abs' and (x.ws[0]&0xf1c0)==0x2040 and dtab_fix(x) is not None): continue
            p=int(m1.group(1),16)
            if p not in vus:
                k=bisect.bisect_right(refs, p); fin=refs[k] if k<len(refs) else None; vus[p]=None
                if fin and T.CODE_END_RT<=p<fin<=T.DATA_END_RT and not (fin-p)%4 and fin-p<=0x400:
                    vals=[_st.unpack_from('<I', buf, p-T.RUNTIME_BASE+4*j)[0] for j in range((fin-p)//4)]
                    if all(v==0 or R<=v<R+0x10000 for v in vals) and any(vals): vus[p]=fin
            if not vus[p]: continue
            T.RELOGE_RAM_SITES.append((x.va, (x.ws[0]>>9)&7, [p])); T.RELOGE_RAM_TABLES[p]=vus[p]
            if RELOGE_CODE==2:                             # controle : talon $400 garde (le journal y voit la valeur)
                x.mn=x.mn+'  [etape C controle : table de pointeurs RAM relogee, talon garde]'; continue
            x.nofix=True; x.mn=x.mn+'  [etape C : table de pointeurs RAM relogee, sans talon]'
            libres.append(([('p1',d)], {p}, set()))
    if RELOGE_NATIF: natif(its, libres)
    return nlib

# (amorce de l'ETAPE C, RELOGE_RAM=1) tables de la ROM dont TOUTES les cases (de leur debut a la table suivante referencee)
# sont des pointeurs vers la RAM PS2 [$900000,$910000) (ETAPE-A §5 : T_587740, T_58af80, T_5924b0 ; 2,2 M appels) : cases
# relogees comme le ferait le talon $400 (+$6F0000 -> $FFxxxx), talon retire derriere les 'MOVEA.L T(PC,Dn),An' qui les lisent
RELOGE_RAM = os.environ.get("RELOGE_RAM", "1") == "1"
T.RELOGE_RAM_TABLES = {}; T.RELOGE_RAM_SITES = []

RELOGE_NATIF = os.environ.get("RELOGE_NATIF", "1") == "1"
RX_REF = re.compile(r'(?:T_|\[PS2 00)([0-9a-f]{6})')
def natif(its, libres):
    """(ETAPE B, RELOGE_NATIF=1) tables relogees lues SEULEMENT par les ecrivains des sites liberes : cases rangees en
    ordre 68K (long gros-boutiste, sans echange des moities) -> plus de remise en ordre (EXG/SWAP/drapeaux) a la lecture,
    et MOVEA.L T(PC,Dn),An devient 'LEA table.L,An ; MOVEA.L 0(An,Dn),An' (sans registre de base sauve).
    Une table citee par une autre instruction (ex. T_5899a4 copie dans $40(A6), relu par un MOVEA ordinaire) reste en
    ordre echange, ainsi que toutes les tables des ecrivains qui la lisent (point fixe)."""
    permis={}                                              # indice d'element -> tables qu'il a le droit de citer
    for ecr,tabs,leas in libres:
        for k_,d in ecr: permis.setdefault(d,set()).update(tabs)
        for e in leas: permis.setdefault(e,set()).update(tabs)
    ext=sorted(list(T.RELOGE_TABLES.items())+list(T.RELOGE_RAM_TABLES.items()))
    def table_de(a):
        k=bisect.bisect_right(ext, (a, 1<<40))-1
        return ext[k][0] if k>=0 and ext[k][0]<=a<ext[k][1] else None
    exclues=set()
    for i,it in enumerate(its):
        for m in RX_REF.finditer(it.mn):
            t=table_de(int(m.group(1),16))
            if t is not None and t not in permis.get(i,()): exclues.add(t)
    while True:                                            # un ecrivain est natif pour toutes ses tables ou aucune
        n0=len(exclues)
        for ecr,tabs,leas in libres:
            if (tabs & exclues) or any(k_=='p2b' for k_,d in ecr): exclues |= tabs
        if len(exclues)==n0: break
    faits=set()
    for ecr,tabs,leas in libres:
        if tabs & exclues: continue
        T.RELOGE_NATIF_TABLES.update(tabs)
        for k_,d in ecr:
            if d in faits: continue
            faits.add(d); x=its[d]; r_=(x.ws[0]>>9)&7
            assert x.ws[2:7]==[0xc188|r_,0x40e7,0x4840,0x44df,0xc188|r_], "etape B : remise en ordre attendue (%x)" % x.va
            x.mn=x.mn.replace(' ; [remise en ordre du long]','')+'  [ordre 68K]'
            if k_=='p1': x.nofix='natif'
            else: x.ws=x.ws[:2]+x.ws[7:]

def assemble(buf, start, end, base=0, external=None, native=()):
    """external(va_fichier) -> adresse 68K absolue pour une cible HORS de l'unite (ou None).
    native : cibles DANS l'unite qui sont du code natif du portage (non traduisible) -> external."""
    items,_=T.translate(buf,start,end)
    FAR_ENT.clear()
    its=classify(items,buf)
    if RELOGE_CODE and T.CODE_CONV and T.RELOGE_KEYS: reloge_code(its, buf)
    vas=[it.va for it in its]
    native=set(native)
    def label(va):
        """offset de la premiere instruction emise a partir de va (dans l'unite)"""
        if not (start <= va < end) or va in native: return None
        k=bisect.bisect_left(vas, va)
        return its[k].off if k < len(its) else None
    # cibles HORS de l'unite : adresse absolue connue (external) -> on peut quand meme
    # employer la forme RELATIVE (BSR/BRA) si elle porte, comme un assembleur classique
    # (et comme le code d'origine : 5 201 BSR pour 6 207 JSR dans la ROM de SFA3)
    for it in its:
        if it.kind in ('call','jump','bcc') and it.tgt is not None and (not (start<=it.tgt<end) or it.tgt in native) and external:
            it.ext=external(it.tgt)
    def target(it):
        t=label(it.tgt) if it.tgt is not None else None
        if it.kind=='bcc' and it.tgt in T.ZONE_OPEN and it.tgt <= it.va <= T.ZONE_OPEN[it.tgt]:
            k=bisect.bisect_left(vas, it.tgt)                   # (HANDOFF §80) retour de boucle interne a une
            if 'prete]' in its[k].mn: t=its[k].off+base_size(its[k])   # zone A8 : apres l'ouverture
        return t if t is not None else it.ext
    # choix initiaux optimistes
    for it in its:
        if it.kind=='bcc' and it.choice!='dbcc': it.choice='short'
        inside=start<=it.tgt<end and it.tgt not in native if it.tgt is not None else False
        if it.kind=='call': it.choice='bsr_s' if (inside or it.ext is not None) else 'jsr'
        if it.kind=='jump': it.choice='none' if inside else ('bra_s' if it.ext is not None else 'jmp')
    for _ in range(30):
        off=base
        for it in its: it.off=off; off+=size(it)
        changed=False
        for n_,it in enumerate(its):
            if it.kind=='switch' and it.ws[0]==0x4ebb and it.choice!='skip':
                h=it.host if it.host is not None else it
                tb=h.off+base_size(h)
                ref=[x for x in its[max(0,n_-3):n_] if x.kind=='tblref' and x.table==it.table]
                far= not (-128<=tb-(it.off+2)<=127) or any(not (-128<=tb-(x.off+2)<=127) for x in ref)
                if far:
                    it.host.hosted=None; it.host=it; it.hosted=it.table; it.choice='skip'; changed=True
        # (HANDOFF §93) entree d'aiguillage a plus de 32 Ko de sa table (routine commune, ex. mips 0x3CE600 depuis
        # la table du perso $1C, mips 0x3995C0) : le mot relatif debordait -> saut au milieu d'une autre routine
        for it in its:
            if it.hosted is None or it.hosted in BRAS_TABLES: continue
            tb=it.off+base_size(it)
            for k_,e in enumerate(T.TABLES.get(it.hosted,[])):
                if e==0: continue
                t=label(e-T.RUNTIME_BASE)
                if t is not None and not (-32768<=t-tb<=32767) and k_ not in FAR_ENT.get(it.hosted,()):
                    FAR_ENT.setdefault(it.hosted,set()).add(k_); changed=True
        for it in its:
            if it.kind=='dtab' and it.choice=='host':
                d8=dtab_start(it)-(it.off+2)
                if not (-128<=d8<=127): it.choice='inline'; changed=True
        for n,it in enumerate(its):
            if it.kind in ('bcc','call','jump') and it.choice not in ('jsr','jmp','dbcc','far'):
                t=target(it)
                if t is None:
                    if it.kind=='bcc': continue
                    it.choice='jsr' if it.kind=='call' else 'jmp'; changed=True; continue
                nxt=it.off+size(it)
                if it.kind=='jump' and it.choice=='none':
                    if t!=nxt or it.hosted is not None: it.choice='bra_s'; changed=True
                    continue
                d=t-(it.off+2)
                short = it.choice in ('short','bsr_s','bra_s')
                if short and not (-128<=d<=127 and d!=0):
                    it.choice={'bcc':'long','call':'bsr_l','jump':'bra_l'}[it.kind]; changed=True
                elif it.kind=='bcc' and it.choice=='long' and not (-32768<=d<=32767):
                    it.choice='far'; changed=True               # Bcc.W hors de portee (repliait en silence)
                elif not short and it.kind in ('call','jump') and not (-32768<=d<=32767):
                    it.choice={'call':'jsr','jump':'jmp'}[it.kind]; changed=True    # trop loin : absolu
        if not changed: break
    # emission
    host_of={it.hosted:it for it in its if it.hosted is not None}
    def table_start(tbl):
        h=host_of.get(tbl)
        return None if h is None else h.off+base_size(h)
    words=[]; unresolved=0
    def put_table(it):
        nonlocal unresolved
        put_switch(it)
        for d in it.dhost:
            if d.choice=='host': words.extend(struct.unpack('>%dH'%(len(d.data)//2), d.data))
    def put_switch(it):
        nonlocal unresolved
        if it.hosted is None: return
        tb=it.off+base_size(it); ents=T.TABLES.get(it.hosted,[])   # entrees relatives A CETTE copie
        if it.hosted in BRAS_TABLES:
            n=len(ents)
            for k in range(n):                                  # BRA.S k -> tremplin k
                d=(tb+2*n+6*k)-(tb+2*k+2)
                if d>127: unresolved+=1; d=0
                words.append(0x6000|(d&0xff))
            for e in ents:                                      # tremplins JMP abs.L
                t=label(e-T.RUNTIME_BASE)
                if t is None: unresolved+=1; t=0
                words.extend([0x4ef9,(t>>16)&0xffff,t&0xffff])
            return
        far=sorted(FAR_ENT.get(it.hosted,()))
        for k_,e in enumerate(ents):
            if e==0: words.append(0); continue                  # trou de la table (cas inutilise)
            t=label(e-T.RUNTIME_BASE)
            if t is None: unresolved+=1; words.append(0)
            elif k_ in far: words.append((2*len(ents)+6*far.index(k_))&0xffff)   # -> tremplin
            else: words.append((t-tb)&0xffff)
        for k_ in far:                                          # tremplins JMP abs.L (HANDOFF §93)
            t=label(ents[k_]-T.RUNTIME_BASE)
            words.extend([0x4ef9,(t>>16)&0xffff,t&0xffff])
    # COPIE DE TABLE PROPRE A CHAQUE AIGUILLAGE (HANDOFF §63) : plusieurs aiguillages voisins peuvent
    # partager une table MIPS ; chacun heberge sa propre copie, dont les entrees sont relatives A CETTE
    # copie. La lecture MOVE.W T(PC,Dn.W),Dm doit donc viser la copie de SON JSR/JMP (et non la derniere).
    def switch_copy(n_, it):
        sw=it
        if it.kind=='tblref':
            sw=next((x for x in its[n_+1:n_+4] if x.kind=='switch' and x.table==it.table), None)
        h=sw.host if (sw is not None and sw.host is not None) else None
        return h.off+base_size(h) if h is not None else table_start(it.table)
    for n_,it in enumerate(its):
        k=it.kind; o=it.off
        if k in ('switch','tblref'):
            tb=switch_copy(n_,it); d=(tb-(o+2)) if tb is not None else None
            if d is None or not (-128<=d<=127): unresolved+=1; d=0
            ix=it.ws[1]&0xf000
            words+=[it.ws[0], ix|(d&0xff)]
            if k=='switch' and it.choice=='skip':
                ts=table_size(it.table)
                words+= [0x6000|ts] if ts<=126 else [0x6000, ts+2]
            put_table(it); continue
        if k=='codeptr':
            a=label(it.tgt) if not T.CODE_CONV else it.tgt+T.RUNTIME_BASE   # §76 : valeur PS2, convertie a l'usage
            if a is None: unresolved+=1; a=0
            if it.choice: a=((a&0xffff)<<16)|(a>>16)            # long echange (mode cps2, en memoire)
            words+=[it.ws[0], (a>>16)&0xffff, a&0xffff]+it.ws[3:]; put_table(it); continue
        if k=='fixed': words+=it.ws; put_table(it); continue
        if k=='dtab' and it.choice=='abs' and it.nofix=='natif':
            n=(it.ws[0]>>9)&7; a=T.addr_to_68k(it.table)        # (etape B) table en ordre 68K, base = destination
            words+=[0x41f9|(n<<9), (a>>16)&0xffff, a&0xffff, (it.ws[0]&~0x3f)|0x30|n, it.ws[1]&0xff00]
            put_table(it); continue
        if k=='dtab' and it.choice=='abs':
            n=it.areg; a=T.addr_to_68k(it.table)
            if it.esz==1 and T.MEMMODE=='cps2':
                # (HANDOFF §80) table d'OCTETS indexee par une valeur quelconque (tirage aleatoire des persos,
                # mips 0x1F771C) : adresse EXACTE (base + index) puis XOR 1 a l'execution (l'ancien 'base XOR 1'
                # supposait un index pair : octet voisin, et hors de la table en bout -> perso $DA)
                words+=[0x2f08|n, 0x41f9|(n<<9), (a>>16)&0xffff, a&0xffff,
                        0x41f0|(n<<9)|n, it.ws[1]&0xff00,            # LEA 0(An,Xi),An
                        0x2f08|n, 0x0a2f, 0x0001, 0x0003, 0x205f|(n<<9),   # adresse XOR 1
                        (it.ws[0]&~0x3f)|0x10|n] + it.ws[2:] + [0x205f|(n<<9)]
            else:
                words+=[0x2f08|n, 0x41f9|(n<<9), (a>>16)&0xffff, a&0xffff,
                        (it.ws[0]&~0x3f)|0x30|n, it.ws[1]&0xff00] + it.ws[2:] + [0x205f|(n<<9)]
            if dtab_fix(it) is not None: words+=[0x4eb8, dtab_fix(it)]
            put_table(it); continue
        if k=='dtab' and it.choice=='host':
            d8=dtab_start(it)-(o+2)
            words+=[it.ws[0], (it.ws[1]&0xff00)|(d8&0xff)] + it.ws[2:]
            put_table(it); continue
        if k=='dtab':
            bra=2 if len(it.data)<=126 else 4
            rest=len(it.ws)-2                                   # mots apres l'extension (deplacement d16 de la destination)
            d8=2*rest + bra                                     # base PC = mot d'extension
            words+=[it.ws[0], (it.ws[1]&0xff00)|(d8&0xff)] + it.ws[2:]
            words+= [0x6000|len(it.data)] if bra==2 else [0x6000, len(it.data)+2]
            words+= list(struct.unpack('>%dH'%(len(it.data)//2), it.data))
            put_table(it); continue
        t=target(it)
        if k=='bcc' and it.choice=='dbcc':
            d=(t-(o+2)) if t is not None else 0
            if t is None: unresolved+=1
            words+=[it.ws[0], d&0xffff]; put_table(it); continue
        if k=='bcc' and it.choice=='far':
            a=t if t is not None else 0
            if t is None: unresolved+=1
            if it.cond==0: words+=[0x4ef9,(a>>16)&0xffff,a&0xffff]
            else: words+=[0x6000|(it.cond^0x0100)|0x06, 0x4ef9,(a>>16)&0xffff,a&0xffff]
            put_table(it); continue
        if k=='bcc':
            if t is None: unresolved+=1; words+=[0x6000|it.cond, 0]; put_table(it); continue
            d=t-(o+2)
            words+= [0x6000|it.cond|(d&0xff)] if it.choice=='short' else [0x6000|it.cond, d&0xffff]
        elif k in ('call','jump'):
            if it.choice in ('jsr','jmp'):
                a=it.ext if it.ext is not None else label(it.tgt)      # cible interne lointaine : NOTRE adresse
                if a is None and external: a=external(it.tgt)
                if a is None: unresolved+=1; a=0
                words+=[0x4eb9 if k=='call' else 0x4ef9, (a>>16)&0xffff, a&0xffff]
            elif it.choice=='none': pass
            else:
                d=t-(o+2); op=0x6100 if k=='call' else 0x6000
                words+= [op|(d&0xff)] if it.choice in ('bsr_s','bra_s') else [op, d&0xffff]
        put_table(it)
    return its, words, unresolved

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    its,words,unres=assemble(ro3,0x201fa8,0x202200,external=T.mips_to_68k)
    print("elements : %d   mots : %d   non resolus : %d"%(len(its),len(words),unres))
