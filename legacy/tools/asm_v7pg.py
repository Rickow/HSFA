# Cave v7 : UPST -> repoint bank + palettes (chaque frame) ; V7PG -> copie pools/listes (one-shot).
# Hook 0x1d1848 = jal 0x1c0400 ; tail-call j 0x1d18a0. Preserve a0-a3+ra (t-regs libres, valide v6).
R={'zero':0,'at':1,'v0':2,'v1':3,'a0':4,'a1':5,'a2':6,'a3':7,
   't0':8,'t1':9,'t2':10,'t3':11,'t4':12,'t5':13,'t6':14,'t7':15,
   's0':16,'ra':31,'t8':24,'t9':25,'sp':29}
def lui(rt,imm):   return 0x3c000000|(R[rt]<<16)|(imm&0xffff)
def ori(rt,rs,imm):return 0x34000000|(R[rs]<<21)|(R[rt]<<16)|(imm&0xffff)
def addiu(rt,rs,imm):return 0x24000000|(R[rs]<<21)|(R[rt]<<16)|(imm&0xffff)
def lw(rt,off,rs): return 0x8c000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def sw(rt,off,rs): return 0xac000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def bne(rs,rt,off):return 0x14000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def beq(rs,rt,off):return 0x10000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def j_(t):   return 0x08000000|((t>>2)&0x3ffffff)
def jal(t):  return 0x0c000000|((t>>2)&0x3ffffff)
NOP=0

BASE=0x1c0400
code=[]
lbl={}
def emit(*ws):
    for w in ws: code.append(w)
def here(): return BASE+len(code)*4

# HOOK ENTREE 0x1d0750 (fonction rendu BG, chaque frame, AVANT la boucle de couches mode3/2/1) :
# 0x1d0750 = j cave ; delay slot = lui v0,0x1e (execute, on ne touche pas v0) ; le cave emule
# l'instruction deplacee addiu sp,-0x70 puis reprend a 0x1d0758 (sd ra,0x60(sp)).
emit(addiu('sp','sp',-0x70))   # instruction deplacee de 0x1d0750
emit(addiu('sp','sp',-0x20), sw('ra',0,'sp'),
     sw('a0',4,'sp'), sw('a1',8,'sp'), sw('a2',0xc,'sp'), sw('a3',0x10,'sp'))
# v7.37 : SLOT 11 DU DESCRIPTEUR v8 POSE EN RAM (plus AUCUNE modif du zb : la recompression du zb
# cassait le boot -- le zb est le BIOS CPS2 charge par le shell. Ici zb reste VANILLA bit-a-bit).
# desc v8 = 0x1dbc30 ; slot 11 = desc+0x98 = 0x1dbcc8 ; entree {u16 type, u16 file, u32 dst, u32 stg}
# type 3 = load BRUT -> dst. Pose AVANT le check UPST (au 1er passage le package n'est pas charge).
# t7 = 0x1580000 ; check 'UPST'
emit(lui('t7',0x0158), lw('t4',0,'t7'),
     lui('t5',0x5453), ori('t5','t5',0x5055))
FIX_UPST=len(code); emit(0,NOP)   # bne t4,t5,EXIT (patch)
# v7.4 : PLUS DE REPOINT (le repoint cassait le HUD : fenetres dynamiques >=0x16c00 hors package).
# A la place : COPIE de la bank residente Upper (package+0x10, 0x2d8000 octets) SUR 0xdb4000,
# one-shot gate u16[0xb84178]==8 (build du 1er match) + garde [0x186a004]!=0 -> une seule fois.
def lhu(rt,off,rs): return 0x94000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def sh(rt,off,rs):  return 0xa4000000|(R[rs]<<21)|(R[rt]<<16)|(off&0xffff)
def slti(rt,rs,imm): return 0x28000000|(R[rs]<<21)|(R[rt]<<16)|(imm&0xffff)
def mult(rs,rt): return (R[rs]<<21)|(R[rt]<<16)|0x18
def divi(rs,rt): return (R[rs]<<21)|(R[rt]<<16)|0x1a
def mflo(rd): return (R[rd]<<11)|0x12
def sll(rd,rt,sa): return (R[rt]<<16)|(R[rd]<<11)|((sa&31)<<6)
emit(lui('t2',0x00b8), ori('t2','t2',0x4178), lhu('t4',0,'t2'), ori('t5','zero',8))
BR_NOT8=len(code); emit(0,NOP)                       # bne t4,t5 -> saute conteneur+bank (patch)
# repoint conteneur SCR3 [0x1dc2f4] = 0x186c760 (CHAQUE frame en combat : le build le reecrit)
emit(lui('t2',0x0186), ori('t2','t2',0xc760),
     lui('t3',0x001d), ori('t3','t3',0xc2f4),
     sw('t2',0,'t3'), sw('t2',4,'t3'), sw('t2',8,'t3'))   # classes 5/6/7 (+0x44/48/4c variantes)
