# (L2 des MAX dans la greffe, work/l2_max_greffe/CONCEPTION.md §4.1, §6.2 n° 4) CROCHETS des persos MAX dans le traducteur
# de la greffe ro9a (e47/untranspile3_v161/mame_test.py, tout sous MAX=1). Modèle : integre_max.py d'Upper MAX
# (tools/integration-max/upper_max/integration_2b31/ag/untranspile/), dont on reprend les sous-fonctions utiles au VERSUS
# (notes/S2 §1, colonne « V »), avec les tables d'HYPER (work/max_hyper/moteur/ACTIONS-EAGLE-ro9a.tsv).
# Code et données MAX préparés à part par prep_max_ro9.py (MAX_PREP = dossier « prep » : symboles.json,
# code_3a0000.bin, blocs/ext_710000.bin = données en T4, blocs/ext_1810000.bin = frames et animations d'Eagle en T5),
# assemblés ÉTIQUETÉS $01 (zones 68K directes de la greffe, greffe3.py MAX_ZONES=1).
# MAX=1 sans MAX_PERSOS : rien n'est posé (base MAX à l'octet, pas 4). MAX_SEL : sélection (pas 5).
import os, sys, hashlib, struct, json, re

PERSOS = [p_.lower() for p_ in os.environ.get('MAX_PERSOS', '').split(',') if p_]
RESERVE = 0x20000                                    # zone du code MAX $3A0000-$3BFFFF (greffe3.py D3, RESERVE_MAX=20000)
ZONE_CODE = (0x3C0000 - RESERVE, 0x3C0000)
MAX_SEL = os.environ.get('MAX_SEL', '0') == '1'
MAX_E5 = os.environ.get('MAX_E5', '0') == '1'          # (pas 8) habillage par TABLES (méthode d'Upper MAX) : aperçu (emplacement 0,
# f545 prolongée), HUD / portraits / noms (emplacement 1 : suite de plan2 jamais employée, plan_commun_max.P2_BASE), palettes
# de sélection (talon E, hors combat) ; aucun talon dans les boucles de rendu
MAX_CRIS = os.environ.get('MAX_CRIS', '0') == '1'      # (pas 9) cris d'Eagle : seulement avec la ROM son MAX (paquet sfa3hamhsfa)
CRIS = {'26': 0x05D9}                                  # base des cris d'Eagle (agent_son_max, = Upper MAX integre_max.CRIS)
H_CRIS, H_CRIS5 = 0x5C9A90, 0x5C9A40                   # tables d'Hyper (= Upper 0x613490 / 0x613440, contenu natif identique ; [$26] d'Hyper : $0540 / $0545)
# D5 = (b) de l'utilisateur (12/11) : pendant L2, en ARCADE ($C201(A5) = 0) la case d'Eagle reste un « ? » (seuil $26 au
# site d'Hyper, talon ; site greffe garde $26) ; =0 : seuil $2A aux deux sites (variante (a), Eagle choisissable en Arcade)
SEUIL_ARCADE = os.environ.get('MAX_SEUIL_ARCADE', '1') == '1'
RB = 0x1F0000                                        # fichier du module = exec - RB
JOURNAL = []
W_ = [None]
CTX = [None]                                         # (its, T, W) gardé par image() pour fin()
CTX_D = {}
SELPAL = {}                                           # (pas 8) palettes de sélection par perso (adresse étiquetée T4)
SITES = {}                                           # sites de code relevés par image(), modifiés par fin()
P = {}                                               # préparation : SYM, ORG, BLOB, BLOC (T5), CODE

def journal(m):
    JOURNAL.append(m); print('max : ' + m)

def S(n):
    assert n in P['SYM'], 'symbole MAX absent : %s' % n
    return P['SYM'][n]

def charge():
    d = os.environ.get('MAX_PREP')
    assert d and os.path.isdir(d), 'MAX_PERSOS : MAX_PREP (dossier de prep_max_ro9.py) absent : %s' % d
    J = json.load(open(os.path.join(d, 'symboles.json'), encoding="utf-8"))
    P.update(SYM=dict(J['symboles']), ORG=J['org'], J=J, DIR=d,
             BLOB=bytearray(open(os.path.join(d, 'blocs', 'ext_%06x.bin' % (J['org'] & 0xFFFFFF)), 'rb').read()),
             CODE=open(os.path.join(d, 'code_%06x.bin' % J['code_org']), 'rb').read())
    assert J['code_org'] == ZONE_CODE[0] and J['code_org'] + J['reserve'] == ZONE_CODE[1], 'code MAX hors de $3A0000-$3BFFFF'
    assert (J['org'] >> 24) == 1 and 0x710000 <= (J['org'] & 0xFFFFFF) and (J['org'] & 0xFFFFFF) + J['taille'] <= 0x800000, 'données MAX hors de T4'
    # bloc d'Eagle (T5) : binaire et symboles du listing (ANIM_26_PTRS_H : table $2B8 au format d'Hyper)
    b = [f for f in os.listdir(os.path.join(d, 'blocs')) if re.fullmatch(r'ext_18[0-9a-f]{5}\.bin', f)]
    assert len(b) == 1, 'bloc d\'Eagle en T5 : %s' % b
    P['T5'] = int(b[0][4:11], 16); P['BLOC'] = open(os.path.join(d, 'blocs', b[0]), 'rb').read()
    assert 0x810000 <= (P['T5'] & 0xFFFFFF) and (P['T5'] & 0xFFFFFF) + len(P['BLOC']) <= 0x900000, 'bloc d\'Eagle hors de T5'
    for l in open(os.path.join(d, 'blocs', 'bloc_%x.lst' % P['T5']), errors='replace', encoding="utf-8"):
        m = re.match(r'^([0-9A-F]{8}) (\w+)\s*$', l)
        if m: P['SYM'].setdefault(m.group(2), int(m.group(1), 16))
    return P

def debut(W, reserve_max):
    """garde d'entrée (après PLAFOND -= RESERVE_MAX)"""
    assert reserve_max == RESERVE, 'MAX=1 : RESERVE_MAX = $%x, attendu $%x (greffe3.py D3)' % (reserve_max, RESERVE)
    zones = os.environ.get('HSFA_ZONES_68K', '')
    assert '710000-800000' in zones and '810000-900000' in zones, 'MAX=1 exige MAX_ZONES=1 (HSFA_ZONES_68K = %s)' % zones
    assert set(PERSOS) <= {'26'}, 'L2 : seul Eagle ($26) est intégré (MAX_PERSOS=%s)' % ','.join(PERSOS)
    W_[0] = W
    if PERSOS: charge()
    journal('crochets actifs, persos : %s%s' % (','.join(PERSOS) or 'aucun', ' (préparation %s)' % P['DIR'] if PERSOS else ''))

