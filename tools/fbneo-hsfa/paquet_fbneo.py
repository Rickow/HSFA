#!/usr/bin/env python3
"""Construit les archives de jeu du coeur FBNeo HSFA (pilotes sfa3hsfa, sfa3uhsfa et sfa3hhsfa) a partir du dossier de
travail. Entree upper_max (sur demande, pas dans la liste par defaut) : Upper + persos MAX, pilote sfa3umhsfa (patch
0013) ; MAX_BANC=<banc MAX relatif a HSFA_WORK> (obligatoire), MAX_SON (ROM son, defaut agent_son_max/roms_son_max_ko),
SFA3MAX_CACHE (defaut : <banc>/sfa3max_cache.txt), HSFA_MAX_CACHE_DIR (dossier de max_cache.py, defaut
scripts/untranspile du depot).

Reproduit le banc MAME du projet :
  - ROM programme traduite (8 x 512 Ko, mots echanges) : roms_tr/sfa3ud (SFA3), mame_ro5/roms_ro5/sfa3ud (Upper),
    mame_ro9/roms_ro9/sfa3ud (Hyper) ;
  - hsfa_ext.bin  : image de $A00000-$EFFFFF (5 Mo ; Hyper : $940000-$EFFFFF, 5,75 Mo) avec les blocs ext_<adresse>.bin
                    que sert banc_mem.lua (bases fixes + ext_liste.txt du dossier du module), mots echanges comme la ROM
                    programme ; la fin est fixe ($F00000) : le pilote deduit la base de la taille du fichier ;
  - hsfa_tab.bin  : tables de banc_sprites.lua / banc_plans.lua (f<N>.bin, plan1, plan2, f312, carte.txt)
                    + parametres (banque commune, pointeur d'animation, fichier de l'intro, bases des plans) ;
  - hsfa_gfx.bin  : (Upper, Hyper) region graphique $2000000-$3FFFFFF au format interne MAME : hsfa_gfx.bin en +0,
                    hsfa_plans.bin en +$1000000 (= HSFA_GFX=...hsfa_gfx.bin,...hsfa_plans.bin@3000000) ;
  - son : ROM d'origine de SFA3 (sfa3hsfa) ou ROM hybride d'Upper hx3.* (sfa3uhsfa et sfa3hhsfa, QSound 16 Mo ;
    les musiques d'Hyper sont jouees par le lecteur de flux ADX du coeur, depuis le Y_DATA.BIN de l'utilisateur) ;
  - ROM graphique sz3.13m-20m et cle phoenix.key de sfa3ud.
Les archives (donnees de jeu) restent dans le dossier de sortie, jamais dans un depot.

Membres lus sur place par le coeur (absents de la liste de ROM du pilote, donc jamais charges en memoire par FBNeo),
STOCKES sans compression, fabriques a partir des fichiers de l'utilisateur ; sans ces fichiers, l'archive est construite
sans eux (le coeur cherche alors Y_DATA.BIN / X_DATA.BIN / l'ISO dans <systeme>/fbneo/hsfa/, sinon musique QSound et
sons SFA3) :
  - hsfa_flux.bin        (Upper, Hyper) AFS reduit : memes indices que Y_DATA.BIN, seuls les flux ADX que le jeu peut
                         demander y sont copies (Hyper : codes de codes_musique_hyper.txt, ~695 Mo ; Upper : persos
                         d'Upper 0030-0036, ~22 Mo), les autres entrees sont vides ;
  - hsfa_flux_table.txt  table code -> flux (agent_flux/hsfa_flux_table.txt) ;
  - hsfa_rejeu.bin       (Hyper) ROM du 2e QSound du rejeu, 8 Mo : entrees e222 (SFA1, banque 0) et e251 (SFA2, banque
                         $40) de X_DATA.BIN, CRC controles d'apres les lignes SOURCE de la table ;
  - hsfa_rejeu_table.txt (Hyper) table du rejeu (agent_son_hyper_rom/rejeu/hsfa_rejeu_table.txt).

Usage : python3 paquet_fbneo.py [sfa3|upper|hyper|ro9a ...]   (defaut : les trois premiers ; ro9a = essai de la greffe)
Variables : HSFA_WORK (dossier work, defaut : dossier parent de ce script), HSFA_SORTIE (defaut : dossier du script).
  HSFA_YDATA : Y_DATA.BIN ou ISO de l'Anthology (flux ADX) ; HSFA_XDATA : X_DATA.BIN ou ISO (rejeu ; defaut :
      HSFA_YDATA si c'est l'ISO, sinon <work>/xdata/X_DATA.BIN s'il existe). Sans source : membres absents.
  HSFA_VOIX_ARCADE=0 : garder les voix « par pas » telles que traduites (defaut : son-hyper/corrige_voix.py,
      voix_arcade.tsv, mesures du 2026-10-16).
  HSFA_CRIS_ARCADE=0 : garder les cris du rejeu tels quels (defaut : cris de degats et K.O. de l'arcade, son-hyper/
      corrige_cris.py, mesures du 2026-10-16).
  HSFA_FLUX_TABLE, HSFA_REJEU_TABLE, HSFA_CODES_HYPER : tables (defauts : agent_flux/, agent_son_hyper_rom/rejeu/,
      agent_hyper_son/codes_musique_hyper.txt sous <work>).
  HSFA_FLUX_ZERO3=1 : ajouter aussi les flux ZERO 3 (codes 0002-002F, joues par le Z80 en mode « Complement ») a
      l'archive d'Upper et a celle de SFA3, pour le DIP « All tracks » (~117 Mo). Hyper garde par defaut TOUS ses flux
      (decision de l'utilisateur du 2026-10-16 : en Vorbis, retirer les flux ZERO 3 ne fait gagner que ~27 Mo).
  HSFA_FLUX_SANS_Q=1 : (Hyper, phase 1 de docs/rapports/PLAN-SON-HYPER.md) omettre les flux q des themes de stage et
      des jingles (rejoues en QSound par le coeur, meme en « All tracks ») en gardant les morceaux d'ecran : flux q qui
      bouclent et durent au plus 25 s (0002, 0004, 0005, 0007, 0008, 002B, 002C), dont la version arcade ne reboucle
      pas toujours comme la PS2 (fin de match 0004). HSFA_FLUX_ZERO3_GARDE="0004,..." : liste explicite a garder.
  HSFA_FLUX_FORMAT=ogg|adx : flux en Ogg Vorbis (defaut depuis le 2026-10-24, decision D6) ou ADX (tools/flux/flux_ogg.py, PLAN-VORBIS.md ; ~5 fois plus
      petit) ; demande ffmpeg (libvorbis), g++, gcc et numpy. HSFA_OGG_QUALITE (defaut 2), HSFA_OGG_CACHE (defaut
      <work>/flux_ogg). Defaut : ogg ; HSFA_FLUX_FORMAT=adx pour l'ancien format.
  HSFA_PARTITIONS=1 : (Hyper) carte musique, musiques ZERO / ZERO 2 jouees par les pilotes Z80 d'origine
      (docs/rapports/PLAN-PARTITIONS-HYPER.md) : membres hsfa_musique.bin (programmes e221 / e250 de X_DATA.BIN, ou
      HSFA_PILOTE_SFA1 / HSFA_PILOTE_SFA2 : image Z80 ou zip arcade sfa.zip / sfa2.zip) et hsfa_musique_table.txt.
      Demande les echantillons du rejeu (hsfa_rejeu.bin) dans le meme zip, ou X_DATA a l'execution.
  HSFA_SANS_FLUX=1 / HSFA_SANS_REJEU=1 : ne pas ajouter ces membres.
  HSFA_ROMS / HSFA_DOSSIER : (essais) autre dossier de ROM programme / de blocs ext_*.bin que celui de JEUX.
  SOURCE_DATE_EPOCH (secondes Unix, convention reproducible-builds.org) : archives DETERMINISTES -- date fixe pour chaque
      membre du zip et pour « construite le » de hsfa_info.txt (UTC), dates des sources ramenees a cette date au plus ;
      deux constructions identiques donnent alors des zips identiques a l'octet. Sans elle : dates reelles (comme avant).
  HSFA_STRICT=1 : n'embarquer QUE les fichiers attendus du jeu -- blocs ext_<adresse>.bin de ext_liste.txt (ecrite par
      mame_test.py) et tables f<N>.bin de carte.txt (banque commune, persos, animations) + f312, plan1, plan2 (+ la liste
      JEUX[..]['tables_en_plus']) ; un fichier attendu absent est une erreur, un fichier en trop est ignore et signale
      (ex. restes de la demonstration MAX : ext_b00000.bin, banques/pl26.bin). Sans elle : tout ce qui est present
      (comme avant).
"""
import hashlib, os, re, struct, sys, time, zipfile, zlib
OUTILS = os.environ.get("HSFA_OUTILS", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # outils du depot (tools/)
sys.path.insert(0, os.path.join(OUTILS, "flux"))

ICI = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("HSFA_WORK", os.path.dirname(ICI))
SORTIE = os.environ.get("HSFA_SORTIE", ICI)

EXT_FIN = 0xF00000                     # fin fixe de l'image des blocs externes ; base = EXT_FIN - taille (pilote)
EXT_DEFAUT = (0xA00000, 0x500000)      # SFA3, Upper : $A00000-$EFFFFF (taille fixe dans d_cps2.cpp)
TAB_LEN = 0x400000
GFX_LEN = 0x2000000
# bases fixes de banc_mem.lua (puis celles de ext_liste.txt)
EXT_FIXES = ["a04000", "b00000", "b40000", "b80000", "bc0000", "b04000", "c80000", "d40000", "d80000", "dc0000", "e00000"]
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
GFX = ["sz3.13m", "sz3.15m", "sz3.17m", "sz3.19m", "sz3.14m", "sz3.16m", "sz3.18m", "sz3.20m"]

JEUX = {
    "sfa3": dict(nom="sfa3hsfa", dossier="mame", roms="mame/roms_tr/sfa3ud", banques="mame/banques",
                 son=("mame/roms_tr/sfa3ud", ["sz3.01", "sz3.02", "sz3.11m", "sz3.12m"]),
                 config={"commun": "254", "ptr_anim": "FF3E48", "gfx_intro": "456"}, gfx=None, flux=()),
    "upper": dict(nom="sfa3uhsfa", dossier="mame_ro5", roms="mame_ro5/roms_ro5/sfa3ud", banques="mame_ro5/banques_hx",
                  son=("agent_son_ro5/hybride/roms_hybride", ["hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"]),
                  config={"commun": "351", "ptr_anim": "FF40BC", "gfx_intro": "456", "plans": "300,340,3a0"},
                  gfx=[("mame_ro5/hsfa_gfx.bin", 0x0000000), ("mame_ro5/hsfa_plans.bin", 0x1000000)],
                  flux=range(0x30, 0x37)),             # musiques des persos d'Upper (sans equivalent QSound)
    # Hyper (BANQUES-ET-MODES-ro9.md) : BANC_COMMUN=545, BANC_PTR_ANIM=FF40BC, pas de BANC_GFX_INTRO (456 par defaut ;
    # emplacement 4 jamais utilise), HSFA_PLANS=300,340,3a0, blocs $940000 / $C84000 (ext_liste.txt) ; son : ROM
    # hybride d'Upper (bruitages, voix, musiques ZERO 3) + flux ADX (DIP "All tracks" par defaut dans le pilote)
    "hyper": dict(nom="sfa3hhsfa", dossier="mame_ro9", roms="mame_ro9/roms_ro9/sfa3ud", banques="mame_ro9/banques_hx",
                  son=("agent_son_ro5/hybride/roms_hybride", ["hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"]),
                  config={"commun": "545", "ptr_anim": "FF40BC", "gfx_intro": "456", "plans": "300,340,3a0"},
                  gfx=[("mame_ro9/hsfa_gfx.bin", 0x0000000), ("mame_ro9/hsfa_plans.bin", 0x1000000)],
                  ext=(0x940000, 0x5C0000),            # taille fixe dans d_cps2.cpp (Sfa3hhsfaRomDesc)
                  flux="codes_hyper", rejeu=True),
    # (agent_coeur_banques, patch 0008 du coeur) ro9a = Hyper + mode Arcade d'Upper greffe (voie B,
    # greffe_arcade/GREFFE-ETAPE4.md), construction figee ro9a7c_fige (etape 7 de la greffe, 64/85 fins, entree ARCADE du menu) : memes reglages qu'Hyper (lance_ro9a.sh :
    # BANC_COMMUN=545, HSFA_PLANS=300,340,3a0, banques_hx de la construction), region graphique de 48 Mo : plans d'Upper
    # (mame_ro5/hsfa_plans.bin) en +$2000000 = $4000000 (HSFA_GFX=...,hsfa_plans.bin@4000000 du banc) ; pilote sfa3hahsfa
    "ro9a": dict(nom="sfa3hahsfa", dossier="greffe_arcade/constructions/ro9a7c_fige/b9",
                 roms="greffe_arcade/constructions/ro9a7c_fige/b9/roms_ro9/sfa3ud",
                 banques="greffe_arcade/constructions/ro9a7c_fige/banques_hx",
                 son=("agent_son_ro5/hybride/roms_hybride", ["hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"]),
                 config={"commun": "545", "ptr_anim": "FF40BC", "gfx_intro": "456", "plans": "300,340,3a0"},
                 gfx=[("mame_ro9/hsfa_gfx.bin", 0x0000000), ("mame_ro9/hsfa_plans.bin", 0x1000000),
                      ("mame_ro5/hsfa_plans.bin", 0x2000000)],
                 gfx_len=0x3000000,                   # taille fixe dans d_cps2.cpp (Sfa3hahsfaRomDesc)
                 trous=True,                          # blocs ext_<trou>.bin -> hsfa_trous.bin (patch 0009)
                 ext=(0x940000, 0x5C0000),
                 flux="codes_hyper", rejeu=True),
    # Upper + persos MAX (construction MAX=1, publication de l'integration MAX) : pilote et archive propres sfa3umhsfa
    # (patch 0013), memes membres que sfa3uhsfa. Banc MAX_BANC (dossier de construction, relatif a HSFA_WORK) ; tuiles
    # MAX (cache SFA3MAX_CACHE de la session MAX, note dans <banc>/sfa3max_cache.txt) a la suite de hsfa_gfx.bin selon
    # max_cache.py ; ROM son MAX_SON. Entree calculee a la construction (_jeu_upper_max).
    "upper_max": "MAX",
}

def _jeu_upper_max():
    """entree upper_max : disposition graphique des persos MAX selon max_cache.py (scripts/untranspile, ou
    HSFA_MAX_CACHE_DIR) et le cache SFA3MAX_CACHE du banc"""
    banc = os.environ.get("MAX_BANC") or sys.exit("upper_max : MAX_BANC = dossier du banc MAX (relatif a HSFA_WORK)")
    f = os.path.join(WORK, banc, "sfa3max_cache.txt")
    if os.path.exists(f) and open(f).read().strip() and not os.environ.get("SFA3MAX_CACHE"):
        os.environ["SFA3MAX_CACHE"] = os.path.expanduser(open(f).read().strip())
    sys.path.insert(0, os.environ.get("HSFA_MAX_CACHE_DIR") or os.path.join(ICI, "..", "..", "scripts", "untranspile"))
    sys.dont_write_bytecode = True
    import max_cache as MC
    return dict(nom="sfa3umhsfa", dossier=banc, roms=os.path.join(banc, "roms_ro5/sfa3ud"),
                banques=os.path.join(banc, "banques_hx"),
                son=(os.environ.get("MAX_SON", "agent_son_max/roms_son_max_ko"),
                     ["hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"]),
                config={"commun": "351", "ptr_anim": "FF40BC", "gfx_intro": "456", "plans": MC.PLANS_HEX},
                gfx=[("mame_ro5/hsfa_gfx.bin", 0x0000000), (MC.FORK + "max_gfx.bin", MC.G_MAX * 128 - 0x2000000),
                     (MC.FORK + "max_portraits_gfx.bin", MC.G0 * 128 - 0x2000000),
                     (os.path.join(banc, "max_plus_gfx.bin"), MC.G_PLUS * 128 - 0x2000000),
                     ("mame_ro5/hsfa_plans.bin", MC.PLANS_ORG - 0x2000000)],
                flux=range(0x30, 0x37))

journal = []

DATE_FIXE = os.environ.get("SOURCE_DATE_EPOCH")
DATE_FIXE = int(DATE_FIXE) if DATE_FIXE not in (None, "") else None
STRICT = os.environ.get("HSFA_STRICT") == "1"


def date_texte(t):
    """date d'un fichier ou de la construction : ramenee a SOURCE_DATE_EPOCH au plus (et en UTC) si elle est donnee"""
    if DATE_FIXE is None:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(min(t, DATE_FIXE)))