# v7.41 : STAGING FIX - corriger les 3 blocs staging CPS2 (SCR1/2/3) a la SOURCE (amont du
# convertisseur 1d1300) chaque frame. Le recompositeur versus ecrit du versus dans 0xbac400/800/c00 ;
# on l'ecrase avec les blocs z5 embarques dans la section (RAM 0x186bb60/f60/0x186c360, 0x400 chacun).
# -> convertisseur produit du correct sur les DEUX parites = couleurs SCR1/2/3 justes + PLUS DE
# CLIGNOTEMENT (c'etait la correction aval work/twin une frame/2 qui perdait la course au convertisseur).
for _src, _dst in ((0x186bb60,0xbac400),(0x186bf60,0xbac800),(0x186c360,0xbacc00)):
    emit(lui('t9',_src>>16), ori('t9','t9',_src&0xffff),
         lui('t2',_dst>>16), ori('t2','t2',_dst&0xffff),
         ori('t1','zero',0x100))
    _L=len(code)
    emit(lw('t4',0,'t9'), sw('t4',0,'t2'),
         addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
    emit(bne('t1','zero',(_L-len(code)-1)&0xffff), NOP)
# palettes SCR3 (rangees travail 0x60-0x7f, conversion auto PARTIELLE seulement) : copie per-frame
# package rows 0x60-0x7f (0x1869010) -> work 0x1ddc00 + twin 0x1e1c00 (0x200 mots)
emit(lui('t9',0x0186), ori('t9','t9',0x9010),
     lui('t2',0x001d), ori('t2','t2',0xdc00),
     lui('t3',0x001e), ori('t3','t3',0x1c00),
     ori('t1','zero',0x200))
LP=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'), sw('t4',0,'t3'),
     addiu('t9','t9',4), addiu('t2','t2',4), addiu('t3','t3',4),
     addiu('t1','t1',-1))
emit(bne('t1','zero',(LP-len(code)-1)&0xffff), NOP)
# APPEND des 182 entrees objets Blanka (table 0x18bb460) a la fin de la liste sprites 0x70002000.
# Purement ADDITIF : on ne touche a aucune entree existante (persos/UI/objets versus intacts),
# on remplace juste le terminateur {0x8000,0x8000} et on en pose un nouveau apres.
# GATE COMBAT-STAGE-8 : ring[0xba4000] == notre page ciel composee (constante unique post-build).
# Menus / autres etats : on saute TOUT le walk (pas de kill = menus intacts) et flag=0 (cave2 inerte).
emit(lui('t2',0x00ba), ori('t2','t2',0x4000), lw('t4',0,'t2'),
     lui('t5',0x0000), ori('t5','t5',0x59e7))
BR_NORING=len(code); emit(0,NOP)                     # bne t4,t5 -> WALK_SKIP (patch)
# v7.42 : RING SCR1 = FOND JUNGLE z5 (au lieu du blank). Le SCR1 (mode 1, tuiles unies coloriees par
# rows 0x20-0x3f = le degrade brumeux) EST le fond de jungle en z5 ; le blank v7.24 le supprimait.
# ring SCR1 z5 embarque dans la bank package inutilisee @0x1590000 (package+0x10000, zone bank basse
# jamais copiee par le cave qui ne prend que le trou remap 0x2c0000+). Copie -> 0xba0000 chaque frame
# (ecrase le ciel psychedelique versus, apres le compositeur). Tuiles SCR1 == z5 (verifie), palettes
# rows 0x20-0x3f corrigees par le staging-fix v7.41.
emit(lui('t9',0x0159), ori('t9','t9',0x0000),
     lui('t2',0x00ba), ori('t2','t2',0x0000), ori('t1','zero',0x1000))
