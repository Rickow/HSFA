#!/usr/bin/env python3
"""cibles.py -- formats de sortie de la construction HSFA et concessions propres a chaque format et a chaque jeu.

Cibles :
  fbneo-hsfa      coeur libretro FinalBurn Neo HSFA (patchs 0001-0030) : la sortie actuelle, PAR DEFAUT, aucune concession
  fbneo-autonome  FinalBurn Neo HSFA autonome (Windows)         : disponible EN ESSAI ; memes archives que fbneo-hsfa,
                  a l'octet (patches/fbneo-autonome) ; annonce de la concession, confirmation, puis construction normale
  mister          MiSTer, coeur CPS-2 de Jotego etendu          : n'existe pas               -> mode BILAN
  cps2-banques    vraie CPS-2 + carte fille a banques           : n'existe pas               -> mode BILAN

Mode BILAN : la construction n'est PAS lancee ; on annonce les concessions et les budgets mesures, on demande
confirmation, et rien n'est ecrit. Chaque concession cite sa source : un patch du coeur (patches/fbneo) ou une mesure
(etude work/multi_cibles du 2026-11-11, zips construits par le script le 2026-11-08). Rien n'est invente : ce qui n'est
pas mesure ou pas verifie porte le statut « a verifier ».

Textes vus par le joueur : francais accentue et anglais, caracteres limites a la page de code cp1252 (console Windows
redirigee : pas de UnicodeEncodeError). Langue : HSFA_LANGUE=fr|en, sinon celle du systeme (francais -> fr, sinon en).

Usage seul (sans construire) :
  python3 cibles.py [--cible C] [--jeux sfa3,upper,...] [--en|--fr]   annonce des concessions et budgets
  python3 cibles.py --table                                          table complete cible x jeu
"""
import locale, os, re, sys, textwrap

DEFAUT = "fbneo-hsfa"
# dispo : la construction produit des archives ; essai : version d'essai (annonce + confirmation avant de construire)
CIBLES = {
    "fbneo-hsfa": dict(dispo=True, essai=False, fr="FinalBurn Neo HSFA (cœur RetroArch du projet)",
                       en="FinalBurn Neo HSFA (the project's RetroArch core)"),
    "fbneo-autonome": dict(dispo=True, essai=True, fr="FinalBurn Neo HSFA autonome (Windows, version d'essai)",
                           en="Standalone FinalBurn Neo HSFA (Windows, test build)"),
    "mister": dict(dispo=False, essai=False, fr="MiSTer (cœur CPS-2 de Jotego étendu)",
                   en="MiSTer (extended Jotego CPS-2 core)"),
    "cps2-banques": dict(dispo=False, essai=False, fr="Vraie CPS-2 avec carte fille à banques",
                         en="Real CPS-2 with a banked daughterboard"),
}
JEUX_NOMS = {"sfa3": "Street Fighter Alpha 3", "upper": "SFA3 Upper", "uppermax": "SFA3 Upper MAX",
             "hyper": "Hyper Street Fighter Alpha", "hyperarcade": "Hyper + mode Arcade d'Upper"}
JEUX_NOMS_EN = dict(JEUX_NOMS, hyperarcade="Hyper + Upper's Arcade mode")
TOUS = tuple(JEUX_NOMS)
UPPER_ET_MAX = ("upper", "uppermax")
HYPERS = ("hyper", "hyperarcade")
AVEC_FLUX = UPPER_ET_MAX + HYPERS