# ------------------------------------------------------------------------------------------------------------------
# tables d'HYPER (ACTIONS-EAGLE-ro9a.tsv ; Upper -> Hyper) : B = par $102 (128 entrées), C = par $116 (40 entrées)
H_COMBAT = ((0x6A57D4, 'MAXD_%s_DCB12'), (0x6A6BD4, 'MAXD_%s_ENTETE_ISM'), (0x6A6DD4, 'MAXD_%s_T88'),
            (0x6A6FD4, 'MAXD_%s_TC0'), (0x6AE814, 'MAXD_%s_T264'))          # actions 1, 2, 4, 5, 6
H_ANIMS = (0x6A7A94, 0x6A7C94, 0x6A7D54)          # actions 8-10 (normal, $F0 < 0, $123 = 2) : gabarit $2B8 à 144 entrées
H_SONS_PAS = 0x6AE614                              # action 25
H_PHYS = (((0x6A7E14, 0x6A8494), 8), ((0x6A8214,), 8), ((0x6A8354,), 8),               # marche : ism A, $132 > 0, $132 = $FF
          ((0x6A8614, 0x6ABA14), 64), ((0x6AA614,), 64), ((0x6AB014,), 64))           # sauts (actions 13-18)
CLES_PHYS = ("$DD492 (marche, $132=0)", "$DD592 (marche, $132 autre)", "$DD692 (marche, $132=$FF)",
             "$DD792 (saut, $132=0)", "$DDF92 (saut, $132 autre)", "$DE792 (saut, $132=$FF)")
H_PAL = 0x6452E0                                   # action 44 : palettes du corps, pointeurs (même format de bloc qu'Upper)
H_JAUGES = ((0x6AF5F0, 40), (0x6AF618, 72))        # actions 65, 66 (octets) : garde, étourdissement d'Eagle
H_PROJ = 0x6A73D4                                  # action 85 : positions de projection
H_FLAMMES = 0x6AE014                               # action 88 : ancrages des flammes
# tables de CODE relogées (étape B, ordre 68K) : table d'Upper (persos_max.json « rappels ») -> table d'Hyper (actions 28-40)
H_RAPPELS = {"748d98": 0x6A59D4, "748e38": 0x6A5BD4, "748ed8": 0x6A5DD4, "748f78": 0x6A5FD4, "749018": 0x6A61D4,
             "7490b8": 0x6A63D4, "7491f8": 0x6A67D4, "749298": 0x6A69D4, "749518": 0x6A71D4, "749658": 0x6A7494,
             "7496f8": 0x6A7694, "749798": 0x6A7894, "74c038": 0x6AD614}
H_T_PROJ = 0x5C3AA0                                # types de projectile (48, tous pris) -> MAX_T_PROJ (64), D10
H_T_EFFETS = 0x5B4300                              # classes du réservoir d'effets (40) -> MAX_T_EFFETS (64), action 42
# (actions 90-109, notes/S8 Q5, tables_max_greffe/TABLES.tsv colonne valeur_upper_max) tables d'Hyper de 40 entrées
# exactement indexées par la base : (table, taille d'entrée, valeur d'Hyper en [$26], valeur d'Upper MAX) ; les tables
# où Upper MAX garde la valeur neutre, ou sans équivalent dans Upper MAX (0x63AE94, 0x63B5CC, 0x63D7EC), ne bougent pas
H_VALEURS = {'26': ((0x5BD170, 2, 0x0000, 0x0048), (0x5C7110, 2, 0x005E, 0x0070), (0x5C7BD0, 2, 0x000B, 0x0000),
                    (0x63B61C, 1, 0x00, 0xFF), (0x63B644, 1, 0x00, 0x03))}
H_RECUL_TYPES = 0x5C2330                           # types de recul d'Hyper (35 types, 80 o) -> MAX_RECUL_TYPES (+ types 40-44)
CLASSES = {"26": {0x33: "psp_1b3904", 0x34: "psp_1b3c20"}}
RAPPELS = {"26": {"748d98": "psp_1b0b90", "748e38": "psp_1b18bc", "748ed8": "psp_1b18bc", "748f78": "psp_1b2f30",
                  "749018": "psp_1b2f30", "7490b8": "psp_1b0238", "7491f8": "psp_1b03cc", "749298": "psp_1b36f8",
                  "749658": "psp_1b1058", "7496f8": "psp_1b3614", "749798": "psp_1b35a8", "74c038": "psp_1b17f0",
                  "749518": "psp_1b3668"}}          # = persos_max.json d'Upper MAX (contrôlé : enveloppes MAXW_ présentes)

