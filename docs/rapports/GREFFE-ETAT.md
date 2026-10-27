# Greffe de l'Arcade d'Upper sur Hyper (voie B) : état à lire en premier

Version publiée le 2026-10-24, résumée du journal de travail de la greffe (`work/greffe_arcade/ETAT.md`, hors dépôt :
il contient les commandes exactes et l'historique complet). Rapports détaillés : [GREFFE-PREPARATION](GREFFE-PREPARATION.md),
[GREFFE-DECORS](GREFFE-DECORS.md), [GREFFE-ETAPE2](GREFFE-ETAPE2.md) à [GREFFE-ETAPE6](GREFFE-ETAPE6.md) ; journal
§144, §147, §165. Outils publiés : `tools/greffe-arcade/` (étapes 2-3 ; les interrupteurs des étapes 4 à 7 ne sont pas
encore versés, [POINT-ETAPE-2026-10-21](POINT-ETAPE-2026-10-21.md) §2.1).

## 1. En bref

- **But** : le produit final part d'Hyper (`ro9`), auquel on greffe la couche du mode Arcade d'Upper (`ro5`) au niveau
  MIPS, avant traduction. Le module obtenu s'appelle `ro9a`. Upper sert d'oracle : mêmes fins, mêmes durées.
- **Référence figée : `ro9a7_fige`** (étape 7, 2026-10-18). Balayage des 85 combinaisons perso × version
  sélectionnables : **60 fins au bout sur 85**, **aucune fin perdue** contre l'étape 6 (`ro9a6b_fige`, 60/85 aussi,
  mais pas les mêmes durées ni le même CONTINUE).
- **Depuis `ro9a7_fige`** : `FIN05_GREFFE` (construction `e9l`, non figée) fait aboutir la fin de 05 dans ses
  4 versions (3 761 images contre 3 760 dans Upper) ; balayage f13 : **64/85**, sans perte.
- **Durées** : les fins abouties durent comme dans Upper à ±2,2 % près (24 sur 64 à ±0,1 %) ; 12 fins abouties n'ont
  pas de durée de référence relevée dans Upper.
- **En attente** : la v151 du traducteur (journal §171). Ensuite : rebase de la greffe, application des décisions
  D1-D3 ([CONFLITS](../../re/CONFLITS.md)), puis nouveau balayage.

## 2. Étapes

| étape | construction de référence | résultat |
|---|---|---|
| 2 | — | l'Arcade d'Upper tourne dans Hyper et enchaîne 3 combats contre la liste d'Upper ([GREFFE-ETAPE2](GREFFE-ETAPE2.md)) |
| 3 | `ro9a3_fige` | Ryu ZERO 3, Ryu ALPHA et Chun-Li ZERO 2 vont jusqu'à la fin et au GAME OVER ([GREFFE-ETAPE3](GREFFE-ETAPE3.md)) ; défaut `PILE_LUI` du traducteur trouvé (v149) |
| 4 | constructions `e5*` | fins suivies plus loin (`RELAIS_J`, `DECOR_UPPER_CHOIX`, `DECOR_FIN`, `A5_116`) ; 2ᵉ fenêtre du bloc en `$C38000` ([GREFFE-ETAPE4](GREFFE-ETAPE4.md)) |
| 5 | — | 59 fins sur 85 au bout, durées à ±2,2 % d'Upper ([GREFFE-ETAPE5](GREFFE-ETAPE5.md)) |
| 6 | `ro9a6b_fige` | 60/85 : `PTR_BAS` (conflit 18/0E réglé), `FE_TABLE`, `PLANS_CONT` (CONTINUE sur le décor grisé du combat, comme Upper) ([GREFFE-ETAPE6](GREFFE-ETAPE6.md)) |
| 7 | **`ro9a7_fige`** | 60/85 sans perte ; CONTINUE : la barre « CONTINUE » vit toute la scène ; fin 02 à la durée d'Upper ; fin de Ken (01) complète |

## 3. Étape 7 : ce qui a changé

Quatre interrupteurs, **à 1 par défaut dans `ro9a7_fige`** (une construction par défaut redonne les mêmes octets) :