LS1=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'), addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
emit(bne('t1','zero',(LS1-len(code)-1)&0xffff), NOP)
# ===== WALK + KILL + INSERTION A/B (emission a labels, 2 passes) =====
def sltu(rd,rs,rt): return (R[rs]<<21)|(R[rt]<<16)|(R[rd]<<11)|0x2b
def srl(rd,rt,sa): return (R[rt]<<16)|(R[rd]<<11)|((sa&31)<<6)|2
def sltiu_(rt,rs,imm): return 0x2c000000|(R[rs]<<21)|(R[rt]<<16)|(imm&0xffff)
_lbl={}; _fix=[]
def L(name): _lbl[name]=len(code)
def B(op,rs,rt,name):
    _fix.append((len(code),op,rs,rt,name)); emit(0,NOP)
emit(lui('t5',0x001c), sw('zero',0x0ff4,'t5'))            # scratch CPOS=0
emit(lui('t2',0x7000), ori('t2','t2',0x2000), ori('t1','zero',0x385),
     lui('t6',0x8000), ori('t6','t6',0x8000), ori('t3','zero',0))
L('WK')
emit(lw('t4',0,'t2'))
B('beq','t4','t6','FOUND')
emit(lhu('t5',2,'t2'), srl('t0','t5',13), ori('t5','zero',1))
B('bne','t0','t5','CHK23')                                # pas classe 1 -> persos ?
emit(lhu('t0',4,'t2'), sltiu_('t5','t0',0x1000))
B('bne','t5','zero','NEXT')
emit(sltiu_('t5','t0',0x4700))
B('beq','t5','zero','NEXT')
# v7.25 : PLUS d'exception 0x1020 - ces entrees = les quads d'ASSOMBRISSEMENT du versus (les zones
# noires !), pas les ombres persos (qui viennent du double-dessin du drawer). z5 n'en a aucune.
emit(sh('zero',4,'t2'), addiu('t3','t3',1))
B('beq','zero','zero','NEXT')
L('CHK23')
emit(addiu('t5','t0',-2), sltiu_('t5','t5',2))
B('beq','t5','zero','NEXT')
emit(lui('t5',0x001c), lw('t0',0x0ff4,'t5'))
B('bne','t0','zero','NEXT')
emit(sw('t2',0x0ff4,'t5'))
L('NEXT')
emit(addiu('t2','t2',8), addiu('t1','t1',-1))
B('bne','t1','zero','WK')
B('beq','zero','zero','APPEND_END')                       # pas de terminateur
L('FOUND')
emit(lui('t5',0x001c), sw('t3',0x0ff8,'t5'))              # flag combat
B('beq','t3','zero','APPEND_END')
emit(sltiu_('t5','t1',0xea))
B('bne','t5','zero','APPEND_END')                         # pas la place
emit(lui('t5',0x001c), lw('t4',0x0ff4,'t5'))              # CPOS
B('bne','t4','zero','HAVE')
emit(addiu('t4','t2',0))                                  # pas de persos -> CPOS=T
L('HAVE')
emit(addiu('t0','t2',-8))                                 # p = T-8
L('SH')
emit(sltu('t5','t0','t4'))
B('bne','t5','zero','SHDONE')                             # p < CPOS -> fini
emit(lw('t5',0,'t0'), sw('t5',0x5f8,'t0'),
     lw('t5',4,'t0'), sw('t5',0x5fc,'t0'),
     addiu('t0','t0',-8))
B('beq','zero','zero','SH')
L('SHDONE')
emit(lui('t9',0x018b), ori('t9','t9',0xb460), ori('t1','zero',191))
L('CA')
emit(lw('t5',0,'t9'), sw('t5',0,'t4'), lw('t5',4,'t9'), sw('t5',4,'t4'),
     addiu('t9','t9',8), addiu('t4','t4',8), addiu('t1','t1',-1))
B('bne','t1','zero','CA')
emit(addiu('t4','t2',0x5f8), ori('t1','zero',38))         # B apres le bloc persos decale
L('CB')
emit(lw('t5',0,'t9'), sw('t5',0,'t4'), lw('t5',4,'t9'), sw('t5',4,'t4'),
     addiu('t9','t9',8), addiu('t4','t4',8), addiu('t1','t1',-1))
B('bne','t1','zero','CB')
emit(sw('t6',0,'t4'))                                     # terminateur a T+0x728
L('APPEND_END')
for pos,op,rs,rt,name in _fix:
    off=(_lbl[name]-pos-1)&0xffff
    code[pos]=(bne(rs,rt,off) if op=='bne' else beq(rs,rt,off))