def donnees(buf, data, end, T, W, GRF_BLOB):
    """après data = bytearray(buf[end:FIN_FICHIER]), avant le relogement des pointeurs (étapes A, B, C). Pointeurs MAX
    = valeurs ÉTIQUETÉES $01 des symboles (T4 / T5) : CONV et RETAG24 les rendent telles quelles."""
    if MAX_SEL:   # ligne 0 de la table des transitions de l'écran de mode = identité (garde des directions : D0 = 0)
        assert buf[0x5C54C0 - RB:0x5C54C0 - RB + 8] == bytes(range(8)), 'T_5C54C0 : ligne 0 inattendue'
        assert buf[0x5C5326 - RB] == 0x26 and buf[0x5C5652 - RB] == 0x26, 'MAX_SEL : module sans les octets d\'Eagle'
    if not PERSOS:
        journal('donnees : rien à poser'); return
    def o(a):
        k = a - RB - end; assert 0 <= k < len(data), 'adresse %x hors des données d\'Hyper' % a
        return k
    def pose(t, i, b, e, aussi=None, attendu=None):
        """(A3) entrée i de la table t : la valeur d'avant doit être celle de Ryu (entrée 0 : copie de Ryu) ou nulle,
        sinon l'adresse de la table est fausse (une donnée d'un natif serait écrasée sans bruit)"""
        a = t + e * i; avant = bytes(data[o(a):o(a) + len(b)]); ryu = bytes(data[o(t):o(t) + len(b)])
        ok = (ryu, bytes(len(b))) + ((bytes(data[o(aussi):o(aussi) + len(b)]),) if aussi else ()) + ((attendu,) if attendu else ())
        assert avant in ok, 'table %x [$%x] : avant %s (attendu %s) : table inattendue' % (t, i, avant.hex(), ' / '.join(x.hex() for x in ok))
        data[o(a):o(a) + len(b)] = b; return avant
    CTX_D.update(lit=lambda a, n: bytes(data[o(a):o(a) + n]), o=o)
    p32 = lambda v: struct.pack('<I', v & 0xFFFFFFFF)
    phys = json.load(open(os.path.join(P['DIR'], 'src', 'physique_max_arcade.json'), encoding="utf-8"))
    # contrôle de place : Ryu ($00) des sauts d'Hyper = arcade
    assert struct.unpack_from('<4I', data, o(H_PHYS[3][0][0])) == (0, 0x72000, 0, 0xFFFFB000), 'table de sauts d\'Hyper inattendue'
    for p in PERSOS:
        i = int(p, 16); n = 0
        for t, lab in H_COMBAT: pose(t, i, p32(S(lab % p)), 4); n += 1
        for t in H_ANIMS: pose(t, i, p32(S('ANIM_%s_PTRS_H' % p)), 4, aussi=H_ANIMS[0]); n += 1   # [$26] des modes = Ryu normal
        pose(H_SONS_PAS, i, p32(S('SONS_PAS_%s' % p)), 4); n += 1
        for k, cle in enumerate(CLES_PHYS):
            v = [int(x, 16) for x in phys[cle][p]]; tabs, e = H_PHYS[k]; assert len(v) * 4 == e
            for t in tabs: pose(t, i, struct.pack('<%dI' % len(v), *v), e); n += 1
        pose(H_PAL, i, p32(S('MAXPAL_%s' % p)), 4); n += 1
        for t, v in H_JAUGES: pose(t, i, bytes([v]), 1); n += 1
        if 'PROJ_POS_%s' % p.upper() in P['SYM']: pose(H_PROJ, i, p32(S('PROJ_POS_%s' % p.upper())), 4); n += 1
        if 'FLAMMES_%s' % p.upper() in P['SYM']: pose(H_FLAMMES, i, p32(S('FLAMMES_%s' % p.upper())), 4); n += 1
        for t, e, av, v in H_VALEURS.get(p, ()):      # (actions 90-109, notes/S8 Q5) [$26] des tables d'Hyper de 40 entrées
            pose(t, i, v.to_bytes(e, 'little'), e, attendu=av.to_bytes(e, 'little')); n += 1
        if MAX_E5: n += habillage(p, i, pose)
        if MAX_CRIS and p in CRIS:                    # (pas 9) cris : base et base + 5 (ROM son MAX : roms_son_max_pas, paquet)
            pose(H_CRIS, i, struct.pack('<H', CRIS[p]), 2, attendu=struct.pack('<H', 0x0540))
            pose(H_CRIS5, i, struct.pack('<H', CRIS[p] + 5), 2, attendu=struct.pack('<H', 0x0545)); n += 2
        journal('Eagle ($%s) : %d écritures dans les tables d\'Hyper (combat, animations $2B8 x 144, sons des pas, marche et '
                'sauts, palettes, jauges, projections, flammes)' % (p, n))

# (pas 8) habillage par tables (emplacement 1, plan_commun_max) : tables du HUD d'Hyper (même disposition qu'Upper 0x95C700… : 40 entrées, rangée 1
# (US) à +80 o pour les noms et leurs x) et aperçu de sélection ; codes = $8000 + local (plan_commun_max)
H_HUD_NOM, H_HUD_XJ1, H_HUD_XJ2 = 0x6A1D40, 0x6A1DE0, 0x6A1E80
H_HUD_VIS = ((0x6A1F20, 'J1', 0), (0x6A2070, 'J2', None), (0x6A21C0, 'J1', -16), (0x6A2310, 'J2', 16))
H_APERCU = 0x5D43F0
H_NOMS = 0x697ED0
def habillage(p, i, pose):
    pose(H_APERCU, i, struct.pack('<I', S('APS_%s' % p)), 4)   # aperçu : emplacement 0 (f545 prolongée), sans talon
    HP = json.load(open(os.path.join(P['DIR'], 'max_plus.json'), encoding="utf-8"))
    N = HP['noms'][p]; VIS = HP['visages'][p]; n = 1
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import plan_commun_max as PC
    assert all(PC.P2_BASE - 0x1000 <= c < 0x10000 for c in [N['code']] + [v['code'] for v in VIS.values()]), 'max_plus.json : codes du HUD hors de la suite de plan2 (prep_max_ro9)'
    for r in (0, 1):                                  # JP, US : même nom ; valeurs d'Hyper en [$26] (mesurées) : $0020, -30, 30
        for t, v, av in ((H_HUD_NOM, N['code'], 0x0020), (H_HUD_XJ1, N['x_J1'], -30), (H_HUD_XJ2, N['x_J2'], 30)):
            pose(t + 80 * r, i, struct.pack('<H', v & 0xFFFF), 2, attendu=struct.pack('<H', av & 0xFFFF)); n += 1
    for t, jx, x in H_HUD_VIS:
        v = VIS[jx]; at = ((v['h'] - 1) << 12) | ((v['w'] - 1) << 8) | v['r']
        if x is None: x = 384 - 16 * v['w']
        elif jx == 'J2': x = 384 - 16 * v['w'] + x
        pose(t, i, struct.pack('<HHhh', v['code'], at, x, 16), 8); n += 1
    n += portraits(p, i, pose)
    # nom de la sélection / du VS (cartouche, frame $0C MAXNOM_<id>) : listes +$40 et +$180 de la structure des noms
    # 0x697ED0 (= Upper 0x961B30 / 0x961C70 ; lignes de 8 o, pointeur à +4) ; bandeaux, WINNER, carte : plus tard
    for t in (H_NOMS + 0x40, H_NOMS + 0x180): pose(t + 4, i, struct.pack('<I', S('MAXNOM_%s' % p)), 8); n += 1
    journal('habillage $%s (tables, emplacement 1) : nom du HUD $%x, visages $%x / $%x, aperçu APS_%s, portraits, nom' % (p, N['code'], VIS['J1']['code'], VIS['J2']['code'], p))
    return n

