#!/usr/bin/env python3
"""Table des commandes son du pilote natif PS2 (Anthology) pour ro3 / ro5 / ro9.
Le pilote natif (C, dans le module) lit la boite aux lettres QSound emulee ($618001-$618019, PS2 base+0x60000),
puis, pour une commande < 0x1200, lit 8 octets dans une table (exec TABLE + 8*cmd) :
  o0 & 0x7F = type : 0 rien ; 1 flux ADX (fid Y_DATA = (o6&0x7F)<<8 | o4, o5 = volume, o6&0x80 = variante) ;
                     2 flux ADX voix (fid = base + o4, base lue dans une structure +0x78) ;
                     3/4 banque SPU2 commune 0/1 (e345/e346) : programme o4, o5, o6 ;
                     >=5 banque SPU2 de perso : perso = PERSO[type-5], programme o4, o5, o6.
Usage : table_son.py [ro3|ro5|ro9] [--tout] [--csv fichier]"""
import struct, sys
DEC="<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin"
BASE=0x1F0000
def find_tables(d):
    w=lambda o: struct.unpack_from("<I",d,o)[0]
    p=d.find(struct.pack("<I",0x28611200))
    while p%4: p=d.find(struct.pack("<I",0x28611200),p+1)
    tab=None
    for k in range(0,0x100,4):
        if w(p+k)>>16==0x3c02 and w(p+k+4)>>16==0x2442:
            imm=w(p+k+4)&0xffff; imm-=0x10000 if imm&0x8000 else 0
            tab=((w(p+k)&0xffff)<<16)+imm; break
    # table perso : 'addiu s5,s5,-5' (26b5fffb) puis lui v0 / addiu v0
    q=d.find(struct.pack("<I",0x26b5fffb),p)
    perso=None
    for k in range(0,0x40,4):
        if w(q+k)>>16==0x3c02 and w(q+k+4)>>16==0x2442:
            imm=w(q+k+4)&0xffff; imm-=0x10000 if imm&0x8000 else 0
            perso=((w(q+k)&0xffff)<<16)+imm; break
    return p,tab,perso
def charger(mod):
    d=open(DEC%mod,"rb").read()
    p,tab,perso=find_tables(d)
    ents=[d[tab-BASE+8*c:tab-BASE+8*c+8] for c in range(0x1200)]
    pt=d[perso-BASE:perso-BASE+64]
    return d,p,tab,perso,ents,pt
def decode(e,pt):
    t=e[0]&0x7f
    if t==0: return ("-",)
    if t==1: return ("ADX",((e[6]&0x7f)<<8)|e[4],e[5],e[6]>>7)
    if t==2: return ("ADXvoix",e[4],e[5],e[6])
    if t in (3,4): return ("SPU2commun%d"%(t-3),e[4],e[5],e[6])
    return ("SPU2perso",pt[t-5],e[4],e[5],e[6])
if __name__=="__main__":
    mod=sys.argv[1] if len(sys.argv)>1 else "ro9"
    d,p,tab,perso,ents,pt=charger(mod)
    print("%s : test 0x1200 a mips 0x%X ; table commandes exec 0x%X (fichier 0x%X) ; table type->perso exec 0x%X : %s"%(mod,p,tab,tab-BASE,perso,pt[:48].hex()))
    if "--tout" in sys.argv:
        for c,e in enumerate(ents):
            r=decode(e,pt)
            if r[0]!="-": print("%04X %s %s"%(c,e.hex(),r))
    if "--csv" in sys.argv:
        f=open(sys.argv[sys.argv.index("--csv")+1],"w"); f.write("cmd,brut,genre,a,b,c,d\n")
        for c,e in enumerate(ents):
            r=decode(e,pt); f.write("%04X,%s,%s\n"%(c,e.hex(),",".join(str(x) for x in r)))