def lit(chemin):
    """lit un fichier (stable : relu si modifie pendant la lecture) et note md5 / date"""
    for _ in range(10):
        st = os.stat(chemin)
        d = open(chemin, "rb").read()
        if os.stat(chemin).st_mtime == st.st_mtime and len(d) == st.st_size:
            break
        time.sleep(2)
    else:
        raise SystemExit("fichier instable (reconstruction en cours ?) : " + chemin)
    rel = os.path.relpath(os.path.realpath(chemin), WORK) if os.path.realpath(chemin).startswith(WORK) else os.path.basename(chemin)
    journal.append("%s  %s  %s  %d" % (hashlib.md5(d).hexdigest(), date_texte(st.st_mtime), rel, len(d)))
    return d

def echange(d):
    """mots gros-boutistes -> format ROM_LOAD16_WORD_SWAP (octets de chaque mot echanges)"""
    b = bytearray(d)
    b[0::2], b[1::2] = d[1::2], d[0::2]
    return bytes(b)

# (agent_coeur_banques, patch 0009 du coeur, prototype) TROUS de la carte CPS2 68K servis en ROM par hsfa_trous.bin
# (membre facultatif, pilotes qui le declarent) : memes plages, meme ordre que HsfaTrous de cps_hsfa.cpp
TROUS = [(0x410000, 0x618000), (0x61A000, 0x660000), (0x668000, 0x700000), (0x710000, 0x800000),
         (0x810000, 0x900000), (0x930000, 0x940000), (0xFB0000, 0xFF0000)]
