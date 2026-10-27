# Projet tiers : SFZ2A-DASH-CPS2 (Cammy de Gold sur l'arcade Zero 2 Alpha)

Dépôt : <https://github.com/Zer0-NexuS/sfz2a-dash-cps2> (lu le 2026-10-16, commit `a00a53d`). Le dépôt ne contient que
deux README et des patchs IPS pour `sfz2ald.zip` (Street Fighter Zero 2 Alpha, CPS2 déchiffré) ; le code source
(« Source Checkpoint 15 », `build_gold.py`, `gold_native/`) n'y est pas publié. Projet de fans, sans lien avec celui-ci.

## Ce qu'ils ont fait

- Portage de **Cammy d'Alpha 2 Gold** dans l'arcade **SFZ2 Alpha** à partir de l'**Anthology PS2** : graphismes,
  animations, collisions, 85 attaques, comportement (routines MIPS du module `X_0526` relevées et réécrites à la main
  en 68000), portraits, fin (17 lignes), voix.
- **Voix de Cammy** : banque partagée `X_0333_MOMO` de l'Anthology (14 échantillons, déclenchés par les tables
  d'événements de Gold), convertie en PCM 8 bits 12 019 Hz pour le QSound ; place trouvée dans les 4 Mo en
  rééchantillonnant 156 longs échantillons à 15/16.
- Révision 31 : correction de cris inversés (étourdi / K.O.), 363 enregistrements de projections de Gold, propriétés
  du perso.
- Sélection : sur Bison, Start deux fois → Cammy ; Start une fois → Final Bison ; sur Akuma, Start → Shin Akuma ; sur
  Ryu, Start deux fois → Evil Ryu.

## Utilité pour HSFA

1. **Référence arcade des versions ALPHA d'Hyper** (ZERO 2 ALPHA = Alpha 2 Gold / module `ro6`) : l'arcade
   **SFZ2 Alpha** (`sfz2al`, `sfz2ald`) est plus proche que SFA2, qui a servi aux comparaisons de voix du 2026-10-16
   (`tools/son-hyper/compare_voix_arcade.py`). Elle a aussi les persos à la Start (Shin Akuma, Final Bison,
   Evil Ryu…) : avec un `sfz2al.zip`, les versions ALPHA et une partie des versions EX d'Hyper pourraient être
   comparées à leur vraie référence.
2. **Cammy ALPHA (`$7E`) est muette dans HSFA** (SON-HYPER-ROM §4.3 : ses voix PS2 sont dans une banque SCEI propre,
   non extraite). Leur travail confirme la source (banque de l'Anthology, ici `X_0333`, 14 voix) et une conversion
   simple (PCM 12 019 Hz) ; chez nous, ces voix pourraient passer par un lecteur d'échantillons du cœur (comme le
   rejeu) sans toucher à la ROM QSound.
3. Méthode comparable (données extraites de l'Anthology, routines MIPS réécrites en 68000, validation en émulation) :
   lecture utile pour la greffe et MAX.

## Suite (2026-10-16)

`sfz2al.zip` (fourni par l'utilisateur) : ROM son et Z80 identiques à SFA2 ; versions ALPHA et EX d'Hyper comparées à
cette référence (SON-HYPER-ROM §4.3, `tools/son-hyper/mesures_voix/sfz2a/`). Sélection des variantes dans SFZ2 Alpha :
Start tapé une ou deux fois sur le perso avant la validation (Ryu ×2 = Evil Ryu, Chun-Li ×1 = Chun-Li classique…).

