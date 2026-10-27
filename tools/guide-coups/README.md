# Tableau des coups d'après le guide BradyGames (Street Fighter Alpha Anthology)

Outils qui ont servi à transformer le guide officiel scanné (PDF de 291 pages, sans texte) en **tableau, une ligne par coup**,
pour tester les coups d'Hyper (session « HSFA PS2 CPS2 »). **Aucune donnée du guide dans le dépôt** (texte protégé) : le PDF et
le tableau des coups restent dans un dossier de travail désigné par la variable `GUIDE`. Le relevé ne garde que les
commandes et les numéros de page, jamais le texte du guide.

Colonnes du tableau (`;`) : `jeu;mode;personnage;version_style;type;nom_du_coup;manipulation;boutons;conditions;page_pdf`
(flèches Unicode pour un perso tourné vers la droite ; charge notée `← (charge) →` ; conditions en français).

## Chaîne

1. `pdftoppm -r 130 -png manuel.pdf $GUIDE/p/p` : pages en images ; `zoom.sh <page> x0 y0 x1 y1` : zone à 300 dpi (flèches).
2. Relevé des commandes par lots de ~24 pages (`consigne_transcription.md` : commandes et numéros de page seulement,
   aucun texte du guide) → tableau des coups (`consigne_tableau.md`) → `$GUIDE/csv/*.csv`.
3. `assemble.py` → `coups_sfa_anthology.csv` / `.md`.
4. Vérification contre SuperCombo Wiki (`consigne_verif_supercombo.md`) : pages des persos téléchargées
   (`https://wiki.supercombo.gg/w/<Jeu>/<Perso>`, jeux `Street_Fighter_Alpha`, `_2`, `_3`, `Pocket_Fighter`), icônes de commande
   converties en jetons (`[Qcf]`, `[Hcb]`, `[Cb]`…) → `$GUIDE/verif/*.tsv` (page, perso, coup, champ, ancien, nouveau, cause, source).
5. `applique_verif.py` (corrections + `corrections_supercombo.txt`), puis `finition.py` (doubles quarts de cercle complets en
   Alpha 3, notes « à tester »). Rejouer 3 → 5 après toute retouche des lots.

## Résultat (2026-10-18)

1 652 lignes (SFA 182, SFA2 408, Gold 46, SFA3 680, Gem Fighter 306, secrets/options 30). Contre SuperCombo : SFA1 159 lignes
vérifiées, SFA2/Gold 283, SFA3 463 ; **90 corrections, toutes des coquilles du guide** (aucune erreur de lecture au zoom), ex.
Messatsu Go Hado d'Alpha 3 (→↘↓↙← ×2), Yoga Flame / Yoga Blast X-ISM, « 2 Punch » au lieu de « 2 Kick » (Cammy, Adon),
supers à un seul quart de cercle. La forme imprimée est gardée dans `conditions`. Restent : 9 lignes « à tester » (ISM selon
SuperCombo différente du guide : M. Bison, Juli, Rolento ; Charlie / Sagat SFA1 ; Angry Charge Gold) ; 18 « [douteux] » (lettres
rognées par la reliure dans des combos, et Gem Fighter, que SuperCombo ne documente que pour Dan et Zangief).
Le jeu fait foi : à confirmer en jeu, sur l'arcade ou dans Hyper.