TROUS_LEN = sum(b - a for a, b in TROUS)            # 0x516000

def trou_de(base, n):
    """decalage dans hsfa_trous.bin d'un bloc [base, base + n) entierement dans un trou, sinon None"""
    o = 0
    for a, b in TROUS:
        if a <= base and base + n <= b: return o + base - a
        o += b - a
    return None

def image_ext(dossier, ext=None, trous=None):
    """trous = bytearray(TROUS_LEN) : les blocs situes dans un trou de la carte y vont (sinon : erreur, comme avant)"""
    EXT_BASE, EXT_LEN = ext or EXT_DEFAUT
    assert EXT_BASE + EXT_LEN == EXT_FIN
    img = bytearray(EXT_LEN)
    pris = bytearray(EXT_LEN)
    bases = [] if STRICT else list(EXT_FIXES)
    lst = os.path.join(dossier, "ext_liste.txt")
    if os.path.exists(lst):
        for l in lit(lst).decode().split():
            if l and l not in bases:
                bases.append(l)
    elif STRICT:
        raise SystemExit("HSFA_STRICT : pas de ext_liste.txt dans " + dossier)
    if STRICT:
        for f in sorted(os.listdir(dossier)):
            if f.startswith("ext_") and f.endswith(".bin") and f[4:-4] not in bases:
                print("  ignore (absent de ext_liste.txt) : " + f)
    n = 0
    for nom in bases:
        p = os.path.join(dossier, "ext_%s.bin" % nom)
        if not os.path.exists(p):
            if STRICT:
                raise SystemExit("HSFA_STRICT : bloc de ext_liste.txt absent : " + p)
            continue
        d = lit(p)
        base = int(nom, 16)
        if trous is not None and trou_de(base, len(d)) is not None:
            o = trou_de(base, len(d))
            trous[o:o + len(d)] = d
            print("  bloc $%06x : %d o (trou de la carte -> hsfa_trous.bin +$%06x)" % (base, len(d), o))
            n += 1
            continue
        if base < EXT_BASE or base + len(d) > EXT_BASE + EXT_LEN:
            raise SystemExit("bloc hors de $%06X-$%06X : %s ($%x, %d o)" % (EXT_BASE, EXT_FIN - 1, p, base, len(d)))
        o = base - EXT_BASE
        if any(pris[o:o + len(d)]):
            print("  ATTENTION : %s chevauche un bloc precedent (le dernier l'emporte)" % p)
        img[o:o + len(d)] = d
        pris[o:o + len(d)] = b"\1" * len(d)
        print("  bloc $%06x : %d o" % (base, len(d)))
        n += 1
    if n == 0:
        raise SystemExit("aucun bloc ext_*.bin dans " + dossier)
    return echange(bytes(img))

