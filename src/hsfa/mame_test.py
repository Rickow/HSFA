#!/usr/bin/env python3
"""ESSAI EN VRAI (HANDOFF §59) : l'image programme traduite (SFA3, mode cps2) remplace le programme
du jeu Phoenix (non chiffre) 'sfa3ud' de MAME ; graphismes/son d'origine.
  vecteurs : SP d'origine, PC = reset porte traduit, IRQ2 = balayage vertical porte traduit,
             autres = RTE ; appels natifs non raccordes -> RTS de repli (le jeu continue).
Ecrit roms_tr/sfa3ud/sz3ud.03c ... sz3.10b (mots inverses).  Usage : mame_test.py [va_reset] [va_irq2]"""
import sys, os, struct, bisect
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
os.environ["MEMMODE"] = "cps2"
import translate as T
from assemble import assemble
from mips import CODE0
from profils import P, NOM as MODULE, chemin as module_chemin     # (HANDOFF §108) profil par module (MODULE=ro3|ro5)
T.AIDES_RECOMP = dict(P['aides'])
if P.get('data_ext'): T.DATA_EXT = P['data_ext']      # (agent_ro9) bloc externe de fin des donnees par module
W = P['travail']
STUB_RTS, STUB_RTE = 0x800, 0x802
STUB_ANIM = 0x810                                        # talons des chargements natifs de tables d'animation

def patch_call(img, it, a):
    """redirige l'appel externe emis pour it (JSR abs.L ou BSR.W) vers l'adresse a"""
    w = struct.unpack_from('>H', img, it.off)[0]
    if w in (0x4eb9, 0x4ef9): struct.pack_into('>I', img, it.off + 2, a); return
    assert w in (0x6100, 0x6000), "appel %x : forme %04x non repatchable" % (it.va, w)
    d = a - (it.off + 2); assert -0x8000 <= d < 0x8000
    struct.pack_into('>h', img, it.off + 2, d)

def native_at(buf, t):
    """(HANDOFF §101) fonction native C du portage ? (criteres de natmiss sur [t, premier 'jr ra'])"""
    from mips import decode
    L = []
    for x in decode(buf, t, t + 0x4000):
        L.append(x)
        if x.m == 'jr' and x.rs == 31: break
    a = sum(1 for x in L if x.m == 'lui' and x.imm == 0x7000); n = len(L)
    s = sum(1 for x in L if x.m in ('sq', 'lq', 'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo')
            or (x.m == 'addiu' and x.rs == 29 and x.rt == 29 and -0x400 < x.simm < -16 and x.simm % 16 == 0))
    lu = {}; relais = False
    for x in L:
        if x.m == 'lui': lu[x.rt] = x.imm
        elif x.m == 'addiu' and x.rs in lu: lu[x.rt] = (lu[x.rs] << 16) + x.simm
        elif (x.m == 'jalr' and x.rs in lu and T.RUNTIME_BASE + CODE0 <= lu[x.rs] < T.CODE_END_RT) or \
             (x.m == 'jal' and T.RUNTIME_BASE + CODE0 <= x.tgt < T.CODE_END_RT): relais = True
    if a == 0 and (n <= 8 or (n <= 24 and relais)): return False
    return a == 0 or (s > 0 and a * 20 < n)