APPEND_END=_lbl['APPEND_END']
# chemin normal : sauter le bloc WALK_SKIP (2 instrs)
emit(beq('zero','zero',3), NOP)
# WALK_SKIP : flag=0 puis continue vers la garde bank
WS=len(code)
emit(lui('t5',0x001c), sw('zero',0x0ff8,'t5'))
code[BR_NORING]=bne('t4','t5',(WS-BR_NORING-1)&0xffff)
emit(lui('t8',0x0186), ori('t8','t8',0xa000))
emit(lw('t4',4,'t8'))                                # garde one-shot bank
BR_DONE=len(code); emit(0,NOP)                       # bne t4,zero -> saute (patch)
# v7.13 : copie SEULEMENT le trou remap (0x2c0000-0x2cf580) = 62 Ko. Le reste de la bank reste
# NATIF -> UI propre, objets versus propres (art versus par-dessus la jungle), menus quasi intacts.
emit(lui('t9',0x0184), ori('t9','t9',0x0010),        # src = 0x1840010 (pkg+0x10+0x2c0000)
     lui('t2',0x0107), ori('t2','t2',0x4000),        # dst = 0x1074000 (0xdb4000+0x2c0000)
     ori('t1','zero',0x3d60))                        # count mots (decor SCR2 : jusqu'a 0x2cf580)
LBK=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'),
     addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
emit(bne('t1','zero',(LBK-len(code)-1)&0xffff), NOP)
# v7.43 : TUILES SCR1 (fond jungle) portees dans la bank z9 (one-shot). plage 0x13ce-0x1731 (868
# tuiles, offset bank 0x279c0-0x2e620, APRES les fenetres persos 0x1e300) + tuile isolee 0x7b8.
# En z9 ces offsets = SCR1 versus (ciel psychedelique) -> remplaces par la jungle z5. Sources
# embarquees dans la bank package inutilisee (0x1594000 plage, 0x159b000 tuile).
emit(lui('t9',0x0159), ori('t9','t9',0x4000),        # src plage = 0x1594000
     lui('t2',0x00dd), ori('t2','t2',0xb9c0),        # dst = 0xddb9c0 (0xdb4000+0x279c0)
     ori('t1','zero',0x1b20))                         # 0x6c80 octets
LSC1=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'), addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
emit(bne('t1','zero',(LSC1-len(code)-1)&0xffff), NOP)
emit(lui('t9',0x0159), ori('t9','t9',0xb000),        # src tuile = 0x159b000
     lui('t2',0x00dc), ori('t2','t2',0x3700),        # dst = 0xdc3700 (0xdb4000+0xf700)
     ori('t1','zero',8))
LSC1b=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'), addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
emit(bne('t1','zero',(LSC1b-len(code)-1)&0xffff), NOP)
# GRILLE OBJETS (tuiles 0x2000-0x2fff, zone libre du versus) : pkg 0x18bbdf0 -> 0xeb4000
emit(lui('t9',0x018b), ori('t9','t9',0xbdf0),
     lui('t2',0x00ff), ori('t2','t2',0x4000),
     ori('t1','zero',0x2a00))
LGR=len(code)
emit(lw('t4',0,'t9'), sw('t4',0,'t2'),
     addiu('t9','t9',4), addiu('t2','t2',4), addiu('t1','t1',-1))
emit(bne('t1','zero',(LGR-len(code)-1)&0xffff), NOP)
emit(ori('t4','zero',1), sw('t4',4,'t8'))            # garde posee
SKIP_BANK=None  # cible des 2 branches = ici
BANK_END=len(code)
# one-shot : t8 = 0x186a000 ; check 'V7PG' (56 37 50 47 -> LE 0x47503756)
emit(lui('t8',0x0186), ori('t8','t8',0xa000), lw('t4',0,'t8'),
     lui('t5',0x4750), ori('t5','t5',0x3756))
