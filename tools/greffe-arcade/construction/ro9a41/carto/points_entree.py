#!/usr/bin/env python3
"""Points d'entree et sites de ro3 utilises par l'outillage (mame_test.py, translate.py, assets_natifs.py, HANDOFF)
-> homologues dans ro5 et ro9 (direct, et par la chaine ro3 -> ro5 -> ro9)."""
import json, os
import commun as C
import homologue as H

PTS = [  # (adresse fichier ro3, role, source)
 (0x926b0, "reset porte (va_reset)", "mame_test.py"),
 (0x2ed20, "initialisation, 1re tache (VA_INIT)", "mame_test.py"),
 (0x2ef30, "tache du jeu par image (ctx+16)", "mame_test.py"),
 (0x2f310, "gestionnaire VBL porte (contient 0x2f310)", "mame_test.py"),
 (0x2ff00, "sauvegarde registres 68K du bloc de tache", "mame_test.py"),
 (0x30130, "restauration registres 68K du bloc de tache", "mame_test.py"),
 (0x898e0, "remplissage (MOVEM recompile) reecrit a la main", "mame_test.py §103"),
 (0x89a10, "binaire -> BCD (scores) reecrit a la main", "mame_test.py §104"),
 (0x10dd50, "recopie tilemap intro (flux d'octets) R1", "mame_test.py §103"),
 (0x10e200, "recopie tilemap intro (flux d'octets) R2", "mame_test.py §103"),
 (0xf72d8, "table de defilement par ligne (combat)", "mame_test.py §104"),
 (0x4a830, "tick de l'intro (table de ticks 0x5855C0)", "mame_test.py §103"),
 (0x4a848, "  - debut du correctif repere musique", "mame_test.py §103"),
 (0x4cc2c, "creation objets intro (lb 0x1129, table 0x585750)", "HANDOFF §103"),
 (0x485a4, "aiguillage du menu des modes (sll 2, table 0x5854A0)", "HANDOFF §102"),
 (0x89228, "site couche manette J1", "mame_test.py"),
 (0x8924c, "site couche manette J2", "mame_test.py"),
 (0x89494, "fin de liste d'objets (page $9621A0)", "HANDOFF §48"),
 (0x1e1a68, "init perso : tables par perso (0x48D678...)", "reponse-hsfa-collisions"),
 (0x1020e8, "emetteur de frames (table 0x58BC30)", "frames-anthology-emetteur"),
 (0x105814, "emetteur de frames type 08 (decor)", "HANDOFF §103"),
 (0x336358, "allocateur d'objets", "translate.py §86"),
 (0x4708c, "appel natif 0x383700 index 0 (intro)", "assets_natifs.py"),
 (0x1ff008, "appel natif 0x383700 index 1", "assets_natifs.py"),
 (0x20f3a4, "appel natif 0x3837d0 (perso, octet $132)", "assets_natifs.py"),
 # natives du module (C du portage)
 (0x381410, "natif : couche manette", "mame_test.py"),
 (0x381770, "natif : manette", "HANDOFF §101"),
 (0x381900, "natif : remappage", "HANDOFF §101"),
 (0x383700, "natif : chargeur table d'animation (site)", "assets_natifs.py"),
 (0x3837d0, "natif : chargeur table d'animation (perso)", "assets_natifs.py"),
 (0x383e20, "natif : tache OPTION (appelle 0x118A60)", "HANDOFF §102"),
 (0x383c90, "etat 1 du libelle du menu (68K, classe natif a tort)", "HANDOFF §101"),
 (0x392fd0, "etat du (R) du menu", "HANDOFF §101"),
 (0x38dff0, "retraduite (classee native a tort)", "HANDOFF §101"),
 (0x38ec10, "retraduite (classee native a tort)", "HANDOFF §101"),
 (0x571900 - 0x1f0000, "natif : nettoyage directions opposees (table $59C030)", "HANDOFF §90"),
 (0x583b20 - 0x1f0000, "natif : attente d'image", "HANDOFF §55"),
 # aides du recompilateur (translate.AIDES_RECOMP, adresses d'execution ro3)
 (0x570360 - 0x1f0000, "aide recompilateur movem_push", "translate.py"),
 (0x5706c0 - 0x1f0000, "aide recompilateur movem_pop", "translate.py"),
 (0x570a20 - 0x1f0000, "aide recompilateur andi_ccr", "translate.py"),
 (0x570d00 - 0x1f0000, "aide recompilateur abcd", "translate.py"),
 (0x57a4b0 - 0x1f0000, "petite fonction BTST rendu a l'appelant", "translate.py §87"),
]

def main():
    out = []
    for va, role, src in PTS:
        f3 = C.func_of('ro3', va)
        r5 = H.homologue('ro3', va, 'ro5'); r9 = H.homologue('ro3', va, 'ro9')
        r59 = H.homologue('ro5', r5['va_dst'] or r5['partenaire'], 'ro9') if r5 and r5['partenaire'] is not None else None
        nat = C.is_native(C.seg('ro3', *f3))[0]
        row = dict(ro3=va, role=role, source=src, ro3_fonction=f3[0], natif=nat,
                   ro5=r5, ro9_direct=r9, ro9_par_ro5=r59)
        out.append(row)
        def fmt(r):
            if not r: return "-"
            return "%s [%s %.2f] fn %s" % (hex(r['va_dst']) if r['va_dst'] is not None else '?', r['classe'][:12], r['score'],
                                         hex(r['partenaire']) if r['partenaire'] is not None else '?')
        print("%-8x %-48s | ro5 %s | ro9 %s | ro9 via ro5 %s" % (va, role[:48], fmt(r5), fmt(r9), fmt(r59)))
    json.dump(out, open(os.path.join(C.OUT, "points_entree.json"), "w"), indent=1, default=lambda o: hex(o) if isinstance(o, int) else str(o))

if __name__ == "__main__":
    main()
