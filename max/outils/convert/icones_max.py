"""Icônes de la grille de sélection pour les 4 persos MAX (choix utilisateur 2026-10-07 : à la place des 4 « ? »).
Les icônes PSP (select_e.pac jeu 2, frames 51-54) sont IDENTIQUES au format d'Upper : visage 22x22 dans un bloc 2x2
tuiles (32x32, marge 5), mêmes numéros de palette d'icône (Ryu 10 = $0A chez Upper, etc. ; vérifié pixel à pixel sur
Ryu). Donc aucune réduction : copie 1:1, palette $0F (Eagle, Maki) / $0C (Yun, Ingrid), déjà chargées par Upper.
Sortie ~/.cache/sfa3max/converti/icones/ : icones.bin (2 rangées de 16 tuiles brutes CPS2 ; icône k = tuiles 2k, 2k+1,
16+2k, 16+2k+1) et icones.json (entrée de la liste d'icônes d'Upper à remplacer, position, attribut)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portraits_max import charger, tuiles_calque, D
# perso : (ID, frame PSP, palette d'icône, entrée de la liste d'icônes 0x772B30 (fichier ro5), case (rangée, colonne))
ICONES = {"pl26": (0x26, 51, 0x0F, 33, (0, 2)), "pl27": (0x27, 52, 0x0F, 35, (0, 4)),
          "pl28": (0x28, 53, 0x0C, 34, (6, 4)), "pl29": (0x29, 54, 0x0C, 36, (6, 2))}
def main():
    sel = charger(D + "select_e.pac", (3, 4, 2)); tuiles = [None] * 32; info = {}
    for k, (pl, (ID, n, pal, ent, (r, c))) in enumerate(ICONES.items()):
        T = tuiles_calque(sel, n, 0)
        pals = {p for _, p in T.values()}; assert pals == {pal}, (pl, pals)
        for (cx, cy), (px, _) in T.items(): tuiles[16 * cy + 2 * k + cx] = px
        info[pl] = {"id": ID, "frame_psp": n, "code_local": 2 * k, "attribut": 0x1100 | pal,
                    "palette": "$%02X d'Upper (= palette %d de select_e.pac, déjà chargée)" % (pal, pal),
                    "entree_liste_icones": ent, "liste": "fichier ro5 0x772B30 (type $10, 37 entrées code u16 + attribut u16 à 0x772B3C)",
                    "case": [r, c], "position_bloc": [-88 + 24 * c, -88 + 24 * r]}
    d = os.path.expanduser("~/.cache/sfa3max/converti/icones"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "icones.bin"), "wb") as f:
        for t in tuiles:
            raw = [15 - ((16 - i) % 16) for i in (t or [0] * 256)]
            f.write(bytes(raw[2 * j] | (raw[2 * j + 1] << 4) for j in range(128)))
    json.dump(info, open(os.path.join(d, "icones.json"), "w"), indent=1)
    print(json.dumps(info, indent=1, ensure_ascii=False)[:1200])
if __name__ == "__main__":
    main()
