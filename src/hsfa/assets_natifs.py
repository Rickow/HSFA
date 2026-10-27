#!/usr/bin/env python3
"""TABLES D'ANIMATION CHARGEES PAR LE CODE NATIF DU PORTAGE (HANDOFF §75).

Le portage a sorti de la ROM certaines tables d'animation (intro, et une par personnage) : le 68K
recompile appelle une fonction native qui decompresse un fichier de X_DATA.BIN a l'adresse FIXE
0xA75000 et range ce pointeur dans $be48(A5) :
  0x383700(i)  i = 0 (intro, mips 0x4708c) ou 1 (mips 0x1ff008) : fichiers  T_59c1b0[i] = (gfx, anim)
  0x3837d0(i)  i = octet $132(A5) < 0x20 (mips 0x20f3a4)       : fichiers  T_59c130[i] = (gfx, anim)
Le fichier « anim » (MWo3/LZSS) contient des POINTEURS ABSOLUS deja poses pour 0xA75000.

Ici : chaque fichier « anim » est decompresse, range a la suite des autres a partir d'une base
virtuelle PS2 VBASE (pointeurs reloges), et la conversion de pointeurs a l'execution projette
[VBASE, VBASE+taille) sur l'emplacement 68K du bloc. Le fichier « gfx » (banque de tuiles, moteur de
sprites natif) n'est pas traite ici.
FICHIERS A ADRESSE FIXE : le fichier 289 (frames de sprites de tous les personnages, 458 Ko) est
charge a 0xA04000 ; ~17 000 pointeurs des donnees du module y visent directement. Il ne tient pas dans
les 4 Mo de ROM programme : projete tel quel en $A04000 (banc MAME : tap de lecture, banc_mem.lua ;
fork : ROM supplementaire).
Cache : work/cps2/anims/f<N>.bin (fichiers decompresses) ; sinon X_DATA.BIN (variable XDATA)."""
import os, sys, struct, csv
D = os.path.dirname(os.path.abspath(__file__))
EXTRACT = "<workspace>/anthology_extract"
CACHE = "<workspace>/work/cps2/anims"
LOAD_BASE = 0xA75000                     # adresse de chargement fixe du portage (ctx+0x9c)
VBASE = 0xA80000                         # base virtuelle PS2 du bloc (libre dans la carte)
T_SITE = 0x59c1b0                        # 0x383700 : (gfx, anim) par index, 4 octets
T_PERSO = 0x59c130                       # 0x3837d0 : (gfx, anim) par index, 4 octets
N_PERSO = 0x20
NATIF_SITE, NATIF_PERSO = 0x383700, 0x3837d0
SITES = {0x4708c: 0, 0x1ff008: 1}        # appels de 0x383700 -> index (a0 constant au site)
FIXES = {289: 0xA04000}                  # fichier -> adresse de chargement fixe (identite en 68K)
PERSO_OFS = 0x132                        # octet lu par l'appelant de 0x3837d0 (lb, adresse MIPS)
PERSO_JOUEUR = {}                        # (HANDOFF §122) ro5 : site -> joueur, index calcule comme 0x2141A0
PERSO_TABLE = None
T_FIN = None; N_FIN = 0; FIN_SITES = ()        # (HANDOFF §122) ro5 : chargeur de la FIN (index dans D8)
N_SITE = 2
SITES_DYN = {}
LOAD_SITE = None
if os.environ.get("MODULE", "ro3") == "ro5":   # (HANDOFF §108) Upper : CARTE-ro5 §6 point 3
    LOAD_BASE = 0xB83800                 # (HANDOFF §122) tous les fichiers d'animation d'Upper (perso, fin, site) : pointeurs internes relatifs a $B83800
    LOAD_SITE = 0xB83800                 # fichiers de l'intro (522/523) : charges 0x800 plus haut (table en +0x31C, comme ro3)
    VBASE = 0xC00000                     # hors RAM ro5 ($A00000-$A7FFFF) et des fichiers fixes ($B04000, $B83000)
    T_SITE, T_PERSO, N_PERSO = 0x628460, 0x628470, 0x28
    NATIF_SITE, NATIF_PERSO = 0x4112d0, 0x4113a0
    SITES = {0x25d6c0: 2, 0x262574: 2, 0x4cc04: 0}
    # (HANDOFF §122) chargeur par perso d'Upper : l'index n'est plus l'octet $132(A5) mais le resultat de la fonction
    # NATIVE 0x2141A0(a0 = $8000000p) (fichier 0x241A0) : table[perso du joueur p] (table 0x60AD90 : identite sauf variantes, cas particuliers).
    # Site d'appel de 0x6013A0 -> joueur p (constante a0 du site, relue dans le MIPS).
    PERSO_JOUEUR = {0x257678: 0, 0x25769c: 1, 0x257d38: 0, 0x257d5c: 1, 0x26b640: 0, 0x26b660: 1}
    # Chargeur des animations de FIN (homologue de ro3 0x3837D0($132)) : natif 0x4114A0, index = D8 (domicile
    # $87F0(A5)), table 0x6283C0 (lui 0x63 ; addiu 0x83C0 signe) : (gfx, anim) 391-418 / 458-485 par perso.
    T_FIN, N_FIN, FIN_SITES = 0x6283c0, 0x28, (0x272d50,)
    PERSO_TABLE = 0x60ad90                  # lui 0x61 ; addiu 0xAD90 (immediat SIGNE)
    SITES_DYN = {0x4cc04: (0x8c21, 2)}  # index a l'execution : (octet $8C21(A5) >> 2) & 1 (intro d'Upper : 2 fichiers)
    FIXES = {390: 0xB04000}
    N_SITE = 3
