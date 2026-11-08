#!/usr/bin/env python3
"""Tables par perso et tables de reference de ro3 -> homologues ro5 / ro9 (par les sites qui forment leur adresse)."""
import json, os, struct, collections
import commun as C, tables_ref as R

T3 = [  # (execution ro3, nom, source)
 (0x67D678, "par perso : 3 pointeurs/ism -> en-tete de 5 decalages (boites) -> $60", "reponse-hsfa-collisions"),
 (0x67D6F8, "par perso : jeux de boites de corps -> $88", "idem"),
 (0x67D778, "par perso : entrees 4 o (mot A bits 16-23) -> $C0", "idem"),
 (0x67D878, "par perso : positions de prise/projection", "idem"),
 (0x67FCF8, "par perso : objets attaches -> $40", "idem"),
 (0x67FD78, "par perso : apparition effets (dx,dy) 1", "idem"),
 (0x67FDF8, "par perso : apparition effets (dx,dy) 2", "idem"),
 (0x67FE78, "par perso : boites supplementaires -> $E6", "idem"),
 (0x67FEF8, "par perso : effets lies au pas -> $264", "idem"),
 (0x5C703C, "table des effets (via 0x48FEF8)", "idem"),
 (0x58BC30, "emetteur de frames : aiguillage par TYPE (16 entrees)", "frames-anthology-emetteur"),
 (0x58B790, "positions fixes des frames type 04/06", "frames-anthology-emetteur"),
 (0x59C0B0, "perso -> banque de sprites X_DATA (u16)", "HANDOFF §51"),
 (0x59C130, "chargeur natif : (gfx, anim) par perso", "assets_natifs.py"),
 (0x59C1B0, "chargeur natif : (gfx, anim) par site", "assets_natifs.py"),
 (0x59C030, "natif nettoyage des directions opposees", "HANDOFF §90"),
 (0x5854A0, "aiguillage du menu des modes (longs, index sll 2)", "HANDOFF §102"),
 (0x5855C0, "table de ticks de l'intro", "HANDOFF §103"),
 (0x585750, "objets de l'intro (type, parametre)", "HANDOFF §103"),
 (0x61F3F0, "tables de tuiles de l'intro (R1)", "mame_test.py"),
 (0x63A9F0, "tables de tuiles de l'intro (R2)", "mame_test.py"),
]

def main():
    out = []
    for X, nom, src in T3:
        row = dict(ro3=X, nom=nom, source=src, sites_ro3=len(R.sites('ro3', X)))
        for d in ('ro5', 'ro9'):
            v, det = R.homologue_table('ro3', X, d)
            row[d] = [(k, n) for k, n in v.most_common(3)]
            row[d + '_classes'] = collections.Counter(c for _, c, _, _, _ in det if c).most_common(3)
        # passage par ro5 si direct vide
        if not row['ro9'] and row['ro5']:
            v, _ = R.homologue_table('ro5', row['ro5'][0][0], 'ro9'); row['ro9_par_ro5'] = [(k, n) for k, n in v.most_common(3)]
        out.append(row)
        print("%-9s %-58s sites %2d | ro5 %-22s | ro9 %-22s %s" % (C.h(X), nom[:58], row['sites_ro3'],
              ' '.join('%s×%d' % (C.h(k), n) for k, n in row['ro5'][:2]),
              ' '.join('%s×%d' % (C.h(k), n) for k, n in row['ro9'][:2]),
              ('(par ro5 : %s)' % ' '.join('%s×%d' % (C.h(k), n) for k, n in row.get('ro9_par_ro5', []))) if 'ro9_par_ro5' in row else ''))
    json.dump(out, open(os.path.join(C.OUT, "tables_perso.json"), "w"), indent=1, default=lambda o: hex(o) if isinstance(o, int) else str(o))

if __name__ == "__main__":
    main()
