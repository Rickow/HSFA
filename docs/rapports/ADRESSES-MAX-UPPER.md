# Les 108 adresses arcade du code MAX, dans Upper (ro5)

Session « adresses MAX → Upper », 2026-10-07. Lecture seule de l'existant. Tout ce qui est produit est dans
`<workspace>/work/agent_max_upper/`. Pas de MAME.

**Conventions**
- *arcade* : adresse 68K dans `sfa3ud_prog.bin`, celle de `adresses_arcade_max.txt`.
- *68K Upper* : adresse dans l'**image Upper traduite actuelle** (`mame_ro5/roms_ro5/sfa3ud`, `carte_image.txt` du 7/10
  12 h 56, la même que `realign.pkl`).
- *va MIPS* : décalage dans `ro5_usa_prog68k.bin`, celui que prend `show.py`. « instr. » est la va de la première
  instruction traduite. « entrée » est l'étiquette MIPS citée comme cible de saut juste avant (début de fonction ou de
  bloc). Pour une adresse d'exécution, ajouter `0x1F0000`.
- Décalages de champs : **numérotation arcade**, sauf mention « brut image ».

---

## 0. En bref

1. **107 adresses sur 108 ont un homologue dans Upper.** 99 sont **identiques** : seuls le portage et le recompilateur
   changent la forme. 8 sont **modifiées par Upper** : `$2AEBC`, `$2E3E0`, `$2E3FE`, `$2E4C2`, `$2E636`, `$2E7F2`, `$2E8C0`,
   `$369C`. **1 est absente** : `$2D5E2`, première entrée de la table des manipulations. Aucune n'est incertaine.
2. **Manipulations** (`$2D5E2 + 8k`, 46 adresses de la liste) : Upper a supprimé la **première** entrée. Toutes les suivantes sont
   donc **décalées d'un rang** : l'entrée arcade *k* devient l'entrée Upper *k − 1*, en `$251F6 + 10(k − 1)`. Les
   définitions sont identiques. L'interpréteur commun est identique au réordonnancement près.
3. **Champs déplacés d'ECARTS** : parmi les 108 routines, **seul `$32F` est touché** (`$2E3E0`, `$2E3FE`, `$2E636`). Aucune
   ne lit ni n'écrit `$145`, `$37F`, `$140/$144`, `$128`, `$149`, `$1FE` ou `$15F` (balayage de chaque étendue).
   S'y ajoute `$2C8`, qu'Upper n'efface plus dans `$2AEBC`.
4. **`$32F` (point 3)** : Upper n'écrit plus rien à la place. Le n° de saisie reste dans **D0** jusqu'à la queue commune
   (`$2E462` → image `$30208`), qui calcule `A3 = $A0(A6) + n×32`. Dans l'arcade, aucune instruction ne lit `$32F`.
   → **Supprimer `move.b d0,$32f(a6)` de `psp_66890`.** Dans l'image, l'octet brut `$32F` est le drapeau arcade `$32E`
   (`$2934E`). L'écrire sans conversion l'écraserait.
5. **Sauts (point 4)** : pointeur **`$2D4(A6)`**, posé selon l'ism `$132` par la routine d'initialisation du perso
   (`$2BE6A`). Il vise 3 tables (ism 0 / `$FF` / autre). Chacune compte **32 entrées × 64 octets** dans l'arcade et
   **40 × 64** dans Upper. Une entrée = 4 fiches de 16 octets {vx, vy, ax, ay}. `$2D0(A6)` (marche, 8 octets par perso)
   est le pendant. Dans Upper, **`$26/$27` existent déjà** : ce sont des copies de `$00` et `$1F`, à remplacer. **`$28/$29`
   débordent** sur la table suivante.