| interrupteur | problème | correctif |
|---|---|---|
| `CONT_GREFFE` | l'objet `$1E` de CONTINUE (la barre verticale, pas le chiffre) partait chez Hyper par la règle de tri « HYPER » et se libérait au bout de 74 images | ses deux sous-états d'Upper sont greffés : l'objet vit toute la scène, écritures identiques à Upper |
| `DESC_FIN` | le champ +`$18` des descripteurs d'acteurs de fin (4 octets de données) était pris pour un pointeur de code et relogé : l'octet de délai d'apparition valait l'octet bas d'une adresse | 144 cases exclues du relogement ; l'acteur de Ken apparaît et se libère aux mêmes images que dans Upper |
| `BANQUES_LU` | une animation de banque lue par Upper n'était pas copiée (banque coupée trop tôt) | chaque banque est copiée jusqu'à la fin de la dernière animation lue ; les creux du prolongement accueillent d'autres régions (bloc de 3,93 Mo) |
| `ANIM24` | Upper lit un pointeur d'animation 24 bits et le masque (`ANDI.L #$00FFFFFF`) : l'adresse 68K du bloc perdait son étiquette `$01` | le masque de la copie remet l'étiquette (`ORI.L #$1000000`) |

Après la référence : **`FIN05_GREFFE`** (défaut 0). L'acteur `$4D` de la fin de 05 était remplacé par un objet d'Hyper,
qui lisait ensuite une table de travers. Cinq routines d'Upper « non vues en Arcade » sont greffées à la place.

Essais écartés pendant l'étape 7 : `CONT_GREFFE` seul (perd Ken ×4, à cause du descripteur : d'où `DESC_FIN`) ;
`REUTIL_VOISIN` (réutilisation au décalage du voisin : sans effet sur la vraie cause).

## 4. Fins qui n'aboutissent pas encore (balayage f13, 21 sur 85)

| perso | versions | symptôme | piste |
|---|---|---|---|
| 07 | 4 | fin jamais atteinte | aussi dans l'oracle Upper : allonger la partie |
| 17 | A, Z2, Z3 | exception pendant la fin | objet `$5E00` traité par le moteur d'Hyper |
| 19 | Z3 | exception pendant la fin | pose d'animation : fichier d'animation natif de fin mal choisi (adresse impaire) |
| 15, 1C, 1D, 22, 23 | Z3 | exception pendant la fin | dessin d'Hyper ; avec l'affichage d'Upper, plantent dans des copies d'Upper |
| 1B, 1E, 21 | Z3 | exception pendant la fin | 21 : table de scènes ; à suivre |
| 1F | Z3 | exception avant la fin | — |
| 20 | Z3 | fin non atteinte | — |
| 06 Z, 0F A, 11 Z2 | 1 chacun | exception en combat | à vérifier dans Hyper seul, adversaire imposé |

Hors périmètre de l'étape 7, en attente d'autres chantiers : chiffre et texte de CONTINUE, lettres du GAME OVER,
scène 1 des fins et décor du boss (il faut les bases de plans par décor d'Upper : chantier des décors), planisphère.

## 5. Place mémoire

| zone | usage |
|---|---|
| 68K `$FF7F00` | drapeau « partie Arcade » ; **D2 : à déplacer en `$FF7E00`** (MAX garde `$FF7F00-$FF7FFF`) |
| 68K `$FF43BE-$FF4CA2` | variables A5 d'Upper relogées |
| PS2 RAM + `$7FF00..$7FF05` | détournées vers les registres des bases de plans `$804200-$804205` (jamais lues ni écrites en mémoire) |
| ROM graphique `$4000000` | `hsfa_plans.bin` d'Upper (écrans d'Upper, bases `400/440/4a0`) ; cœur FBNeo : patch 0008, pilote `sfa3hahsfa` |
| blocs externes | 1ʳᵉ fenêtre `$D0C000-$EFFFFF`, 2ᵉ fenêtre `$C38000-$C83FFF` ; marge ≈ 100 Ko |
| image 68K `$3A0000-$3BFFFF` | **D3 : réservé au code MAX** ; les tables d'animation natives de la greffe descendent de `$20000` |
| code greffé | zone du Z80 recompilé d'Hyper et 2ᵉ zone d'exécution |

Manque de place : la ROM programme est pleine et le bloc de la greffe proche de sa limite. Voies : trous de la carte
68K (patch 0009, prototype) et banque commutée (`$804210`, non prototypée) : [COEUR-BANQUES](COEUR-BANQUES.md) §B.

## 6. Prochaines étapes

1. Rebase sur la v151 du traducteur (règles du §171).
2. Décisions D1-D3 : drapeau en `$FF7E00`, tables natives abaissées de `$20000`, ids MAX `$26-$29` dans Hyper.
3. Balayer les 85 ; figer `FIN05_GREFFE` s'il ne perd rien.
4. Fins restantes, une à la fois, chaque correctif derrière un interrupteur ; toute fin perdue = correctif écarté.
5. Décor de l'Arcade : décision D4, le décor suit le joueur 2, perso et version, SFA1 compris
   ([GREFFE-ETAPE4](GREFFE-ETAPE4.md) §9).