FIX_V7=len(code); emit(0,NOP)     # bne t4,t5,EXIT (patch)
def copy(src_off,dst,count,dst2=None):
    emit(addiu('t9','t8',src_off), lui('t2',dst>>16), ori('t2','t2',dst&0xffff))
    if dst2: emit(lui('t3',dst2>>16), ori('t3','t3',dst2&0xffff))
    emit(ori('t1','zero',count))
    L=len(code)
    ws=[lw('t4',0,'t9'), sw('t4',0,'t2')]
    if dst2: ws.append(sw('t4',0,'t3'))
    ws+=[addiu('t9','t9',4), addiu('t2','t2',4)]
    if dst2: ws.append(addiu('t3','t3',4))
    ws.append(addiu('t1','t1',-1))
    emit(*ws)
    emit(bne('t1','zero',(L-len(code)-1)&0xffff), NOP)
copy(0x0010, 0x640c60, 0x300)              # pages SCR2 1-4 -> slots 1-4
copy(0x0c10, 0x643960, 0xc0)               # page SCR2 ciel -> slot 0x10 (slot 0 partage INTACT)
copy(0x0f10, 0x696018, 4, dst2=0xb83250)   # liste SCR2 16B : blob round1 + COPIE RUNTIME
copy(0x0f10, 0x696028, 4, dst2=0x696038)   # listes SCR2 VARIANTES rounds 2/3 (blob 0x696028/0x696038 !)
copy(0x0f20, 0x6446e0, 0x300)              # pool SCR3 -> slots 0x0e-0x1d (0x643c60+0xe*0xc0, fin 0x6452e0)
copy(0x1b20, 0x696050, 16, dst2=0x696090)  # liste SCR3 64B (+0x0e) copies blob 1+2
copy(0x1b20, 0x6960d0, 16, dst2=0xb832d0)  # liste SCR3 : 3e copie blob + COPIE RUNTIME 0xb832d0
copy(0x1b60, 0x660660, 0x100)              # palA -> bloc stage 0x10 (inutilise avec lock)
copy(0x1f60, 0x662680, 0x100)              # palB -> bloc idx2 (inutilise avec lock)
copy(0x2360, 0x6646a0, 0x100)              # palC (SCR3 rangees 0x60-0x7f) -> bloc versus table 0x664280
# redirections s16 stage 8 POUR TOUTES LES VARIANTES [0xb88100] in {0,2,4,6} :
# tableA idx 8/a/c/e -> bloc 0x420 ; tableB idem -> 0x820 (b88100 varie avec la rotation naturelle !)
emit(lui('t2',0x0066), ori('t2','t2',0x0248), ori('t4','zero',0x420),
     sh('t4',0,'t2'), sh('t4',2,'t2'), sh('t4',4,'t2'), sh('t4',6,'t2'))
emit(lui('t2',0x0066), ori('t2','t2',0x1e68), ori('t4','zero',0x820),
     sh('t4',0,'t2'), sh('t4',2,'t2'), sh('t4',4,'t2'), sh('t4',6,'t2'))
# PAS de trigger : le magic se rearme a chaque chargement (e527 recharge) -> copie pendant
# l'ecran de chargement, AVANT le layout naturel (chemin b674f8 de fin de load). Le reset
# dirty 62/63 est ECARTE (teste s09 : il vide le ring sans relancer le layout des pages).
emit(sw('zero',0,'t8'))                    # clear magic = one-shot par cycle de load
# EXIT
EXIT=here()
emit(lw('a0',4,'sp'), lw('a1',8,'sp'), lw('a2',0xc,'sp'), lw('a3',0x10,'sp'),
     lw('ra',0,'sp'), addiu('sp','sp',0x20),
     j_(0x1d0758), NOP)
# patch les 2 branches vers EXIT
for FIX in (FIX_UPST,FIX_V7):
    off=(EXIT-(BASE+FIX*4)-4)>>2
    code[FIX]=bne('t4','t5',off&0xffff)
# branches du bloc bank -> BANK_END
code[BR_NOT8]=bne('t4','t5',(BANK_END-BR_NOT8-1)&0xffff)
code[BR_DONE]=bne('t4','zero',(BANK_END-BR_DONE-1)&0xffff)

# ===== CAVE2 : post-convertisseur palettes (hook 0x1d0818 jal->ici) =====
CAVE2=here()
emit(addiu('sp','sp',-0x10), sw('ra',0,'sp'))
emit(jal(0x1d1300), NOP)                              # l'appel original
emit(lui('t5',0x001c), lw('t4',0x0ff8,'t5'))          # flag combat ?
BR_C2X=len(code); emit(0,NOP)                         # beq t4,zero -> C2X
def palloop(srcaddr,dst,twin,count):
    emit(lui('t9',srcaddr>>16), ori('t9','t9',srcaddr&0xffff),
         lui('t2',dst>>16), ori('t2','t2',dst&0xffff),
         lui('t3',twin>>16), ori('t3','t3',twin&0xffff),
         ori('t1','zero',count))
    L=len(code)
    emit(lw('t4',0,'t9'), sw('t4',0,'t2'), sw('t4',0,'t3'),
         addiu('t9','t9',4), addiu('t2','t2',4), addiu('t3','t3',4),
         addiu('t1','t1',-1))
    emit(bne('t1','zero',(L-len(code)-1)&0xffff), NOP)
