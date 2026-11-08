#!/usr/bin/env python3
"""Profil de module ro9 (et rappel ro3/ro5) : toutes les constantes que l'outillage ro3 code en dur, avec leur
homologue etabli par cette cartographie (voir CARTE-ro9.md). Ecrit profil_module_ro9.json (adresses 'fichier'
pour le code, 'execution' pour les tables de donnees, comme dans mame_test.py / translate.py)."""
import json, os
P = {
 "module": "ro9", "fichier": "ro9_usa_prog68k.bin", "nom_interne": "zero9_usa.bin",
 "base_ram": "0xB80000", "A5": "0xB88000",
 "z80_fin": "0x22B00", "natif_chargeur_debut": "0x22B00", "aides_debut": "0x22DC0", "c0_outillage": "0x22DE0",
 "code_fin_entete_plus12": "0x3BF140", "code_fin_reelle": "0x3BF180", "donnees_fichier": ["0x3BF180", "0x977200"],
 "donnees_execution": ["0x5AF180", "0xB67200"],
 "va_reset": "0x3DA00", "va_init": "0x3EC20", "va_frame": "0x3EE30", "vbl_fonction": "0x3F1B0", "vbl_contient": "0x3F224",
 "rts_sauvegarde_registres": ["0x3FE50", "0x40080"],
 "aides_recomp_execution": {"0x212DC0": "movem_push", "0x213120": "movem_pop", "0x213480": "andi_ccr", "0x213610": "abcd"},
 "btst_rendu_appelant_execution": "0x214400",
 "reecritures_main": {"REMPL": ["0x38AF40", "0x38AFF8"], "BCD": ["0x38B070", "0x38B2E8"],
                      "R1": ["0x315AC0", "0x315C34", "table 0x640960"], "R2": ["0x315F00", "0x316060", "table 0x643C60"],
                      "DEF (a refaire, routine modifiee)": ["0x392008", "0x392264"]},
 "intro_ticks_0x4A830": None, "intro_table_0x585750": None,
 "manette_natif": "0x23D20", "manette_sites": {"0x38A958": [1, "0x58", "0x51A"], "0x38A97C": [2, "0x5C", "0x91A"]},
 "natifs_identiques_ro5": {"manette": "0x24080", "remappage/directions": "0x241B0", "attente_image": "0x3BA5C0"},
 "chargeur_natif_unique": {"fonction": "0x22B00", "sites": ["0x970BC", "0x31AF78", "0x31AFA4"],
                           "table_u16_par_id_etendu_execution": "0x5AF2B0", "variable_pointeur": "$C0BC(A5) (ro3 $BE48)"},
 "positions_adresse_fixe_ro9": "pointeurs vers 0xC80000-0xD0FFFE (a identifier ; ro3 fichier 289 en 0xA04000)",
 "menu_modes": {"aiguillage_sll2": "0x62FC0", "routine": "0x62B30", "table_lanceurs_execution": "0x5B4210",
                "nav_haut_bas_execution": ["0x5B41F0", "0x5B4200"], "libelles_execution": "0x69CF54",
                "EXIT_site_0x1CAC80": "0x63438", "OPTION_natif": "0x24AB0"},
 "setjmp_longjmp_sites": 6,
 "variables_A5_decalees": {"$C000": "$C200", "$C010": "$C210", "$C012": "$C212", "$C018": "$C218", "$C019": "$C219",
                           "$BE48": "$C0BC", "regle": "+0x200 sur le bloc Anthology $C0xx-$C1xx (65 votes)"},
 "tables_par_perso_execution (128 entrees, index $102)": {"0x67D678": "0x6A6BD4", "0x67D6F8": "0x6A6DD4", "0x67D778": "0x6A6FD4",
     "0x67D878": "0x6A73D4", "0x67FCF8": "0x6AE014", "0x67FD78": "0x6AE214", "0x67FDF8": "0x6AE414", "0x67FE78": "0x6AE614",
     "0x67FEF8": "0x6AE814", "0x5C703C": "0x5F0BDC"},
 "emetteur_frames_table_execution": "0x5CAAF0", "positions_type04_execution": "0x5CA650",
 "perso_banque_execution": "0x5AF1B0", "noms_execution": ["0x5B0A40", "0x5B2570"],
 "versions": {"id_etendu": "$102(An) (PS2) -> $116 = table 0x5C5300, $117/$D3 = table 0x5C2490, fonction 0x321BA0",
              "grille_perso_x_version_execution": "0x5C5380"},
 "stages_execution": {"table_A": "0x660240", "table_B": "0x661E60", "index": "$100(A5)+$C178(A5)"},
 "zone_donnees_versions_execution": ["0x8AF140", "0xB0F140"],
}
json.dump(P, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "profil_module_ro9.json"), "w"), indent=1, ensure_ascii=False)
print("ecrit profil_module_ro9.json")