# portraits (sélection, VS, victoire) : modèle integre_max.portraits() d'Upper MAX (frames de type $08 + bloc de 48 palettes
# = 6 couleurs × 8), tables d'Hyper : poses 0x62EBA0 (66 décalages u16, lignes de 8 o par perso, pointeur de frame à +4 ;
# même structure qu'Upper 0x674C00), palettes 0x67E1E0 (pointeur par perso, blocs de $600 o comme Upper 0x72BDF0, relevé
# par le contenu du bloc de Ryu). Codes des frames : emplacement 1 (plan_commun_max.code : P2_BASE + g - G0 - $1000). Bloc posé à
# la fin des données MAX (T4). Poses >= 32 (bande partagée : yeux du VS / de la victoire) : non posées en L2 (relevé).
H_POSES, H_PAL_PORTRAITS = 0x62EBA0, 0x67E1E0
def portraits(p, i, pose):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import plan_commun_max as PC
    import array
    lit, o = CTX_D['lit'], CTX_D['o']
    FORK = os.environ['MAX_CACHE']; CV = os.path.join(os.path.dirname(FORK.rstrip('/')), 'converti', 'pl%s' % p) + '/'
    G0 = 0x4DAAB + os.path.getsize(os.path.join(FORK, 'max_gfx.bin')) // 128
    pj = json.load(open(CV + 'portraits.json', encoding="utf-8"))
    hx = array.array('I', open(os.path.join(FORK, 'p%s_portraits_hx.bin' % p), 'rb').read())
    offs = struct.unpack('<66H', lit(H_POSES, 132))
    pal0 = struct.unpack('<I', lit(H_PAL_PORTRAITS, 4))[0]
    blk = bytearray(lit(pal0, 0x600)); src = open(CV + 'portraits_palettes.bin', 'rb').read()
    var_ = pj.get('128x224', {}).get('variantes', {}); mp_ = var_.get('palette_du_fichier_vers_r')
    rdir = bool(mp_) and 'direct' in var_.get('attributs', ''); dec_ = 0
    if rdir:
        n_ = len(mp_); f0_ = min(int(f) for f in mp_); s2 = bytearray(len(src))
        for f_, r_ in mp_.items(): s2[32*r_:32*r_+32] = src[32*int(f_):32*int(f_)+32]
        for k_ in range(f0_): s2[32*(n_+k_):32*(n_+k_)+32] = src[32*k_:32*k_+32]
        src = bytes(s2); dec_ = n_
    blk[:len(src)] = src
    vic_ = CV + 'portraits_victoire_variantes.bin'; var2_ = CV + 'portraits_palettes_variantes.bin'
    if os.path.exists(vic_) and os.path.exists(var2_) and mp_:
        vb_ = open(vic_, 'rb').read(); sb_ = open(var2_, 'rb').read(); kk = len(vb_) // 32 // 6
        assert kk in (4, 8) and len(vb_) == 32 * 6 * kk
        P_ = lambda d, n: d[32 * n:32 * n + 32]
        for v_ in range(6):
            g = 0x100 * v_
            if rdir:
                for f_, r_ in mp_.items(): blk[g + 32 * r_:g + 32 * r_ + 32] = P_(sb_, 4 * v_ + r_)
                for r_ in range(min(int(f) for f in mp_)): blk[g + 32 * (dec_ + r_):g + 32 * (dec_ + r_) + 32] = P_(vb_, kk * v_ + r_)
            else:
                for r_ in range(kk): blk[g + 32 * r_:g + 32 * r_ + 32] = P_(vb_, kk * v_ + r_)
                for f_, r_ in mp_.items(): blk[g + 32 * int(f_):g + 32 * int(f_) + 32] = P_(sb_, 4 * v_ + r_)
    # bloc à la fin des données MAX (T4), aligné sur 16
    B = P['BLOB']; B += bytes((-len(B)) % 16); PB = P['ORG'] + len(B); n = 0; bande = 0; deja = {}
    for fam, x in pj.items():
        a = PB + len(blk); objs = x['objs']; d_ = dec_ if fam == '320x160' else 0
        blk += struct.pack('<HHH', 8, x['T'], len(objs) - 1)
        for L, at, xx, yy in objs:
            if d_: assert (at & 0x1f) + d_ < 0x20; at += d_
            blk += struct.pack('<HHhh', PC.code(int(hx[L]), G0), at & 0xffff, xx, yy)
        for po in x['poses']:
            t_ = po['table_0x484C00']; assert t_['id'] == i, 'portraits : poses de l\'ID %x' % t_['id']
            if offs[t_['pose']] >= 0x1704: bande += 1; continue
            dej = deja.get(offs[t_['pose']])          # poses qui partagent une ligne (décalages égaux) : la dernière gagne, comme Upper
            pose(H_POSES + offs[t_['pose']] + 4, i, struct.pack('<I', a), 8, attendu=dej); n += 1
            deja[offs[t_['pose']]] = struct.pack('<I', a)
        blk += bytes(len(blk) & 1)
    pose(H_PAL_PORTRAITS, i, struct.pack('<I', PB), 4, attendu=struct.pack('<I', 0x68B5E0)); n += 1   # [$26] d'Hyper (mesuré) : un bloc à lui
    # palettes de SÉLECTION / VS (lues par 0x6774E0 + décalage[id] + couleur × 128 : 4 palettes par couleur ; [$26] d'Hyper
    # = bloc de Ryu) : bloc propre de 6 × 128 o, comme Upper MAX (SELPAL) : palettes 0-3 du fichier, celles de la sélection
    # (variantes, 4 v + r) aux emplacements visés par les attributs ; lecteur dévié par le talon E (fin())
    while len(blk) & 0x1f: blk += b"\0"
    SELPAL[p] = PB + len(blk)
    vf_ = CV + 'portraits_palettes_variantes.bin'; cible_ = lambda f_, r_: r_ if rdir else int(f_)
    assert os.path.exists(vf_) and mp_ and all(cible_(f, r) < 4 for f, r in mp_.items()), 'palettes de sélection : variantes absentes'
    vv_ = open(vf_, 'rb').read()
    for v_ in range(6):
        q_ = bytearray(src[:0x80])
        for f_, r_ in mp_.items(): q_[32*cible_(f_, r_):32*cible_(f_, r_)+32] = vv_[32*(4*v_+r_):32*(4*v_+r_)+32]
        blk += q_
    blk += bytes((-len(blk)) % 4)
    B += bytes(blk[j ^ 1] for j in range(len(blk)))          # ordre de l'image (mots échangés), comme les blocs d'Upper MAX
    assert (P['ORG'] & 0xFFFFFF) + len(B) <= 0x800000, 'T4 pleine (portraits)'
    journal('portraits $%s : %d poses + palettes, %d poses >= 32 non posées, bloc $%x (%d o, codes : emplacement 1)' % (p, n - 1, bande, PB, len(blk)))
    return n