def tables_attendues(carte, config, en_plus=()):
    """HSFA_STRICT : f<banque commune>, f<N> de carte.txt (lignes « perso id N » et « anim ptr N », N > 0), f312, plan1,
    plan2 (+ en_plus) : exactement ce que banques.py tout / 312 / plans ecrit (et hsfa_gfx.py / hsfa_plans.py, _hx)"""
    att = {"f%s" % config["commun"], "f312", "plan1", "plan2"} | set(en_plus)
    for l in carte.decode().splitlines():
        m = l.split()
        if len(m) == 3 and m[0] in ("perso", "anim") and int(m[2]) > 0:
            att.add("f%d" % int(m[2]))
    return att

def tables(dossier, config, en_plus=()):
    ent = [("config", "".join("%s=%s\n" % kv for kv in config.items()).encode())]
    carte = lit(os.path.join(dossier, "carte.txt"))
    ent.append(("carte", carte))
    att = tables_attendues(carte, config, en_plus) if STRICT else None
    if STRICT:
        manque = sorted(n for n in att if not os.path.exists(os.path.join(dossier, n + ".bin")))
        if manque:
            raise SystemExit("HSFA_STRICT : tables attendues absentes de %s : %s" % (dossier, ", ".join(manque)))
    for f in sorted(os.listdir(dossier)):
        if f.endswith(".bin"):
            if STRICT and f[:-4] not in att:
                print("  ignore (table non attendue) : " + f)
                continue
            nom = f[:-4]
            if len(nom) > 23:
                raise SystemExit("nom de table trop long : " + f)
            ent.append((nom, lit(os.path.join(dossier, f))))
    tete = bytearray(b"HSFATAB1" + struct.pack("<II", len(ent), 0))
    o = 16 + 32 * len(ent)
    corps = bytearray()
    for nom, d in ent:
        tete += nom.encode().ljust(24, b"\0") + struct.pack("<II", o + len(corps), len(d))
        corps += d
        corps += bytes((-len(corps)) % 4)
    blob = bytes(tete + corps)
    if len(blob) > TAB_LEN:
        raise SystemExit("tables : %d o > %d (agrandir hsfa_tab.bin dans le pilote)" % (len(blob), TAB_LEN))
    print("  tables : %d entrees, %d o" % (len(ent), len(blob)))
    return blob + bytes(TAB_LEN - len(blob))

