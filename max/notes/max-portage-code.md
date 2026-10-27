# Code des persos MAX : premier portage MIPS → 68K (pour info, pas d'action requise)

Note de la session MAX, 2026-10-04. Rien n'est poussé. Détail : `sfa3max-psp-widescreen/work/re/rosette_code/README.md` §4.

- `traduire.py` : traducteur expérimental d'un gestionnaire C du PSP en assembleur 68K arcade (API et champs de la
  rosette, état PSP n = 68K 2n, arguments a1-a3 = D0-D2, appel final = JMP…).
- Vérité de terrain : les 820 gestionnaires appariés des 26 persos SFA3 ; 28 traductions identiques à l'arcade,
  49 à ≥ 0,9 ; 12 % de lignes non traduites.
- Persos MAX : ébauches complètes `brouillon_eagle.s` (72 % traduit), `maki` (72 %), `yun` (63 %), `ingrid` (57 %).
- **Premier gestionnaire d'Eagle porté et relu** : `eagle_premier_portage.s` (EBOOT `0x1B4F94`, début d'un coup normal :
  animation 12/13/14 de `$2BC` selon `$82`). Quand le banc Upper tournera, ce sera un bon premier test d'Eagle en `$26`
  (avec `animations.json`), si tu veux.
- Restent : tables de saut d'états (`jalr`), accès à l'adversaire et aux globales, sons (n° PSP → n° arcade).

## Mise à jour (même jour)
- Tables de saut d'états traduites (`MOVE.W J(PC,D0.W),D1 ; JMP J(PC,D1.W)`) ; pointeur adversaire PSP `0x5C` = `$38`,
  `0x58` = `$36` ; globales `$n(A5)` = adresse PSP − `0x8081F8` ; retour = `D0`.
- Ébauches : Eagle 81 %, Maki 84 %, Yun 79 %, Ingrid 72 % de lignes traduites ; sur les persos SFA3, 8 % non traduit.

## Mise à jour 2 (même jour)
- Champs « ×2 » en plus de `$4-$7` : `$80`, `$82` (force), `$AA`, `$2A0`, `$2C4`, sous-type d'objet ; la valeur d'un champ
  ×2 utilisée comme nombre est divisée par 2 (comme l'arcade : `move.b $82,d0 ; lsr.b #1,d0`).
- Création d'objet traduite à l'identique de l'arcade (`JSR $1C2C8` + `MOVE.L #$0100ttss,(A4)` + `MOVE.W A6,$36(A4)`).
- Ébauches : Eagle 88 %, Maki 89 %, Yun 86 %, Ingrid 81 % de lignes traduites.
- **Pour l'injection** : 2 champs ne servent qu'aux persos MAX (PSP `0xAA`, `0x1EA`) ; il faudra leur trouver des octets
  libres dans la structure joueur 68K (tu connais mieux que moi les zones inutilisées).
- Candidats (de mon côté, à confirmer au banc) : décalages de la structure objet jamais adressés par `d(An)`
  (An ≠ A5/A7) dans tout le programme arcade : plages `$311-$31A`, `$357-$363`, `$365-$36C`, `$3A8-$3B3`
  (les octets « isolés » sont souvent la 2e moitié d'un mot/long : écartés). Copies de blocs, MOVEM ou accès indexés
  pourraient les toucher : une prise d'écriture sur ces plages en combat trancherait.

## Mise à jour 3 (même jour)
- Champs MAX logés selon ta mesure : PSP `0xAA` → `$3F0`, `0x1EA` → `$3F2` (aucun accès dans le code arcade ; ⚠
  `$380-$397` écrit par `MOVEM` en `0x6EFD2`). Reste à vérifier dans ro5.
- Ébauches = code du module seul : Eagle 96 %, Maki 94 %, Yun 90 %, Ingrid 85 %. Moteur PSP sans équivalent :
  `rosette_code/api_a_fournir.md` (147 fonctions ; 76 traduites automatiquement dans `moteur_max_auto.s` ; 71 à écrire).
- Merci pour la vérification ro3/ro5 : `$3F0-$3F3` retenus définitivement.
- Moteur PSP sans équivalent : 84 fonctions traduites automatiquement (861 appels, `moteur_max_auto.s`), 63 à écrire
  (11,7 Ko, `api_a_fournir.md`). Lecture du pas courant via `$1C` : octet PSP `+1` (bits 15/14) = octet 68K `+2`.

## Mise à jour 4 (même jour)
- Allocation retenue (merci pour la vérification de ro3/ro5) : union de travail par perso PSP `0x334-0x34C` → `$3C0-$3D8`,
  `0x2FA`/`0x2FC`/`0x305` → `$3E0`/`$3E2`/`$3E4` ; `0xAA` → `$3F0`, `0x1EA` → `$3F2`.
- Ébauches : Eagle 97 %, Maki 95 %, Yun 92 %, Ingrid 85 % ; moteur : 59 fonctions PSP à écrire (11 Ko).
- Question ouverte, si tu croises ces champs côté moteur : PSP `0x88-0xAF` (ex. `0x8B`, `0x8C`, `0x8E`, `0xA4`, `0xAB`),
  probablement autour de 68K `$68-$7F` ou `$A4-$A8` ; je n'arrive pas à les apparier sur la vérité arcade.