6. **Avertissement d'intégration.** L'image Upper traduite suit la **disposition mémoire du portage PS2** :
   - octets de structure en XOR 1 (`$102` arcade = `$103` brut : `MOVE.B $0103(A6)`, va `0x248508`, MIPS `lb 258`) ;
   - longs à demi-mots échangés (`MOVE.L #$6020000,$4(A1)` pour l'arcade `#$02060000`) ;
   - mots couvrant deux octets lus inversés (`CMPI.W #$0002,$4(A6)` pour l'arcade `#$0200`) ;
   - tables de données en longs échangés ;
   - pointeurs de tables PS2 convertis à l'exécution par `JSR $400` (CONV_A0). Les adresses dans `[$60ACC0, $C3FC50)`
     sont converties, les autres passent telles quelles.

   Les variables A5 sont aussi relogées par le portage (ex. `-$5CD2(A5)` → `-$746C(A5)`, table de `realign.pkl`).
   **Le code MAX écrit en numérotation arcade devra être converti de la même façon** avant d'être mêlé à l'image Upper.
   Les adresses 68K ci-dessous sont des adresses de cette image.

---

## 1. Les 108 adresses

Statuts : **identique** (même routine, même effet ; seuls changent la disposition du portage et le réordonnancement du
recompilateur) ; **modifiée par Upper** ; **absente**. Le détail machine est dans `correspondances.tsv`, qui ajoute la
source de l'homologue, le ratio de similarité des corps normalisés et la part d'instructions alignées.

| arcade | nom | 68K Upper | va MIPS (instr. / entrée) | statut | remarque |
|---|---|---|---|---|---|
| `$1B4D0` | affichage / test de plan (parallaxe) | `$19D34` | `0xc65f8` / `0xc65b0` | **identique** | portage seulement |
| `$1BD5C` | A3 = table selon $E (plan) | `$1A666` | `0xcb0d4` / `0xcb0d0` | **identique** | portage seulement |
| `$1BD68` | A3 = caméra du plan $E, D0 = décalage | `$1A68A` | `0xcb13c` / `0xcb120` | **identique** | SUBI.W #$C0 traduit ADDI.W #$FF40 |
| `$1BDA6` | aléa (graine $AE(A5)) | `$1A6DE` | `0xcb360` / `0xcb350` | **identique** | octets $AE/$AF de la graine : disposition du portage |
| `$1C1C8` | allocation d'un projectile (réservoir) | `$1AB86` | `0xccd3c` / `0xccd10` | **identique** | portage seulement |
| `$1C2C8` | allocation d'objet standard ($10) | `$1ACB8` | `0xcd5cc` / `0xcd5a0` | **identique** | portage seulement |
| `$1C2DE` | allocation + raz d'objet standard | `$1ACCE` | `0xcd6e4` / `0xcd6e0` | **identique** | portage seulement |
| `$1C368` | allocation d'effet ($18) | `$1AD88` | `0xcdb4c` / `0xcdb20` | **identique** | portage seulement |
| `$1C37E` | allocation + raz d'effet | `$1AD9E` | `0xcdc64` / `0xcdc60` | **identique** | portage seulement |
| `$20674` | points / réaction ($AC(A5), $125) | `$016FA` | `0x27da0` / `0x27cc0` | **identique** | portage seulement |
| `$2068C` | points, force $82 (pose $216) | `$0171C` | `0x27e68` / `0x27e40` | **identique** | portage seulement |
| `$206AE` | points | `$01748` | `0x280d0` / `0x27ff0` | **identique** | portage seulement |
| `$2A708` | lancer l'animation n (table $2B0) | `$51A40` | `0x2398d8` / `0x2398c0` | **identique** | table par perso $DCB12 -> image $1DF038 (40 pointeurs, $26/$27 = copies) |
| `$2A710` | lancer l'animation n (table $2BC) + octets perso/ism -> $23E/$293 | `$51A56` | `0x239934` / `0x239900` | **identique** | idem $2A708 ; index (ism+1)x2 inchangé |
| `$2A758` | lancer l'animation n (table $2B4) | `$51AD2` | `0x239b28` / `0x239b10` | **identique** | portage seulement |
| `$2A75E` | lancer l'animation n (table $2B8) | `$51AE6` | `0x239b68` / `0x239b50` | **identique** | portage seulement |
| `$2A770` | charger le pas d'animation A0 | `$51B04` | `0x239c48` / `0x239c30` | **identique** | portage seulement |
| `$2A7EA` | avancer l'animation | `$51BCC` | `0x239fb4` / `0x239f80` | **identique** | portage seulement |
| `$2A98C` | état $2000600 (garde/chute) | `$51E4C` | `0x23acf8` / `0x23ace0` | **identique** | portage seulement |
| `$2AA08` | intégrer vitesse/accélération ($40-$4C) | `$51EE0` | `0x23afa8` / `0x23af80` | **identique** | portage seulement |
| `$2AEBC` | fin de coup -> $2F770 (efface $2C8, $5B) | `$52604` | `0x23e970` / `0x23e960` | **modifiée par Upper** | n'efface plus $2C8(A6) (MOVEQ #0,D0 retiré, sans effet : $2F770 le refait) ; ne fait que CLR.B $5B puis JMP $31942 |
| `$2AF7A` | test de sol / atterrissage | `$526F0` | `0x23ef2c` / `0x23eef0` | **identique** | portage seulement |
| `$2B1FC` | test | `$529BE` | `0x240064` / `0x240030` | **identique** | portage seulement |
| `$2B828` | Gen : changement de style ($11<->$13) | `$530D6` | `0x244914` / `0x2448c0` | **identique** | masque #$000A0000 remplacé par CMPI.B #$11/#$13 (même effet ; neutre pour $26-$29) |
| `$2BB26` | retour en garde | `$53536` | `0x246628` / `0x246620` | **identique** | portage seulement |
| `$2BB5A` | retour au neutre | `$5356C` | `0x24671c` / `0x2466f0` | **identique** | portage seulement |
| `$2C0AC` | $D(A6) := table[mode $138(A5), côté $101] | `$539EA` | `0x248470` / `0x248460` | **identique** | portage seulement |
| `$2D5E2` | manipulation n° 0 (déf. $2E0FE) | — | — | **absente** | 1re entrée (déf. $2E0FE = 0001 0012 0F00) sans homologue : déf. présente en $D0CCB0, jamais référencée (ni image ni MIPS) ; à recréer : LEA $D0CCB0,A3 ; BRA $25468 |
| `$2E3E0` | saisie (n -> $32F) variante adversaire $1C/$D | `$30156` | `0x15cda4` / `0x15cd80` | **modifiée par Upper** | écriture $32F(A6) supprimée (D0 = n passe en registre jusqu'à la queue commune $30208 = arcade $2E462) |
| `$2E3FE` | déclenchement d'une saisie (n -> $32F), selon $3E / état $4-$6 | `$30182` | `0x15cee8` / `0x15ce90` | **modifiée par Upper** | écriture $32F(A6) supprimée ; BRA $2E366 devient BSR $300BE + RTS |
| `$2E422` | saisie, chemin « joueur » de $2E3FE | `$301AA` | `0x15d184` / `0x15d168` | **identique** | entrée interne (label MIPS 0x15d168, pas de prologue) : JMP possible dans l'image ; $204/$200 lus #$402/#$0002 (disposition) |
| `$2E4C2` | victime mise en état « saisi » | `$3028A` | `0x15da04` / `0x15d9e0` | **modifiée par Upper** | ajouts : appels $9F314 (A6=victime, drapeaux $C32D(A5)) et $9E9E0 (A8=victime) en tête ; en fin, si bit 4 de $C372(A5) nul : CLR.B $5F(A6) et $5F(A1) |
| `$2E636` | saisie variante (adversaire $31, n -> $32F) | `$304B6` | `0x15ead4` / `0x15eab0` | **modifiée par Upper** | écriture $32F(A6) supprimée ; reste identique (l'écart « $25D remplacé par un appel » d'ECARTS concerne $2E614 -> $3047C) |
| `$2E7F2` | coup direct à la victime $38 (attaque n de $A0) | `$306B0` | `0x15f9a0` / `0x15f990` | **modifiée par Upper** | ajout en fin : si bit 4 de $C373(A5) nul (JSR $1156) -> CLR.B $2CE(A1) ; variables -$5CD2/-$5CD0(A5) relogées (-$746C/-$746A, portage) |
| `$2E8C0` | A0 = objet du camp ($156/$158(A5)) | `$307E6` | `0x15fd94` / `0x15fd70` | **modifiée par Upper** | TST.B $59(A6) remplacé par BSR $30802 : table T_615070 [mode $138(A5)x2 (+$10 si $AC(A5)=2) + côté $101(A6)] |
| `$2E96C` | prise, attaque n de $A0 (D2=1) | `$3090E` | `0x160790` / `0x160780` | **identique** | A5 relogées (portage) |
| `$2E970` | prise, attaque n de $A0 (D2=0) | `$30912` | `0x1607bc` / `0x1607b0` | **identique** | A5 relogées (portage) |
| `$2EA06` | mash (boutons $378) en saisie | `$309B0` | `0x160ba4` / `0x160b70` | **identique** | table $C94DA -> $F96B0 (mêmes valeurs, longs échangés) |
| `$2EA7A` | mash de la victime ($AE) | `$30A22` | `0x160d90` / `0x160d70` | **identique** | table $C945A -> $F9630 |
| `$2EB06` | annulation de coup normal | `$30AA0` | `0x1611fc` / `0x1611c0` | **identique** | portage seulement |
| `$2EC28` | poing faible + pied faible | `$30BB6` | `0x161c7c` / `0x161c40` | **identique** | portage seulement |
| `$2EF6C` | gain de jauge super $11E | `$31034` | `0x164d34` / `0x164d00` | **identique** | chemin mort ×1,25 retiré ; temporaire -$4B0A(A5) relogé |
| `$2F52C` | pose $291=1, $2A0=10 puis neutre | `$316A4` | `0x168564` / `0x168550` | **identique** | portage seulement |
| `$2F53C` | neutre (suite) | `$316B4` | `0x1685c4` / `0x168590` | **identique** | portage seulement |
| `$2F5AC` | neutre (variante) | `$31736` | `0x168b38` / `0x168af0` | **identique** | portage seulement |
| `$2F6F8` | test contre-attaque ($125/$3E/$CE) | `$318CE` | `0x169b74` / `0x169b40` | **identique** | portage seulement |
| `$2F728` | force du poing pressé -> $82 | `$318FA` | `0x169cb8` / `0x169cb0` | **identique** | portage seulement |
| `$2F74C` | force du pied pressé -> $82 | `$3191E` | `0x169da8` / `0x169da0` | **identique** | portage seulement |
| `$2F770` | raz $3E/$294, libère l'adversaire | `$31942` | `0x169e94` / `0x169e90` | **identique** | portage seulement |
| `$2F796` | remise à l'état neutre | `$31978` | `0x169fe4` / `0x169fb0` | **identique** | portage seulement |
| `$2F980` | lecture de combinaison de boutons | `$31AFC` | `0x16aab8` / `0x16aa80` | **identique** | portage seulement |
| `$2F9BE` | placer l'adversaire (table $DD212) | `$31B3A` | `0x16adb4` / `0x16ad90` | **identique** | table par perso $DD212 -> $1DF8F8 (40 pointeurs) |
| `$2FA36` | se placer sur l'adversaire (table $DD212) | `$31BEE` | `0x16b1a4` / `0x16b180` | **identique** | realign.pkl donnait $31CA2 (= arcade $2FAAE) : homologue réel $31BEE ; table $DD212 -> $1DF8F8 |
| `$33074` | projectile : routine commune | `$2B168` | `0x137a18` / `0x137a00` | **identique** | portage seulement |
| `$330C4` | projectile : demi-tour | `$2B1BA` | `0x137c58` / `0x137c40` | **identique** | portage seulement |
| `$33120` | projectile : renvoi (Soul Reflect) | `$2B236` | `0x137ea8` / `0x137e90` | **identique** | portage seulement |
| `$0369C` | son/voix propre au perso (masque par ID) | `$2B5F2` | `0x138ea0` / `0x138e70` | **modifiée par Upper** | masque #$03210D40 BTST ID remplacé par BSR $2B594 (table d'octets par ID T_6132e0, fichier 0x4232E0) : entrées $28/$29 à ajouter |
| `$804DA` | création de 3 objets fils | `$32662` | `0x16f7cc` / `0x16f790` | **identique** | réorganisé (BSR/BRA du recompilateur) |
| `$80668` | création d'objet fils | `$3281A` | `0x170054` / `0x170030` | **identique** | portage seulement |
| `$80B70` | objet fils lié à l'attaque n (table $A0) | `$32DAC` | `0x171ea8` / `0x171e90` | **identique** | portage seulement |
| `$80E8E` | objet fils | `$33012` | `0x172c7c` / `0x172c70` | **identique** | portage seulement |
| `$82E36` | objet fils selon la force $82 / ism | `$33B2E` | `0x176ad4` / `0x176ab0` | **identique** | réorganisé (BMI -> BSR $33DB8) |
| `$97CD6` | effet / son | `$40D8A` | `0x1c62a0` / `0x1c6290` | **identique** | portage seulement |

| arcade | déf. arcade | 68K Upper | va MIPS (instr. / entrée) |
|---|---|---|---|
| `$2D5EA` | `$2E104` | `$251F6` | `0x10d104` / `0x10d0f0` |
| `$2D5F2` | `$2E10C` | `$25200` | `0x10d134` / `0x10d120` |
| `$2D5FA` | `$2E134` | `$2520A` | `0x10d164` / `0x10d150` |
| `$2D602` | `$2E13C` | `$25214` | `0x10d194` / `0x10d180` |
| `$2D60A` | `$2E114` | `$2521E` | `0x10d1c4` / `0x10d1b0` |
| `$2D612` | `$2E11C` | `$25228` | `0x10d1f4` / `0x10d1e0` |
| `$2D61A` | `$2E124` | `$25232` | `0x10d224` / `0x10d210` |
| `$2D622` | `$2E12C` | `$2523C` | `0x10d254` / `0x10d240` |
| `$2D62A` | `$2E14C` | `$25246` | `0x10d284` / `0x10d270` |
| `$2D632` | `$2E154` | `$25250` | `0x10d2b4` / `0x10d2a0` |
| `$2D63A` | `$2E144` | `$2525A` | `0x10d2e4` / `0x10d2d0` |
| `$2D642` | `$2E164` | `$25264` | `0x10d314` / `0x10d300` |
| `$2D64A` | `$2E16E` | `$2526E` | `0x10d344` / `0x10d330` |
| `$2D652` | `$2E178` | `$25278` | `0x10d374` / `0x10d360` |
| `$2D65A` | `$2E182` | `$25282` | `0x10d3a4` / `0x10d390` |
| `$2D662` | `$2E18C` | `$2528C` | `0x10d3d4` / `0x10d3c0` |
| `$2D66A` | `$2E198` | `$25296` | `0x10d404` / `0x10d3f0` |
| `$2D672` | `$2E1A4` | `$252A0` | `0x10d434` / `0x10d420` |
| `$2D67A` | `$2E1B0` | `$252AA` | `0x10d464` / `0x10d450` |
| `$2D682` | `$2E1BC` | `$252B4` | `0x10d494` / `0x10d480` |
| `$2D68A` | `$2E1C4` | `$252BE` | `0x10d4c4` / `0x10d4b0` |
| `$2D692` | `$2E1CC` | `$252C8` | `0x10d4f4` / `0x10d4e0` |
| `$2D69A` | `$2E1D8` | `$252D2` | `0x10d524` / `0x10d510` |
| `$2D6A2` | `$2E1E4` | `$252DC` | `0x10d554` / `0x10d540` |
| `$2D6AA` | `$2E1F0` | `$252E6` | `0x10d584` / `0x10d570` |
| `$2D6B2` | `$2E1FC` | `$252F0` | `0x10d5b4` / `0x10d5a0` |
| `$2D6BA` | `$2E208` | `$252FA` | `0x10d5e4` / `0x10d5d0` |
| `$2D6C2` | `$2E216` | `$25304` | `0x10d614` / `0x10d600` |
| `$2D6CA` | `$2E224` | `$2530E` | `0x10d644` / `0x10d630` |
| `$2D6D2` | `$2E238` | `$25318` | `0x10d674` / `0x10d660` |
| `$2D6DA` | `$2E24C` | `$25322` | `0x10d6a4` / `0x10d690` |
| `$2D6EA` | `$2E25A` | `$25336` | `0x10d704` / `0x10d6f0` |
| `$2D6F2` | `$2E260` | `$25340` | `0x10d734` / `0x10d720` |
| `$2D6FA` | `$2E266` | `$2534A` | `0x10d764` / `0x10d750` |
| `$2D702` | `$2E272` | `$25354` | `0x10d794` / `0x10d780` |
| `$2D70A` | `$2E27E` | `$2535E` | `0x10d7c4` / `0x10d7b0` |
| `$2D712` | `$2E286` | `$25368` | `0x10d7f4` / `0x10d7e0` |
| `$2D71A` | `$2E28A` | `$25372` | `0x10d824` / `0x10d810` |
| `$2D722` | `$2E282` | `$2537C` | `0x10d854` / `0x10d840` |
| `$2D72A` | `$2E29E` | `$25386` | `0x10d884` / `0x10d870` |
| `$2D732` | `$2E2A6` | `$25390` | `0x10d8b4` / `0x10d8a0` |
| `$2D73A` | `$2E28E` | `$2539A` | `0x10d8e4` / `0x10d8d0` |
| `$2D742` | `$2E296` | `$253A4` | `0x10d914` / `0x10d900` |
| `$2D74A` | `$2E2AE` | `$253AE` | `0x10d944` / `0x10d930` |
| `$2D752` | `$2E2B6` | `$253B8` | `0x10d974` / `0x10d960` |

Tronc commun des manipulations : arcade `$2D7E6` → `$25468`, `$2D900` → `$255C8`, `$2D998` → `$25686`, `$2D9F8` → `$256F6`,
`$2DA84` → `$257A6`, `$2DBBA` → `$2595C`, `$2DCFE` → `$25ADE`, `$2DDDC` → `$25BD8`. Comparaison des multiensembles
d'instructions normalisées (`interp.py`) : rien ne manque dans Upper, hormis les tables en ligne et deux `CMPI.W` sans
effet (`$2DD6C`, `$2DD76`). L'écart « BTST #4,D6 retiré ×6 » d'ECARTS est un **réordonnancement** : `BTST #4,D6` est
toujours là (image `$254CE`), avec le test inversé. Seul ajout réel : `BSR $25D04` dans la branche « maintien »
(`$2DD68`). Il calcule un niveau de charge (seuils `$79/$F1/$1E1/$3C1/$5A1`). Il ne concerne que les entrées `$2D7D6/$2D7DE`,
que MAX n'utilise pas.

**Pour `TAB_MANIPS`** : remplacer chaque `$2D5E2 + 8k` (k ≥ 1) par `$251F6 + 10(k − 1)`. Pour k = 0, recréer l'entrée
(`LEA $D0CCB0,A3 ; BRA $25468`, définition déjà en place à `$D0CCB0`) ou marquer la manip « sans équivalent ». La
définition de k = 0 se trouve dans `ext_c80000.bin` (+`$8CCB0`), mais ni l'image ni le MIPS ne la référencent : aucun
`0x00971790` dans `ro5`.

---

## 2. Routines modifiées par Upper : détail

| arcade → Upper | différence (preuve) | conséquence pour MAX |
|---|---|---|
| `$2AEBC` → `$52604` (va `0x23e970`) | MIPS : `sb zero,91(v0)` (`CLR.B $5B`) puis `jal 0x359e90` (= `$2F770`). `MOVEQ #0,D0` et `MOVE.B D0,$2C8(A6)` ont disparu (écart ECARTS (a) « `$2C8` n'est plus remis à zéro »). | `$2C8` reste dans Upper (lu en `$30430` = arcade `$2E5C6`). Si MAX compte sur sa remise à zéro, faire `clr.b $2c8` (en disposition image) avant `JMP $52604`. |
| `$2E3E0` → `$30156` (va `0x15cda4`, fonction `0x15cd80`) | L'instruction `MOVE.B D0,$32F(A6)` disparaît. La fonction MIPS commence directement par `MOVEA.W $38(A6),A1`, et l'image a un `RTS [retour partagé]` en `$30154` à sa place. | Appeler `$30156` avec D0 = n (`psp_cf3e8`). |
| `$2E3FE` → `$30182` (va `0x15cee8`, fonction `0x15ce90`) | Pas d'écriture de `$32F`. MIPS : `lb v1,62(v0)` = `TST.B $3E` en tête. `BRA $2E366` devient `BSR $300BE ; BRA $30206 (RTS)`. | — |
| `$2E636` → `$304B6` (va `0x15ead4`, fonction `0x15eab0`) | Pas d'écriture de `$32F`. Les tests `$31`, `$3E`, `$24E`, `$200/$E`, `$25D`, `$D6`, `$23F`, `$2CE`, `$204/$202/$200` sont tous présents (image `$304B6-$3054C`). ECARTS lit « `$2E66E` : `$25D` remplacé par un appel » : c'est en fait `$2E614` → `$3047C`, où Upper insère `JSR $1196` (option `$C372` bit 6), qui conditionne deux tests de plus (`$D6`, `$23F`). | — |
| `$2E4C2` → `$3028A` (va `0x15da04`, entrée `0x15d9e0`) | En tête : `EXG A6,A1 ; JSR $9F314 ; EXG`. Cette routine met à jour les drapeaux `$C32D(A5)`. Puis `JSR $9E9E0` avec A8 = victime. Ces deux routines viennent de `0x4104b0` et `0x40c790`, hors code recompilé du 68K. En fin : `JSR $1186` (`BTST #4,$C372(A5)`). S'il vaut 0 : `CLR.B $5F(A6)` et `CLR.B $5F(A1)`. | Comportement d'Upper (options console `$FF4372-77`, statistiques). À garder tel quel : MAX saute en `$2E4C2` → `$3028A`. |
| `$2E7F2` → `$306B0` (va `0x15f9a0`) | Après `MOVE.B #6,$114(A0)`, Upper ajoute `JSR $1156` (`BTST #4,$C373(A5)`). S'il vaut 0 : `CLR.B $2CE(A1)`. Les variables `-$5CD2/-$5CD0(A5)` sont relogées en `-$746C/-$746A` (portage). | Neutre pour MAX (`psp_672dc`). |
| `$2E8C0` → `$307E6` (va `0x15fd94`) | `TST.B $59(A6)` devient `BSR $30802`. Cette routine calcule l'indice `$138(A5)×2 (+$10 si $AC(A5) = 2) + $101(A6)` et lit `T_615070` (fichier `0x425070`). C'est le calcul que l'arcade fait une seule fois à l'initialisation (`$2BDD6` : `$59 := table[$138×2 + $101]`), avec en plus un cas `$AC(A5) = 2`. | Le résultat (A0 = `$156` ou `$158(A5)`) ne dépend plus de `$59(A6)`. |
| `$369C` → `$2B5F2` (va `0x138ea0`) | `MOVE.L #$03210D40,D0 ; BTST ID,D0` devient `BSR $2B594` : `MOVE.B T_6132e0(PC,ID),D2` (fichier `0x4232E0`, un octet par ID). | Pour `$28/$29`, il faut **ajouter 2 octets** à cette table. `$26/$27` sont à vérifier ; la table compte au moins 40 entrées. |

Variantes de forme jugées identiques : `$2B828` (masque Gen `#$000A0000` → `CMPI.B #$11 / #$13`, même effet, sans
incidence pour `$26-$29`), `$1BD68` (`SUBI.W #$C0` → `ADDI.W #$FF40`), `$2EF6C` (chemin mort ×1,25 retiré).

**Correction d'alignement** : `realign.pkl` donne pour `$2FA36` deux homologues. Le premier (`$31CA2`) est l'homologue
de `$2FAAE`. Le vrai est **`$31BEE`** (va `0x16b1a4`).

**Tables par perso utilisées par ces routines** : dans l'image, ce sont des longs échangés, en général des pointeurs PS2
convertis par `JSR $400`.

| table | arcade | Upper | entrées | `$26/$27` dans Upper |
|---|---|---|---|---|
| pointeurs `$DCB12` (`$2A710`) | 32+ | `$1DF038` | 40 | copies (pointeur par défaut) |
| pointeurs `$DD212` (`$2F9BE`, `$2FA36`) | 32+ | `$1DF8F8` | 40 | copies |
| marche `$2D0` | 3 × 32 × 8 | 3 × 40 × 8 | 40 | copies de `$00` / `$1F` |
| sauts `$2D4` | 3 × 32 × 64 | 3 × 40 × 64 | 40 | copies de `$00` / `$1F` |
| routines d'objets `$32F46` (par **type** d'objet, pas par perso) | 37 (`$00-$24`) | `$A65F0` | 38 + `$26/$27` **nuls** | libres ; `$28+` = autre table |

Pour les projectiles de MAX (`psp_fils_26..29`) : dans Upper, les **types `$26` et `$27` sont libres** (pointeur 0 en
`$A65F0+$98/$9C`). `$28/$29` collisionnent avec la table suivante (`$2C3EB0…`). Le pointeur est lu en long échangé puis
passé à CONV (`$400`). Une adresse d'image 68K (< `$60ACC0`) passe donc sans conversion.

---

## 3. `$32F` (arcade `$2E3FE` / `$2E422`) : la convention d'Upper

**Arcade** : 9 sites écrivent `MOVE.B D0,$32F(A6)` : `$2E3E0`, `$2E3FE`, `$2E5D4`, `$2E5F0`, `$2E614`, `$2E636`, `$2E6EC`,
`$2E700`, `$2E714`. **Aucune** instruction de `arc.pkl` ne lit `$32F` : pas de `d16(An)`, et les seuls voisins
(`$32C/$32D/$32E`, `MOVEP ($32C,A0)`) n'y touchent pas. Le n° de saisie n'est utilisé que **dans D0**, par la queue commune
`$2E462`, qui fait `ANDI.W #$FF,D0 ; LSL.W #5,D0 ; A3 = $A0(A6) + D0` (fiche d'attaque), puis `$2E4C2`.

**Upper** : les 9 écritures ont disparu. Les 3 routines de la liste :
- `$2E3E0` → `$30156` (va `0x15cda4`) : l'image n'a qu'un `RTS` partagé en `$30154`. La fonction MIPS `0x15cd80`
  commence par `lw v0,A6 ; lh v0,56(v0)` = `MOVEA.W $38(A6),A1`.
- `$2E3FE` → `$30182` (va `0x15cee8`). La fonction MIPS `0x15ce90` commence par `lb v1,62(v0)` = `TST.B $3E(A6)`.
- `$2E636` → `$304B6` (va `0x15ead4`). La fonction `0x15eab0` commence par `MOVEA.W $38(A6),A1`.

Upper ne met **rien** à la place : ni autre champ, ni variable A5. Le n° reste dans D0 jusqu'à la queue commune, image
`$30208` (va `0x15d6c0`) = `$2E462`, identique. Le chemin « joueur » `$2E422` est l'image **`$301AA`** (étiquette MIPS
`0x15d168`, sans prologue : c'est un bloc interne de la fonction `0x15ce90`). Dans l'image 68K, il se termine par
`BSR $30208 / BRA $30206 (RTS)`, on peut donc y sauter par `JMP`. Ses tests sont ceux de l'arcade : `$23F`, `$25D`,
`$4.w = $204/$200`, `$24E`, `$202` avec `$54 = $C`. Dans l'image, ils s'écrivent `#$402/#$0002` (disposition du portage).
Champs Upper : sur les instructions traduites, l'octet brut `$32F` sert au drapeau arcade `$32E` (`$2934E/$29354` →
image `$50472/$50478`). L'octet brut `$32E` (= arcade `$32F`) n'est utilisé nulle part.

**À appliquer à `psp_66890`** (`moteur_max_main.s` l. 580) :
```
psp_66890:
        tst.b   $3e(a6)          ; (octet : $3f brut dans l'image)
        bne.s   .non
        jmp     $301aa           ; = arcade $2E422 ; D0 = n, aucune écriture de $32F
.non:   moveq   #0, d0
        rts
```
Il ne faut **pas** écrire `$32F`. En numérotation arcade, ce serait inutile. Écrit tel quel dans l'image (octet brut
`$32F`), cela écraserait le drapeau `$32E` d'Upper. La même règle vaut pour `psp_cf3e8` (Eagle), qui appelle `$2E3E0` →
`$30156`.

---

## 4. Physique des sauts : tables par perso et par ism

### Arcade SFA3

Initialisation du perso (bloc `$2BDD6-$2BEA6`, fin `$2BE6A`) :
```
2BE6A movea.l #$DD492,A0 ; movea.l #$DD792,A1      ; $132 = 0
2BE76 tst.b $132(A6) ; beq.s pose
2BE7E movea.l #$DD692,A0 ; movea.l #$DE792,A1      ; $132 = $FF
2BE8A cmpi.b #-1,$132(A6) ; beq.s pose
2BE92 movea.l #$DD592,A0 ; movea.l #$DDF92,A1      ; $132 = autre (1)
2BE9E move.l A0,$2D0(A6) ; move.l A1,$2D4(A6) ; rts
```
- **`$2D4(A6)` = sauts** : `ID × 64` (`EXT.W ; LSL.W #6`).
  - Chaque entrée de 64 octets contient 4 fiches de 16 octets {vx.l, vy.l, ax.l, ay.l} en 16.16 :
    - `+$00` saut vertical ;
    - `+$10` copie de `+$00`, jamais lue ;
    - `+$20` et `+$30` sauts en diagonale. Le choix se fait par les bits 0-1 de `$371` (ou par `$211` si `$125`).
  - Lecteurs : `$2AA76-$2AA90` (D1 = 0/`$20`/`$30` ; D0 = vx, `$44` = vy, D1 = ax, `$4C` = ay ; vx et ax sont ensuite
    orientés dans `$40/$48`) et `$285FC-$28616` (`LEA $20(A0,D0.W)`, diagonale fixe).
  - 3 tables contiguës : `$DD792` (ism 0), `$DDF92` (autre), `$DE792` (`$FF`). Chacune fait **32 entrées × 64 = `$800`**.
  - Exemple, Ryu ism 0 : `00000000 00072000 00000000 FFFFB000 | (copie) | FFFC8000 00070000 00000500 FFFFB000 | 00040000 00074000 FFFFFB00 FFFFB000`.
- **`$2D0(A6)` = marche** : `ID × 8 + 0/4` (avant/arrière). Lecteurs `$282C2`, `$2A938`. Tables `$DD492` / `$DD592` /
  `$DD692`, 32 × 8 octets chacune.
- `$2AF02` (vitesses de projection, table `$2C57C`) est indexé par le **type de coup** (`$29F/$25F`), pas par le perso.

### Upper

Même code, image `$53878-$5391E` (va `0x2477c8-0x247c84`) :

| ism `$132` | marche `$2D0` | sauts `$2D4` |
|---|---|---|
| 0 | `$1DFC18` | `$1DFFD8` |
| autre | `$1DFD58` | `$1E09D8` |
| `$FF` | `$1DFE98` | `$1E13D8` |

- Les tables sont contiguës, dans le même ordre que l'arcade.
- **40 entrées** : `$140` octets par table de marche, **`$A00` par table de sauts**.
- Données en longs échangés.
- Lecteurs inchangés : `LSL #6` en image `$51FA2` et `$4F5E6` (`LEA $20(A0,D0.W)` en `$4F5FA`), `LSL #3` en `$4F1E2` et
  `$51DD4`.

Contrôles faits sur les données :
- `$00`, `$01`, `$15`, `$1F` × 3 tables : identiques à l'arcade ;
- `$20-$25` : nouveaux persos ;
- **`$26` = copie de `$00`, `$27` = copie de `$1F`** (remplissage) ;
- entrée `$28` : c'est l'entrée `$00` de la table suivante. Après la dernière table de sauts (`$1E1DD8`), c'est une
  table d'octets (`00 00 … 01 00 01 01 02 02 …`), donc des vitesses absurdes.

### Équivalence avec la PSP et entrées nécessaires

- **Correspondance avec la PSP.** La PSP pose deux pointeurs (`0x2C0/0x2C4`) par style ; l'arcade et Upper aussi
  (`$2D0` marche, `$2D4` sauts), par ism. Il y a 3 jeux dans l'arcade comme dans Upper. Côté PSP, « 32 octets par
  perso » ne correspond pas aux 64 octets de l'arcade. Ce sont sans doute 2 fiches {vx, vy, ax, ay}, vertical et
  diagonale, à répartir en `+$00/$10` (copie) et `+$20/$30` (signes à vérifier). Cette partie est à confirmer sur
  `0x22C1C6` et `0x6099C`. Je n'ai pas lu le code PSP.
- **Entrées `$26-$29`.**
  - `$26/$27` : réécrire les fiches de remplissage dans les 6 tables, 3 × 64 + 3 × 8 octets par perso.
  - `$28/$29` : il faut **agrandir les 6 tables à 42 entrées** (sauts `$A80`, marche `$150`). Comme elles sont contiguës,
    il faut les **déplacer** et corriger les 6 `LEA` de l'image (`$538D2`, `$538D8`, `$538E4`, `$538EA`, `$538F8`,
    `$538FE` ; va `0x247afc`, `0x247b0c`, `0x247b50`, `0x247b60`, `0x247c4c`, `0x247c5c`).
  - Autre solution : garder les 4 persos MAX en `$26/$27` ou réutiliser des n° existants. Mais les pseudo-ID
    `$28-$2C` d'Upper (ECARTS §9) imposent de toute façon des choix pour `$28/$29`.

---

## 5. Méthode et limites

- **Homologues.** 46 viennent de `realign.pkl` (`agent_upper_ecarts`, même image que `carte_image.txt`). 15 ont été
  établis à la main entre les instructions alignées voisines (`voisins.py`, `img.py`, `show.py`). 45 sont des entrées de
  manipulations, appariées par rang ; 1 est absente. Les définitions de manipulation ont été comparées octet à octet dans
  `ext_c80000.bin`. Une correction : `$2FA36`.
- **Comparaison des corps.** L'étendue arcade est balayée linéairement jusqu'au premier `RTS/JMP/BRA` au-delà des
  cibles avant. Côté Upper, le **texte de `carte_image.txt`** est normalisé (`norme.py`) :
  - contrôle ignoré ;
  - idiomes du traducteur ramenés à l'instruction d'origine ;
  - déplacements `.b/.w` masqués `&~3` ;
  - immédiats canoniques (ordre d'octets) ;
  - A5 ramené en numérotation arcade par la table apprise (avec tolérance XOR 1 et voisinage `$20`).

  Mesures : ratio `difflib` et multiensembles sur une fenêtre de 2 × la taille (`multi.py`). Chaque cas à moins de 0,95
  ou avec un manque a été lu côte à côte (`cote.sh`). Les longues routines réorganisées (`$82E36`, `$804DA`, `$2F9BE`,
  `$2FA36`, interpréteur) ont été vérifiées par multiensembles et lecture partielle.
- **Limites.**
  - Les **données** propres aux routines (tables d'animation, fiches) n'ont été comparées que là où elles sont citées
    plus haut.
  - « Identique » porte sur le code.
  - Les va « entrée » sont les étiquettes MIPS citées juste avant l'instruction. Pour `show.py`, la va « instr. » suffit.

## 6. Fichiers

- `ADRESSES-MAX-UPPER.md` : ce rapport.
- `correspondances.tsv` : 108 lignes (arcade, nom, 68K Upper, va instr., va entrée, statut, remarque, source, ratio,
  part alignée).
- Scripts :
  - `carte_mm.py` : carte image → toutes les va et textes, plus les cibles de saut ;
  - `correspond.py` : homologues, étendues, normalisation, comparaison ;
  - `norme.py` ;
  - `statuts.py` : verdicts et TSV final ;
  - `multi.py` ;
  - `interp.py` : interpréteur des manipulations ;
  - `voisins.py` ;
  - `img.py` : image + va + carte ;
  - `arc.py` : désassemblage de `sfa3ud` ;
  - `vue.py` et `cote.sh` : lecture des comparaisons ;
  - `image.py` : reconstruit l'image depuis `roms_ro5/sfa3ud`.
- Caches et sorties intermédiaires (`carte_mm.pkl`, `correspondances_auto.tsv`, `comparaisons.txt`, `image_upper.bin`)
  dans le scratchpad (variable `CACHE_MAX_UPPER`).
- Ordre de relance : `carte_mm.py` → `correspond.py` → `statuts.py`. Pour `multi.py`, `interp.py` et l'image, lancer
  d'abord `image.py <scratchpad>/image_upper.bin`.

---

## 7. Complément (liste régénérée : 113 adresses ; image Upper reconstruite)

**Image reconstruite (carte de 13 h 45).** Les va MIPS ne changent pas. Le code de l'image est décalé, en général de
**+`$28`** : par exemple `$2E422` est maintenant `$301D2`, l'interpréteur des manipulations `$25490`, `$2E3E0` `$3017E`.
Dans les sections 0 à 6, les **adresses 68K de code** sont celles de l'image de 12 h 56. Les adresses à jour sont
dans `correspondances.tsv` (colonne `upper_68k`, recalculée depuis la va avec la carte actuelle ; l'ancienne valeur est
dans `upper_68k_image_12h56`). Les **tables de données n'ont pas bougé** (comparaison octet à octet des images) :
- sauts et marche `$1DFC18-$1E1DD8` ;
- pointeurs `$1DF038` et `$1DF8F8` ;
- types d'objets `$A65F0` ;
- manipulations `$D0CCxx`.

Le mieux est de citer le code d'Upper par sa **va MIPS**.

Mises à jour qui en découlent :
- `TAB_MANIPS` : arcade `$2D5E2 + 8k` (k ≥ 1) → **`$2521E + 10(k − 1)`**. Pour recréer k = 0 : `LEA $D0CCB0,A3 ; BRA $25490`.
- `psp_66890` : **`jmp $301d2`** (va `0x15d184`).
- Les 6 `LEA` des tables de physique sont maintenant en `$538FA`, `$53900`, `$5390C`, `$53912`, `$53920`, `$53926` (va
  inchangées).

**Sorties de la liste** : `$1C2DE`, `$2B828`, `$2D5E2`. Leurs verdicts restent ceux de la section 1 et ne figurent plus
dans le TSV.

### Nouvelles adresses

| arcade | nom | 68K Upper (carte actuelle) | va MIPS (instr. / entrée) | statut | remarque |
|---|---|---|---|---|---|
| `$1C206` | raz d'objet et retour au réservoir (`$6E84/$6E86`) | `$1ABEA` | `0xccfd4` / `0xccfd0` | **modifiée** | efface **en plus** `$DC(A6)` (MIPS `sb a0,220(v1)`, va `0xcd128`) : c'est le compteur de vie des projectiles, lu en `$32EFE`. Le reste est identique. |
| `$2BAF2` | retour en garde (`$2B828` puis `$2BAF8`) | `$53528` | `0x246548` / `0x246540` | identique | `JSR $2B828` (va `0x2448c0`), `MOVEQ #0,D0`, `JMP $2BAF8` |
| `$2BAF8` (demandée, absente de la liste) | lancer l'animation n, état `$2000000`, raz `$2C8`… | `$5352E` | `0x246578` / `0x246570` | identique | `JSR $2A708` (va `0x2398c0`), `$2BB5A` (va `0x2466f0`), `$2F490`, raz `$B0/$5E/$5D/$23A` |
| `$2ECD8` | super : seuil de jauge `$11E` selon l'ism, puis `$2ED02` avec D2 = 1 | `$30C90` | `0x162358` / `0x162300` | **modifiée** | Upper ajoute `TST.B $F0(A6)` → échec en tête, et **force le seuil à `$90` si `$123(A6) ≥ 2`**. Les seuils par ism (`$30` / `$90` / `$48`) et la suite (`TST $B9`, D2 = 1) sont inchangés. |
| `$2ED00` | super : D2 = 0, `$2ED02` (`$4.l = $2020400` → `$2EDA0`, sinon `$31`) | `$30CDC` | `0x16266c` / `0x162660` | identique | `$2ED02` = `0x162690`. Le test long s'écrit `CMPI.L #$40202` dans l'image (disposition). |
| `$2ED28` | super : D2 = 0, `$2ED2A` (`$2000606`, état `$200`, `$B9/$CE/$10D(A5)`, `$6 ∉ {E,10,12}`, cas `$A`, `$2CE`) | `$30D4C` | `0x162b2c` / `0x162b20` | identique | `$2ED2A` = `0x162b50`. Remarque : l'homologue de **`$2ED1C`** (D2 = 1, fonction `0x162800`) a reçu dans Upper le **même seuil de jauge** que `$2ECD8`. |
| `$2EDA0` | super : déclenchement | `$30DF4` | `0x1633e0` / `0x1633d0` | identique | raz `$5D/$5E`, `$2AF7A` (va `0x23eef0`), `$162/$124/$B9`, `$10D/$10E/$8A(A5)`, `$2E8C0` (va `0x15fd70`), `$114 := 2`, `$3F := $254`, raz `$2C8/$D6`, `$2F770`, D0 = 1 |
| `$3323A` | projectile : en-tête d'animation | `$2B3AE` | `0x138520` / `0x138510` | identique | **format conservé** (détail plus bas) |
| `$2E700` | saisie, variante « adversaire `$31` = 0 » (n → `$32F`) | — | — | **absente** | détail plus bas |

**`$3323A`, format de l'en-tête.** Dans l'arcade comme dans Upper, `A0 = $60(A6)`, puis
`$90/$94/$98/$9C/$A0 := A0 + mot[0], mot[2], mot[4], mot[6], mot[8]` : 5 mots signés relatifs au début de l'en-tête.

Dans Upper (va `0x138520-0x1386b0`) :
- `$60` est un long échangé, puis passé à CONV `$400`. Un pointeur d'espace PS2 est converti ; une adresse d'image passe
  telle quelle.
- Les 5 mots sont lus tels quels (`MOVE.W $0002(A0)`…).
- Les 5 pointeurs sont écrits en longs échangés.

Un en-tête MAX de 5 mots relatifs convient donc tel quel. Seuls le pointeur `$60` et les longs écrits suivent la
disposition.

La table voisine **`$3327A`** (lue par `$331D0`, indexée par le **type** d'objet `$2(A6)`) est dans Upper en image
`$0A9510` (`T_6131d0`, va du lecteur `0x1381a8`) :
- arcade : 37 entrées (`$00-$24`) ;
- Upper : 38 entrées (`$00-$25`), le type 7 étant rempli dans Upper ;
- dès l'entrée `$26`, une autre table commence : **aucune place libre**, contrairement à `$32F46` (`$26/$27` nuls).

**`$2E700` absente.** Arcade : `MOVE.B D0,$32F ; A1 = $38(A6) ; TST.B $31(A1) ; BNE $2E52A (échec) ; BRA $2E646`. Dans
Upper, la suite commune `$2E646` (étiquette `0x15eb70`, image `$304EE`) n'a que trois appelants :
- `$2E636` (test `$31` = non nul) ;
- `$2E6EC` → va `0x15f4b4` (test `$2C8`) ;
- `$2E714` → va `0x15f574` (sans test).

Il n'y a aucune variante « `$31` = 0 ». Équivalent à écrire, sans `$32F` et en disposition image :
`MOVEA.W $38(A6),A1 ; TST.B $30(A1) [= $31 arcade] ; BNE.S échec ; JMP $304EE [va 0x15eb70]`, avec
`échec : MOVEQ #0,D0 ; RTS` (= `$2E52A`, va `0x15dc90`).

### Variable caméra `$290(A5)`

- **Arcade** : `$FF8290`, un mot. C'est le **X de la caméra** dans le décor, c'est-à-dire le bord gauche de l'écran.
  - Les persos et objets passent en X écran par `SUB.W $290(A5)` (`$23CBC`, `$8DE4E`, `$A78C6`) ou l'inverse
    (`ADD.W`, `$6EF34`).
  - Il est posé à `#$40` au début d'un combat (`$1E00A`… puis `$26(A5) := $290`, scroll du plan), à `#$200` en
    `$ABE32`, et borné à `$1C0` (`$AF3BA`).
  - Son voisin `$292` est écrit en même temps (`$26024`, `$AAEF6`).
- **Upper** : **`$292(A5)`** (`$FF8292`). Les deux mots du long `$290` sont échangés par la disposition du portage. Le
  MIPS lui-même adresse `0x292` :
  - va `0x15b060` : `addiu v0,v0,0x292 ; sh` = `MOVE.W #$40,$0292(A5)`, homologue de `$1E00A` ;
  - `$0292(A5),$0026(A5)` pour `$1E02E` ;
  - `CMPI.W #$1C0,$0292(A5)` (va `0x106c54`) pour `$AF3BA`.

  En sens inverse, l'arcade `$292` devient `$290` (va `0x2b574`). Aucun relogement A5 : cette zone basse n'est pas
  dans la table de relocalisation, la seule différence est l'échange de demi-mots. Même contenu, sans changement
  constaté.

  → Dans le code MAX (`moteur_max_main.s` l. 738, `move.w $290(a5),d0`) : **`move.w $292(a5),d0`** en disposition
  Upper.

### `physique_max_arcade.json` : les entrées `$26-$29`

- **Format.** Il est bon. Chaque entrée de saut compte 16 longs (64 octets) : 4 fiches {vx, vy, ax, ay} en 16.16, avec
  `+$10` = copie de `+$00`, `+$20` à vx < 0 et ax = `+$500`, `+$30` à vx > 0 et ax = `−$500`, comme les 40 entrées
  existantes. Chaque entrée de marche compte 2 longs (8 octets), le premier négatif. Ce sont des **valeurs logiques**
  (gros-boutiste, arcade). Dans les tables d'Upper, elles doivent être **écrites en longs échangés** : `00072000` est
  stocké `2000 0007`, comme le reste de ces tables.
- **Étiquettes d'ism inversées dans le JSON.**

  | table | étiquette du JSON | ism réel (code `$2BE6A`) |
  |---|---|---|
  | saut `$DDF92` | `$132=$FF` | **autre** |
  | saut `$DE792` | « autre » | **`$FF`** |
  | marche `$DD592` | `$132=$FF` | **autre** |
  | marche `$DD692` | « autre » | **`$FF`** |

  Dans Upper :

  | ism | sauts | marche |
  |---|---|---|
  | 0 | `$1DFFD8` | `$1DFC18` |
  | autre | `$1E09D8` | `$1DFD58` |
  | `$FF` | `$1E13D8` | `$1DFE98` |

  Les valeurs du JSON sont identiques pour les 3 ism, donc l'erreur est sans effet aujourd'hui. Il faut la corriger
  avant d'y mettre des valeurs différentes par style.
- **Remarque.** Dans l'arcade comme dans Upper, la marche des persos existants **varie selon l'ism** (Ryu :
  `FFFD0000/00020000`, `FFFCE000/00022000`, `FFFCF000/00021000`). Le JSON donne la même marche aux 3 styles : à
  confirmer si c'est voulu.
- **Place.** `$26/$27` remplacent les copies de remplissage d'Upper. `$28/$29` n'ont **pas de place** : les 6 tables
  font 40 entrées et sont contiguës, il faut les déplacer et les agrandir (voir §4).

Scripts ajoutés : `cartenv.py` (carte actuelle par va ou par adresse image) et `complement.py` (TSV à 113 lignes,
68K recalculées ; à lancer après `statuts.py`).