palloop(0x18bbbb0,0x1dcac0,0x1e0ac0,0x30)   # rows 0x1b-0x1d (objets)
palloop(0x18bbc70,0x1dc7c0,0x1e07c0,0x20)   # rows 0x0f-0x10 (arbre/serpent)
palloop(0x18bbd30,0x1dc880,0x1e0880,0x30)   # rows 0x12-0x14
palloop(0x18c65f0,0x1dc940,0x1e0940,0x30)   # rows 0x15-0x17 (ecrasees par les palettes persos selon match)
# v7.28 : fenetre SCR3 (rows 0x60-0x7f) : le TWIN garde les palettes VERSUS (la conversion C du twin
# n'a lieu qu'avant nos writes one-shot -> fige) alors que le work est correct (circuit natif via bloc
# 0x6646a0 ecrase). Fix : copie work->twin post-1d1300 chaque frame (une frame sur deux le fond SCR3
# etait dessine avec les couleurs versus = le "fond noir/sombre").
palloop(0x1ddc00,0x1e1c00,0x1e1c00,0x200)   # rows 0x60-0x7f : work -> twin (double-write twin, ok)
palloop(0x1dd400,0x1e1400,0x1e1400,0x200)   # v7.35 rows 0x40-0x5f (fenetre B SCR2) : work -> twin
# (meme mecanisme que 0x60-0x7f : twin B fige versus -> teinte bleue 1 frame/2 sur le decor)
C2X=len(code)
code[BR_C2X]=beq('t4','zero',(C2X-BR_C2X-1)&0xffff)
emit(lw('ra',0,'sp'), addiu('sp','sp',0x10))
emit(0x03e00008, NOP)                                 # jr ra
# ===== CAVE3 v7.36 : mapping camera versus -> fenetres z5. CALIBRATION (2026-07-19) :
# camera versus = desc2x in [0,0x180] (butees mesurees aux coins par marche tandem) ; les courses
# SCR2 z5 et versus sont IDENTIQUES (s2 = cam tel quel) ; s1 = 0x152+cam*23/96 ; s3 = 0x124+cam*23/48
# (verifie exact aux 3 points z5 : cam 0xc0 -> 0x180/0xc0/0x180). desc1x versus = couche ANIMEE
# (derive continue, ne JAMAIS l'utiliser). hook 0x1d0784 (jal 0x1d0a20 = collecte+pose des bandes, avec le writer-desc
# AU MILIEU via (*[maitre+0xc])(1) -> la bande 1 est collectee avec le desc frais NON clampe).
# CAVE3 = jal 0x1d0a20 puis RE-pose des champs X (scrolls+passes+phases) des DEUX bandes,
# valeurs natives z5 : s1=clamp(+0x18,[0x152,0x1ae]) ; s2=rel*96/23 ; s3=rel*2+0x124 ;
# d4=(s1+0x40)&0x1ff ; d8=(s2+0x40)&0x3ff ; dc=(s3+0x40)&0x7ff ; phases f4/f8/fc = &7/&f/&1f.
def andi(rt,rs,imm): return 0x30000000|(R[rs]<<21)|(R[rt]<<16)|(imm&0xffff)
CAVE3=here()
emit(addiu('sp','sp',-0x10), sw('ra',0,'sp'))
emit(jal(0x1d0a20), NOP)
for _band in (0xc080, 0xc198):
    emit(lui('t0',0x001d), ori('t0','t0',_band),
         lw('t1',0x20,'t0'),
         slti('t5','t1',0))
    emit(beq('t5','zero',2), NOP, ori('t1','zero',0))
    emit(slti('t5','t1',0x181))
    emit(bne('t5','zero',2), NOP, ori('t1','zero',0x180))
    emit(sw('t1',0x20,'t0'),
         ori('t4','zero',23), mult('t1','t4'), mflo('t2'),
         ori('t4','zero',96), divi('t2','t4'), mflo('t3'),
         addiu('t3','t3',0x152), sw('t3',0x18,'t0'),
         ori('t4','zero',48), divi('t2','t4'), mflo('t6'),
         addiu('t6','t6',0x124), sw('t6',0x28,'t0'))
    emit(addiu('t5','t3',0x40), andi('t5','t5',0x1ff), sw('t5',0xd4,'t0'),
         andi('t7','t5',7), sw('t7',0xf4,'t0'))
    emit(addiu('t5','t1',0x40), andi('t5','t5',0x3ff), sw('t5',0xd8,'t0'),
         andi('t7','t5',0xf), sw('t7',0xf8,'t0'))
    emit(addiu('t5','t6',0x40), andi('t5','t5',0x7ff), sw('t5',0xdc,'t0'),
         andi('t7','t5',0x1f), sw('t7',0xfc,'t0'))