def _code68(data, T, a):
    """case d'une table de code relogée (étape B, ordre 68K) -> adresse 68K"""
    hi, lo = struct.unpack_from('<HH', data, a - T.CODE_END_RT); return (hi << 16) | lo

def _pose68(data, T, a, v):
    struct.pack_into('<HH', data, a - T.CODE_END_RT, (v >> 16) & 0xFFFF, v & 0xFFFF)

def tables_code(data, T):
    """après l'étape B (cases des T.RELOGE_TABLES en adresses 68K), avant data = bytes(data)"""
    if not PERSOS:
        journal('tables_code : %d tables relogées connues' % len(T.RELOGE_TABLES)); return
    tab = dict(T.RELOGE_TABLES)
    for t in list(H_RAPPELS.values()) + [H_T_PROJ, H_T_EFFETS]:
        assert t in tab and t in T.RELOGE_NATIF_TABLES, 'table de code %x non relogée (ordre 68K)' % t
    for p in PERSOS:
        i = int(p, 16)
        for u, r in RAPPELS[p].items():
            t = H_RAPPELS[u]; assert tab[t] >= t + 4 * (i + 1); _pose68(data, T, t + 4 * i, S('MAXW_%s_%s' % (p, u)))
        journal('Eagle ($%s) : %d rappels -> enveloppes MAXW (tables de code d\'Hyper)' % (p, len(RAPPELS[p])))
    # types de projectile : 48 cases d'Hyper + 16 ; case du type d'Eagle ($30) = son gestionnaire, les autres = case 0
    assert tab[H_T_PROJ] == H_T_PROJ + 4 * 48
    tp = [_code68(data, T, H_T_PROJ + 4 * k) for k in range(48)]; tp += [tp[0]] * 16
    ty = S('TYPE_PROJ_EAGLE'); assert 48 <= ty < 64, 'TYPE_PROJ_EAGLE = $%x (D10 : $30)' % ty
    tp[ty] = S('TIR_W_26') if 'TIR_W_26' in P['SYM'] else S('psp_fils_26')
    struct.pack_into('>64I', P['BLOB'], S('MAX_T_PROJ') - P['ORG'], *tp)
    # classes d'effets : 40 d'Hyper + classes MAX
    assert tab[H_T_EFFETS] == H_T_EFFETS + 160
    ef = [_code68(data, T, H_T_EFFETS + 4 * k) for k in range(40)] + [0] * 24
    for p in PERSOS:
        for c, r in CLASSES[p].items():
            assert ef[c] == 0; ef[c] = S('EFFET_W_%02X' % c) if 'EFFET_W_%02X' % c in P['SYM'] else S(r)
    struct.pack_into('>64I', P['BLOB'], S('MAX_T_EFFETS') - P['ORG'], *ef)
    journal('types de projectile -> MAX_T_PROJ ($%x, type $%x) ; classes d\'effets -> MAX_T_EFFETS ($%x, %s)' % (
        S('MAX_T_PROJ'), ty, S('MAX_T_EFFETS'), ', '.join('$%02X' % c for p in PERSOS for c in CLASSES[p])))

def palettes(data, end):
    pass                                             # Hyper : table des palettes par pointeurs, rien à déplacer (action 44)

def carte_md5(lignes):
    """empreinte des positions de la carte (« adresse va » par ligne), sans le texte des instructions (= prepare_max)"""
    return hashlib.md5(''.join(' '.join(l_.split(None, 2)[:2]) + '\n' for l_ in lignes).encode()).hexdigest()

def lea_abs(img, ancien, nouveau, attendu, nom):
    """tous les LEA abs.L,An de l'adresse ancien -> nouveau ; nombre de sites contrôlé (modèle : integre_max.image)"""
    n = 0
    for reg in range(8):
        pat = struct.pack('>HI', 0x41F9 | (reg << 9), ancien); k = img.find(pat)
        while 0 <= k < ZONE_CODE[0]:
            if k % 2 == 0: struct.pack_into('>I', img, k + 2, nouveau); n += 1
            k = img.find(pat, k + 2)
    assert n == attendu, '%s : LEA $%x : %d sites (%d attendus)' % (nom, ancien, n, attendu)
    journal('%s : LEA $%x -> $%x (%d sites)' % (nom, ancien, nouveau, n))

def image(img, its, T, W, EXT_PLUS, carte_lignes, code_fin):
    """après la pose des données dans l'image, avant les talons natifs. Les POSITIONS de la carte (adresse d'image, va)
    doivent être celles de la base MAX (celle de la préparation, ou MAX_CARTE_MD5) : le code MAX appelle le code traduit
    par adresses d'image. Le texte des instructions n'entre pas dans l'empreinte."""
    md5 = carte_md5(carte_lignes)
    journal('carte %s (%d lignes), fin du code $%x' % (md5, len(carte_lignes), code_fin))
    ref = P['J']['carte_md5'] if PERSOS else os.environ.get('MAX_CARTE_MD5')
    if ref: assert md5 == ref, 'carte %s différente de la base MAX %s : le code traduit a bougé' % (md5, ref)
    CTX[0] = (its, T, W)
    if MAX_SEL: sites_selection(img)
    if not PERSOS: return
    lea_abs(img, T.addr_to_68k(H_T_PROJ) & 0xFFFFFF, S('MAX_T_PROJ'), 2, 'types de projectile')
    lea_abs(img, T.addr_to_68k(H_T_EFFETS) & 0xFFFFFF, S('MAX_T_EFFETS'), 1, 'classes d\'effets')
    # (A2) reculs MAX : table des types = copie de celle d'Hyper (contrôlée à l'octet sur 80 o) + types 40-44
    a_rt = T.addr_to_68k(H_RECUL_TYPES) & 0xFFFFFF; o_ = S('MAX_RECUL_TYPES') - P['ORG']
    assert bytes(P['BLOB'][o_:o_ + 80]) == bytes(img[a_rt:a_rt + 80]), 'MAX_RECUL_TYPES : 80 premiers octets différents de 0x5C2330'
    lea_abs(img, a_rt, S('MAX_RECUL_TYPES'), 1, 'types de recul')
    recul_tables(img, T)
    sites_prises(img)
    if MAX_E5: sites_habillage(img)
    for org, b in ((P['ORG'], P['BLOB']), (P['T5'], P['BLOC'])):
        open(os.path.join(W, 'ext_%06x.bin' % (org & 0xFFFFFF)), 'wb').write(bytes(b)); EXT_PLUS.append('%06x' % (org & 0xFFFFFF))
    journal('blocs MAX : données $%x (%d o), Eagle $%x (%d o)' % (P['ORG'] & 0xFFFFFF, len(P['BLOB']), P['T5'] & 0xFFFFFF, len(P['BLOC'])))