def langue_defaut():
    """fr ou en : HSFA_LANGUE, sinon la langue du systeme (francais -> fr, tout le reste -> en)"""
    v = os.environ.get("HSFA_LANGUE", "").strip().lower()
    if v in ("fr", "en"):
        return v
    noms = [os.environ.get(k, "") for k in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")]
    try:
        noms.append(locale.getlocale()[0] or "")              # Windows : « French_France »
    except Exception:
        pass
    for n in noms:
        if n and n not in ("C", "POSIX", "C.UTF-8"):
            return "fr" if n.lower().startswith("fr") else "en"
    return "en"


def libelle(cible, langue="fr"):
    """nom du format pour un menu, avec la mention « bilan seulement » s'il ne produit rien"""
    c = CIBLES[cible]
    return c[langue] + ("" if c["dispo"] else (" (bilan seulement)" if langue == "fr" else " (report only)"))

# ----------------------------------------------------------------------------------------------------------------------
# Budgets MESURES (zips construits par le script le 2026-11-08 ; programmes, tables, ROM son : budgets/*.py ; 68000 :
# coeur instrumente, saut des boucles coupe, cycles/RESULTATS.md ; plans par decor et union d'un combat : tuiles
# dessinees, cycles/tuiles/RESULTATS.md ; plans d'Hyper mesures dans la greffe, 17 decors). Mo = 2^20 octets.
# ----------------------------------------------------------------------------------------------------------------------
BUDGETS = {
    #           prog occupe / donnees au-dela de 4 Mo / trous ; QSound reference ; Z80 ; flux ; objets pire combat
    "sfa3": dict(plans_decor=0.99, union_combat=1.72, prog=3.93, ext=0.44, trous=0.0, qsound=8.00, z80_ko=256, flux=0, flux_mo=0.0,
                 objets_paire=5.61, objets_borne=10.42, sdram=44.8, cyc_med=72.0, cyc_sat=6.7),
    "upper": dict(plans_decor=0.99, union_combat=1.7, prog=3.97, ext=1.21, trous=0.0, qsound=8.88, z80_ko=288, flux=7, flux_mo=4.9,
                  objets_paire=5.79, objets_borne=14.10, sdram=71.2, cyc_med=74.8, cyc_sat=10.6),
    "uppermax": dict(plans_decor=0.99, union_combat=1.69, prog=3.77, ext=2.81, trous=0.0, qsound=10.29, z80_ko=288, flux=7, flux_mo=4.9,
                     objets_paire=8.84, objets_borne=18.49, sdram=83.7, cyc_med=75.3, cyc_sat=11.4),
    "hyper": dict(plans_decor=1.19, union_combat=1.01, prog=3.95, ext=3.11, trous=0.0, qsound=8.88, z80_ko=288, flux=216, flux_mo=146.5,
                  objets_paire=4.05, objets_borne=6.90, sdram=78.5, cyc_med=68.6, cyc_sat=5.1, rejeu=8.0),
    "hyperarcade": dict(plans_decor=1.19, union_combat=1.78, prog=3.62, ext=5.65, trous=1.16, qsound=8.88, z80_ko=288, flux=216, flux_mo=146.5,
                        objets_paire=5.84, objets_borne=16.96, sdram=93.1, cyc_med=84.3, cyc_sat=15.6, rejeu=8.0),
}
ARCADE_CYC = (64.8, 0.2)        # arcade sfa3ud dans le meme coeur, meme decor : mediane %, images saturees %
LIMITES = {
    "cps2-banques": dict(prog=4.0, fenetre=32.0, plans=8.0, qsound=8.0, z80_ko=256),
    "mister": dict(sdram=128.0),
}

# ----------------------------------------------------------------------------------------------------------------------
# Concessions : (id, cibles, jeux, statut, source, texte fr, texte en)
#   statut : "certain" (decoule d'un patch ou d'une mesure) / "a verifier" (depend d'un point non verifie)
#   source : une chaine (references seules, identique dans les deux langues) ou un couple (fr, en)
# ----------------------------------------------------------------------------------------------------------------------
C = []
def _c(ident, cibles, jeux, statut, source, fr, en):
    sfr, sen = source if isinstance(source, tuple) else (source, source)
    C.append(dict(id=ident, cibles=cibles, jeux=jeux, statut=statut, source=sfr, source_en=sen, fr=fr, en=en))

M_C = ("mister", "cps2-banques")
# --- FBNeo autonome (version d'essai, mesuree : parties pilotees sous Wine contre le coeur libretro, 11/11)
_c("auto_frontal", ("fbneo-autonome",), TOUS, "certain",
   ("patches/fbneo-autonome (W01-W04) ; parties pilotées sous Wine contre le cœur RetroArch (11/11)",
    "patches/fbneo-autonome (W01-W04); games driven under Wine against the RetroArch core (11/11)"),
   "Pas de perte de contenu : mêmes archives, mêmes options (commutateurs DIP, mêmes valeurs par défaut), 16:9 avec "
   "bords et format d'écran dans le menu Vidéo ; image et son identiques au cœur RetroArch. Les sauvegardes d'état de "
   "RetroArch ne se chargent pas dans FinalBurn Neo autonome (formats différents).",
   "No content loss: same archives, same options (DIP switches, same defaults), 16:9 with edges and screen format in "
   "the Video menu; picture and sound identical to the RetroArch core. RetroArch save states do not load in "
   "standalone FinalBurn Neo (different formats).")
# --- communes MiSTer / CPS-2
_c("pas_16_9", ("cps2-banques",), TOUS, "certain", ("patchs widescreen, 0012, 0022, 0023", "widescreen patches, 0012, 0022, 0023"),
   "Pas de 16:9 : image 4:3 de la borne (384 × 224).", "No 16:9: arcade 4:3 picture (384 × 224).")
_c("pas_16_9_m", ("mister",), TOUS, "a verifier", ("patchs widescreen, 0012, 0022, 0023", "widescreen patches, 0012, 0022, 0023"),
   "Pas de 16:9 au départ : le cœur de Jotego dessine 384 pixels de large ; passer à 512 est un chantier à part.",
   "No 16:9 at first: Jotego's core draws 384 pixels wide; going to 512 is a separate project.")
_c("options_ps2", ("cps2-banques",), TOUS, "certain", ("0003 (écran OPTION de la PS2 en options du cœur)", "0003 (PS2 OPTION screen as core options)"),
   "Réglages de l'écran OPTION de l'Anthology (difficulté, dégâts, minuteur, vitesse, manches, EXTRA OPTION) : valeurs "
   "par défaut du jeu, non réglables.",
   "Anthology OPTION screen settings (difficulty, damage, timer, speed, rounds, EXTRA OPTION): game defaults, not "
   "adjustable.")
_c("options_ps2_m", ("mister",), TOUS, "a verifier", "0003",
   "Réglages de l'écran OPTION : seulement si le menu du cœur (OSD) les écrit en mémoire, ce qui reste à programmer ; "
   "sinon, valeurs par défaut.",
   "OPTION screen settings: only if the core's on-screen menu (OSD) writes them to memory, which is still to be "
   "written; otherwise, defaults.")
_c("sang", M_C, TOUS, "certain", "0018 (option Blood)",
   "Sang rouge ou blanc : choisi à la construction (rouge par défaut), pas en jeu.",
   "Red or white blood: chosen at build time (red by default), not in game.")
_c("ombres", ("cps2-banques",), TOUS, "certain", ("0011 (ombres transparentes de la PSP)", "0011 (PSP-style translucent shadows)"),
   "Ombres opaques, comme sur la borne (pas d'ombres transparentes façon PSP).",
   "Opaque shadows, as on the arcade board (no PSP-style translucent shadows).")
_c("ombres_m", ("mister",), TOUS, "a verifier", "0011",
   "Ombres transparentes façon PSP : seulement si le mélange des couleurs est ajouté au cœur ; sinon, opaques comme sur "
   "la borne.",
   "PSP-style translucent shadows: only if colour blending is added to the core; otherwise, opaque as on the arcade "
   "board.")
_c("provocation_m", ("mister",), TOUS, "a verifier", ("0014 (provocation sur Select)", "0014 (taunt on Select)"),
   "Provocation : seulement si le cœur FPGA contourne le défaut du portage comme le cœur HSFA, ou si le traducteur "
   "le corrige ; sinon, impossible.",
   "Taunt: only if the FPGA core works around the PS2 port's defect as the HSFA core does, or if the translator fixes "
   "it; otherwise, impossible.")
_c("provocation", ("cps2-banques",), TOUS, "certain", ("0014 (provocation sur Select)", "0014 (taunt on Select)"),
   "Provocation : impossible (défaut du portage PS2 que seul le cœur HSFA contourne), sauf correctif du traducteur, "
   "à écrire.",
   "Taunt: impossible (a PS2 port defect that only the HSFA core works around), unless the translator gets a fix, "
   "still to be written.")
_c("roulette", ("cps2-banques",), ("upper", "uppermax", "hyper", "hyperarcade"), "certain", "0007 (Hyper), 0016 (Upper)",
   "Sélection : Start tenu sur la grille lance la roulette (personnage au hasard). Les choix faits avec Start (Shin "
   "Akuma, EX Balrog ; versions EX et S-ISM d'Hyper) deviennent aléatoires, sauf correctif du traducteur, à écrire.",
   "Character select: holding Start on the grid spins the roulette (random character). Start-based picks (Shin Akuma, "
   "EX Balrog; Hyper's EX and S-ISM versions) become random, unless the translator gets a fix, still to be written.")
_c("lenteurs", M_C, TOUS, "certain", ("mesure : cycles du 68000 par image (work/multi_cibles/cycles)",
   "measured: 68000 cycles per frame (work/multi_cibles/cycles)"),
   "Ralentissements possibles en combat : la traduction utilise {cyc_med} % du temps du 68000 (médiane), contre "
   "{arc_med} % pour la borne, et {cyc_sat} % des images sont saturées (borne : {arc_sat} %). La carte réelle a des "
   "temps d'attente que FBNeo ne compte pas : la marge y sera plus mince.",
   "Possible slowdowns in fights: the translation uses {cyc_med}% of the 68000's time (median), against {arc_med}% for "
   "the arcade game, and {cyc_sat}% of frames are saturated (arcade: {arc_sat}%). Real hardware has wait states that "
   "FBNeo does not count: the margin will be thinner there.")
_c("port_ram", M_C, TOUS, "a verifier", ("carte 68K du programme traduit ($F00000-$FAFFFF non décodé, coeur-fbneo.md §5.3)",
   "68K memory map of the translated program ($F00000-$FAFFFF not decoded, coeur-fbneo.md §5.3)"),
   "Le programme lit des variables du portage dans une zone que la carte ne décode pas (le cœur y rend 0) : "
   "comportement à vérifier sur la cible (risque de blocage).",
   "The program reads port variables in an area the board does not decode (the core returns 0 there): behaviour to "
   "be checked on the target (risk of a hang).")
# --- SFA3
_c("codes_tuiles", ("cps2-banques",), TOUS, "certain", ("patch de base (HsfaEclater, plans) ; inventaire_patchs.md §3",
   "base patch (HsfaEclater, planes); inventaire_patchs.md §3"),
   "Pas encore possible : le programme traduit écrit des codes de tuiles du portage PS2 (objets et décors) que seul le "
   "cœur HSFA convertit. Il faut d'abord que le traducteur écrive des codes que la carte comprend (codes de la borne "
   "pour SFA3 ; emplacement et rang servis par la carte à banques pour les autres jeux).",
   "Not possible yet: the translated program writes PS2-port tile codes (sprites and stages) that only the HSFA core "
   "converts. The translator must first emit codes the board understands (arcade codes for SFA3; slot and index "
   "served by the banked daughterboard for the other games).")
# --- Upper, MAX, Hyper : musique en flux
_c("flux_upper", ("cps2-banques",), UPPER_ET_MAX, "certain", ("patchs ws-flux, 0004, 0005 ; mesure : 7 flux (4,9 Mo)",
   "ws-flux patches, 0004, 0005; measured: 7 streams (4.9 MB)"),
   "Les 7 musiques qui n'existent que sur le disque PS2 (dont le thème du décor de Guile) ne sont pas en QSound : un "
   "thème existant les remplace (à choisir), ou bien silence.",
   "The 7 tracks that only exist on the PS2 disc (Guile's stage theme among them) are not in QSound: an existing theme "
   "plays instead (to be chosen), or silence.")
_c("flux_upper_m", ("mister",), UPPER_ET_MAX, "a verifier", "ws-flux, 0004, 0005",
   "Les 7 musiques du disque PS2 : seulement si le cœur gagne un lecteur de flux depuis la carte SD (PCM, comme le "
   "MSU-1 du cœur SNES) ; sinon, comme sur CPS-2 (thème existant ou silence).",
   "The 7 PS2-disc tracks: only if the core gains a stream player reading from the SD card (PCM, like the SNES core's "
   "MSU-1); otherwise, as on CPS-2 (existing theme or silence).")
_c("son_upper", ("cps2-banques",), UPPER_ET_MAX + HYPERS, "a verifier", ("mesure : table des échantillons du Z80 hybride",
   "measured: sample table of the hybrid Z80 program"),
   "Son : {qsound} Mo d'échantillons pour 8 Mo câblés. Il faut une banque son sur la carte fille (lignes au-delà de "
   "8 Mo à vérifier) ; sinon, des musiques d'Alpha 3 perdent des instruments.",
   "Sound: {qsound} MB of samples for 8 MB wired. A sound bank is needed on the daughterboard (lines above 8 MB to be "
   "checked); otherwise, some Alpha 3 tunes lose instruments.")
_c("z80", ("cps2-banques",), UPPER_ET_MAX + HYPERS, "a verifier", ("mesure : hx3.02 occupe les banques 14 et 15 du Z80",
   "measured: hx3.02 uses Z80 banks 14 and 15"),
   "Programme son de 288 Ko pour 256 Ko sur la carte : support plus grand ou carte fille (câblage à vérifier).",
   "288 KB sound program for 256 KB on the board: bigger socket or daughterboard (wiring to be checked).")
_c("max_effets", ("cps2-banques",), ("uppermax",), "certain", ("0010 (mélange des objets)", "0010 (sprite blending)"),
   "Effets des personnages MAX opaques (aucune transparence sur CPS-2).",
   "MAX characters' effects are opaque (no blending on CPS-2).")
_c("max_effets_m", ("mister",), ("uppermax",), "a verifier", "0010",
   "Effets des personnages MAX transparents seulement si le mélange est ajouté au cœur ; sinon, opaques.",
   "MAX characters' effects are translucent only if blending is added to the core; otherwise, opaque.")
# --- Hyper
_c("hyper_son", ("cps2-banques",), HYPERS, "certain", ("0001 (rejeu), 0006 (carte musique), flux (216 musiques, 146,5 Mo)",
   "0001 (replay), 0006 (music map), streams (216 tracks, 146.5 MB)"),
   "Hyper avec le son d'Upper : thèmes et voix d'Alpha 3 pour toutes les versions. Plus de musiques propres à chaque "
   "version (arrangements de SF2, d'Alpha, d'Alpha 2), plus de voix par version, plus de thèmes en flux pour les "
   "personnages console d'Upper.",
   "Hyper with Upper's sound: Alpha 3 themes and voices for every version. No per-version music (SF2, Alpha and "
   "Alpha 2 arrangements), no per-version voices, no streamed themes for Upper's console characters.")
_c("hyper_son_m", ("mister",), HYPERS, "a verifier", ("0001, 0006, flux", "0001, 0006, streams"),
   "Musiques propres à chaque version : seulement avec un lecteur de flux depuis la carte SD (à écrire). Voix par "
   "version : seulement si un 2e QSound tient dans le FPGA. Partitions de SFA1 et SFA2 par leur pilote d'origine "
   "(carte musique) : non (il faudrait 3 QSound). Sinon, son d'Upper comme sur CPS-2.",
   "Per-version music: only with a stream player reading from the SD card (to be written). Per-version voices: only "
   "if a 2nd QSound fits in the FPGA. SFA1 and SFA2 scores through their original driver: no (that would take 3 "
   "QSound chips). Otherwise, Upper's sound as on CPS-2.")

# Prerequis materiels (ce qu'il faut avoir, pas ce qu'on perd)
P = []
def _p(cible, jeux, statut, fr, en):
    P.append(dict(cibles=(cible,), jeux=jeux, statut=statut, fr=fr, en=en))
_p("cps2-banques", TOUS, "a verifier", "Carte B de CPS-2 à clé neutre (Phoenix ou clé reprogrammée).",
   "CPS-2 B board with a neutral key (Phoenix or reprogrammed key).")
_p("cps2-banques", ("upper", "uppermax", "hyper", "hyperarcade"), "a verifier",
   "Carte fille à banques sur CN5/CN6 et CN7 (graphismes, son) et petite carte sur les supports du programme (données "
   "au-delà de 4 Mo) : à concevoir et à fabriquer.",
   "Banked daughterboard on CN5/CN6 and CN7 (graphics, sound) and a small board on the program sockets (data above "
   "4 MB): to be designed and built.")
_p("mister", TOUS, "certain", "Cœur CPS-2 de Jotego étendu (blocs externes, conversion des objets, banques, son de "
   "16 Mo) : n'existe pas.",
   "Extended Jotego CPS-2 core (external blocks, sprite conversion, banks, 16 MB sound): does not exist.")
_p("mister", ("upper", "uppermax", "hyper", "hyperarcade"), "certain",
   "Barrette SDRAM de 128 Mo (besoin mesuré : {sdram} Mo une fois la ROM étendue tassée).",
   "128 MB SDRAM module (measured need: {sdram} MB once the extended ROM is packed).")
_p("fbneo-autonome", TOUS, "certain", "FinalBurn Neo HSFA autonome (fbneo64.exe ou fbneo64ws.exe, Windows 64 bits) : "
   "version d'essai construite (patches/fbneo-autonome), pas encore publiée.",
   "Standalone FinalBurn Neo HSFA (fbneo64.exe or fbneo64ws.exe, 64-bit Windows): test build made "
   "(patches/fbneo-autonome), not released yet.")


def _n(x, k="fr", f="%.1f"):
    s = f % x if isinstance(x, (int, float)) else str(x)
    return s.replace(".", ",") if k == "fr" else s


def _fmt(t, jeu, k="fr"):
    b = BUDGETS.get(jeu, {})
    return t.format(cyc_med=_n(b.get("cyc_med", "?"), k), cyc_sat=_n(b.get("cyc_sat", "?"), k),
                    arc_med=_n(ARCADE_CYC[0], k), arc_sat=_n(ARCADE_CYC[1], k),
                    qsound=_n(b.get("qsound", "?"), k, "%.2f"), sdram=_n(b.get("sdram", "?"), k))


def concessions(cible, jeu):
    return [c for c in C if cible in c["cibles"] and jeu in c["jeux"]]


def prerequis(cible, jeu):
    return [p for p in P if cible in p["cibles"] and jeu in p["jeux"]]


def ligne_budget(cible, jeu, k="fr"):
    """budgets mesures face aux limites de la cible (texte court, une ligne par grandeur)"""
    b = BUDGETS[jeu]; L = []; n = lambda x, f="%.2f": _n(x, k, f)
    fr = k == "fr"
    if cible == "cps2-banques":
        L.append(("programme : %s Mo, plus %s Mo de données au-delà%s (carte : 4 Mo)" if fr else
                  "program: %s MB, plus %s MB of data beyond%s (board: 4 MB)") % (
            n(b["prog"]), n(b["ext"]), ((", dont %s Mo dans les trous" if fr else ", %s MB of it in the holes") % n(b["trous"]))
            if b["trous"] else ""))
        L.append(("graphismes d'un combat : objets du commun et des 2 personnages (tables complètes) %s Mo, décor "
                  "jusqu'à %s Mo ; dessiné en jeu : jusqu'à %s Mo (fenêtre : 32 Mo, plans : 8 Mo)" if fr else
                  "graphics of one fight: common and 2-character sprites (full tables) %s MB, stage up to %s MB; drawn "
                  "in game: up to %s MB (window: 32 MB, planes: 8 MB)") % (n(b["objets_paire"], "%.1f"),
                 n(b["plans_decor"], "%.1f"), n(b["union_combat"], "%.1f")))
        L.append(("son QSound : %s Mo (carte : 8 Mo) ; programme son : %d Ko (carte : 256 Ko) ; musiques en flux : %d (%s Mo)"
                  if fr else "QSound: %s MB (board: 8 MB); sound program: %d KB (board: 256 KB); streamed tracks: %d (%s MB)")
                 % (n(b["qsound"]), b["z80_ko"], b["flux"], n(b["flux_mo"], "%.1f"))
                 + (((" ; 2e QSound : %s Mo" if fr else "; 2nd QSound: %s MB") % n(b["rejeu"], "%.0f")) if b.get("rejeu") else ""))
    elif cible == "mister":
        L.append(("mémoire : %s Mo une fois tassée (SDRAM : 32, 64 ou 128 Mo) ; musiques en flux : %d (%s Mo)" if fr else
                  "memory: %s MB once packed (SDRAM: 32, 64 or 128 MB); streamed tracks: %d (%s MB)")
                 % (n(b["sdram"], "%.1f"), b["flux"], n(b["flux_mo"], "%.1f")))
    if cible in ("cps2-banques", "mister"):
        L.append(("68000 en combat : %s %% du budget (médiane), %s %% d'images saturées (borne : %s %% et %s %%)" if fr else
                  "68000 in fights: %s%% of the budget (median), %s%% saturated frames (arcade: %s%% and %s%%)")
                 % (n(b["cyc_med"], "%.1f"), n(b["cyc_sat"], "%.1f"), n(ARCADE_CYC[0], "%.1f"), n(ARCADE_CYC[1], "%.1f")))
    return L


def insecables(s, langue="fr"):
    """espaces insecables (U+00A0, dans cp1252) : nombre et unite ; en francais, avant « : ; ? ! » et dans les
    guillemets. textwrap ne coupe pas a U+00A0 : pas de « 8 » en fin de ligne et « Mo » au debut de la suivante"""
    s = re.sub(r"(\d) (Mo|Ko|MB|KB|%|×)", "\\1\u00a0\\2", s)
    s = re.sub(r"× (\d)", "×\u00a0\\1", s)
    s = s.replace("[to be checked]", "[to\u00a0be\u00a0checked]").replace("[à vérifier]", "[à\u00a0vérifier]")
    if langue == "fr":
        s = re.sub(r" ([:;?!»])", "\u00a0\\1", s).replace("« ", "«\u00a0")
    return s


def rapport(cible, jeux, langue="fr"):
    """texte de l'annonce : concessions par jeu, prerequis, budgets ; une chaine"""
    k = "fr" if langue == "fr" else "en"
    fr = k == "fr"
    t = CIBLES[cible]
    out = []
    titre = insecables(("Format de sortie : %s" if fr else "Output format: %s") % t[k], k)
    out += [titre, "=" * len(titre)]
    if cible == DEFAUT:
        out.append("Sortie actuelle du projet : aucune concession." if fr else "Current project output: no concession.")
        return "\n".join(out)
    if not t["dispo"]:
        out.append(insecables("Format pas encore disponible : mode bilan (rien n'est construit)." if fr
                   else "Format not available yet: report mode (nothing is built).", k))
    elif t["essai"]:
        out.append(insecables("Format disponible en essai : les archives produites sont celles de FinalBurn Neo HSFA, à l'octet."
                   if fr else "Format available as a test build: the archives produced are those of FinalBurn Neo "
                   "HSFA, byte for byte.", k))
    W = lambda s, ind: textwrap.fill(insecables(s, k), 96, initial_indent=ind, subsequent_indent=" " * len(ind))
    noms = JEUX_NOMS if fr else JEUX_NOMS_EN
    a_verifier = " [à vérifier]" if fr else " [to be checked]"
    corps = {}                                            # texte par jeu ; des jeux au texte identique sont groupes
    for j in jeux:
        L = []
        cs = concessions(cible, j)
        if not cs:
            L.append("  - " + ("aucune concession connue" if fr else "no known concession"))
        for c in cs:
            marque = "" if c["statut"] == "certain" else a_verifier
            L.append(W(_fmt(c[k], j, k) + marque, "  - "))
            L.append(W("source : " + c["source"] if fr else "source: " + c["source_en"], "      "))
        for p in prerequis(cible, j):
            marque = "" if p["statut"] == "certain" else a_verifier
            L.append(W(("Il faut : " if fr else "Requires: ") + _fmt(p[k], j, k) + marque, "  * "))
        for l in ligne_budget(cible, j, k):
            L.append(W(("mesure : " if fr else "measured: ") + l, "  . "))
        corps.setdefault("\n".join(L), []).append(j)
    for texte, js in corps.items():
        out.append("")
        if len(js) > 1 and len(js) == len(jeux):
            out.append(("Tous les jeux (%s)" if fr else "All games (%s)") % ", ".join(js))
        else:
            out.append(W(", ".join("%s (%s)" % (noms.get(j, j), j) for j in js), ""))
        out.append(texte)
    return "\n".join(out)


def table(langue="fr"):
    """table cible x jeu (identifiants des concessions), pour le RAPPORT"""
    lignes = ["| cible | " + " | ".join(TOUS) + " |", "|---|" + "---|" * len(TOUS)]
    for cb in CIBLES:
        cases = []
        for j in TOUS:
            ids = [c["id"] + ("?" if c["statut"] != "certain" else "") for c in concessions(cb, j)]
            cases.append(", ".join(ids) or "aucune")
        lignes.append("| %s | %s |" % (cb, " | ".join(cases)))
    return "\n".join(lignes)


def question(langue="fr"):
    return ("Confirmer ce format malgré ces concessions ? (o/N) " if langue == "fr"
            else "Confirm this format despite these concessions? (y/N) ")


def confirme(cible, jeux, oui=False, demande=input, ecrit=print, langue=None):
    """annonce (toujours) puis demande ; True = l'utilisateur accepte. Sans terminal et sans --oui : refus."""
    langue = langue or langue_defaut()
    ecrit(rapport(cible, jeux, langue))
    if cible == DEFAUT:
        return True
    if oui:
        ecrit("(confirmé par --oui)" if langue == "fr" else "(confirmed by --oui)"); return True
    if not sys.stdin or not sys.stdin.isatty():
        ecrit("Pas de terminal : relancer avec --oui pour confirmer." if langue == "fr"
              else "No terminal: run again with --oui (or --yes) to confirm.")
        return False
    r = demande("\n" + question(langue)).strip().lower()
    return r in ("o", "oui", "y", "yes")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="concessions par format de sortie (HSFA)")
    ap.add_argument("--cible", choices=list(CIBLES), default=None)
    ap.add_argument("--jeux", default=",".join(TOUS))
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--en", action="store_true")
    ap.add_argument("--fr", action="store_true")
    a = ap.parse_args()
    lg = "en" if a.en else "fr" if a.fr else langue_defaut()
    if a.table:
        print(table(lg)); sys.exit(0)
    for cb in ([a.cible] if a.cible else list(CIBLES)):
        print(rapport(cb, [j for j in a.jeux.split(",") if j], lg)); print()