emit(lw('ra',0,'sp'), addiu('sp','sp',0x10))
emit(0x03e00008, NOP)
assert here() <= 0x1c0f00, hex(here())   # zone libre verifiee jusqu'a 0x1c1000 (vanilla = zeros)
lines=[]
for i,w in enumerate(code):
    lines.append('patch=1,EE,%08x,word,%08x'%(BASE+i*4,w))
lines.append('patch=1,EE,001d0750,word,%08x'%j_(0x1c0400))
lines.append('patch=1,EE,001d0818,word,%08x'%jal(CAVE2))
lines.append('patch=1,EE,001d0784,word,%08x'%jal(CAVE3))
lines.append('patch=1,EE,00290834,word,34030008')   # lock stage 8 (versus/descripteur 0x696018)
lines.append('patch=1,EE,0028874c,word,34030008')   # char-select : lh v1,(table) -> ori v1,zero,8
lines.append('patch=1,EE,00288758,word,a443c178')   # store char-select RESTAURE (ecrit 8)
lines.append('patch=1,EE,00286c30,word,34020008')   # cycleur : addiu v0,v0,8 -> ori v0,zero,8
lines.append('patch=1,EE,00286c34,word,a462c178')   # store cycleur RESTAURE (ecrit 8)
# v7.29 LOCK VARIANTE [0xb88100]=4 (PAS 0 !) : la config couches du stage Blanka z5 = [0,1,3,2] =
# celle de la VARIANTE 4 (prouve par v726_02 b88100=4 -> [1,3,2] ; v728 lock 0 -> [3,2,1] = mauvais
# cablage -> fond noir). Variante 4 : bloc bleu deja regle (repoint conteneurs x3 v7.26), ciel-boucle
# deja regle (SCR1 blank v7.24). Implementation DATA PURE : sh originaux RESTAURES, on force les
# SOURCES -> les writers du jeu propagent 4 naturellement.
lines.append('patch=1,EE,0021e92c,word,a4a30100')   # sh v1,0x100(a1) RESTAURE
lines.append('patch=1,EE,00286c20,word,a4430100')   # sh v1,0x100(v0) RESTAURE (cycleur)
lines.append('patch=1,EE,0028872c,word,a4430100')   # sh RESTAURE (char-select)
lines.append('patch=1,EE,00290814,word,a4430100')   # sh RESTAURE (writer principal)
lines.append('patch=1,EE,00508ad0,word,a4430100')   # sh RESTAURE
lines.append('patch=1,EE,00510ca8,word,a4640100')   # sh a0,0x100(v1) RESTAURE
lines.append('patch=1,EE,0051175c,word,a4640100')   # sh a0,0x100(v1) RESTAURE
for i in range(4):                                   # table variantes 0x5b5cb0 (8 u16 = 16 octets,
    lines.append('patch=1,EE,%08x,word,00040004' % (0x5b5cb0+i*4))  # 0x5b5cc0 = table STAGES, ne pas toucher !)
lines.append('patch=1,EE,00b84314,short,0004')      # source des 4 copieurs
lines.append('patch=1,EE,00b88174,short,0004')      # source du cycleur
lines.append('patch=1,EE,00b88100,short,0004')      # filet
open(r"E:\tmp\v7pg_lines.txt",'w').write('\n'.join(lines)+'\n')
print('cave: %d instr, fin @%s ; EXIT @0x%x'%(len(code),hex(here()),EXIT))
print('\n'.join(lines[:6]))