def fin(img):
    """tout à la fin, avant l'échange d'octets et l'écriture des 8 ROM : code MAX puis talons, dans ZONE_CODE"""
    assert not any(img[ZONE_CODE[0]:ZONE_CODE[1]]), 'zone du code MAX non vide à l\'entrée de fin()'
    z = Zone(img, *ZONE_CODE)
    if PERSOS:
        c = P['CODE']; img[ZONE_CODE[0]:ZONE_CODE[0] + len(c)] = c; z.a = ZONE_CODE[0] + len(c)
        journal('code MAX : %d o en $%x-$%x' % (len(c), ZONE_CODE[0], ZONE_CODE[0] + len(c)))
    if PERSOS: talon_prises(img, z)
    if PERSOS and MAX_E5: talons_habillage(img, z)
    if MAX_SEL: talons_selection(img, z)
    journal('fin : zone $%x-$%x %s' % (ZONE_CODE[0], ZONE_CODE[1] - 1, 'vide' if not any(img[ZONE_CODE[0]:ZONE_CODE[1]]) else 'occupée'))
    open(os.path.join(W_[0], 'max_journal.txt'), 'w', encoding="utf-8").write('\n'.join(JOURNAL) + '\n')

# ------------------------------------------------------------------------------------------------------------------
# outils (modele : integre_max.py d'Upper MAX, _va_image / _sites / _recoupe) : aucune adresse d'image en dur ; un site
# est trouve par la va MIPS (fichier) de sa premiere instruction (carte de la construction), puis ses octets sont controles.

class Zone:
    """place libre (octets nuls) de [lo, hi) dans l'image, prise dans l'ordre ; generalisable a d'autres zones de code
    68K (decors : $380000) : Zone(img, lo, hi).prend(octets) rend l'adresse posee"""
    def __init__(self, img, lo, hi): self.img, self.a, self.hi = img, lo, hi
    def prend(self, mots, nom):
        b = struct.pack('>%dH' % len(mots), *mots)
        a = (self.a + 1) & ~1
        assert a + len(b) <= self.hi and not any(self.img[a:a + len(b)]), '%s : zone $%x-$%x pleine' % (nom, a, self.hi)
        self.img[a:a + len(b)] = b; self.a = a + len(b)
        journal('talon %s : %d octets en $%x' % (nom, len(b), a))
        return a

def recul_tables(img, T):
    """(A2 ; revue finale : méthode d'Upper MAX, REL16_N) séquences de recul par TABLES : les deux tables rel16 d'Hyper
    (0x66A260 et sa variante 0x66A5AE, 64 entrées : 32 + 32 pour $329 > 0) et leurs séquences sont RECOPIÉES dans le bloc
    MAX (octets d'image tels quels, même parité), prolongées de 5 entrées (n° 64-68 = séquences MAX RECUL_S25-S29) ; les
    2 LEA du lecteur sont redirigés (même instruction, même coût : aucun talon sur le chemin des natifs)."""
    H = (0x66A260, 0x66A5AE); N = 64; B = P['BLOB']
    bases = [T.addr_to_68k(h) & 0xFFFFFF for h in H]
    offs = [[struct.unpack_from('>h', img, b_ + 2 * k)[0] for k in range(N)] for b_ in bases]
    def fin(x):                                       # fin d'une séquence (octet logique n = img[(x + n) ^ 1], terminée par < 0)
        n = 0
        while img[(x + n) ^ 1] < 0x80: n += 1
        return x + n + 1
    cibles = [b_ + o for b_, os_ in zip(bases, offs) for o in os_]
    lo = min(cibles + bases) & ~1; hi = (max(fin(c) for c in cibles) + 1) & ~1
    assert hi - lo < 0x4000, 'recul : plage de %x octets' % (hi - lo)
    B += bytes(len(B) & 1); dest = len(B); B += img[lo:hi]
    nouv = lambda x: dest + (x - lo)                  # décalage dans le bloc d'une adresse d'image copiée
    # séquences MAX : recopiées à la suite (la table rel16 doit les atteindre en 16 bits)
    sq = []
    for k in range(25, 30):
        o = S('RECUL_S%d' % k) - P['ORG']; m = 0
        while B[(o + m) ^ 1] < 0x80: m += 1
        B += bytes(len(B) & 1); sq.append(len(B)); B += bytes(B[o:o + ((m + 2) & ~1)])
    nt = []
    for b_, os_ in zip(bases, offs):
        B += bytes(len(B) & 1); t = len(B); nt.append(t)
        for k in range(N): B += struct.pack('>h', nouv(b_ + os_[k]) - t)
        for q in sq: B += struct.pack('>h', q - t)
    for t, b_, os_ in zip(nt, bases, offs):            # contrôle : chaque séquence native lue par la copie = l'originale
        for k in range(N):
            x = b_ + os_[k]; y = t + struct.unpack_from('>h', B, t + 2 * k)[0]
            assert all(img[(x + j) ^ 1] == B[(y + j) ^ 1] for j in range(fin(x) - x)), 'recul : séquence %d de %x' % (k, b_)
    for b_, t, h in zip(bases, nt, H):
        lea_abs(img, b_, P['ORG'] + t, 1, 'séquences de recul 0x%X' % h)
    journal('recul : tables rel16 0x%X / 0x%X et séquences ($%x o) recopiées dans le bloc MAX, + 5 séquences MAX (n° 64-68)' % (H[0], H[1], hi - lo))

