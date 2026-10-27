#!/usr/bin/env python3
"""Traducteur d'idiomes MIPS(recompile) -> 68000.

Ne decompile pas : reconnait les sequences stereotypees emises par le recompilateur
et re-emet l'instruction 68000 d'origine. Simulation symbolique legere : on suit ce
que contient chaque registre MIPS (un immediat, l'adresse d'un registre 68K emule,
la valeur d'un registre 68K...).

Encodage 68000 (verifie contre la ROM CPS2) :
  MOVE.B #imm,(d16,A5) = 1b7c   MOVE.W = 3b7c   MOVE.L = 2b7c
  MOVE.B Dn ,(d16,A5)  = 1b40|n MOVE.W = 3b40|n MOVE.L = 2b40|n
"""
import sys, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # (agent_ro9) la copie, pas les originaux
from mips import decode, REG

A5_SLOT = 0x1114                      # [0x70001114] = registre A5
ACTIVE_EXTRA={}           # case A8/D8 -> registre 68K prete (zone en cours, HANDOFF §54)
def slot_name(off):
    if off in ACTIVE_EXTRA: return ACTIVE_EXTRA[off]
    if 0x1100 <= off <= 0x111c: return ('A', (off-0x1100)//4)
    if 0x1124 <= off <= 0x1140: return ('D', (off-0x1124)//4)
    return None

SZ_TOP = {'B':1, 'W':3, 'L':2}        # nibble haut de MOVE selon la taille
RES_SLOT  = 0x1150                    # dernier resultat (flags Z)
NFLG_SLOT = 0x1158                    # signe (flag N)
X_SLOT    = 0x1154                    # drapeau X (retenue etendue)
# BTST #imm,(d16,An) = 0x0828 | mode<<3 | reg   -> (d16,A5) = mode 5, reg 5 = 0x082d
# Generalise a tout registre d'adresse An (le recensement a montre que A6 seul
# pese 17,8 % des instructions manquees, A4 4,3 % : A5 n'etait qu'un cas).
#   mode 5 = (d16,An) ; champ EA = mode<<3 | n
def enc_btst_an(bit, n, disp):  return [0x0828 | (n&7), bit & 0xff, disp & 0xffff]
def enc_clr_an(size, n, disp):
    sz={'B':0,'W':1,'L':2}[size]
    return [0x4200 | (sz<<6) | 0x28 | (n&7), disp & 0xffff]
def enc_btst_a5(bit, disp):   return enc_btst_an(bit, 5, disp)
def enc_clr_a5(size, disp):   return enc_clr_an(size, 5, disp)
BCC = {'bne':0x6600, 'beq':0x6700}    # BNE / BEQ (deplacement a resoudre)
# Branchements conditionnels selon le drapeau teste par le MIPS :
#   RES (0x1150) = resultat de la derniere operation -> Z (==0) et N (signe)
#   0x1158       = RETENUE (C) : -1 ou 0, calculee par sltu dans les CMP/SUB
#                  (et non le flag N comme note auparavant : voir HANDOFF)
BCC_OF = {('Z','beq'):('BEQ',0x6700), ('Z','bne'):('BNE',0x6600),
          ('Z','bltz'):('BMI',0x6b00),('Z','bgez'):('BPL',0x6a00),
          ('C','bltz'):('BCS',0x6500),('C','bgez'):('BCC',0x6400),
          ('C','bne'):('BCS',0x6500), ('C','beq'):('BCC',0x6400),
          ('Z','bgtz'):('BGT',0x6e00),('Z','blez'):('BLE',0x6f00)}
SZMASK = {'B':0xff, 'W':0xffff, 'L':0xffffffff}
# apres un bloc a drapeaux EXACTS, le signe de RES vaut N^V : bltz/bgez = BLT/BGE
SIGNED_OF = {'bltz':('BLT',0x6d00), 'bgez':('BGE',0x6c00), 'bgtz':('BGT',0x6e00), 'blez':('BLE',0x6f00)}
SZN = {'B':0,'W':1,'L':2}
def _src_ea(src):
    """operande source d'un CMP : ('imm',v) | ('D',n) | ('mem',sz,disp,an)"""
    if src[0]=='D':   return [src[1]&7], "D%d"%src[1]
    if src[0]=='mem': return [0x28|(src[3]&7)], "$%04x(A%d)"%(src[2],src[3])
    if src[0]=='idx':                                  # (HANDOFF §124) d8(An,Dn.x) : ('idx', sz, An, Dn, taille Dn, d8)
        _,_,n,dn,dsz,d8=src; return [0x30|(n&7)], "%d(A%d,D%d.%s)"%(d8,n,dn,dsz)
    return None, None
def enc_cmp(size, dst, src):
    """CMP/CMPI. dst,src : ('D',n) | ('mem',sz,disp,an) | ('imm',v). Rend (mots, mnemo) ou None."""
    # (HANDOFF §70) operande memoire lu en DEMI-MOT (lh) mais compare en OCTET (extension 24 bits) :
    # c'est l'octet BAS du demi-mot petit-boutiste = octet MIPS de meme adresse -> 68K : adresse XOR 1
    # (compteur de la boucle des objets joueurs : CMPI.B #4 sur le mauvais octet -> 1 024 tours)
    def _fixb(o):
        if o[0]=='mem' and o[1]=='W' and size=='B' and MEMMODE=='cps2': return ('mem','B',o[2]^1,o[3])
        return o
    dst=_fixb(dst); src=_fixb(src)
    sz=SZN[size]
    # (agent_hyper_defauts, CMPMM) comparaison MEMOIRE - MEMOIRE (aucune forme 68K directe) : rendait None, le CMP etait
    # PERDU sans trace et le branchement relisait des drapeaux perimes. Cas type : D8 servi par son domicile
    # $87F0(A5) compare a un champ (Hyper mips 0x2DDF3C, plafond de la jauge de super 'CMP.W $11E(A6),D8 ; BCC ;
    # MOVE.W D8,$11E(A6)' : jauge sans plafond, au-dela de $90). Temporaire D0 (D0-D1 en .L) sauve sur la pile,
    # MOVEM final (ne touche pas les drapeaux). CMPMM=0 : ancien comportement.
    if CMPMM and dst[0]=='mem' and src[0]=='mem' and dst[3]!=7 and src[3]!=7:
        CMPMM_N.append((size,dst,src))
        if size=='L' and MEMMODE=='cps2':             # longs a moities echangees : valeurs reelles par SWAP
            return [0x48e7, 0xc000, 0x2028|(dst[3]&7), dst[2]&0xffff, 0x4840, 0x2228|(src[3]&7), src[2]&0xffff, 0x4841,
                    0xb081, 0x4cdf, 0x0003], \
                   "CMP.L $%04x(A%d),$%04x(A%d)  [memoire-memoire, par D0/D1 sauves]"%(src[2],src[3],dst[2],dst[3])
        mv={'B':0x1028,'W':0x3028,'L':0x2028}[size]
        return [0x2f00, mv|(dst[3]&7), dst[2]&0xffff, 0xb000|(sz<<6)|0x28|(src[3]&7), src[2]&0xffff, 0x4cdf, 0x0001], \
               "CMP.%s $%04x(A%d),$%04x(A%d)  [memoire-memoire, par D0 sauve]"%(size,src[2],src[3],dst[2],dst[3])
    # (agent_hyper_defauts, CMPX, ESSAI non valide, defaut 0) minuende en memoire, soustrait dans un registre D :
    # 'CMP.x Dn,mem' n'existe pas -> temporaire Dt (!= Dn) sauve ; longs a moities echangees remis par SWAP
    if CMPX and dst[0]=='mem' and src[0]=='D' and dst[3]!=7:
        CMPX_N.append((size,dst,src)); t=1 if src[1]==0 else 0
        mv={'B':0x1028,'W':0x3028,'L':0x2028}[size]|(t<<9)
        ws=[0x2f00|t, mv|(dst[3]&7), dst[2]&0xffff]+([0x4840|t] if size=='L' and MEMMODE=='cps2' else [])
        return ws+[0xb000|(t<<9)|(sz<<6)|(src[1]&7), 0x4cdf, 1<<t], \
               "CMP.%s D%d,$%04x(A%d)  [minuende en memoire, par D%d sauve]"%(size,src[1],dst[2],dst[3],t)
    if MEMMODE=='cps2' and size=='L':
        # (HANDOFF §80) long MEMOIRE a moities echangees : on compare la valeur REELLE (temporaire Dt remis en
        # ordre par SWAP, MOVEM final sans drapeaux). Avant : CMPI.L #$40202,$4(A6) contre le long echange.
        if dst[0]=='mem' and src[0]=='imm':
            an,disp=dst[3],dst[2]
            # (HANDOFF §88) constante = adresse PS2 (pointeur range en memoire) : convertie comme le fait
            # MOVE.L #const (sinon 'CMPI.L #$92C000,$BF40(A5)' ne vaut jamais : flash de palette jamais retire)
            _v=src[1]&0xffffffff
            if _v>=0x200000:
                _a=addr_to_68k(_v)
                if _a is not None: src=('imm',_a)
            return [0x2f00, 0x2028|(an&7), disp&0xffff, 0x4840, 0x0c80]+_imm_words('L',src[1]&0xffffffff)+[0x4cdf,0x0001], \
                   "CMPI.L #$%x,$%04x(A%d)  [long echange, par D0]"%(src[1]&0xffffffff,disp,an)
        if dst[0] in ('D','A') and src[0]=='mem':
            an,disp=src[3],src[2]; t=0 if not (dst[0]=='D' and dst[1]==0) else 1
            op=(0xb080|((dst[1]&7)<<9)|t) if dst[0]=='D' else (0xb1c0|((dst[1]&7)<<9)|t)
            return [0x2f00|t, 0x2028|(t<<9)|(an&7), disp&0xffff, 0x4840|t, op, 0x4cdf, 1<<t], \
                   "CMP%s.L $%04x(A%d),%s%d  [long echange, par D%d]"%("A" if dst[0]=='A' else "",disp,an,dst[0],dst[1],t)
    if src[0]=='imm':
        v=src[1] & SZMASK[size]
        if dst[0]=='D':
            return [0x0c00|(sz<<6)|(dst[1]&7)]+_imm_words(size,v), "CMPI.%s #$%x,D%d"%(size,v,dst[1])
        if dst[0]=='mem':
            return [0x0c00|(sz<<6)|0x28|(dst[3]&7)]+_imm_words(size,v)+[dst[2]&0xffff], \
                   "CMPI.%s #$%x,$%04x(A%d)"%(size,v,dst[2],dst[3])
        if dst[0]=='abs' and dst[1]==size:                # (HANDOFF §78) boite aux lettres QSound $61801F
            a,note=abs_addr(dst[2],size)
            return [0x0c00|(sz<<6)|0x39]+_imm_words(size,v)+abs_words(a), "CMPI.%s #$%x,$%06x.L%s"%(size,v,a&0xffffff,note)
        return None
    if dst[0]=='A':                                    # CMPA.W/L <ea>,An
        opm=0xb0c0 if size=='W' else 0xb1c0
        if src[0]=='A': return [opm|((dst[1]&7)<<9)|0x08|(src[1]&7)], "CMPA.%s A%d,A%d"%(size,src[1],dst[1])
        if src[0]=='D': return [opm|((dst[1]&7)<<9)|(src[1]&7)], "CMPA.%s D%d,A%d"%(size,src[1],dst[1])
        if src[0]=='mem': return [opm|((dst[1]&7)<<9)|0x28|(src[3]&7), src[2]&0xffff], "CMPA.%s $%04x(A%d),A%d"%(size,src[2],src[3],dst[1])
        return None
    if dst[0]=='D':
        ea,t=_src_ea(src)
        if ea is None: return None
        ws=[0xb000|((dst[1]&7)<<9)|(sz<<6)|ea[0]]
        if src[0]=='mem': ws.append(src[2]&0xffff)
        if src[0]=='idx': ws.append(idx_ext(src[3],src[4],src[5]))
        if src[0]=='idx' and size=='B' and MEMMODE=='cps2':      # (§124) adresse exacte a l'execution (byte_index_exact)
            return ws, "CMP.%s %s,D%d  [index pair suppose]"%(size,t,dst[1])
        return ws, "CMP.%s %s,D%d"%(size,t,dst[1])
    return None

def enc_move_mem_mem(size, sn, sdisp, dn, ddisp):
    """MOVE.x d16(An),d16(Am) : dest reg m / mode 5, source 0x28|n, puis les deux deplacements"""
    return [(SZ_TOP[size]<<12) | ((dn&7)<<9) | (5<<6) | 0x28 | (sn&7), sdisp&0xffff, ddisp&0xffff]
def enc_move_reg_dn(size, src, dn):
    """MOVE.x Dm,Dn ou MOVE.x Am,Dn (dest mode 0) ; src = ('D',m) | ('A',m)"""
    ea = (src[1]&7) | (0x08 if src[0]=='A' else 0)
    return [(SZ_TOP[size]<<12) | ((dn&7)<<9) | ea]
def enc_addsub_mem(size, v, an, disp):
    """ADDQ/SUBQ/ADDI/SUBI.x #v,d16(An) (arithmetique EN PLACE en memoire)"""
    sz=SZN[size]; ea=0x28|(an&7)
    if 1 <= v <= 8:   return [0x5000|((v&7)<<9)|(sz<<6)|ea, disp&0xffff], "ADDQ.%s #%d,$%04x(A%d)"%(size,v,disp,an)
    if -8 <= v <= -1: return [0x5100|(((-v)&7)<<9)|(sz<<6)|ea, disp&0xffff], "SUBQ.%s #%d,$%04x(A%d)"%(size,-v,disp,an)
    if v < 0: return [0x0400|(sz<<6)|ea]+_imm_words(size,-v)+[disp&0xffff], "SUBI.%s #$%x,$%04x(A%d)"%(size,(-v)&SZMASK[size],disp,an)
    return [0x0600|(sz<<6)|ea]+_imm_words(size,v)+[disp&0xffff], "ADDI.%s #$%x,$%04x(A%d)"%(size,v&SZMASK[size],disp,an)

# Tables de sauts rencontrees : adresse d'execution -> liste des cibles MIPS.
# L'assembleur s'en sert pour reconstruire la table 68K ('dc.w cible-table').
TABLES = {}
_DATA_REFS=None
def data_refs(buf):
    """toutes les adresses de DONNEES construites par 'lui+addiu' dans le code.
    Les tables du recompilateur sont placees bout a bout : une table s'arrete la ou
    commence la suivante referencee par le code (sinon on deborderait sur elle)."""
    global _DATA_REFS
    if _DATA_REFS is None or _DATA_REFS[0]!=id(buf):
        import struct as _st
        from mips import decode, CODE0
        CODE1=_st.unpack_from('<I',buf,12)[0]             # fin du code DU MODULE (pas celle de SFA3)
        refs=set(); lu={}
        for x in decode(buf, CODE0, CODE1):
            if x.m=='lui': lu[x.rt]=x.imm
            elif x.m=='addiu' and x.rs in lu:
                v=((lu[x.rs]<<16)+x.simm)&0xffffffff
                if CODE1 <= v-RUNTIME_BASE < len(buf): refs.add(v)
                lu.pop(x.rt,None)
            elif x.rt in lu and x.m not in ('sw','sh','sb','sd','sq','beq','bne'): lu.pop(x.rt,None)
        _DATA_REFS=(id(buf),sorted(refs))
    return _DATA_REFS[1]

def read_jump_table(buf, tbl, maxn=256):
    """lit la table de pointeurs du recompilateur (u32, adresses d'execution de code).
    S'arrete a la premiere entree qui ne pointe pas dans la zone de code, OU au debut
    de la table suivante referencee par le code."""
    import struct, bisect
    from mips import CODE0
    CODE1=struct.unpack_from('<I',buf,12)[0]
    refs=data_refs(buf); k=bisect.bisect_right(refs, tbl)
    lim=refs[k] if k < len(refs) else None
    o=tbl-RUNTIME_BASE; ent=[]
    while 0<=o<=len(buf)-4 and len(ent)<maxn:
        # (HANDOFF §67) arret a la table suivante referencee, SAUF si la table finit par un TROU juste
        # avant : le portage indexe alors au-dela (T_587150 = 3 cas, 0, puis T_587160 : index 8 valide)
        if lim is not None and o+RUNTIME_BASE >= lim and not (ent and ent[-1]==0): break
        v=struct.unpack_from('<I',buf,o)[0]
        # (HANDOFF §67) une entree NULLE est un trou (cas inutilise) : la table continue apres
        # (T_587150 : 3 cas, 0, puis 12 autres ; l'index 8 tombait hors de la table tronquee)
        if v!=0 and not (CODE0 <= v-RUNTIME_BASE < CODE1): break
        ent.append(v); o+=4
    while ent and ent[-1]==0: ent.pop()
    return ent

# Tables de VALEURS lues par index (a copier telles quelles dans la sortie) :
# adresse d'execution -> taille d'element lue
DATA_TABLES = {}
def enc_move_pcidx(size, dn_idx, dst):
    """MOVE.x tbl(PC,Dk.W),<dst>  (source mode 7 reg 3 = 0x3b + mot d'extension ;
    le deplacement 8 bits est resolu par l'assembleur). dst = ('D',n) | ('mem',disp,an)"""
    ext=((dn_idx&7)<<12)
    if dst[0]=='D': return [(SZ_TOP[size]<<12)|((dst[1]&7)<<9)|0x3b, ext]
    return [(SZ_TOP[size]<<12)|((dst[2]&7)<<9)|(5<<6)|0x3b, ext, dst[1]&0xffff]
MEMOP = {'addu':(0xd000,'ADD'), 'subu':(0x9000,'SUB'), 'and':(0xc000,'AND'), 'or':(0x8000,'OR')}
def enc_op_dn_mem(kind, size, dn, an, disp):
    """ADD/SUB/AND/OR/EOR.x Dn,d16(An) : operation EN PLACE en memoire (opmode 4+taille)"""
    sz=SZN[size]
    if kind=='xor': return [0xb100|((dn&7)<<9)|(sz<<6)|0x28|(an&7), disp&0xffff], "EOR"
    base,name=MEMOP[kind]
    return [base|((dn&7)<<9)|((4+sz)<<6)|0x28|(an&7), disp&0xffff], name

def is_swap(L, i, slot):
    """SWAP Dn : Dn = (Dn.bas << 16) | (Dn.haut >> 16)
    lw Dn ; andi 0xffff ; sll 16 ; lw Dn ; lui 0xffff ; and ; srl 16 ; andi 0xffff ; or ; [sw Dn]"""
    want=[('lw',slot),('andi',0xffff),('sll',16),('lw',slot),('lui',0xffff),('and',None),
          ('srl',16),('andi',0xffff),('or',None)]
    seq=[x for x in L[max(0,i-16):i] if not (x.m=='lui' and x.imm==0x7000)][-len(want):]
    if len(seq)!=len(want): return False
    for x,(mm,a) in zip(seq,want):
        if x.m!=mm: return False
        if mm in ('lw','andi','lui') and x.imm!=a: return False
        if mm in ('sll','srl') and x.sa!=a: return False
    return True
AIDES_RECOMP = {0x570360:'movem_push', 0x5706c0:'movem_pop', 0x570a20:'andi_ccr', 0x570d00:'abcd'}
AIDE_ROXR=__import__('os').environ.get('AIDE_ROXR','1')!='0'; AIDE_ROXR_N=set()   # (agent_defauts_banc)
def _rev16(v): return int('{:016b}'.format(v & 0xffff)[::-1], 2)
def aide_recomp(kind, st):
    """(HANDOFF §83) traduction d'un appel a une aide du recompilateur (arguments a0=r4, a1=r5 suivis).
    movem_push/pop : masque au format predecrement (bit 15 = D0) ; la pile du portage (case $114C) est NOTRE pile.
    abcd(src, dst) : addition BCD d'UN octet, adresses PS2 (octet 68K = adresse XOR 1), X en entree et en sortie :
    rendue par 'ABCD -(A0),-(A1)' sur (adresse XOR 1)+1, drapeaux preserves autour (chaine de retenues)."""
    a0=st.get(4); a1=st.get(5)
    def cst(sy):
        if sy and sy.kind in ('imm','const') and isinstance(sy.val,int): return sy.val & 0xffff
        return None
    if kind in ('movem_push','movem_pop','andi_ccr'):
        v=cst(a0)
        if v is None: return None, None
        if kind=='andi_ccr': return [0x023c, v & 0xff], "ANDI #$%02x,CCR  [aide du recompilateur]"%(v & 0xff)
        if kind=='movem_push': return [0x48e7, v], "MOVEM.L #$%04x,-(SP)  [aide du recompilateur]"%v
        return [0x4cdf, _rev16(v)], "MOVEM.L (SP)+,#$%04x  [aide du recompilateur]"%_rev16(v)
    if kind=='roxr':
        # (agent_defauts_banc, AIDE_ROXR) roxr(octet, n) : ROXR.B #n sur l'octet bas d'un registre D (a0 = sa case),
        # X en entree et en sortie, C/N/Z poses (SFA3 mips 0x570AA0, Upper 0x213240, Hyper 0x213500 : octant de la
        # visee du Killer Bee Assault, arcade $05DB06 'ROXR.B #1,D6'). Talon traduit jusqu'ici : seuls ses
        # branchements restaient, D6 gardait 0
        if not AIDE_ROXR: return None, None
        if a0 and a0.kind=='const' and isinstance(a0.val,int) and 0x70001124 <= a0.val < 0x70001144 and a0.val % 4 == 0:
            n=(a0.val-0x70001124)//4; c=cst(a1)
            if c is not None and 1 <= c <= 8:
                AIDE_ROXR_N.add((n,c))
                return [0xe010|((c&7)<<9)|n], "ROXR.B #%d,D%d  [aide du recompilateur, AIDE_ROXR]"%(c,n)
        return None, None
    if kind=='abcd':
        def dreg(sy):                                   # pointeur sur la case d'un registre D = son octet bas
            if sy and sy.kind=='const' and isinstance(sy.val,int) and 0x70001124 <= sy.val < 0x70001144 and sy.val % 4 == 0:
                return (sy.val-0x70001124)//4
            return None
        if dreg(a0) is not None and dreg(a1) is not None:
            y,x=dreg(a0),dreg(a1)
            return [0xc100|(x<<9)|y], "ABCD D%d,D%d  [aide du recompilateur]"%(y,x)
        ops=[]
        for sy in (a0, a1):
            if not (sy and sy.kind=='an' and sy.val[0]!=7): return None, None
            ops.append(sy.val)
        sc=[k for k in range(7) if k not in (ops[0][0],ops[1][0])][:2]   # registres de travail hors des bases
        ws=[0x40e7, 0x48e7, 0x8000|(1<<(7-sc[0]))|(1<<(7-sc[1]))]        # MOVE SR,-(SP) ; MOVEM.L D0/As/At,-(SP)
        for k,(n,d) in zip(sc,ops):                     # LEA d(An),Ak ; MOVE.L Ak,D0 ; EORI.W #1,D0 ; ADDQ.L #1,D0 ; MOVEA.L D0,Ak
            ws+=[0x41e8|(k<<9)|n, d & 0xffff, 0x2008|k, 0x0a40, 0x0001, 0x5280, 0x2040|(k<<9)]
        ws+=[0x44ef, 0x000c, 0xc108|(sc[1]<<9)|sc[0],   # MOVE 12(SP),CCR ; ABCD -(As),-(At)
             0x4cdf, 0x0001|(1<<(8+sc[0]))|(1<<(8+sc[1])), 0x548f]   # MOVEM.L (SP)+ ; ADDQ.L #2,SP (drapeaux gardes)
        return ws, "ABCD $%04x(A%d)^1,$%04x(A%d)^1  [aide du recompilateur, octets PS2]"%(ops[0][1]&0xffff,ops[0][0],ops[1][1]&0xffff,ops[1][0])
    return None, None

# (HANDOFF §83) masque 32 bits 'lui ; ori' sur un registre D (ANDI.L #$F000F000 des copies de palette,
# ANDI.L #$03FF03FF / ORI.L #$E0002000 des constructeurs du HUD...). Diagnostic : MASQ_OK=v1,v2 restreint la liste.
def _masque_ok(v):
    import os
    e=os.environ.get("MASQ_OK")
    return True if not e or e=="tous" else (v & 0xffffffff) in {int(x,16) for x in e.split(",")}
def bswap32_or(L, i):
    """(HANDOFF §90) 'or' final d'un arbre (4 feuilles 'lw Dn' masquees/decalees) qui vaut bswap32(Dn) : long range
    OCTET PAR OCTET par le portage (champ u8[4], ex. octets d'etat $4-$7 d'un personnage : 'MOVE.L D1,$4(A6)' de la
    pose de fin de manche, ROM $2AD0C). Rend n ou None (evaluation symbolique sur une valeur test)."""
    def defn(j, r):
        for k in range(j-1, max(-1, j-30), -1):
            if L[k].m=='lui' and L[k].imm==0x7000: continue
            if dest_reg(L[k])==r: return k
            if L[k].m in ('jal','jalr','jr','beq','bne','blez','bgtz','bltz','bgez'): return None
        return None
    slot=[None]
    def ev(k, depth, v0):
        if k is None or depth>12: return None
        x=L[k]
        if x.m=='lw' and 0x1124<=x.imm<0x1144 and not (x.imm&3):
            if slot[0] is None: slot[0]=x.imm
            return v0 if slot[0]==x.imm else None
        if x.m=='lui': return (x.imm<<16)&0xffffffff
        if x.m=='or':
            a=ev(defn(k,x.rs),depth+1,v0); b=ev(defn(k,x.rt),depth+1,v0)
            return None if a is None or b is None else a|b
        if x.m=='and':
            a=ev(defn(k,x.rs),depth+1,v0); b=ev(defn(k,x.rt),depth+1,v0)
            return None if a is None or b is None else a&b
        if x.m=='andi':
            a=ev(defn(k,x.rs),depth+1,v0); return None if a is None else a&x.imm
        if x.m in ('sll','srl','sra'):
            a=ev(defn(k,x.rt),depth+1,v0)
            if a is None: return None
            if x.m=='sll': return (a<<x.sa)&0xffffffff
            if x.m=='srl': return a>>x.sa
            return ((a-(1<<32) if a&0x80000000 else a)>>x.sa)&0xffffffff
        return None
    v0=0x11223344
    r=ev(i, 0, v0)
    if r==0x44332211 and slot[0] is not None: return (slot[0]-0x1124)//4
    return None
def bswap16_mem(L, i, r):
    """(HANDOFF §92) mot range par 'sh r' qui vaut bswap16 d'un MOT LU EN MEMOIRE (deux feuilles 'lh d(An)') :
    le portage recopie un champ a octets inverses (ROM $1A602 'MOVE.W (A1),$2(A4)', apparition des objets
    du decor). Rend (An, d) de la source ou None (evaluation symbolique sur une valeur test, 64 bits)."""
    M64=(1<<64)-1
    def s64(v): return v-(1<<64) if v>>63 else v
    def defn(j, r):
        for k in range(j-1, max(-1, j-40), -1):
            if L[k].m=='lui' and L[k].imm==0x7000: continue
            if dest_reg(L[k])==r: return k
            if L[k].m in ('jal','jalr','jr','beq','bne','blez','bgtz','bltz','bgez'): return None
        return None
    src=[None]
    def const_of(j):
        """lui (+ addiu) -> constante, sinon None"""
        if j is None: return None
        x=L[j]
        if x.m=='lui': return (x.imm<<16)&0xffffffff
        if x.m=='addiu':
            c=const_of(defn(j, x.rs))
            return None if c is None else (c+x.simm)&0xffffffff
        return None
    def dreg_w(j):
        """registre = Dk.W etendu (lh slot Dk ; dsll32/dsra32 16) -> k, sinon None"""
        if j is None: return None
        x=L[j]
        if x.m in ('dsra32','dsll32','sra','sll') and x.sa==16: return dreg_w(defn(j, x.rt))
        if x.m=='lh' and L[j].rs is not None:
            nm=slot_name(x.imm & 0xffff)
            if nm and nm[0]=='D': return nm[1]
        return None
    def idx_base(j, imm):
        """base = constante + Dk.W (+ imm) -> (constante + imm, k), sinon None"""
        x=L[j]
        if x.m=='addiu':
            r=idx_base(defn(j, x.rs), imm + x.simm) if defn(j, x.rs) is not None else None
            return r
        if x.m=='addu':
            for p,q in ((x.rs,x.rt),(x.rt,x.rs)):
                c=const_of(defn(j,p)); k_=dreg_w(defn(j,q))
                if c is not None and k_ is not None: return ((c+imm)&0xffffffff, k_)
            if IDXRMW_ON:                            # (HANDOFF §138) table designee par un REGISTRE d'adresse
                for p,q in ((x.rs,x.rt),(x.rt,x.rs)):   # (Upper mips 0x54C70 : A8 prete = table des decors)
                    jp=defn(j,p); k_=dreg_w(defn(j,q))
                    if jp is not None and k_ is not None and L[jp].m=='lw':
                        nm=slot_name(L[jp].imm & 0xffff)
                        if nm and nm[0]=='A' and nm[1]<7: return ('A', nm[1], imm, k_)
        return None
    def ev(k, depth):
        if k is None or depth>16: return None
        x=L[k]
        if x.m in ('lh','lhu'):
            b=defn(k, x.rs)
            if b is None: return None
            if L[b].m=='lw':
                nm=slot_name(L[b].imm)
                if not nm or nm[0]!='A' or nm[1]>=7: return None
                s=('an', nm[1], x.simm & 0xffff)
            else:
                ib=idx_base(b, x.simm)               # (HANDOFF §100) table de donnees indexee par Dk.W
                if ib is None: return None
                s=('anidx',)+ib[1:] if ib[0]=='A' else ('idx',)+ib
            if src[0] is None: src[0]=s
            if src[0]!=s: return None
            return 0x1122
        if x.m=='or':
            a=ev(defn(k,x.rs),depth+1); b=ev(defn(k,x.rt),depth+1)
            return None if a is None or b is None else a|b
        if x.m=='andi':
            a=ev(defn(k,x.rs),depth+1); return None if a is None else a&x.imm
        if x.m in ('sll','srl','sra','dsll32','dsra32','dsrl32'):
            a=ev(defn(k,x.rt),depth+1)
            if a is None: return None
            if x.m=='sll': v=(a<<x.sa)&0xffffffff; return (v|~0xffffffff)&M64 if v>>31 else v
            if x.m=='srl': return (a&0xffffffff)>>x.sa
            if x.m=='sra': return (s64(a)>>x.sa)&M64
            if x.m=='dsll32': return (a<<(32+x.sa))&M64
            if x.m=='dsrl32': return (a&M64)>>(32+x.sa)
            return (s64(a)>>(32+x.sa))&M64
        return None
    v=ev(defn(i, r), 0)
    if v is not None and (v & 0xffff)==0x2211 and src[0] is not None: return src[0]
    return None
def swap_or(L, i):
    """(HANDOFF §83) 'or' qui assemble SWAP(Dn) dans un registre MIPS temporaire (long a ranger dans l'ordre
    NATUREL, ex. liste d'objets du HUD, ROM $21982 'MOVEM.L D0-D1,(A2)') : une branche 'lw Dn ; andi $FFFF ;
    sll 16', l'autre 'lw Dn ; lui $FFFF ; and ; srl 16 ; andi $FFFF [; andi $FFFF]'. Rend n ou None."""
    def defn(j, r):
        for k in range(j-1, max(-1, j-24), -1):
            if L[k].m=='lui' and L[k].imm==0x7000: continue
            if dest_reg(L[k])==r: return k
            if L[k].m in ('beq','bne','j','jal','jr','jalr','blez','bgtz','bltz','bgez'): return None
        return None
    def slot(k):
        if k is None or L[k].m!='lw' or not (0x1124 <= L[k].imm < 0x1144) or (L[k].imm & 3): return None
        return (L[k].imm-0x1124)//4
    def bas(r, j):
        k=defn(j, r)
        if k is None or L[k].m!='sll' or L[k].sa!=16: return None
        k2=defn(k, L[k].rt)
        if k2 is None or L[k2].m!='andi' or L[k2].imm!=0xffff: return None
        return slot(defn(k2, L[k2].rs))
    def haut(r, j):
        k=defn(j, r)
        while k is not None and L[k].m=='andi' and L[k].imm==0xffff: j=k; r=L[k].rs; k=defn(j, r)
        if k is None or L[k].m!='srl' or L[k].sa!=16: return None
        k2=defn(k, L[k].rt)
        if k2 is None or L[k2].m!='and': return None
        a,b=defn(k2, L[k2].rs), defn(k2, L[k2].rt)
        for x,y in ((a,b),(b,a)):
            if y is not None and L[y].m=='lui' and L[y].imm==0xffff: return slot(x)
        return None
    x=L[i]
    for p,q in ((x.rs,x.rt),(x.rt,x.rs)):
        n=bas(p, i)
        if n is not None and haut(q, i)==n: return n
    return None
DMEMOP = {'addu':(0xd000,'ADD'), 'subu':(0x9000,'SUB'), 'and':(0xc000,'AND'), 'or':(0x8000,'OR')}
def enc_op_mem_dn(kind, size, mr, dn):
    """ADD/SUB/AND/OR.x d16(An),Dn"""
    base,name=DMEMOP[kind]; msz,disp,an=mr
    if MEMMODE=='cps2' and size=='L':
        # (HANDOFF §80) operande long en memoire a moities echangees : remis en ordre dans Dt (vitesse += gravite
        # de l'intro des personnages, mips 0x2BDEEC : J2 traversait le sol)
        t=0 if dn!=0 else 1
        return [0x2f00|t, 0x2028|(t<<9)|(an&7), disp&0xffff, 0x4840|t, base|((dn&7)<<9)|(2<<6)|t, 0x4cdf, 1<<t], \
               "%s.L $%04x(A%d),D%d  [long echange, par D%d]"%(name,disp,an,dn,t)
    return [base|((dn&7)<<9)|(SZN[size]<<6)|0x28|(an&7), disp&0xffff], "%s.%s $%04x(A%d),D%d"%(name,size,disp,an,dn)
def enc_sub_dn(size, src, dn):
    """SUB/SUBI/SUBQ.x <src>,Dn ; src = ('imm',v) | ('D',m) | ('mem',sz,disp,an)"""
    if src[0]=='imm':
        v=src[1] & SZMASK[size]
        if 1 <= v <= 8: return [0x5100|((v&7)<<9)|(SZN[size]<<6)|(dn&7)], "SUBQ.%s #%d,D%d"%(size,v,dn)
        return [0x0400|(SZN[size]<<6)|(dn&7)]+_imm_words(size,v), "SUBI.%s #$%x,D%d"%(size,v,dn)
    if src[0]=='D': return [0x9000|((dn&7)<<9)|(SZN[size]<<6)|(src[1]&7)], "SUB.%s D%d,D%d"%(size,src[1],dn)
    if src[0]=='mem': return enc_op_mem_dn('subu', size, src[1:], dn)
    return None, None

def derives_from(L, i, r, j, rd):
    """le registre r, lu par L[i], vaut-il le resultat du 'subu rd' de L[j] ? (remontee de L[i-1] a
    L[j] par andi / decalages / copies ; tout autre ecriture de r -> non). Ex. mips 0x260b0 :
    'CMP.W D1,D2 ; BCC ; MOVE.W D1,D2' -- l'ecriture dans D2 est un rechargement, pas la difference."""
    for k in range(i-1, j-1, -1):
        y=L[k]
        if k==j: return r==rd
        if y.m in ('andi','addiu','ori','xori','slti','sltiu','lui','lb','lbu','lh','lhu','lw','ld','lq'):
            w=y.rt
        elif y.m in ('sll','sra','srl','dsll','dsra','dsrl','dsll32','dsra32','dsrl32','addu','daddu','subu',
                     'dsubu','and','or','xor','nor','slt','sltu','sllv','srlv','srav','mflo','mfhi','movz','movn'):
            w=y.rd
        elif y.m in ('jal','jalr','jr','j') or y.m.startswith('b'):
            continue
        else:
            w=None
        if w!=r or r==0: continue
        if y.m=='andi' or (y.m in ('addiu','ori') and y.imm==0): r=y.rs; continue
        if y.m in ('sll','sra','srl','dsll','dsra','dsrl','dsll32','dsra32','dsrl32'): r=y.rt; continue
        if y.m in ('addu','daddu','or') and 0 in (y.rs, y.rt): r=y.rs or y.rt; continue
        return False
    return False

def addx_at(L, i):
    """(HANDOFF §77) ADDX du recompilateur recent : 'lw t,X ; andi a,t,1 ; lw b,Dn ; addu a,b,a ;
    lw c,Dm ; addu a,c,a ; sw a,Dk' (Dk = Dn ou Dm) -> ADDX.L Dautre,Dk (division longue 0x8E7E0 :
    ADD.L D3,D3 ; ADDX.L D0,D0). Rend (source, destination, index apres le sw) ou None."""
    seq=[]; k=i
    while k<len(L) and len(seq)<7:
        y=L[k]; k+=1
        if (y.m=='sll' and y.w==0) or (y.m=='lui' and y.imm==0x7000): continue
        seq.append(y)
    if len(seq)<7: return None
    ms=[y.m for y in seq]
    if ms!=['lw','andi','lw','addu','lw','addu','sw'] or seq[1].imm!=1: return None
    t,a=seq[0].rt,seq[1].rt
    if seq[1].rs!=t: return None
    dn=slot_name(seq[2].simm&0xffff); dm=slot_name(seq[4].simm&0xffff); dk=slot_name(seq[6].simm&0xffff)
    if not (dn and dm and dk and dn[0]==dm[0]==dk[0]=='D'): return None
    b=seq[2].rt; c=seq[4].rt
    if {seq[3].rs,seq[3].rt}!={a,b} or seq[3].rd!=a or {seq[5].rs,seq[5].rt}!={a,c} or seq[5].rd!=a: return None
    if seq[6].rt!=a or dk not in (dn,dm): return None
    src=dm if dk==dn else dn
    return src[1], dk[1], k

def full_flags_block(L, i, r):
    """Recompilateur RECENT (Hyper) : apres 'subu r,a,b' il calcule C et V par formules completes
    (nor/and/or puis masque du bit de signe), puis :
        beq sC,zero,+28 ; addiu -1 ; sw C ; beq zero,zero,+16 ; sw zero,C     (retenue)
        sw r,RES                                                           (Z/N)
        beq sV,zero,+28 ; lw RES ; subu x,zero,RES ; sw x,RES                (V : N^V dans RES)
    Rend (vas a absorber, va du 'sw' de la negation, va du 'sw r,RES') ou None."""
    absorb=[]; negsw=None; resw=None; j=i+1; n=len(L)
    while j<n and j<i+60:
        x=L[j]
        if x.m in ('jal','jalr','jr') : return None
        if x.m=='sw' and x.rt==r and x.imm==RES_SLOT: resw=x.va; j+=1; continue
        if x.m=='beq' and x.rt==0 and x.rs!=0 and x.simm*4+4==28:
            k=j+1; seq=[]; idx=[]
            while k<n and len(seq)<6:
                y=L[k]
                if not (y.m=='sll' and y.w==0) and not (y.m=='lui' and y.imm==0x7000): seq.append(y); idx.append(k)
                k+=1
            ms=[y.m for y in seq]
            if ms[:4]==['addiu','sw','beq','sw'] and seq[1].imm==NFLG_SLOT and seq[2].rs==0 and seq[2].rt==0:
                absorb+= [x.va, seq[2].va]; j=idx[3]+1; continue
            if resw and ms[:3]==['lw','subu','sw'] and seq[0].imm==RES_SLOT and seq[1].rs==0 and seq[2].imm==RES_SLOT:
                absorb.append(x.va); negsw=seq[2].va
                return absorb, negsw, resw
            j+=1; continue
        if x.m in ('beq','bne','bgez','bltz','blez','bgtz'):
            break
        j+=1
    if resw and absorb: return absorb, negsw, resw
    return None

def exact_flags(L, i):
    """Variante 'drapeaux EXACTS' d'une soustraction (CMP/SUB), 2 165 blocs dans ro3 :
        r = a - b ; andi r,0xff|0xffff (taille)
        C = bit de signe de (~a&b)|(~a&r)|(b&r)      -> beq sC,zero (interne)
        V = bit de signe de (a&~b&~r)|(~a&b&r)       -> beq sV,zero (interne)
        RES = r ; si V : RES = -RES   => le SIGNE de RES vaut N xor V (comparaison SIGNEE)
    Rend (taille, adresses a absorber, adresses des 'sw RES' internes, derniere adresse)
    ou None."""
    r=L[i].rd; size=None; masks=[]; absorb=[]; resw=[]; neg=False; spilled=set(); sregs=set(); long_=False
    for j in range(i+1, min(len(L), i+64)):
        x=L[j]
        # (HANDOFF §77) comparaison 32 bits : masque de signe = 'and' avec un registre 'lui 0x8000'
        if x.m=='lui' and x.imm==0x8000: sregs.add(x.rt); continue
        if x.m=='and' and (x.rs in sregs or x.rt in sregs): masks.append(x.rd); long_=True; continue
        if x.rs==29 and x.m=='sw' and x.rt in masks: spilled.add(x.simm); continue
        if x.rs==29 and x.m=='lw' and x.simm in spilled: masks.append(x.rt); continue
        if x.rs==29 and x.m=='sw' and x.rt==r and size is None: spilled.add(('r',x.simm)); continue
        if x.rs==29 and x.m=='lw' and ('r',x.simm) in spilled: r=x.rt; continue
        if size is None and x.m=='andi' and x.rs==r and x.imm in (0xff,0xffff):
            size='B' if x.imm==0xff else 'W'; continue
        if x.m=='andi' and x.imm in (0x80,0x8000): masks.append(x.rt); continue
        if x.m=='beq' and x.rt==0 and x.rs in masks: absorb.append(x.va); continue
        if x.m=='beq' and x.rs==0 and x.rt==0 and absorb and len(absorb)<3: absorb.append(x.va); continue
        if x.m=='sw' and x.imm==RES_SLOT: resw.append(x.va)
        if x.m=='subu' and x.rs==0: neg=True; continue
        if neg and x.m=='sw' and x.imm==RES_SLOT:
            if size is None and long_: size='L'
            return (size, absorb, resw, x.va) if size and len(masks)>=2 and len(absorb)>=2 else None
        if x.m in ('jal','jalr','jr') : return None
    return None

def _operand(sym, mr):
    """operande symbolique d'un CMP : ('D',n) | ('A',n) | ('mem',sz,disp,an) | ('imm',v)"""
    if sym is not None:
        if sym.kind=='an' and sym.val[1]==0: return ('A',sym.val[0])
        if sym.kind=='reg68' and sym.val and sym.val[0]=='D': return ('D',sym.val[1])
        if sym.kind=='zx': return sym.val[0]
        if sym.kind=='imm': return ('imm',sym.val)
        # (HANDOFF §126) constante 32 bits 'lui+ori/addiu' (souvent une adresse PS2, convertie par enc_cmp §88) :
        # 40 blocs exacts longs perdus dans Upper ('CMPI.L #$A2C000,$C040(A5)')
        if sym.kind=='const' and CONST_OP: return ('imm',sym.val)
    if mr: return ('mem',)+mr
    return None

def enc_imm_dn(size, v, n):
    """valeur immediate -> Dn : MOVEQ si .L et -128..127 (forme courte, celle du code
    d'origine), sinon MOVE.x #v,Dn"""
    if size=='L':
        sv = v - 0x100000000 if v & 0x80000000 else v
        if -128 <= sv <= 127: return [0x7000|((n&7)<<9)|(sv&0xff)], "MOVEQ #%d,D%d"%(sv,n)
        return [0x203c|((n&7)<<9),(v>>16)&0xffff,v&0xffff], "MOVE.L #$%x,D%d"%(v&0xffffffff,n)
    if size=='W': return [0x303c|((n&7)<<9), v&0xffff], "MOVE.W #$%x,D%d"%(v&0xffff,n)
    return [0x103c|((n&7)<<9), v&0xff], "MOVE.B #$%x,D%d"%(v&0xff,n)
SHIFT_TYPE = {'sll':('LSL',1,1), 'srl':('LSR',0,1), 'sra':('ASR',0,0)}   # nom, direction, type (0=AS,1=LS)
def enc_shift_dn(kind, size, cnt, n):
    """decalage d'un registre par un compte immediat (1..8). La ROM prefere LSL a ASL
    pour les decalages a gauche (LSL.W 677 contre ASL.W 63)."""
    name,d,t = SHIFT_TYPE[kind]
    return [0xe000|((cnt&7)<<9)|(d<<8)|({'B':0,'W':1,'L':2}[size]<<6)|(t<<3)|(n&7)], "%s.%s #%d,D%d"%(name,size,cnt,n)

def _shorten(ins):
    """(d16,An) avec d16 = 0 -> (An) : forme qu'utilise le code d'origine (optimisation
    d'assembleur ; ROM : 'NEG.W D0 ; MOVE.W (A2),D1' present, forme '0(A2)' absente)."""
    import m68k
    op=ins[0]; h=op>>12
    if h in (6,7,0xe): return ins                       # Bcc/BSR, MOVEQ, decalages registre
    if h in (1,2,3):                                    # MOVE : source puis destination
        sz={1:0,3:1,2:2}[h]
        sm,sr=(op>>3)&7,op&7; dm,dr=(op>>6)&7,(op>>9)&7
        sl=m68k.ea_words(sm,sr,sz); dl=m68k.ea_words(dm,dr,sz)
        if sl is None or dl is None or len(ins)<1+sl+dl: return ins
        new=list(ins); drop=set()
        if dm==5 and ins[1+sl]==0: new[0]=(new[0]&~(7<<6))|(2<<6); drop.add(1+sl)
        if sm==5 and ins[1]==0: new[0]=(new[0]&~(7<<3))|(2<<3); drop.add(1)
        return [w for k,w in enumerate(new) if k not in drop]
    imm=0
    if (op&0xf100)==0 and ((op>>9)&7) in (0,1,2,3,5,6) and ((op>>6)&3)<3:
        imm = 2 if ((op>>6)&3)==2 else 1                # ORI/ANDI/SUBI/ADDI/EORI/CMPI #
    elif (op&0xff00)==0x0800: imm=1                     # BTST/BCHG/BCLR/BSET #bit
    if ((op>>3)&7)==5 and len(ins)>1+imm and ins[1+imm]==0:
        return [(op&~0x38)|(2<<3)] + ins[1:1+imm] + ins[2+imm:]
    return ins

def _acc_size(op):
    h=op>>12
    if h in (1,2,3): return {1:1,3:2,2:4}[h]
    sz=(op>>6)&3
    return {0:1,1:2,2:4}.get(sz)

def _rewrite_ea(ins, n, from_mode, disp, to_mode):
    """dans une instruction, remplace l'EA (from_mode, An) [+ deplacement 'disp' si mode 5]
    par to_mode. Rend la nouvelle instruction ou None."""
    import m68k
    op=ins[0]; h=op>>12; size=_acc_size(op)
    if h in (6,7,0xe) or size is None: return None
    if h in (1,2,3):
        sz={1:0,3:1,2:2}[h]
        sm,sr=(op>>3)&7,op&7; dm,dr=(op>>6)&7,(op>>9)&7
        sl=m68k.ea_words(sm,sr,sz); dl=m68k.ea_words(dm,dr,sz)
        if sl is None or dl is None: return None
        if sm==from_mode and sr==n and (from_mode!=5 or ins[1]==disp):
            new=[(op&~0x38)|(to_mode<<3)]+ins[1:]
            if from_mode==5: new=new[:1]+new[2:]
            return new
        if dm==from_mode and dr==n and (from_mode!=5 or ins[1+sl]==disp):
            new=[(op&~(7<<6))|(to_mode<<6)]+ins[1:]
            if from_mode==5: new=new[:1+sl]+new[2+sl:]
            return new
        return None
    if ((op>>3)&7)==from_mode and (op&7)==n:
        imm=0
        if (op&0xf100)==0 and ((op>>9)&7) in (0,1,2,3,5,6): imm = 2 if ((op>>6)&3)==2 else 1
        if from_mode==5 and (len(ins)<2+imm or ins[1+imm]!=disp): return None
        new=[(op&~0x38)|(to_mode<<3)]+ins[1:]
        if from_mode==5: new=new[:1+imm]+new[2+imm:]
        return new
    return None

def merge_postinc(out):
    """'ADDQ.W #s,An' suivi d'un acces de taille s a -s(An)  -> (An)+
       'SUBQ.W #s,An' suivi d'un acces de taille s a (An)    -> -(An)
    (formes de la ROM : 2cc1 = MOVE.L D1,(A6)+). Les deux entrees doivent etre consecutives."""
    import m68k
    res=list(out); prev=None
    for k,(va,mn,ws) in enumerate(res):
        if not ws: continue
        if prev is not None:
            pva,pmn,pws=res[prev]
            if len(pws)==1 and (pws[0]&0xf1f8) in (0x5048,0x5148):   # ADDQ.W/SUBQ.W #s,An (bits 11-9 = s)
                q=pws[0]; s=((q>>9)&7) or 8; n=q&7; sub=bool(q&0x0100)
                i=0; new=[]; done=False
                while i<len(ws):
                    r=m68k.decode_one(ws,i,len(ws)); L=r[0] if r else len(ws)-i
                    ins=list(ws[i:i+L]); cand=None
                    if not done and _acc_size(ins[0])==s:
                        cand=(_rewrite_ea(ins,n,2,None,4) if sub else _rewrite_ea(ins,n,5,(-s)&0xffff,3))
                    if cand: new+=cand; done=True
                    else: new+=ins
                    i+=L
                if done:
                    res[prev]=(pva,"(%s absorbe : %s)"%(pmn,"-(A%d)"%n if sub else "(A%d)+"%n),[])
                    res[k]=(va,mn+("  [-(A%d)]"%n if sub else "  [(A%d)+]"%n),new)
        prev=k
    return res

LONG_POSTINC=[0]
MEM_MISS=[]
AUDIT_MEM=__import__('os').environ.get('AUDIT_MEM')=='1'
DN_ALU=[0]
DN_ALU_ON=__import__('os').environ.get('DN_ALU','1')!='0'
from dn_alu import dn_alu as _dn_alu, a_alu as _a_alu, mem_fix as _mem_fix
MEM_FIX=[0]
ADDA_MEM=[0]
CHUTES=[]
def _chute(L, ins, reg, src, absread, memread, idxread, idxbig):
    """(HANDOFF §107) audit : ecriture de registre sans aucune instruction emise"""
    L.append((ins.va, ins.m, ins.imm, reg, (src.kind if src else None), bool(absread.get(ins.rt)),
              bool(memread.get(ins.rt)), bool(idxread.get(ins.rt)), bool(idxbig.get(ins.rt))))
ABS_AN=[0]
def merge_long_postinc(out, targets):
    """(HANDOFF §103) lecture d'un long par post-increment, emise en deux moities :
       'ADDQ.W #2,An ; SWAP Dm ; MOVE.W -2(An),Dm ; SWAP Dm ; MOVE.W (An)+,Dm'  ->  'MOVE.L (An)+,Dm'
    (moitie haute = premier mot, comme le long 68K). Jamais si un branchement vise l'interieur de la suite,
    ni si un Bcc suit (drapeaux du dernier MOVE.W)."""
    res=list(out)
    idx=[k for k,(va,mn,ws) in enumerate(res) if ws]
    j=0
    while j+4 < len(idx):
        k=[idx[j+t] for t in range(5)]
        w=[res[x][2] for x in k]
        ok=False
        if len(w[0])==1 and (w[0][0]&0xfff8)==0x5448 and len(w[1])==1 and (w[1][0]&0xfff8)==0x4840:
            n=w[0][0]&7; m=w[1][0]&7
            ok=(w[2]==[0x3028|(m<<9)|n,0xfffe] and w[3]==[0x4840|m] and w[4]==[0x3018|(m<<9)|n])
        if ok and any(res[x][0] in targets and res[x][0]!=res[k[0]][0] for x in range(k[0]+1,k[4]+1)): ok=False
        if ok and j+5 < len(idx):
            nx=res[idx[j+5]][2][0]
            if (nx&0xf000)==0x6000 and (nx&0x0f00) not in (0x0000,0x0100): ok=False
        if ok:
            va0,mn0,_=res[k[0]]
            res[k[0]]=(va0,"MOVE.L (A%d)+,D%d  [long par post-increment]"%(n,m),[0x2018|(m<<9)|n])
            for x in k[1:]: res[x]=(res[x][0],"(%s absorbe)"%res[x][1],[])
            LONG_POSTINC[0]+=1; j+=5; continue
        j+=1
    return res

def _ecrase_nzvc(w):
    """premier mot d'une instruction qui ECRASE N,Z,V,C sans les lire (liste blanche prudente)"""
    t=w>>12
    if t in (1,2,3): return ((w>>6)&7)!=1                      # MOVE (pas MOVEA)
    if (w&0xf100)==0x7000: return True                         # MOVEQ
    if (w&0xff00) in (0x4a00,0x4200): return (w&0xc0)!=0xc0     # TST / CLR
    if t==0xb: return True                                     # CMP / CMPA / CMPM / EOR
    if (w&0xff00)==0x0c00: return (w&0xc0)!=0xc0               # CMPI
    if t==5: return (w&0xc0)!=0xc0 and ((w>>3)&7)!=1           # ADDQ / SUBQ (pas An, pas Scc/DBcc)
    return False
VRAM_SHIFT=[0]
COPIES=[0]
COPIES_ON=os.environ.get('COPIES','1')!='0'
IDX_X4=[0]
def vram_shift_const(out, targets=()):
    """(HANDOFF §110) adresse de la memoire video PS2 formee par decalage : 'MOVEQ #0,Dn ; MOVE.W #imm,Dn ;
    LSL.L #8,Dn' (ROM $25E8E : tampons de palettes $91C000 / $920000 du generique de fin, mips 0x27A94 / 0x27AD0).
    La constante n'est pas vue comme une adresse -> la base des palettes visait $93C000 / $940000 (fins noires).
    On convertit l'immediat quand imm << 8 tombe dans la memoire video PS2."""
    res=list(out)
    idx=[k for k,(va,mn,ws) in enumerate(res) if ws]
    for j in range(len(idx)-2):
        a,b,c=(res[idx[j+t]][2] for t in range(3))
        if len(a)!=1 or len(b)!=2 or len(c)!=1: continue
        n=(b[0]>>9)&7
        if a[0]!=(0x7000|(n<<9)) or b[0]!=(0x303c|(n<<9)) or c[0]!=(0xe188|n): continue
        v=b[1]<<8; rel=v-(RAM_HI<<16)
        if not (0x20000 <= rel < 0x50000): continue
        if any(res[idx[j+t]][0] in targets and res[idx[j+t]][0]!=res[idx[j]][0] for t in (1,2)): continue
        t=addr_to_68k(v)               # avec la marque materielle (HW_TAG) : jamais reconvertie a l'execution
        if t is None: continue
        va,mn,_=res[idx[j]]
        res[idx[j]]=(va,"MOVE.L #$%08x,D%d  [memoire video, forme par decalage]"%(t,n),[0x203c|(n<<9),t>>16,t&0xffff])
        for x in (idx[j+1],idx[j+2]): res[x]=(res[x][0],"(%s absorbe)"%res[x][1],[])
        VRAM_SHIFT[0]+=1
    return res
VRAM_TABLE=[0]
VRAM_TABLE_ON=os.environ.get('VRAM_TABLE','1')!='0'
VRAM_TABLE_BUF=[None]                  # module en cours (translate) : lecture des tables de donnees
def vram_table_shift(out, targets=()):
    """(agent_decor_cammy, DECOR-CAMMY.md) adresse de la memoire video PS2 formee par decalage d'un mot de TABLE :
    'MOVE.W T(PC,Dx.W),Dn ; LSL.L #8,Dn ; ANDI.L #$00FFFFFF,Dn' (gestionnaire scroll2 du decor $2C de Cammy :
    ro5 mips 0x155D08, T_614A60 = $A240/$A340 ; ro3 mips 0x111698, T_58C2E0 = $9240/$9340). Le mot est une adresse
    video HOTE >> 8 (donnees du module, non converties) : la base CPS-A de scroll2 visait $924000 / $934000 au lieu de
    $904000 / $914000 (plan du dessus faux : sol et batiments caches, motif bruite). Comme vram_shift_const (§110),
    mais a l'execution et borne : si la valeur tombe dans la video hote [base+$20000, base+$50000), elle devient
    l'adresse CPS2 marquee (addr_to_68k) ; sinon elle reste telle quelle. TST.L final : N, Z, V, C comme l'ANDI.
    Garde : la table doit commencer par une adresse video (contenu lu dans le module), et l'instruction suivante
    ne doit pas lire X (MOVE / SWAP). VRAM_TABLE=0 : ancien comportement."""
    import re as _re
    buf=VRAM_TABLE_BUF[0]
    if buf is None: return out
    res=list(out)
    idx=[k for k,(va,mn,ws) in enumerate(res) if ws]
    for j in range(len(idx)-3):
        (va_a,mn_a,a),(va_b,mn_b,b),(va_c,mn_c,c)=(res[idx[j+t]] for t in range(3))
        m=_re.match(r"MOVE\.W T_([0-9a-f]{6})\(PC,D\d\.W\),D(\d)$", mn_a)
        if not m: continue
        n=int(m.group(2)); tb=int(m.group(1),16)
        if b!=[0xe188|n] or c!=[0x0280|n,0x00ff,0xffff]: continue
        if any(res[idx[j+t]][0] in targets and res[idx[j+t]][0]!=va_a for t in (1,2)): continue
        nxt=res[idx[j+3]][1]
        if not (nxt.startswith("MOVE") or nxt.startswith("SWAP")): continue
        o=tb-0x1f0000
        if not (0 <= o < len(buf)-1): continue
        w=struct.unpack_from('<H',buf,o)[0]
        lo=(RAM_HI<<16)+0x20000; hi=(RAM_HI<<16)+0x50000
        if not (lo <= (w<<8) < hi): continue
        t=addr_to_68k(lo)
        if t is None or addr_to_68k(lo+0x1000)!=t+0x1000: continue
        d=(t-lo)&0xffffffff
        ws=[0x0c80|n,lo>>16,lo&0xffff, 0x6500|0x0e,           # CMPI.L #lo,Dn ; BCS.S fin
            0x0c80|n,hi>>16,hi&0xffff, 0x6400|0x06,           # CMPI.L #hi,Dn ; BCC.S fin
            0x0680|n,d>>16,d&0xffff,                          # ADDI.L #(cps2 - hote),Dn
            0x4a80|n]                                         # fin : TST.L Dn
        res[idx[j+2]]=(va_c,mn_c+" ; [video hote $%x-$%x -> $%x+ : CMPI/BCS/CMPI/BCC/ADDI.L #$%08x ; TST.L D%d]  [memoire video, mot de table decale]"%(lo,hi,t,d,n),c+ws)
        VRAM_TABLE[0]+=1
    return res
LONG_SR=[0]
def drop_dead_sr(out):
    """(HANDOFF §104) operation en place sur un long echange (inplace_long) : la sauvegarde des drapeaux
    (MOVE SR,-(SP) ... MOVE (SP)+,CCR ; MOVEM.L (SP)+,Dt) est inutile quand l'instruction suivante ecrase N,Z,V,C
    sans les lire (X n'est touche ni par SWAP ni par MOVE : il reste celui de l'operation)."""
    res=list(out)
    idx=[k for k,(va,mn,ws) in enumerate(res) if ws]
    for j in range(len(idx)-1):
        va,mn,ws=res[idx[j]]
        if not mn.startswith("[long echange]") or 0x40e7 not in ws or len(ws)<4 or ws[-2]!=0x4cdf: continue
        if not _ecrase_nzvc(res[idx[j+1]][2][0]): continue
        dt=(ws[-1]).bit_length()-1
        nw=[x for x in ws[:-2] if x not in (0x40e7,0x44df)]
        # (les mots 0x40e7/0x44df ne peuvent pas etre des deplacements/immediats ici : verifie par la longueur)
        if len(nw)!=len(ws)-4: continue
        res[idx[j]]=(va,mn+"  [drapeaux morts]",nw+[0x201f|(dt<<9)])        # MOVE.L (SP)+,Dt
        LONG_SR[0]+=1
    return res

def byte_streams(out):
    """FLUX D'OCTETS (An)+ EN MODE cps2 (HANDOFF §65) : 'ADDQ.W #1,An ; MOVE.B -2(An),Dm' (XOR 1 du
    deplacement -1, juste seulement si An etait IMPAIR). Un flux alterne la parite a chaque octet : on
    rend l'adresse exacte a l'execution, An XOR 1, en basculant le bit 0 de An via la pile :
      MOVE.L An,-(SP) ; EORI.B #1,3(SP) ; MOVEA.L (SP)+,An ; MOVE.B (An),Dm (ou Dm,(An)) ;
      (meme bascule) ; ADDQ.L #1,An ; TST.B Dm   (drapeaux de MOVE.B : N,Z, V=C=0)"""
    res=list(out); prev=None
    for k,(va,mn,ws) in enumerate(res):
        if not ws: continue
        if prev is not None:
            pva,pmn,pws=res[prev]
            if len(pws)==1 and (pws[0]&0xfff8)==0x5248 and len(ws)==2 and ws[1]==0xfffe and (ws[0]&0xf000)==0x1000:
                n=pws[0]&7; w=ws[0]; src=w&0x3f; dst=(w>>6)&0x3f
                tog=[0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
                acc=None
                if src==(0x28|n) and (dst&7)==0:                        # MOVE.B d(An),Dm (dest : reg<<3|mode)
                    m=dst>>3; acc=[0x1010|(m<<9)|n]
                elif (src&0x38)==0 and dst==((n<<3)|5):                 # MOVE.B Dm,d(An) (dest : reg<<3|mode)
                    m=src&7; acc=[0x1080|(n<<9)|m]
                if acc:
                    res[prev]=(pva,"(ADDQ.W #1,A%d : flux d'octets)"%n,[])
                    res[k]=(va,mn+"  [flux d'octets (A%d)+ : adresse XOR 1 a l'execution]"%n,
                            tog+acc+tog+[0x5288|n, 0x4a00|m])
        # (HANDOFF §126) ouverture d'une zone D8 intercalee entre l'ADDQ et la lecture (Upper mips 0x250604-0x250610 :
        # 'ADDQ.W #1,A4 ; [D8 <- D7 prete] ; MOVE.B -2(A4),D7') : ne touche pas An -> le flux reste reconnu
        if prev is not None and "[D8 <- D" in mn and res[prev][2] and len(res[prev][2])==1: continue
        prev=k
    return res

BYTE_EA=[0]
BYTE_EA_ON=__import__('os').environ.get('FLUXEA','1')!='0'
def byte_streams_ea(out, br_targets=()):
    """(agent_bandeau_A) FLUX D'OCTETS (An)+ HORS REGISTRE DE DONNEES EN MODE cps2 : byte_streams ne reconnait que
    'ADDQ.W #1,An ; MOVE.B -2(An),Dm' (et l'ecriture Dm,-2(An)). Les autres formes gardaient le deplacement -2
    (XOR 1 de -1), juste seulement si An etait IMPAIR : MOVE.B -2(A3),$E(A4) (memoire -> memoire), CMP.B/ADD.B
    -2(An),Dm, TST.B -2(An), CMPI.B #imm,-2(An), MOVE.B d(Ak),-2(An), copie MOVE.B -2(A3),-2(A2)... SFA3 mips
    0x937B4 (ROM $337E4) : le 1er octet (vitesse) etait lu dans le mot precedent (Y) -> textes « STREET FIGHTER
    ALPHA » de la transition du gros A lances a $48/$70/$98 px par image au lieu de 0. Adresse exacte a
    l'execution pour chaque An en attente (+1) dont l'EA vaut -2(An) :
      (bascule du bit 0 de An via la pile) ; <instr> (An) ; MOVE SR,-(SP) ; (bascule) ; MOVE (SP)+,CCR ; ADDQ.L #1,An
    (l'instruction pose ses drapeaux, X compris ; ADDQ sur An n'y touche pas). FLUXEA=0 : ancien comportement."""
    res=list(out)
    tog=lambda n: [0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
    def eas(ws):
        """[(champ, mode, reg, index du mot d'extension, nb de mots)] des EA d'une instruction OCTET reconnue"""
        w=ws[0]; top=w>>12
        if top==1:                                                  # MOVE.B
            sm,sr,dm,dr=(w>>3)&7,w&7,(w>>6)&7,(w>>9)&7
            import m68k
            ks=m68k.ea_words(sm,sr,0); kd=m68k.ea_words(dm,dr,0)
            if ks is None or kd is None or 1+ks+kd!=len(ws): return None
            return [('s',sm,sr,1,ks),('d',dm,dr,1+ks,kd)]
        if top==0 and (w&0xff00) in (0x0000,0x0200,0x0400,0x0600,0x0a00,0x0c00) and (w>>6)&3==0:   # ORI..CMPI .B #imm
            if len(ws)!=3: return None
            return [('s',(w>>3)&7,w&7,2,1)]
        if (w&0xffc0) in (0x4a00,0x4200,0x4400,0x4600) and len(ws)==2:      # TST.B CLR.B NEG.B NOT.B
            return [('s',(w>>3)&7,w&7,1,1)]
        if top in (8,9,0xb,0xc,0xd) and (w>>6)&7 in (0,4) and len(ws)==2:   # OR/SUB/CMP(EOR)/AND/ADD .B
            if top==0xb and (w>>6)&7==4: pass                             # EOR.B Dn,<ea>
            return [('s',(w>>3)&7,w&7,1,1)]
        return None
    for k,(va,mn,ws) in enumerate(res):
        if not ws or len(ws)<2 or va in br_targets: continue
        # ADDQ.W #1,An en attente juste avant (1 ou 2 : copie (A3)+ -> (A2)+)
        pend={}; j=k-1
        while j>=0 and len(pend)<2:
            pva,pmn,pws=res[j]
            if not pws: j-=1; continue
            if len(pws)==1 and (pws[0]&0xfff8)==0x5248 and (pws[0]&7)!=7 and (pws[0]&7) not in pend:
                pend[pws[0]&7]=j; j-=1; continue
            break
        if not pend: continue
        e=eas(ws)
        if not e: continue
        cible=[x for x in e if x[1]==5 and x[2] in pend and ws[x[3]]==0xfffe]
        if not cible: continue
        regs={x[2] for x in cible}
        # un autre EA qui utilise un des An bascules : on laisse
        if any(x not in cible and x[1] in (2,3,4,5,6) and x[2] in regs for x in e): continue
        w=ws[0]; drop=set()
        for f,m_,r_,ix,nw in cible:
            if f=='s': w=(w&~0x3f)|0x10|r_
            else: w=(w&~0x0fc0)|(r_<<9)|(2<<6)
            drop.add(ix)
        ins=[w]+[x for i,x in enumerate(ws[1:],1) if i not in drop]
        pre=[]; post=[]
        for r_ in sorted(regs): pre+=tog(r_); post+=tog(r_)
        new=pre+ins+[0x40e7]+post+[0x44df]+[0x5288|r_ for r_ in sorted(regs)]
        for r_ in regs:
            pva,pmn,pws=res[pend[r_]]
            res[pend[r_]]=(pva,"(ADDQ.W #1,A%d : flux d'octets)"%r_,[])
        res[k]=(va,mn+"  [flux d'octets %s : adresse XOR 1 a l'execution]"%",".join("(A%d)+"%r_ for r_ in sorted(regs)),new)
        BYTE_EA[0]+=1
    return res

BYTE_PRE=[0]
BYTE_PRE_ON=__import__('os').environ.get('BYTE_PRE','1')!='0'
def byte_streams_pre(out):
    """(agent_ro9) FLUX D'OCTETS DECROISSANT EN MODE cps2 : 'SUBQ.W #1,An ; MOVE.B 1(An),<ea>' (deplacement 0 XOR 1,
    juste seulement si An est PAIR apres le decrement). Hyper mips 0x33C4F0 : A8 = table 0x5C6960 + 4*perso + 4,
    puis 'A8 -= 1 ; lb 0(A8)' : premier octet lu a une adresse IMPAIRE -> octet du perso suivant. Adresse exacte
    a l'execution (An XOR 1, bascule du bit 0 via la pile) ; la bascule de retour garde les drapeaux du MOVE.B."""
    import m68k
    res=list(out); prev=None
    tog=lambda n: [0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
    for k,(va,mn,ws) in enumerate(res):
        if not ws: continue
        if prev is not None:
            pva,pmn,pws=res[prev]
            if len(pws)==1 and (pws[0]&0xfff8)==0x5348 and len(ws)>=2 and (ws[0]&0xf000)==0x1000 and ws[1]==0x0001:
                n=pws[0]&7; w=ws[0]; dmode=(w>>6)&7; dreg=(w>>9)&7
                r=m68k.decode_one(ws,0,len(ws))
                if (w&0x3f)==(0x28|n) and r and r[0]==len(ws) and not (dmode in (2,3,4,5,6) and dreg==n) \
                   and not (dmode==7 and dreg in (2,3)):
                    new=tog(n)+[(w&~0x3f)|0x10|n]+ws[2:]+[0x40e7]+tog(n)+[0x44df]
                    res[k]=(va,mn+"  [flux d'octets -(A%d) : adresse XOR 1 a l'execution]"%n,new)
                    BYTE_PRE[0]+=1
        prev=k
    return res

def _idx_rmw_store(L, k, r, lim=4, sz=('sb','sh')):
    """(HANDOFF §138) 'op r' suivi (sans branchement) d'un sb/sh de r : lecture-modification-ecriture"""
    for y in L[k+1:k+1+lim]:
        if y.m in sz and y.rt==r: return True
        if dest_reg(y)==r or y.m[0] in 'bj': return False
    return False

def byte_index_exact(out):
    """OCTET INDEXE EN MODE cps2 (HANDOFF §66) : 'd8(An,Xn)' portait d8 XOR 1 en supposant l'index PAIR ;
    faux pour un index impair (numero de joueur 0/1 : ecriture dans le mot voisin). Adresse exacte a
    l'execution = (An + Xn + d_mips) XOR 1 :
      MOVE.L An,-(SP) ; LEA d_mips(An,Xn),An ; (bascule du bit 0 via la pile) ; <instr> (An) ; MOVEA.L (SP)+,An
    (l'instruction pose elle-meme les drapeaux ; MOVEA ne les touche pas)."""
    import m68k
    res=[]
    for va,mn,ws in out:
        if not ws or 'index pair suppose' not in mn:
            res.append((va,mn,ws)); continue
        r=m68k.decode_one(ws,0,len(ws))
        if not r or r[0]!=len(ws): res.append((va,mn,ws)); continue
        w=ws[0]; new=None
        src_mode,src_reg=(w>>3)&7,w&7
        is_move=(w&0xc000)==0 and (w&0x3000)!=0
        dst_mode,dst_reg=((w>>6)&7,(w>>9)&7) if is_move else (None,None)
        if src_mode==6 and (w&0xf100)==0 and ((w>>9)&7) in (0,1,2,3,5,6):
            n=src_reg; ext=ws[-1]                         # (HANDOFF §138) #imm,d8(An,Xn) : extension APRES l'immediat
            ins=[(w&~0x3f)|0x10|n]+ws[1:-1]
        elif src_mode==6:                                 # EA source (ou unique) indexee : mot d'extension en ws[1]
            n=src_reg; ext=ws[1]; rest=ws[2:]
            if is_move and dst_mode in (2,3,4,5,6) and dst_reg==n: res.append((va,mn,ws)); continue
            ins=[(w&~0x3f)|0x10|n]+rest
        elif is_move and dst_mode==6:                     # destination indexee : extension apres celles de la source
            L=len(ws); n=dst_reg; ext=ws[-1]
            if src_mode in (2,3,4,5,6) and src_reg==n: res.append((va,mn,ws)); continue
            ins=[(w&~0x0fc0)|(n<<9)|(2<<6)]+ws[1:-1]
        else:
            res.append((va,mn,ws)); continue
        if (ext>>12)&0xf==(8|n): res.append((va,mn,ws)); continue     # index = An lui-meme : on laisse
        d8=(ext&0xff)^1                                   # deplacement MIPS (le XOR 1 etait sur d8)
        lea=[0x41f0|(n<<9)|n, (ext&0xff00)|(d8&0xff)]
        tog=[0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
        res.append((va, mn.replace('index pair suppose','adresse XOR 1 a l execution'),
                    [0x2f08|n]+lea+tog+ins+[0x205f|(n<<9)]))
    return res

def byte_after_adda(out):
    """(HANDOFF §97) OCTET VIA UN REGISTRE D'ADRESSE DE PARITE INCONNUE : apres 'ADDA.W/L Dk,An', un acces
    octet d16(An) portait d16 XOR 1 en supposant An pair (ROM : 'LEA $128(A6),A0 ; ADDA.W D0,A0 ;
    MOVE.B D0,(A0)', tableau des resultats de manche : mauvais octet pour les manches d'index pair).
    Adresse exacte a l'execution, comme byte_index_exact :
      MOVE.L An,-(SP) ; LEA d_mips(An),An ; (bascule du bit 0 via la pile) ; <instr> (An) ; MOVEA.L (SP)+,An
    Juste quelle que soit la parite : appliquee jusqu'a la reaffectation de An ou une rupture."""
    import m68k
    res=[]; dirty=set(); N=[0]
    for va,mn,ws in out:
        if not ws: res.append((va,mn,ws)); continue
        # suivi des registres : ADDA Dk,An -> sale ; LEA/MOVEA vers An -> propre ; rupture -> tout propre
        def scan(words):
            i=0; n=len(words)
            while i<n:
                r=m68k.decode_one(words,i,n)
                if r is None: break
                w=words[i]
                if (w&0xf0f8) in (0xd0c0,) and (w&0x01c0) in (0x00c0,0x01c0): dirty.add((w>>9)&7)   # ADDA.W/L Dk,An
                elif (w&0xf1c0)==0x41c0 or ((w&0xc1c0)==0x0040 and (w&0x3000)): dirty.discard((w>>9)&7)          # LEA / MOVEA
                elif w==0x4e75 or (w&0xffc0) in (0x4ec0,0x4e80) or (w&0xff00)==0x6000: dirty.clear()
                i+=r[0]
        r=m68k.decode_one(ws,0,len(ws))
        single = r is not None and r[0]==len(ws)
        w=ws[0]; new=None
        if single and dirty and '[' not in mn and ' .B' not in mn and mn.split(' ')[0].endswith('.B'):
            is_move=(w&0xf000)==0x1000
            src_mode,src_reg=(w>>3)&7,w&7
            dst_mode,dst_reg=((w>>6)&7,(w>>9)&7) if is_move else (None,None)
            n=None
            if src_mode==5 and src_reg in dirty and src_reg!=7 and not (is_move and dst_mode in (2,3,4,5,6) and dst_reg==src_reg):
                n=src_reg; k=1 if is_move else len(ws)-1
                ins=[(w&~0x3f)|0x10|n]+ws[1:k]+ws[k+1:]
            elif is_move and dst_mode==5 and dst_reg in dirty and dst_reg!=7 and not (src_mode in (2,3,4,5,6) and src_reg==dst_reg):
                n=dst_reg; k=len(ws)-1
                ins=[(w&~0x0fc0)|(n<<9)|(2<<6)]+ws[1:k]
            if n is not None:
                d=ws[k]^1                                  # deplacement MIPS (le XOR 1 etait sur d16)
                tog=[0x2f08|n, 0x0a2f,0x0001,0x0003, 0x205f|(n<<9)]
                new=[0x2f08|n, 0x41e8|(n<<9)|n, d]+tog+ins+[0x205f|(n<<9)]
                N[0]+=1
        if new: res.append((va, mn+"  [octet via A apres ADDA : adresse XOR 1 a l'execution]", new))
        else: res.append((va,mn,ws))
        scan(ws)
    BYTE_ADDA[0]+=N[0]
    return res
BYTE_ADDA=[0]

def zero_disp_short(ws):
    """applique _shorten a chaque instruction d'une suite de mots"""
    import m68k
    out=[]; i=0; n=len(ws)
    while i<n:
        r=m68k.decode_one(ws,i,n)
        if r is None or i+r[0]>n: out+=ws[i:]; break
        out+=_shorten(list(ws[i:i+r[0]])); i+=r[0]
    return out

def movea_l_mem(an, disp, am):
    """MOVEA.L d16(An),Am. En mode cps2 la valeur est rangee echangee en memoire : on la
    remet dans l'ordre via un registre de donnees (SWAP n'existe que sur Dn), en preservant
    les indicateurs (MOVEA n'en modifie aucun, SWAP si) :
      MOVEA.L d(An),Am ; EXG Am,D0 ; MOVE SR,-(SP) ; SWAP D0 ; MOVE (SP)+,CCR ; EXG Am,D0"""
    ws=[0x2068|((am&7)<<9)|(an&7), disp&0xffff]
    mn="MOVEA.L $%04x(A%d),A%d"%(disp,an,am)
    if MEMMODE=='cps2':
        exg=0xc188|(0<<9)|(am&7)                       # EXG D0,Am (mode donnee/adresse)
        ws+=[exg,0x40e7,SWAP_OP|0,0x44df,exg]; mn+=" ; [remise en ordre du long]"
    return ws, mn

def idx_ext(dn, dsz, d8):
    """mot d'extension breve d8(An,Dn.W/.L)"""
    return ((dn&7)<<12) | (0x800 if dsz=='L' else 0) | (d8&0xff)
def idxbig_seq(size, n, dn, dsz, d16, op):
    """(HANDOFF §78) acces a d16(An,Dn) : An sauve, adresse exacte calculee (octet : XOR 1 en mode cps2),
    'op' = mots de l'instruction qui utilise (An), puis An restaure"""
    ws=[0x2f08|n, 0x41e8|((n&7)<<9)|(n&7), d16&0xffff, (0xd1c0 if dsz=='L' else 0xd0c0)|((n&7)<<9)|(dn&7)]
    if MEMMODE=='cps2' and size=='B': ws+=[0x2f08|n, 0x0a2f, 0x0001, 0x0003, 0x205f|((n&7)<<9)]
    return ws+op+[0x205f|((n&7)<<9)]
def idx_note(size):
    return "  [octet indexe : index pair suppose]" if (MEMMODE=='cps2' and size=='B') else ""

N_BTST_CONFLIT=[0]          # (HANDOFF §80) BTST differe sauve avant une ecriture du meme octet
def enc_logic_mem(kind, size, mask, an, disp):
    """operation logique EN PLACE sur la memoire avec un immediat :
      octet, un seul bit : BSET / BCLR / BCHG #b,d(An)   (forme de la ROM)
      sinon              : ORI / ANDI / EORI.x #imm,d(An)"""
    ea=0x28|(an&7); full=SZMASK[size]; m=mask & full
    if size=='B':
        if kind=='or'  and m and (m&(m-1))==0:
            b=m.bit_length()-1; return [0x08c0|ea, b, disp&0xffff], "BSET #%d,$%04x(A%d)"%(b,disp,an)
        inv=(~m)&0xff
        if kind=='and' and inv and (inv&(inv-1))==0:
            b=inv.bit_length()-1; return [0x0880|ea, b, disp&0xffff], "BCLR #%d,$%04x(A%d)"%(b,disp,an)
        if kind=='xor' and m and (m&(m-1))==0:
            b=m.bit_length()-1; return [0x0840|ea, b, disp&0xffff], "BCHG #%d,$%04x(A%d)"%(b,disp,an)
    base={'or':0x0000,'and':0x0200,'xor':0x0a00}[kind]
    return [base|(SZN[size]<<6)|ea]+_imm_words(size,m)+[disp&0xffff], "%s.%s #$%x,$%04x(A%d)"%(
        {'or':'ORI','and':'ANDI','xor':'EORI'}[kind],size,m,disp,an)

def abs_addr(host, size):
    """adresse ABSOLUE : mode hote = adresse PS2 brute ; mode cps2 = convertie par la carte
    (octet : XOR 1, l'adresse etant connue exactement). Rend (adresse, note)."""
    if MEMMODE!='cps2': return host & 0xffffffff, ""
    a=addr_to_68k(host)
    if a is None: return host & 0xffffffff, "  [ADRESSE HOTE %08x HORS CARTE : crochet du portage ?]"%host
    off=host-(RAM_HI<<16)
    # entrees (BYTE_EXACT) et RAM partagee QSound (0x60000-0x61FFF -> $618000, octets IMPAIRS comme la ROM :
    # port 0x96001F = ROM $61801F, HANDOFF §78) : correspondance octet EXACTE
    if size=='B' and off not in BYTE_EXACT and not (0x60000<=off<0x62000): a^=1
    return a, ""
def _producer(L, i, r, lim=24):
    """indice de la derniere instruction qui ecrit le registre MIPS r avant L[i]"""
    for j in range(i-1, max(-1,i-lim), -1):
        if dest_reg(L[j])==r: return j
        if L[j].m in ('jal','jalr','jr','beq','bne','bgez','bltz'): return None
    return None
def _origin(L, j):
    """source d'une valeur a travers les extensions de signe : ('slot',off,taille) ou
    ('mem',base_reg_j,disp,taille) - simplifie : on rend l'instruction de chargement"""
    while j is not None and L[j].m in ('dsll32','dsra32'):
        j=_producer(L, j, L[j].rt)
    return j
def c_dispatch(L, i):
    """(HANDOFF §140) AIGUILLEUR « C » DU PORTAGE (Hyper mips 0x2D550, fin de match VERSUS) : 'lw x,An_dom ;
    lh y,d(x) ; ext ; sra k1 ; sll k2 ; lui/addiu T ; addu ; lw t,0(..) ; jalr t' (index lu en MEMOIRE, transforme
    en temporaires : aucun registre 68K). Rend (table, An, d, taille, k1, k2) ou None."""
    j=_producer(L, i, L[i].rs, 8)
    if j is None or L[j].m!='lw' or L[j].simm!=0: return None
    a=_producer(L, j, L[j].rs, 8)
    if a is None or L[a].m!='addu': return None
    for p_,q_ in ((L[a].rs,L[a].rt),(L[a].rt,L[a].rs)):
        jt=_producer(L, a, p_, 8); jx=_producer(L, a, q_, 8)
        if jt is None or jx is None or L[jt].m!='addiu': continue
        jl=_producer(L, jt, L[jt].rs, 8)
        if jl is None or L[jl].m!='lui': continue
        tbl=((L[jl].imm<<16)+L[jt].simm)&0xffffffff
        if L[jx].m!='sll' or L[jx].sa not in (1,2,3): continue
        k2=L[jx].sa; k1=0; js=_producer(L, jx, L[jx].rt, 8)
        if js is not None and L[js].m in ('sra','srl') and 1<=L[js].sa<=3: k1=L[js].sa; js=_producer(L, js, L[js].rt, 8)
        js=_origin(L, js)
        if js is None or L[js].m not in ('lh','lhu','lb','lbu'): continue
        jb=_producer(L, js, L[js].rs, 8)
        if jb is None or L[jb].m!='lw': continue
        nm=slot_name(L[jb].simm & 0xffff)
        if not nm or nm[0]!='A': continue
        return tbl, nm[1], L[js].simm, ('W' if L[js].m in ('lh','lhu') else 'B'), k1, k2
    return None
def adda_mem(L, i):
    """(HANDOFF §107) 'lw rB,An ; [addiu rB,rB,d] ; lh rH,d'(rB) ; dsll32/dsra32 (signe) ; lw rA,Am ; addu rX,rA,rS ;
    sw rX,Am' = ADDA.W d(An),Am (tables a decalages relatifs Capcom). Rend (n, d) ou None."""
    x=L[i]
    j=_producer(L,i,x.rt,8)
    if j is None or L[j].m!='addu': return None
    for rA,rS in ((L[j].rs,L[j].rt),(L[j].rt,L[j].rs)):
        k=_producer(L,j,rA,8)
        if k is None or L[k].m!='lw' or L[k].imm!=x.imm: continue
        h=_origin(L,_producer(L,j,rS,8))
        if h is None or L[h].m!='lh': continue
        # extension de signe 16 bits exacte (dsll32 16 / dsra32 16) entre lh et addu
        js=_producer(L,j,rS,8)
        if L[js].m!='dsra32' or L[js].sa!=16: continue
        d=L[h].simm; b_=_producer(L,h,L[h].rs,8)
        if b_ is not None and L[b_].m=='addiu' and L[b_].rt==L[h].rs and L[b_].rs==L[h].rs:
            d+=L[b_].simm; b_=_producer(L,b_,L[h].rs,8)
        if b_ is None or L[b_].m!='lw': continue
        nm=slot_name(L[b_].imm)
        if not nm or nm[0]!='A' or nm[1]>6 or not (-0x8000<=d<=0x7fff): continue
        return nm[1], d
    return None

def bswap16_of(L, i):
    """'or' = ((x & $FF) << 8) | ((x & $FF00) >> 8 & $FF) : inversion des octets d'un mot
    (champ que le portage range octet par octet). Rend ('slot',off) ou ('mem',disp,base_slot)
    de x (charge en .W), sinon None."""
    x=L[i]; parts=[]
    for r in (x.rs, x.rt):
        j=_producer(L, i, r); seq=[]
        while j is not None and L[j].m in ('andi','sll','sra','srl') and len(seq)<5:
            seq.append((L[j].m, L[j].imm if L[j].m=='andi' else L[j].sa)); j=_producer(L, j, L[j].rt)
        j=_origin(L, j) if j is not None else None
        if j is None or L[j].m not in ('lh','lhu'): return None
        parts.append((tuple(seq), j))
    kinds=set()
    for seq,j in parts:
        s2=[t for t in seq if t!=('andi',0xff)]
        if s2==[('sll',8)] and ('andi',0xff) in seq: kinds.add('lo')
        elif s2 in ([('sra',8),('andi',0xff00)],[('srl',8),('andi',0xff00)]): kinds.add('hi')
        else: return None
    if kinds!={'lo','hi'}: return None
    a,b=L[parts[0][1]],L[parts[1][1]]
    if a.imm!=b.imm: return None
    pa,pb=_producer(L,parts[0][1],a.rs),_producer(L,parts[1][1],b.rs)
    if pa is None or pb is None: return None
    A,B=L[pa],L[pb]
    if A.m==B.m=='lui' and A.imm==0x7000 and a.imm==b.imm and 0x1124<=a.imm<=0x1140:
        return ('D',(a.imm-0x1124)//4)                   # mot d'un registre D (source = case du banc)
    if not (A.m==B.m=='lw' and A.imm==B.imm): return None
    pl=_producer(L,pa,A.rs)
    if pl is not None and L[pl].m=='lui' and L[pl].imm==0x7000:
        if 0x1100<=A.imm<0x111c: return ('mem', a.simm & 0xffff, (A.imm-0x1100)//4)   # d16(An)
        return None
    pl2=_producer(L,parts[0][1],a.rs)
    if L[pl2].m=='lui' and L[pl2].imm==0x7000 and 0x1124<=a.imm<=0x1140: return ('D',(a.imm-0x1124)//4)
    return None
def rot_of(L, i):
    """'or' = (x >> k) | (x << (w-k)), x = Dn.w zero-etendu (w = 8 ou 16) : ROR #k (ou ROL).
    Rend (dn, taille, 'ror'|'rol', compte) ou None."""
    x=L[i]; parts=[]
    for r in (x.rs, x.rt):
        j=_producer(L, i, r)
        if j is None or L[j].m not in ('sll','srl','sra'): return None
        sh=(L[j].m, L[j].sa); j=_producer(L, j, L[j].rt)
        msk=None
        if j is not None and L[j].m=='andi' and L[j].imm in (0xff,0xffff): msk=L[j].imm; j=_producer(L, j, L[j].rs)
        j=_origin(L, j) if j is not None else None
        if j is None or L[j].m not in ('lhu','lbu','lh','lb','lw'): return None
        pl=_producer(L, j, L[j].rs)
        if pl is None or L[pl].m!='lui' or L[pl].imm!=0x7000 or not (0x1124<=L[j].imm<=0x1140): return None
        w=32 if L[j].m=='lw' else (16 if L[j].m in ('lh','lhu') else 8)   # (HANDOFF §88) ROL.L #4 du score
        if msk is not None and msk!=(1<<w)-1: return None
        if msk is None and L[j].m in ('lh','lb'): return None     # il faut la valeur non signee
        if w==32 and msk is not None: return None
        parts.append((sh, (L[j].imm-0x1124)//4, w))
    (s1,d1,w1),(s2,d2,w2)=parts
    if d1!=d2 or w1!=w2: return None
    sh={s1[0]:s1[1]} ; sh.update({s2[0]:s2[1]})
    right=sh.get('srl', sh.get('sra')); left=sh.get('sll')
    if right is None or left is None or right+left!=w1: return None
    sz={32:'L',16:'W',8:'B'}[w1]
    if sz=='L' and min(right,left)>8: return None
    return (d1, sz, 'ror', right) if right<=8 else (d1, sz, 'rol', left)
def lui_only(L, i, r):
    """valeur 32 bits chargee par un 'lui' SEUL (ex. vitesse 16.16 $FFFC0000). Adresse
    (RAM/video/donnees) -> Sym 'const' (convertie par la carte), sinon immediat."""
    j=_producer(L, i, r, 10)
    if j is None or L[j].m!='lui' or L[j].imm==0x7000: return None
    v=(L[j].imm<<16)&0xffffffff
    if addr_to_68k(v) is not None or 0x1f0000<=v<(RAM_HI<<16): return Sym('const',v)
    return Sym('imm',v)
def is_code_ptr(v):
    """adresse d'execution d'un DEBUT DE FONCTION du module (pointeur de code a relocaliser)"""
    s=_CODE_STARTS.get('set')
    return s is not None and v in s
_CODE_STARTS={}
CODE_CONV=None     # {n: entree 'convertir An'} : adresses de code PS2 laissees telles quelles, converties a l'usage
def enc_dynbit(op, dn, tgt):
    """BTST/BCHG/BCLR/BSET Dn,<ea> (numero de bit dans un registre)"""
    base={'btst':0x0100,'bchg':0x0140,'bclr':0x0180,'bset':0x01c0}[op]|((dn&7)<<9)
    if tgt[0]=='D': return [base|(tgt[1]&7)], "%s D%d,D%d"%(op.upper(),dn,tgt[1])
    _,sz,disp,an=tgt
    return [base|0x28|(an&7), disp&0xffff], "%s D%d,$%04x(A%d)"%(op.upper(),dn,disp,an)
def abs_words(a): return [(a>>16)&0xffff, a&0xffff]

def carry_block(L, i):
    """Apres 'sw RES' d'une soustraction, le recompilateur calcule la RETENUE :
    sltu at,x,y ; beq at,zero,+28 ; nop ; addiu r,zero,-1 ; sw r,C ; beq zero,zero,+16 ;
    nop ; sw zero,C. Ces deux branchements sont INTERNES (pas des Bcc 68K).
    Rend les adresses des deux 'beq' a absorber, ou None."""
    for j in range(i+1, min(len(L), i+14)):
        x=L[j]
        if x.m in ('sltu','slt') and j+1<len(L) and L[j+1].m=='beq' and L[j+1].rs==x.rd and L[j+1].rt==0:
            for k in range(j+2, min(len(L), j+8)):
                if L[k].m=='beq' and L[k].rs==0 and L[k].rt==0: return (L[j+1].va, L[k].va)
            return None
        if x.m in ('jal','jalr','jr','beq','bne','bltz','bgez','bgtz','blez'): return None
    return None
def enc_tst_an(size, n, disp): return [0x4a00 | ({'B':0,'W':1,'L':2}[size]<<6) | 0x28 | (n&7), disp&0xffff]
def enc_tst_dn(size, n):       return [0x4a00 | ({'B':0,'W':1,'L':2}[size]<<6) | (n&7)]
# arithmetique registre-registre : <base> | dst<<9 | taille<<6 | src
ARITH = {'addu':0xd000, 'subu':0x9000, 'and':0xc000, 'or':0x8000, 'xor':0xb100}
ARITH_NAME = {'addu':'ADD','subu':'SUB','and':'AND','or':'OR','xor':'EOR'}
def enc_arith(kind, size, dst, src):
    if kind=='xor':     # (HANDOFF §80) EOR Dn,<ea> : le champ registre est la SOURCE (EOR.L D2,D4 = $B584, pas $B982)
        return [ARITH[kind] | ((src&7)<<9) | ({'B':0,'W':1,'L':2}[size]<<6) | (dst&7)]
    return [ARITH[kind] | (dst<<9) | ({'B':0,'W':1,'L':2}[size]<<6) | (src&7)]
RTS = 0x4e75
def enc_jsr_abs(addr): return [0x4eb9, (addr>>16)&0xffff, addr&0xffff]
def enc_jmp_abs(addr): return [0x4ef9, (addr>>16)&0xffff, addr&0xffff]

def tail_branch(L, i):
    """variante : l'appel est suivi d'un saut inconditionnel ('beq zero,zero') vers
    l'EPILOGUE commun de la fonction ('ld ra ; addiu sp ; jr ra'). C'est aussi un
    appel terminal (16 % des appels). Rend l'adresse du saut a absorber, ou None.
    Le 'jr ra' de l'epilogue, lui, reste un RTS : d'autres chemins y aboutissent."""
    j=i+2
    while j < len(L) and L[j].m=='sll' and L[j].w==0: j+=1
    if j>=len(L): return None
    y=L[j]
    if not (y.m=='beq' and y.rs==0 and y.rt==0): return None
    t=y.va+4+y.simm*4
    for k in range(j, min(len(L), j+400)):
        if L[k].va==t:
            q=k
            while q<len(L) and q<k+6:
                x=L[q]
                if (x.m=='sll' and x.w==0) or (x.m=='ld' and x.rt==31) or \
                   (x.m=='addiu' and x.rs==29 and x.rt==29): q+=1; continue
                return y.va if (x.m=='jr' and x.rs==31) else None
            return None
    return None

def tail_return(L, i):
    """L[i] est un appel (jal/jalr). Si l'appel est IMMEDIATEMENT suivi du retour de
    la fonction (delay slot, puis 'ld ra ; addiu sp,+X ; jr ra' dans un ordre
    quelconque, nop ignores), c'est un APPEL TERMINAL : en 68K, un JMP.
    Mesure dans la ROM : JMP = 5 559 contre 55 'JSR/BSR ; RTS' => JMP a 99 %.
    Rend l'adresse du 'jr ra' a ne PAS traduire en RTS, ou None.

    NB : semantiquement, un appel terminal est un GOTO. Selon la position de la
    cible dans la disposition de sortie, le 68K d'origine avait un JMP (37 % mesures),
    un BRA court (45 %) ou RIEN (18 %, la routine enchaine sur la suivante). Ce choix
    d'encodage releve de l'ASSEMBLEUR (assemble.py), pas du traducteur : on emet JMP."""
    j=i+2; seen_ld=seen_sp=False
    while j < len(L) and j < i+8:
        x=L[j]
        if x.m=='sll' and x.w==0: j+=1; continue
        if x.m=='ld' and x.rt==31: seen_ld=True; j+=1; continue
        if x.m=='addiu' and x.rs==29 and x.rt==29 and x.simm>0: seen_sp=True; j+=1; continue
        if x.m=='jr' and x.rs==31:
            # le delay slot du jr ra peut porter l'addiu sp
            if not seen_sp and j+1<len(L) and L[j+1].m=='addiu' and L[j+1].rs==29: seen_sp=True
            return x.va if seen_ld and seen_sp else None
        return None
    return None

# offset_fichier = adresse_execution - RUNTIME_BASE
# = base de chargement ecrite dans l'EN-TETE du module (mot 2 = 0x1f0000).
# CORRIGE le 2026-09-26 : la valeur 0x1f0008 utilisee jusque-la etait FAUSSE de 8
# octets. Elle faisait tomber chaque cible de 'jal' sur les 2 'nop' d'alignement
# qui precedent la fonction (les fonctions sont alignees sur 16 octets). Mesure sur
# les 10 824 appels : cible = prologue 'addiu sp,sp,-X' dans 65 a 89 % des cas avec
# 0x1f0000, dans 0 % des cas avec 0x1f0008.
RUNTIME_BASE = 0x1f0000
_PTS=None
def _load_map():
    """charge les POINTS d'ancrage (pas seulement les bornes de blocs).

    Interpoler lineairement d'un bout a l'autre d'un bloc est FAUX : le taux
    d'expansion varie localement (une instruction 68K se recompile en 2 a 20
    instructions MIPS selon l'operation). La verification par opcodes l'a montre :
    aux POINTS d'ancrage l'identite est forte, a une position interpolee sur tout
    un bloc elle retombe au niveau du bruit. On interpole donc PAR MORCEAUX, entre
    les deux points d'ancrage qui encadrent l'adresse demandee.
    """
    global _PTS
    if _PTS is not None: return _PTS
    import json, os, bisect
    d=os.path.dirname(os.path.abspath(__file__))
    pts=[]
    for name in ("map_chain2.json","map_ro3_sfa3.json"):
        f=os.path.join(d,name)
        if not os.path.exists(f): continue
        try: blocks=json.load(open(f))["blocks"]
        except Exception: continue
        for b in blocks:
            p=b.get("pts")
            if p: pts += [tuple(x) for x in p]
            else: pts += [tuple(b["mips"]+[]) and (b["mips"][0],b["m68k"][0]),
                          (b["mips"][1],b["m68k"][1])]
        if pts: break
    _PTS=sorted(set(pts))
    return _PTS

MAX_INTERP = 0x800        # au-dela, on ne pretend pas savoir (0x800 MIPS ~ 0x130 68K)
def mips_to_68k(va):
    """traduit une adresse MIPS en adresse 68K par interpolation PAR MORCEAUX."""
    import bisect
    pts=_load_map()
    if not pts: return None
    xs=[p[0] for p in pts]
    i=bisect.bisect_left(xs,va)
    if i<len(pts) and pts[i][0]==va: return pts[i][1] & ~1
    if i==0 or i>=len(pts): return None
    (m0,k0),(m1,k1)=pts[i-1],pts[i]
    if m1<=m0 or k1<=k0: return None
    if (va-m0)>MAX_INTERP and (m1-va)>MAX_INTERP: return None
    r=(m1-m0)/(k1-k0)
    if not (2.0<=r<=16.0): return None      # segment non plausible : on s'abstient
    return (k0 + round((va-m0)/r)) & ~1

# MOVE : destination = reg(bits 11-9) | mode(bits 8-6) ; (d16,An) => mode 5
#   A5 : (1<<12)|(5<<9)|(5<<6)|0x3c = 0x1b7c  (verifie contre la ROM)
def enc_move_imm_an(size, imm, n, disp):
    op = (SZ_TOP[size]<<12) | ((n&7)<<9) | (5<<6) | 0x3c
    if size == 'L':
        return [op, (imm>>16)&0xffff, imm&0xffff, disp&0xffff]
    return [op, imm&SZMASK[size], disp&0xffff]

def enc_move_dn_an(size, dn, n, disp):
    return [(SZ_TOP[size]<<12) | ((n&7)<<9) | (5<<6) | (dn&7), disp&0xffff]

def enc_move_imm_a5(size, imm, disp): return enc_move_imm_an(size, imm, 5, disp)
def enc_move_dn_a5(size, n, disp):    return enc_move_dn_an(size, n, 5, disp)

# operation immediate sur Dn : ORI/ANDI/SUBI/ADDI/EORI = base | taille<<6 | Dn
IMMOP = {'or':0x0000, 'and':0x0200, 'xor':0x0a00}
IMMOP_NAME = {'or':'ORI', 'and':'ANDI', 'xor':'EORI'}
def _imm_words(size, v):
    if size=='L': return [(v>>16)&0xffff, v&0xffff]
    if size=='B': return [v&0xff]
    return [v&0xffff]
def enc_immop_dn(kind, size, n, v):
    sz={'B':0,'W':1,'L':2}[size]
    return [IMMOP[kind] | (sz<<6) | (n&7)] + _imm_words(size, v)
def enc_addimm_dn(size, n, v):
    """ADDQ/SUBQ si |v| <= 8 (forme courte, celle d'un programmeur 68K), sinon ADDI."""
    sz={'B':0,'W':1,'L':2}[size]
    if 1 <= v <= 8:   return [0x5000 | ((v&7)<<9) | (sz<<6) | (n&7)], "ADDQ.%s #%d,D%d"%(size,v,n)
    if -8 <= v <= -1: return [0x5100 | (((-v)&7)<<9) | (sz<<6) | (n&7)], "SUBQ.%s #%d,D%d"%(size,-v,n)
    return [0x0600 | (sz<<6) | (n&7)] + _imm_words(size, v), "ADDI.%s #$%x,D%d"%(size,v&0xffffffff,n)
def enc_move_an_dn(size, an, disp, dn):
    """MOVE.x (d16,An),Dn : destination Dn = reg dn, mode 0 ; source (d16,An) = 0x28|an"""
    return [(SZ_TOP[size]<<12) | ((dn&7)<<9) | 0x28 | (an&7), disp&0xffff]

# Ecritures d'un registre d'ADRESSE (verifie contre la ROM : 3c6e 0038 = MOVEA.W $38(A6),A6)
def enc_movea_w_an(n, disp, m): return [0x3068 | ((m&7)<<9) | (n&7), disp&0xffff]
def enc_movea_l_an(n, m):       return [0x2048 | ((m&7)<<9) | (n&7)]
def enc_lea_an(n, disp, m):     return [0x41e8 | ((m&7)<<9) | (n&7), disp&0xffff]
def enc_adda_dn(size, dn, m):   return [(0xd0c0 if size=='W' else 0xd1c0) | ((m&7)<<9) | (dn&7)]
def enc_lea_index(n, dn, size, m):
    return [0x41f0 | ((m&7)<<9) | (n&7), ((dn&7)<<12) | (0x800 if size=='L' else 0)]
def enc_addq_an(v, m):
    # .W plutot que .L : meme effet sur un registre d'adresse, et c'est la forme que
    # prefere le code d'origine (ROM : ADDQ/SUBQ.W 132 contre .L 83)
    if 1 <= v <= 8:   return [0x5048 | ((v&7)<<9) | (m&7)], "ADDQ.W #%d,A%d"%(v,m)
    if -8 <= v <= -1: return [0x5148 | (((-v)&7)<<9) | (m&7)], "SUBQ.W #%d,A%d"%(-v,m)
    return enc_lea_an(m, v, m), "LEA $%04x(A%d),A%d"%(v&0xffff,m,m)

# Base de la RAM 68K emulee, PROPRE A CHAQUE MODULE (verifie par deux methodes : fin des
# donnees dans l'en-tete arrondie a 0x80000, et constante 'lui X ; addu' la plus frequente
# du code de conversion d'adresse) : SFA3 0x900000, Upper 0xa00000, Hyper 0xb80000.
# La memoire video CPS2 emulee suit : base + 0x10000 .. base + 0x4ffff.
RAM_HI = 0x90
_RAM_CACHE = {}

# ---------------------------------------------------------------------------
# MODE MEMOIRE (decision 2026-09-27, validee avec l'utilisateur)
#   'hote' : deplacements PS2 bruts (pour comparer a la ROM arcade : outils de validation)
#   'cps2' : RECETTE UNIVERSELLE, le 68K voit la memoire comme le code PS2 la voit :
#              mot  -> meme adresse ; octet -> adresse XOR 1 ;
#              long -> meme adresse, mais la valeur est rangee MOITIES ECHANGEES en memoire.
#            Principe : en memoire les longs sont echanges, dans les registres ils sont
#            justes ; on echange (SWAP) au passage memoire <-> registre. Une copie
#            memoire -> memoire ne demande donc rien.
#            Consequence : les donnees du module copiees dans la ROM de sortie doivent
#            avoir les octets de chaque mot de 16 bits inverses (LE16 -> BE16).
import os as _os
MEMMODE = _os.environ.get("MEMMODE", "hote")
EXTRA_REGS=_os.environ.get("EXTRA_REGS","1")=="1"      # A8/D8 -> registres pretes (HANDOFF §54)
TYPE_REGS={int(x) for x in _os.environ.get("TYPE_REGS","5,6").split(",")}   # bases typees (A6 objet, A5 globales)
TYPE_ACC=None              # mode 'type' : statistiques d'acces (registre, deplacement) du module
def mconv(disp, size, an=None):
    """deplacement hote -> deplacement 68K selon le mode.
    cps2 : octets XOR 1 (recette). type : MODELE TYPE (HANDOFF §44) - le deplacement 68K
    depend du type du champ (u8 / s16 / s32 / u8[4]) deduit des acces et des constantes."""
    if MEMMODE=='type' and an is not None and TYPE_ACC is not None and an in TYPE_REGS:
        import typed_rule
        return (disp + typed_rule.predict_typed(TYPE_ACC[1], an, size, disp)) & 0xffff
    return (disp ^ 1) & 0xffff if (MEMMODE=='cps2' and size=='B') else disp & 0xffff
def rev_field(an, disp):
    """mode 'type' : champ u8[4] (octets) lu/ecrit en long -> valeur MIPS = octets inverses"""
    if MEMMODE!='type' or TYPE_ACC is None or an not in TYPE_REGS: return False
    import typed_rule
    return typed_rule.long_type(TYPE_ACC[1], an, disp)=='u8x4'
def bs32(v): return int.from_bytes((v&0xffffffff).to_bytes(4,'little'),'big')
def type_const(an, disp, v):
    """mode 'type' : constante longue ecrite dans un champ u8[4] / s16[2] -> forme de la ROM"""
    if MEMMODE!='type' or TYPE_ACC is None or an not in TYPE_REGS: return v
    import typed_rule
    t=typed_rule.long_type(TYPE_ACC[1], an, disp)
    if t=='u8x4': return int.from_bytes(v.to_bytes(4,'little'),'big')
    if t=='s16x2': return ((v&0xffff)<<16)|(v>>16)
    return v
def swap32(v): return ((v & 0xffff) << 16) | ((v >> 16) & 0xffff)

# Carte des adresses PS2 -> CPS2 (a completer par l'apprentissage sur SFA3, addr_probe.py).
# Entrees : (debut PS2 relatif a la base RAM du module, fin, debut 68K). La RAM est connue :
# base RAM PS2 -> $FF0000.
ADDRMAP = [(0x00000, 0x10000, 0xff0000),     # RAM de travail : base RAM -> $FF0000
           (0x60000, 0x62000, 0x618000),     # memoire partagee QSOUND $618000-$619FFF (HANDOFF §57)
           (0x10000, 0x12000, 0x700000),     # memoire d'OBJETS page 1 ($700000) - HANDOFF §45 : lue par
           (0x12000, 0x14000, 0x708000),     #  le moteur de sprites natif via *(ctx+208) = base RAM+0x10000
           (0x20000, 0x50000, 0x900000)]     # memoire video CPS2 $900000-$92FFFF (appris sur SFA3 :
                                             #  90c360<->92c360 x22/x22, 90c380<->92c380 x19/x19...)
# Donnees du module : l'outil de portage a REORGANISE les tables une par une (decalages
# differents dans une meme zone) => on ne reutilise pas les adresses d'origine : les donnees
# sont copiees d'un bloc dans la ROM produite, a DATA_BASE (choisi a l'assemblage).
DATA_BASE = None
PORT_RAM = 0xF00000                    # RAM PROPRE AU FORK (zone libre de la CPS2) : variables du portage
# REGISTRES MATERIELS CPS2 que le portage a remplaces par ses variables (HANDOFF §57 : alignement de la
# routine de reset d'origine $91E sur sa version portee). Adresse hote (relative a la base RAM) -> CPS2.
HWREG = {0x62184:0x400002, 0x62186:0x400004, 0x62188:0x400006, 0x6218a:0x400008, 0x6218c:0x40000a,
         0x62198:0x804040, 0x6219a:0x8040a0, 0x621a0:0x8040e0,
         0x62146:0x804166, 0x62150:0x804170}
HWREG.update({0x62118+r: 0x80410c+r for r in range(0, 0x18, 2)})    # CPS-A : defilements, controle video (+$0C)
# ENTREES (HANDOFF §62 : routine d'entrees de la ROM $1460 <-> balayage vertical porte, memes destinations A5)
# (HANDOFF §80) CORRIGE : le portage range le MOT d'entree en petit-boutiste -> octet haut (pieces/Start,
# bits 15-8) en +1 : paires CROISEES (relevees par role : ROM $1482.. contre mips 0x83B3C..). Le portage
# fait lui-meme 'nor' la ou la ROM fait NOT (tout sauf $804010).
HWREG.update({0x62190:0x804001, 0x62191:0x804000, 0x62192:0x804011, 0x62193:0x804010,
              0x62194:0x804021, 0x62195:0x804020, 0x62196:0x804030})
# (HANDOFF §80) plus de NOT ajoute : il compensait le 'nor' du portage, que la traduction PERDAIT ; le 'nor'
# est maintenant traduit (NOT.B Dn), la lecture du vrai port reste brute
INPUT_INV = {}
BYTE_EXACT = {0x62190, 0x62191, 0x62192, 0x62193, 0x62194, 0x62195}   # releves octet a octet (pas de XOR 1)
# registres de base CPS-A (16 bits en $804100..$80410A) que le portage a ELARGIS a 32 bits (adresses hote)
WIDEREG = {0x62100+4*k: 0x804100+2*k for k in range(6)}
# (HANDOFF §138) base des objets CPS2 ($400000, arcade 'MOVE.W #$7000,$400000') elargie de meme par le portage
if __import__('os').environ.get('OBJBASE','1')!='0': WIDEREG[0x62180]=0x400000
# POINTEURS DU PORTAGE A L'EXECUTION (HANDOFF §63, banc MAME) : les donnees du module contiennent des
# pointeurs BRUTS (adresses d'execution PS2 : donnees 0x58xxxx.., RAM 0x90xxxx..), impossibles a reperer
# statiquement de facon sure (64 000 candidats, dont une large part de paires de s16). DPTR_FIX = {n:
# adresse d'une routine qui convertit An si sa valeur tombe dans une plage PS2} : appelee apres chaque
# MOVEA.L venant de la memoire ou d'un Dn. HW_TAG : nos adresses MATERIELLES CPS2 ($618000, $700000,
# $804000, $900000...) portent l'octet haut $01 (ignore par le bus 24 bits du 68000) pour ne jamais etre
# confondues avec une adresse PS2 de la meme plage. (Cible finale : plan memoire IDENTITE dans le fork.)
DPTR_FIX = {}
HW_TAG = False
def addr_to_68k(v):
    a = _addr_to_68k(v)
    if HW_TAG and a is not None and 0x400000 <= a < 0xF00000: a |= 0x01000000
    return a
# (agent_son_hyper_rom, SON-HYPER-ROM.md §13) BLOC DE DONNEES AJOUTE (redirection du son par version) : plage
# d'execution PS2 [SON_X, SON_X + SON_LEN) hors du module et de sa RAM, servie a la suite du bloc externe de fin des
# donnees (DATA_EXT + taille de ce bloc)
SON_X = None; SON_LEN = 0
def son_y():
    return (DATA_EXT + (DATA_END_RT - DATA_SPLIT) + 1) & ~1
def _addr_to_68k(v):
    if SON_X is not None and DATA_SPLIT is not None and SON_X <= v < SON_X + SON_LEN: return son_y() + (v - SON_X)
    rel = v - (RAM_HI<<16)
    if MEMMODE in ('cps2','type') and rel in HWREG: return HWREG[rel]   # rendu au vrai registre CPS2
    for a0,a1,k in ADDRMAP:
        if a0 <= rel < a1: return k + (rel - a0)
    if DATA_BASE is not None and DATA_SPLIT is not None and DATA_SPLIT <= v < DATA_END_RT:
        return DATA_EXT + (v - DATA_SPLIT)                   # (HANDOFF §108) fin des donnees -> bloc externe
    if DATA_BASE is not None and CODE_END_RT <= v < DATA_END_RT:
        return DATA_BASE + (v - CODE_END_RT)                 # donnees du module -> ROM
    if DATA_BASE is not None and DATA_END_RT <= v < (RAM_HI<<16):
        return PORT_RAM + (v - DATA_END_RT)                  # variables du portage sous la RAM ($88xxxx)
    if DATA_BASE is not None and 0x50000 <= rel < 0x80000:
        return PORT_RAM + 0x80000 + (rel - 0x50000)          # variables du portage apres la video ($96xxxx)
    return None
DATA_SPLIT = None                      # (HANDOFF §108) donnees au-dela : bloc externe (programme CPS2 limite a 4 Mo)
DATA_EXT = 0xC80000
CODE_END_RT = 0x1f0000 + 0x393c40      # debut des donnees (fin du code) ; relu dans l'en-tete du module
DATA_END_RT = 0x88c700                 # fin des donnees (mot 6 de l'en-tete) ; relu par module
def code_end_translate(buf):
    """fin de code a TRADUIRE : l'en-tete (+12) peut couper la derniere fonction (ro3 : delai de
    branchement, 'ld ra', 'addiu sp', 'jr ra' au-dela, HANDOFF §76) -> jusqu'au 'jr ra' qui suit + delai"""
    import struct as _st
    e=_st.unpack_from('<I',buf,12)[0]
    for o in range(e, e+0x20, 4):
        if _st.unpack_from('<I',buf,o)[0]==0x03e00008: return o+8
    return e

def set_module_bounds(buf):
    global CODE_END_RT, DATA_END_RT
    import struct as _st
    CODE_END_RT = 0x1f0000 + _st.unpack_from('<I',buf,12)[0]
    DATA_END_RT = _st.unpack_from('<I',buf,24)[0]
SWAP_OP = 0x4840          # SWAP Dn

def btst_target(size, disp, bit):
    """BTST sur la memoire agit sur un OCTET. Pour un bit d'un MOT lu en h (meme adresse
    68K dans les deux modes) : bit >= 8 -> octet h, bit-8 ; bit < 8 -> octet h+1.
    (Auparavant : BTST #b,h avec b jusqu'a 15, ce qui testait le mauvais octet.)"""
    if size=='W':
        return (disp, bit-8) if bit >= 8 else ((disp+1)&0xffff, bit)
    return (disp, bit)

def inplace_long(kind, an, disp, src):
    """operation EN PLACE sur un long en memoire, mode cps2 (valeur rangee echangee) :
      MOVE.L Dt,-(SP) ; MOVE.L d(An),Dt ; SWAP Dt ; <op>,Dt ; MOVE SR,-(SP) ; SWAP Dt ;
      MOVE.L Dt,d(An) ; MOVE (SP)+,CCR ; MOVEM.L (SP)+,Dt
    Les indicateurs poses par l'operation sont PRESERVES (SWAP et MOVE les ecraseraient ;
    MOVEM ne touche pas aux indicateurs). kind : addu/subu/and/or/xor (src=('D',n))
    ou 'add' (src=('imm',v)). Rend (mots, mnemonique)."""
    dn = src[1] if src[0]=='D' else -1
    dt = 6 if dn==7 else 7                              # registre temporaire != source
    w=[0x2f00|dt]                                       # MOVE.L Dt,-(SP)
    w+=[0x2028|(dt<<9)|(an&7), disp&0xffff]             # MOVE.L d(An),Dt
    w+=[SWAP_OP|dt]
    if kind=='neg':
        w+=[0x4480|dt]; opm="NEG.L D%d"%dt
    elif kind.startswith('logic_'):
        k=kind[6:]; v=src[1]&0xffffffff
        w+=[{'or':0x0080,'and':0x0280,'xor':0x0a80}[k]|dt,(v>>16)&0xffff,v&0xffff]
        opm="%s.L #$%x,D%d"%({'or':'ORI','and':'ANDI','xor':'EORI'}[k],v,dt)
    elif src[0]=='D':
        base={'addu':0xd080,'subu':0x9080,'and':0xc080,'or':0x8080}.get(kind)
        if base is not None: w+=[base|(dt<<9)|(dn&7)]; nm={'addu':'ADD','subu':'SUB','and':'AND','or':'OR'}[kind]
        else: w+=[0xb180|((dn&7)<<9)|dt]; nm='EOR'      # EOR.L Dn,Dt
        opm="%s.L D%d,D%d"%(nm,dn,dt)
    else:
        v=src[1]
        if 1<=v<=8:   w+=[0x5080|((v&7)<<9)|dt]; opm="ADDQ.L #%d,D%d"%(v,dt)
        elif -8<=v<=-1: w+=[0x5180|(((-v)&7)<<9)|dt]; opm="SUBQ.L #%d,D%d"%(-v,dt)
        else: w+=[0x0680|dt,(v>>16)&0xffff,v&0xffff]; opm="ADDI.L #$%x,D%d"%(v&0xffffffff,dt)
    w+=[0x40e7]                                         # MOVE SR,-(SP)
    w+=[SWAP_OP|dt]
    w+=[0x2000|((an&7)<<9)|(5<<6)|dt, disp&0xffff]     # MOVE.L Dt,d(An)
    w+=[0x44df]                                         # MOVE (SP)+,CCR
    w+=[0x4cdf, 1<<dt]                                  # MOVEM.L (SP)+,Dt
    return w, "[long echange] %s sur $%04x(A%d) via D%d"%(opm,disp,an,dt)

def ram_hi_of(buf):
    import struct
    key=bytes(buf[:32])
    if key not in _RAM_CACHE:
        end=struct.unpack_from('<I',buf,24)[0] if buf[:4]==b'MWo3' else 0x88c700
        _RAM_CACHE[key]=((end+0x7ffff)&~0x7ffff)>>16
    return _RAM_CACHE[key]

def movea_fixup(L, i, m_slot):
    """Apres 'sw zext16 -> slot Am' (MOVEA.W), le recompilateur CONVERTIT l'adresse
    68K en adresse hote : si le mot est negatif (0x8000..0xffff = RAM 68K 0xFFxxxx),
    Am += 0x900000.   lh Am ; dsll32 ; dsra32 ; bgez +32 ; nop ; lw Am ; lui 0x90 ;
    addu ; sw Am   (les 'lui 0x7000' sont ignores). Ce code n'a PAS de contrepartie
    68K. Rend les adresses (bgez, sw final) a absorber, ou None."""
    want=[('lh',m_slot),('dsll32',None),('dsra32',None),('bgez',None),('sll',None),
          ('lw',m_slot),('lui',RAM_HI),('addu',None),('sw',m_slot)]
    k=0; j=i+1; bg=None
    while j < len(L) and j < i+20 and k < len(want):
        x=L[j]
        if x.m=='lui' and x.imm==0x7000: j+=1; continue
        mm,arg=want[k]
        if x.m!=mm: return None
        if arg is not None and mm in ('lh','lw','sw') and x.imm!=arg: return None
        if mm=='lui' and x.imm!=arg: return None
        if mm=='bgez': bg=x.va
        k+=1; j+=1
    return (bg, L[j-1].va) if k==len(want) else None

# registre de DESTINATION d'une instruction MIPS (pour invalider l'etat suivi)
_DEST_RT = {'lb','lh','lw','lbu','lhu','ld','lwu','addiu','daddiu','andi','ori','xori',
            'lui','slti','sltiu','lq'}
_DEST_RD = {'addu','subu','daddu','dsubu','and','or','xor','nor','slt','sltu','sll','srl',
            'sra','sllv','srlv','srav','dsll','dsrl','dsra','dsll32','dsrl32','dsra32',
            'movz','movn','mfhi','mflo'}
def dest_reg(ins):
    if ins.m in _DEST_RT: return ins.rt
    if ins.m in _DEST_RD: return ins.rd
    return None
_SHIFT_KEEP = ('dsll32','dsra32','sll','sra')

class Sym:
    """valeur symbolique d'un registre MIPS"""
    __slots__=('kind','val','sz')
    def __init__(s,k,v=None,sz=None): s.kind=k; s.val=v; s.sz=sz      # 'imm' | 'an'((n,disp)) | 'reg68'(('D',n)) | None
    def __repr__(s): return "Sym(%s,%r,%s)"%(s.kind,s.val,s.sz)

_XPLAN={}
def extra_zones(buf):
    """zones ou A8/D8 recoivent un registre 68K prete (extra_regs.plan), triees par debut"""
    key=id(buf)
    if key not in _XPLAN:
        import extra_regs
        p,_=extra_regs.plan(buf)
        _XPLAN[key]=sorted((lo,hi,slot,kind,reg) for zs in p.values() for (kind,reg,slot,lo,hi) in zs)
    return _XPLAN[key]
_EMPTY={}
def empty_funcs(buf):
    """debuts de fonction dont le corps se reduit a 'jr ra' (cf. emptied.py), par module"""
    key=id(buf)
    if key not in _EMPTY:
        import struct as _st
        from mips import decode as _dec
        end=_st.unpack_from('<I',buf,12)[0]
        c0=0x22de0 if end==0x3bf140 else 0x22b00
        starts={x.tgt-RUNTIME_BASE for x in _dec(buf,c0,end) if x.m=='jal'}
        E=set()
        for s0 in starts:
            if not (c0<=s0<end): continue
            ins=[x for x in _dec(buf,s0,s0+0x20) if not (x.m=='sll' and x.w==0)]
            body=[x for x in ins[:6] if not (x.rs==29 and x.m in ('addiu','sd','ld','sw','lw'))]
            if body and body[0].m=='jr' and body[0].rs==31: E.add(s0)
        _EMPTY[key]=E
    return _EMPTY[key]
FTC_CTX={}
def an_slots(n):
    """cases MIPS qui designent le registre 68K An : la sienne, et celle de A8 s'il lui est prete (HANDOFF §80)"""
    return {0x1100+4*n} | ({0x1120} if ACTIVE_EXTRA.get(0x1120)==('A',n) else set())

CONST_OP=__import__('os').environ.get('CONST_OP','1')!='0'   # (HANDOFF §126)
# (greffe_arcade, etape 4) PILE_LUI=1 : une valeur LUE EN MEMOIRE rangee sur la pile MIPS n'est pas prise pour la constante
# d'un 'lui' perime du meme registre. Cas : 'lui v1,0x7000 ; lw a0,A5(v1) ; lh a0,$138(a0) ; dsll32/dsra32 v1,a0 ;
# sw v1,408(sp)' (v1 garde lui 0x7000 dans la table) -> CMPI.W #6,$138(A5) devenait CMP #$70000000,#6 et n'etait pas
# emis : le BEQ suivant lisait les drapeaux de l'appelant (Upper 0x269340, temporaires de pile des fonctions a
# prologue 'sq'). PILE_LUI=0 : ancien comportement.
PILE_LUI=__import__('os').environ.get('PILE_LUI','1')!='0'; PILE_LUI_N=[0]
EXACT_MISS=[]   # (HANDOFF §126) blocs exacts sans operande : (va, taille, dst?, src?)
TBLBYTE_ON=__import__('os').environ.get('TBLBYTE','1')!='0'; TBLBYTE_N=[0]   # (HANDOFF §137)
MEMSHL_ON=__import__('os').environ.get('MEMSHL','1')!='0'; MEMSHL_N=[0]   # (HANDOFF §137)
IDXRMW_ON=__import__('os').environ.get('IDXRMW','1')!='0'; IDXRMW_N=[0]
CDISP_ON=__import__('os').environ.get('CDISP','1')!='0'; CDISP_N=[0]   # (HANDOFF §140) aiguilleurs C du portage   # (HANDOFF §138) RMW octet/mot indexe
SHIFT_MR_FIX=__import__('os').environ.get('SHIFT_MR','1')!='0'; SHIFT_MR_N=[0]   # (HANDOFF §137)
ANDAND_ON=__import__('os').environ.get('ANDAND','1')!='0'   # (HANDOFF §137)
SPILL_Q=__import__('os').environ.get('SPILL_Q','1')!='0'   # (HANDOFF §137)
TBLMASK_ON=__import__('os').environ.get('TBLMASK','1')!='0'; TBLMASK_N=[0]   # (HANDOFF §132)
BIGSHIFT_ON=__import__('os').environ.get('BIGSHIFT','1')!='0'; BIGSHIFT_N=[0]; ABSEXT_ON=__import__('os').environ.get('ABSEXT','1')!='0'; ABSEXT_N=[0]   # (HANDOFF §132)
TBLMEM_ON=__import__('os').environ.get('TBLMEM','1')!='0'; TBLMEM_N=[0]   # (HANDOFF §132)
D8HI_ON=__import__('os').environ.get('D8HI','1')!='0'; D8HI_N=[0]   # (HANDOFF §132)
ROT_ON=__import__('os').environ.get('ROT','1')!='0'; ROT_N=[0]   # (HANDOFF §132)
LOGIC_ZERO=__import__('os').environ.get('LOGIC_ZERO','1')!='0'; LOGIC_ZERO_N=[0]   # (HANDOFF §132)
TBLOP_ON=__import__('os').environ.get('TBLOP','1')!='0'; TBLOP_N=[0]   # (HANDOFF §132)
MEMSHIFT_ON=__import__('os').environ.get('MEMSHIFT','1')!='0'; MEMSHIFT_N=[0]   # (HANDOFF §132)
MEMSHIFT_GARDE=__import__('os').environ.get('MEMSHIFT_GARDE','0')=='1'   # (HANDOFF §137) ancien mot haut garde (faux ici)
MULS_ON=__import__('os').environ.get('MULS','1')!='0'; MULS_N=[0]   # (HANDOFF §132)
EXT_MEM=__import__('os').environ.get('EXT_MEM','1')!='0'; EXT_MEM_N=[0]   # (HANDOFF §128)
LUI_IMM=__import__('os').environ.get('LUI_IMM','1')!='0'; LUI_IMM_N=[0]   # (HANDOFF §126)
SW_X4=__import__('os').environ.get('SW_X4','1')!='0'; SW_X4_N=[0]   # (HANDOFF §126)
EXG_PILE=__import__('os').environ.get('EXG_PILE','1')!='0'; EXG_PILE_N=[0]   # (HANDOFF §126)
# (agent_defauts_banc, EXG_PILE_D) meme echange par la pile MIPS entre deux registres D : 'tmp = D2 ; D2 = D3 ;
# D3 = tmp' (SFA3 mips 0x2597E8, EXG D2,D3 de la visee du Killer Bee Assault de Cammy, arcade $05DB2C) rendu
# 'MOVE.L D3,D2 ; MOVE.L D2,D3' : D3 gardait sa valeur -> mauvais octant, vitesse nulle, super arrete (etat $16)
EXG_PILE_D=__import__('os').environ.get('EXG_PILE_D','1')!='0'; EXG_PILE_D_N=set()
BITOP_DN=__import__('os').environ.get('BITOP_DN','1')!='0'; BITOP_DN_N=set()   # (agent_defauts_banc)
CMPDMEM=__import__('os').environ.get('CMPDMEM','1')!='0'; CMPDMEM_N=set()   # (agent_defauts_banc / banc_coups)
TBL_TST=__import__('os').environ.get('TBL_TST','1')!='0'; TBL_TST_N=[0]   # (HANDOFF §126)
FTC_AVANT=__import__('os').environ.get('FTC_AVANT','1')!='0'; FTC_AVANT_N=[0]   # (HANDOFF §126)
# (agent_coups) saut terminal ('jal ; beq zero,zero -> epilogue') absorbe par un JMP, mais CIBLE d'un autre branchement
# ('BEQ fin ... BSR x ; fin: RTS') : il doit rester un RTS, sinon le branchement tombe sur l'instruction emise suivante
# (super boule d'Akuma : 'TST.B $35 ; BEQ rts' devenu 'BEQ JMP $2BAF2', fin du coup avant le lancer). TAILBR=0 : ancien.
TAILBR=__import__('os').environ.get('TAILBR','1')!='0'; TAILBR_N=[0]
# (agent_coups) constante 'lui' SEULE rangee dans Dn puis utilisee comme VALEUR (BTST Dk,Dn ; ASR ; ADD...) : la prendre
# pour une adresse PS2 la convertissait (masque de types $800000 -> $3103C0 / $296340 : boules de Sakura a 42 coups dans
# Upper ; plafond de vitesse $900000 -> $FF0000). LUIDN=0 : ancien comportement.
LUIDN=__import__('os').environ.get('LUIDN','1')!='0'; LUIDN_LOG=[]
CMPMM=__import__('os').environ.get('CMPMM','1')!='0'; CMPMM_N=[]
# (agent_defauts_banc, RETAG24) POINTEUR ETIQUETE REMASQUE SUR 24 BITS : le jeu range un octet de drapeaux dans
# l'octet fort d'un pointeur (MOVE.L ptr,(A1) ; MOVE.B drapeau,(A1)) puis l'isole par ANDI.L #$00FFFFFF. Dans la
# traduction l'octet fort d'une adresse 68K hors ROM porte l'etiquette $01 (HW_TAG, talon CONV $400) : le masque
# l'efface, et une adresse 68K du bloc externe des donnees retombe dans la plage PS2 que CONV convertit (Hyper :
# fantomes des supers des versions ZERO / ZERO 2 / ALPHA, animations en $94xxxx-$9Exxxx -> instruction illegale).
# Apres le masque, si la valeur tombe dans un bloc 68K etiquete ET dans la plage convertie, on remet l'etiquette.
# RETAG_FN (pose par mame_test) rend les plages [lo, hi) concernees ; vide (SFA3, Upper) -> rien d'emis.
RETAG24=__import__('os').environ.get('RETAG24','1')!='0'; RETAG_FN=None; RETAG24_N=set()
def retag_seq(n, plages):
    """MOVE SR,-(SP) ; pour chaque plage : CMPI.L #lo,Dn ; BCS.S suiv ; CMPI.L #hi,Dn ; BCC.S suiv ;
    ORI.L #$01000000,Dn ; BRA.S fin ; suiv: ... ; fin: MOVE (SP)+,CCR (drapeaux du ANDI gardes)"""
    blocs=[]
    for k,(lo,hi) in enumerate(plages):
        der = k==len(plages)-1
        b=[0x0c80|n,lo>>16,lo&0xffff, 0x6500, 0x0c80|n,hi>>16,hi&0xffff, 0x6400, 0x0080|n,0x0100,0x0000]
        if not der: b+=[0x6000]
        blocs.append(b)
    ws=[0x40e7]
    for k,b in enumerate(blocs):
        reste=sum(len(x) for x in blocs[k+1:])
        b=list(b)
        # BCS.S / BCC.S -> bloc suivant (fin du bloc courant) ; BRA.S -> fin (apres les blocs suivants)
        b[3]=0x6500|((2*(len(b)-4))&0xff); b[7]=0x6400|((2*(len(b)-8))&0xff)
        if len(b)==12: b[11]=0x6000|((2*reste)&0xff)
        ws+=b
    return ws+[0x44df]
CMPX=__import__('os').environ.get('CMPX','0')=='1'; CMPX_N=[]   # (agent_hyper_defauts) essai, voir enc_cmp   # (agent_hyper_defauts) CMP memoire-memoire
_LDST=('lb','lbu','lh','lhu','lw','lwl','lwr','ld','lq','sb','sh','sw','swl','swr','sd','sq')
_ARITH=('sra','srl','sll','srav','srlv','sllv','and','or','xor','nor','addu','subu','daddu','dsubu','slt','sltu',
        'andi','ori','xori','addiu','slti','sltiu','mult','multu','dsra','dsrl','dsll','dsra32','dsrl32','dsll32')
def lui_dn_usage(L, i, slot):
    """(agent_coups) premier usage de la case Dn ecrite par L[i] : 'val' (arithmetique / test de bit), 'addr' (base d'un
    acces memoire, copie vers An, appel), ou None (inconnu : ecrasee, appel, fenetre depassee)."""
    for j in range(i+1, min(len(L), i+40)):
        x=L[j]
        if x.m in ('jal','jalr','jr'): return None
        if x.m in ('sw','sd','sq') and (x.imm & 0xffff)==slot: return None
        if x.m=='lw' and (x.imm & 0xffff)==slot:
            r=x.rt
            for k in range(j+1, min(len(L), j+7)):
                y=L[k]
                if y.m in _LDST and y.rs==r: return 'addr'
                if y.m=='sw' and y.rt==r:
                    nm=slot_name(y.imm & 0xffff)
                    return 'addr' if (nm and nm[0]=='A') else None
                if y.m in ('jalr','jr') and y.rs==r: return 'addr'
                if y.m in _ARITH and r in (getattr(y,'rs',None), getattr(y,'rt',None)):
                    if y.m in ('addu','daddu','addiu'):        # base + index : adresse si le resultat sert de base
                        d=dest_reg(y)
                        for q in range(k+1, min(len(L), k+4)):
                            if L[q].m in _LDST and L[q].rs==d: return 'addr'
                    return 'val'
                if dest_reg(y)==r: return None
            return None
    return None

LATERAL_REW=[0]; LATERAL_OK_VA=set()
def rot_idiom(L, i):
    """(HANDOFF §132) ROTATION 16 bits du 68K decomposee : 'sh y,Dk' avec y = ((Dk >> Dn) | (Dk << (16 - Dn))) & $FFFF
    (ROR.W Dn,Dk) ou ((Dk << Dn) | (Dk >> (16 - Dn))) (ROL.W). Lecture arriere sur 24 instructions. Rend (sens, k, n)."""
    x=L[i]
    if x.m!='sh': return None
    def prod(r, j):
        for t in range(j-1, max(-1, j-24), -1):
            y=L[t]
            if dest_reg(y)==r or (y.m in ('sllv','srlv','srav') and y.rd==r): return t
        return None
    def slot_of(r, j):                                     # registre r = 'lhu/lh Dslot' (+ andi 0xffff) -> numero D
        t=prod(r, j)
        if t is None: return None
        y=L[t]
        if y.m=='andi' and y.imm==0xffff: return slot_of(y.rs, t)
        if y.m in ('lhu','lh') and 0x1124<=(y.simm&0xffff)<=0x1140 and (y.simm-0x1124)%4==0: return (y.simm-0x1124)//4
        return None
    t=prod(x.rt, i)
    if t is None: return None
    if L[t].m=='andi' and L[t].imm==0xffff: t=prod(L[t].rs, t)
    if t is None or L[t].m!='or': return None
    o=L[t]; parts=[]
    for r in (o.rs, o.rt):
        u=prod(r, t)
        if u is None or L[u].m not in ('sllv','srlv','srav'): return None
        parts.append(u)
    sh={L[u].m=='sllv': u for u in parts}
    if set(sh)!={True,False}: return None
    ul, ur = sh[True], sh[False]                           # gauche, droite ; 'sllv rd,rs,rt' : rd = rt << rs
    kl, kr = slot_of(L[ul].rt, ul), slot_of(L[ur].rt, ur)
    if kl is None or kl!=kr or kl!=(x.simm-0x1124)//4: return None
    # le compte d'un cote = Dn, de l'autre = 16 - Dn (addiu c,zero,16 ; subu c,c,Dn)
    def cnt(r, j):
        n=slot_of(r, j)
        if n is not None: return ('n', n)
        t2=prod(r, j)
        if t2 is not None and L[t2].m=='subu':
            t3=prod(L[t2].rs, t2)
            if t3 is not None and L[t3].m=='addiu' and L[t3].rs==0 and L[t3].simm==16:
                n2=slot_of(L[t2].rt, t2)
                if n2 is not None: return ('16-', n2)
        return None
    cl, cr = cnt(L[ul].rs, ul), cnt(L[ur].rs, ur)
    if not cl or not cr or cl[1]!=cr[1]: return None
    if cr[0]=='n' and cl[0]=='16-': return ('ROR', kl, cr[1])
    if cl[0]=='n' and cr[0]=='16-': return ('ROL', kl, cl[1])
    return None

def _zone_restore_ws(slot,kind,reg):
    """(HANDOFF §130) restauration d'une zone A8/D8 (meme sequence que la fermeture normale, drapeaux preserves)"""
    ws=[0x201f|(reg<<9)] if kind=='D' else [0x205f|(reg<<9)]
    if slot==0x1120 and A8_HOME is not None:
        H=A8_HOME&0xffff
        ws=[0x40e7, 0x2f08|reg, 0x3b5f, (H+2)&0xffff, 0x3b5f, H, 0x44df, 0x205f|(reg<<9)]
    if slot==0x1144 and D8_HOME is not None:
        ws=[0x40e7, SWAP_OP|reg, 0x2b40|(reg&7), D8_HOME&0xffff, 0x202d|((reg&7)<<9), (D8_HOME+8)&0xffff, 0x44df]
    return ws

def flags_to_caller(i, pend, pend_va, absorbed, out):
    """(HANDOFF §66, §80) DRAPEAUX RENDUS A L'APPELANT : le test en attente (dernier RES ecrit avant le
    retour) est emis devant le RTS -- ou devant un BRA qui mene directement a l'epilogue. True si emis."""
    ins_list=FTC_CTX['ins_list']; ins=ins_list[i]
    if pend and pend[0] in ('tst_mem','tst_dn','tst_idx','tst_abs','cmp','btst','btst_dn','btst_dyn') and pend_va is not None:
        k=i-1; last_res=None
        while k>=0 and k>=i-40:
            y=ins_list[k]
            # (HANDOFF §76) les branchements INTERNES du calcul de retenue (absorbes) ne coupent pas
            # la recherche : 'MOVE.B $2C9(A6),D0 ; CMP.B $B(A6),D0 ; RTS' (ROM $2AAB2) perdait son CMP
            if y.m in ('jal','jalr','jr') or (y.m in _BRANCHES and y.va not in absorbed): break
            if y.m=='sw' and (y.simm & 0xffff)==RES_SLOT: last_res=y.va; break
            k-=1
        # (HANDOFF §114) drapeaux EXACTS (recompilateur recent, Upper/Hyper) : la derniere ecriture de RES est
        # celle du bloc (apres 'RES = -RES' si V), loin du 'subu' ou le test a ete pose -> acceptee aussi
        # (Upper mips 0x23B520 : 'MOVE.B $2C8(A6),D0 ; CMP.B $A(A6),D0 ; RTS' perdait son CMP -> recursion sans fin)
        kp=FTC_CTX.get('keep_pend',())
        if last_res is not None and ((last_res<=pend_va+8 and last_res>=pend_va-8) or (pend[0]=='cmp' and last_res in kp)):
            if pend[0]=='tst_mem':
                _,sz,disp,an=pend; out.append((ins.va,"TST.%s $%04x(A%d)  [drapeaux rendus a l'appelant]"%(sz,disp,an),enc_tst_an(sz,an,disp)))
            elif pend[0]=='tst_dn':
                _,sz,dn=pend; out.append((ins.va,"TST.%s D%d  [drapeaux rendus a l'appelant]"%(sz,dn),enc_tst_dn(sz,dn)))
            elif pend[0]=='tst_abs':
                _,sz,host=pend; a_,note=abs_addr(host,sz)
                out.append((ins.va,"TST.%s $%06x.L  [drapeaux rendus a l'appelant]"%(sz,a_&0xffffff),[0x4a00|(SZN[sz]<<6)|0x39]+abs_words(a_)))
            elif pend[0]=='tst_idx':
                _,sz,n,dn,dsz,d8=pend
                out.append((ins.va,"TST.%s %d(A%d,D%d.%s)  [drapeaux rendus a l'appelant]"%(sz,d8,n,dn,dsz),
                            [0x4a00|(SZN[sz]<<6)|0x30|(n&7), idx_ext(dn,dsz,d8)]))
            elif pend[0]=='btst':
                # (HANDOFF §87) BTST rendu a l'appelant : petite fonction du portage 'lb ; andi bit ; sw RES ; jr ra'
                # (0x57A4B0 : bit 4 de $C1A4(A5), condition du remplissage de la jauge de super en debut de combat)
                _,bb,bd,ban=pend; out.append((ins.va,"BTST #%d,$%04x(A%d)  [drapeaux rendus a l'appelant]"%(bb,bd&0xffff,ban),enc_btst_an(bb,ban,bd)))
            elif pend[0]=='btst_dn':
                # (HANDOFF §93) 'MOVE.W $378(A6),D0 ; BTST #15,D0 ; RTS' (ROM $2E0CC, nouvel appui sur Start =
                # provocation) : le BTST etait perdu, tout nouvel appui declenchait la provocation
                _,bit,dn=pend; out.append((ins.va,"BTST #%d,D%d  [drapeaux rendus a l'appelant]"%(bit,dn),[0x0800|(dn&7), bit]))
            elif pend[0]=='btst_dyn':
                # (HANDOFF §125) BTST Dn,<ea> a bit DYNAMIQUE rendu a l'appelant : test du masque des adversaires battus
                # d'Upper (mips 0x251CC0 : 'CMPI.B #$20,D1 ; BCC ; BTST D1,D2 | BTST D1,D3 ; RTS') -> le mode Arcade
                # allait droit a Bison (la boucle de 0x250FB8 relisait des drapeaux perimes)
                _,dn,tgt=pend; ws_,mn_=enc_dynbit('btst',dn,tgt); out.append((ins.va,mn_+"  [drapeaux rendus a l'appelant]",ws_))
            elif pend[0]=='cmp':
                r=enc_cmp(pend[3],pend[1],pend[2])
                if r: out.append((ins.va,r[1]+"  [drapeaux rendus a l'appelant]",r[0]))
            return True
    return False

def translate(buf, start, end, verbose=False):
    global RAM_HI, TYPE_ACC
    RAM_HI = ram_hi_of(buf)
    set_module_bounds(buf)
    if _CODE_STARTS.get('id')!=id(buf):
        import struct as _st
        from mips import decode as _dec
        _e=_st.unpack_from('<I',buf,12)[0]; _c0=0x22de0 if _e==0x3bf140 else 0x22b00
        # debuts de fonction = PROLOGUES 'addiu sp,sp,-16 ; sd ra,0(sp)' (y compris les fonctions jamais
        # appelees par jal, seulement par pointeur : entrees de taches, routines d'etat...)
        _L=list(_dec(buf,_c0,_e)); _S=set()
        for _k in range(len(_L)-1):
            _x=_L[_k]
            if _x.m=='addiu' and _x.rs==29 and _x.rt==29 and _x.simm<0 and _L[_k+1].m=='sd' and _L[_k+1].rt==31:
                _S.add(_x.va+RUNTIME_BASE)
        _CODE_STARTS['set']=_S
        _CODE_STARTS['id']=id(buf)
    if MEMMODE=='type' and (TYPE_ACC is None or TYPE_ACC[0]!=id(buf)):
        from layout_rule import access_stats
        TYPE_ACC=(id(buf), access_stats(buf))
    
    st={}                      # registre MIPS -> Sym
    global REG68
    REG68={}                   # ('D',n)/('A',n) -> Sym (valeur courante)
    memread={}                 # registre MIPS -> ('mem', size, disp)  lecture [A5+disp]
    pend=None                  # test en attente : ('btst', bit, disp)
    lui={}                     # registre MIPS -> valeur lui
    out=[]                     # (va_mips, mnemonique, [mots 68K])
    unknown=0
    no_rts=set()               # 'jr ra' qui terminent un appel terminal (-> JMP)
    no_rts_ind=set()           # 'jr ra' qui terminent un JMP indirect (table de sauts)
    absorbed=set()             # 'beq zero,zero' vers l'epilogue, absorbes par un JMP
    tail_abs=set()             # (agent_coups) parmi eux : ceux des appels terminaux (tail_branch)
    ldsize={}                  # registre MIPS -> taille du chargement de slot (B/W/L)
    idxread={}                 # registre MIPS -> lecture indexee (taille, An, Dn, taille Dn, d8)
    idxbig={}                  # (HANDOFF §78) idem, deplacement 16 bits : (taille, An, Dn, taille Dn, d16 MIPS)
    spill={}                   # deplacement sur la pile MIPS -> valeur symbolique rangee
    absread={}                 # registre MIPS -> lecture a adresse ABSOLUE (taille, adresse hote)
    moved=None                 # derniere lecture memoire deplacee par un MOVE (flags deja poses)
    flags_obj=None; flags_len=-1; moved_obj=None; moved_mlen=-1
    moved_d=None; moved_len=-1 # dernier registre source d'un MOVE registre->registre (s'il est la derniere emission)
    flags_set=None             # derniere arithmetique en place (flags deja poses)
    last_sub=None              # derniere operation Dn emise (ses drapeaux sont poses)
    arith_written=None; arith_len=0   # dernier ADDQ/SUBQ/ADDI (Dn, op, valeur) emis vers son propre Dn
    keep_pend=set()            # 'sw RES' internes a un bloc de drapeaux exacts
    revd=set()                 # mode type : registres D contenant une valeur u8[4] INVERSEE
    signed_res=set()           # 'sw RES' suivis d'une correction V (RES porte N^V : comparaisons signees)
    exact_blk=None             # (debut, fin, dst, src, taille) du dernier bloc exact
    ins_list=hautes_moities(slot_ori(unaligned_pairs(list(decode(buf,start,end)))))
    pend_obj=None; pend_va=None; ccr_restore=False; N_BTST_CONFLIT[0]+=0
    ins_vas=[x.va for x in ins_list]
    FTC_CTX['ins_list']=ins_list; FTC_CTX['keep_pend']=keep_pend
    br_targets={x.va+4+x.simm*4 for x in ins_list if x.m in _BRANCHES}   # BRA compris (HANDOFF §66)
    ZONES=[z for z in extra_zones(buf) if z[1]>=start and z[0]<end] if EXTRA_REGS else []
    priv=private_stack(ins_list)                 # empiler/depiler sur la pile privee 0x114C (HANDOFF §72)
    xrestore=None
    zopen=[]                   # zones ouvertes (lo,hi,slot,kind,reg)
    ACTIVE_EXTRA.clear()
    i=0
    while i < len(ins_list):
        ins=ins_list[i]; m=ins.m; _n0=len(out)
        if m=='swapd':                                 # (HANDOFF §82) moitie haute d'un registre D
            out.append((ins.va,"SWAP D%d  [moitie haute du registre]"%ins.rt,[0x4840|(ins.rt&7)])); i+=1; continue
        if DBG_RANGE and DBG_RANGE[0]<=ins.va<DBG_RANGE[1]:
            print('DBG %07x %-6s rt=%d pend=%s st_rt=%s abs=%s'%(ins.va,m,ins.rt,pend,st.get(ins.rt),absread.get(ins.rt)))
        if m=='lw' and (ins.simm & 0xffff)==X_SLOT:
            ax=addx_at(ins_list, i)
            if ax:
                sn,dk,k=ax
                out.append((ins.va,"ADDX.L D%d,D%d"%(sn,dk),[0xd180|((dk&7)<<9)|(sn&7)]))
                REG68[('D',dk)]=None; pend=None; i=k; continue
        if arith_written is not None and len(out)!=arith_len: arith_written=None   # autre instruction emise
        if moved_d is not None and len(out)!=moved_len: moved_d=None   # (HANDOFF §80) idem : MOVE Dx,Dy perime
        # (HANDOFF §80) idem pour « drapeaux deja poses par l'operation en place » : valable tant que rien d'autre
        # n'est emis (sinon le souvenir d'une autre fonction supprimait le TST.B $A(A6) de l'ecran VS, mips 0x14EBB8)
        if moved is not moved_obj: moved_obj=moved; moved_mlen=len(out)      # (HANDOFF §80) lecture deplacee :
        elif moved is not None and len(out)!=moved_mlen: moved=None; moved_obj=None   # valable jusqu'a la suivante
        if flags_set is not flags_obj: flags_obj=flags_set; flags_len=len(out)
        elif flags_set is not None and len(out)!=flags_len: flags_set=None; flags_obj=None
        # (HANDOFF §80) « drapeaux deja poses par l'operation en place » : faux apres une operation de BIT
        # (BSET/BCLR/BCHG ne posent pas N/Z sur l'octet) et a un point de jonction (le chemin qui saute
        # l'operation arrive sans ces drapeaux) : TST.B $A9(A5) de l'ecran-titre perdu
        if flags_set is not None and out and out[-1][1][:4] in ('BSET','BCLR','BCHG','BTST'): flags_set=None
        # (HANDOFF §80) ecriture dans la case d'un registre D ou A : les lectures indexees par lui (ou basees sur
        # lui) sont perimees
        if m in ('sb','sh','sw') and lui.get(ins.rs)==0x7000:
            _nm=slot_name(ins.simm & 0xffff)
            if _nm and _nm[0] in 'DA':
                for _d in (idxread, idxbig):
                    for _r in [r_ for r_,ix in _d.items() if (_nm[0]=='D' and ix[2]==_nm[1]) or (_nm[0]=='A' and ix[1]==_nm[1])]:
                        if _r!=ins.rt: _d.pop(_r,None)
        if ins.va in br_targets: flags_set=None
        if ccr_restore:                                # (HANDOFF §80) drapeaux du BTST en attente sauves avant l'ecriture
            out.append((ins_list[i-1].va,"MOVE (SP)+,CCR  [drapeaux du test anterieur a l'ecriture]",[0x46df])); ccr_restore=False
        if pend is not pend_obj: pend_obj=pend; pend_va=ins_list[i-1].va if i else None   # ou le test a ete pose
        # A8/D8 : fermeture (restauration) puis ouverture (sauvegarde) des zones de registre prete
        for z in list(zopen):
            if ins.va > z[1] and not (m=='sll' and ins.w==0):   # sur la 1re instruction UTILE (cible des sorties)
                lo,hi,slot,kind,reg=z
                import extra_regs as _xr
                cva=hi if (slot,lo) in _xr.EARLY_CLOSE else ins.va   # (HANDOFF §80) fermeture avant l'epilogue partage
                ws=[0x201f|(reg<<9)] if kind=='D' else [0x205f|(reg<<9)]
                if slot==0x1120 and A8_HOME is not None:     # (HANDOFF §80) valeur rendue au domicile de A8 (long
                    H=A8_HOME&0xffff                           # recette cps2 : mot bas en +0), drapeaux preserves
                    ws=[0x40e7, 0x2f08|reg, 0x3b5f, (H+2)&0xffff, 0x3b5f, H, 0x44df, 0x205f|(reg<<9)]
                if slot==0x1144 and D8_HOME is not None:     # (HANDOFF §72-73) valeur rendue au domicile de D8,
                    # registre prete restaure depuis sa sauvegarde FIXE (pas la pile : la pile privee s'y entrelace)
                    ws=[0x40e7, SWAP_OP|reg, 0x2b40|(reg&7), D8_HOME&0xffff,
                        0x202d|((reg&7)<<9), (D8_HOME+8)&0xffff, 0x44df]
                out.append((cva,"MOVE%s.L (SP)+,%s%d  [fin du registre prete a %s]"%("" if kind=='D' else "A",kind,reg,
                            "A8" if slot==0x1120 else "D8"),ws))
                if slot==0x1144 and D8_HOME is not None and pend:
                    # (HANDOFF §73) test en attente sur le registre prete : il porte desormais sur le domicile
                    def _home(o, sz):
                        if o==('D',reg): return ('mem', sz, (D8_HOME ^ (1 if sz=='B' else 0)) & 0xffff, 5)
                        return o
                    if pend[0]=='cmp' and pend[3] in ('B','W'):
                        pend=(pend[0], _home(pend[1],pend[3]), _home(pend[2],pend[3]))+tuple(pend[3:])
                    elif pend[0]=='tst_dn' and pend[2]==reg and pend[1] in ('B','W'):
                        pend=('tst_mem', pend[1], (D8_HOME ^ (1 if pend[1]=='B' else 0)) & 0xffff, 5)
                zopen.remove(z); ACTIVE_EXTRA.pop(slot,None)
        for z in ZONES:
            if z[0]==ins.va and z not in zopen:
                lo,hi,slot,kind,reg=z
                ws=[0x2f00|reg] if kind=='D' else [0x2f08|reg]
                if slot==0x1120 and A8_HOME is not None:     # (HANDOFF §80) sauvegarde (MOVEM : drapeaux intacts)
                    H=A8_HOME&0xffff                           # + chargement depuis le domicile de A8
                    ws=[0x48e7, 1<<(7-reg), 0x40e7, 0x3f2d, H, 0x3f2d, (H+2)&0xffff, 0x205f|(reg<<9), 0x44df]
                    ZONE_OPEN[lo]=hi
                if slot==0x1144 and D8_HOME is not None:     # (HANDOFF §72-73) sauvegarde FIXE + chargement
                    ws=[0x40e7, 0x2b40|(reg&7), (D8_HOME+8)&0xffff,
                        0x202d|((reg&7)<<9), D8_HOME&0xffff, SWAP_OP|reg, 0x44df]
                out.append((ins.va,"MOVE.L %s%d,-(SP)  [%s <- %s%d prete]"%(kind,reg,"A8" if slot==0x1120 else "D8",kind,reg),ws))
                zopen.append(z); ACTIVE_EXTRA[slot]=(kind,reg)
        # INVALIDATION : un registre ecrase ne porte plus la lecture memoire qu'il
        # portait (sinon on emettrait de faux MOVE (d16,An),Dn). Les decalages
        # d'extension de signe, eux, PROPAGENT la lecture a leur destination.
        # INSTANTANE des informations des SOURCES, pris AVANT d'invalider la
        # destination : quand destination == source ('andi v1,v1,0xff', tres frequent),
        # l'invalidation effacait l'information avant que le traitement ne la lise.
        SM={ins.rs:memread.get(ins.rs), ins.rt:memread.get(ins.rt)}
        SAB={ins.rs:absread.get(ins.rs), ins.rt:absread.get(ins.rt)}    # (HANDOFF §78) idem pour l'absolu
        SL={ins.rs:ldsize.get(ins.rs), ins.rt:ldsize.get(ins.rt)}
        SI={ins.rs:idxread.get(ins.rs), ins.rt:idxread.get(ins.rt)}
        d=dest_reg(ins)
        # (HANDOFF §137) un 'sll/sra' n'est une extension de signe que de 16 ou 24 : sinon il ne conserve rien
        _keep_ok = m in ('dsll32','dsra32') or (m in ('sll','sra') and (ins.sa in (16,24) or not SHIFT_MR_FIX))
        if d and not (m in _SHIFT_KEEP and _keep_ok): ldsize.pop(d,None)
        if d:
            keepa = absread.get(ins.rt) if (m in _SHIFT_KEEP and _keep_ok) else None
            absread.pop(d,None)
            if keepa: absread[d]=keepa
            keepi = idxread.get(ins.rt) if (m in _SHIFT_KEEP and _keep_ok) else None
            idxread.pop(d,None); idxbig.pop(d,None)
            if keepi: idxread[d]=keepi
            keep = memread.get(ins.rt) if (m in _SHIFT_KEEP and _keep_ok) else None
            memread.pop(d,None)
            if keep: memread[d]=keep
        if m in ('jal','jalr'): flags_set=None   # (HANDOFF §66) un appel ecrase aussi les drapeaux
        if m in ('jal','jalr'):                  # un appel ecrase v0/v1 (valeurs de retour)
            # (st[v0] est lu par le traitement du jalr : il est efface APRES, pas ici)
            for r in (2,3): memread.pop(r,None)
        if m=='lui':
            lui[ins.rt]=ins.imm; st[ins.rt]=None; i+=1; continue
        if m=='sll' and ins.w==0: i+=1; continue          # nop
        # RESULTAT NATIF DU PORTAGE (HANDOFF §65) : 'jal f ; beq/bne v0,zero' teste la valeur rendue par
        # une fonction PS2 (le code 68K traduit ne rend JAMAIS de valeur dans v0). Le portage y a greffe
        # des attentes (ex. mode C de l'attraction : 'moteur occupe ?' -> on reessaie a l'image
        # suivante). Comportement arcade = pas d'attente : v0 suppose NUL (beq -> BRA, bne -> rien).
        if m in ('beq','bne') and {ins.rs,ins.rt}=={2,0}:
            k=i-1; prod=None
            while k>=0 and k>=i-4:
                y=ins_list[k]
                if y.m in ('jal','jalr'): prod=y; break
                if dest_reg(y)==2: break
                k-=1
            if prod is not None:
                tgt=ins.va+4+ins.simm*4
                if m=='beq': out.append((ins.va,"BRA (cible %08x)  [resultat natif du portage suppose nul]"%tgt,[0x6000]))
                else: out.append((ins.va,"(test d'un resultat natif du portage, suppose nul : pas de saut)",[]))
                i+=1; continue
        if xrestore is not None:                 # base remise a 0x7000 apres un acces au domicile de D8
            r_,st_old=xrestore; xrestore=None
            if r_ not in lui and st.get(r_) is not None and st[r_].kind=='an' and st[r_].val==(5,0):
                lui[r_]=0x7000; st[r_]=st_old
        if ins.va in priv:
            act=priv[ins.va]
            if act=='skip': i+=1; continue
            kind,off=act
            nm=slot_name(off)
            if nm and nm[0] in 'AD' and nm[1]<=7:
                n=nm[1]; isA=nm[0]=='A'
                if kind=='push': ws=[0x2f08|n] if isA else [0x2f00|n]; mn="MOVE.L %s%d,-(SP)"%(nm[0],n)
                else: ws=[0x205f|(n<<9)] if isA else [0x201f|(n<<9)]; mn="MOVE%s.L (SP)+,%s%d"%("A" if isA else "",nm[0],n)
            elif off==0x1144 and D8_HOME is not None:
                # (HANDOFF §77) le domicile est un long a moities echangees (recette cps2 : mot bas en +0) ;
                # la pile transporte des VALEURS REELLES (registres) -> mot a mot, dans le bon ordre
                H=D8_HOME&0xffff
                if kind=='push': ws=[0x3f2d, H, 0x3f2d, (H+2)&0xffff]; mn="MOVE.W $%04x(A5),-(SP) ; MOVE.W $%04x(A5),-(SP)  [D8 reel]"%(H,(H+2)&0xffff)
                else: ws=[0x3b5f, (H+2)&0xffff, 0x3b5f, H]; mn="MOVE.W (SP)+,$%04x(A5) ; MOVE.W (SP)+,$%04x(A5)  [D8 reel]"%((H+2)&0xffff,H)
            else: ws=None
            if ws:
                out.append((ins.va,mn+"  [pile privee 0x114C -> pile 68K]",ws)); i+=1; continue
        if (D8HI_ON and m in ('lh','lhu') and lui.get(ins.rs)==0x7000 and (ins.simm & 0xffff)==0x1146
                and 0x1144 in ACTIVE_EXTRA and ACTIVE_EXTRA[0x1144][0]=='D'):
            # (HANDOFF §132) MOT HAUT de D8 prete (case 0x1146) : le domicile est perime dans la zone (D8 recharge depuis
            # la pile, SFA3 mips 0x101800) -> valeur symbolique « mot haut du registre prete »
            st[ins.rt]=Sym('dhi',ACTIVE_EXTRA[0x1144][1]); lui.pop(ins.rt,None); memread.pop(ins.rt,None); i+=1; continue
        if (D8_HOME is not None and m in ('lb','lbu','lh','lhu','lw','sb','sh','sw') and lui.get(ins.rs)==0x7000
                and 0x1144<=(ins.simm & 0xffff)<0x1148 and (ins.simm & 0xffff) not in ACTIVE_EXTRA):
            # D8 SANS REGISTRE PRETE -> variable (d16,A5) : la base devient A5 pour cette instruction
            from mips import Ins
            d=(D8_HOME+((ins.simm & 0xffff)-0x1144)) & 0xffff
            w=(ins.w & 0xffff0000) | d
            ins=Ins(ins.va,w); ins_list[i]=ins; m=ins.m
            xrestore=(ins.rs, st.get(ins.rs))
            lui.pop(ins.rs,None); st[ins.rs]=Sym('an',(5,0))
            SM={ins.rs:memread.get(ins.rs), ins.rt:memread.get(ins.rt)}
            SL={ins.rs:ldsize.get(ins.rs), ins.rt:ldsize.get(ins.rt)}
            SI={ins.rs:idxread.get(ins.rs), ins.rt:idxread.get(ins.rt)}
        # EXTENSION DE SIGNE EN PLACE (HANDOFF §67) : 'lb r,Dk ; dsll32/dsra32 24 ; sh r,Dk' = EXT.W Dk ;
        # 'lh r,Dk ; (16) ; sw r,Dk' = EXT.L Dk ; 'lb r,Dk ; (24) ; sw r,Dk' = EXT.W + EXT.L. N'etait pas
        # traduit (ROM $F3DA0 : MOVE.B $3(A6),D1 ; EXT.W D1 ; LSL.W #2,D1 -> octet haut perime dans l'index).
        if m in ('sh','sw') and lui.get(ins.rs)==0x7000 and slot_name(ins.simm & 0xffff) and slot_name(ins.simm & 0xffff)[0]=='D':
            r=sign_ext_inplace(ins_list, i)
            if r is not None:
                k=slot_name(ins.simm & 0xffff)[1]
                if r=='W': ws=[0x4880|k]; mn="EXT.W D%d"%k
                elif r=='L': ws=[0x48c0|k]; mn="EXT.L D%d"%k
                else: ws=[0x4880|k,0x48c0|k]; mn="EXT.W D%d ; EXT.L D%d"%(k,k)
                out.append((ins.va,mn,ws)); st.pop(ins.rt,None); i+=1; continue
        # LEA T(PC,Dn.W),Am SUR UNE TABLE DE DONNEES (HANDOFF §65) : addu r,sext16(Dn),T ; sw r,Am.
        # Etait perdu (Am gardait une valeur perimee : ex. table des reglages par region -> A0).
        if m=='sw' and lui.get(ins.rs)==0x7000 and slot_name(ins.simm & 0xffff) and slot_name(ins.simm & 0xffff)[0]=='A':
            r=lea_table_index(ins_list, i)
            if r is not None:
                const,dk=r; n=slot_name(ins.simm & 0xffff)[1]; a68=addr_to_68k(const)
                out.append((ins.va,"LEA $%06x.L,A%d ; ADDA.W D%d,A%d  [LEA T_%06x(PC,D%d.W),A%d]"%(a68&0xffffff,n,dk,n,const,dk,n),
                            [0x41f9|((n&7)<<9),(a68>>16)&0xffff,a68&0xffff, 0xd0c0|((n&7)<<9)|dk]))
                i+=1; continue
        # REALIGNEMENT DU PORTAGE (HANDOFF §63) : lw r,Rn ; addiu r2,r,3 ; addiu r3,zero,-4 ; and r4,r2,r3 ;
        # sw r4,Rn = Rn <- (Rn+3) & ~3. Le portage a aligne sur 4 octets les longs de ses tableaux de
        # donnees et realigne le pointeur avant chaque lecture longue ; nos donnees sont CELLES du portage,
        # il faut donc garder ce realignement (absent du 68K d'origine). Les drapeaux sont preserves.
        if m=='lw' and lui.get(ins.rs)==0x7000 and slot_name(ins.simm & 0xffff):
            seq=[]; k=i+1
            while k<len(ins_list) and len(seq)<4:
                y=ins_list[k]; k+=1
                if (y.m=='sll' and y.w==0) or (y.m=='lui' and y.imm==0x7000): continue
                seq.append(y)
            if (len(seq)==4 and seq[0].m=='addiu' and seq[0].rs==ins.rt and seq[0].simm==3
                and seq[1].m=='addiu' and seq[1].rs==0 and seq[1].simm==-4 and seq[2].m=='and'
                and {seq[2].rs,seq[2].rt}=={seq[0].rt,seq[1].rt} and seq[3].m=='sw'
                and seq[3].rt==seq[2].rd and (seq[3].simm & 0xffff)==(ins.simm & 0xffff)):
                kind,n=slot_name(ins.simm & 0xffff)
                if kind=='D': ws=[0x40e7,0x5680|n,0x0200|n,0x00fc,0x44df]
                else:
                    x=0xc188|(n&7); ws=[0x40e7,x,0x5680,0x0200,0x00fc,x,0x44df]
                out.append((ins.va,"[realignement du portage] %s%d <- (%s%d+3) & ~3"%(kind,n,kind,n),ws))
                for y in seq: st.pop(y.rt,None); lui.pop(y.rt,None)
                st.pop(ins.rt,None); lui[seq[3].rs]=0x7000
                i=k; continue
        # TEMPORAIRES SUR LA PILE MIPS : quand une fonction manipule trop de valeurs, le
        # recompilateur les range sur SA pile (sw rX,off(sp)) puis les relit. Ce ne sont pas des
        # acces 68K : on fait suivre la valeur symbolique, pour que tous les idiomes voient au
        # travers (ex. CMPI.B #$10,D1 dont les operandes passent par 284(sp) et 280(sp)).
        def _spill_an(r_, j_, am_):
            # (HANDOFF §126) ECHANGE PAR LA PILE MIPS : 'tmp = A1 ; A1 = A6 ; A6 = tmp' (Upper mips 0x3BBD8, EXG A1,A6
            # autour de l'appel de 0x2486B0) : la valeur de la 2e ecriture est relue d'un temporaire qui contenait Am
            if not EXG_PILE: return False
            for y_ in ins_list[i+1:j_]:
                if y_.m=='lw' and y_.rs==29 and y_.rt==r_ and y_.simm in spill:
                    sy_=spill[y_.simm][0]
                    if sy_ and sy_.kind=='an' and sy_.val==(am_,0): EXG_PILE_N[0]+=1; return True
            return False
        # (HANDOFF §137) temporaires 64/128 bits du recompilateur ('sq v0,176(sp) ; lq v0,176(sp)', Hyper mips 0x969DC,
        # Upper 0x261CD4) : suivis comme les 32 bits (la valeur d'un operande de comparaison exacte etait perdue)
        if ins.rs==29 and m in (('sw','sh','sb','sd','sq') if SPILL_Q else ('sw','sh','sb')) and ins.rt not in (31,) :
            _sv=st.get(ins.rt)
            # (HANDOFF §126) constantes rangees sur la pile : 'sw zero' (= 0) et 'lui' seul (= imm<<16) perdaient leur
            # valeur -> operande d'un bloc exact inconnu (Upper mips 0x38B94 'CMPI.B #0', 0x10DE08 'CMPI.L #$20000')
            if _sv is None and CONST_OP and ins.rt==0: _sv=Sym('imm',0)
            elif _sv is None and CONST_OP and ins.rt in lui and not (CMPX and memread.get(ins.rt)) \
                 and not (PILE_LUI and (memread.get(ins.rt) or ldsize.get(ins.rt))): _sv=Sym('const',(lui[ins.rt]<<16)&0xffffffff)
            spill[ins.simm]=(_sv, memread.get(ins.rt), ldsize.get(ins.rt), idxread.get(ins.rt))
            i+=1; continue
        if ins.rs==29 and m in (('lw','lh','lb','lhu','lbu','ld','lq') if SPILL_Q else ('lw','lh','lb','lhu','lbu')) and ins.simm in spill:
            sy,mr,ls,ix=spill[ins.simm]
            st[ins.rt]=sy; lui.pop(ins.rt,None)
            if mr: memread[ins.rt]=mr
            if ls: ldsize[ins.rt]=ls
            if ix: idxread[ins.rt]=ix
            i+=1; continue
        # addiu rX, zero, imm  -> immediat (SIGNE, garde sur 32 bits : -1 = $FFFFFFFF ; CORRECTION,
        # il etait tronque a 16 bits et 'MOVE.L #-1' devenait 'MOVE.L #$0000FFFF')
        if m=='ori' and ins.rs==0:                        # ori rX,zero,imm : immediat NON signe
            st[ins.rt]=Sym('imm', ins.imm); lui.pop(ins.rt,None); i+=1; continue
        if m=='addiu' and ins.rs==0:
            st[ins.rt]=Sym('imm', ins.simm & 0xffffffff); lui.pop(ins.rt,None); i+=1; continue
        # addiu rX, rY, imm  ou rY = A5+k  ->  A5 + (k+imm)   [le recompilateur
        # calcule l'adresse dans le registre au lieu d'utiliser le deplacement]
        if m=='addiu':
            b=st.get(ins.rs)
            # (HANDOFF §138) 'lb x,d(An+Dn) ; addiu x,x,k ; sb x,d(An+Dn)' = ADDQ/ADDI en place indexe
            # (SFA3 arcade $0232F8 'ADDQ.B #1,(A0,D0.W)' perdu)
            if IDXRMW_ON and b is None and SI.get(ins.rs) and SI[ins.rs][0] in ('B','W') and _idx_rmw_store(ins_list,i,ins.rt):
                st[ins.rt]=Sym('idxrmw',('add',ins.simm,SI[ins.rs])); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='an':
                n,d=b.val
                st[ins.rt]=Sym('an', (n,(d + ins.simm) & 0xffff)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='reg68' and b.val and b.val[0]=='D':
                st[ins.rt]=Sym('arithi',('add', b.val[1], ins.simm), SL.get(ins.rs)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='an_d':                     # An + Dn + decalage
                v=b.val+(0,)
                st[ins.rt]=Sym('an_d',(v[0],v[1],v[2],v[3]+ins.simm)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='const':                    # adresse constante + decalage
                st[ins.rt]=Sym('const',(b.val+ins.simm)&0xffffffff); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='tblidx':                   # table + index + decalage : entree voisine
                tbl,ix,scale=b.val                        # (ROM : 2d7b 001a ... puis 2d7b 0018 ...)
                st[ins.rt]=Sym('tblidx',((tbl+ins.simm)&0xffffffff,ix,scale)); lui.pop(ins.rt,None); i+=1; continue
            if SM.get(ins.rs) and not (b and b.kind=='zx'):  # valeur lue en memoire + imm
                st[ins.rt]=Sym('memadd',(SM[ins.rs], ins.simm)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='zx':                   # dst - imm (CMPI/SUBI/SUBQ)
                base,szz=b.val
                st[ins.rt]=Sym('sub',(base,('imm',(-ins.simm) & SZMASK[szz]),szz)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='sub' and b.val[1] and b.val[1][0]=='imm' and ins.rt==ins.rs:
                # (HANDOFF §80) immediat trop grand pour un addiu, decoupe en deux : 'addiu -$8000 ; addiu -$7FFF'
                # = CMPI.W #$FFFF,(A3) (fin de la liste de sprites, mips 0x101B2C : faute d'adresse sinon)
                base,(_,k),szz=b.val
                st[ins.rt]=Sym('sub',(base,('imm',(k-ins.simm) & SZMASK[szz]),szz)); lui.pop(ins.rt,None); i+=1; continue
            if ins.rs in lui:                        # lui+addiu = adresse constante
                st[ins.rt]=Sym('const', ((lui[ins.rs]<<16) + ins.simm) & 0xffffffff)
                lui.pop(ins.rt,None); i+=1; continue
            st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
        # lw rX, 0x1114(rY) avec lui rY,0x7000 -> rX = A5
        if m=='lw' and lui.get(ins.rs)==0x7000 and ins.imm in (RES_SLOT, NFLG_SLOT):
            st[ins.rt]=Sym('flag', 'Z' if ins.imm==RES_SLOT else 'C')
            lui.pop(ins.rt,None); i+=1; continue
        if m=='lw' and lui.get(ins.rs)==0x7000:
            nm=slot_name(ins.imm)
            if nm and nm[0]=='A' and nm[1]<7: st[ins.rt]=Sym('an', (nm[1],0))
            else: st[ins.rt]=Sym('reg68', nm) if nm else None
            ldsize[ins.rt]='L'
            lui.pop(ins.rt,None); i+=1; continue
        if m in ('lb','lh','lbu','lhu') and lui.get(ins.rs)==0x7000:
            nm=slot_name(ins.imm)
            st[ins.rt]=Sym('reg68', nm) if nm else None
            ldsize[ins.rt]='B' if m in ('lb','lbu') else 'W'
            lui.pop(ins.rt,None); i+=1; continue
        # ecriture d'une valeur dans un slot de registre 68K : on suit la valeur
        # sw rX, RES : positionne Z/N. Si la valeur n'a ete que LUE (memoire ou Dn)
        # sans etre deplacee, le 68K avait un TST ; si elle a deja ete deplacee (MOVE
        # emis), c'est le MOVE qui a positionne les drapeaux : rien a ajouter.
        if m=='sw' and lui.get(ins.rs)==0x7000 and ins.imm==RES_SLOT and ins.va in keep_pend:
            i+=1; continue
        if m=='sw' and lui.get(ins.rs)==0x7000 and ins.imm==RES_SLOT:
            if pend is None or pend[0]!='btst':
                mr=memread.get(ins.rt); sy=st.get(ins.rt)
                if mr and flags_set is not None and flags_set==('mem',mr[2],mr[1],mr[0]):
                    pend=None                                  # l'operation en place a pose les drapeaux
                    cb=carry_block(ins_list, i)
                    if cb: absorbed.update(cb)
                elif absread.get(ins.rt) and sy is None and (pend is None or pend[0]!='btst'):
                    pend=('tst_abs',)+absread[ins.rt]
                elif idxread.get(ins.rt) and sy is None:
                    pend=('tst_idx',)+idxread[ins.rt]               # (taille, An, Dn, taille Dn, d8)
                elif sy and sy.kind in ('sub','dmem','memarith') and last_sub is not None and sy.val==last_sub:
                    pend=None                                 # l'operation emise a pose les drapeaux
                    cb=carry_block(ins_list, i)
                    if cb: absorbed.update(cb)
                elif sy and sy.kind=='sub' and sy.val[1] is not None:
                    pend=('cmp',)+sy.val+((True,) if ins.va in signed_res else ())   # (dst, src, taille[, exact])
                    cb=carry_block(ins_list, i)
                    if cb: absorbed.update(cb)
                elif CMPDMEM and sy and sy.kind=='dmem' and sy.val[1]=='subu' and sy.val[2][0] in ('B','W','L'):
                    # (agent_defauts_banc / banc_coups, CMPDMEM) 'Dn - memoire' dont le resultat ne va QUE dans RES =
                    # CMP.x d(An),Dn : le symbole 'dmem' n'etait traite qu'emis (last_sub) -> CMP perdu, le branchement
                    # relisait des drapeaux perimes (SFA3 mips 0x128984, arcade $803F2 'CMP.L $44(A6),D0' : arcs bleus
                    # du Kikosho de Chun-Li, objet $FFBF00 tue a l'image 40)
                    pend=('cmp',('D',sy.val[0]),('mem',)+tuple(sy.val[2]),sy.val[2][0])+((True,) if ins.va in signed_res else ())
                    CMPDMEM_N.add(ins.va)
                    cb=carry_block(ins_list, i)
                    if cb: absorbed.update(cb)
                elif mr and mr!=moved:
                    pend=('tst_mem',)+mr                      # (sz,disp,an)
                elif sy and sy.kind=='arithi' and sy.val[0]=='and' and sy.val[2] and (sy.val[2]&(sy.val[2]-1))==0:
                    pend=('btst_dn', sy.val[2].bit_length()-1, sy.val[1])     # BTST #b,Dn
                elif sy and sy.kind in ('neg','shift','scaled') and last_sub is not None:
                    pend=None                                  # NEG / decalage ont pose les drapeaux
                elif sy and sy.kind in ('memadd','memarith'):
                    pend=None                                  # l'ADDQ/SUBQ en place a pose les drapeaux
                    cb=carry_block(ins_list, i)
                    if cb: absorbed.update(cb)
                elif sy and sy.kind=='reg68' and sy.val and sy.val[0]=='D' and ldsize.get(ins.rt) \
                     and moved_d!=('D',sy.val[1]):
                    pend=('tst_dn', ldsize[ins.rt], sy.val[1])
                elif sy and sy.kind=='dynbit' and sy.val[0]=='btst':
                    pend=('btst_dyn',)+sy.val[1:]                  # (dn, cible)
                elif TBL_TST and sy and sy.kind=='tblval' and sy.val[2] in ('B','W') and not any(
                        y.m in ('sw','sh','sb') and 0x1100<=(y.simm & 0xffff)<RES_SLOT for y in ins_list[max(0,i-12):i]):
                    # (aucune ecriture de registre 68K depuis la lecture : sinon 'D0 = T[D0]' a deja pose les drapeaux
                    #  ET change l'index -> relire T[D0] plantait SFA3, mips 0x187BE8)
                    # (HANDOFF §126) valeur de TABLE seulement testee (Upper mips 0x25063C : 'si T[D8+$50] = 0', liste
                    # des decors de SURVIVAL) : rien n'etait emis, le BNE lisait des drapeaux perimes. TST d(PC,Xn)
                    # n'existe pas sur 68000 -> registre de passage sauve, MOVEM de restauration (drapeaux intacts)
                    _tb,_ix,_sz=sy.val; _k=0 if _ix!=0 else 1
                    # trois entrees : l'assembleur reconnait la lecture de table (hebergee apres elle) a son 1er mot
                    out.append((ins.va,"MOVE.L D%d,-(SP)  [test d'une valeur de table]"%_k,[0x2f00|_k]))
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D%d.W),D%d"%(_sz,_tb,_ix,_k),enc_move_pcidx(_sz,_ix,('D',_k))))
                    out.append((ins.va,"MOVEM.L (SP)+,D%d  [drapeaux de la valeur gardes]"%_k,[0x4cdf,1<<_k]))
                    TBL_TST_N[0]+=1; pend=None
                elif sy and sy.kind=='dynbit':
                    pend=None                                      # BSET/BCLR/BCHG : Z = ancien bit
                elif sy and sy.kind=='memlogic' and out and out[-1][1][:4] in ('BSET','BCLR','BCHG'):
                    # (HANDOFF §92) RES = RESULTE de l'operation logique en place (ROM 'EORI.B #1,$B(A6) ; BEQ',
                    # $2861A, saut de mur de Chun-Li) ; l'operation de bit emise pose Z = ancien bit : TST.B
                    _k,_m,(_sz,_d,_an)=sy.val
                    pend=('tst_mem',_sz,_d,_an)
                elif sy and sy.kind=='arithi' and arith_written==(sy.val[1],sy.val[0],sy.val[2]):
                    # (HANDOFF §73) RES = la valeur deja RANGEE dans Dn par l'ADDQ/SUBQ emis : ses drapeaux
                    # suffisent (sinon CMPI #k sur la NOUVELLE valeur : une iteration de moins)
                    pend=None
                elif sy and sy.kind=='arithi' and sy.val[0]=='add' and sy.sz:
                    # Dn + (-k) range dans RES seulement : CMPI #k,Dn (le recompilateur code
                    # la comparaison comme l'addition de l'oppose). Si la somme retourne ensuite
                    # dans Dn, c'etait un ADDQ/SUBQ : l'ecriture de Dn annule ce CMP.
                    pend=('cmp',('D',sy.val[1]),('imm',(-sy.val[2]) & SZMASK[sy.sz]),sy.sz)
                else: pend=None
            # le bloc de calcul de la RETENUE qui suit toute ecriture de RES est interne au
            # recompilateur (il le produit meme quand aucun Bcc ne lit C) : toujours absorbe
            cb=carry_block(ins_list, i)
            if cb: absorbed.update(cb)
            i+=1; continue
        if m in ('sb','sh','sw') and lui.get(ins.rs)==0x7000:
            nm=slot_name(ins.imm)
            if ins.va in absorbed:
                out.append((ins.va,"(ecriture de registre d'adresse absorbee : conversion d'adresse ou 2e moitie d'un EXG)",[])); i+=1; continue
            if nm==('A',7) and ins.imm==0x111c:
                # A7 : dans le portage la pile 68K EST la pile MIPS ; la case A7 est morte (3 acces dans SFA3,
                # ex. le reset qui repositionne la pile). La traduire deplacerait NOTRE vraie pile (HANDOFF §59)
                out.append((ins.va,"(ecriture de A7 absorbee : pile du portage = pile MIPS)",[])); i+=1; continue
            if nm and nm[0]=='A' and m=='sw':
                src=st.get(ins.rt); am=nm[1]
                # (HANDOFF §86) MOVEA.W An,Am : 'lh An ; (ext. de signe) ; andi $FFFF ; sw Am' + conversion d'adresse
                # (movea_fixup). Etait PERDU : l'allocateur d'objets (mips 0x336358, A4 -> A3 puis A2) laissait A2/A3
                # perimes -> objet ecrit en $FF3F00, sur les pointeurs de plans (blocs dans le decor au K.O.)
                _j=_producer(ins_list, i, ins.rt, 8) if src is None and ins.rt!=0 else None
                if _j is not None and ins_list[_j].m=='andi' and ins_list[_j].imm==0xffff:
                    _k=_origin(ins_list, _producer(ins_list, _j, ins_list[_j].rs, 8))
                    _sn=slot_name(ins_list[_k].imm) if (_k is not None and ins_list[_k].m=='lh') else None
                    if _sn and _sn[0]=='A' and _sn[1]<7 and _sn[1]!=am:
                        n=_sn[1]
                        out.append((ins.va,"MOVEA.W A%d,A%d"%(n,am),[0x3048|((am&7)<<9)|(n&7)]))
                        fx=movea_fixup(ins_list,i,ins.imm)
                        if fx: absorbed.update(fx)
                        for r,sy in list(st.items()):
                            if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                        REG68[nm]=None; i+=1; continue
                if src and src.kind=='reg68' and src.val and src.val[0]=='D':
                    k=src.val[1]                              # MOVEA.L Dk,Am
                    out.append((ins.va,"MOVEA.L D%d,A%d"%(k,am),[0x2040|((am&7)<<9)|(k&7)]))
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src is None and ins.rt!=0 and memread.get(ins.rt) and memread[ins.rt][0]=='L':
                    msz,mdisp,man=memread[ins.rt]
                    ws,mn=movea_l_mem(man,mdisp,am)
                    out.append((ins.va,mn,ws))
                    for r,sy in list(st.items()):          # l'ancienne valeur de Am n'a plus cours
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]=='L':
                    # (HANDOFF §106) MOVEA.L abs.L,Am : 'lui ; addiu ; [addiu] ; lw ; sw Am' etait PERDU (aucun cas
                    # pour un registre A) -> Am perime. Ex. fin de l'intro (mips 0x4FF10) : pointeurs de palettes
                    # $339838/$33979C de l'arcade -> couleurs prises n'importe ou (Bison, Akuma).
                    _,host=absread[ins.rt]; a_,note=abs_addr(host,'L')
                    ws=[0x2079|((am&7)<<9)]+abs_words(a_)
                    mn="MOVEA.L $%06x.L,A%d%s"%(a_&0xffffff,am,note)
                    if MEMMODE=='cps2':
                        exg=0xc188|(am&7); ws+=[exg,0x40e7,SWAP_OP|0,0x44df,exg]; mn+=" ; [remise en ordre du long]"
                    out.append((ins.va,mn,ws)); ABS_AN[0]+=1
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                _am=adda_mem(ins_list, i) if src is None else None
                if _am:
                    n_,d_=_am                                   # (HANDOFF §107) ADDA.W d(An),Am : etait PERDU
                    out.append((ins.va,"ADDA.W $%04x(A%d),A%d  [decalage relatif]"%(d_&0xffff,n_,am),
                                [0xd0e8|((am&7)<<9)|(n_&7), d_&0xffff]))
                    ADDA_MEM[0]+=1
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='an_tbl' and src.val[0]==am:
                    _,tbl,ix=src.val; DATA_TABLES[tbl]='W'
                    out.append((ins.va,"ADDA.W T_%06x(PC,D%d.W),A%d"%(tbl,ix,am),[0xd0c0|((am&7)<<9)|0x3b,(ix&7)<<12]))
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='tblent':
                    # MOVEA.L T(PC,Dk.W),Am : table de POINTEURS (HANDOFF §67 : ROM $27776, table des objets
                    # joueurs -> A6 ; n'etait pas traduit, A6 perime -> l'initialisation du joueur etait sautee)
                    tbl,ix,scale=src.val; DATA_TABLES[tbl]='L'
                    ws=[0x207b|((am&7)<<9), (ix&7)<<12]              # MOVEA.L T(PC,Dk.W),Am
                    mn="MOVEA.L T_%06x(PC,D%d.W),A%d"%(tbl,ix,am)
                    if MEMMODE=='cps2':
                        exg=0xc188|(am&7); ws=ws+[exg,0x40e7,SWAP_OP|0,0x44df,exg]; mn+=" ; [remise en ordre du long]"
                    if scale==4:
                        # (HANDOFF §112) index BRUT ('sll 2' sur l'index : code ajoute par le portage, ex. SURVIVAL
                        # mips 0x1F1D24, octet $C19C) : x4 dans Dk, sauve et rendu intact (le MIPS decale dans un
                        # temporaire), drapeaux compris. Elements separes : l'assembleur reconnait la lecture de table.
                        out.append((ins.va,"MOVE SR,-(SP) ; MOVEM.L D%d,-(SP) ; ADD.W D%d,D%d x2  [index brut x4]"%(ix,ix,ix),
                                    [0x40e7,0x48e7,1<<(15-ix),0xd040|(ix<<9)|ix,0xd040|(ix<<9)|ix]))
                        out.append((ins.va,mn,ws))
                        out.append((ins.va,"MOVEM.L (SP)+,D%d ; MOVE (SP)+,CCR"%ix,[0x4cdf,1<<ix,0x44df]))
                        IDX_X4[0]+=1
                    else:
                        out.append((ins.va,mn,ws))
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='adda_idx' and src.val[0]==am:
                    _,(sz,n,dn,dsz,d8)=src.val
                    out.append((ins.va,"ADDA.W %d(A%d,D%d.%s),A%d"%(d8,n,dn,dsz,am),
                                [0xd0f0|((am&7)<<9)|(n&7), idx_ext(dn,dsz,d8)]))
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src is None and ins.rt!=0 and idxread.get(ins.rt) and idxread[ins.rt][0]=='L':
                    sz,n,dn,dsz,d8=idxread[ins.rt]               # MOVEA.L d8(An,Dn),Am (pointeur en table)
                    ws=[0x2070|((am&7)<<9)|(n&7), idx_ext(dn,dsz,d8)]
                    mn="MOVEA.L %d(A%d,D%d.%s),A%d"%(d8,n,dn,dsz,am)
                    if MEMMODE=='cps2':
                        exg=0xc188|(am&7); ws+=[exg,0x40e7,SWAP_OP|0,0x44df,exg]; mn+=" ; [remise en ordre du long]"
                    out.append((ins.va,mn,ws))
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='zx' and src.val[0][0]=='D' and src.val[1]=='W':
                    k=src.val[0][1]                           # MOVEA.W Dk,Am (+ conversion hote absorbee)
                    out.append((ins.va,"MOVEA.W D%d,A%d"%(k,am),[0x3040|((am&7)<<9)|(k&7)]))
                    fx=movea_fixup(ins_list,i,ins.imm)
                    if fx: absorbed.update(fx)
                    for r,sy in list(st.items()):
                        if sy and sy.kind=='an' and sy.val[0]==am: st[r]=None
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='zx' and src.val[0][0]=='mem' and src.val[1]=='W':
                    src=Sym('zext16', src.val[0][1:])
                if src is None and ins.rt!=0:
                    lo=lui_only(ins_list, i, ins.rt)             # LEA d'une adresse chargee par un lui seul
                    if lo is not None: src=Sym('const',lo.val)
                if src and src.kind=='const':
                    # adresse constante chargee dans An (LEA abs.L ou MOVEA.L #). En mode hote :
                    # adresse PS2 brute ; la conversion vers la carte CPS2 se fait via ADDRMAP.
                    v=src.val
                    if is_code_ptr(v):                            # POINTEUR DE CODE : notre etiquette (assembleur)
                        out.append((ins.va,"LEA CODE_%07x,A%d  [pointeur de code]"%(v-RUNTIME_BASE,am),
                                    [0x41f9|((am&7)<<9),0,0]))
                        REG68[nm]=None; i+=1; continue
                    va68=addr_to_68k(v) if MEMMODE=='cps2' else v
                    tag="" if va68==v else "  [PS2 %08x]"%v
                    if va68 is None: va68=v; tag="  [PS2 %08x, ZONE NON CONVERTIE]"%v
                    out.append((ins.va,"LEA $%06x.L,A%d%s"%(va68&0xffffff,am,tag),
                                [0x41f9|((am&7)<<9),(va68>>16)&0xffff,va68&0xffff]))
                    REG68[nm]=None; i+=1; continue
                if src and src.kind=='zext16':
                    sz,disp,an=src.val
                    out.append((ins.va,"MOVEA.W $%04x(A%d),A%d"%(disp,an,am),enc_movea_w_an(an,disp,am)))
                    fx=movea_fixup(ins_list,i,ins.imm)
                    if fx: absorbed.update(fx)
                elif src and src.kind=='an' and src.val[1]==0 and src.val[0]!=am and \
                     any(y.m=='sw' and lui.get(y.rs,None)==0x7000 and y.imm in an_slots(src.val[0])
                         and ((st.get(y.rt) and st[y.rt].kind=='an' and st[y.rt].val==(am,0)) or _spill_an(y.rt,_j,am))
                         for _j,y in enumerate(ins_list[i+1:i+4],i+1)):
                    n=src.val[0]
                    # ECHANGE : MOVEA seul oubliait la 2e moitie (l'autre registre gardait sa valeur)
                    # (HANDOFF §80) l'autre registre peut etre A8 prete sur An : sa case est alors 0x1120
                    for y in ins_list[i+1:i+4]:
                        if y.m=='sw' and y.imm in an_slots(n): absorbed.add(y.va); break
                    out.append((ins.va,"EXG A%d,A%d"%(n,am),[0xc148|((n&7)<<9)|(am&7)]))
                    for r,sy in list(st.items()):          # les deux registres ont change
                        if sy and sy.kind=='an' and sy.val[0] in (am,n): st[r]=None
                    REG68[nm]=None; i+=1; continue
                elif src and src.kind=='an':
                    n,dd=src.val
                    if n==am and dd:
                        ws,mn=enc_addq_an(dd - (0x10000 if dd&0x8000 else 0), am); out.append((ins.va,mn,ws))
                    elif n!=am and dd==0:
                        out.append((ins.va,"MOVEA.L A%d,A%d"%(n,am),enc_movea_l_an(n,am)))
                    elif n!=am:
                        out.append((ins.va,"LEA $%04x(A%d),A%d"%(dd,n,am),enc_lea_an(n,dd,am)))
                elif TBLBYTE_ON and src and src.kind=='tblmem' and src.val[1][0]=='W':
                    # (HANDOFF §137) An = table + mot memoire signe (Hyper mips 0x5A448) : LEA T.L,An ; ADDA.W d(Ak),An
                    _tb,(_msz,_d,_ak)=src.val; _a68=addr_to_68k(_tb)
                    out.append((ins.va,"LEA $%06x.L,A%d ; ADDA.W $%04x(A%d),A%d  [table + mot memoire]"%(_a68&0xffffff,am,_d&0xffff,_ak,am),
                                [0x41f9|((am&7)<<9),(_a68>>16)&0xffff,_a68&0xffff, 0xd0e8|((am&7)<<9)|(_ak&7), _d&0xffff]))
                    TBLBYTE_N[0]+=1
                elif src and src.kind=='an_dhi' and src.val[0]==am:
                    # (HANDOFF §132) An += mot haut (signe) du registre prete a D8 : SWAP ; ADDA.W ; SWAP, drapeaux gardes
                    _r=src.val[1]
                    out.append((ins.va,"ADDA.W (mot haut de D%d),A%d  [D8 prete : SWAP/ADDA.W/SWAP]"%(_r,am),
                                [0x40e7, 0x4840|_r, enc_adda_dn('W',_r,am)[0], 0x4840|_r, 0x46df]))
                    D8HI_N[0]+=1
                elif src and src.kind=='an_d':
                    # forme (An, Dn, taille) ou (An, Dn, taille, d8) apres un addiu
                    n,dn,sz,d8=(src.val+(0,))[:4]
                    if n==am and d8==0: out.append((ins.va,"ADDA.%s D%d,A%d"%(sz,dn,am),enc_adda_dn(sz,dn,am)))
                    elif -128<=d8<=127:
                        ws=enc_lea_index(n,dn,sz,am); ws[1]=(ws[1]&0xff00)|(d8&0xff)
                        out.append((ins.va,"LEA %d(A%d,D%d.%s),A%d"%(d8,n,dn,sz,am),ws))
                # CORRECTION : des registres MIPS peuvent garder l'ANCIENNE valeur de Am (ex.
                # 'lw a1,A6 ; addiu a0,a1,4 ; sw a0,A6 ; sw a2,0(a1)' = MOVE.L D1,(A6)+ : l'ecriture
                # passe par l'ancien A6). Si Am a change d'une quantite CONNUE, on les recale
                # (d -> d - delta) ; sinon on les invalide (mieux vaut ne rien traduire que mal).
                delta=None
                if src and src.kind=='an' and src.val[0]==am: delta=src.val[1]
                for r,sy in list(st.items()):
                    if sy and sy.kind=='an' and sy.val[0]==am:
                        if delta is not None: st[r]=Sym('an',(am,(sy.val[1]-delta)&0xffff))
                        else: st[r]=None
                if len(out)==_n0 and DN_ALU_ON:
                    _r=_a_alu(ins_list, i, am, bswap16_of)
                    if _r: out.append((ins.va,_r[1],_r[0])); DN_ALU[0]+=1
                if len(out)==_n0: _chute(CHUTES, ins, 'A', src, absread, memread, idxread, idxbig)
                REG68[nm]=None
                i+=1; continue
            if nm:
                src = Sym('imm',0) if ins.rt==0 else st.get(ins.rt)
                rev_prev = nm[0]=='D' and nm[1] in revd
                if nm[0]=='D': revd.discard(nm[1])
                if src and src.kind=='arith' and nm[0]=='D':
                    kind,dn,sn = src.val
                    size={'sb':'B','sh':'W','sw':'L'}[m]
                    if dn==nm[1]:          # le resultat retourne dans l'operande gauche
                        out.append((ins.va,"%s.%s D%d,D%d"%(ARITH_NAME[kind],size,sn,dn),
                                    enc_arith(kind,size,dn,sn)))
                        # (HANDOFF §64) le chemin 'bloc exact' ci-dessous emettait une 2e fois la meme
                        # soustraction (SUB.W D5,D7 double dans les listes de sprites) : on s'arrete ici
                        if exact_blk and exact_blk[0]<=ins.va<=exact_blk[1]+0x40 and exact_blk[2]==('D',nm[1]):
                            exact_blk=None
                            if pend and pend[0]=='cmp': pend=None
                        REG68[nm]=None; i+=1; continue
                size={'sb':'B','sh':'W','sw':'L'}[m]
                if nm[0]=='D' and exact_blk and exact_blk[0]<=ins.va<=exact_blk[1]+0x40 \
                   and exact_blk[2]==('D',nm[1]) and exact_blk[4]==size \
                   and derives_from(ins_list, i, ins.rt, exact_blk[5], exact_blk[6]):
                    ws,mn=enc_sub_dn(size,exact_blk[3],nm[1])
                    if ws:
                        out.append((ins.va,mn,ws)); exact_blk=None
                        if pend and pend[0]=='cmp': pend=None
                        REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='dop_idx' and src.val[0]==nm[1] and src.val[2][0]==size:
                    dn,op,(sz,n,xn,xsz,d8)=src.val
                    top={'addu':0xd000,'subu':0x9000,'and':0xc000,'or':0x8000}[op]
                    ws=[top|((dn&7)<<9)|(SZN[size]<<6)|0x30|(n&7), idx_ext(xn,xsz,d8)]
                    out.append((ins.va,"%s.%s %d(A%d,D%d.%s),D%d%s"%({'addu':'ADD','subu':'SUB','and':'AND','or':'OR'}[op],
                                size,d8,n,xn,xsz,dn,idx_note(size)),ws)); last_sub=src.val
                    REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='rot' and src.val[0]==nm[1] and src.val[1]==size:
                    dn,sz,kind,cnt=src.val
                    w=(0xe018 if kind=='ror' else 0xe118)|((cnt&7)<<9)|({'B':0,'W':1,'L':2}[sz]<<6)|dn
                    out.append((ins.va,"%s.%s #%d,D%d"%(kind.upper(),sz,cnt,dn),[w])); last_sub=('rot',dn)
                    REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='bswap16' and size=='W':
                    # MOVE.W puis ROR.W #8 : le recompilateur inverse les octets (champ range
                    # octet par octet) ; on reproduit la valeur qu'il obtient
                    bs=src.val; ws=[]; mn=""
                    if bs[0]=='mem':
                        _,disp,an=bs; disp=mconv(disp,'W',an)
                        ws=enc_move_an_dn('W',an,disp,nm[1]); mn="MOVE.W $%04x(A%d),D%d ; "%(disp,an,nm[1])
                    elif bs[1]!=nm[1]:
                        ws=enc_move_reg_dn('W',('D',bs[1]),nm[1]); mn="MOVE.W D%d,D%d ; "%(bs[1],nm[1])
                    if bs[0]=='mem' and MEMMODE=='type' and bs[2] in TYPE_REGS:
                        # mode type : champ d'octets lu en mot -> le recompilateur inverse pour
                        # retrouver la VRAIE valeur ; la ROM a un simple MOVE.W
                        mn=mn.rstrip(' ;')
                    else:
                        ws=ws+[0xe058|nm[1]]; mn+="ROR.W #8,D%d  [octets inverses par le recompilateur]"%nm[1]
                    out.append((ins.va,mn,ws)); REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='dynbit' and src.val[0]!='btst' and src.val[2]==('D',nm[1]) and size=='L':
                    ws,mn=enc_dynbit(src.val[0],src.val[1],src.val[2])
                    out.append((ins.va,mn,ws)); pend=None; REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='mask24' and src.val==nm[1] and size=='L':
                    # CORRECTION : ce n'est PAS un masque d'adresse ajoute par le recompilateur mais
                    # le ANDI.L #$FFFFFF00,Dn du jeu (27 sites MIPS <-> 28 dans la ROM : etat d'objet
                    # $0200xx00 dont on isole les 3 octets hauts). La valeur du registre etant
                    # l'image octets-inverses de celle du 68K, le masque devient $00FFFFFF.
                    if rev_prev:                               # mode type : valeur remise a l'endroit
                        out.append((ins.va,"ANDI.L #$ffffff00,D%d"%nm[1],[0x0280|nm[1],0xffff,0xff00])); revd.add(nm[1])
                    else:
                        ws_=[0x0280|nm[1],0x00ff,0xffff]; mn_="ANDI.L #$00ffffff,D%d  [ROM : ANDI.L #$ffffff00, registre octets-inverses]"%nm[1]
                        pl_=RETAG_FN() if (RETAG24 and RETAG_FN) else None
                        if pl_:                                # (agent_defauts_banc, RETAG24) etiquette $01 remise
                            ws_+=retag_seq(nm[1],pl_); RETAG24_N.add(ins.va)
                            mn_+=" ; [RETAG24 : D%d dans %s -> ORI.L #$01000000]"%(nm[1],",".join("$%x-$%x"%p for p in pl_))
                        out.append((ins.va,mn_,ws_))
                    last_sub=('andi24',nm[1]); REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='neg' and src.val==nm[1]:
                    out.append((ins.va,"NEG.%s D%d"%(size,nm[1]),[0x4400|({'B':0,'W':1,'L':2}[size]<<6)|nm[1]]))
                    last_sub=('neg',nm[1]); REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind in ('shift','scaled') and src.val[1 if src.kind=='shift' else 0]==nm[1]:
                    if src.kind=='shift': kind,dn,cnt=src.val
                    else: kind,dn,cnt='sll',src.val[0],{2:1,4:2}[src.val[1]]
                    # (HANDOFF §132) decalage de plus de 8 (immediat 68K limite a 8) : en tranches (Upper mips 0x412A58, LSL #12)
                    ws=[]; mn=[]; c_=cnt
                    while c_>0:
                        w_,m_=enc_shift_dn(kind,size,min(c_,8),dn); ws+=w_; mn.append(m_); c_-=min(c_,8)
                    if cnt>8: BIGSHIFT_N[0]+=1
                    out.append((ins.va," ; ".join(mn),ws)); last_sub=('shift',dn); REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src is None and ins.rt!=0 and m=='sw':
                    src=lui_only(ins_list, i, ins.rt)
                if nm[0]=='D' and src and src.kind=='imm' and m=='sw' and ins.rt!=0 and src.val>0xffff:
                    ws,mn=enc_imm_dn('L',src.val,nm[1])
                    out.append((ins.va,mn,ws)); REG68[nm]=src; i+=1; continue
                if nm[0]=='D' and src and src.kind=='const' and m=='sw':
                    v=src.val
                    if MEMMODE=='cps2':
                        a68=addr_to_68k(v)                 # une adresse PS2 rangee dans Dn
                        if a68 is not None and LUIDN and isinstance(v,int) and (v & 0xffff)==0 \
                           and lui_dn_usage(ins_list, i, ins.imm & 0xffff)=='val':
                            LUIDN_LOG.append((ins.va, v, a68)); a68=None   # (agent_coups) constante, pas une adresse
                        if a68 is not None: v=a68
                    ws,mn=enc_imm_dn('L',v,nm[1])
                    out.append((ins.va,mn,ws)); REG68[nm]=src; i+=1; continue
                if nm[0]=='D' and src and src.kind=='imm' and ins.rt!=0:
                    v=src.val
                    # (HANDOFF §79) pas de re-extension de signe ici : addiu est deja etendu sur 32 bits, et
                    # 'ori rX,zero,$FF05' vaut $0000FF05 (commande son de la ROM $3210 : MOVE.L #$0000FF05,D1)
                    ws,mn=enc_imm_dn(size,v,nm[1])
                    out.append((ins.va,mn,ws)); REG68[nm]=src; i+=1; continue
                if nm[0]=='D' and m=='sw' and is_swap(ins_list, i, ins.imm):
                    out.append((ins.va,"SWAP D%d"%nm[1],[0x4840|(nm[1]&7)]))
                    REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='dmem' and src.val[0]==nm[1] and src.val[2][0]==size:
                    ws,mn=enc_op_mem_dn(src.val[1],size,src.val[2],nm[1])
                    out.append((ins.va,mn,ws)); last_sub=src.val; REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='memarith' and src.val[2]==nm[1] \
                   and src.val[1] in ('addu','and','or') and src.val[0][0]==size:
                    ws,mn=enc_op_mem_dn(src.val[1],size,src.val[0],nm[1])
                    out.append((ins.va,mn,ws)); last_sub=src.val; REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='sub' and src.val[0]==('D',nm[1]) \
                   and src.val[1] is not None and src.val[2]==size:
                    ws,mn=enc_sub_dn(size,src.val[1],nm[1])
                    if ws:
                        out.append((ins.va,mn,ws)); last_sub=src.val
                        if pend and pend[0]=='cmp': pend=None      # c'etait un SUB, pas un CMP
                        REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='notd' and src.val==nm[1]:
                    out.append((ins.va,"NOT.%s D%d"%(size,nm[1]),[0x4600|(SZN[size]<<6)|(nm[1]&7)]))
                    if pend and pend[0]=='cmp': pend=None
                    REG68[nm]=None; i+=1; continue
                if nm[0]=='D' and src and src.kind=='arithi' and src.val[1]==nm[1]:
                    kind,dn,v = src.val
                    if pend and pend[0]=='cmp' and pend[1]==('D',dn): pend=None   # c'etait un ADDQ, pas un CMP
                    _bop=None
                    if BITOP_DN and pend and pend[0]=='btst_dn' and pend[2]==dn and kind in ('and','or','xor'):
                        # (agent_defauts_banc, BITOP_DN) 'RES = Dn & bit ; Dn = Dn & ~bit (| bit, ^ bit) ; bne RES' =
                        # BCLR (BSET, BCHG) #b,Dn : Z = ANCIEN bit. Le BTST rendu au branchement lisait le bit deja efface
                        # (SFA3 mips 0x25992C, arcade $05DB46 'BCLR #0,D6 ; BNE' de la visee du Killer Bee Assault)
                        _b=pend[1]; _w={'B':0xff,'W':0xffff,'L':0xffffffff}[size]
                        if _b < {'B':8,'W':16,'L':32}[size]:
                            if kind=='and' and (v & _w)==((~(1<<_b)) & _w): _bop=('BCLR',0x0880)
                            elif kind=='or' and (v & _w)==(1<<_b): _bop=('BSET',0x08c0)
                            elif kind=='xor' and (v & _w)==(1<<_b): _bop=('BCHG',0x0840)
                    if _bop is not None:
                        out.append((ins.va,"%s #%d,D%d  [test du bit avant l'operation, BITOP_DN]"%(_bop[0],_b,dn),[_bop[1]|(dn&7),_b]))
                        BITOP_DN_N.add(ins.va); pend=None
                        REG68[nm]=None; i+=1; continue
                    if kind=='add':
                        ws,mn = enc_addimm_dn(size, dn, v)
                        out.append((ins.va, mn, ws))
                    else:
                        out.append((ins.va,"%s.%s #$%x,D%d"%(IMMOP_NAME[kind],size,v,dn),
                                    enc_immop_dn(kind,size,dn,v)))
                    arith_written=(dn,kind,v); arith_len=len(out)   # (HANDOFF §73) drapeaux poses par l'operation
                elif (nm[0]=='D' and src and src.kind in ('reg68','an') and ins.rt!=0
                      and (src.kind=='an' and src.val[1]==0 or src.kind=='reg68' and src.val and src.val[0]=='D')):
                    reg = ('A',src.val[0]) if src.kind=='an' else ('D',src.val[1])
                    _xd=None
                    if EXG_PILE_D and reg[0]=='D' and reg[1]!=nm[1] and size=='L' and m=='sw':
                        # (agent_defauts_banc, EXG_PILE_D) 2e moitie : 'lw rX,off(sp)' (temporaire = ancien Dn) puis
                        # 'sw rX,case(Dm)' dans les 4 instructions suivantes
                        for _j,y in enumerate(ins_list[i+1:i+5],i+1):
                            if y.m=='sw' and lui.get(y.rs,None)==0x7000 and y.imm==0x1124+4*reg[1]:
                                for y_ in ins_list[i+1:_j]:
                                    if y_.m=='lw' and y_.rs==29 and y_.rt==y.rt and y_.simm in spill:
                                        sy_=spill[y_.simm][0]
                                        if sy_ and sy_.kind=='reg68' and sy_.val==('D',nm[1]): _xd=y
                                # temporaire dans un REGISTRE MIPS (recompilateur d'Hyper : 'lw s3,D0 ; lw a0,D1 ;
                                # sw a0,D0 ; sw s3,D1', mips 0x31388C, arcade $5850C) : s3 garde l'ancien Dn
                                _sy=st.get(y.rt)
                                if (_xd is None and y.rt!=ins.rt and _sy and _sy.kind=='reg68' and _sy.val==('D',nm[1])
                                        and ldsize.get(y.rt) in (None,'L')
                                        and not any(getattr(y_,'rt',None)==y.rt and y_.m in ('lw','lh','lb','lhu','lbu','addiu','ori','lui')
                                                    for y_ in ins_list[i+1:_j])):
                                    _xd=y
                                break
                            if y.m in ('jal','jalr','jr') or y.m in _BRANCHES: break
                    if _xd is not None:
                        absorbed.add(_xd.va); EXG_PILE_D_N.add(ins.va)
                        out.append((ins.va,"EXG D%d,D%d  [echange par la pile MIPS, EXG_PILE_D]"%(reg[1],nm[1]),
                                    [0xc140|((reg[1]&7)<<9)|(nm[1]&7)]))
                        for r_,sy in list(st.items()):
                            if sy and sy.kind=='reg68' and sy.val in (('D',reg[1]),('D',nm[1])): st[r_]=None
                        for k_ in list(spill):
                            if spill[k_][0] and spill[k_][0].kind=='reg68' and spill[k_][0].val in (('D',reg[1]),('D',nm[1])):
                                spill[k_]=(None,)+tuple(spill[k_][1:])
                    elif reg!=('D',nm[1]) and not (reg[0]=='A' and size=='B'):
                        out.append((ins.va,"MOVE.%s %s%d,D%d"%(size,reg[0],reg[1],nm[1]),
                                    enc_move_reg_dn(size,reg,nm[1])))
                        moved_d=reg; moved_len=len(out)   # (HANDOFF §80) valable tant que rien d'autre n'est emis
                elif (ABSEXT_ON and nm[0]=='D' and src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]=='W'
                      and size=='L' and _origin(ins_list,_producer(ins_list,i,ins.rt,8)) is not None
                      and ins_list[_origin(ins_list,_producer(ins_list,i,ins.rt,8))].m=='lh'):
                    # (HANDOFF §132) mot absolu SIGNE range en long : MOVE.W abs,Dn ; EXT.L Dn (Upper mips 0x405024)
                    _sz,_host=absread[ins.rt]; _a,_note=abs_addr(_host,'W')
                    out.append((ins.va,"MOVE.W $%06x.L,D%d ; EXT.L D%d%s"%(_a&0xffffff,nm[1],nm[1],_note),
                                [0x3039|((nm[1]&7)<<9)]+abs_words(_a)+[0x48c0|nm[1]])); ABSEXT_N[0]+=1
                elif nm[0]=='D' and src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]==size:
                    sz,host=absread[ins.rt]; a,note=abs_addr(host,size)
                    ws=[(SZ_TOP[size]<<12)|((nm[1]&7)<<9)|0x39]+abs_words(a)
                    if MEMMODE=='cps2' and size=='L': ws=ws+[SWAP_OP|nm[1]]
                    inv=INPUT_INV.get(host-(RAM_HI<<16)) if MEMMODE in ('cps2','type') else None
                    if inv:                                      # entree CPS2 active a l'etat bas : le portage l'inversait
                        ws=ws+[0x4600|({'B':0,'W':1,'L':2}[size]<<6)|nm[1]]; note+="  ; NOT (entree inversee par le portage)"
                    out.append((ins.va,"MOVE.%s $%06x.L,D%d%s"%(size,a&0xffffff,nm[1],note),ws))
                elif nm[0]=='D' and src is None and ins.rt!=0 and idxbig.get(ins.rt) and idxbig[ins.rt][0]==size:
                    sz,n,dn,dsz,dd=idxbig[ins.rt]
                    op=[(SZ_TOP[size]<<12)|((nm[1]&7)<<9)|0x10|(n&7)]
                    ws=idxbig_seq(size,n,dn,dsz,dd,op)
                    if MEMMODE=='cps2' and size=='L': ws=ws+[SWAP_OP|nm[1]]
                    out.append((ins.va,"MOVE.%s $%04x(A%d,D%d.%s),D%d  [deplacement 16 bits]"%(size,dd&0xffff,n,dn,dsz,nm[1]),ws))
                elif nm[0]=='D' and src is None and ins.rt!=0 and idxread.get(ins.rt) and idxread[ins.rt][0]==size:
                    sz,n,dn,dsz,d8=idxread[ins.rt]
                    ws=[(SZ_TOP[size]<<12)|((nm[1]&7)<<9)|0x30|(n&7), idx_ext(dn,dsz,d8)]
                    if MEMMODE=='cps2' and size=='L': ws=ws+[SWAP_OP|nm[1]]
                    out.append((ins.va,"MOVE.%s %d(A%d,D%d.%s),D%d%s"%(size,d8,n,dn,dsz,nm[1],idx_note(size)),ws))
                    # (HANDOFF §80) la valeur est maintenant dans Dk : un test ulterieur porte sur Dk, et les lectures
                    # indexees PAR Dk sont perimees ('MOVE.W 0(A0,D0.W),D0' puis TST.W 0(A0,D0.W) : index ecrase)
                    for r_ in [r_ for r_,ix in idxread.items() if ix[2]==nm[1] or r_==ins.rt]: idxread.pop(r_,None)
                    st[ins.rt]=Sym('reg68',('D',nm[1])); SL[ins.rt]=size
                elif ROT_ON and nm[0]=='D' and size=='W' and rot_idiom(ins_list, i):
                    _dir,_k,_n=rot_idiom(ins_list, i)
                    out.append((ins.va,"%s.W D%d,D%d  [rotation decomposee]"%(_dir,_n,_k),[(0xe078 if _dir=='ROR' else 0xe178)|((_n&7)<<9)|(_k&7)]))
                    ROT_N[0]+=1
                elif TBLBYTE_ON and nm[0]=='D' and src and src.kind=='tblval' and src.val[2]=='W' and size=='B':
                    # (HANDOFF §137) Dn.B = octet bas d'un mot de table (Hyper mips 0x1122AC, 3 sites) : temporaire
                    _tb,_ix,_=src.val; _dn=nm[1]; _t=next(t for t in range(8) if t not in (_dn,_ix))
                    out.append((ins.va,"MOVE.L D%d,-(SP)  [octet bas d'un mot de table]"%_t,[0x2f00|_t]))
                    out.append((ins.va,"MOVE.W T_%06x(PC,D%d.W),D%d"%(_tb,_ix,_t),enc_move_pcidx('W',_ix,('D',_t))))
                    out.append((ins.va,"MOVE.B D%d,D%d ; MOVEM.L (SP)+,D%d"%(_t,_dn,_t),[0x1000|((_dn&7)<<9)|_t,0x4cdf,1<<_t]))
                    TBLBYTE_N[0]+=1
                elif TBLMASK_ON and nm[0]=='D' and src and src.kind=='tblmaskval' and src.val[4] in ('B','W') and size in ('B','W','L'):
                    # (HANDOFF §132) Dd = T[(Dn & k) x s] : [MOVE.W Dn,Dd ;] ANDI.W #k ; ADD.W (x s) ; MOVE.x T(PC,Dd.W),Dd ; EXT
                    _tb,_dn,_mk,_sc,_sz=src.val; _dd=nm[1]; ws=[]
                    if _dn!=_dd: ws+=[0x3000|((_dd&7)<<9)|(_dn&7)]
                    ws+=[0x0240|_dd,_mk]+[0xd040|((_dd&7)<<9)|_dd]*{1:0,2:1,4:2}[_sc]
                    out.append((ins.va,"ANDI.W #%d,D%d ; x%d  [index de table masque]"%(_mk,_dd,_sc),ws))
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D%d.W),D%d"%(_sz,_tb,_dd,_dd),enc_move_pcidx(_sz,_dd,('D',_dd))))
                    ext=[]
                    if _sz=='B' and size in ('W','L'): ext.append(0x4880|_dd)
                    if _sz in ('B','W') and size=='L': ext.append(0x48c0|_dd)
                    if ext: out.append((ins.va,"EXT  [valeur de table signee]",ext))
                    TBLMASK_N[0]+=1
                elif TBLMEM_ON and nm[0]=='D' and src and src.kind=='tblmemval':
                    # (HANDOFF §132) Dn = ext(T[ext(champ)]) : le registre destination sert d'index
                    _tb,(_msz,_d,_an),_sz=src.val; _dn=nm[1]
                    ws=enc_move_an_dn(_msz,_an,_d,_dn)+([0x4880|_dn] if _msz=='B' else [])
                    out.append((ins.va,"MOVE.%s $%04x(A%d),D%d%s  [index de table lu en memoire]"%(_msz,_d&0xffff,_an,_dn," ; EXT.W" if _msz=='B' else ""),ws))
                    ws2=enc_move_pcidx(_sz,_dn,('D',_dn))
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D%d.W),D%d"%(_sz,_tb,_dn,_dn),ws2))
                    ext=[]
                    if _sz=='B' and size in ('W','L'): ext.append(0x4880|_dn)
                    if size=='L': ext.append(0x48c0|_dn)
                    if ext: out.append((ins.va,"EXT  [valeur de table signee]",ext))
                    TBLMEM_N[0]+=1
                elif nm[0]=='D' and src and src.kind=='tblop' and size=='L' and src.val[1]==nm[1]:
                    # (HANDOFF §132) Dn op= T(PC,Dk.W).L : temporaire (long de table a moities echangees -> SWAP), MOVEM final
                    _op,_dn,_tb,_ix,_sc=src.val; _t=0 if _ix!=0 and _dn!=0 else (1 if _ix!=1 and _dn!=1 else 2)
                    DATA_TABLES[_tb]='L'
                    _opw={'or':0x8080,'and':0xc080,'addu':0xd080}[_op]|((_dn&7)<<9)|_t
                    out.append((ins.va,"MOVE.L D%d,-(SP)  [operation avec un long de table]"%_t,[0x2f00|_t]))
                    out.append((ins.va,"MOVE.L T_%06x(PC,D%d.W),D%d"%(_tb,_ix,_t),enc_move_pcidx('L',_ix,('D',_t))))
                    out.append((ins.va,"SWAP D%d ; %s.L D%d,D%d ; MOVEM.L (SP)+,D%d"%(_t,{'or':'OR','and':'AND','addu':'ADD'}[_op],_t,_dn,_t),
                                [SWAP_OP|_t,_opw,0x4cdf,1<<_t]))
                    TBLOP_N[0]+=1
                elif nm[0]=='D' and src and src.kind=='memshift' and size in ('W','L') and MEMMODE=='cps2':
                    # (HANDOFF §132) Dn = (long memoire >> k) : MOVE.L + SWAP (moities echangees) + ASR/LSR.L #k ; en mot
                    # ('sh'), le mot haut de Dn est garde (copie sur la pile, mot bas remplace)
                    (_sz,_d,_an),_m,_k=src.val; _dn=nm[1]
                    _sh=(0xe080 if _m=='sra' else 0xe088)|((_k&7)<<9)|(_dn&7)
                    _ld=enc_move_an_dn('L',_an,_d,_dn)+[SWAP_OP|_dn,_sh]
                    # (HANDOFF §137) en mot aussi, la valeur decalee ENTIERE : les 12 sites (SFA3 $BF40, Upper $C140) alignent un
                    # pointeur video sur 256 (>> 8 puis LSL.L #8 puis conversion d'adresse) ; garder l'ancien mot haut perdait le
                    # marqueur materiel $01 -> $0090C000 converti comme une adresse PS2 -> plantage a la fin des fins de SFA3
                    if size=='L' or not MEMSHIFT_GARDE:
                        out.append((ins.va,"MOVE.L $%04x(A%d),D%d ; SWAP ; %s.L #%d,D%d  [long memoire decale]"%(_d&0xffff,_an,_dn,'ASR' if _m=='sra' else 'LSR',_k,_dn),_ld))
                    else:
                        out.append((ins.va,"MOVE.W de ($%04x(A%d).L %s %d) dans D%d  [long memoire decale, mot haut garde]"%(_d&0xffff,_an,'>>',_k,_dn),
                                    [0x2f00|_dn]+_ld+[0x3f40|_dn,0x0002,0x201f|(_dn<<9)]))
                    MEMSHIFT_N[0]+=1
                elif nm[0]=='D' and src and src.kind=='mul' and size=='L' and MULS_ON:
                    # (HANDOFF §132) Dn = op1.W x op2.W -> [MOVE.W op1,Dn ;] MULS.W/MULU.W op2,Dn
                    _mm,_a,_b=src.val; _dn=nm[1]; _op=0xc1c0 if _mm=='mult' else 0xc0c0; _nm='MULS' if _mm=='mult' else 'MULU'
                    _ok=lambda o: o and (o[0]=='D' or (o[0]=='mem' and o[1]=='W'))
                    if _a==('D',_dn): _o,_pre=_b,None
                    elif _b==('D',_dn): _o,_pre=_a,None
                    else: _o,_pre=_b,_a
                    if _ok(_o) and (_pre is None or _ok(_pre)):
                        if _pre is not None:
                            if _pre[0]=='D': out.append((ins.va,"MOVE.W D%d,D%d"%(_pre[1],_dn),[0x3000|((_dn&7)<<9)|(_pre[1]&7)]))
                            else: out.append((ins.va,"MOVE.W $%04x(A%d),D%d"%(_pre[2]&0xffff,_pre[3],_dn),enc_move_an_dn('W',_pre[3],_pre[2],_dn)))
                        _ea,_t=_src_ea(_o)
                        out.append((ins.va,"%s.W %s,D%d  [mult du R5900]"%(_nm,_t,_dn),[_op|((_dn&7)<<9)|_ea[0]]+([_o[2]&0xffff] if _o[0]=='mem' else [])))
                        MULS_N[0]+=1
                elif nm[0]=='D' and src and src.kind=='tblent' and size=='L':
                    tbl,ix,scale=src.val; DATA_TABLES[tbl]='L'
                    ws=enc_move_pcidx('L',ix,('D',nm[1]))
                    if MEMMODE=='cps2': ws=ws+[SWAP_OP|nm[1]]
                    out.append((ins.va,"MOVE.L T_%06x(PC,D%d.W),D%d"%(tbl,ix,nm[1]),ws))
                elif (nm[0]=='D' and src and src.kind=='tblval' and src.val[2]=='B' and size=='W'
                      and _origin(ins_list,_producer(ins_list,i,ins.rt,8)) is not None
                      and ins_list[_origin(ins_list,_producer(ins_list,i,ins.rt,8))].m=='lb'):
                    # octet SIGNE d'une table range en mot (lb ; sh) : MOVE.B + EXT.W (HANDOFF §66 : etape de
                    # l'intro, D0 restait perime)
                    tbl,ix,_=src.val
                    ws=enc_move_pcidx('B',ix,('D',nm[1]))+[0x4880|nm[1]]
                    out.append((ins.va,"MOVE.B T_%06x(PC,D%d.W),D%d ; EXT.W D%d"%(tbl,ix,nm[1],nm[1]),ws))
                elif nm[0]=='D' and src and src.kind=='tblval' and src.val[2]==size:
                    tbl,ix,_=src.val
                    ws=enc_move_pcidx(size,ix,('D',nm[1]))
                    if MEMMODE=='cps2' and size=='L': ws=ws+[SWAP_OP|nm[1]]
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D%d.W),D%d"%(size,tbl,ix,nm[1]),ws))
                elif nm[0]=='D' and ins.rt!=0 and src is None and ins.rt in memread:
                    msz,disp,an = memread[ins.rt]
                    if msz=='W' and size=='B' and MEMMODE in ('cps2','hote'):
                        # (HANDOFF §69) octet lu via 'lh' (demi-mot entier, octet BAS garde par sb) : l'octet bas
                        # d'un demi-mot petit-boutiste est l'octet MIPS de meme adresse -> 68K : adresse XOR 1
                        # (ROM $27766 : MOVE.B -$4FDE(A5),D0, compteur de la boucle des objets joueurs)
                        d=(disp^1) if MEMMODE=='cps2' else disp
                        out.append((ins.va,"MOVE.B $%04x(A%d),D%d  [octet bas d'un lh]"%(d&0xffff,an,nm[1]),
                                    enc_move_an_dn('B',an,d,nm[1])))
                        moved=None
                    elif EXT_MEM and MEMMODE in ('cps2','hote') and (msz,size) in (('B','W'),('B','L'),('W','L')) \
                         and _origin(ins_list,_producer(ins_list,i,ins.rt,8)) is not None \
                         and ins_list[_origin(ins_list,_producer(ins_list,i,ins.rt,8))].m in ('lb','lh'):
                        # (HANDOFF §128) lecture SIGNEE plus etroite que le rangement ('lb ; dsll32/dsra32 ; sh Dk') :
                        # MOVE + EXT. Rien n'etait emis (Upper mips 0x413270 : 'MOVE.B $10D(A5),D0 ; EXT.W D0' perdu,
                        # D0 gardait $FF -> animation $FF d'un objet du decor $42 -> erreur d'adresse)
                        n_=nm[1]; ws=enc_move_an_dn(msz,an,disp,n_)
                        mn_="MOVE.%s $%04x(A%d),D%d"%(msz,disp&0xffff,an,n_)
                        if msz=='B': ws=ws+[0x4880|n_]; mn_+=" ; EXT.W D%d"%n_
                        if size=='L': ws=ws+[0x48c0|n_]; mn_+=" ; EXT.L D%d"%n_
                        out.append((ins.va,mn_+"  [lecture signee etendue]",ws)); EXT_MEM_N[0]+=1
                        moved=None
                    elif msz==size:
                        ws=enc_move_an_dn(size,an,disp,nm[1])
                        if MEMMODE=='cps2' and size=='L': ws=ws+[SWAP_OP|nm[1]]
                        out.append((ins.va,"MOVE.%s $%04x(A%d),D%d"%(size,disp,an,nm[1])
                                    +(" ; SWAP D%d"%nm[1] if MEMMODE=='cps2' and size=='L' else ""),ws))
                        moved=memread[ins.rt]
                        if size=='L' and rev_field(an,disp): revd.add(nm[1])
                prev = REG68.get(nm)
                REG68[nm]= src
                # mise a zero d'un registre de donnees -> le 68K emet MOVEQ #0,Dn
                # CORRECTION : on n'essaie plus d'eviter les doublons grace a la valeur
                # 'connue' du registre : ce souvenir debordait d'une fonction a l'autre et
                # supprimait des effacements reels (D2 garde une valeur perimee).
                if nm[0]=='D' and ins.rt==0:
                    if m=='sw': out.append((ins.va,"MOVEQ #$0,D%d"%nm[1],[0x7000|(nm[1]<<9)]))
                    elif m=='sh': out.append((ins.va,"CLR.W D%d"%nm[1],[0x4240|nm[1]]))
                    else: out.append((ins.va,"CLR.B D%d"%nm[1],[0x4200|nm[1]]))
                if len(out)==_n0 and m in ('sw','sh','sb') and nm[0]=='D' and DN_ALU_ON:
                    _r=_dn_alu(ins_list, i, nm[1], size, lambda t: addr_to_68k(t) is not None)
                    if _r:
                        out.append((ins.va,_r[1],_r[0])); DN_ALU[0]+=1
                        if '[valeur de table]' in _r[1]: DATA_TABLES.setdefault(int(_r[1].split('T_')[1][:6],16), size)
                        REG68[nm]=None
                if len(out)==_n0 and m in ('sw','sh','sb'): _chute(CHUTES, ins, nm[0], src, absread, memread, idxread, idxbig)
            i+=1; continue
        # lecture [A5+disp] : on retient l'origine pour reconnaitre BTST/TST
        if m in ('lb','lbu','lh','lhu') and st.get(ins.rs) and st[ins.rs].kind=='tblidx' and ins.simm==0:
            tbl,ix,scale=st[ins.rs].val
            szz='B' if m in ('lb','lbu') else 'W'
            DATA_TABLES[tbl]=szz
            st[ins.rt]=Sym('tblval',(tbl,ix,szz)); lui.pop(ins.rt,None); i+=1; continue
        if m=='lw' and st.get(ins.rs) and st[ins.rs].kind=='tblidx' and ins.simm==0:
            st[ins.rt]=Sym('tblent', st[ins.rs].val); lui.pop(ins.rt,None); i+=1; continue
        if m in ('lb','lh','lw','lbu','lhu') and ins.rs in lui and lui[ins.rs]!=0x7000 and not st.get(ins.rs):
            sz={'lb':'B','lbu':'B','lh':'W','lhu':'W','lw':'L'}[m]
            absread[ins.rt]=(sz, ((lui[ins.rs]<<16)+ins.simm)&0xffffffff)
            st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
        if m in ('lb','lh','lw','lbu','lhu') and st.get(ins.rs) and st[ins.rs].kind=='const':
            sz={'lb':'B','lbu':'B','lh':'W','lhu':'W','lw':'L'}[m]     # lui+addiu puis lecture : abs.L
            absread[ins.rt]=(sz, (st[ins.rs].val+ins.simm)&0xffffffff)
            st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
        if m in ('lb','lh','lw','lbu','lhu') and st.get(ins.rs) and st[ins.rs].kind=='an_d':
            n,dn,dsz,d8=(st[ins.rs].val+(0,))[:4]
            d8=(d8+ins.simm)
            if not (-128<=d8<=127) and -0x8000<=d8<=0x7fff:
                sz={'lb':'B','lbu':'B','lh':'W','lhu':'W','lw':'L'}[m]
                idxbig[ins.rt]=(sz,n,dn,dsz,d8); idxread.pop(ins.rt,None)
                st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
            if -128<=d8<=127:
                sz={'lb':'B','lbu':'B','lh':'W','lhu':'W','lw':'L'}[m]
                if MEMMODE=='cps2' and sz=='B': d8^=1        # octet indexe : index PAIR suppose (HANDOFF §61)
                idxread[ins.rt]=(sz,n,dn,dsz,d8)
                st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
        if m in ('lb','lh','lw','lbu','lhu'):
            b=st.get(ins.rs)
            if b and b.kind=='an':
                sz={'lb':'B','lbu':'B','lh':'W','lhu':'W','lw':'L'}[m]
                memread[ins.rt]=(sz,mconv((b.val[1]+ins.simm)&0xffff,sz,b.val[0]),b.val[0])
                st[ins.rt]=None; lui.pop(ins.rt,None); i+=1; continue
        if m=='or' and MEMMODE=='cps2':
            n_=bswap32_or(ins_list, i)
            if n_ is not None:                         # (HANDOFF §90) bswap32(Dn) range octet par octet
                st[ins.rd]=Sym('bswap32',('D',n_)); lui.pop(ins.rd,None); i+=1; continue
            n_=swap_or(ins_list, i)
            if n_ is not None:                         # (HANDOFF §83) SWAP(Dn) assemble pour un rangement naturel
                st[ins.rd]=Sym('swapd',('D',n_)); lui.pop(ins.rd,None); i+=1; continue
        # (HANDOFF §122) COPIE DE REGISTRE du recompilateur recent : 'addu/or/daddu rd,rs,zero' (daddu = addu au
        # decodage). Le registre recoit tout ce que l'on sait de la source (valeur symbolique, lecture memoire, absolue,
        # indexee, taille) ; 'rd = zero + zero' = constante 0. Avant : suivi efface -> operande d'un CMP « drapeaux
        # exacts » inconnu -> comparaison perdue (Psycho Crusher de Bison sans fin dans Upper, 18 blocs ro5).
        if COPIES_ON and m in ('addu','or') and 0 in (ins.rs, ins.rt) and ins.rd != 0:
            src_r = ins.rs or ins.rt
            if src_r == 0:
                st[ins.rd]=Sym('imm',0); lui.pop(ins.rd,None)
            else:
                st[ins.rd]=st.get(src_r)
                if src_r in lui: lui[ins.rd]=lui[src_r]
                else: lui.pop(ins.rd,None)
                if SM.get(src_r): memread[ins.rd]=SM[src_r]
                if SAB.get(src_r): absread[ins.rd]=SAB[src_r]
                if SL.get(src_r): ldsize[ins.rd]=SL[src_r]
                if SI.get(src_r): idxread[ins.rd]=SI[src_r]
            COPIES[0]+=1
            i+=1; continue
        # propagation a travers l'extension de signe
        if m=='dsrl32' and ins.sa==8 and st.get(ins.rt) and st[ins.rt].kind=='reg68' \
           and st[ins.rt].val and st[ins.rt].val[0]=='D':
            # 'dsll32 x,8 ; dsrl32 x,8' = ANDI.L #$FFFFFF00,Dn du jeu, sur la valeur
            # octets-inversee (voir l'ecriture du registre)
            st[ins.rd]=Sym('mask24', st[ins.rt].val[1]); i+=1; continue
        if m=='srl' and 1<=ins.sa<=(31 if BIGSHIFT_ON else 8) and st.get(ins.rt) and st[ins.rt].kind=='reg68' \
           and st[ins.rt].val and st[ins.rt].val[0]=='D':
            st[ins.rd]=Sym('shift',('srl', st[ins.rt].val[1], ins.sa)); i+=1; continue
        # (HANDOFF §132) DECALAGE d'un long lu en memoire ('lw x,d(An) ; sra x,8' -> Dn) : n'emettait rien (SFA3 mips
        # 0x19A8F8 : D0.W = $C040(A5).L >> 8, 6 sites par module)
        if MEMSHIFT_ON and m in ('sra','srl') and 1<=ins.sa<=8 and SM.get(ins.rt) and SM[ins.rt][0]=='L' and st.get(ins.rt) is None:
            st[ins.rd]=Sym('memshift',(SM[ins.rt],m,ins.sa)); memread.pop(ins.rd,None); lui.pop(ins.rd,None); i+=1; continue
        if m in ('dsll32','dsra32','sll','sra'):
            # (HANDOFF §137) la lecture memoire ne suit QUE les extensions de signe (dsll32/dsra32, sll/sra de 16 ou 24) :
            # un vrai decalage ('lh D8 ; sll 3 ; sh D8', Hyper mips 0x5A41C) faisait emettre 'MOVE.W x,x' (decalage perdu)
            if ins.rt in memread and (not SHIFT_MR_FIX or m in ('dsll32','dsra32') or ins.sa in (16,24)):
                memread[ins.rd]=memread[ins.rt]
            elif SHIFT_MR_FIX and ins.rt in memread: SHIFT_MR_N[0]+=1
            # (HANDOFF §118) lecture ABSOLUE propagee par l'extension de signe (comparaison 'drapeaux exacts' sur
            # la boite aux lettres QSound $61801F, recompilateur recent : Upper restait muet)
            if m in ('dsll32','dsra32') and absread.get(ins.rt): absread[ins.rd]=absread[ins.rt]
            # dsll32/dsra32 = extension de signe (le recompilateur ne s'en sert que pour
            # ca) : la valeur symbolique suit. Un 'sll' simple est une multiplication.
            if m in ('dsll32','dsra32'):
                st[ins.rd]=st.get(ins.rt)
                if ins.rt in ldsize: ldsize[ins.rd]=ldsize[ins.rt]
            elif m=='sll' and ins.sa in (1,2) and st.get(ins.rt) and st[ins.rt].kind=='reg68' \
                 and st[ins.rt].val and st[ins.rt].val[0]=='D':
                st[ins.rd]=Sym('scaled',(st[ins.rt].val[1], 1<<ins.sa))   # index de table (ou LSL #1/#2)
            elif (TBLMASK_ON and m=='sll' and ins.sa in (1,2) and st.get(ins.rt) and st[ins.rt].kind=='arithi'
                  and st[ins.rt].val[0]=='and' and st[ins.rt].val[2] in (1,3,7,15,31,63,127,255)):
                # (HANDOFF §132) index de table masque puis double/quadruple : (Dn & k) x 2 / x 4
                st[ins.rd]=Sym('maskscaled',(st[ins.rt].val[1],st[ins.rt].val[2],1<<ins.sa))
            elif m in ('sll','sra') and 1<=ins.sa<=(31 if BIGSHIFT_ON else 8) and st.get(ins.rt) and st[ins.rt].kind=='reg68' \
                 and st[ins.rt].val and st[ins.rt].val[0]=='D':
                st[ins.rd]=Sym('shift',(m, st[ins.rt].val[1], ins.sa))
            else: st[ins.rd]=None
            i+=1; continue
        # andi rY, rX, masque-de-bit  ou rX vient de [A5+disp]  -> BTST #bit
        if m=='andi' and ins.imm in (0xff,0xffff):
            szz='B' if ins.imm==0xff else 'W'
            b=st.get(ins.rs); mr=SM.get(ins.rs)
            base=None
            if b and b.kind=='zx' and b.val[1]==szz: base=b.val[0]
            elif mr and mr[0]==szz: base=('mem',)+mr
            elif SAB.get(ins.rs) and SAB[ins.rs][0]==szz:     # (HANDOFF §78) CMPI #k,abs.L
                base=('abs',szz,SAB[ins.rs][1])
            elif b and b.kind=='reg68' and b.val and b.val[0]=='D' and SL.get(ins.rs)==szz:
                base=('D',b.val[1])
            if base is not None:
                st[ins.rt]=Sym('zx',(base,szz)); lui.pop(ins.rt,None)
                if mr: memread[ins.rt]=mr
                i+=1; continue
        if m=='ori' and ins.rs in lui:               # lui + ori = valeur 32 bits (comme lui + addiu)
            st[ins.rt]=Sym('const', ((lui[ins.rs]<<16) | ins.imm) & 0xffffffff)
            lui.pop(ins.rt,None); i+=1; continue
        if m in ('andi','ori','xori'):
            b=st.get(ins.rs)
            # (HANDOFF §138) idem pour ANDI/ORI/EORI en place indexe (SFA3 arcade $023288 'ANDI.B #$7F,(A0,D0.W)' perdu)
            if (IDXRMW_ON and b is None and SI.get(ins.rs) and SI[ins.rs][0] in ('B','W')
                    and ins.imm!=SZMASK[SI[ins.rs][0]] and _idx_rmw_store(ins_list,i,ins.rt)):
                st[ins.rt]=Sym('idxrmw',({'andi':'and','ori':'or','xori':'xor'}[m],ins.imm,SI[ins.rs]))
                lui.pop(ins.rt,None); i+=1; continue
            # (HANDOFF §137) deux masques successifs ('andi x,Dn,$FFFF ; andi x,x,$FFFF') : masque combine
            if ANDAND_ON and m=='andi' and b and b.kind=='arithi' and b.val[0]=='and':
                st[ins.rt]=Sym('arithi',('and', b.val[1], b.val[2] & ins.imm)); lui.pop(ins.rt,None); i+=1; continue
            if b and b.kind=='reg68' and b.val and b.val[0]=='D' and ins.rs not in memread:
                st[ins.rt]=Sym('arithi',({'andi':'and','ori':'or','xori':'xor'}[m], b.val[1], ins.imm))
                lui.pop(ins.rt,None); i+=1; continue
        if m in ('ori','xori') and SM.get(ins.rs):
            st[ins.rt]=Sym('memlogic',({'ori':'or','xori':'xor'}[m], ins.imm, SM[ins.rs]))
            memread.pop(ins.rt,None); lui.pop(ins.rt,None); i+=1; continue
        if m=='andi' and SM.get(ins.rs) and not (ins.imm and (ins.imm&(ins.imm-1))==0):
            st[ins.rt]=Sym('memlogic',('and', ins.imm, SM[ins.rs]))   # masque d'effacement (BCLR/ANDI)
            memread.pop(ins.rt,None); lui.pop(ins.rt,None); i+=1; continue
        if m=='andi' and SM.get(ins.rs):
            mask=ins.imm
            if mask and (mask & (mask-1))==0:
                bd,bb=btst_target(SM[ins.rs][0], SM[ins.rs][1], mask.bit_length()-1)
                pend=('btst', bb, bd, SM[ins.rs][2])
                st[ins.rt]=Sym('memlogic',('and', mask, SM[ins.rs]))   # (HANDOFF §78) si reecrit : ANDI en place
                memread.pop(ins.rt,None); lui.pop(ins.rt,None)
            i+=1; continue

        # (HANDOFF §132) registre D <op> valeur LONGUE de table ('lw x,T(Dk) ; or y,Dn,x ; sw y,Dn') : OR/AND/ADD.L
        # (SFA3 mips 0x1F3158 : 'OR.L T(PC,D8.W),D2' perdu)
        if TBLOP_ON and m in ('or','and','addu') and ins.rd!=0:
            _x,_y=st.get(ins.rs),st.get(ins.rt)
            for _p,_q in ((_x,_y),(_y,_x)):
                if _p and _q and _p.kind=='reg68' and _p.val and _p.val[0]=='D' and _q.kind=='tblent':
                    st[ins.rd]=Sym('tblop',(m,_p.val[1])+tuple(_q.val)); lui.pop(ins.rd,None); memread.pop(ins.rd,None); break
            else: _p=None
            if _p is not None: i+=1; continue
        # (HANDOFF §132) MULTIPLICATION du R5900 a trois operandes ('mult rd,rs,rt' : rd = LO) = MULS.W / MULU.W du 68K.
        # N'etait pas suivie : rd gardait sa valeur symbolique d'AVANT (SFA3 mips 0x107898 : 'MOVE.L D2,D0' emis au lieu
        # de 'MULS.W D2,D0', silencieusement). Operandes inconnus -> rd invalide (chute visible, plus de valeur perimee).
        if m in ('mult','multu') and ((ins.w>>11)&31):
            _rd=(ins.w>>11)&31
            # (HANDOFF §137) operande zero-etendu ('andi x,Dn,$FFFF') = Dn.W non signe -> MULU.W (Hyper mips 0x51EC0)
            def _u(sy):
                if sy and sy.kind=='arithi' and sy.val[0]=='and' and sy.val[2]==0xffff: return ('D',sy.val[1])
                if sy and sy.kind=='zx' and sy.val[1]=='W' and sy.val[0][0]=='D': return sy.val[0]   # (§137) andi $FFFF : non signe
                return None
            _a=_operand(st.get(ins.rs),SM.get(ins.rs)) or _u(st.get(ins.rs)); _b=_operand(st.get(ins.rt),SM.get(ins.rt)) or _u(st.get(ins.rt))
            _mm=m
            if _u(st.get(ins.rs)) and _u(st.get(ins.rt)): _mm='multu'      # deux operandes non signes : MULU
            st[_rd]=Sym('mul',(_mm,_a,_b)) if (MULS_ON and _a and _b) else None
            for _d in (lui,memread,ldsize,idxread,absread): _d.pop(_rd,None)
            i+=1; continue
        # arithmetique registre-registre : les deux operandes viennent de slots D
        if m=='subu' and ins.rs==0 and SM.get(ins.rt):
            st[ins.rd]=Sym('memneg', SM[ins.rt]); lui.pop(ins.rd,None); i+=1; continue
        if m=='subu' and ins.rs==0:
            b=st.get(ins.rt)
            if b and b.kind=='reg68' and b.val and b.val[0]=='D':
                st[ins.rd]=Sym('neg', b.val[1]); lui.pop(ins.rd,None); i+=1; continue
        if m=='subu' and ins.rs!=0:
            ef=exact_flags(ins_list, i)
            if ef:
                size,ab,resw,endva=ef
                dst=_operand(st.get(ins.rs),SM.get(ins.rs)); src=_operand(st.get(ins.rt),SM.get(ins.rt))
                if dst is None and absread.get(ins.rs) and st.get(ins.rs) is None: dst=('abs',)+tuple(absread[ins.rs])   # (§118)
                if src is None and absread.get(ins.rt) and st.get(ins.rt) is None: src=('abs',)+tuple(absread[ins.rt])
                if src is None and SI.get(ins.rt) and st.get(ins.rt) is None and SI[ins.rt][0]==size:   # (§124) d8(An,Dn)
                    src=('idx',)+tuple(SI[ins.rt])
                # (HANDOFF §126) constante formee par un 'lui' SEUL (mot bas nul : 'lui s2,5' = #$50000) : Vega restait
                # accroche au grillage (Upper mips 0x383710, 'CMPI.L #$50000,$40(A6) ; BGE' perdu -> BRA/BPL parasites)
                if src is None and LUI_IMM and st.get(ins.rt) is None and ins.rt in lui:
                    src=('imm',(lui[ins.rt]<<16)&0xffffffff); LUI_IMM_N[0]+=1
                if not (dst and src):
                    # (HANDOFF §126) AUDIT : bloc 'drapeaux exacts' reconnu mais operande inconnu -> comparaison perdue
                    _d=lambda r_: (st.get(r_).kind if st.get(r_) else None, r_ in lui, bool(SM.get(r_)), bool(absread.get(r_)), bool(SI.get(r_)))
                    EXACT_MISS.append((ins.va, size, None if dst else _d(ins.rs), None if src else _d(ins.rt)))
                if dst and src:
                    pend=('cmp',dst,src,size,True)         # True = drapeaux exacts (signe = N^V)
                    absorbed.update(ab); keep_pend.update(resw+[endva])
                    exact_blk=(ins.va,endva,dst,src,size,i,ins.rd)
        # BIT DYNAMIQUE (BTST/BSET/BCLR/BCHG Dn,<ea>) : le recompilateur construit le
        # masque '1 << (Dn & 7)' (octet memoire) ou '1 << (Dn & 31)' (registre) avec sllv,
        # l'inverse avec nor (BCLR), puis and/or/xor avec l'operande
        if m=='sllv':
            amt=st.get(ins.rs); one=st.get(ins.rt)
            if one and one.kind=='imm' and one.val==1 and amt and amt.kind=='arithi' \
               and amt.val[0]=='and' and amt.val[2] in (7,31):
                st[ins.rd]=Sym('bitn',(amt.val[1],amt.val[2])); lui.pop(ins.rd,None); i+=1; continue
        # (HANDOFF §80) 'nor rd,rs,zero' sur un registre D ou une lecture memoire = NOT (front montant de Start :
        # ROM $45AC 'MOVE.B $61,D0 ; NOT.B D0 ; AND.B $60,D0' perdait son NOT)
        if m=='nor' and ins.rt==0 and ins.rd!=0:
            b=st.get(ins.rs)
            if b and b.kind=='reg68' and b.val and b.val[0]=='D':
                st[ins.rd]=Sym('notd', b.val[1]); lui.pop(ins.rd,None); memread.pop(ins.rd,None); i+=1; continue
            if SM.get(ins.rs) and not (b and b.kind=='bitn'):
                st[ins.rd]=Sym('memnot', SM[ins.rs]); lui.pop(ins.rd,None); memread.pop(ins.rd,None); i+=1; continue
        if m=='nor' and ins.rt==0 and st.get(ins.rs) and st[ins.rs].kind=='bitn':
            st[ins.rd]=Sym('bitn_inv',st[ins.rs].val); lui.pop(ins.rd,None); i+=1; continue
        if m=='or':
            bs=bswap16_of(ins_list, i)
            if bs is not None:
                st[ins.rd]=Sym('bswap16',bs); lui.pop(ins.rd,None); i+=1; continue
            ro=rot_of(ins_list, i)
            if ro is not None:
                st[ins.rd]=Sym('rot',ro); lui.pop(ins.rd,None); i+=1; continue
        if m=='andi' and st.get(ins.rs) and st[ins.rs].kind in ('rot','bswap16'):
            st[ins.rt]=st[ins.rs]; lui.pop(ins.rt,None); i+=1; continue
        # (HANDOFF §138) ADD/SUB entre DEUX lectures memoire, reecrit sur la premiere : 'm1 += m2'
        # (Upper mips 0x1EC4F0 : '$2A4(A5) += $44(A6)', position de defilement, perdu)
        if (IDXRMW_ON and m in ('addu','subu') and ins.rd!=0 and SM.get(ins.rs) and SM.get(ins.rt)
                and SM[ins.rs][0]==SM[ins.rt][0] and SM[ins.rs]!=SM[ins.rt] and _idx_rmw_store(ins_list,i,ins.rd,lim=3,sz=('sb','sh','sw'))):
            st[ins.rd]=Sym('mem2',(m, SM[ins.rs], SM[ins.rt])); memread.pop(ins.rd,None); lui.pop(ins.rd,None)
            i+=1; continue
        if m in ('and','or','xor'):
            # (HANDOFF §77) mot a octets inverses combine a la memoire : '$14(A5) |= swap16(D1)' (champ
            # de bits range octet par octet, mips 0x1848D0) -> ROR.W #8,Dk ; OR.W Dk,mem ; ROR.W #8,Dk
            bsm=None
            for r1,r2 in ((ins.rs,ins.rt),(ins.rt,ins.rs)):
                b1=st.get(r1)
                if b1 and b1.kind=='bswap16' and b1.val and b1.val[0]=='D' and SM.get(r2) and SM[r2][0]=='W':
                    bsm=Sym('bsmem',(m,b1.val[1],SM[r2])); break
            if bsm is not None:
                st[ins.rd]=bsm; lui.pop(ins.rd,None); i+=1; continue
            if SM.get(ins.rs) and SM.get(ins.rt) and SM[ins.rs][0]==SM[ins.rt][0] and ins.rd!=0:
                # (HANDOFF §78) operation logique entre DEUX lectures memoire ('$C008 |= $C004')
                st[ins.rd]=Sym('mem2',(m, SM[ins.rs], SM[ins.rt])); memread.pop(ins.rd,None); lui.pop(ins.rd,None)
                i+=1; continue
            ml=None                                  # (HANDOFF §78) masque dans un registre ('addiu -2 ; and')
            for r1,r2 in ((ins.rs,ins.rt),(ins.rt,ins.rs)):
                b1=st.get(r1)
                if b1 and b1.kind=='imm' and SM.get(r2) and ins.rd!=0:
                    ml=Sym('memlogic',(m, b1.val & SZMASK[SM[r2][0]], SM[r2])); break
            if ml is not None:
                st[ins.rd]=ml; memread.pop(ins.rd,None); lui.pop(ins.rd,None); i+=1; continue
            done=False
            for r1,r2 in ((ins.rs,ins.rt),(ins.rt,ins.rs)):
                bn=st.get(r1)
                if not (bn and bn.kind in ('bitn','bitn_inv')): continue
                op={('and','bitn'):'btst',('or','bitn'):'bset',('xor','bitn'):'bchg',
                    ('and','bitn_inv'):'bclr'}.get((m,bn.kind))
                if op is None: break
                dn,mod=bn.val; o=st.get(r2); tgt=None
                if mod==7 and SM.get(r2) and SM[r2][0]=='B': tgt=('mem',)+SM[r2]
                elif mod==31 and o and o.kind=='reg68' and o.val and o.val[0]=='D': tgt=('D',o.val[1])
                if tgt: st[ins.rd]=Sym('dynbit',(op,dn,tgt)); lui.pop(ins.rd,None); done=True
                break
            if done: i+=1; continue
        # registre OP valeur de table indexee :  ADDA.W d8(An,Xn),Am  /  ADD.x d8(An,Xn),Dn
        if m in ('addu','subu','and','or'):
            done=False
            for rx,ry in ((ins.rs,ins.rt),(ins.rt,ins.rs)):
                ix=SI.get(ry); x=st.get(rx)
                if not ix or (m=='subu' and rx!=ins.rs): continue
                if x and x.kind=='an' and x.val[1]==0 and m=='addu' and ix[0]=='W':
                    st[ins.rd]=Sym('adda_idx',(x.val[0],ix)); done=True; break
                if x and x.kind=='reg68' and x.val and x.val[0]=='D' and SL.get(rx)==ix[0] \
                   and (ix[0]!='L' or MEMMODE!='cps2'):
                    st[ins.rd]=Sym('dop_idx',(x.val[1],m,ix)); done=True; break
            if done: lui.pop(ins.rd,None); i+=1; continue
        # (HANDOFF §132) table INDEXEE PAR UN CHAMP MEMOIRE signe ('lb x,d(An) ; ext ; addu y,T,x ; lb z,0(y)') : Upper
        # mips 0x3AE5D4 / 0x3B4E58 (9 sites, D0 = T[$1FE(A6)]) - rien n'etait emis
        if TBLMASK_ON and m=='addu':
            for _c,_r in ((st.get(ins.rs),ins.rt),(st.get(ins.rt),ins.rs)):
                if (_c and _c.kind=='const' and isinstance(_c.val,int) and addr_to_68k(_c.val) is not None and st.get(_r)
                        and st[_r].kind=='maskscaled'):
                    st[ins.rd]=Sym('tblmask',(_c.val,)+tuple(st[_r].val)); lui.pop(ins.rd,None); memread.pop(ins.rd,None); break
            else: _c=None
            if _c is not None: i+=1; continue
        if TBLMASK_ON and m in ('lb','lh','lw') and ins.simm==0 and st.get(ins.rs) and st[ins.rs].kind=='tblmask':
            _tb,_dn,_mk,_sc=st[ins.rs].val; _sz={'lb':'B','lh':'W','lw':'L'}[m]
            DATA_TABLES[_tb]=_sz
            st[ins.rt]=Sym('tblmaskval',(_tb,_dn,_mk,_sc,_sz)); lui.pop(ins.rt,None); memread.pop(ins.rt,None); i+=1; continue
        if TBLMEM_ON and m=='addu':
            for _c,_r in ((st.get(ins.rs),ins.rt),(st.get(ins.rt),ins.rs)):
                if (_c and _c.kind=='const' and isinstance(_c.val,int) and addr_to_68k(_c.val) is not None and st.get(_r) is None
                        and SM.get(_r) and SM[_r][0] in ('B','W')):
                    st[ins.rd]=Sym('tblmem',(_c.val,SM[_r])); lui.pop(ins.rd,None); memread.pop(ins.rd,None); break
            else: _c=None
            if _c is not None: i+=1; continue
        if TBLMEM_ON and m in ('lb','lh') and ins.simm==0 and st.get(ins.rs) and st[ins.rs].kind=='tblmem':
            _tb,_mr=st[ins.rs].val; _sz='B' if m=='lb' else 'W'
            DATA_TABLES[_tb]=_sz
            st[ins.rt]=Sym('tblmemval',(_tb,_mr,_sz)); lui.pop(ins.rt,None); memread.pop(ins.rt,None); i+=1; continue
        if m in ARITH:
            sa=st.get(ins.rs); sb=st.get(ins.rt)
            if (sa and sa.kind=='reg68' and sa.val and sa.val[0]=='D'
                and sb and sb.kind=='reg68' and sb.val and sb.val[0]=='D'):
                st[ins.rd]=Sym('arith',(m, sa.val[1], sb.val[1]))
                lui.pop(ins.rd,None); i+=1; continue
            if m in ('addu','daddu'):
                # x + (-imm) avec -imm construit par lui+ori : c'est une soustraction (CMPI/SUBI .L)
                for mr_r,other,oreg in ((ins.rs,sb,ins.rt),(ins.rt,sa,ins.rs)):
                    mr=SM.get(mr_r)
                    if other is None and oreg in lui and oreg!=0:     # (HANDOFF §78) constante chargee par un lui seul
                        other=Sym('const',(lui[oreg]<<16)&0xffffffff)
                    if mr and mr[0]=='L' and other and other.kind=='const':
                        st[ins.rd]=Sym('sub',(('mem',)+mr, ('imm',(-other.val)&0xffffffff), 'L'))
                        lui.pop(ins.rd,None); break
                else: mr=None
                if st.get(ins.rd) is not None and st[ins.rd].kind=='sub': i+=1; continue
                for x,y in ((sa,sb),(sb,sa)):
                    if x and x.kind=='const' and y and y.kind=='scaled':
                        st[ins.rd]=Sym('tblidx',(x.val,)+y.val); lui.pop(ins.rd,None); break
                    if x and x.kind=='const' and y and y.kind=='reg68' and y.val and y.val[0]=='D':
                        st[ins.rd]=Sym('tblidx',(x.val, y.val[1], 1)); lui.pop(ins.rd,None); break
                else: x=None
                if x is not None and st.get(ins.rd) and st[ins.rd].kind=='tblidx':
                    i+=1; continue
            if m in ('addu','subu','and','or'):
                # Dn OP memoire -> resultat destine a Dn :  OP.x d16(An),Dn
                if sa and sa.kind=='reg68' and sa.val and sa.val[0]=='D' and SM.get(ins.rt):
                    st[ins.rd]=Sym('dmem',(sa.val[1], m, SM[ins.rt])); lui.pop(ins.rd,None); i+=1; continue
            if m in ('addu','subu','and','or','xor'):
                done=False
                for x_mr,y,commut in ((SM.get(ins.rs),sb,True),(SM.get(ins.rt),sa,m!='subu')):
                    if x_mr and commut and y and y.kind=='reg68' and y.val and y.val[0]=='D':
                        st[ins.rd]=Sym('memarith',(x_mr,m,y.val[1])); lui.pop(ins.rd,None); done=True; break
                if done: i+=1; continue
            if m=='subu' and sa and sa.kind=='an' and sa.val[1]==0:
                nx=ins_list[i+1] if i+1<len(ins_list) else None
                szz='W' if (nx is not None and nx.m=='dsll32' and nx.sa==16) else 'L'
                src=_operand(sb, SM.get(ins.rt))
                st[ins.rd]=Sym('sub',(('A',sa.val[0]),src,szz)) if src else None
                lui.pop(ins.rd,None); i+=1; continue
            dst=None; dsz=None
            if m=='subu' and sa and sa.kind=='reg68' and sa.val and sa.val[0]=='D' and SL.get(ins.rs):
                dst=('D',sa.val[1]); dsz=SL[ins.rs]
            elif m=='subu' and SM.get(ins.rs) and (sa is None or sa.kind not in ('zx',)):
                dst=('mem',)+SM[ins.rs]; dsz=SM[ins.rs][0]
            if dst is not None and full_flags_block(ins_list, i, ins.rd):
                # x - y (CMP/SUB), forme du recompilateur recent (Hyper) : registres alloues
                src=None
                if sb and sb.kind=='imm': src=('imm',sb.val & SZMASK[dsz])
                elif sb and sb.kind=='const': src=('imm',sb.val & SZMASK[dsz])
                elif sb and sb.kind=='reg68' and sb.val and sb.val[0]=='D': src=('D',sb.val[1])
                elif SM.get(ins.rt) and SM[ins.rt][0]==dsz: src=('mem',)+SM[ins.rt]
                if src:
                    st[ins.rd]=Sym('sub',(dst,src,dsz)); lui.pop(ins.rd,None)
                    fb=full_flags_block(ins_list, i, ins.rd)
                    if fb:
                        ab,negsw,resw=fb; absorbed.update(ab)
                        if negsw: keep_pend.add(negsw); signed_res.add(resw)
                    i+=1; continue
            if m=='subu' and sa and sa.kind=='zx':
                base,szz=sa.val; src=None
                if sb and sb.kind=='zx' and sb.val[1]==szz: src=sb.val[0]
                elif sb and sb.kind=='reg68' and sb.val and sb.val[0]=='D': src=('D',sb.val[1])
                elif sb and sb.kind=='imm': src=('imm',sb.val)
                elif SM.get(ins.rt) and SM[ins.rt][0]==szz: src=('mem',)+SM[ins.rt]
                st[ins.rd]=Sym('sub',(base,src,szz)) if src else None
                lui.pop(ins.rd,None); i+=1; continue
            if m in ('addu','daddu'):
                for x,y,ry in ((sa,sb,ins.rt),(sb,sa,ins.rs)):
                    if x and x.kind=='an' and x.val[1]==0 and y and y.kind=='tblval' and y.val[2]=='W':
                        # (HANDOFF §83) ADDA.W T(PC,Dk.W),An : choix de la variante de palette de « ROUND »
                        # (mips 0xB3314, table $598BF0 indexee par $100(A5)) - etait perdu (variante 0 orange)
                        st[ins.rd]=Sym('an_tbl',(x.val[0], y.val[0], y.val[1])); lui.pop(ins.rd,None); break
                    if D8HI_ON and x and x.kind=='an' and x.val[1]==0 and y and y.kind=='dhi':
                        st[ins.rd]=Sym('an_dhi',(x.val[0], y.val)); lui.pop(ins.rd,None); break
                    if (x and x.kind=='an' and x.val[1]==0 and y and y.kind=='reg68'
                        and y.val and y.val[0]=='D' and SL.get(ry) in ('W','L')):
                        st[ins.rd]=Sym('an_d',(x.val[0], y.val[1], SL[ry])); lui.pop(ins.rd,None); break
                    # (HANDOFF §85) Dn + constante 32 bits chargee par un 'lui' SEUL : ADDI.L #$16000000,D1 des
                    # constructeurs d'objets (code de tuile +$1600, mips 0xFE6F8 : portraits, bandes de l'ecran
                    # de presentation) - etait perdu (10 sites)
                    yc=y if (y and y.kind=='const') else (Sym('const',(lui[ry]<<16)&0xffffffff) if (y is None and ry in lui and ry!=0) else None)
                    if x and x.kind=='reg68' and x.val and x.val[0]=='D' and yc is not None and isinstance(yc.val,int):
                        st[ins.rd]=Sym('arithi',('add', x.val[1], yc.val & 0xffffffff)); lui.pop(ins.rd,None); break
                else:
                    st[ins.rd]=None; lui.pop(ins.rd,None)
                i+=1; continue
            if m in ('and','or','xor'):
                # (HANDOFF §132) 'and rd,rs,zero' = 0 (Upper mips 0x14FF20 : CLR du mot perdu) ; 'xor/or rd,rs,zero' = copie
                if LOGIC_ZERO and 0 in (ins.rs,ins.rt):
                    _o=ins.rs or ins.rt
                    st[ins.rd]=Sym('imm',0) if (m=='and' or _o==0) else st.get(_o)
                    lui.pop(ins.rd,None); LOGIC_ZERO_N[0]+=1; i+=1; continue
                for x,y,ry in ((sa,sb,ins.rt),(sb,sa,ins.rs)):
                    # (HANDOFF §132) constante 'lui' SEULE (EORI.L #$10000,D8 : Upper mips 0x259220)
                    if LOGIC_ZERO and y is None and ry in lui and ry!=0: y=Sym('const',(lui[ry]<<16)&0xffffffff)
                    # (HANDOFF §83) masque 32 bits 'lui ; ori' ('const') : ANDI.L #$F000F000,D4 de la copie de
                    # palette (mips 0xB3384) etait perdu -> anciennes couleurs melangees (bande de « ROUND » verte)
                    if (x and x.kind=='reg68' and x.val and x.val[0]=='D' and y and
                        (y.kind=='imm' or (y.kind=='const' and isinstance(y.val,int) and _masque_ok(y.val)))):
                        st[ins.rd]=Sym('arithi',(m, x.val[1], y.val & 0xffffffff)); lui.pop(ins.rd,None); break
                else:
                    st[ins.rd]=None; lui.pop(ins.rd,None)
                i+=1; continue
            st[ins.rd]=None; lui.pop(ins.rd,None); i+=1; continue
        # jal <cible>, ou jalr vers une adresse CONSTANTE (lui+addiu) -> JSR/JMP (xxx).L
        # (les 'stubs' de ro3 sont des veneers 68K 'JSR x ; JMP y' recompiles ainsi)
        tgt=None
        if m=='jal': tgt=ins.tgt
        elif m=='jalr':
            c=st.get(ins.rs)
            if c and c.kind=='const': tgt=c.val
        if tgt is not None and tgt in AIDES_RECOMP and MEMMODE=='cps2':
            # (HANDOFF §83) AIDES DU RECOMPILATEUR (hors du code traduit, talons RTS jusqu'ici) : MOVEM a masque,
            # ANDI #imm,CCR et ABCD octet par octet. Le chrono s'affichait « 00 » (conversion BCD $BA54/$BA58 vide)
            ws_,mn_=aide_recomp(AIDES_RECOMP[tgt], st)
            if ws_ is not None:
                tr=tail_return(ins_list, i)
                if tr is not None: no_rts.add(tr)
                else:
                    tb=tail_branch(ins_list, i)
                    if tb is not None: tr=tb; absorbed.add(tb); tail_abs.add(tb)
                if tr is not None: ws_=ws_+[RTS]; mn_+=" ; RTS  [appel terminal]"
                out.append((ins.va,mn_,ws_))
                for r in (2,3): st.pop(r,None)
                i+=1; continue
        if tgt is not None:
            tr=tail_return(ins_list, i)
            if tr is not None: no_rts.add(tr)
            else:
                tb=tail_branch(ins_list, i)
                if tb is not None: tr=tb; absorbed.add(tb); tail_abs.add(tb)
            k=mips_to_68k(tgt - RUNTIME_BASE)
            name,enc=("JMP",enc_jmp_abs) if tr is not None else ("JSR",enc_jsr_abs)
            if tr is not None and (tgt - RUNTIME_BASE) in empty_funcs(buf):
                # appel TERMINAL vers une fonction 'jr ra' = RTS partage de la ROM (HANDOFF §47)
                out.append((ins.va,"RTS  [appel terminal vers un RTS partage, mips %08x]"%tgt,[RTS]))
                for r in (2,3): st.pop(r,None)
                i+=1; continue
            if k is not None:
                out.append((ins.va,"%s $%06x.L  [mips %08x]"%(name,k,tgt), enc(k)))
            else:
                out.append((ins.va,"%s ???  [cible %08x -> fichier %07x, hors carte]"%(
                    name, tgt, tgt-RUNTIME_BASE), enc(0)))
            for r in (2,3): st.pop(r,None)
            i+=1; continue
        # APPEL INDIRECT PAR REGISTRE D'ADRESSE (HANDOFF §70) : 'lw r,An ; jalr r' = JSR (An) (JMP (An) si
        # terminal). N'etait pas emis du tout : le gestionnaire d'objets de la ROM ($336F6, MOVEA.L
        # table(PC,D0.W),A0 ; JSR (A0)) n'appelait aucune routine d'objet (carte du monde figee).
        if m=='jalr':
            j=_producer(ins_list, i, ins.rs, 8)
            if j is not None and ins_list[j].m=='lw' and slot_name(ins_list[j].simm & 0xffff) \
               and slot_name(ins_list[j].simm & 0xffff)[0]=='A':
                n=slot_name(ins_list[j].simm & 0xffff)[1]
                tr=tail_return(ins_list, i)
                if tr is not None: no_rts_ind.add(tr)
                else:
                    tb=tail_branch(ins_list, i)
                    if tb is not None: tr=tb; absorbed.add(tb); tail_abs.add(tb)
                # (HANDOFF §76) adresse de code PS2 en memoire -> la notre, a l'usage
                cc=[0x4eb9, CODE_CONV[n]>>16, CODE_CONV[n]&0xffff] if CODE_CONV else []
                if tr is not None: out.append((ins.va,"JMP (A%d)"%n,cc+[0x4ed0|n]))
                else: out.append((ins.va,"JSR (A%d)"%n,cc+[0x4e90|n]))
                for r in (2,3): st.pop(r,None)
                i+=1; continue
        # jalr vers une adresse CALCULEE (table de sauts : 'lui/addiu table ; addu index ;
        # lw ; jalr'). S'il est terminal, c'est un JMP indirect 68K (JMP d(PC,Dn) / JMP (An)) :
        # le 'jr ra' qui suit n'est PAS un RTS. Le saut lui-meme n'est pas encore
        # traduit (il faut la table) : on n'emet rien pour lui, il reste compte comme manque.
        if m=='jalr' and st.get(ins.rs) and st[ins.rs].kind=='tblent':
            tbl,ix,scale=st[ins.rs].val
            # Aiguillage d'etat Capcom (1 558 dans la ROM, 97 % sous cette forme exacte) :
            #   MOVE.W tbl(PC,D0.W),D1 ; JMP tbl(PC,D1.W) ; tbl: dc.w h0-tbl, h1-tbl...
            # Le recompilateur a remplace la lecture de table par une COPIE D0->D1 et
            # un saut par SA table de pointeurs. On remet la forme d'origine.
            src=None; name="T_%06x"%tbl
            # (HANDOFF §102) echelle 4 ('sll 2' sur l'index) : index BRUT (code ajoute par le portage, ex. aiguillage
            # des modes par l'octet $C001) et non deja double comme chez Capcom ('sll 1') -> doubler dans Dix
            # (registre d'arrivee de la lecture, ecrase de toute facon) avant la lecture de la table de mots
            for k in range(len(out)-1, max(-1,len(out)-6), -1):
                mn=out[k][1]
                if mn.startswith("MOVE.W D") and mn.endswith(",D%d"%ix):
                    src=int(mn.split()[1].split(',')[0][1:])
                    # remplacee SUR PLACE (a l'adresse de la copie), pas deplacee au jalr :
                    # sinon la copie apparaissait comme 'manquee' au recensement
                    if scale==4:                      # elements separes : l'assembleur reconnait la lecture de table
                        va_k=out[k][0]
                        out[k:k+1]=[(va_k,"MOVE.W D%d,D%d"%(src,ix),[0x3000|(ix<<9)|src]),
                                    (va_k,"ADD.W D%d,D%d  [index brut double]"%(ix,ix),[0xd040|(ix<<9)|ix]),
                                    (va_k,"MOVE.W %s(PC,D%d.W),D%d"%(name,ix,ix),[0x303b|((ix&7)<<9), 0x0006|(ix<<12)])]
                    elif scale==1 and SW_X4:          # (HANDOFF §126) index deja x4 (table de BRA.W d'origine)
                        va_k=out[k][0]; SW_X4_N[0]+=1
                        out[k:k+1]=[(va_k,"MOVE.W D%d,D%d"%(src,ix),[0x3000|(ix<<9)|src]),
                                    (va_k,"LSR.W #1,D%d  [index deja x4 : moitie]"%ix,[0xe248|ix]),
                                    (va_k,"MOVE.W %s(PC,D%d.W),D%d"%(name,ix,ix),[0x303b|((ix&7)<<9), 0x0006|(ix<<12)])]
                    else:
                        out[k]=(out[k][0],"MOVE.W %s(PC,D%d.W),D%d"%(name,src,ix),[0x323b|0, 0x0006 | (src<<12)])
                    break
            if src is None:
                # pas de copie Dn->Dm devant : forme Capcom sur le MEME registre (ROM $40AC :
                # MOVE.W tbl(PC,D0.W),D0 ; JSR tbl(PC,D0.W)) - le recompilateur a reduit la lecture a
                # 'MOVE.W D0,D0', sans trace. On remet la lecture de table sur l'index lui-meme.
                if scale==4:
                    out.append((ins.va,"ADD.W D%d,D%d  [index brut double]"%(ix,ix),[0xd040|(ix<<9)|ix]))
                    out.append((ins.va,"MOVE.W %s(PC,D%d.W),D%d"%(name,ix,ix),[0x303b|((ix&7)<<9), 0x0006|(ix<<12)]))
                elif scale==1 and SW_X4:
                    # (HANDOFF §126) index DEJA multiplie par 4 dans le registre 68K (forme d'origine : table de BRA.W,
                    # 'LSL.W #2,D0 ; JSR T(PC,D0.W)', Upper mips 0x1003F0) : la table de mots reconstruite veut 2*i.
                    # Le registre est ecrase par la lecture de toute facon (Upper perso 21 : D0 = 8 -> 5e entree, plantage)
                    SW_X4_N[0]+=1
                    out.append((ins.va,"LSR.W #1,D%d  [index deja x4 : moitie]"%ix,[0xe248|ix]))
                    out.append((ins.va,"MOVE.W %s(PC,D%d.W),D%d"%(name,ix,ix),[0x303b|((ix&7)<<9), 0x0006|(ix<<12)]))
                else:
                    out.append((ins.va,"MOVE.W %s(PC,D%d.W),D%d"%(name,ix,ix),[0x303b|((ix&7)<<9), 0x0006|(ix<<12)]))
            tr=tail_return(ins_list, i)
            tb=tail_branch(ins_list, i) if tr is None else None
            terminal = tr is not None or tb is not None
            # terminal -> JMP par table (la table suit le JMP) ; sinon -> JSR par table
            # (ROM : 323b 000c 4ebb 1008 4ef9 ... : la table suit l'instruction SUIVANTE)
            op = 0x4efb if terminal else 0x4ebb
            out.append((ins.va,"%s %s(PC,D%d.W)   [table de %d entrees]"%("JMP" if terminal else "JSR",name,ix,
                        len(TABLES.setdefault(tbl, read_jump_table(buf,tbl)))),
                        [op, 0x0002 | (ix<<12)]))
            if tr is not None: no_rts_ind.add(tr)
            if tb is not None: absorbed.add(tb); tail_abs.add(tb)
            for r in (2,3): st.pop(r,None)
            i+=1; continue
        if CDISP_ON and m=='jalr' and MEMMODE=='cps2':
            _cd=c_dispatch(ins_list, i)
            if _cd is not None:
                # (HANDOFF §140) table de LONGS du portage indexee par (champ >> k1) << k2 : forme Capcom
                # 'MOVE.W T(PC,Dt.W),Dt ; JSR T(PC,Dt.W)' sur un temporaire D7 sauve (aucun registre 68K touche)
                _tb,_an,_d,_sz,_k1,_k2=_cd; t_=7
                ws=[0x2f07]+enc_move_an_dn(_sz,_an,_d,t_)+([0x4887] if _sz=='B' else [])
                _sh=_k2-1-_k1                                          # (v >> k1) << (k2-1) : index de table de MOTS
                if _k1: ws+=[0x0247,(0xffff<<_k1)&0xffff]               # ANDI.W #~(2^k1-1),D7
                if _sh>0: ws+=[0xe148|((_sh&7)<<9)|t_]                  # LSL.W #sh,D7
                if _sh<0: ws+=[0xe040|(((-_sh)&7)<<9)|t_]               # ASR.W #-sh,D7
                out.append((ins.va,"MOVE.L D7,-(SP) ; MOVE.%s $%04x(A%d),D7 ; index (>>%d)<<%d  [aiguilleur C du portage]"%(_sz,_d&0xffff,_an,_k1,_k2-1),ws))
                name="T_%06x"%_tb
                out.append((ins.va,"MOVE.W %s(PC,D7.W),D7"%name,[0x303b|(7<<9), 0x0006|(7<<12)]))
                out.append((ins.va,"JSR %s(PC,D7.W)   [table de %d entrees]"%(name,len(TABLES.setdefault(_tb,read_jump_table(buf,_tb)))),
                            [0x4ebb, 0x0002|(7<<12)]))
                out.append((ins.va,"MOVEM.L (SP)+,D7",[0x4cdf,0x0080]))
                CDISP_N[0]+=1
                for r in (2,3): st.pop(r,None)
                i+=1; continue
        if m=='jalr':
            tr=tail_return(ins_list, i)
            if tr is not None: no_rts_ind.add(tr)
            else:
                tb=tail_branch(ins_list, i)
                if tb is not None: absorbed.add(tb); tail_abs.add(tb)
            for r in (2,3): st.pop(r,None)
            i+=1; continue
        # jr ra -> RTS  (sauf s'il clot un appel terminal deja traduit en JMP)
        if m=='jr' and ins.rs==31:
            # DRAPEAUX RENDUS A L'APPELANT (HANDOFF §66) : 'TST.B x(A5) ; RTS' (ROM $77A2, fin de fondu :
            # l'appelant fait BSR ; BNE). Si la derniere ecriture de RES avant ce retour est celle du test en
            # attente, aucun branchement local ne l'a emis : on l'emet devant le RTS.
            _n0=len(out)
            if flags_to_caller(i, pend, pend_va, absorbed, out):
                pend=None
                # (HANDOFF §126) test rendu place AVANT les restaurations de l'epilogue ('lq/ld ..,sp', 'addiu sp') :
                # un BRA d'un autre chemin vers l'epilogue tombait sur ce test (emis a l'adresse du 'jr ra') et perdait
                # ses propres drapeaux (Upper mips 0x251CC0 : 'BTST D1,D2 ; BRA fin ... fin: BTST D1,D3 ; RTS' ->
                # adversaire jamais vu battu, Adon sans fin en Arcade)
                _e=i
                while FTC_AVANT and _e>0 and ((ins_list[_e-1].m=='sll' and ins_list[_e-1].w==0) or
                        (ins_list[_e-1].m in ('lq','ld') and ins_list[_e-1].rs==29) or
                        (ins_list[_e-1].m=='addiu' and ins_list[_e-1].rs==29 and ins_list[_e-1].rt==29)): _e-=1
                if FTC_AVANT and _e>0 and any(ins_list[_x].va in br_targets for _x in range(_e,i+1)):
                    for _q in range(_n0,len(out)): out[_q]=(ins_list[_e-1].va,)+tuple(out[_q][1:])
                    FTC_AVANT_N[0]+=1
            # un retour absorbe qui est AUSSI la cible d'un branchement (epilogue partage : ROM
            # 'BEQ fin ... JMP (table) ; fin: RTS') doit rester un RTS, sinon le branchement tombe
            # sur l'instruction emise suivante (HANDOFF §64)
            if (ins.va in no_rts or ins.va in no_rts_ind) and epilogue_is_target(ins_list, i, br_targets):
                out.append((ins.va,"RTS  [retour partage : cible d'un branchement]",[RTS])); i+=1; continue
            if ins.va in no_rts: out.append((ins.va,"(retour absorbe par le JMP)",[]))
            elif ins.va in no_rts_ind: out.append((ins.va,"(retour absorbe par un JMP indirect)",[]))
            else: out.append((ins.va,"RTS",[RTS]))
            i+=1; continue
        # (HANDOFF §73) test de SIGNE d'une valeur tout juste modifiee EN PLACE en memoire (ADDQ/SUBQ emis) :
        # les drapeaux de l'operation portent la valeur -> BPL/BMI (DBRA sur D8 a domicile memoire :
        # SUBQ.W #1,$87F0(A5) ; BPL boucle)
        if DBG_VA and ins.va==DBG_VA: print('DBG', m, st.get(ins.rs) and st[ins.rs].kind, ins.va in absorbed)
        if m in ('bgez','bltz') and st.get(ins.rs) is not None and st[ins.rs].kind in ('memadd','memarith') \
           and ins.va not in absorbed:
            tgt=ins.va+4+ins.simm*4
            cc=0x0a00 if m=='bgez' else 0x0b00
            out.append((ins.va,"%s (cible %08x)  [signe de l'operation en place]"%("BPL" if m=='bgez' else "BMI",tgt),[0x6000|cc]))
            i+=1; continue
        # (HANDOFF §140) TEST « C » DU PORTAGE : 'lb/lh/lw r,mem ; bne/beq r,zero,T' (code ajoute d'Hyper, sans case
        # RES : Hyper mips 0x2C480 'TST.B $8B(A5) ; BNE', 0x3B4300 tests $C320/$C326/$C327) -> TST.x mem ; Bcc
        if CDISP_ON and m in ('beq','bne') and ins.rt==0 and ins.rs not in (0,) and ins.va not in absorbed \
           and st.get(ins.rs) is None and (memread.get(ins.rs) or absread.get(ins.rs) or idxread.get(ins.rs)):
            _p=_origin(ins_list, _producer(ins_list, i, ins.rs, 6))
            if _p is not None and ins_list[_p].m in ('lb','lbu','lh','lhu','lw'):
                tgt=ins.va+4+ins.simm*4; _w=None
                if memread.get(ins.rs):
                    sz,disp,an=memread[ins.rs]; _w=enc_tst_an(sz,an,disp); _t="TST.%s $%04x(A%d)"%(sz,disp&0xffff,an)
                elif absread.get(ins.rs):
                    sz,host=absread[ins.rs]; a_,note=abs_addr(host,sz)
                    _w=[0x4a00|(SZN[sz]<<6)|0x39]+abs_words(a_); _t="TST.%s $%06x.L%s"%(sz,a_&0xffffff,note)
                else:
                    sz,n,dn,dsz,d8=idxread[ins.rs]
                    _w=[0x4a00|(SZN[sz]<<6)|0x30|(n&7), idx_ext(dn,dsz,d8)]; _t="TST.%s %d(A%d,D%d.%s)%s"%(sz,d8,n,dn,dsz,idx_note(sz))
                out.append((ins.va,_t+"  [test C du portage]",_w))
                out.append((ins.va,"%s (cible %08x)"%(m.upper(),tgt),[0x6600 if m=='bne' else 0x6700]))
                CDISP_N[0]+=1; flags_set=None; pend=None; i+=1; continue
        if m in ('beq','bne','bltz','bgez','bgtz','blez') and not (m in ('beq','bne') and ins.rs==0 and ins.rt==0) \
           and ins.va not in absorbed and (m in ('bltz','bgez','bgtz','blez') or ins.rt==0):
            f=st.get(ins.rs)
            if f and f.kind=='flag' and (f.val,m) in BCC_OF:
                name,op=BCC_OF[(f.val,m)]
                if pend and pend[0]=='tst_mem' and f.val=='Z' and MEMMODE=='cps2' and pend[1]=='L' \
                   and m in ('bltz','bgez'):
                    _,sz,disp,an=pend                  # signe seul : le mot haut suffit
                    out.append((ins.va,"TST.W $%04x(A%d)  [signe du long echange]"%((disp+2)&0xffff,an),
                                enc_tst_an('W',an,(disp+2)&0xffff)))
                elif pend and pend[0]=='tst_mem' and f.val=='Z':
                    _,sz,disp,an=pend
                    out.append((ins.va,"TST.%s $%04x(A%d)"%(sz,disp,an),enc_tst_an(sz,an,disp)))
                elif pend and pend[0]=='tst_dn' and f.val=='Z':
                    _,sz,dn=pend
                    out.append((ins.va,"TST.%s D%d"%(sz,dn),enc_tst_dn(sz,dn)))
                elif pend and pend[0]=='tst_idx' and f.val=='Z':
                    _,sz,n,dn,dsz,d8=pend
                    out.append((ins.va,"TST.%s %d(A%d,D%d.%s)%s"%(sz,d8,n,dn,dsz,idx_note(sz)),
                                [0x4a00|(SZN[sz]<<6)|0x30|(n&7), idx_ext(dn,dsz,d8)]))
                elif pend and pend[0]=='tst_abs' and f.val=='Z':
                    _,sz,host=pend; a,note=abs_addr(host,sz)
                    out.append((ins.va,"TST.%s $%06x.L%s"%(sz,a&0xffffff,note),[0x4a00|(SZN[sz]<<6)|0x39]+abs_words(a)))
                elif pend and pend[0]=='btst_dyn' and f.val=='Z' and m in ('beq','bne'):
                    _,dn,tgt=pend
                    ws,mn=enc_dynbit('btst',dn,tgt); out.append((ins.va,mn,ws))
                elif pend and pend[0]=='btst_dn' and f.val=='Z' and m in ('beq','bne'):
                    _,bit,dn=pend
                    out.append((ins.va,"BTST #%d,D%d"%(bit,dn),[0x0800|(dn&7), bit]))
                elif pend and pend[0]=='cmp':
                    dst,src,sz=pend[1],pend[2],pend[3]
                    if MEMMODE=='type' and src[0]=='imm' and sz=='L' and (
                       (dst[0]=='D' and dst[1] in revd) or (dst[0]=='mem' and rev_field(dst[3],dst[2]))):
                        src=('imm',bs32(src[1]))               # constante remise a l'endroit (ROM)
                    r=enc_cmp(sz,dst,src)
                    if r: out.append((ins.va,r[1],r[0]))
                    if len(pend)>4 and pend[4] and f.val=='Z' and m in SIGNED_OF:
                        name,op=SIGNED_OF[m]              # signe de RES = N^V : comparaison signee
                if pend and pend[0]=='btst' and m in ('beq','bne'):
                    kind,bit,disp,an=pend
                    out.append((ins.va,"BTST #$%x,$%04x(A%d)"%(bit,disp,an), enc_btst_an(bit,an,disp)))
                out.append((ins.va,"%s (cible %08x)"%(name,ins.va+4+ins.simm*4),[op]))
                pend=None; i+=1; continue
        if m=='bgez' and st.get(ins.rs) and st[ins.rs].kind=='arithi' \
           and st[ins.rs].val[0]=='add' and st[ins.rs].val[2]==-1:
            dn=st[ins.rs].val[1]
            tgt_=ins.va+4+ins.simm*4
            for k in range(len(out)-1, max(-1,len(out)-4), -1):
                if out[k][1]=="SUBQ.W #1,D%d"%dn:
                    # (HANDOFF §74) le recompilateur rend DBRA par 'decrementer ; boucler si >= 0' : pour un
                    # compteur NEGATIF (-1 -> -2) il SORT, la ou DBRA bouclerait 65 534 fois (le code ajoute par
                    # le portage ecrase D6 de la boucle d'affichage : le portage s'en sort grace a cette nuance).
                    # -> SUBQ.W #1,Dn ; BPL (semantique exacte), sauf si des drapeaux anterieurs sont relus
                    # apres la boucle ou en tete de boucle (DBRA ne les touche pas).
                    import bisect as _bis
                    j_t=_bis.bisect_left(ins_vas, tgt_)
                    if flags_read_first(ins_list, i+1) or flags_read_first(ins_list, j_t):
                        out[k]=(out[k][0],"(decrementation absorbee par le DBRA)",[])
                        out.append((ins.va,"DBRA D%d (cible %08x)"%(dn,tgt_),[0x51c8|dn,0]))
                    else:
                        out.append((ins.va,"BPL (cible %08x)  [DBRA du recompilateur : boucle si >= 0]"%tgt_,[0x6a00]))
                    pend=None; break
            else:
                i+=1; continue
            i+=1; continue
        if m in ('bgez','bltz') and ins.va in absorbed:
            out.append((ins.va,"(test interne a la conversion d'adresse, absorbe)",[])); i+=1; continue
        if m=='beq' and ins.va in absorbed and not (ins.rs==0 and ins.rt==0):
            out.append((ins.va,"(calcul interne de la retenue, absorbe)",[])); i+=1; continue
        if m=='beq' and ins.va in absorbed and TAILBR and ins.va in tail_abs and ins.va in br_targets:
            TAILBR_N[0]+=1
            out.append((ins.va,"RTS  [saut terminal absorbe, cible d'un branchement]",[RTS])); i+=1; continue
        if m=='beq' and ins.va in absorbed:
            # saut inconditionnel absorbe : vers l'epilogue (appel terminal) ou saut
            # interne du calcul de la retenue
            out.append((ins.va,"(saut inconditionnel interne, absorbe)",[])); i+=1; continue
        if m in ('beq','beql') and ins.rs==0 and ins.rt==0:
            # (HANDOFF §80) BRA vers l'epilogue ('jr ra') : le test en attente est rendu a l'appelant, comme
            # devant un RTS (mips 0x3649F8 : 'MOVE.W $16(A6),D0 ; CMP.W $64(A6),D0 ; BRA fin' = test de sol)
            import bisect as _bis2; _t=ins.va+4+ins.simm*4; _k=_bis2.bisect_left(ins_vas,_t)
            # (HANDOFF §122) epilogue du recompilateur recent : restaurations 'lq ...,sp' / 'ld ra' / 'addiu sp' avant
            # le 'jr ra' (test de sol d'Upper mips 0x3DEDB4 : Bison volait sans fin, la manche ne finissait pas)
            while _k<len(ins_list) and ((ins_list[_k].m=='sll' and ins_list[_k].w==0) or
                                        (ins_list[_k].m in ('lq','ld') and ins_list[_k].rs==29) or
                                        (ins_list[_k].m=='addiu' and ins_list[_k].rs==29 and ins_list[_k].rt==29)): _k+=1
            if _k<len(ins_list) and ins_list[_k].m=='jr' and ins_list[_k].rs==31:
                if flags_to_caller(i, pend, pend_va, absorbed, out): pend=None
            # BRANCHEMENT INCONDITIONNEL (BRA du 68K : retour de boucle, saut 'sinon', vers l'epilogue...) :
            # n'etait JAMAIS traduit (HANDOFF §63) ; on reproduit le flot du MIPS.
            out.append((ins.va,"BRA (cible %08x)"%(ins.va+4+ins.simm*4),[0x6000])); i+=1; continue
        if m in ('bne','beq') and pend and pend[0]=='btst':
            kind,bit,disp,an = pend
            out.append((ins.va,"BTST #$%x,$%04x(A%d)"%(bit,disp,an), enc_btst_an(bit,an,disp)))
            out.append((ins.va,"%s (cible %08x)"%(m.upper(),ins.va+4+ins.simm*4),
                        [BCC[m]]))
            pend=None; i+=1; continue
        # (HANDOFF §137) mot memoire decale SUR PLACE ('lh x,d(An) ; sll y,x,k ; sh y,d(An)', ex. D8 servi par son
        # domicile : 'LSL.W #3,D8' a Hyper mips 0x5A41C, SFA3 0x7E674) -> k x 'LSL.W d(An)' (decalage memoire de 1)
        if MEMSHL_ON and m=='sh' and st.get(ins.rs) and st[ins.rs].kind=='an' and st[ins.rs].val[1]==0:
            _p=_producer(ins_list,i,ins.rt,8)
            if _p is not None and ins_list[_p].m=='sll' and 1<=ins_list[_p].sa<=8:
                _q=_producer(ins_list,_p,ins_list[_p].rt,8)
                if (_q is not None and ins_list[_q].m in ('lh','lhu') and ins_list[_q].simm==ins.simm
                        and st.get(ins_list[_q].rs) is not None and ins_list[_q].rs==ins.rs):
                    _an=st[ins.rs].val[0]; _d=ins.simm&0xffff
                    out.append((ins.va,"LSL.W $%04x(A%d) x%d  [mot memoire decale sur place]"%(_d,_an,ins_list[_p].sa),
                                [0xe3e8|(_an&7),_d]*ins_list[_p].sa)); MEMSHL_N[0]+=1; i+=1; continue
        # store vers [An + disp]  -> MOVE.x src,(d16,An)
        if m in ('sb','sh','sw') and ins.rs in lui and lui[ins.rs]!=0x7000 and not st.get(ins.rs):
            size={'sb':'B','sh':'W','sw':'L'}[m]; src=st.get(ins.rt)
            wrel=((lui[ins.rs]<<16)+ins.simm) - (RAM_HI<<16)
            if MEMMODE in ('cps2','type') and m=='sw' and wrel in WIDEREG:
                # registre de base CPS-A ELARGI par le portage (adresse hote 32 bits) -> registre CPS2
                # 16 bits = adresse 68K >> 8 (ROM : MOVE.W $40(A5),$804102)
                reg=WIDEREG[wrel]; ra=abs_words(reg)
                if IDXRMW_ON and src is None and ins.rt!=0 and ins.rt in lui:   # (HANDOFF §138) 'lui' SEUL ($920000 :
                    src=Sym('const',(lui[ins.rt]<<16)&0xffffffff); IDXRMW_N[0]+=1   # bases objets/scroll1 perdues)
                if src and src.kind=='const':
                    v=(addr_to_68k(src.val) or src.val)>>8
                    out.append((ins.va,"MOVE.W #$%x,$%06x.L  [registre CPS-A, elargi par le portage]"%(v&0xffff,reg),
                                [0x33fc, v&0xffff]+ra)); i+=1; continue
                load=None
                if src is None and ins.rt!=0 and memread.get(ins.rt) and memread[ins.rt][0]=='L':
                    _,sd,sn=memread[ins.rt]; load=[0x2028|(sn&7), sd&0xffff]; ltxt="$%04x(A%d)"%(sd,sn)
                    if MEMMODE=='cps2': load=load+[SWAP_OP]
                elif src and src.kind=='reg68' and src.val and src.val[0]=='D':
                    k=src.val[1]; load=[0x2000|(k&7)]+([SWAP_OP] if MEMMODE=='cps2' and False else []); ltxt="D%d"%k
                if load:
                    ws=[0x2f00]+load+[0xe088, 0x33c0]+ra+[0x4cdf,0x0001]
                    out.append((ins.va,"MOVE.L D0,-(SP) ; MOVE.L %s,D0 ; LSR.L #8,D0 ; MOVE.W D0,$%06x.L ; MOVEM.L (SP)+,D0  [registre CPS-A elargi]"%(ltxt,reg),ws))
                    i+=1; continue
            a,note=abs_addr((lui[ins.rs]<<16)+ins.simm, size)
            dea=(1<<9)|(7<<6)                             # destination (xxx).L : mode 7, reg 1
            if ins.rt==0:
                out.append((ins.va,"CLR.%s $%06x.L%s"%(size,a&0xffffff,note),
                            [0x4200|(SZN[size]<<6)|0x39]+abs_words(a))); i+=1; continue
            if src and src.kind=='imm':
                v=src.val & SZMASK[size]
                v=swap32(v) if (MEMMODE=='cps2' and size=='L') else v
                out.append((ins.va,"MOVE.%s #$%x,$%06x.L%s"%(size,v,a&0xffffff,note),
                            [(SZ_TOP[size]<<12)|dea|0x3c]+_imm_words(size,v)+abs_words(a))); i+=1; continue
            if src and src.kind=='reg68' and src.val and src.val[0]=='D':
                k=src.val[1]; ws=[(SZ_TOP[size]<<12)|dea|(k&7)]+abs_words(a)
                if MEMMODE=='cps2' and size=='L': ws=[SWAP_OP|k]+ws+[SWAP_OP|k]
                out.append((ins.va,"MOVE.%s D%d,$%06x.L%s"%(size,k,a&0xffffff,note),ws)); i+=1; continue
            if src is None and ins.rt!=0 and memread.get(ins.rt) and memread[ins.rt][0]==size:
                msz,sd,sn=memread[ins.rt]                  # (d16,An) -> absolu : copie
                out.append((ins.va,"MOVE.%s $%04x(A%d),$%06x.L%s"%(size,sd,sn,a&0xffffff,note),
                            [(SZ_TOP[size]<<12)|dea|0x28|(sn&7), sd&0xffff]+abs_words(a))); i+=1; continue
            # (HANDOFF §78) copies vers l'absolu depuis une lecture INDEXEE ou ABSOLUE (commandes son $96xxxx)
            if src is None and ins.rt!=0 and idxread.get(ins.rt) and idxread[ins.rt][0]==size:
                sz,n,dn,dsz,d8=idxread[ins.rt]
                out.append((ins.va,"MOVE.%s %d(A%d,D%d.%s),$%06x.L%s%s"%(size,d8,n,dn,dsz,a&0xffffff,note,idx_note(size)),
                            [(SZ_TOP[size]<<12)|dea|0x30|(n&7), idx_ext(dn,dsz,d8)]+abs_words(a))); i+=1; continue
            if src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]==size:
                _,host=absread[ins.rt]; a2,note2=abs_addr(host,size)
                out.append((ins.va,"MOVE.%s $%06x.L,$%06x.L%s%s"%(size,a2&0xffffff,a&0xffffff,note2,note),
                            [(SZ_TOP[size]<<12)|dea|0x39]+abs_words(a2)+abs_words(a))); i+=1; continue
        if m in ('sb','sh','sw') and st.get(ins.rs) and st[ins.rs].kind=='an_d':
            n,dn,dsz,d8=(st[ins.rs].val+(0,))[:4]; d8+=ins.simm
            size={'sb':'B','sh':'W','sw':'L'}[m]; src=st.get(ins.rt)
            if not (-128 <= d8 + (1 if (MEMMODE=='cps2' and size=='B') else 0) <= 127) and -0x8000 <= d8 <= 0x7fff:
                # (HANDOFF §78) deplacement hors d8 : adresse exacte calculee dans An (sauve), octet XOR 1
                dd=d8                                          # (valeur MIPS : pas encore XOR)
                srcw=None; stxt=None; mr=memread.get(ins.rt) if ins.rt!=0 else None
                if ins.rt==0: op=[0x4200|(SZN[size]<<6)|0x10|(n&7)]; stxt="CLR"
                elif src and src.kind=='reg68' and src.val and src.val[0]=='D':
                    k=src.val[1]; op=[(SZ_TOP[size]<<12)|((n&7)<<9)|(2<<6)|(k&7)]; stxt="D%d"%k
                    if MEMMODE=='cps2' and size=='L': op=[SWAP_OP|k]+op+[SWAP_OP|k]
                elif src and src.kind=='imm':
                    v=src.val & SZMASK[size]; v=swap32(v) if (MEMMODE=='cps2' and size=='L') else v
                    op=[(SZ_TOP[size]<<12)|((n&7)<<9)|(2<<6)|0x3c]+_imm_words(size,v); stxt="#$%x"%v
                elif mr and mr[0]==size and mr[2]!=n:
                    op=[(SZ_TOP[size]<<12)|((n&7)<<9)|(2<<6)|0x28|(mr[2]&7), mr[1]&0xffff]; stxt="$%04x(A%d)"%(mr[1],mr[2])
                else: op=None
                if op is not None:
                    ws=[0x2f08|n, 0x41e8|((n&7)<<9)|(n&7), dd&0xffff, (0xd1c0 if dsz=='L' else 0xd0c0)|((n&7)<<9)|(dn&7)]
                    if MEMMODE=='cps2' and size=='B': ws+=[0x2f08|n, 0x0a2f, 0x0001, 0x0003, 0x205f|((n&7)<<9)]
                    ws+=op+[0x205f|((n&7)<<9)]
                    out.append((ins.va,"MOVE.%s %s,$%04x(A%d,D%d.%s)  [deplacement 16 bits : adresse calculee]"%(size,stxt,dd&0xffff,n,dn,dsz),ws))
                    i+=1; continue
            if MEMMODE=='cps2' and size=='B': d8^=1          # octet indexe : index PAIR suppose (HANDOFF §61)
            if -128<=d8<=127:
                dea=(6<<6)|((n&7)<<9)              # destination d8(An,Xn) : reg n, mode 6
                if src and src.kind=='idxrmw' and src.val[2]==(size,n,dn,dsz,d8):
                    op_,v_,_ix=src.val; sz_=SZN[size]; ea_=0x30|(n&7)    # (HANDOFF §138) op en place indexe
                    if op_=='add':
                        v_=v_ & SZMASK[size]; v_=v_-(SZMASK[size]+1) if v_>SZMASK[size]//2 else v_
                        if 1<=v_<=8:    ws=[0x5000|((v_&7)<<9)|(sz_<<6)|ea_]; mn_="ADDQ.%s #%d"%(size,v_)
                        elif -8<=v_<=-1: ws=[0x5100|(((-v_)&7)<<9)|(sz_<<6)|ea_]; mn_="SUBQ.%s #%d"%(size,-v_)
                        else: ws=[0x0600|(sz_<<6)|ea_]+_imm_words(size,v_&SZMASK[size]); mn_="ADDI.%s #$%x"%(size,v_&SZMASK[size])
                    else:
                        v_=v_ & SZMASK[size]
                        ws=[{'and':0x0200,'or':0x0000,'xor':0x0a00}[op_]|(sz_<<6)|ea_]+_imm_words(size,v_)
                        mn_="%s.%s #$%x"%({'and':'ANDI','or':'ORI','xor':'EORI'}[op_],size,v_)
                    out.append((ins.va,"%s,%d(A%d,D%d.%s)  [lecture-modification-ecriture indexee]%s"%(mn_,d8,n,dn,dsz,idx_note(size)),
                                ws+[idx_ext(dn,dsz,d8)]))
                    IDXRMW_N[0]+=1; flags_set=None; i+=1; continue
                if ins.rt==0:
                    out.append((ins.va,"CLR.%s %d(A%d,D%d.%s)%s"%(size,d8,n,dn,dsz,idx_note(size)),
                                [0x4200|({'B':0,'W':1,'L':2}[size]<<6)|0x30|(n&7), idx_ext(dn,dsz,d8)])); i+=1; continue
                if src and src.kind=='reg68' and src.val and src.val[0]=='D':
                    k=src.val[1]; ws=[(SZ_TOP[size]<<12)|dea|(k&7), idx_ext(dn,dsz,d8)]
                    if MEMMODE=='cps2' and size=='L': ws=[SWAP_OP|k]+ws+[SWAP_OP|k]
                    out.append((ins.va,"MOVE.%s D%d,%d(A%d,D%d.%s)%s"%(size,k,d8,n,dn,dsz,idx_note(size)),ws)); i+=1; continue
                if src and src.kind=='an' and src.val[1]==0 and size in ('W','L'):
                    # (HANDOFF §80) registre d'adresse range a une adresse indexee (ROM $30BBA : MOVE.L A0,0(A6,D1.W),
                    # position du script d'IA sauvee apres chaque commande : perdue, l'IA recommencait son script)
                    k=src.val[0]
                    if size=='W' or MEMMODE!='cps2':
                        ws=[(SZ_TOP[size]<<12)|dea|0x08|(k&7), idx_ext(dn,dsz,d8)]
                        mn="MOVE.%s A%d,%d(A%d,D%d.%s)"%(size,k,d8,n,dn,dsz)
                    else:                                   # long a moities echangees : par Dt (SWAP final =
                        t=0 if dn!=0 else 1                 # drapeaux d'un MOVE.L ; MOVEM sans drapeaux)
                        ws=[0x2f00|t, 0x2008|(t<<9)|(k&7), SWAP_OP|t, (2<<12)|dea|t, idx_ext(dn,dsz,d8),
                            SWAP_OP|t, 0x4cdf, 1<<t]
                        mn="MOVE.L A%d,%d(A%d,D%d.%s)  [long echange, par D%d]"%(k,d8,n,dn,dsz,t)
                    out.append((ins.va,mn,ws)); i+=1; continue
                if src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]==size:
                    _,host=absread[ins.rt]; a2,note2=abs_addr(host,size)     # (HANDOFF §78) absolu -> indexe
                    out.append((ins.va,"MOVE.%s $%06x.L,%d(A%d,D%d.%s)%s%s"%(size,a2&0xffffff,d8,n,dn,dsz,note2,idx_note(size)),
                                [(SZ_TOP[size]<<12)|dea|0x39]+abs_words(a2)+[idx_ext(dn,dsz,d8)])); i+=1; continue
                if src is None and ins.rt!=0 and idxread.get(ins.rt) and idxread[ins.rt][0]==size and size!='B':
                    sz,sn,sdn,sdsz,sd8=idxread[ins.rt]                        # indexe -> indexe (mots/longs)
                    out.append((ins.va,"MOVE.%s %d(A%d,D%d.%s),%d(A%d,D%d.%s)"%(size,sd8,sn,sdn,sdsz,d8,n,dn,dsz),
                                [(SZ_TOP[size]<<12)|dea|0x30|(sn&7), idx_ext(sdn,sdsz,sd8), idx_ext(dn,dsz,d8)])); i+=1; continue
                if ins.rt!=0 and memread.get(ins.rt) and memread[ins.rt][0]==size and (src is None or src.kind!='imm'):
                    # (HANDOFF §77) copie memoire -> indexe : MOVE.x d16(Am),d8(An,Dn) (tampon circulaire
                    # mips 0x1EF220, 'traines' des personnages : le corps entier etait perdu)
                    msz,sd,sn=memread[ins.rt]
                    out.append((ins.va,"MOVE.%s $%04x(A%d),%d(A%d,D%d.%s)%s"%(size,sd,sn,d8,n,dn,dsz,idx_note(size)),
                                [(SZ_TOP[size]<<12)|dea|0x28|(sn&7), sd&0xffff, idx_ext(dn,dsz,d8)])); i+=1; continue
                if src and src.kind=='imm':
                    v=src.val & SZMASK[size]
                    v=swap32(v) if (MEMMODE=='cps2' and size=='L') else v
                    out.append((ins.va,"MOVE.%s #$%x,%d(A%d,D%d.%s)%s"%(size,v,d8,n,dn,dsz,idx_note(size)),
                                [(SZ_TOP[size]<<12)|dea|0x3c]+_imm_words(size,v)+[idx_ext(dn,dsz,d8)])); i+=1; continue
        if m in ('sb','sh','sw'):
            base=st.get(ins.rs)
            if base and base.kind=='an':
                size={'sb':'B','sh':'W','sw':'L'}[m]
                src=st.get(ins.rt)
                an,d0=base.val
                disp=mconv((d0 + ins.simm) & 0xffff, size, an)
                if pend and pend[0]=='btst' and pend[3]==an and 0 <= ((pend[2]-disp) & 0xffff) < {'B':1,'W':2,'L':4}[size]:
                    # (HANDOFF §80) le test d'un bit est differe jusqu'au Bcc, mais l'octet teste est REECRIT avant :
                    # le BTST relirait la nouvelle valeur (ROM $1B0D4 : BCLR #7,$11A(A0) ; BEQ -> bit Start perdu)
                    _same=False
                    if src and src.kind=='memlogic' and src.val[2]==(size,disp,an) and size=='B':
                        _mn=enc_logic_mem(src.val[0],'B',src.val[1],an,disp)[1]
                        _same=_mn[:4] in ('BSET','BCLR','BCHG') and int(_mn.split('#')[1].split(',')[0])==pend[1]
                    if _same: pend=None                        # forme de la ROM : Z = ancien bit, pose par l'operation
                    else:
                        _k,_b,_d,_a=pend; N_BTST_CONFLIT[0]+=1
                        out.append((ins.va,"BTST #$%x,$%04x(A%d) ; MOVE SR,-(SP)  [test anterieur a l'ecriture]"%(_b,_d,_a),
                                    enc_btst_an(_b,_a,_d)+[0x40e7]))
                        pend=None; ccr_restore=True
                if MEMMODE=='cps2' and size=='W' and ins.rt!=0:
                    bs16=bswap16_mem(ins_list, i, ins.rt)
                    if bs16 is not None and bs16[0]=='idx':
                        # (HANDOFF §100) source = table de donnees indexee par Dk.W : octets croises via un An prete
                        _,tc,dk=bs16; ta=addr_to_68k(tc)
                        if ta is not None:
                            n_=1 if an==0 else 0
                            ws_=[0x2f08|n_, 0x41f9|(n_<<9), (ta>>16)&0xffff, ta&0xffff, 0xd0c0|(n_<<9)|dk]
                            ws_+=enc_move_mem_mem('B',n_,1,an,disp)+enc_move_mem_mem('B',n_,0,an,disp+1)+[0x205f|(n_<<9)]
                            out.append((ins.va,"MOVE.L A%d,-(SP) ; LEA $%06x.L,A%d ; ADDA.W D%d,A%d ; MOVE.B 1(A%d),$%04x(A%d) ; MOVE.B (A%d),$%04x(A%d) ; MOVEA.L (SP)+,A%d  [mot a octets inverses lu dans une table indexee]"
                                        %(n_,ta,n_,dk,n_,n_,disp,an,n_,(disp+1)&0xffff,an,n_), ws_))
                            i+=1; continue
                    if bs16 is not None and bs16[0]=='anidx':
                        # (HANDOFF §138) idem, table designee par An : MOVE.L At,-(SP) ; MOVEA.L An,At ; ADDA.W Dk,At ;
                        # MOVE.B d+1(At),disp(Am) ; MOVE.B d(At),disp+1(Am) ; MOVEA.L (SP)+,At
                        _,sn_,sd_,dk=bs16; n_=[r for r in (0,1,2) if r not in (an,sn_)][0]
                        ws_=[0x2f08|n_, 0x2048|(n_<<9)|sn_, 0xd0c0|(n_<<9)|dk]
                        ws_+=enc_move_mem_mem('B',n_,sd_+1,an,disp)+enc_move_mem_mem('B',n_,sd_,an,disp+1)+[0x205f|(n_<<9)]
                        out.append((ins.va,"MOVE.L A%d,-(SP) ; MOVEA.L A%d,A%d ; ADDA.W D%d,A%d ; MOVE.B %d(A%d),$%04x(A%d) ; MOVE.B %d(A%d),$%04x(A%d) ; MOVEA.L (SP)+,A%d  [mot a octets inverses lu dans une table designee par A%d]"
                                    %(n_,sn_,n_,dk,n_,sd_+1,n_,disp,an,sd_,n_,(disp+1)&0xffff,an,n_,sn_), ws_))
                        IDXRMW_N[0]+=1; i+=1; continue
                    if bs16 is not None and bs16[0]=='an':
                        # (HANDOFF §92) champ a octets inverses recopie d'un mot en memoire : octets 68K croises
                        _,sa_,sd_=bs16
                        out.append((ins.va,"MOVE.B $%04x(A%d),$%04x(A%d) ; MOVE.B $%04x(A%d),$%04x(A%d)  [mot a octets inverses]"
                                    %((sd_+1)&0xffff,sa_,disp,an,sd_,sa_,(disp+1)&0xffff,an),
                                    enc_move_mem_mem('B',sa_,sd_+1,an,disp)+enc_move_mem_mem('B',sa_,sd_,an,disp+1)))
                        i+=1; continue
                if src and src.kind=='tblval' and src.val[2]==size:
                    tbl,ix,_=src.val
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D%d.W),$%04x(A%d)"%(size,tbl,ix,disp,an),
                                enc_move_pcidx(size,ix,('mem',disp,an)))); i+=1; continue
                if src and src.kind=='memnot' and src.val==(size,disp,an):
                    out.append((ins.va,"NOT.%s $%04x(A%d)"%(size,disp,an),[0x4600|(SZN[size]<<6)|0x28|(an&7), disp&0xffff]))
                    flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='mem2' and size in ('B','W','L'):
                    op_,ma,mb=src.val
                    if op_ in ('addu','subu') and (ma[2],ma[1])==(an,disp) and ma[0]==size and (mb[2],mb[1])!=(an,disp):
                        # (HANDOFF §138) m1 +=/-= m2 : MOVE.L D0,-(SP) ; MOVE.x m2,D0 [; SWAP] ; ADD/SUB.x D0,m1 ;
                        # MOVEM.L (SP)+,D0 (drapeaux de l'operation preserves)
                        ld=[(SZ_TOP[size]<<12)|0x28|(mb[2]&7), mb[1]&0xffff]
                        if MEMMODE=='cps2' and size=='L':
                            w2,mn2=inplace_long(op_,an,disp,('D',0)); ld=ld+[SWAP_OP|0]
                        else:
                            w2=[(0xd100 if op_=='addu' else 0x9100)|(SZN[size]<<6)|0x28|(an&7), disp&0xffff]
                            mn2="%s.%s D0,$%04x(A%d)"%('ADD' if op_=='addu' else 'SUB',size,disp,an)
                        out.append((ins.va,"MOVE.L D0,-(SP) ; MOVE.%s $%04x(A%d),D0 ; %s ; MOVEM.L (SP)+,D0  [memoire %s= memoire]"%(
                            size,mb[1],mb[2],mn2,'+' if op_=='addu' else '-'), [0x2f00]+ld+w2+[0x4cdf,0x0001]))
                        IDXRMW_N[0]+=1; flags_set=None; i+=1; continue
                    if (ma[2],ma[1])==(an,disp) or (mb[2],mb[1])==(an,disp):
                        o=mb if (ma[2],ma[1])==(an,disp) else ma          # l'autre operande
                        if o[0]==size and (o[2],o[1])!=(an,disp):
                            psh=0x2f00 if size=='L' else 0x3f00; pop=0x201f if size=='L' else 0x301f
                            ld=[(SZ_TOP[size]<<12)|0x28|(o[2]&7), o[1]&0xffff]              # MOVE.x o,D0
                            base={'or':0x8100,'and':0xc100,'xor':0xb100}[op_]|(SZN[size]<<6)|0x28|(an&7)
                            out.append((ins.va,"MOVE D0,-(SP) ; MOVE.%s $%04x(A%d),D0 ; %s.%s D0,$%04x(A%d) ; MOVE (SP)+,D0"%(
                                size,o[1],o[2],{'or':'OR','and':'AND','xor':'EOR'}[op_],size,disp,an),
                                [psh]+ld+[base, disp&0xffff, pop]))
                            i+=1; continue
                if IDXRMW_ON and src and src.kind=='tblmemval' and src.val[2]==size:
                    # (HANDOFF §138) champ <- T[ext(champ index)] (Hyper mips 0x2F5ED0 : 'MOVE.B T(PC,D8.W),$70(A6)'
                    # avec D8 servi par son domicile, perdu) : index par D0 sauve, MOVEM final (drapeaux du MOVE)
                    _tb,(_msz,_d,_an),_sz=src.val
                    out.append((ins.va,"MOVE.L D0,-(SP) ; MOVE.%s $%04x(A%d),D0%s  [index de table lu en memoire]"%(
                        _msz,_d&0xffff,_an," ; EXT.W" if _msz=='B' else ""),
                        [0x2f00]+enc_move_an_dn(_msz,_an,_d,0)+([0x4880] if _msz=='B' else [])))
                    out.append((ins.va,"MOVE.%s T_%06x(PC,D0.W),$%04x(A%d)"%(size,_tb,disp&0xffff,an),
                                enc_move_pcidx(size,0,('mem',disp,an))))
                    out.append((ins.va,"MOVEM.L (SP)+,D0",[0x4cdf,0x0001]))
                    IDXRMW_N[0]+=1; flags_set=None; i+=1; continue
                if src and src.kind=='memlogic':
                    kind,mask,(msz,mdisp,man)=src.val
                    if (man,mdisp)==(an,disp) and msz==size:
                        if MEMMODE=='cps2' and size=='L':
                            ws,mn=inplace_long('logic_'+kind,an,disp,('imm',mask))
                        else:
                            ws,mn=enc_logic_mem(kind,size,mask,an,disp)
                        out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='bswap16' and src.val[0]=='D' and size=='W':
                    # mot aux octets inverses (champ range octet par octet) depuis Dk vers la memoire
                    k=src.val[1]
                    out.append((ins.va,"ROR.W #8,D%d ; MOVE.W D%d,$%04x(A%d) ; ROR.W #8,D%d  [octets inverses]"%(k,k,disp,an,k),
                                [0xe058|k]+enc_move_dn_an('W',k,an,disp)+[0xe058|k])); i+=1; continue
                if src and src.kind=='bsmem' and size=='W' and (src.val[2][2],src.val[2][1])==(an,disp):
                    op,k,_mr=src.val
                    base={'or':0x8168,'and':0xc168,'xor':0xb168}[op]|((k&7)<<9)|(an&7)
                    nm_={'or':'OR','and':'AND','xor':'EOR'}[op]
                    out.append((ins.va,"ROR.W #8,D%d ; %s.W D%d,$%04x(A%d) ; ROR.W #8,D%d  [octets inverses]"%(k,nm_,k,disp,an,k),
                                [0xe058|k, base, disp&0xffff, 0xe058|k])); i+=1; continue
                if src and src.kind=='dynbit' and src.val[0]!='btst' and src.val[2]==('mem',size,disp,an):
                    ws,mn=enc_dynbit(src.val[0],src.val[1],src.val[2])
                    out.append((ins.va,mn,ws)); pend=None; flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='an' and src.val[1]==0 and size=='L' and MEMMODE=='cps2' and src.val[0]!=an:
                    # (HANDOFF §67) MOVE.L An,d(Am) en mode cps2 (long range moities echangees) : mot bas en d,
                    # mot haut en d+2 ; le SWAP final redonne exactement les drapeaux d'un MOVE.L (N=bit 31, Z)
                    k=src.val[0]
                    ws=[(3<<12)|((an&7)<<9)|(5<<6)|(1<<3)|(k&7), disp&0xffff, 0xc188|(k&7), SWAP_OP|0,
                        (3<<12)|((an&7)<<9)|(5<<6)|0, (disp+2)&0xffff, SWAP_OP|0, 0xc188|(k&7)]
                    out.append((ins.va,"MOVE.L A%d,$%04x(A%d)  [long echange : MOVE.W bas + EXG/SWAP haut]"%(k,disp,an),ws))
                    i+=1; continue
                if src and src.kind=='an' and src.val[1]==0 and size=='L' and MEMMODE=='cps2' and src.val[0]==an and an!=7:
                    # (HANDOFF §80) MOVE.L An,d(An) (registre range dans la memoire qu'il designe : chainage
                    # « ADDQ #8,A0 ; MOVE.L A0,-4(A0) » d'une image d'animation construite en RAM, mips 0xB87A0) :
                    # par D0 (la forme EXG ecraserait la base). SWAP final : drapeaux d'un MOVE.L ; MOVEM sans drapeaux
                    ws=[0x2f00, 0x2008|an, SWAP_OP|0, 0x2140|(an<<9), disp&0xffff, SWAP_OP|0, 0x4cdf, 0x0001]
                    out.append((ins.va,"MOVE.L A%d,$%04x(A%d)  [long echange, par D0]"%(an,disp,an),ws)); i+=1; continue
                if src and src.kind=='an' and src.val[1]==0 and (size=='W' or (size=='L' and MEMMODE!='cps2')):
                    # registre d'adresse range en memoire. .W : les 16 bits bas d'une adresse hote
                    # et de l'adresse 68K coincident (RAM et video) ; .L seulement en mode hote
                    k=src.val[0]
                    out.append((ins.va,"MOVE.%s A%d,$%04x(A%d)"%(size,k,disp,an),
                                [(SZ_TOP[size]<<12)|((an&7)<<9)|(5<<6)|(1<<3)|(k&7), disp&0xffff])); i+=1; continue
                if src and src.kind=='memneg':
                    msz,mdisp,man=src.val
                    if (man,mdisp)==(an,disp) and msz==size:
                        if MEMMODE=='cps2' and size=='L':
                            ws,mn=inplace_long('neg',an,disp,('D',-1))
                        else:
                            ws=[0x4400|({'B':0,'W':1,'L':2}[size]<<6)|0x28|(an&7), disp&0xffff]
                            mn="NEG.%s $%04x(A%d)"%(size,disp,an)
                        out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='memarith':
                    (msz,mdisp,man),op,dn = src.val
                    if (man,mdisp)==(an,disp) and msz==size and MEMMODE=='cps2' and size=='L':
                        ws,mn=inplace_long(op,an,disp,('D',dn))
                        out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); i+=1; continue
                    if (man,mdisp)==(an,disp) and msz==size:
                        ws,name=enc_op_dn_mem(op,size,dn,an,disp)
                        out.append((ins.va,"%s.%s D%d,$%04x(A%d)"%(name,size,dn,disp,an),ws))
                        flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='memadd':
                    (msz,mdisp,man),v = src.val
                    if (man,mdisp)==(an,disp) and msz==size and MEMMODE=='cps2' and size=='L':
                        ws,mn=inplace_long('add',an,disp,('imm',v))
                        out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); i+=1; continue
                    if (man,mdisp)==(an,disp) and msz==size:     # relu et reecrit au MEME endroit
                        ws,mn=enc_addsub_mem(size,v,an,disp)
                        out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); i+=1; continue
                if src and src.kind=='sub' and src.val[0]==('mem',size,disp,an) and src.val[1] and src.val[1][0]=='D' and size in ('B','W'):
                    k=src.val[1][1]                           # (HANDOFF §78) SUB.x Dk,d16(An) en place
                    out.append((ins.va,"SUB.%s D%d,$%04x(A%d)"%(size,k,disp,an),
                                [0x9100|((k&7)<<9)|(SZN[size]<<6)|0x28|(an&7), disp&0xffff]))
                    flags_set=('mem',an,disp,size); last_sub=src.val
                    if pend and pend[0]=='cmp': pend=None
                    i+=1; continue
                if src and src.kind=='sub' and src.val[0]==('mem',size,disp,an) and src.val[1] and src.val[1][0]=='imm':
                    # (HANDOFF §78) 'lh ; andi $FFFF ; addiu -k ; sh' au meme endroit = SUBI/SUBQ en place
                    k=src.val[1][1] & SZMASK[size]; v=-(k if k < (SZMASK[size]+1)//2 else k-(SZMASK[size]+1))
                    if MEMMODE=='cps2' and size=='L': ws,mn=inplace_long('add',an,disp,('imm',v))
                    else: ws,mn=enc_addsub_mem(size,v,an,disp)
                    out.append((ins.va,mn,ws)); flags_set=('mem',an,disp,size); last_sub=src.val   # (HANDOFF §90) drapeaux poses par SUBI en place
                    if pend and pend[0]=='cmp': pend=None
                    i+=1; continue
                if src is None and ins.rt!=0 and absread.get(ins.rt) and absread[ins.rt][0]==size:
                    _,host=absread[ins.rt]; a,note=abs_addr(host,size)     # abs.L -> d16(An) : copie
                    out.append((ins.va,"MOVE.%s $%06x.L,$%04x(A%d)%s"%(size,a&0xffffff,disp,an,note),
                                [(SZ_TOP[size]<<12)|((an&7)<<9)|(5<<6)|0x39]+abs_words(a)+[disp&0xffff]))
                    i+=1; continue
                if src is None and ins.rt!=0 and memread.get(ins.rt) and memread[ins.rt][0]==size:
                    msz,sdisp,san = memread[ins.rt]
                    out.append((ins.va,"MOVE.%s $%04x(A%d),$%04x(A%d)"%(size,sdisp,san,disp,an),
                                enc_move_mem_mem(size,san,sdisp,an,disp)))
                    moved=memread[ins.rt]; i+=1; continue
                if ins.rt==0:                                  # sw zero -> CLR
                    # la ROM utilise CLR (ex. 422c 01e5 = CLR.B $1e5(A4), 426e 0012 = CLR.W
                    # $12(A6)) ; on reproduit l'original, donc CLR est aussi sur que chez lui
                    out.append((ins.va,"CLR.%s $%04x(A%d)"%(size,disp,an),
                                enc_clr_an(size,an,disp))); i+=1; continue
                if src is None and ins.rt!=0 and size=='L':
                    src=lui_only(ins_list, i, ins.rt)
                if src and src.kind=='const' and size=='L' and is_code_ptr(src.val):
                    out.append((ins.va,"MOVE.L #CODE_%07x%s,$%04x(A%d)  [pointeur de code]"%(src.val-RUNTIME_BASE,
                                "_ECH" if MEMMODE=='cps2' else "",disp,an), enc_move_imm_an('L',0,an,disp))); i+=1; continue
                if src and src.kind=='const' and size=='L':
                    v=src.val
                    if MEMMODE=='cps2':
                        # (HANDOFF §101) une constante IMPAIRE n'est pas une adresse de donnees : en-tete d'objet
                        # (drapeau 1 | type << 16 : $00780001 libelle du menu de modes, $00760001 « ® » ; 5 sur 4 871)
                        a68=addr_to_68k(v) if not (v & 1) else None   # adresse PS2 -> carte CPS2
                        if a68 is not None: v=a68
                        v=swap32(v)
                    out.append((ins.va,"MOVE.L #$%x,$%04x(A%d)%s"%(v,disp,an,"  [long echange]" if MEMMODE=='cps2' else ""),
                                enc_move_imm_an('L',v,an,disp))); i+=1; continue
                if src is None and ins.rt!=0 and idxbig.get(ins.rt) and idxbig[ins.rt][0]==size and idxbig[ins.rt][1]!=an:
                    sz,n,dn,dsz,dd=idxbig[ins.rt]
                    op=[(SZ_TOP[size]<<12)|((an&7)<<9)|(5<<6)|0x10|(n&7), disp&0xffff]
                    out.append((ins.va,"MOVE.%s $%04x(A%d,D%d.%s),$%04x(A%d)  [deplacement 16 bits]"%(size,dd&0xffff,n,dn,dsz,disp,an),
                                idxbig_seq(size,n,dn,dsz,dd,op))); i+=1; continue
                # (2) valeur d'une table de longs copiee en memoire (memoire -> memoire : pas de SWAP)
                if src is None and ins.rt!=0 and idxread.get(ins.rt) and idxread[ins.rt][0]==size:
                    sz,n,dn,dsz,d8=idxread[ins.rt]           # indexe -> (d16,Am) : copie, pas de SWAP
                    out.append((ins.va,"MOVE.%s %d(A%d,D%d.%s),$%04x(A%d)%s"%(size,d8,n,dn,dsz,disp,an,idx_note(size)),
                                [(SZ_TOP[size]<<12)|((an&7)<<9)|(5<<6)|0x30|(n&7), idx_ext(dn,dsz,d8), disp&0xffff]))
                    i+=1; continue
                if src and src.kind=='tblent' and size=='L':
                    tbl,ix,scale=src.val
                    DATA_TABLES[tbl]='L'
                    out.append((ins.va,"MOVE.L T_%06x(PC,D%d.W),$%04x(A%d)"%(tbl,ix,disp,an),
                                enc_move_pcidx('L',ix,('mem',disp,an)))); i+=1; continue
                if src and src.kind=='imm':
                    iv0=src.val & SZMASK[size]
                    if size=='L': iv0=type_const(an,(d0+ins.simm)&0xffff,iv0)
                    iv=swap32(iv0) if (MEMMODE=='cps2' and size=='L') else iv0
                    out.append((ins.va,"MOVE.%s #$%x,$%04x(A%d)"%(size,iv,disp,an)
                                +("  [long echange]" if iv!=iv0 else ""),
                                enc_move_imm_an(size,iv,an,disp))); i+=1; continue
                if src and src.kind=='bswap32' and size=='L':
                    # (HANDOFF §90) champ octet par octet : octets PS2 = Dn gros-boutiste ; memoire 68K = octets PS2 XOR 1
                    # -> chaque moitie de Dn a octets inverses (ROR.W #8 / SWAP / ROR.W #8 / SWAP), puis restauration
                    n=src.val[1]; bs=[0xe058|n, SWAP_OP|n, 0xe058|n, SWAP_OP|n]
                    out.append((ins.va,"MOVE.L D%d,$%04x(A%d)  [champ octet par octet : octets inverses par moitie]"%(n,disp,an),
                                bs+enc_move_dn_an('L',n,an,disp)+bs))
                    i+=1; continue
                if src and src.kind=='swapd' and size=='L':
                    # (HANDOFF §83) le portage range SWAP(Dn) : en memoire a moities echangees, c'est le long
                    # dans l'ordre NATUREL (liste d'objets du HUD, ROM $21982 'MOVEM.L D0-D1,(A2)') : pas de SWAP
                    n=src.val[1]
                    out.append((ins.va,"MOVE.L D%d,$%04x(A%d)  [ordre naturel]"%(n,disp,an),enc_move_dn_an('L',n,an,disp)))
                    i+=1; continue
                if src and src.kind=='reg68' and src.val and src.val[0]=='D':
                    n=src.val[1]
                    known=REG68.get(src.val)
                    if known is not None and known.kind=='imm' and known.val==0:
                        pass   # le 68K ferait MOVEQ #0,Dn puis MOVE.x Dn,...
                    ws=enc_move_dn_an(size,n,an,disp)
                    if MEMMODE=='cps2' and size=='L':
                        ws=[SWAP_OP|n]+ws+[SWAP_OP|n]         # echanger, ecrire, restaurer
                    out.append((ins.va,("SWAP D%d ; "%n if MEMMODE=='cps2' and size=='L' else "")
                                +"MOVE.%s D%d,$%04x(A%d)"%(size,n,disp,an)
                                +(" ; SWAP D%d"%n if MEMMODE=='cps2' and size=='L' else ""),ws)); i+=1; continue
                unknown+=1; i+=1; continue
        d=dest_reg(ins)
        # (HANDOFF §107) AUDIT : une ECRITURE dans une case de registre 68K (ou des drapeaux) qui arrive ici n'a ete
        # prise par aucun cas -> rien n'est emis (ex. §106 : MOVEA.L abs.L,An perdu). Releve pour la passe d'audit.
        if m in ('sw','sh','sb') and lui.get(ins.rs)==0x7000 and 0x1100<=ins.imm<0x1160:
            _sy=st.get(ins.rt)
            CHUTES.append((ins.va, m, ins.imm, (_sy.kind if _sy else None), bool(absread.get(ins.rt)), bool(memread.get(ins.rt)),
                           bool(idxread.get(ins.rt)), bool(idxbig.get(ins.rt))))
        if d: st.pop(d,None); lui.pop(d,None)
        i+=1
    # (HANDOFF §130) SORTIES LATERALES d'une zone de registre prete (extra_regs.LATERAL) : le branchement qui quitte la
    # zone ailleurs que par sa fin sautait sans restaurer le registre prete (pile desequilibree). Reecrit en
    # 'B<cond inverse> suite ; <restauration, drapeaux preserves> ; BRA cible'.
    import extra_regs as _xr2, re as _re2
    for (lo,hi,slot,kind,reg) in ZONES:
        lat=_xr2.LATERAL.get((slot,lo))
        if not lat: continue
        rws=_zone_restore_ws(slot,kind,reg)
        for b in lat:
            for q,(va,mn,ws) in enumerate(out):
                if va!=b or not ws or not (0x6000<=ws[0]<=0x6fff and (ws[0]&0xff)==0 and len(ws)==1): continue
                mt=_re2.search(r'\(cible ([0-9a-f]+)\)',mn)
                if not mt: continue
                t_=int(mt.group(1),16)
                if lo<=t_<=hi: continue
                rep=[(va,"BRA (cible %08x)  [sortie laterale de zone]"%t_,[0x6000])]
                if (ws[0]&0x0f00)!=0:                       # conditionnel : test inverse vers la suite
                    rep=[(va,"%s (cible %08x)  [sortie laterale : test inverse]"%(mn.split()[0],b+8),[ws[0]^0x0100])]+rep
                out[q:q+1]=rep[:-1]+[(va,"(restauration du registre prete %s%d, sortie laterale)"%(kind,reg),rws)]+rep[-1:]
                LATERAL_REW[0]+=1; LATERAL_OK_VA.add(b)
                break
    if DN_ALU_ON:                                         # (HANDOFF §107) ecritures memoire perdues
        out,_nm=_mem_fix(ins_list, out, inplace_long, abs_addr, addr_to_68k); MEM_FIX[0]+=_nm
    out=[(va, mn.replace('$0000(A','(A'), zero_disp_short(ws) if ws else ws) for va,mn,ws in out]
    out=merge_postinc(out)
    if MEMMODE=='cps2' and _os.environ.get("LONG_POSTINC","1")!="0": out=merge_long_postinc(out, br_targets)
    if MEMMODE=='cps2': out=vram_shift_const(out, br_targets)
    if MEMMODE=='cps2' and VRAM_TABLE_ON: VRAM_TABLE_BUF[0]=buf; out=vram_table_shift(out, br_targets)   # (agent_decor_cammy) mot de table video
    if MEMMODE=='cps2' and _os.environ.get("DROP_SR","1")!="0": out=drop_dead_sr(out)
    if MEMMODE=='cps2': out=byte_streams(out); out=byte_streams_pre(out) if BYTE_PRE_ON else out; out=byte_index_exact(out); out=byte_after_adda(out)   # (agent_ro9) flux decroissant
    if MEMMODE=='cps2' and BYTE_EA_ON: out=byte_streams_ea(out, br_targets)   # (agent_bandeau_A) flux hors Dn
    if DPTR_FIX: out=[dptr_fix(e) for e in out]
    if AUDIT_MEM:                                         # (HANDOFF §107) ecritures memoire sans trace dans la sortie
        _vas={va for va,mn,ws in out}
        for _ix,_x in enumerate(ins_list):
            if _x.m in ('sw','sh','sb','swl','swr','sd') and _x.va not in _vas and _x.rs!=29:
                _b=None
                for _k in range(_ix-1, max(-1, _ix-8), -1):
                    if dest_reg(ins_list[_k])==_x.rs: _b=ins_list[_k]; break
                if _b is not None and _b.m=='lui' and _b.imm==0x7000: continue      # cases de registres : audit a part
                MEM_MISS.append((_x.va, _x.m, _x.imm))
    return out, unknown

def flags_read_first(L, k, lim=40):
    """a partir de L[k], la case RES/C est-elle LUE avant d'etre ecrite (bloc lineaire) ?"""
    for y in L[k:k+lim]:
        if y.m in ('lw','lh','lb') and (y.simm & 0xffff) in (RES_SLOT, NFLG_SLOT): return True
        if y.m=='sw' and (y.simm & 0xffff) in (RES_SLOT, NFLG_SLOT): return False
        if y.m in ('jal','jalr','jr'): return False
    return False

def sign_ext_inplace(L, i):
    """L[i] = sh/sw r,Dk : r = extension de signe de Dk lu en octet/mot -> 'W' (EXT.W), 'L' (EXT.L),
    'WL' (octet -> long), sinon None"""
    st_=L[i]; j=_producer(L, i, st_.rt, 8)
    if j is None or L[j].m!='dsra32': return None
    sa=L[j].sa; y=_producer(L, j, L[j].rt, 4)
    if y is None or L[y].m!='dsll32' or L[y].sa!=sa: return None
    z=_producer(L, y, L[y].rt, 6)
    if z is None or L[z].m not in ('lb','lh') or (L[z].simm & 0xffff)!=(st_.simm & 0xffff): return None
    if L[z].m=='lb' and sa==24: return 'W' if st_.m=='sh' else 'WL'
    if L[z].m=='lh' and sa==16 and st_.m=='sw': return 'L'
    return None

def lea_table_index(L, i):
    """L[i] = sw r,An : r = addu(sext16(Dk), T) avec T adresse de DONNEES -> (T, k), sinon None"""
    j=_producer(L, i, L[i].rt, 8)
    if j is None or L[j].m!='addu': return None
    const=None; dk=None
    for r in (L[j].rs, L[j].rt):
        p=_producer(L, j, r, 8)
        if p is None: return None
        x=L[p]
        if x.m in ('addiu','ori') and x.rs==r:
            q=_producer(L, p, r, 4)
            if q is not None and L[q].m=='lui':
                const=(L[q].imm<<16)+(x.simm if x.m=='addiu' else x.imm); continue
            return None
        if x.m=='dsra32':
            y=_producer(L, p, x.rt, 4)
            if y is None or L[y].m!='dsll32': return None
            z=_producer(L, y, L[y].rt, 4)
            if z is None or L[z].m!='lh': return None
            sn=slot_name(L[z].simm & 0xffff)
            if not sn or sn[0]!='D': return None
            dk=sn[1]; continue
        return None
    if const is None or dk is None or not (CODE_END_RT <= const < DATA_END_RT): return None
    if addr_to_68k(const) is None: return None
    return const, dk

_BRANCHES=('beq','bne','beql','bnel','bgez','bltz','blez','bgtz','bgezl','bltzl','blezl','bgtzl')
def epilogue_is_target(L, i, targets):
    """le 'jr ra' L[i] ou une instruction de son epilogue (ld ra, addiu sp, nop) est-il une cible ?"""
    j=i
    while j>=0:
        x=L[j]
        if x.va in targets: return True
        if j<i and not ((x.m=='ld' and x.rt==31) or (x.m=='addiu' and x.rt==29 and x.rs==29)
                        or (x.m=='sll' and x.w==0) or (x.m=='lui' and x.imm==0x7000)): return False
        j-=1
    return False

DBG_VA = int(_os.environ.get('DBG_VA','0'),16)
DBG_RANGE = tuple(int(x,16) for x in _os.environ['DBG_RANGE'].split('-')) if _os.environ.get('DBG_RANGE') else None
# (HANDOFF §80) domicile memoire de A8 : un A8 pose par l'appelant (parametre) survit a l'appel
A8_HOME = int(_os.environ.get("A8_HOME","87e0"),16) if _os.environ.get("A8_HOME","87e0")!="none" else None
ZONE_OPEN = {}             # debut de zone A8 -> fin : un retour de boucle INTERNE saute l'ouverture (assemble.py)
D8_HOME = int(_os.environ.get("D8_HOME","87f0"),16) if _os.environ.get("D8_HOME","87f0")!="none" else None
PRIV_SLOT = 0x114c
def private_stack(L):
    """PILE PRIVEE (HANDOFF §72) : empiler 'lw S,0x114C ; addiu T,S,-4 ; sw T,0x114C ; sw V,0(T)' (V lu dans
    une case de registre) ; depiler 'lw S,0x114C ; addiu T,S,4 ; sw T,0x114C ; lw V,0(S) ; sw V,case'.
    Rend {va: ('push'|'pop', case) | 'skip'} : l'action sur la derniere instruction, les autres sautees."""
    act={}
    def base_is_priv(k, r):
        j=_producer(L, k, r, 6)
        return j if (j is not None and L[j].m=='lw' and (L[j].simm & 0xffff)==PRIV_SLOT) else None
    for k,x in enumerate(L):
        # empiler
        if x.m=='sw' and x.simm==0:
            j=_producer(L, k, x.rs, 6)
            if j is None or L[j].m!='addiu' or L[j].simm!=-4: continue
            jl=base_is_priv(j, L[j].rs)
            if jl is None: continue
            v=_producer(L, k, x.rt, 10)
            if v is None or L[v].m!='lw' or not (0x1100<=(L[v].simm & 0xffff)<0x1148): continue
            act[x.va]=('push', L[v].simm & 0xffff)
            for y in L[jl:k]:
                if (y.m in ('lw','sw') and (y.simm & 0xffff)==PRIV_SLOT) or y is L[j]: act.setdefault(y.va,'skip')
        # depiler
        if x.m=='sw' and 0x1100<=(x.simm & 0xffff)<0x1148:
            v=_producer(L, k, x.rt, 6)
            if v is None or L[v].m!='lw' or L[v].simm!=0: continue
            jl=base_is_priv(v, L[v].rs)
            if jl is None: continue
            act[x.va]=('pop', x.simm & 0xffff)
            for y in L[jl:k]:
                if (y.m in ('lw','sw') and (y.simm & 0xffff)==PRIV_SLOT) or y is L[v] \
                   or (y.m=='addiu' and y.rs==L[jl].rt and y.simm==4):
                    act.setdefault(y.va,'skip')
    return act

def hautes_moities(L):
    """(HANDOFF §82) acces a la MOITIE HAUTE d'un registre D (case +2 : 'lh/sh $112E' = mot haut de D2), forme
    des MOVE.L decoupes par le recompilateur (ex. constructeurs de listes d'objets : 'MOVE.L (A0)+,D2' charge
    code:attributs). Avant : traite comme le mot bas (le code etait ecrase par l'attribut). -> pseudo-instruction
    'swapd' (SWAP Dn) avant l'acces, acces au mot bas, et 'swapd' apres le dernier usage : l'ecriture de la case
    pour 'sh', ou le premier rangement de la valeur lue (suivie a travers or/addu/and...) pour 'lh'."""
    from mips import Ins
    class Swapd:
        __slots__=('va','w','op','rs','rt','rd','sa','fn','imm','simm','tgt','m')
        def __init__(s, va, n):
            s.va=va; s.w=0; s.op=-1; s.rs=0; s.rt=n; s.rd=0; s.sa=0; s.fn=0; s.imm=0; s.simm=0; s.tgt=0; s.m='swapd'
    out=[]; apres={}; ouvert=set()
    lui7=set()
    for k,x in enumerate(L):
        if x.m=='lui': (lui7.add if x.imm==0x7000 else lui7.discard)(x.rt)
        o=x.imm & 0xffff
        haut = x.m in ('lh','lhu','sh') and x.rs in lui7 and 0x1124<=o<=0x1143 and (o-0x1124)%4==2
        n=(o-0x1124)//4 if haut else None
        if haut and n in ouvert:                       # groupe deja permute : acces au mot bas
            out.append(Ins(x.va, x.w-2))
            for m_ in apres.pop(k, ()): out.append(Swapd(x.va, m_)); ouvert.discard(m_)
            continue
        if not haut:
            out.append(x)
            for m_ in apres.pop(k, ()): out.append(Swapd(x.va, m_)); ouvert.discard(m_)
            continue
        out.append(Swapd(x.va, n)); out.append(Ins(x.va, x.w-2))
        if x.m=='sh': out.append(Swapd(x.va, n)); continue
        ouvert.add(n)
        live={x.rt}; fin=None
        for j in range(k+1, min(len(L), k+16)):
            y=L[j]
            if y.m in ('sh','sb','sw') and y.rt in live: fin=j; break
            if y.m in ('addu','or','and','xor','subu','daddu') and ({y.rs,y.rt} & live): live.add(y.rd); continue
            if y.m in ('addiu','andi','ori','xori','dsll32','dsra32','sll','sra','srl') and y.rs in live and y.m[0]!='d': live.add(y.rt); continue
            if y.m in ('dsll32','dsra32','sll','sra','srl') and y.rt in live: live.add(y.rd); continue
        apres.setdefault(fin if fin is not None else k, []).append(n)
    return out

def slot_ori(L):
    """(HANDOFF §78) case du banc de registres adressee par 'ori rX,rL,off' (rL = lui 0x7000) puis
    'lw/sw r,0(rX)' (ex. MOVEA.L $E6(A6),A3 non aligne, mips 0xF51AC) : on reecrit en 'lui rX,0x7000'
    et on reporte 'off' sur les acces suivants par rX (forme habituelle 'lui ; sw r,off(rX)')."""
    from mips import Ins
    out=list(L); n=len(out)
    LS=('lb','lbu','lh','lhu','lw','sb','sh','sw')
    for k in range(n):
        x=out[k]
        if x is None or x.m!='ori' or x.rs==0 or not (0x1100<=x.imm<0x1160): continue
        j=_producer(out, k, x.rs, 8)
        if j is None or out[j].m!='lui' or out[j].imm!=0x7000: continue
        rX=x.rt; off=x.imm; uses=[]
        for q in range(k+1, min(n, k+16)):
            y=out[q]
            if y.m in LS and y.rs==rX: uses.append(q)
            if dest_reg(y)==rX or y.m in ('jal','jalr','jr','j') or y.m in _BRANCHES: break
        if not uses or any(not (-0x8000 <= out[q].simm+off <= 0x7fff) for q in uses): continue
        out[k]=Ins(x.va, (0x0f<<26)|(rX<<16)|0x7000)              # lui rX,0x7000
        for q in uses:
            y=out[q]; out[q]=Ins(y.va, (y.w & 0xffff0000) | ((y.simm+off) & 0xffff))
    return out

def unaligned_pairs(L):
    """ACCES LONGS NON ALIGNES (HANDOFF §67) : le recompilateur ecrit un long 68K a un deplacement
    pair non multiple de 4 avec swl/swr (lwl/lwr pour lire) : 'swl r,d+3(b) ; swr r,d(b)'. On remplace la
    paire par un 'sw r,d(b)' (resp. 'lw') synthetique, que les traitements existants traduisent
    (ex. MOVE.L (A0),$32(A6), ROM $2A774). 80 + 30 paires dans SFA3."""
    from mips import Ins
    out=list(L); n=len(out)
    for k in range(n):
        x=out[k]
        if x is None or x.m not in ('swl','swr','lwl','lwr'): continue
        j=k+1
        while j<n and out[j] is not None and out[j].m=='sll' and out[j].w==0: j+=1
        if j>=n or out[j] is None: continue
        y=out[j]
        pair={'swl':'swr','swr':'swl','lwl':'lwr','lwr':'lwl'}[x.m]
        if y.m!=pair or y.rs!=x.rs or y.rt!=x.rt: continue
        l,r=(x,y) if x.m in ('swl','lwl') else (y,x)
        if l.simm!=r.simm+3: continue
        op=0x2b if x.m in ('swl','swr') else 0x23
        out[k]=Ins(x.va, (op<<26)|(x.rs<<21)|(x.rt<<16)|(r.simm & 0xffff))
        out[j]=Ins(y.va, 0)                               # nop a la place de la 2e moitie
    return out

def dptr_fix(e):
    """MOVEA.L <memoire ou Dn>,An -> + JSR (conversion An).W (voir DPTR_FIX)"""
    va,mn,ws=e
    if not ws or (ws[0] & 0xf1c0)!=0x2040: return e
    mode,reg=(ws[0]>>3)&7,ws[0]&7; n=(ws[0]>>9)&7
    if mode==1 or (mode==7 and reg in (2,3,4)) or (mode in (2,3,4,5,6) and reg==7) or n not in DPTR_FIX: return e
    return (va, mn+" ; JSR CONV_A%d"%n, list(ws)+[0x4eb8, DPTR_FIX[n]])

if __name__=="__main__":
    ro3=open("<workspace>/anthology_extract/decompressed/ro3_usa_prog68k.bin","rb").read()
    S="<workspace>/work/cps2"
    k68=open(S+"/sfa3_prog.bin","rb").read()
    out,unk = translate(ro3, 0x201fa8, 0x202200)
    print("=== traduction de MIPS 0x201fa8 (%d instructions 68K emises) ==="%len(out))
    words=[]
    for va,mn,ws in out:
        print("  %08x   %-28s  %s"%(va,mn,' '.join('%04x'%x for x in ws)))
        words+=ws
    print()
    ref=struct.unpack('>%dH'%(len(words)), k68[0x9350:0x9350+len(words)*2])
    print("=== comparaison avec le vrai 68K @0x9350 ===")
    print("  produit :", ' '.join('%04x'%x for x in words[:20]))
    print("  reel    :", ' '.join('%04x'%x for x in ref[:20]))
    same=sum(1 for a,b in zip(words,ref) if a==b)
    print("\n  %d/%d mots identiques (%.0f%%)"%(same,len(words),100*same/max(1,len(words))))