def image_gfx(liste, gfx_len=GFX_LEN):
    img = bytearray(gfx_len)
    for rel, o in liste:
        d = lit(os.path.join(WORK, rel))
        if o + len(d) > gfx_len:
            raise SystemExit("%s depasse la region etendue" % rel)
        if o == 0 and len(d) > 0x1000000:
            print("  ATTENTION : hsfa_gfx.bin > 16 Mo, recouvert par hsfa_plans.bin en $3000000")
        img[o:o + len(d)] = d
        print("  %s -> $%07x (%d o)" % (rel, 0x2000000 + o, len(d)))
    return bytes(img)

# ---------------------------------------------------------------------------------------------------------------------
# Membres lus sur place par le coeur (STOCKES) : flux ADX reduits et rejeu QSound

def _iso_fichier(f, nom):
    """decalage et taille d'un fichier de la racine ISO9660, ou None"""
    f.seek(0x8000); pvd = f.read(2048)
    if pvd[1:6] != b"CD001": return None
    lba, tai = struct.unpack_from("<I", pvd, 158)[0], struct.unpack_from("<I", pvd, 166)[0]
    f.seek(lba * 2048); d = f.read(tai); p = 0
    while p < tai:
        l = d[p]
        if not l: p = (p // 2048 + 1) * 2048; continue
        nl = d[p + 32]; n = d[p + 33:p + 33 + nl].split(b";")[0].decode("latin1")
        if n == nom: return struct.unpack_from("<I", d, p + 2)[0] * 2048, struct.unpack_from("<I", d, p + 10)[0]
        p += l
    return None

def source_iso(chemin, nom):
    """(fichier, base) : fichier lui-meme (base 0) ou ISO contenant nom"""
    with open(chemin, "rb") as f:
        r = _iso_fichier(f, nom)
    return (chemin, r[0]) if r else (chemin, 0)

def table_flux():
    return os.environ.get("HSFA_FLUX_TABLE") or os.path.join(WORK, "agent_flux", "hsfa_flux_table.txt")

def codes_flux(J):
    """codes de musique du jeu a copier en flux"""
    sel = J.get("flux") or ()
    if sel == "codes_hyper":
        f = os.environ.get("HSFA_CODES_HYPER") or os.path.join(WORK, "agent_hyper_son", "codes_musique_hyper.txt")
        codes = {int(l.split()[0], 16) for l in lit(f).decode().splitlines() if l.strip()}
    else:
        codes = set(sel)
        if os.environ.get("HSFA_FLUX_ZERO3") == "1":
            codes |= set(range(0x02, 0x30))
    return codes

def membres_flux(J):
    """(hsfa_flux.bin : (taille, generateur de blocs), hsfa_flux_table.txt) ou None"""
    if os.environ.get("HSFA_SANS_FLUX") == "1": return None
    if not J.get("flux") and os.environ.get("HSFA_FLUX_ZERO3") != "1": return None
    y = os.environ.get("HSFA_YDATA")
    if not y:
        print("  (pas de HSFA_YDATA : archive sans flux ADX)")
        return None
    codes = codes_flux(J)
    texte = lit(table_flux())
    fids, omis = set(), set()
    sans_q = J.get("flux") == "codes_hyper" and os.environ.get("HSFA_FLUX_SANS_Q") == "1"
    garde_txt = os.environ.get("HSFA_FLUX_ZERO3_GARDE")
    garde = None if garde_txt is None else {int(c, 16) for c in garde_txt.replace(" ", "").split(",") if c}
    gardes = []
    for l in texte.decode().splitlines():
        m = re.match(r"([0-9A-Fa-f]{4})\s+(\d+)\s+(\d+)\s*(\S*)", l)
        if m and int(m.group(1), 16) in codes and "x" not in m.group(4):
            if sans_q and "q" in m.group(4):
                d = re.search(r";\s*([0-9.]+)\s*s\s+boucle", l)
                ecran = (int(m.group(1), 16) in garde) if garde is not None else bool(d and float(d.group(1)) <= 25.0)
                if not ecran: omis.add(int(m.group(2))); continue
                gardes.append(m.group(1))
            fids.add(int(m.group(2)))
    if gardes: print("  %d flux ZERO 3 d'ecran gardes en version PS2 : %s" % (len(gardes), " ".join(gardes)))
    omis -= fids                                       # un flux aussi demande par un code sans q reste
    if omis: print("  %d flux ZERO 3 omis (HSFA_FLUX_SANS_Q=1 : joues en QSound)" % len(omis))
    chemin, base = source_iso(y, "Y_DATA.BIN")
    with open(chemin, "rb") as f:
        f.seek(base); h = f.read(8)
        if h[:4] != b"AFS\0": raise SystemExit("Y_DATA : en-tete AFS absent (%s)" % y)
        n = struct.unpack_from("<I", h, 4)[0]
        f.seek(base + 8); t = f.read(8 * n)
        toc = [struct.unpack_from("<II", t, 8 * i) for i in range(n)]
    st = os.stat(chemin)
    for i in fids:
        if i >= n: raise SystemExit("flux Y%d hors de Y_DATA (%d entrees)" % (i, n))
    fmt = os.environ.get("HSFA_FLUX_FORMAT", "ogg")
    oggs = {}                                          # entree -> fichier Ogg (les autres restent en ADX)
    if fmt == "ogg":
        import flux_ogg
        cache = os.environ.get("HSFA_OGG_CACHE") or os.path.join(WORK, "flux_ogg")
        md5 = {}
        with open(chemin, "rb") as f:
            for i in sorted(fids):
                f.seek(base + toc[i][0]); md5[i] = hashlib.md5(f.read(toc[i][1])).hexdigest()
        source = chemin + ("@%x" % base if base else "")
        oggs = {i: c for i, c in flux_ogg.encode_tous(source, sorted(md5.items()), cache).items() if c}
    elif fmt != "adx":
        raise SystemExit("HSFA_FLUX_FORMAT : adx ou ogg (%s)" % fmt)
    tai = {i: (os.path.getsize(oggs[i]) if i in oggs else toc[i][1]) for i in fids}
    ent = [(0, 0)] * n
    o = (8 + 8 * n + 2047) // 2048 * 2048
    for i in sorted(fids):
        ent[i] = (o, tai[i]); o += (tai[i] + 2047) // 2048 * 2048
    taille = o
    tete = bytearray(b"AFS\0" + struct.pack("<I", n) + b"".join(struct.pack("<II", *e) for e in ent))
    tete += bytes((8 + 8 * n + 2047) // 2048 * 2048 - len(tete))
    def blocs():
        yield bytes(tete)
        with open(chemin, "rb") as f:
            for i in sorted(fids):
                if i in oggs:
                    yield open(oggs[i], "rb").read()
                else:
                    f.seek(base + toc[i][0]); reste = toc[i][1]
                    while reste:
                        d = f.read(min(reste, 1 << 20))
                        if not d: raise SystemExit("Y_DATA tronque (flux Y%d)" % i)
                        reste -= len(d); yield d
                pad = (-tai[i]) % 2048
                if pad: yield bytes(pad)
    fmt_txt = "%d Ogg Vorbis q%s, %d ADX" % (len(oggs), os.environ.get("HSFA_OGG_QUALITE", "2"), len(fids) - len(oggs)) \
        if fmt == "ogg" else "ADX"
    journal.append("-  %s  %s (Y_DATA%s) : %d flux (%s), %d o" % (date_texte(st.st_mtime), os.path.basename(chemin),
                   " @%x" % base if base else "", len(fids), fmt_txt, taille))
    print("  hsfa_flux.bin : %d flux sur %d codes (%s), %.1f Mo" % (len(fids), len(codes), fmt_txt, taille / 1e6))
    return (taille, blocs), texte

def membres_rejeu(J):
    """(hsfa_rejeu.bin, hsfa_rejeu_table.txt) ou None"""
    if not J.get("rejeu") or os.environ.get("HSFA_SANS_REJEU") == "1": return None
    tab = os.environ.get("HSFA_REJEU_TABLE") or os.path.join(WORK, "agent_son_hyper_rom", "rejeu", "hsfa_rejeu_table.txt")
    x = os.environ.get("HSFA_XDATA")
    if not x:
        y = os.environ.get("HSFA_YDATA")
        if y and source_iso(y, "X_DATA.BIN")[1]: x = y
        elif os.path.exists(os.path.join(WORK, "xdata", "X_DATA.BIN")): x = os.path.join(WORK, "xdata", "X_DATA.BIN")
    if not x or not os.path.exists(tab):
        print("  (pas de X_DATA ou de table du rejeu : archive sans rejeu, sons SFA3)")
        return None
    texte = lit(tab)
    chemin, base = source_iso(x, "X_DATA.BIN")
    rom = bytearray(0x800000)
    with open(chemin, "rb") as f:
        for l in texte.decode().splitlines():
            m = re.match(r"SOURCE (\S+) ([0-9A-Fa-f]+) ([0-9A-Fa-f]+) ([0-9A-Fa-f]+) ([0-9A-Fa-f]+)", l)
            if not m: continue
            nom, off, tai, banque, crc = m.group(1), *(int(m.group(k), 16) for k in range(2, 6))
            f.seek(base + off); d = f.read(tai)
            if len(d) != tai or zlib.crc32(d) != crc:
                raise SystemExit("X_DATA : %s illisible ou CRC different (%s)" % (nom, x))
            o = banque << 16
            if o + tai > len(rom): raise SystemExit("rejeu : %s hors des 8 Mo" % nom)
            rom[o:o + tai] = d
            print("  hsfa_rejeu.bin : %s (X_DATA +$%x, %d o, CRC %08X) en banque $%02X" % (nom, off, tai, crc, banque))
    journal.append("%s  %s  %s (X_DATA%s) -> hsfa_rejeu.bin  %d" % (hashlib.md5(rom).hexdigest(),
                   date_texte(os.stat(chemin).st_mtime), os.path.basename(chemin), " @%x" % base if base else "", len(rom)))
    if os.environ.get("HSFA_CRIS_ARCADE") != "0":       # cris de degats / K.O. mesures sur l'arcade (2026-10-16)
        sys.path.insert(0, os.path.join(OUTILS, "son-hyper"))
        import corrige_cris
        j = []
        texte = "\n".join(corrige_cris.applique(texte.decode().split("\n"), j)).encode()
        print("  hsfa_rejeu_table.txt : %d cri(s) remplace(s) par ceux de l'arcade (son-hyper/cris_arcade.tsv)" % len(j))
    return bytes(rom), texte

def _afs_entree(chemin, base, i):
    """(decalage, taille) de l'entree i d'un AFS (Y_DATA / X_DATA), ou None"""
    with open(chemin, "rb") as f:
        f.seek(base); h = f.read(8)
        if h[:4] != b"AFS\0": return None
        n = struct.unpack_from("<I", h, 4)[0]
        if i >= n: return None
        f.seek(base + 8 + 8 * i); o, t = struct.unpack("<II", f.read(8))
    return base + o, t

PILOTES_MUSIQUE = (("sfa1", 221, b"version 1.05A", "sfa", 0x000000), ("sfa2", 250, b"version 1.05C", "sfa2", 0x400000))

def _pilote_image(nom, entree, jeu_zip, x):
    """image Z80 (region audiocpu MAME) d'un pilote : HSFA_PILOTE_<NOM> (image ou zip arcade), sinon entree de X_DATA"""
    v = os.environ.get("HSFA_PILOTE_" + nom.upper())
    if v and v.lower().endswith(".zip"):
        sys.path.insert(0, os.path.join(OUTILS, "son-hyper"))
        import tempfile, rendu_partitions
        with tempfile.TemporaryDirectory() as t:
            z80, _ = rendu_partitions.depuis_zip(jeu_zip, v, t)
            return open(z80, "rb").read(), os.path.basename(v)
    if v: return lit(v), os.path.basename(v)
    if not x: return None, None
    chemin, base = source_iso(x, "X_DATA.BIN")
    e = _afs_entree(chemin, base, entree)
    if not e: raise SystemExit("X_DATA : entree %d introuvable (%s n'est pas un AFS ?)" % (entree, x))
    with open(chemin, "rb") as f:
        f.seek(e[0]); return f.read(e[1]), "X_DATA e%d" % entree

def membres_musique(J):
    """(hsfa_musique.bin, hsfa_musique_table.txt) ou None (carte musique, Hyper, HSFA_PARTITIONS=1)"""
    if not J.get("rejeu") or os.environ.get("HSFA_PARTITIONS") != "1": return None
    sys.path.insert(0, os.path.join(OUTILS, "son-hyper"))
    from rendu_partitions import HYPER
    x = os.environ.get("HSFA_XDATA")
    if not x:
        y = os.environ.get("HSFA_YDATA")
        if y and source_iso(y, "X_DATA.BIN")[1]: x = y
        elif os.path.exists(os.path.join(WORK, "xdata", "X_DATA.BIN")): x = os.path.join(WORK, "xdata", "X_DATA.BIN")
    donnees, lignes = bytearray(), ["# carte musique (paquet_fbneo.py) : PILOTE nom decalage taille crc32 rom_off rom_tai",
                                     "# puis code_hyper pilote code_pilote gain_%"]
    for nom, entree, version, jeu_zip, rom_off in PILOTES_MUSIQUE:
        img, src = _pilote_image(nom, entree, jeu_zip, x)
        if img is None:
            print("  (pas de X_DATA ni de HSFA_PILOTE_%s : archive sans partitions)" % nom.upper()); return None
        if version not in img[:0x400]:
            raise SystemExit("pilote %s (%s) : chaine %r absente, ce n'est pas le bon programme" % (nom, src, version.decode()))
        if len(img) < 0x18000: raise SystemExit("pilote %s (%s) : %d o, trop court" % (nom, src, len(img)))
        lignes.append("PILOTE %s %x %x %08x %x 400000" % (nom, len(donnees), len(img), zlib.crc32(img), rom_off))
        print("  hsfa_musique.bin : pilote %s depuis %s (%d o, CRC %08X)" % (nom, src, len(img), zlib.crc32(img)))
        journal.append("%s  -  %s -> hsfa_musique.bin (pilote %s)  %d" % (hashlib.md5(img).hexdigest(), src, nom, len(img)))
        donnees += img
    gains = {}                                          # gain par morceau, cale sur le niveau des flux PS2
    g = os.path.join(OUTILS, "son-hyper", "gains_partitions.tsv")
    if os.path.exists(g):
        for l in open(g, encoding="utf-8"):
            c = l.rstrip("\n").split("\t")
            if len(c) >= 8 and not l.startswith("#") and c[0] != "code_hyper": gains[int(c[0], 16)] = int(c[7])
    for jeu, nom in (("sfa", "sfa1"), ("sfa2", "sfa2")):
        for h, c in sorted(HYPER[jeu].items()):
            lignes.append("%04X %s %04X %d" % (h, nom, c, gains.get(h, 100)))
    return bytes(donnees), ("\n".join(lignes) + "\n").encode()

def ecrit_membre(z, nom, d, stocke=False):
    """membre du zip (date fixe si SOURCE_DATE_EPOCH) ; d = octets, ou (taille, generateur) pour un gros membre stocke"""
    meth = zipfile.ZIP_STORED if stocke else zipfile.ZIP_DEFLATED
    if DATE_FIXE is None:
        zi = zipfile.ZipInfo(nom, date_time=time.localtime(time.time())[:6])
    else:
        # membre a date fixe (ZIP : heure locale sans fuseau, 1980 au plus tot ; secondes paires), droits et
        # systeme d'origine fixes (sinon 0 sous Windows, 3 ailleurs) : octets identiques d'une construction a l'autre
        zi = zipfile.ZipInfo(nom, date_time=time.gmtime(max(DATE_FIXE, 315532800))[:6])
        zi.create_system = 3
        zi.external_attr = 0o644 << 16
    zi.compress_type = meth
    if isinstance(d, tuple):
        taille, gen = d
        zi.file_size = taille
        n = 0
        with z.open(zi, "w") as w:
            for b in gen():
                w.write(b); n += len(b)
        if n != taille: raise SystemExit("%s : %d o ecrits au lieu de %d" % (nom, n, taille))
    elif DATE_FIXE is None and not stocke:
        z.writestr(nom, d)
    else:
        z.writestr(zi, d, compresslevel=None if stocke else 6)

def construit(cle):
    J = JEUX[cle]
    if J == "MAX": J = _jeu_upper_max()
    journal.clear()
    print("== %s (%s)" % (J["nom"], cle))
    roms = os.environ.get("HSFA_ROMS") or os.path.join(WORK, J["roms"])
    fichiers = []
    for f in PRG + GFX + ["phoenix.key"]:
        fichiers.append((f, lit(os.path.join(roms, f))))
    sd, sl = J["son"]
    for f in sl:
        fichiers.append((f, lit(os.path.join(WORK, sd, f))))
    trous = bytearray(TROUS_LEN) if J.get("trous") else None
    fichiers.append(("hsfa_ext.bin", image_ext(os.environ.get("HSFA_DOSSIER") or os.path.join(WORK, J["dossier"]), J.get("ext"), trous)))
    if trous is not None and any(trous):              # membre facultatif : seulement s'il sert
        fichiers.append(("hsfa_trous.bin", echange(bytes(trous))))
    if J.get("rejeu") and os.environ.get("HSFA_VOIX_ARCADE") != "0":   # voix « par pas » mesurees sur l'arcade
        sys.path.insert(0, os.path.join(OUTILS, "son-hyper"))
        import corrige_voix
        d = dict(fichiers)
        ext = bytearray(d["hsfa_ext.bin"]); prog = bytearray(b"".join(d[f] for f in corrige_voix.PROG))
        j = []
        try:
            corrige_voix.applique(ext, prog, corrige_voix.corrections(os.path.join(OUTILS, "son-hyper", "voix_arcade.tsv")), j)
            fichiers = [(f, bytes(ext) if f == "hsfa_ext.bin" else x) for f, x in fichiers]
            print("  hsfa_ext.bin : %d voix remplacee(s) par celles de l'arcade (son-hyper/voix_arcade.tsv)"
                  % len([x for x in j if "->" in x]))
        except SystemExit as e:
            print("  (voix de l'arcade non appliquees : %s)" % e)
    fichiers.append(("hsfa_tab.bin", tables(os.path.join(WORK, J["banques"]), J["config"], J.get("tables_en_plus", ()))))
    if J["gfx"]:
        fichiers.append(("hsfa_gfx.bin", image_gfx(J["gfx"], J.get("gfx_len", GFX_LEN))))
    stockes = []                                       # membres lus sur place par le coeur : sans compression
    mf = membres_flux(J)
    if mf:
        stockes += [("hsfa_flux.bin", mf[0]), ("hsfa_flux_table.txt", mf[1])]
    mr = membres_rejeu(J)
    if mr:
        stockes += [("hsfa_rejeu.bin", mr[0]), ("hsfa_rejeu_table.txt", mr[1])]
    mm = membres_musique(J)
    if mm:
        stockes += [("hsfa_musique.bin", mm[0]), ("hsfa_musique_table.txt", mm[1])]
    info = "Archive %s construite le %s par paquet_fbneo.py\nmd5  date  fichier source  taille\n%s\n" % (
        J["nom"], date_texte(time.time()), "\n".join(journal))
    sortie = os.path.join(SORTIE, J["nom"] + ".zip")
    tmp = sortie + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f, d in fichiers + [("hsfa_info.txt", info)]:
            ecrit_membre(z, f, d)
        for f, d in stockes:
            ecrit_membre(z, f, d, stocke=True)
    os.replace(tmp, sortie)
    open(os.path.join(SORTIE, J["nom"] + "_sources.txt"), "w").write(info)
    print("  -> %s (%.1f Mo)" % (sortie, os.path.getsize(sortie) / 2**20))

if __name__ == "__main__":
    for c in (sys.argv[1:] or ["sfa3", "upper", "hyper"]):
        construit(c)