# (pas 8) palettes de SÉLECTION / VS : comme Upper MAX (talon_selpal), un seul talon, au lecteur de 0x6774E0 (écrans de
# sélection et de VS, jamais dans la boucle de combat ; natifs : mesurés à l'octet) : id MAX ($26-$2F, D0 = 2 × id) dont une
# entrée de SELPAL_TAB est posée -> bloc propre ; sinon chemin d'origine. Sert tel quel à Maki, Yun, Ingrid (table par id).
VA_SELPAL = 0x31FA64       # LEA T_6774E0,A0 ; ADD.W 0(A0,D0.W),D1 ; ADDA.W D1,A0 (D0 = 2 × id, D1 = couleur × 128)
def talon_e(nat, tab):
    w = [0x0C40, 0x004C, 0x6522, 0x0C40, 0x0060, 0x641C,              # cmpi.w #2*$26,d0 ; bcs nat ; cmpi.w #2*$30,d0 ; bcc nat
         0x2F00, 0x0440, 0x004C, 0xD040, 0x41FA, 0x0020,              # move.l d0,-(sp) ; subi.w #$4C,d0 ; add.w d0,d0 ; lea TAB(pc),a0
         0x2070, 0x0000, 0x201F, 0xB0FC, 0x0000, 0x6704, 0xD0C1, 0x4E75,   # movea.l 0(a0,d0.w),a0 ; move.l (sp)+,d0 ; cmpa.w #0,a0 ; beq nat ; adda.w d1,a0 ; rts
         0x41F9, nat >> 16, nat & 0xFFFF, 0xD270, 0x0000, 0xD0C1, 0x4E75]  # nat : lea T_6774E0,a0 ; add.w 0(a0,d0.w),d1 ; adda.w d1,a0 ; rts
    assert len(w) * 2 == 54
    for k in range(10): v = tab.get('%02x' % (0x26 + k), 0); w += [v >> 16, v & 0xFFFF]   # TAB : 10 longs, ids $26-$2F
    return w
def sites_habillage(img):
    k = site_va(img, VA_SELPAL, '41f9', 'habillage E (palettes de sélection)')
    assert img[k + 6:k + 12] == bytes.fromhex('d2700000d0c1'), 'habillage E : suite « ADD.W 0(A0,D0.W),D1 ; ADDA.W D1,A0 » attendue en $%x' % (k + 6)
    SITES['selpal'] = k

def talons_habillage(img, z):
    k = SITES['selpal']; nat = struct.unpack_from('>I', img, k + 2)[0]
    t = z.prend(talon_e(nat, SELPAL), 'habillage E (palettes de sélection)'); jsr(img, k, t, 12)
    journal('palettes de sélection : ids %s' % ', '.join('$' + p for p in sorted(SELPAL)))

# (méthode d'Upper MAX : integre_max.talon_prises, note LECONS_UPPER_MAX §2) masques de prise par id : ids < $20 = masque
# de 32 bits, ids $20-$3F = « ADDI.B #$E0,D3 ; MOVEQ #m,D0 ; BSR lecteur (BTST.L D3,D0) » ; les MOVEQ d'Hyper (sol KK #$17,
# air PP #$29, air KK #$17, = bits 32-37 des masques PSP, vérifié) n'ont pas les ids MAX : prise avant + KK d'Eagle jamais
# reconnue (banc : E26h). L'immédiat du MOVEQ devient m' = m | bits des MAX lus dans les masques PSP de 48 bits de l'EBOOT
# (0x213F68 / 7A / 80, bit [id PSP]), sur place (Upper MAX : talon ; ici, tant que m' < $80, aucun talon). Sites d'Hyper par va MIPS (fichier) : homologues d'Upper 0x240E38 / 0x24146C / 0x241594. MAX_PRISES=0 : sans.
MAX_PRISES = os.environ.get('MAX_PRISES', '1') == '1'
VA_PRISES = ((0x2C1B3C, '060300e070176102', 0x213F68, 'sol KK'), (0x2C216C, '060300e070296188', 0x213F7A, 'air PP'),
             (0x2C2294, '060300e070176100ff6c', 0x213F80, 'air KK'))