def main():
    va_reset = int(sys.argv[1], 16) if len(sys.argv) > 1 else P['va_reset']
    va_irq2 = int(sys.argv[2], 16) if len(sys.argv) > 2 else P.get('irq2')
    va_frame = int(sys.argv[3], 16) if len(sys.argv) > 3 else P['va_frame']      # ctx+16
    va_init = int(os.environ.get("VA_INIT", "%x" % P['va_init']), 16)      # initialisation (1re tache)
    buf = open(module_chemin(), "rb").read()
    os.makedirs(W, exist_ok=True)
    end = struct.unpack_from('<I', buf, 12)[0]
    T.set_module_bounds(buf)
    CODE = 0x1000
    import kernel68k as K
    # ADRESSES DE CODE PS2 CONVERTIES A L'USAGE (HANDOFF §76) : table (adresse PS2 -> notre adresse) des
    # debuts de fonction (cibles de jal + prologues vises par un long des donnees) ; plus de relocation
    # statique des donnees (faux positifs : paires de mots de script '0000 0040' = 0x400000)
    CODEMAP, CODECONV = 0x3E0000, 0x3FF000
    from mips import decode
    Lm = list(decode(buf, CODE0, end))
    keys = {x.tgt for x in Lm if x.m == 'jal' and T.RUNTIME_BASE + CODE0 <= x.tgt < T.CODE_END_RT}
    def prologue(va):                                        # debut de fonction plausible (cle en trop : sans effet)
        w = struct.unpack_from('<I', buf, va)[0]
        return ((w >> 16) == 0x27bd and (w & 0x8000)) or w == 0x03e00008 or (w & 0xffe0ffff) == 0x3c007000
                                                             # addiu sp,sp,-N | jr ra (vide) | lui rX,0x7000 (feuille)
    for o in range(end, len(buf) - 3, 4):
        v = struct.unpack_from('<I', buf, o)[0]
        if T.RUNTIME_BASE + CODE0 <= v < T.CODE_END_RT and v % 4 == 0 and prologue(v - T.RUNTIME_BASE): keys.add(v)
    T.translate(buf, CODE0, CODE0 + 4)                        # initialise l'ensemble des debuts connus
    keys |= set(T._CODE_STARTS.get('set') or ())             # (constantes CODE_x emises par le traducteur)
    keys = sorted(keys)
    assert CODEMAP + 8*len(keys) <= CODECONV
    import assemble as _AS
    if _AS.RELOGE_CODE: T.RELOGE_KEYS = set(keys)        # (ETAPE B) relogement des tables de pointeurs de code
    HASH = None if os.environ.get("CODECONV_DICHO") == "1" else 0x3C0000      # (HANDOFF §98) table de hachage, 128 Ko
    cconv, CCE = K.build_code_conv(CODECONV, CODEMAP, len(keys), T.RUNTIME_BASE + CODE0, T.CODE_END_RT, hash_addr=HASH)
    T.CODE_CONV = CCE
    KORG = 0xB00
    _, KL = K.build(KORG, 0)                             # adresses des points d'entree du noyau
    # appels systeme PS2 (numeros lus dans SLUS_213.17, HANDOFF §80) : 0x20 CreateThread 0x1033E0, 0x21 DeleteThread
    # 0x1033F0, 0x23 ExitThread 0x103410, 0x24 ExitDeleteThread 0x103420, 0x25 TerminateThread(tid) 0x103430 (tue un
    # AUTRE fil : le portage a deja efface l'etat de son emplacement -> RTS ; c'etait FINIR : la tache principale se
    # tuait elle-meme en fin de partie), 0x32 SleepThread 0x103500
    SYSC = {0x1033e0: KL['creer'], 0x103500: KL['ceder'], 0x103410: KL['finir'], 0x103420: KL['finir']}
    # TABLES D'ANIMATION CHARGEES PAR LE CODE NATIF (assets_natifs, HANDOFF §75) : talons 68K
    import assets_natifs as AN
    ablob, ava = AN.build(buf)
    asite, aperso = AN.tables(buf)
    stub_site = [STUB_ANIM + 10*k for k in range(len(asite))]
    stub_perso = STUB_ANIM + 10*len(asite)
    if AN.NATIF_SITE is not None: SYSC[AN.NATIF_SITE + T.RUNTIME_BASE] = stub_site[0]  # site 0 ; autres sites : appel repatche
    if AN.NATIF_PERSO is not None: SYSC[AN.NATIF_PERSO + T.RUNTIME_BASE] = stub_perso   # (agent_ro9) ro9 : aucun
    def ext(t):                                          # appels natifs : noyau pour les appels systeme de fils, sinon RTS
        return SYSC.get(t + T.RUNTIME_BASE, STUB_RTS)
    import json                                          # fonctions NATIVES du module (dans ses bornes) : externes
    NAT = [int(k, 16) for k, v in json.load(open(os.path.join(D, P['hooks']))).items() if v["type"] == "natif du module"]
    # (HANDOFF §101) classees « natives » a tort : code 68K recompile (cases de registres 0x70001100), a traduire.
    # 0x383C90 = etat 1 de l'objet du libelle du menu de modes (lit $C001) : sinon talon RTS et table d'etats a 0
    # Critere de natmiss recalcule sur la VRAIE plage de la fonction (entree -> premier 'jr ra') : natmiss decoupe
    # sur les seules cibles de 'jal', une routine atteinte par table de sauts heritait des traits de la precedente
    NAT = [a for a in NAT if native_at(buf, a)]
    # POINTEURS PS2 BRUTS DES DONNEES (HANDOFF §63) : conversion a l'execution (routines en $400)
    CONV = 0x400
    T.HW_TAG = os.environ.get("DPTR", "runtime") == "runtime"
    if T.HW_TAG: T.DPTR_FIX = K.build_conv(CONV, [(0, 1, 0)])[1]
    T.DATA_BASE = 0x200000
    SON_BLOB = None
    if os.environ.get("HSFA_SON_DONNEES"):            # (agent_son_hyper_rom) bloc ajoute, cf. translate.SON_X
        SON_BLOB = open(os.environ["HSFA_SON_DONNEES"], "rb").read(); SON_BLOB += bytes(len(SON_BLOB) & 1)
        T.SON_X = int(os.environ.get("HSFA_SON_X", "E70000"), 16); T.SON_LEN = len(SON_BLOB)
    def plages_conv():                                   # (agent_defauts_banc) plages du talon CONV (HANDOFF §63)
        R = T.RAM_HI << 16; PR = T.PORT_RAM; TG = 0x01000000
        ranges = ([(T.CODE_END_RT, T.DATA_SPLIT, T.DATA_BASE - T.CODE_END_RT),
                   (T.DATA_SPLIT, T.DATA_END_RT, T.DATA_EXT - T.DATA_SPLIT + (TG if P.get('data_ext') else 0))] if T.DATA_SPLIT else
                  [(T.CODE_END_RT, T.DATA_END_RT, T.DATA_BASE - T.CODE_END_RT)]) + [
                  (T.DATA_END_RT, R, PR - T.DATA_END_RT),
                  (R, R + 0x10000, 0xff0000 - R),
                  (R + 0x10000, R + 0x12000, TG + 0x700000 - (R + 0x10000)),
                  (R + 0x12000, R + 0x14000, TG + 0x708000 - (R + 0x12000)),
                  (R + 0x20000, R + 0x50000, TG + 0x900000 - (R + 0x20000)),
                  (R + 0x50000, R + 0x60000, PR + 0x80000 - (R + 0x50000)),
                  (R + 0x60000, R + 0x62000, TG + 0x618000 - (R + 0x60000)),
                  (R + 0x62000, R + 0x80000, PR + 0x80000 + 0x12000 - (R + 0x62000))]
        NDATA = (T.DATA_SPLIT - T.CODE_END_RT) if T.DATA_SPLIT else (len(buf) - end)   # donnees DANS l'image
        ASSET = (T.DATA_BASE + NDATA + 0xff) & ~0xff      # bloc des tables d'animation, apres les donnees
        if ablob: ranges.append((AN.VBASE, AN.VBASE + len(ablob), ASSET - AN.VBASE))   # (agent_ro9) ro9 : bloc vide
        if T.SON_X is not None: ranges.append((T.SON_X, T.SON_X + T.SON_LEN, T.son_y() + TG - T.SON_X))
        return ranges
    def plages_retag():                                  # (agent_defauts_banc, RETAG24) blocs 68K etiquetes x plages converties
        if not T.HW_TAG or not T.DATA_SPLIT: return []
        blocs = []
        if P.get('data_ext'): blocs.append((T.DATA_EXT, T.DATA_EXT + (T.DATA_END_RT - T.DATA_SPLIT)))
        if T.SON_X is not None: blocs.append((T.son_y(), T.son_y() + T.SON_LEN))
        res = []
        for b0, b1 in blocs:
            for r0, r1, add in plages_conv():
                if add == 0: continue
                lo, hi = max(b0, r0), min(b1, r1)
                if lo < hi: res.append((lo, hi))
        res.sort(); m = []
        for lo, hi in res:
            if m and lo <= m[-1][1]: m[-1] = (m[-1][0], max(hi, m[-1][1]))
            else: m.append((lo, hi))
        return m
    T.RETAG_FN = plages_retag
    its, words, unres = assemble(buf, CODE0, T.code_end_translate(buf), base=CODE, external=ext, native=NAT)
    PLAFOND = 0x3C0000 - len(ablob) - 4*len(aperso) - 0x2000   # sous la table de hachage (HANDOFF §98)
    COUPE_BLOCS = os.environ.get('COUPE_BLOCS', '1') != '0'   # (agent_defauts_banc)
    def coupe():                                         # (HANDOFF §108) donnees trop grandes : la fin part en externe
        lim = T.CODE_END_RT + (PLAFOND - T.DATA_BASE)
        if lim >= T.DATA_END_RT: return None
        if P.get('blocs'):
            # (HANDOFF §126) coupure au DEBUT d'un bloc de perso : le code fait 'table d'animation + decalage 16 bits'
            # a l'execution ; une coupure au milieu du bloc envoyait le pointeur hors du bloc externe (Upper : bloc
            # 0x8E4AE0, table 0x8E4BE4 + $45E4 = 0x8E91C8 > coupure 0x8E7000 -> erreur d'adresse contre Bison)
            ta, nb_ = P['blocs']
            db = [__import__('struct').unpack_from('<I', buf, ta - T.RUNTIME_BASE + 4*k)[0] for k in range(nb_)]
            cand = [d for d in db if T.CODE_END_RT <= d <= lim]
            if cand: return max(cand) & ~1
        if P.get('blocs_lignes') and COUPE_BLOCS:
            # (agent_defauts_banc, COUPE_BLOCS) meme regle pour Hyper, dont les blocs par perso passent par des LIGNES
            # (table[$102] -> 3 lignes de 4 pointeurs $2B0/$2B8/$2B4/$2BC, BLOC-HYPER.md §0) : debut d'un groupe = plus
            # petit pointeur des lignes d'un id. La coupure a lim & ~$FFF tombait dans le bloc d'Evil Ryu ($8D3410-$8E025F) :
            # elle a recule de $1000 quand le code a grandi (regle de remasquage 24 bits) -> table $8D3626 + decalage hors du bloc externe
            # (Shoryu Ken / Tatsumaki / Messatsu d'Evil Ryu ALPHA ne rendaient plus la main)
            _u = lambda a: __import__('struct').unpack_from('<I', buf, a - T.RUNTIME_BASE)[0]
            iv = set()                                   # [premier, dernier pointeur] des lignes de chaque id
            for ta, nb_ in P['blocs_lignes']:
                for k in range(nb_):
                    bl = _u(ta + 4*k)
                    if not (T.CODE_END_RT <= bl < T.DATA_END_RT): continue
                    ps = [_u(bl + 4*j) for j in range(12)]
                    ps = [x for x in ps if T.CODE_END_RT <= x < T.DATA_END_RT]
                    if ps: iv.add((min(ps), max(ps)))
            # un debut de groupe qui ne tombe a l'interieur d'aucun autre groupe (les versions d'un perso se partagent
            # des tables : Evil Ryu $60/$77/$7B commencent en $8D3410/$8D3494/$8D3518)
            cand = [d for d, _ in iv if T.CODE_END_RT <= d <= lim and not any(a < d <= b for a, b in iv)]
            if cand: return max(cand) & ~1
        return lim & ~0xfff
    for _ in range(4):                                   # base des donnees STABLE (la taille du code en depend)
        nb = (CODE + 2*len(words) + 0xfff) & ~0xfff
        if nb == T.DATA_BASE and coupe() == T.DATA_SPLIT: break
        T.DATA_BASE = nb; T.DATA_SPLIT = coupe()
        its, words, unres = assemble(buf, CODE0, T.code_end_translate(buf), base=CODE, external=ext, native=NAT)
    if T.DATA_SPLIT: print("donnees : fin du segment ($%x-$%x) en bloc externe $%x (HANDOFF §108)" % (T.DATA_SPLIT, T.DATA_END_RT, T.DATA_EXT))
    assert CODE + 2*len(words) <= T.DATA_BASE, "code (%x) chevauche les donnees (%x)" % (CODE+2*len(words), T.DATA_BASE)
    vas = [it.va for it in its]
    lab = lambda va: its[bisect.bisect_left(vas, va)].off
    if va_irq2 is None:                                  # fonction du gestionnaire VBL porte (contient 0x2f310)
        starts = sorted({x.tgt - T.RUNTIME_BASE for x in __import__('mips').decode(buf, CODE0, end) if x.m == 'jal'})
        va_irq2 = starts[bisect.bisect_right(starts, P['irq2_dans']) - 1]
    img = bytearray(0x400000)
    STACK = int(os.environ.get("PILE", "664000"), 16)     # pile 68K HORS de la RAM du jeu (effacee au reset)
    struct.pack_into('>I', img, 0, STACK)
    for v in range(1, 64):                                # chaque exception : sa propre boucle BRA.S *
        struct.pack_into('>I', img, 4*v, 0xA00 + 2*v); struct.pack_into('>H', img, 0xA00 + 2*v, 0x60fe)
    # AMORCAGE 68K reproduisant la boucle native du portage (moteur 0x1CB764..) : reset (ctx+4) une fois,
    # puis a chaque image la tache du jeu (ctx+16 = mips 0x2EF30) ; l'IRQ2 pose un drapeau d'image.
    # NOYAU DE TACHES (kernel68k, HANDOFF §61) + AMORCAGE : reset porte, initialisation portee (cree la
    # premiere tache : mips 0x2ED20), puis l'ordonnanceur au premier plan ; IRQ2 = balayage vertical porte.
    kcode, KL = K.build(KORG, lab(va_irq2), code_conv=CCE[0])
    assert len(kcode) <= 0x1000 - KORG
    img[KORG:KORG+len(kcode)] = kcode
    init = lab(va_init)
    boot = [0x4bf9, 0x00ff, 0x8000,                       # LEA $FF8000,A5 (la pile vient du vecteur 0)
            0x4eb9, lab(va_reset) >> 16, lab(va_reset) & 0xffff,
            0x4bf9, 0x00ff, 0x8000,
            0x4eb9, init >> 16, init & 0xffff,            # JSR initialisation (cree la 1re tache)
            0x4bf9, 0x00ff, 0x8000,
            0x46fc, 0x2000,                               # MOVE.W #$2000,SR (interruptions permises)
            0x4ef9, KL['ordo'] >> 16, KL['ordo'] & 0xffff]   # JMP ordonnanceur
    struct.pack_into('>%dH' % len(boot), img, 0x900, *boot)
    struct.pack_into('>I', img, 4, 0x900)
    struct.pack_into('>I', img, 0x68, KL['irq2'])        # niveau 2 (balayage vertical CPS2)
    img[STUB_RTS:STUB_RTS+4] = bytes.fromhex('4e754e73')
    if T.HW_TAG:
        ranges = plages_conv()
        NDATA = (T.DATA_SPLIT - T.CODE_END_RT) if T.DATA_SPLIT else (len(buf) - end)   # donnees DANS l'image
        ASSET = (T.DATA_BASE + NDATA + 0xff) & ~0xff      # bloc des tables d'animation, apres les donnees
        ccode, _ = K.build_conv(CONV, ranges)
        assert CONV + len(ccode) <= STUB_RTS
        img[CONV:CONV+len(ccode)] = ccode
    img[CODE:CODE+2*len(words)] = struct.pack('>%dH' % len(words), *words)
    # sauvegarde / restauration des registres 68K dans le bloc de tache (emulation d'un banc de registres
    # partage entre fils PS2) : inutile avec notre noyau (chaque tache garde ses registres sur sa pile)
    for va in P['sauve_regs']:
        struct.pack_into('>H', img, lab(va), 0x4e75)
    # (HANDOFF §103) ROUTINES REECRITES A LA MAIN (forme de la ROM) : le portage a recompile des MOVEM en boucles
    # d'ecritures une a une (SWAP / MOVE.L / SWAP + registre D8 prete) : trop lent, les effacements de l'ecran a
    # chaque scene de l'intro prenaient 8-10 images au lieu de ~4 -> intro 1,35x plus lente, musique en avance.
    # 0x898E0 : remplissage, D1=D2=D3=D0 puis (D4+1) x 16 longs -(A0) (valeur en memoire = moities echangees)
    REMPL = [0x4840, 0x2200, 0x2400, 0x2600,                  # SWAP D0 ; MOVE.L D0,D1/D2/D3
             0x48e0, 0xf000, 0x48e0, 0xf000, 0x48e0, 0xf000, 0x48e0, 0xf000,   # 4 x MOVEM.L D0-D3,-(A0)
             0x51cc, 0xffee,                                  # DBRA D4,boucle
             0x4840, 0x2200, 0x2400, 0x2600, 0x4e75]          # SWAP D0 ; D1-D3 = D0 ; RTS
    # 0x10DD50 / 0x10E200 : recopie de tables de tuiles (mot de code + octet d'attribut par entree, flux d'octets
    # partant d'une adresse PAIRE) : 2 entrees par tour, octets lus par MOVE.W (A2)+ (octet PS2 pair = poids faible)
    def recopie(table, decal, n, attr_off, plus):
        t = T.addr_to_68k(table)
        w = [0x0280, 0x0000, 0x00ff, 0x3200, 0xd041, 0xd041, decal,          # ANDI.L #$FF,D0 ; D0*3 ; LSL.L
             0x41f9, t >> 16, t & 0xffff, 0xd1c0]                            # LEA table,A0 ; ADDA.L D0,A0
        w += ([0x3c3c, n // 2 - 1] if n > 128 else [0x7c00 | (n // 2 - 1)])   # D6 = paires - 1 (forme d'origine)
        w += [0x45e8, attr_off, 0x48e7, 0x1400,                             # LEA attr(A0),A2 ; MOVEM.L D3/D5,-(SP)
              0x7200, 0x7600, 0x3a3c, 0x1600]                                # MOVEQ #0,D1/D3 ; MOVE.W #$1600,D5
        boucle = len(w)
        code = [0x3018, 0xd045, 0x32c0] if plus else [0x32d8]                 # code (+ $1600) ou MOVE.W (A0)+,(A1)+
        w += [0x161a, 0x121a] + code + [0x32c1] + code + [0x32c3]            # octets lus un a un : (A2) = octet PS2
                                                                             # impair (entree 2), 1(A2) = pair (entree 1)
        w += [0x51ce, (2 * boucle - 2 * (len(w) + 1)) & 0xffff]              # DBRA D6,boucle
        w += [0x3203, 0x4cdf, 0x0028, 0x4e75]                                # D1 = dernier octet ; MOVEM.L (SP)+ ; RTS
        if not plus: w[-1:-1] = [0x3028, 0xfffe]                             # D0 = dernier code (MOVE.W -2(A0),D0)
        return w
    R1 = recopie(0x61F3F0, 0xe188, 256, 0x200, True)      # LSL.L #8 : blocs de 768 o, 256 entrees, codes + $1600
    R2 = recopie(0x63A9F0, 0xed88, 64, 0x80, False)       # LSL.L #6 : blocs de 192 o, 64 entrees
    # (HANDOFF §104) 0xF72F8 : table de defilement par ligne (combat) : 40 entrees $C0 + partie entiere d'un
    # accumulateur ($1C, long echange) puis 16 entrees d'un second ($18), puis remplissages. Accumulateur garde en
    # registre (D7, sauve) au lieu d'un aller-retour memoire par entree ; remplissages par longs. La reecriture part
    # de 0xF72D8 (les deux CLR.L : accumulateurs a 0, ecrits en memoire a la fin de chaque boucle).
    def bcl(w, debut): return 0x6a00 | ((2 * debut - 2 * (len(w) + 1)) & 0xff)          # BPL.S debut
    DEF = [0x302c, 0x0020, 0x43f3, 0x0000,               # MOVE.W $20(A4),D0 ; LEA 0(A3,D0.W),A1
           0x2f07, 0x7e00, 0x7227]                       # MOVE.L D7,-(SP) ; MOVEQ #0,D7 (CLR.L $1C juste avant) ; MOVEQ #39,D1
    l1 = len(DEF)
    DEF += [0x4847, 0x3007, 0x4847, 0x0640, 0x00c0, 0x32c0, 0xde83, 0x5341]   # D0 = $C0 + V.hi ; (A1)+ ; V += D3
    DEF += [bcl(DEF, l1)]
    DEF += [0x4847, 0x2947, 0x001c,                      # SWAP D7 ; MOVE.L D7,$1C(A4)
            0x302c, 0x0020, 0x43f3, 0x0000,              # MOVE.W $20(A4),D0 ; LEA 0(A3,D0.W),A1
            0x7e00, 0x720f]                              # MOVEQ #0,D7 ($18 remis a 0 juste avant) ; MOVEQ #15,D1
    l2 = len(DEF)
    DEF += [0x9e83, 0x4847, 0x3007, 0x4847, 0x0640, 0x00c0,   # V -= D3 ; D0 = $C0 + V.hi
            0x0c41, 0x0008, 0x6602, 0x3400, 0x3300, 0x5341]   # CMPI #8,D1 ; BNE.S ; MOVE.W D0,D2 ; -(A1) ; SUBQ
    DEF += [bcl(DEF, l2)]
    DEF += [0x4847, 0x2947, 0x0018,                      # SWAP D7 ; MOVE.L D7,$18(A4)
            0x3e00, 0x4847, 0x3e00, 0x7243]              # D7 = D0:D0 ; MOVEQ #67,D1 ($88 mots)
    l3 = len(DEF); DEF += [0x2307, 0x5341]; DEF += [bcl(DEF, l3)]       # MOVE.L D7,-(A1) ; SUBQ ; BPL
    DEF += [0x3e02, 0x4847, 0x3e02, 0x721f]              # D7 = D2:D2 ; MOVEQ #31,D1 ($40 mots)
    l4 = len(DEF); DEF += [0x2307, 0x5341]; DEF += [bcl(DEF, l4)]
    DEF += [0x4cdf, 0x0080, 0x4e75]                      # MOVEM.L (SP)+,D7 (drapeaux gardes) ; RTS
    # (HANDOFF §104) 0x89A10 : binaire -> BCD (scores) : pour chaque bit a 1 de D0, addition BCD de 8 octets
    # (table A2, pas de 8) dans l'accumulateur A3. Le MIPS traite les octets PS2 A-8..A-1 en montant ; en 68K
    # (octet PS2 p = 68K p^1) : deplacements -7,-8,-5,-6,-3,-4,-1,-2. Chaque ABCD etait emule (~15 instructions).
    BCD = [0x48e7, 0x0600]                               # MOVEM.L D5-D6,-(SP)
    lb = len(BCD)
    BCD += [0xe288, 0x6400]                              # LSR.L #1,D0 ; BCC.S saut (deplacement pose plus bas)
    ib = len(BCD) - 1
    BCD += [0x023c, 0x00ef]                              # ANDI #$EF,CCR (X = 0 ; LSR l'a mis a 1)
    for d_ in (-7, -8, -5, -6, -3, -4, -1, -2):
        BCD += [0x1a2a, d_ & 0xffff, 0x1c2b, d_ & 0xffff, 0xcd05, 0x1746, d_ & 0xffff]   # ABCD (A2)d,(A3)d via D5/D6
    BCD[ib] |= (2 * len(BCD) - 2 * (ib + 1)) & 0xff
    BCD += [0x504a, 0x5342, 0x6a00, (2 * lb - 2 * (len(BCD) + 3)) & 0xffff]   # ADDQ.W #8,A2 ; SUBQ.W #1,D2 ; BPL.W
    BCD += [0x4cdf, 0x0060, 0x4e75]                      # MOVEM.L (SP)+,D5-D6 ; RTS
    for va, ws_, fin in ((0x898e0, REMPL, 0x89998), (0x89a10, BCD, 0x89c88), (0x10dd50, R1, 0x10dec4), (0x10e200, R2, 0x10e360),
                         (0xf72d8, DEF, 0xf75f4))[:int(os.environ.get("MAINS", "99")) if P['mains'] else 0]:
        a0_ = lab(va)
        fin_ = lab(fin + 4)                                  # apres le RTS de la routine traduite
        assert fin_ - a0_ >= 2 * len(ws_), "routine %x : place %d < %d" % (va, fin_ - a0_, 2 * len(ws_))
        struct.pack_into('>%dH' % len(ws_), img, a0_, *ws_)
        print("routine %x reecrite a la main (%d mots en $%x)" % (va, len(ws_), a0_))
    # INTRO CALEE SUR LA MUSIQUE (HANDOFF §103). L'arcade (ROM $4CCE/$4CE8) lit a chaque tick le repere de musique
    # que le Z80 ecrit en RAM partagee ($618021) dans $B(A5) ; les scenes avancent sur ces reperes. Le portage PS2
    # (musique differente) le remplace par une table de ticks (0x5855C0, index $C18E(A5)) qui deborde de ~90 images
    # sur la musique arcade. On remet la lecture arcade ; le premier tick apres l'init (index $C18E = 0) efface le
    # repere comme l'arcade a l'init.
    if P['musique']:
        d0_, d1_ = lab(P['musique'][0]), lab(P['musique'][1]); IXM = P['musique'][2]
        MUS = [0x4a6d, IXM, 0x660a,                          # TST.W $C18E(A5) ; BNE.S lire
               0x4239, 0x0061, 0x8021,                       # CLR.B $618021.L
               0x586d, IXM,                                  # ADDQ.W #4,$C18E(A5)
               0x1b79, 0x0061, 0x8021, 0x000b]               # lire : MOVE.B $618021.L,$B(A5)
        MUS += [0x6000, (d1_ - (d0_ + 2 * len(MUS) + 2)) & 0xffff]   # BRA.W suite (ADDQ.W #1,$6(A5))
        assert d1_ - d0_ >= 2 * len(MUS), "repere musique : place"
        struct.pack_into('>%dH' % len(MUS), img, d0_, *MUS)
        print("intro : repere de musique arcade en $%x (au lieu de la table de ticks PS2)" % d0_)
    data = bytearray(buf[end:]); data = data[:len(data)//2*2]
    demo = os.environ.get("MAX_DEMO")                    # (HANDOFF §99) ex. pl26 : garde de Ryu -> frames 0-5 du perso MAX
    if demo:
        import json
        adr = json.load(open(os.path.join(W, "banques", demo + "_frames.json")))
        # correspondance « frame de Ryu -> frame du perso MAX » de la session MAX (test_banc/frames_test.json) :
        # tout long des donnees egal a l'adresse d'execution d'une frame de Ryu est redirige
        corr = json.load(open(os.path.expanduser("~/.cache/sfa3max/converti/%s/test_banc/frames_test.json" % demo)))
        m = {int(e["ryu_frame_execution"], 16): adr[e["eagle_psp_frame"]] for e in corr}
        f5_ = os.path.expanduser("~/.cache/sfa3max/converti/%s/test_banc/frames_test_ro5.json" % demo)
        if MODULE == 'ro5' and os.path.exists(f5_):
            # (HANDOFF §129) correspondance d'Upper fournie par la session MAX (adresses FICHIER ro5, 20/20)
            m = {int(e["ro5_fichier"], 16) + T.RUNTIME_BASE: adr[e["eagle_psp_frame"]] for e in json.load(open(f5_))}
            print("demonstration %s (Upper) : %d frames de Ryu (frames_test_ro5.json)" % (demo, len(m)))
        elif MODULE == 'ro5':
            # (HANDOFF §129) correspondance donnee en adresses de SFA3 (ro3) : le bloc des frames de Ryu d'Upper a la meme
            # disposition a +$D75EC (codes de tuiles differents) ; frame gardee si son en-tete (type, T, n-1) est identique
            b3_ = open(os.path.join(os.path.dirname(module_chemin()), "ro3_usa_prog68k.bin"), "rb").read()
            m5 = {}
            for a3, d_ in m.items():
                f3 = a3 - T.RUNTIME_BASE; f5 = f3 + 0xD75EC
                if struct.unpack_from('<HHH', b3_, f3) == struct.unpack_from('<HHH', buf, f5): m5[f5 + T.RUNTIME_BASE] = d_
            print("demonstration %s (Upper) : %d frames de Ryu sur %d retrouvees a +$D75EC" % (demo, len(m5), len(m)))
            m = m5
        nred = 0
        for o in range(0, len(data) - 3, 2):
            v = struct.unpack_from('<I', data, o)[0]
            if v in m: struct.pack_into('<I', data, o, m[v]); nred += 1
        print("demonstration %s : %d frames de Ryu, %d pointeurs rediriges" % (demo, len(m), nred))
    # (PALETTES MAX) les 30 palettes du perso MAX (format du module : mots 0x0RGB, luminosite 0, mot 15 = numero) a la
    # place de celles d'un perso du jeu dans la table moteur fichier 0x451230 (PS2 0x641230 : 32 decalages u16 par ID,
    # relatifs a la table). Le moteur copie lui-meme son groupe de 5 (((ism + 1) x 2 + $129) x 5) dans les palettes
    # d'objets du joueur : aucune prise Lua. MAX_PAL=plNN (defaut : MAX_DEMO), MAX_PAL_ID = ID remplace (defaut 0, Ryu).
    pal = os.environ.get("MAX_PAL", demo or "") if P['palettes'] else ""
    if pal:
        TPAL, NPAL = P['palettes'], 30                     # decalage FICHIER de la table
        pid = int(os.environ.get("MAX_PAL_ID", "0"), 16)
        # (HANDOFF §119) Upper : 40 decalages SIGNES (T.Hawk et Shin Akuma ont leur bloc AVANT la table)
        NID = 0x28 if MODULE == 'ro5' else 0x20
        tab = struct.unpack_from('<%dh' % NID, buf, TPAL)
        _part = [i for i in range(NID) if tab[i] == tab[pid] and i != pid]
        # (HANDOFF §129) Upper : Ryu (0) partage son bloc avec $26 (place MAX qui reprend Ryu) -> avertissement seulement
        if _part: print("palettes : bloc de l'ID %x partage avec %s (tous recoivent les palettes MAX)" % (pid, ",".join("%x" % i for i in _part)))
        src = open(os.path.expanduser("~/.cache/sfa3max/converti/%s/palettes_module.bin" % pal), "rb").read()
        assert len(src) == 32 * NPAL, "%s : %d palettes (%d attendues : 6 groupes de 5)" % (pal, len(src) // 32, NPAL)
        assert all(src[32*k+30] == k and src[32*k+31] == 0 for k in range(NPAL)), "%s : mot 15 != numero" % pal
        o = TPAL + tab[pid] - end                        # indice dans 'data' (octets du fichier, petit-boutistes)
        data[o:o+len(src)] = src
        print("palettes %s : %d palettes a la place de l'ID %x (fichier $%x)" % (pal, NPAL, pid, TPAL + tab[pid]))
    # (HANDOFF §130) PORTRAITS D'UN PERSO MAX (Upper, fork) : MAX_PORTRAITS=plNN (session MAX : portraits.json,
    # portraits_palettes.bin, tuiles ~/.cache/sfa3max/fork/max_portraits_gfx.bin chargees au code $5C06C).
    # Frames de type 8 (u16 8, T, n-1, n x (code, attr, x, y)) : code + $1C00 -> emplacement 1 (plan2.bin du fork).
    # plan2.bin (copie de travail !) est prolonge : index locaux PB1 + k -> code global $5C06C + k (meme alignement
    # modulo 16 : un objet de largeur w lit code + i dans sa ligne de 16). Bloc externe $D60000 : palettes de portrait
    # (copie du bloc de Ryu, 4 premieres remplacees) + frames ; table des palettes 0x53BDF0 et table des poses
    # 0x484C00 redirigees pour l'ID du perso (fourni par le paquet).
    por = os.environ.get("MAX_PORTRAITS")
    EXT_PLUS = []; pid = None; SELPAL = None
    if por and MODULE == 'ro5':
        import json
        PB, G0 = 0xD60000, 0x5C06C
        CV = os.path.expanduser("~/.cache/sfa3max/converti/%s/" % por)
        pj = json.load(open(CV + "portraits.json"))
        import array
        hx = array.array('I', open(os.path.expanduser("~/.cache/sfa3max/fork/p%s_portraits_hx.bin" % por[2:]), "rb").read())
        pl2p = os.path.join(W, "banques_hx", "plan2.bin")
        p2 = array.array('I', open(pl2p, "rb").read())
        if len(p2) <= 0xA60C or p2[0xA60C] != G0:         # prolongement (une fois) : PB1 = $A60C (= $5C06C mod 16)
            p2 = p2[:0xA60C] + array.array('I', [0xFFFFFFFF] * max(0, 0xA60C - len(p2))) + array.array('I', range(G0, G0 + 0x2000))
            open(pl2p, "wb").write(p2.tobytes())
        # (HANDOFF §131) le rendu des frames de type 8 d'Upper ajoute $1C00 (mips 0x1414A4, ADDI.L #$1C000000), et non $1600
        loc = lambda L: 0xA60C + (int(hx[L]) - G0) - 0x1C00   # code de frame (u16) pour la tuile locale L
        blk = bytearray()
        pal0 = struct.unpack_from('<I', buf, 0x53BDF0)[0] - T.RUNTIME_BASE      # bloc de Ryu (ID 0)
        pb = bytearray(buf[pal0:pal0 + 0x600]); src = open(CV + "portraits_palettes.bin", "rb").read()
        pb[:len(src)] = src; blk += pb
        offs = struct.unpack_from('<66H', buf, 0x484C00); nred = 0; pid = None
        for fam, x in pj.items():
            a = PB + len(blk); objs = x["objs"]
            blk += struct.pack('<HHH', 8, x["T"], len(objs) - 1)
            for L, at, xx, yy in objs: blk += struct.pack('<HHhh', loc(L) & 0xffff, at & 0xffff, xx, yy)
            for po in x["poses"]:
                t_ = po["table_0x484C00"]; pid = t_["id"]
                o = 0x484C00 + offs[t_["pose"]] + 8 * t_["id"] + 4 - end
                if t_["id"] < 40: struct.pack_into('<I', data, o, a); nred += 1
        if pid is not None and pid < 40: struct.pack_into('<I', data, 0x53BDF0 + 4 * pid - end, PB)
        # (HANDOFF §131) palettes du portrait de SELECTION (rendu 0x56E9C : $1BB4E0 + table[perso] + variante x $80,
        # 6 variantes x 4 palettes) : decalages 16 bits -> deviation 68K (voir plus bas) vers ce bloc (6 x les 4)
        while len(blk) & 0x1f: blk += b"\0"
        SELPAL = PB + len(blk)
        vf_ = CV + "portraits_palettes_variantes.bin"; mp_ = pj.get("128x224", {}).get("variantes", {}).get("palette_du_fichier_vers_r")
        if os.path.exists(vf_) and mp_ and all(int(f) < 4 for f in mp_):
            # (HANDOFF §131) 6 variantes de la session MAX (24 palettes, index 4v + r) : la palette r de la variante v est
            # posee a la place de sa palette d'origine f dans le fichier -> attributs des objets inchanges
            vv_ = open(vf_, "rb").read()
            for v_ in range(6):
                q_ = bytearray(src[:0x80])
                for f_, r_ in mp_.items(): q_[32*int(f_):32*int(f_)+32] = vv_[32*(4*v_+r_):32*(4*v_+r_)+32]
                blk += q_
            print("portraits : 6 variantes de selection (fichier -> r : %s)" % mp_)
        else:   # sans variantes (ou palette d'origine >= 4, ex. Ingrid : remappage des attributs a faire) : les 4 repetees
            blk += src[:0x80] * 6
        blk += bytes(len(blk) & 1)
        open(os.path.join(W, "ext_%06x.bin" % PB), "wb").write(bytes(b for i in range(0, len(blk), 2) for b in (blk[i+1], blk[i])))
        EXT_PLUS.append("%06x" % PB)
        print("portraits %s : %d poses redirigees (ID %s), palettes + frames en $%x (%d o), plan2 prolonge" % (por, nred, pid, PB, len(blk)))
    nrel=0
    for o in range(0, len(data) - 3, 4) if not T.CODE_CONV else ():   # (ancienne relocation statique)
        v = struct.unpack_from('<I', data, o)[0]
        if T.is_code_ptr(v):
            struct.pack_into('<I', data, o, lab(v - T.RUNTIME_BASE)); nrel += 1
    if T.RELOGE_RAM_TABLES:                              # (amorce de l'etape C) pointeurs RAM PS2 -> $FFxxxx
        R_ = T.RAM_HI << 16; nrr = 0
        for p_, f_ in sorted(T.RELOGE_RAM_TABLES.items()):
            for a_ in range(p_, f_, 4):
                o_ = a_ - T.CODE_END_RT; v_ = struct.unpack_from('<I', data, o_)[0]
                if v_ == 0: continue
                assert R_ <= v_ < R_ + 0x10000
                l_ = v_ - R_ + 0xff0000                  # = talon $400 (plage (R, R + $10000) -> $FF0000)
                if p_ in T.RELOGE_NATIF_TABLES: struct.pack_into('<HH', data, o_, l_ >> 16, l_ & 0xffff)
                else: struct.pack_into('<I', data, o_, l_)
                nrr += 1
        print("etape C (amorce) : %d tables de pointeurs RAM relogees (%d cases), %d lectures sans talon" % (
              len(T.RELOGE_RAM_TABLES), nrr, len(T.RELOGE_RAM_SITES)))
        with open(os.path.join(W, "etapeC_ram.txt"), "w") as f_:
            for p_, f2_ in sorted(T.RELOGE_RAM_TABLES.items()):
                f_.write("table %06x-%06x  68K $%06x  %d cases%s\n" % (p_, f2_, T.addr_to_68k(p_) & 0xffffff, (f2_ - p_) // 4,
                         "  ordre 68K" if p_ in T.RELOGE_NATIF_TABLES else ""))
            for va_, n_, tb_ in T.RELOGE_RAM_SITES:
                f_.write("lecture mips %07x A%d $%06x  table %06x\n" % (va_, n_, lab(va_), tb_[0]))
    if T.RELOGE_TABLES:                                  # (ETAPE B) cases des tables de code -> etiquettes 68K
        nrc = 0; kset = set(keys)
        for p_, f_ in sorted(T.RELOGE_TABLES.items()):
            for a_ in range(p_, f_, 4):
                o_ = a_ - T.CODE_END_RT; v_ = struct.unpack_from('<I', data, o_)[0]
                if v_ == 0: continue
                assert v_ in kset, "etape B : case %x = %x hors des cles" % (a_, v_)
                l_ = lab(v_ - T.RUNTIME_BASE)
                if p_ in T.RELOGE_NATIF_TABLES: struct.pack_into('<HH', data, o_, l_ >> 16, l_ & 0xffff)   # ordre 68K
                else: struct.pack_into('<I', data, o_, l_)       # moities echangees (recette cps2)
                nrc += 1
        print("etape B : %d tables de code relogees (%d cases, %d tables en ordre 68K), %d sites directs%s" % (len(T.RELOGE_TABLES),
              nrc, len(T.RELOGE_NATIF_TABLES), len(T.RELOGE_SITES), " (CONTROLE : talon de code garde)" if _AS.RELOGE_CODE == 2 else ""))
        with open(os.path.join(W, "etapeB_reloge.txt"), "w") as f_:
            for p_, f2_ in sorted(T.RELOGE_TABLES.items()):
                f_.write("table %06x-%06x  68K $%06x  %d cases%s\n" % (p_, f2_, T.addr_to_68k(p_) & 0xffffff, (f2_ - p_) // 4,
                         "  ordre 68K" if p_ in T.RELOGE_NATIF_TABLES else ""))
            for va_, n_, tb_ in T.RELOGE_SITES:
                f_.write("site mips %07x A%d $%06x  tables %s\n" % (va_, n_, lab(va_), ",".join("%06x" % t for t in tb_)))
    data = bytes(data)
    print("pointeurs de code relocalises dans les donnees :", nrel)
    be = bytes(b for i in range(0, len(data), 2) for b in (data[i+1], data[i]))
    if T.DATA_SPLIT:                                     # (HANDOFF §108) fin des donnees : bloc externe (banc_mem.lua)
        k_ = T.DATA_SPLIT - T.CODE_END_RT
        if SON_BLOB is not None:                         # (agent_son_hyper_rom) bloc ajoute a la suite
            assert T.DATA_EXT + len(be) - k_ == T.son_y()
            be = be + bytes(b for i in range(0, len(SON_BLOB), 2) for b in (SON_BLOB[i+1], SON_BLOB[i]))
            print("donnees du son par version : %d octets, exec $%x -> $%x" % (len(SON_BLOB), T.SON_X, T.son_y()))
        open(os.path.join(W, "ext_%06x.bin" % T.DATA_EXT), "wb").write(be[k_:])
        print("donnees externes : %d octets -> ext_%06x.bin" % (len(be) - k_, T.DATA_EXT))
        be = be[:k_]
    img[T.DATA_BASE:T.DATA_BASE+len(be)] = be
    if por and MODULE == 'ro5' and pid is not None:
        # (HANDOFF §131) deviation du rendu des palettes de selection pour l'ID MAX (index pid x 2 dans D0) :
        # 'LEA $1BB4E0,A0 ; ADD.W (A0,D0.W),D1 ; ADDA.W D1,A0' -> 'JSR stub ; NOP x3' ; stub dans le trou entre la
        # fin du code et le debut des donnees
        a_ = T.addr_to_68k(0x7251A0) & 0xffffff
        pat = struct.pack('>HHHHHH', 0x41f9, a_ >> 16, a_ & 0xffff, 0xd270, 0x0000, 0xd0c1)
        o_ = img.find(pat, 0, T.DATA_BASE)
        assert o_ > 0 and img.find(pat, o_ + 2, T.DATA_BASE) < 0, "portraits : motif de selection introuvable ou multiple"
        st_ = (CODE + 2 * len(words) + 0x0f) & ~0x0f
        stub = struct.pack('>10H', 0x0c40, 2 * pid, 0x660a, 0x41f9, SELPAL >> 16, SELPAL & 0xffff, 0xd0c1, 0x4e75,
                           0x41f9, a_ >> 16) + struct.pack('>HHHHH', a_ & 0xffff, 0xd270, 0x0000, 0xd0c1, 0x4e75)
        assert st_ + len(stub) <= T.DATA_BASE and not any(img[st_:st_ + len(stub)]), "portraits : pas de place pour le stub"
        img[st_:st_ + len(stub)] = stub
        img[o_:o_ + 12] = struct.pack('>HHHHHH', 0x4eb9, st_ >> 16, st_ & 0xffff, 0x4e71, 0x4e71, 0x4e71)
        print("portraits : deviation des palettes de selection en $%x (stub $%x, palettes $%x)" % (o_, st_, SELPAL))
    # (HANDOFF §103) table 0x585750 (objets de l'intro : type, parametre) : le MIPS lit le parametre par
    # 'lb 0x1129', octet HAUT du mot charge dans D1 (seul acces octet a +1 d'un registre de tout le module, retouche
    # du portage : table aux octets arcade). La traduction lit l'octet bas (MOVE.B D1) -> parametre 0 pour tous,
    # bits de scene 4/2/0 au lieu de 5..0 ($FF8017 = $15 au lieu de $3F), fondus des portraits jamais lances.
    # Seul lecteur de la table : on echange les octets du parametre dans l'image.
    if P['objets_intro']:                                # (agent_ro9) ro9 : table absente
        t_ = T.addr_to_68k(P['objets_intro'])
        for k_ in range(12):
            o_ = t_ + 4 * k_ + 2
            img[o_], img[o_ + 1] = img[o_ + 1], img[o_]
        print("table 0x585750 en $%x : parametres remis en octet bas" % t_)
    if T.HW_TAG:
        assert T.DATA_BASE + len(be) <= ASSET
        tperso = ASSET + len(ablob)
        assert tperso + 4*len(aperso) <= len(img), "bloc d'animation hors de l'image"
        img[ASSET:ASSET+len(ablob)] = bytes(b for i in range(0, len(ablob), 2) for b in (ablob[i+1], ablob[i]))
        for k, n in enumerate(aperso):                   # table index -> pointeur (long lu par le 68K : moities echangees)
            struct.pack_into('>I', img, tperso + 4*k, AN.swapped(ava[n]) if n else 0)
        for k, n in enumerate(asite):                    # MOVE.L #ptr,$be48(A5) ; RTS
            struct.pack_into('>HIHH', img, stub_site[k], 0x2b7c, AN.swapped(ava[n]), P['be48'], 0x4e75)
        o = (AN.PERSO_OFS ^ 1)                           # octet MIPS -> 68K (recette cps2 : XOR 1)
        st = [0x48e7, 0x8080,                            # MOVEM.L D0/A0,-(SP)
              0x7000, 0x102d, o,                         # MOVEQ #0,D0 ; MOVE.B $133(A5),D0
              0x0c40, AN.N_PERSO, 0x6412,                # CMPI.W #$20,D0 ; BCC fin
              0xe548, 0x41f9, tperso >> 16, tperso & 0xffff,   # LSL.W #2,D0 ; LEA table,A0
              0x2030, 0x0000, 0x6704,                    # MOVE.L 0(A0,D0.W),D0 ; BEQ fin
              0x2b40, P['be48'],                         # MOVE.L D0,$be48(A5)
              0x4cdf, 0x0101, 0x4e75]                    # fin : MOVEM.L (SP)+,D0/A0 ; RTS
        struct.pack_into('>%dH' % len(st), img, stub_perso, *st)
        assert stub_perso + 2*len(st) <= 0x900
        o_dyn = stub_perso + 2*len(st); stub_dyn = {}
        for site, (octet, dec) in AN.SITES_DYN.items():  # (HANDOFF §108) index du fichier choisi a l'execution
            p0, p1 = AN.swapped(ava[asite[0]]), AN.swapped(ava[asite[1]])
            sd = [0x2f00, 0x102d, (octet ^ 1) & 0xffff, 0xe008 | (dec << 9), 0x0240, 0x0001, 0x660a,
                  0x2b7c, p0 >> 16, p0 & 0xffff, P['be48'], 0x6008,
                  0x2b7c, p1 >> 16, p1 & 0xffff, P['be48'], 0x201f, 0x4e75]
            struct.pack_into('>%dH' % len(sd), img, o_dyn, *sd); stub_dyn[site] = o_dyn; o_dyn += 2*len(sd)
        assert o_dyn <= 0x900
        # (HANDOFF §122) Upper : talons par JOUEUR pour le chargeur par perso. Reproduisent la fonction native 0x2141A0 :
        # perso = octet ROM $102 de la structure ($FF8400 + p*$400 ; 68K $103), index = table[perso] (octets, XOR 1),
        # sauf ($13F(A5) == 4 et +$125 != 0 et perso == $0A) -> $15 ; index 4 et +$132 < 0 -> $12 ; 6 et +$132 < 0 -> $14.
        stub_pj = {}
        if AN.PERSO_JOUEUR:
            tab68 = T.addr_to_68k(AN.PERSO_TABLE) & 0xffffff
            o_pj = tperso + 4*len(aperso)
            for pj in (0, 1):
                base = 0xFF8400 + 0x400 * pj
                w = []; lab_ = {}; fix = []
                def E(*ws): w.extend(ws)
                def B(op, cible): fix.append((len(w), cible)); w.append(op)      # Bcc.S, deplacement resolu apres
                E(0x48e7, 0xc0c0)                                   # MOVEM.L D0-D1/A0-A1,-(SP)
                E(0x43f9, base >> 16, base & 0xffff)                # LEA base,A1
                E(0x7000, 0x1029, 0x0103)                           # MOVEQ #0,D0 ; MOVE.B $103(A1),D0
                E(0x0c2d, 0x0004, 0x013e); B(0x6600, 'tbl')         # CMPI.B #4,$13E(A5) ; BNE tbl
                E(0x4a29, 0x0124); B(0x6700, 'tbl')                 # TST.B $124(A1) ; BEQ tbl
                E(0x0c00, 0x000a); B(0x6600, 'tbl')                 # CMPI.B #$A,D0 ; BNE tbl
                E(0x7015); B(0x6000, 'load')                        # MOVEQ #$15,D0 ; BRA load
                lab_['tbl'] = len(w)
                E(0x223c, tab68 >> 16, tab68 & 0xffff)              # MOVE.L #table,D1
                E(0xd280, 0x0a81, 0x0000, 0x0001)                   # ADD.L D0,D1 ; EORI.L #1,D1
                E(0x2041, 0x1010, 0x4880)                           # MOVEA.L D1,A0 ; MOVE.B (A0),D0 ; EXT.W D0
                E(0x0c40, 0x0004); B(0x6600, 'c6')                  # CMPI.W #4,D0 ; BNE c6
                E(0x4a29, 0x0133); B(0x6a00, 'c6')                  # TST.B $133(A1) ; BPL c6
                E(0x7012)                                           # MOVEQ #$12,D0
                lab_['c6'] = len(w)
                E(0x0c40, 0x0006); B(0x6600, 'load')                # CMPI.W #6,D0 ; BNE load
                E(0x4a29, 0x0133); B(0x6a00, 'load')                # TST.B $133(A1) ; BPL load
                E(0x7014)                                           # MOVEQ #$14,D0
                lab_['load'] = len(w)
                E(0x0c40, AN.N_PERSO); B(0x6400, 'fin')             # CMPI.W #N,D0 ; BCC fin
                E(0xe548, 0x41f9, tperso >> 16, tperso & 0xffff)    # LSL.W #2,D0 ; LEA table des pointeurs,A0
                E(0x2030, 0x0000); B(0x6700, 'fin')                 # MOVE.L 0(A0,D0.W),D0 ; BEQ fin
                E(0x2b40, P['be48'])                                # MOVE.L D0,$be48(A5)
                lab_['fin'] = len(w)
                E(0x4cdf, 0x0303, 0x4e75)                           # MOVEM.L (SP)+,D0-D1/A0-A1 ; RTS
                for k_, c_ in fix:
                    dsp = 2 * (lab_[c_] - (k_ + 1)); assert -128 <= dsp < 128 and dsp != 0
                    w[k_] |= dsp & 0xff
                assert o_pj + 2*len(w) <= len(img)
                struct.pack_into('>%dH' % len(w), img, o_pj, *w); stub_pj[pj] = o_pj; o_pj += 2*len(w)
            # (HANDOFF §122) talon du chargeur de FIN : index = octet bas de D8 (domicile $87F0(A5)), table des pointeurs
            afin = AN.fin_tables(buf) if AN.T_FIN else []
            if afin:
                tfin = o_pj
                for k, n in enumerate(afin): struct.pack_into('>I', img, tfin + 4*k, AN.swapped(ava[n]) if n else 0)
                o_pj = tfin + 4*len(afin)
                w = [0x48e7, 0x8080, 0x7000, 0x102d, (T.D8_HOME + 1) & 0xffff,   # MOVEM.L D0/A0,-(SP) ; MOVEQ #0,D0 ;
                                                                       # MOVE.B $87F1(A5),D0 (octet bas de D8 = index)
                     0x0c40, len(afin), 0x6412,                        # CMPI.W #N,D0 ; BCC fin
                     0xe548, 0x41f9, tfin >> 16, tfin & 0xffff,        # LSL.W #2,D0 ; LEA tfin,A0
                     0x2030, 0x0000, 0x6704,                           # MOVE.L 0(A0,D0.W),D0 ; BEQ fin
                     0x2b40, P['be48'],                                # MOVE.L D0,$be48(A5)
                     0x4cdf, 0x0101, 0x4e75]                           # fin : MOVEM.L (SP)+,D0/A0 ; RTS
                struct.pack_into('>%dH' % len(w), img, o_pj, *w); stub_pj['fin'] = o_pj; o_pj += 2*len(w)
            tperso_fin = o_pj
        for it in its:                                   # sites de 0x383700 autres que l'index 0 : vers leur talon
            if it.kind == 'call' and it.va in AN.FIN_SITES and 'fin' in stub_pj:
                patch_call(img, it, stub_pj['fin']); continue
            if it.kind == 'call' and it.va in AN.PERSO_JOUEUR and stub_pj:
                patch_call(img, it, stub_pj[AN.PERSO_JOUEUR[it.va]]); continue
            if it.kind == 'call' and it.va in stub_dyn:
                patch_call(img, it, stub_dyn[it.va])
            elif it.kind == 'call' and it.va in AN.SITES and AN.SITES[it.va]:
                patch_call(img, it, stub_site[AN.SITES[it.va]])
        print("tables d'animation natives : %d fichiers, %d octets en $%x" % (len(ava), len(ablob), ASSET))
        assert (tperso_fin if stub_pj else tperso + 4*len(aperso)) <= (HASH or CODEMAP), "donnees + blocs chevauchent la table des adresses de code"
        cible = {v: lab(v - T.RUNTIME_BASE) for v in keys}
        # (agent_options, OPTIONS.md) OPTION du menu des modes : la tache de l'ecran d'options du portage est du C
        # natif (affichage PS2, reglages dans la sauvegarde de l'Anthology) -> sans traduction : ecran noir.
        # OPTION_RETOUR=1 (defaut) : l'adresse de cette tache se convertit en celle de la routine de SORTIE de l'ecran
        # (traduite : applique, remet l'etat a zero, relance la tache d'amorcage) = OPTION puis EXIT tout de suite ;
        # retour a l'ecran-titre puis au menu. Les reglages passent par les options du coeur / banc_options.lua.
        # OPTION_RETOUR=0 : ancien comportement (ROM identique).
        if P.get('option') and os.environ.get("OPTION_RETOUR", "1") != "0":
            tache, sortie = P['option'][:2]
            assert tache in cible and sortie in cible, "OPTION_RETOUR : %x / %x absentes de la table" % (tache, sortie)
            cible[tache] = cible[sortie]
            print("OPTION : tache %x -> sortie de l'ecran d'options %x ($%x) (agent_options, OPTION_RETOUR)" % (tache, sortie, cible[sortie]))
        # (agent_options) EXIT du menu des modes : appel natif 0x1CAC80 (retour au menu general de l'Anthology) -> talon
        # RTS puis attente sans fin (ecran noir). EXIT_RETOUR=1 (defaut) : l'appel va a la meme routine de sortie (retour
        # au menu des modes ; il n'y a rien a quitter sur CPS2). EXIT_RETOUR=0 : ancien comportement.
        if P.get('option') and os.environ.get("EXIT_RETOUR", "1") != "0":
            # Le menu appelle EXIT depuis SA tache (emplacement $80, celui que la sortie veut recreer) : on fait comme
            # OPTION -> nouvelle tache (emplacement $40) sur la routine de sortie, puis fin de la tache du menu.
            # Tremplin $804 (libre entre le RTE $802 et STUB_ANIM $810, a portee des BSR.W) -> talon pres de CODECONV.
            tache, sortie, creer, finir, curseur = P['option']
            n_exit, STUB_EXIT, TALON = 0, STUB_RTE + 2, CODECONV - 0x20
            assert img[STUB_EXIT:STUB_EXIT+6] == bytes(6) and img[TALON:TALON+0x20] == bytes(0x20) and CODEMAP + 8*len(keys) <= TALON
            struct.pack_into('>HI', img, STUB_EXIT, 0x4ef9, TALON)                          # JMP talon.L
            # curseur du menu remis sur OPTION (5) : la tache relancee par la sortie ne montre le menu que dans ce cas
            # (sinon elle lance directement le mode du curseur : EXIT recommencerait, VERSUS partirait)
            struct.pack_into('>HHIHHHIHIHI', img, TALON, 0x13fc, 5, curseur,               # MOVE.B #5,curseur.L
                             0x303c, 0x40, 0x41f9, sortie,                                   # MOVE.W #$40,D0 ; LEA sortie,A0
                             0x4eb9, lab(creer - T.RUNTIME_BASE), 0x4ef9, lab(finir - T.RUNTIME_BASE))   # JSR creer ; JMP finir
            for it in its:
                if it.kind in ('call', 'jump') and getattr(it, 'tgt', None) == 0x1CAC80 - T.RUNTIME_BASE:
                    patch_call(img, it, STUB_EXIT); n_exit += 1
            print("EXIT : %d appel(s) de 0x1cac80 -> tache %x ($%x) creee par $%x, puis $%x (agent_options, EXIT_RETOUR)" % (n_exit, sortie, cible[sortie], lab(creer - T.RUNTIME_BASE), lab(finir - T.RUNTIME_BASE)))
        for k, v in enumerate(keys):                     # table des adresses de code (triee)
            struct.pack_into('>II', img, CODEMAP + 8*k, v, cible[v])
        if HASH is not None:
            ht = K.build_hash([(v, cible[v]) for v in keys])
            assert img[HASH:HASH+len(ht)] == bytes(len(ht)), "table de hachage : zone $%x occupee" % HASH
            img[HASH:HASH+len(ht)] = ht
            print("conversion des adresses de code : table de hachage %d cles en $%x (HANDOFF §98)" % (len(keys), HASH))
        img[CODECONV:CODECONV+len(cconv)] = cconv
        print("adresses de code converties a l'usage : %d debuts de fonction ($%x)" % (len(keys), CODEMAP))
        # SETJMP / LONGJMP du recompilateur (branchements entre fonctions, HANDOFF §75) : tampon en RAM du noyau
        # (+0 pile au moment du setjmp, adresse de retour sur son sommet ; +4 adresse de retour)
        import hooks_fork
        sj = hooks_fork.setjmp_sites(buf)
        bufs = sorted({b for _, b in sj.values()})
        JMPBUF = 0x663890
        assert JMPBUF + 8*len(bufs) <= 0x663900
        o = o_dyn if MODULE == 'ro3' else 0x940; sjs = {}   # (HANDOFF §108) Upper : talons suivants apres l'amorcage
        LIM = 0x900 if o < 0x900 else 0xa00
        for k, b in enumerate(bufs):
            jb = JMPBUF + 8*k
            sjs[('setjmp', b)] = o                       # MOVE.L (A7),jb+4 ; MOVE.L A7,jb ; RTS
            struct.pack_into('>7H', img, o, 0x23d7, (jb+4) >> 16, (jb+4) & 0xffff, 0x23cf, jb >> 16, jb & 0xffff, 0x4e75); o += 14
            sjs[('longjmp', b)] = o                      # MOVEA.L jb,A7 ; MOVE.L jb+4,(A7) ; RTS
            struct.pack_into('>7H', img, o, 0x2e79, jb >> 16, jb & 0xffff, 0x2eb9, (jb+4) >> 16, (jb+4) & 0xffff, 0x4e75); o += 14
        assert o <= LIM, "talons natifs : %x" % o
        for it in its:
            if it.kind == 'call' and it.va in sj:
                patch_call(img, it, sjs[sj[it.va]])
        print("setjmp/longjmp : %d sites, %d tampons" % (len(sj), len(bufs)))
        # COUCHE MANETTE DU PORTAGE (natif 0x381410, HANDOFF §80) : mot d'entrees du joueur = $58/$5C | Start<<15
        # (ROM $1B096) ; A8 (structure joueur) n'est pas transmis : un talon par site (J1 0x89228, J2 0x8924c)
        stub_in = {}
        for site, (shift, src, dst) in P['manette'].items():
            stub_in[site] = o
            st2 = [0x48e7, 0xc000,                       # MOVEM.L D0-D1,-(SP)
                   0x102d, 0x0062, 0x7200,               # MOVE.B $62(A5),D0 ; MOVEQ #0,D1
                   0xe008 | (shift << 9), 0xe251,        # LSR.B #shift,D0 ; ROXR.W #1,D1
                   0x826d, src, 0x3b41, dst,             # OR.W src(A5),D1 ; MOVE.W D1,dst(A5)
                   0x4cdf, 0x0003, 0x4e75]               # MOVEM.L (SP)+,D0-D1 ; RTS
            struct.pack_into('>%dH' % len(st2), img, o, *st2); o += 2*len(st2)
        assert o <= LIM, "talons natifs : %x" % o
        for it in its:
            if it.kind in ('call', 'jump') and it.va in stub_in:
                patch_call(img, it, stub_in[it.va])
        print("couche manette : %d sites" % len(stub_in))
        for n, base in AN.FIXES.items():                 # fichiers a adresse fixe : memoire externe du banc ($A04000...)
            d = AN.fichier(n); d += bytes(len(d) & 1)
            assert all(not (r0 <= base < r1) for r0, r1, _ in ranges), "fichier %d : sa plage serait convertie" % n
            open(os.path.join(W, "ext_%06x.bin" % base), "wb").write(bytes(b for i in range(0, len(d), 2) for b in (d[i+1], d[i])))
            print("fichier %d : %d octets a adresse fixe $%x (banc_mem.lua)" % (n, len(d), base))
        # (agent_ro9) liste des blocs externes pour banc_mem_liste.lua (banc_mem.lua ne connait que des bases fixes)
        exts = sorted(["%06x" % b_ for b_ in AN.FIXES.values()] + (["%06x" % T.DATA_EXT] if T.DATA_SPLIT else []) + EXT_PLUS)
        open(os.path.join(W, "ext_liste.txt"), "w").write("\n".join(exts) + "\n")
    sw = bytes(b for i in range(0, len(img), 2) for b in (img[i+1], img[i]))
    out = os.path.join(W, P['sortie'], "sfa3ud"); os.makedirs(out, exist_ok=True)
    names = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
    for k, n in enumerate(names): open(os.path.join(out, n), "wb").write(sw[k*0x80000:(k+1)*0x80000])
    src = os.path.join("<workspace>/work/mame", "roms", "sfa3ud")
    for f in os.listdir(src):
        if f not in names and not os.path.exists(os.path.join(out, f)): os.symlink(os.path.join(src, f), os.path.join(out, f))
    with open(os.path.join(W, "carte_image.txt"), "w") as f:          # adresse 68K -> va MIPS + mnemonique
        for it in its:
            if it.ws or it.kind!='fixed': f.write("%06x %07x %s\n" % (it.off, it.va, it.mn))
    import assemble as _A
    print("aiguillages : %d entrees hors de portee 16 bits -> tremplins (HANDOFF §93)" % sum(len(v) for v in _A.FAR_ENT.values()))
    print("octets via An apres ADDA Dk,An : %d acces a adresse exacte (HANDOFF §97)" % T.BYTE_ADDA[0])
    print("flux d'octets decroissants -(An) a adresse exacte : %d (agent_ro9)" % T.BYTE_PRE[0])
    print("flux d'octets (An)+ hors Dn a adresse exacte : %d (agent_bandeau_A, FLUXEA)" % T.BYTE_EA[0])
    print("drapeaux rendus places avant un epilogue partage : %d (HANDOFF §126)" % T.FTC_AVANT_N[0])
    print("sauts terminaux absorbes gardes en RTS (cibles de branchements) : %d (agent_coups, TAILBR)" % T.TAILBR_N[0])
    print("constantes lui seules gardees en valeur dans Dn : %d %s (agent_coups, LUIDN)" % (len(T.LUIDN_LOG), sorted({"%x:%x->%x" % e for e in T.LUIDN_LOG})))
    print("coupure des donnees au debut d'un bloc de perso (lignes) : %s (agent_defauts_banc, COUPE_BLOCS)" % ("$%x" % T.DATA_SPLIT if (P.get('blocs_lignes') and COUPE_BLOCS and T.DATA_SPLIT) else "non"))
    print("pointeurs remasques sur 24 bits reetiquetes : %d sites, plages %s (agent_defauts_banc, RETAG24)" % (len(T.RETAG24_N), ",".join("$%x-$%x" % p_ for p_ in plages_retag()) or "aucune"))
    print("echanges Dn<->Dm par la pile MIPS : %d (agent_defauts_banc, EXG_PILE_D)" % len(T.EXG_PILE_D_N))
    print("aide ROXR du recompilateur : %d formes (agent_defauts_banc, AIDE_ROXR)" % len(T.AIDE_ROXR_N))
    print("comparaisons Dn - memoire rendues au branchement : %d (agent_defauts_banc, CMPDMEM)" % len(T.CMPDMEM_N))
    print("BCLR/BSET/BCHG #b,Dn testes avant l'operation : %d (agent_defauts_banc, BITOP_DN)" % len(T.BITOP_DN_N))
    print("comparaisons memoire-memoire par un temporaire : %d appels, %d formes (agent_hyper_defauts, CMPMM)" % (len(T.CMPMM_N), len(set(T.CMPMM_N))))
    if T.CMPX: print("ESSAI CMPX : minuendes en memoire contre Dn : %d formes" % len(set(T.CMPX_N)))
    print("valeurs de table seulement testees : %d (HANDOFF §126)" % T.TBL_TST_N[0])
    print("echanges An<->Am par la pile MIPS : %d (HANDOFF §126)" % T.EXG_PILE_N[0])
    print("aiguillages a index deja x4 : %d (HANDOFF §126)" % T.SW_X4_N[0])
    print("comparaisons exactes a constante lui seule : %d (HANDOFF §126)" % T.LUI_IMM_N[0])
    open(os.path.join(W, 'audit_exacts.txt'), 'w').write(''.join('%07x %s dst=%s src=%s\n' % e for e in T.EXACT_MISS)); print('blocs exacts sans operande (audit_exacts.txt) : %d (HANDOFF §126)' % len(T.EXACT_MISS))
    print('lectures signees etendues (MOVE + EXT) : %d (HANDOFF §128)' % T.EXT_MEM_N[0])
    print('multiplications MULS/MULU (mult du R5900) : %d (HANDOFF §132)' % T.MULS_N[0])
    print('decalages de lectures memoire (plus propages comme extension) : %d (HANDOFF §137)' % T.SHIFT_MR_N[0])
    print('lectures-modifications-ecritures indexees / memoire+memoire / registres elargis : %d (HANDOFF §138)' % T.IDXRMW_N[0])
    print('aiguilleurs C du portage (table de longs indexee par un champ) : %d (HANDOFF §140)' % T.CDISP_N[0])
    print('longs memoire decales vers un registre D : %d (HANDOFF §132)' % T.MEMSHIFT_N[0])
    print('operations D <- long de table : %d (HANDOFF §132)' % T.TBLOP_N[0])
    import extra_regs as _XR; print('sorties laterales de zones A8/D8 : %d prevues, %d reecrites (HANDOFF §130)' % (_XR.LATERAL_N[0], T.LATERAL_REW[0]))
    import extra_regs as _X
    print("zones A8/D8 : retours de boucle sur la restauration : %d (agent_ro9)" % _X.BACK_AFTER_N[0])
    print("longs par post-increment fusionnes : %d (HANDOFF §103)" % T.LONG_POSTINC[0])
    print("adresses video formees par decalage converties : %d (HANDOFF §110)" % T.VRAM_SHIFT[0])
    print("adresses video formees par decalage d'un mot de table converties : %d (agent_decor_cammy, VRAM_TABLE)" % T.VRAM_TABLE[0])
    print("pointeurs de table a index brut (x4) : %d (HANDOFF §112)" % T.IDX_X4[0])
    print("operations sur long echange sans sauvegarde des drapeaux : %d (HANDOFF §104)" % T.LONG_SR[0])
    print("MOVEA.L abs.L,An retrouves : %d (HANDOFF §106)" % T.ABS_AN[0])
    print("ADDA.W d(An),Am retrouves : %d (HANDOFF §107)" % T.ADDA_MEM[0])
    print("ecritures Dn retrouvees (dn_alu) : %d (HANDOFF §107)" % T.DN_ALU[0])
    print("ecritures memoire retrouvees (mem_fix) : %d (HANDOFF §107)" % T.MEM_FIX[0])
    if T.MEM_MISS:
        import json as _js
        _js.dump(sorted({hex(c[0]):c for c in T.MEM_MISS}.keys()), open(os.path.join(W, "mem_miss.json"), "w"))
        print("ecritures memoire sans trace : %d (mem_miss.json)" % len({c[0] for c in T.MEM_MISS}))
    if T.CHUTES:                                         # (HANDOFF §107) ecritures de registre non traduites
        import json as _js
        _js.dump([[hex(c[0])] + list(c[1:]) for c in T.CHUTES], open(os.path.join(W, "chutes.json"), "w"))
        print("ecritures de registre tombees sans traduction : %d (chutes.json)" % len(T.CHUTES))
    print("reset -> $%x (mips %x), IRQ2 -> $%x (mips %x), donnees $%x, non resolus %d"
          % (lab(va_reset), va_reset, lab(va_irq2), va_irq2, T.DATA_BASE, unres))

if __name__ == "__main__":
    main()