if os.environ.get("MODULE", "ro3") == "ro9":   # (agent_ro9) Hyper : AUCUN chargeur natif de tables d'animation
    # Le seul chargeur natif de ro9 (0x22B00, sites 0x970BC / 0x31AF78 / 0x31AFA4) est l'homologue du chargeur
    # 4 joueurs de ro3 0x3838D0 (banques graphiques via 0x154D20 / 0x155080 ; tables 0x5AF2B0 / 0x5AF1B0) : il
    # n'appelle pas 0x154C90 (decompression d'un fichier « anim » a ctx+0x9C) et n'ecrit pas $C0BC(A5).
    # Les homologues de 0x383700 / 0x3837D0 n'existent pas -> pas de talons, bloc virtuel vide.
    LOAD_BASE = LOAD_SITE = None
    VBASE = 0xD20000                     # inutilise (bloc vide) ; hors RAM ro9 ($B80000-$BFFFFF) et du fichier 547
    T_SITE = T_PERSO = None
    N_PERSO = 0
    NATIF_SITE = NATIF_PERSO = None
    SITES = {}
    SITES_DYN = {}
    FIXES = {547: 0xC84000}              # frames de sprites (en-tete d1ff f2ff.. comme 289/390), 553 352 o :
                                         # 39 656 longs alignes des donnees dans [$C84000, $D0B188)
    N_SITE = 0
CACHE_ECRIT = os.environ.get("ANIM_CACHE", CACHE)   # (agent_ro9) cache en ecriture (lecture : CACHE d'abord)

def fichier(n):
    for c_ in (CACHE, CACHE_ECRIT):
        p = os.path.join(c_, "f%d.bin" % n)
        if os.path.exists(p): return open(p, "rb").read()
    sys.path.insert(0, EXTRACT)
    from mwo3_codec import decompress
    man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(os.path.join(EXTRACT, "manifest.csv")))}
    o, s = man[n]
    with open(os.environ["XDATA"], "rb") as f:
        f.seek(o); d = bytes(decompress(f.read(s)))
    os.makedirs(CACHE_ECRIT, exist_ok=True); open(os.path.join(CACHE_ECRIT, "f%d.bin" % n), "wb").write(d)
    return d

def tables(buf, rtbase=0x1F0000):
    """(anim par index de 0x383700, anim par index de 0x3837d0) ; 0 = pas de fichier"""
    site = [struct.unpack_from('<h', buf, T_SITE - rtbase + 4*i + 2)[0] for i in range(N_SITE)]
    perso = []
    for i in range(N_PERSO):
        g, a = struct.unpack_from('<hh', buf, T_PERSO - rtbase + 4*i)
        perso.append(a if g else 0)
    return site, perso

def fin_tables(buf, rtbase=0x1F0000):
    """(HANDOFF §122) anim par index du chargeur de fin (ro5) ; 0 = pas de fichier"""
    fin = []
    for i in range(N_FIN):
        g, a = struct.unpack_from('<hh', buf, T_FIN - rtbase + 4*i)
        fin.append(a if g else 0)
    return fin

def build(buf):
    """-> (bloc au format PS2 petit-boutiste, {fichier: adresse virtuelle PS2})"""
    site, perso = tables(buf)
    fin = fin_tables(buf) if T_FIN else []
    blob = bytearray(); va = {}
    for n in sorted({x for x in site + perso + fin if x}):
        d = bytearray(fichier(n)); d += bytes(-len(d) % 16)
        base = VBASE + len(blob); va[n] = base
        lb = LOAD_SITE if (LOAD_SITE and n in site) else LOAD_BASE      # (HANDOFF §108) base de chargement du fichier
        for o in range(0, len(d) - 3, 4):
            v = struct.unpack_from('<I', d, o)[0]
            if lb <= v < lb + len(d): struct.pack_into('<I', d, o, v - lb + base)
        blob += d
    return bytes(blob), va

def swapped(v):
    """long tel que le lit le 68K apres la recette cps2 (moities echangees)"""
    return ((v & 0xffff) << 16) | (v >> 16)

if __name__ == "__main__":
    sys.path.insert(0, D)
    import census
    b, va = build(open(census.RO3, "rb").read())
    print("bloc : %d octets, %d fichiers" % (len(b), len(va)))
    for n, a in sorted(va.items()): print("  fichier %d -> PS2 virtuel %06x" % (n, a))