ID_PSP = {'26': 0x26}
def sites_prises(img):
    if not (PERSOS and MAX_PRISES): return
    L = []
    for va, att, psp, nom in VA_PRISES:
        k = site_va(img, va, att, 'prises : ' + nom); b = k + 6        # BSR.B / BSR.W en k + 6
        d = img[b + 1]; lec = b + 2 + ((d - 256 if d & 0x80 else d) if d else struct.unpack_from('>h', img, b + 2)[0])
        L.append((k, len(att) // 2, lec, psp, nom))
    assert len({x[2] for x in L}) == 1 and img[L[0][2]:L[0][2] + 2] == bytes.fromhex('0700'), 'prises : lecteurs %s' % [hex(x[2]) for x in L]
    SITES['prises'] = L

def talon_prises(img, z):
    if not (PERSOS and MAX_PRISES): return
    f = os.environ.get('MAX_EBOOT') or os.path.join(os.path.dirname(os.path.dirname(os.environ['MAX_CACHE'].rstrip('/'))), 'psp', 'BOOT.BIN')
    eb = open(f, 'rb').read()[0x74:]
    for k, n, lec, psp, nom in SITES['prises']:
        m0 = img[k + 5]; m48 = int.from_bytes(eb[psp:psp + 6], 'little')
        assert (m48 >> 32) & 0x3F == m0, 'prises : %s : MOVEQ #$%x d\'Hyper != bits 32-37 du masque PSP ($%x)' % (nom, m0, (m48 >> 32) & 0x3F)
        aj = 0
        for p in PERSOS:
            if (m48 >> ID_PSP[p]) & 1: aj |= 1 << (int(p, 16) - 0x20)
        m1 = m0 | aj
        if m1 == m0: journal('prises : %s : #$%x, aucun MAX ne l\'a sur PSP : site laissé' % (nom, m0)); continue
        # (revue finale V4) MOVEQ réécrit SUR PLACE : aucun talon, aucun cycle de plus pour les natifs ; un masque qui ne
        # tient plus dans un MOVEQ positif (bit 7 et plus : Maki, Yun, Ingrid) demandera un talon à coût égal (L4)
        assert m1 < 0x80, 'prises : %s : masque #$%x hors d\'un MOVEQ positif (L4 : talon à coût égal à concevoir)' % (nom, m1)
        assert img[k + 4] == 0x70, 'prises : MOVEQ attendu en $%x' % (k + 4)
        img[k + 5] = m1
        journal('prises : %s : MOVEQ #$%x -> #$%x sur place en $%x (lecteur $%x)' % (nom, m0, m1, k + 4, lec))

def _va_image():
    d = {}
    for it in CTX[0][0]:
        if (it.ws or it.kind != 'fixed') and it.off not in d: d[it.off] = it.va
    return d

def site_va(img, va, attendu, nom):
    """adresse d'image unique de la va MIPS va (premiere instruction ecrite), octets controles (hexa)"""
    r = sorted(a for a, v in _va_image().items() if v == va)
    assert r and r[-1] - r[0] < 16, '%s : va %x absente de la carte ou en plusieurs endroits (%s)' % (nom, va, ' '.join('$%x' % x for x in r))
    a = r[0]; b = bytes.fromhex(attendu)
    assert img[a:a + len(b)] == b, '%s : $%x vaut %s, attendu %s' % (nom, a, img[a:a + len(b)].hex(), b.hex())
    return a

def jsr(img, a, cible, n):
    """remplace n octets en a par JSR cible.L puis des NOP"""
    assert n >= 6 and n % 2 == 0
    struct.pack_into('>HHH', img, a, 0x4EB9, cible >> 16, cible & 0xFFFF)
    for k in range(a + 6, a + n, 2): struct.pack_into('>H', img, k, 0x4E71)

# ------------------------------------------------------------------------------------------------------------------
# SELECTION (MAX_SEL, CONCEPTION §3.1-§3.2 ; octets du module : greffe3.py MAX_SEL). Va MIPS (fichier = exec - $1F0000) :
VA_SEUIL_HYPER = 0x319CF4     # CMPI.B #$26,D0 ; BLT  (selection d'Hyper : VERSUS, ARCADE initiale, TRAINING...)
VA_SEUIL_GREFFE = 0xEC3D94    # meme suite dans la copie greffee (selection Arcade d'Upper)
VA_MODE_DIR = 0x31BB50        # ecran de mode : MOVE.B $5C(A6),D1 ; EXT.W D1 (directions)
VA_MODE_VALIDE = 0x31BE4C     # ecran de mode : ADDQ.B #2,$4(A6) ; BSET #3,$3D(A6) (validation, minuterie, copie de l'autre joueur)
BASE_MAX = 0x26               # premiere base MAX ($117(A6) = perso de base ; ids d'Hyper < $26, versions anciennes : base < $26)

def sites_selection(img):
    SITES['seuil_h'] = site_va(img, VA_SEUIL_HYPER, '0c0000266d', 'seuil (Hyper)')
    SITES['seuil_g'] = site_va(img, VA_SEUIL_GREFFE, '0c0000266d', 'seuil (copie greffee)')
    SITES['mode_dir'] = site_va(img, VA_MODE_DIR, '122e005c4881', 'mode : directions')
    SITES['mode_val'] = site_va(img, VA_MODE_VALIDE, '542e000408ee0003003d', 'mode : validation')
    journal('selection : seuils $%x / $%x, mode $%x / $%x' % (SITES['seuil_h'], SITES['seuil_g'], SITES['mode_dir'], SITES['mode_val']))

def talons_selection(img, z):
    # 1. seuil des « ? » : $2A (D3) ; ARCADE : $26 au site d'Hyper (D5 = b), site greffe inchange
    k = SITES['seuil_h']; d8 = img[k + 5]; assert d8 not in (0, 0xFF), 'seuil : BLT.S attendu en $%x' % (k + 4)
    d8 -= 0x100 if d8 & 0x80 else 0
    blt = k + 4 + 2 + d8                                  # cible du BLT (case < seuil : perso)
    if SEUIL_ARCADE:
        t = z.prend([0x4A2D, 0xC201,                      # TST.B $C201(A5)         (mode du menu d'Hyper : 0 = ARCADE)
                     0x6606,                              # BNE.S +6
                     0x0C00, 0x0026,                      # CMPI.B #$26,D0          ARCADE : la case d'Eagle reste un « ? »
                     0x6004,                              # BRA.S +4
                     0x0C00, 0x002A,                      # CMPI.B #$2A,D0          autres modes : seuil $2A
                     0x6D02,                              # BLT.S +2
                     0x4E75,                              # RTS                     (suite d'origine apres le BLT)
                     0x588F,                              # ADDQ.L #4,SP
                     0x4EF9, blt >> 16, blt & 0xFFFF], 'seuil')   # JMP cible du BLT
        jsr(img, k, t, 6)
        journal('seuil : site d\'Hyper $%x -> talon $%x ($26 en ARCADE, $2A sinon ; BLT -> $%x) ; site greffe $%x garde $26'
                % (k, t, blt, SITES['seuil_g']))
    else:
        for c in ('seuil_h', 'seuil_g'): img[SITES[c] + 3] = 0x2A
        journal('seuil : $2A aux deux sites')
    # 2. ecran de mode : base MAX -> directions ignorees (curseur sur « normal ») ; ligne 0 de T_5C54C0 = identite
    t = z.prend([0x122E, 0x005C,                          # MOVE.B $5C(A6),D1       (instructions remplacees)
                 0x4881,                                  # EXT.W D1
                 0x0C2E, BASE_MAX, 0x0117,                # CMPI.B #$26,$117(A6)
                 0x6502,                                  # BCS.S +2                natif : directions gardees
                 0x4240,                                  # CLR.W D0                MAX : aucune direction
                 0x4E75], 'mode (directions)')            # RTS
    jsr(img, SITES['mode_dir'], t, 6)
    # 3. validation de l'ecran de mode (manette, minuterie, copie du mode de l'autre joueur) : base MAX -> $5C = 0 (normal)
    t = z.prend([0x0C2E, BASE_MAX, 0x0117,                # CMPI.B #$26,$117(A6)
                 0x6504,                                  # BCS.S +4
                 0x422E, 0x005C,                          # CLR.B $5C(A6)
                 0x542E, 0x0004,                          # ADDQ.B #2,$4(A6)        (instructions remplacees)
                 0x08EE, 0x0003, 0x003D,                  # BSET #3,$3D(A6)
                 0x4E75], 'mode (validation)')            # RTS
    jsr(img, SITES['mode_val'], t, 10)
    journal('mode : base >= $%x -> mode normal seul (directions $%x, validation $%x)' % (BASE_MAX, SITES['mode_dir'], SITES['mode_val']))
