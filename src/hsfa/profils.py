"""(HANDOFF §108) PROFILS PAR MODULE pour mame_test.py / translate.py / assets_natifs.py.
MODULE=ro3 (defaut, SFA3) ou ro5 (Upper). Les valeurs ro5 viennent de work/carto_ro5/CARTE-ro5.md (§3, §6).
Toute valeur absente d'un profil = fonctionnalite desactivee pour ce module (routine a la main, correctif...)."""
import os

EXTRACT = os.environ.get("EXTRACT_MODULES", "<workspace>/anthology_extract/decompressed")   # (agent_son_hyper_rom)

PROFILS = {
    'ro3': dict(
        fichier='ro3_usa_prog68k.bin',
        va_reset=0x926b0, va_frame=0x2ef30, va_init=0x2ed20,
        irq2_dans=0x2f310,                       # adresse DANS la fonction du balayage vertical porte
        sauve_regs=(0x2ff00, 0x30130),           # sauvegarde / restauration des registres (-> RTS)
        hooks='hooks_fork_ro3.json',
        manette={0x89228: (1, 0x58, 0x51a), 0x8924c: (2, 0x5c, 0x91a)},
        aides={0x570360: 'movem_push', 0x5706c0: 'movem_pop', 0x570a20: 'andi_ccr', 0x570d00: 'abcd', 0x570aa0: 'roxr'},
        be48=0xbe48,                             # pointeur d'animation native ($BE48(A5))
        musique=(0x4a848, 0x4a988, 0xc18e),      # repere musique (§103) : debut, suite, index de la table de ticks
        objets_intro=0x585750,                   # table (type, parametre) lue par 'lb 0x1129' (§103)
        palettes=0x451230,                       # table moteur des palettes par perso (§105)
        mains=True,                              # routines reecrites a la main (§103-§104)
        travail='<workspace>/work/mame', sortie='roms_tr',
        option=(0x573e20, 0x5792e0, 0x21f710, 0x21f8e0, 0xff4001),           # (agent_options) tache OPTION, sortie de l'ecran, creer / finir une tache (exec.), curseur des modes (68K)
    ),
    'ro5': dict(
        fichier='ro5_usa_prog68k.bin',
        va_reset=0xced70, va_frame=0x324b0, va_init=0x322a0,
        irq2=0x32830,                            # fonction du balayage vertical (CARTE-ro5 §3.1)
        sauve_regs=(0x334d0, 0x33700),
        hooks='hooks_fork_ro5.json',
        manette={0xc5738: (1, 0x58, 0x51a), 0xc575c: (2, 0x5c, 0x91a)},
        aides={0x212b00: 'movem_push', 0x212e60: 'movem_pop', 0x2131c0: 'andi_ccr', 0x2134a0: 'abcd', 0x213240: 'roxr'},
        be48=0xc0bc,
        musique=(0x5081c, 0x5098c, 0xc38e),      # (HANDOFF §118) avec la ROM son de SFA3 (le Z80 d'Upper n'a pas les musiques)
        objets_intro=0x60ca50,
        palettes=0x5072B0,                       # (HANDOFF §119) 40 decalages signes ; groupe = couleur x 5 (et non (ism+1)x2+couleur)
        mains=False,                             # homologues a verifier (CARTE-ro5 §6 point 7)
        blocs=(0x61a100, 32),                    # (HANDOFF §126) table des blocs de donnees par perso : la coupure des
                                                 # donnees (§108) tombe au debut d'un bloc (pointeurs base + decalage)
        travail='<workspace>/work/mame_ro5', sortie='roms_ro5',
        option=(0x5f22e0, 0x5f72e0, 0x222ce0, 0x222eb0, 0xff4201),           # (agent_options) tache OPTION, sortie de l'ecran, creer / finir une tache (exec.), curseur des modes (68K)
    ),
    # (agent_ro9, MISE-EN-ROUTE-ro9.md) Hyper : valeurs de CARTE-ro9 §4, reverifiees dans le MIPS (outils/compare.py)
    'ro9': dict(
        fichier='ro9_usa_prog68k.bin',
        va_reset=0x3da00, va_frame=0x3ee30, va_init=0x3ec20,   # = ro5 0xCED70 / 0x324B0 / 0x322A0 (MIPS masque)
        irq2=0x3f1b0,                            # fonction du balayage vertical (contient 0x3F224 ; = ro5 0x32830)
        sauve_regs=(0x3fe50, 0x40080),           # identiques a ro5 0x334D0 / 0x33700
        hooks='hooks_fork_ro9.json',             # MODULE=ro9 hooks_fork.py (regenere a l'identique)
        manette={0x38a958: (1, 0x58, 0x51a), 0x38a97c: (2, 0x5c, 0x91a)},   # jalr natif 0x23D20 (= ro5 0x23BB0)
        aides={0x212dc0: 'movem_push', 0x213120: 'movem_pop', 0x213480: 'andi_ccr', 0x213610: 'abcd', 0x213500: 'roxr'},
        be48=0xc0bc,                             # homologue de $BE48 : LU seulement (0x3728A4..), aucun natif ne l'ecrit
        musique=None,                            # pas de table de ticks d'intro dans ro9 (CARTE-ro9 §4.3)
        objets_intro=None,                       # pas de table 0x585750 ni d'acces 'lb 0x1129' dans ro9
        palettes=None,
        mains=False,
        blocs_lignes=((0x6A7A94, 128), (0x6A7C94, 48), (0x6A7D54, 48)),   # (agent_defauts_banc, COUPE_BLOCS) BLOC-HYPER §0
        data_ext=0x940000,                       # fin des donnees en $940000 (marquee $01 dans la conversion) :
                                                 # $C80000 est occupe par le fichier fixe 547 ($C84000-$D0B188)
        travail='<workspace>/work/mame_ro9', sortie='roms_ro9',
        option=(0x214ab0, 0x2185b0, 0x22f660, 0x22f830, 0xff4201),           # (agent_options) tache OPTION, sortie de l'ecran, creer / finir une tache (exec.), curseur des modes (68K)
    ),
}

NOM = os.environ.get("MODULE", "ro3")
P = PROFILS[NOM]
if os.environ.get("TRAVAIL"): P = dict(P, travail=os.environ["TRAVAIL"])   # (agent_ro9) essais hors des dossiers partages
def chemin(): return os.path.join(EXTRACT, P['fichier'])
