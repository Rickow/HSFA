# Étape A de la réorganisation des données : instrumentation (SFA3)

Plan : `github/docs/architecture/ARCHI-Reorganisation-Donnees.md`. Contexte : HANDOFF §29, §44, §63, §76, §98, §104 et §138.
Aucune ROM ni aucun fichier du traducteur n'a été modifié. Tout est dans `work/agent_reorg_A/`.

## 0. Référence des mesures

- **ROM traduite** : copie figée de `work/mame/roms_tr` prise le 2026-10-07 à 15:17 (ROM du §138). Elle est dans `roms_tr/`, avec `sz3ud.03c` = `d57d087b…`. Les md5 sont dans `md5_roms_tr.txt`, ainsi que ceux de `carte_image.txt` et `ext_a04000.bin`, copiés au même moment.
  - L'image programme désentrelacée est dans `prog_tr.bin`.
  - La ROM partagée est depuis passée à la §140 (`a51fe745…`). **Toutes les mesures ci-dessous portent sur la copie §138.** Pour refaire les mesures sur la §140, il faut recopier `roms_tr`, `carte_image.txt` et `ext_*.bin`, puis relancer.
- **Arcade** : `work/mame/roms` (`REF=1`), MAME 0.285 standard. Chaque exécution a ses propres `-nvram_directory`/`-cfg_directory` (sous `nv/` et `cfg/`) et tourne sous `nice -n 19`.
- **Transparence vérifiée** : le test des commandes, instrumenté, donne **42/42 actions identiques**, avec 5359 tours en 4019 images (133,3 %), comme sans instrumentation.
- **Upper non traité** : une validation d'Upper occupait `mame_ro5` pendant toute la session (§6).

## 1. Outils

Tous les outils sont dans `outils/`. Les lanceurs sont `lancer.sh` et les fichiers de `runs/`.

| outil | rôle |
|---|---|
| `journal_conv.lua` | **Journal des conversions.** S'accroche aux talons de données `CONV_A0..A6` (`$400 $41E $440 $462 $484 $4A6 $4C8`) et de code `CCONV_A0..A6` (`$3FF000 $3FF01E … $3FF0C8`), par prise sur l'espace *opcodes*. Pour chaque appel, il relève : la valeur de An, l'appelant (PC = adresse de retour), la case d'origine et le dernier écrivain de la case si elle est en RAM. La case d'origine est la plus récente lecture d'un long `(a, a+2)` de même valeur, moitiés échangées ou natif ; elle est cherchée dans un anneau des 64 dernières lectures (RAM, ROM de données, RAM du portage, blocs externes). Agrégation en Lua, vidage à l'arrêt. Lecture seule. |
| `analyse_conv.py` | Analyse du journal → `.json` + `.txt`. Contenu : conversions faites ou laissées par zone de valeur ; cases d'origine (ROM / RAM) ; croisement origine × zone ; classement des sites pour les étapes B-D ; grappes de tables ROM (adresse PS2 comprise) ; cases RAM et leurs écrivains (va MIPS + mnémonique de la carte). |
| `suivi_ecrivains.lua` + `analyse_suivi.py` | Passe 2 : pour les cases RAM qui fournissent des pointeurs PS2, indique qui les écrit et d'où vient la valeur (copie d'une table ROM, autre case RAM, ou immédiat/calcul). |
| `carte_vars.py` → `vars.json` | Carte des variables. Côté traduction : 1035 accès A5 (adresse/taille) et 630 champs A6 < `$400`, tirés de la carte. Côté arcade : 1018 / 631, tirés de `agent_couverture/arc_insn.pkl`. Trois adresses arcade candidates par variable : vote des instructions alignées (`agent_symboles/_cache/paires_a5.json`), recette (avec relocation de la zone basse, `reloc_a5.pkl`), modèle typé (`typed_rule.py`). |
| `compare_ram.py` | **Oracle RAM traduction ↔ arcade** (§3). Modes `--synchro`, `--tournee` et `--attr`. Sorties `.txt`, `.tsv` (une ligne par variable) et `.json`. |
| `disposition.lua` + `disposition_carte.lua` | **Accesseur par adresse arcade** (§4). La table est générée par `gen_disposition.py` à partir de `vars.json` et du verdict de l'oracle. |
| `runs/attr.lua` | Attraction sans entrée. Vide la RAM 30 images après chaque changement de (`$FF8000`, `$FF8002`, `$FF8004`), avec des noms d'état identiques côté arcade et côté traduction. |
| `runs/synchro.lua`, `runs/adversaires.lua`, `runs/tournee_sync.lua` | **Manches synchronisées** pour l'oracle (§3). |
| `runs/tournee_j.lua`, `commandes_j.lua`, `tournee_f.lua`, `tournee_s.lua`, `attr_s.lua` | Pilotes qui chargent le journal ou le suivi, puis `tournee.lua` / `commandes.lua` sans modification. |

Pièges rencontrés, utiles pour la suite :
- **Prélecture du 68000.** Le mot qui suit le `RTS` d'un talon est l'entrée du talon suivant, et il est prélu à chaque retour (autant de fausses entrées que de vraies). Un appel authentique se reconnaît à un PC situé hors de la zone des talons : PC vaut alors l'adresse de retour, et le `JSR` n'a pas encore empilé.
- **Prise d'écriture trop tôt sur l'arcade.** Une prise d'écriture posée avant l'image 1000 casse le test de RAM de l'amorçage : l'arcade reste à l'état 0.
- **Plages qui se chevauchent.** La plage du code PS2 `[$212B00,$583C40)` recouvre celle des données ROM 68K `[$93000,$3C0000)`. Une valeur de cet intervalle peut donc être un pointeur 68K déjà converti ou une adresse de code PS2. L'analyse tranche par la table de hachage du code (début de fonction connu ⇒ code).

## 2. Journal des conversions : résultats

Parcours : attraction (20 000 images), tournée Ryu (`PERSO=00`, 40 000 images, avec et sans graine, puis avec l'ordre des adversaires imposé), test des commandes. Total : **146 800 images, 16,8 M appels authentiques de talons**.

| | appels | convertis | laissés |
|---|---|---|---|
| talons de données | 14,13 M | 4,74 M (33,6 %) | 9,39 M (66,4 %) |
| talons de code | 2,66 M | 2,66 M (100 %) | 0 |

Par parcours, la proportion est la même : données converties 38 % (attraction), 33 % (tournée), 31 % (commandes).

**Valeurs vues aux talons de données** (appels) :
- 68K ROM déjà converti : 3,09 M ;
- code PS2, laissé puis converti par le talon de code qui suit : 2,68 M ;
- données PS2 : 2,42 M ;
- RAM PS2 : 2,21 M ;
- 68K RAM déjà converti : 2,07 M ;
- trou `$980000`, c'est-à-dire des pointeurs vers le bloc externe `$A04000` (fichier 289, servi par `banc_mem.lua`) : 1,07 M ;
- matériel étiqueté `$01` : 0,48 M ;
- vidéo PS2 : 0,09 M ;
- tables natives : 0,02 M.

**Sites.** 655 sites statiques (631 données, 24 code), dont 379 actifs sur ces parcours (358 données, 21 code) :

| classe (données) | sites | appels |
|---|---|---|
| **ne convertissent jamais** (valeur toujours déjà 68K, code, ou trou) | **230** | **8,56 M** (61 % des appels de données) |
| conversions venant de tables ROM seulement | 82 | 0,63 M |
| conversions venant de cases RAM seulement | 28 | 0,10 M |
| mixtes ROM/RAM ou ROM + quelques lectures non retrouvées | 18 | 4,83 M |
| valeur calculée (aucune lecture correspondante) | 1 | ~0 |

Côté code, la provenance est presque entièrement ROM : 12 sites ROM pur, 7 sites ROM avec quelques lectures non retrouvées (2,5 M appels), et 1 site RAM (`$0199A8` `JMP (A0)`, 14 k appels : pointeur `$40(A6)` d'objet incrémenté par `ADD.L`). Les sites « ne convertissent jamais » chargent surtout depuis la RAM (5,5 M appels), puis depuis la ROM (3,0 M). Le premier poste est `MOVEA.L $1C(A6),A0` (pointeur d'animation des objets) : la traduction le range déjà en 68K.

**Cases d'origine**

| zone | cases | contenu |
|---|---|---|
| **ROM de données** | **9 144** (+194 tables natives) | 5 926 pointeurs de données PS2 ; 224 pointeurs de **code** PS2 (114 vus seulement par le talon de données, 110 par le talon de code) ; 21 pointeurs vers la **RAM PS2** (tables `T_587740` `$096B00`, `T_58af80` `$09A344`, `T_5924b0` `$0A1870` : 2,2 M appels à elles seules) ; 4 vers la vidéo ; **2 969 vers le bloc externe `$A04000`** (trou, laissés tels quels). 6 693 grappes contiguës, la liste et les adresses PS2 sont dans `conv_tous.json` / `tables_rom`. |
| **RAM** | **228** | 185 contiennent **déjà une adresse 68K** (ROM 139, RAM 41, matériel 5 : 5,6 M appels, talons inutiles aujourd'hui) ; **31 contiennent un pointeur de données PS2 brut** (0,26 M appels) ; 4 un pointeur de code PS2 ; 5 un pointeur de tables natives. |
| inconnue | 1 groupe | 37 k appels : valeurs calculées (`MOVEA.L Dn,An`, noyau `$0C40`, `$0B9C`). |

**Qui alimente les cases RAM à pointeurs PS2** (passe 2, `resultats/suivi.txt` : 35 cases, 84 couples case/écrivain) :
- le plus souvent, une **copie depuis une table ROM** : `MOVE.L 0(A0,D0.W),$88/$C0/$E6/$264(A6)` (tables PS2 `0x67D6FC…`, `0x67FE7C…`), `MOVE.L $FFFC(A0),$2B0..$2BC(A6)`, `MOVE.L $FFFC(A1),$FFFC(A0)` (table PS2 `0x85104C` → `$FFD308…`) ;
- sinon un **calcul sur le pointeur** : `ADD.L D1,D7 sur $40(A6)`, `ADDI.L #$94` ;
- un **talon natif** : `$FF3E48` (= `$BE48(A5)`, pointeur d'animations) est rempli par les talons `STUB_ANIM` (`$810`) de `mame_test.py`.

Répartition des couples case/écrivain : 39 copies ROM, 31 immédiat/calcul, 11 RAM→RAM, 3 tables natives.

Fichiers : `resultats/conv_tous.{txt,json}` (union des parcours), `conv_attr`, `conv_tournee`, `conv_commandes`, `suivi.{txt,json}`. Journaux bruts dans `journaux/`.

## 3. Oracle RAM traduction ↔ arcade

**Synchronisation.** Les deux machines jouent la même tournée (`tournee.lua` sans modification), avec trois ajouts :
1. **Même ordre d'adversaires.** La liste de 10 persos est à `$FF0F82` sur l'arcade et à `$FF0E4C` dans la traduction (relogée de −`$136`, octets XOR 1). Elle diffère naturellement : arcade `0f 10 16 0d 09 03 06 0b 01 0a`, traduction `04 07 10 0c 09 02 0e 0b 01 0a`. Elle n'est **pas** tirée de la graine `$FF80AE` : imposer la graine ne la change pas. Elle est imposée des deux côtés par une prise d'écriture qui remplace la valeur (`ADV=…`), posée après l'image 1000.
2. **Même hasard au début du combat** : hors combat, `$FF80AE` reçoit `SYNC_SEED`.
3. **Vidages** aux images 1, 30 et 60 du combat, avant les entrées de J1.

Résultat : 19 manches appariées, mêmes décors et adversaires, soit **57 paires**, plus **130 paires** d'attraction sur les mêmes changements d'état (`dumps/sync3_*`, `dumps/attr_*`).

**Verdicts, `resultats/ram_oracle.{txt,tsv,json}`, 187 paires.** Une variable est un couple (adresse traduction, taille) ; une même adresse lue en octet et en mot compte deux fois. Lecture des catégories :
- **identique** : égale dans toutes les paires ;
- **identique sous une autre forme** : égale partout, mais sous une autre adresse candidate ou une autre forme (octets échangés `u8x2`, `u8x4`, `s16x2`) ;
- **dynamique** : égale dès que l'état est le même (au moins une paire non nulle égale, ou ≥ 90 % de paires égales) ;
- **structurelle** : jamais égale ;
- **forme X (dynamique)** : égale seulement sous une autre forme.

| | variables A5 (1035) | champs joueur J1+J2 (630) |
|---|---|---|
| **identique** | 147 | 31 |
| identique sous une autre forme / adresse | 22 | 16 |
| **dynamique** | 203 | 173 |
| toujours nulle des deux côtés (non probant) | 373 | 325 |
| **propre au portage** (`$FF4000-$FF4FFF`, ou ni vote ni accès arcade) | 237 | 14 |
| forme X (dynamique) | 12 | 28 |
| pointeur (valeur propre à la disposition ROM) / matériel `$01` | 4 | 12 |
| **structurelle** | 37 | 30 |

Pour A5, sur les 425 variables non nulles et comparables :
- **350 (82 %) sont identiques ou égales dès que l'état est le même, avec la recette actuelle** ;
- 22 de plus le sont sous une autre forme ou une autre adresse, soit **372 (87,5 %)** ;
- 12 sont du type « forme X (dynamique) » ;
- 41 sont structurelles ou des pointeurs.

Points saillants de l'oracle :
- **Champs joueur qui contiennent des pointeurs PS2 bruts** (`$88`, `$C0`, `$E6`, `$264`, `$2B0-$2BC` en long : traduction `0x6802E0…`, arcade `$100000…`). Ce sont exactement les cases RAM du journal : l'oracle et le journal se recoupent.
- **Pointeurs 68K** (`$1C`, `$60`, `$8C-$A0`, `$14C`, `$2D0`, `$2D4`, `$220-$234`) : ils diffèrent seulement parce que les ROM n'ont pas la même disposition.
- `$150` et `$FF80E0`, `$FF8380` (pointeurs matériels) diffèrent par l'étiquette `$01` du banc.
- **Longs s32 dont la partie entière n'est pas où la recette l'attend** : `$FF8210`/`$FF8212`, `$FF8290`, `$FF8214`/`$FF8216`, `$FF82A4`/`$FF82A6` ; champ joueur `$03E`→`$03C`. Les deux mots sont vus inversés (traduction `0 / 48` contre arcade `48 / 0`). Ce sont des cas que le modèle typé doit couvrir à l'étape E.
- **Octets par paire (`u8x2`)** pris pour des mots par la recette : champ `$0C` (`00FF` contre `FF00`), liste d'adversaires.
- **Propres au portage, confirmés** : `$FF3BD4`/`$FF3BDC`/`$FF3BE4` ; champ `$01A` (`$4000`/`$6000` : bits d'attributs, cf. §64) ; `$FF801A`.
- Les votes des instructions alignées sont corrigés par l'oracle dans quelques cas. Exemple : le champ `$038/$039` en octet est identique avec l'adresse du modèle typé, pas avec celle du vote. `gen_disposition.py` retient l'adresse que la RAM valide.

Comparaison brute par zones de 4 Ko (identité d'adresse, sans relocation) : `$FF8000-$FFFFFF` est identique à 10-65 % selon la zone, ou à octets échangés (`$FF9000-$FFCFFF` : 43-65 %). La moitié basse `$FF0000-$FF3FFF` est à ~0 % d'identité : c'est attendu, elle est relogée (§4 de SYMBOLES), et seule l'analyse par variable la relocalise.

## 4. `disposition.lua`

```lua
local D = dofile("<workspace>/work/agent_reorg_A/outils/disposition.lua")
D.lire(0xFF80AE, 2)                 D.ecrire(0xFF8115, 1, 8)
D.lire_champ(0xFF8400, 0x102, 1)    D.ecrire_champ(base, depl_arcade, taille, v)
D.force("ff8115=8,Lff8458=12345,Wff8050=90")      -- syntaxe FORCE de tournee.lua, + W
D.adresse(a, n) -> adresse traduction, forme ;  D.octets(a, {...}) -> {adresse traduction = octet}
```

- **En arcade** (`REF=1`), l'accesseur est l'identité.
- **En traduction**, il applique dans l'ordre :
  1. la recette (octet XOR 1, mot à la même adresse, long à moitiés échangées) ;
  2. les 25 intervalles relogés de la zone basse ;
  3. 132 exceptions par variable (59 en A5, 73 champs), qui viennent des votes ou de l'oracle ;
  4. 50 formes établies par la RAM : `u8x2`, `u8x4`, `s16x2`.

**Validé** : à la 30e image de la 1re manche synchronisée, il lit les 215 variables « identiques » (A5 et champs J1/J2, relogées comprises) **par leur adresse arcade**. Les **262 lectures sur 262 sont égales** au vidage arcade du même instant (`runs/test_disp*.lua`).

L'accesseur sert déjà au forçage de la liste d'adversaires (`runs/adversaires.lua`) et à la détection des combats (`runs/synchro.lua`). Après les étapes B-E, il suffit de régénérer la table (`gen_disposition.py`), les scripts restent inchangés.

## 5. Ce que ça implique pour les étapes B-E

- **B, pointeurs de code.**
  - Tout le travail du talon de code (2,66 M appels) vient de **cases ROM** : 224 cases, surtout de petites tables d'aiguillage (`T_589760` `$098B20`, 24 cases, 1,7 M appels ; `T_58a520`, `T_58c990`, `T_588bd0`, `T_585ca0`…). Seul `$0199A8` lit un pointeur de code en RAM (`$40(A6)`, calculé).
  - Ces mêmes tables passent **d'abord** par le talon de données, qui laisse la valeur (2,68 M appels inutiles). Reloger ces 224 cases et retirer les deux talons à ces sites supprime ~5,3 M appels sur 16,8 M (32 %).
  - Le chevauchement code PS2 / ROM 68K (`$212B00-$3C0000`) disparaît en même temps : aujourd'hui, une adresse 68K de données passée au talon de code serait convertie à tort si elle tombait sur un début de fonction PS2.
- **C, tables ROM de données.**
  - 5 926 cases de pointeurs de données PS2, 21 de pointeurs RAM PS2 (2,2 M appels, relogement trivial +`$6F0000`, à faire en premier), 194 de tables natives, 4 vidéo. Les grappes et leurs adresses PS2 sont dans `conv_tous.json`.
  - **2 969 cases visent le bloc externe `$A04000`** et restent brutes : il faut décider leur sort avant de retirer des talons (une adresse fixe dans le fork ou un relogement).
  - Le journal ne voit que les cases **parcourues**. Le relogement statique doit partir de la structure des tables (pas, taille d'élément) et utiliser le journal comme contrôle, pas comme liste complète.
- **D, RAM.**
  - 185 des 228 cases RAM lues avant un talon contiennent déjà une adresse 68K. 230 sites (61 % des appels de données) **ne convertissent jamais** sur ces parcours.
  - Les 31 cases RAM qui portent encore des pointeurs PS2 sont remplies par des **copies de tables ROM** (`MOVE.L 0(A0,D0.W),$xx(A6)`) ou par de l'arithmétique sur ces pointeurs. Une fois C fait, elles deviendront 68K d'elles-mêmes. Exception : `$FF3E48`, rempli par les talons natifs `$810` : `mame_test.py` devra y émettre une adresse 68K.
  - Retirer un talon demande quand même une preuve statique, puisque « jamais » ne vaut que pour la couverture. La passe 2 (`suivi_ecrivains.lua`) est à relancer sur toute case candidate.
  - Critère de fin : **journal vide** (aucune valeur PS2 vue par un talon) sur les 72 fins et les modes.
- **E, RAM typée.**
  - L'oracle est en place. Les 372 variables A5 identiques (sous une forme ou une autre) ou dynamiques forment la base de non-régression. Les 37 structurelles et 12 « forme X », plus les 30 + 28 côté joueurs, sont la **liste de travail du typage** : s32 dont la partie entière est à +2, `u8[2]`, `u8[4]`.
  - 373 variables A5 restent toujours nulles sur ces parcours : il faudra d'autres scénarios (modes, options, fins) pour les juger.
  - À chaque bascule, il suffit de relancer `runs/tournee_sync.lua` des deux côtés puis `compare_ram.py` : les « identique » doivent le rester et les « structurel » doivent passer à « identique ».

## 6. Reste à faire et limites

- **Upper** : non mesuré, car une validation d'Upper occupait `mame_ro5` (consigne).
  - Les talons ont la même disposition (`build_conv` à taille fixe : mêmes adresses `$400…` et `$3FF000…`), donc `journal_conv.lua` s'applique tel quel sur le fork.
  - Il faut en revanche adapter `analyse_conv.py`, dont les plages sont lues dans l'image avec des `assert` propres à SFA3. Lancement : modèle `scripts/validation/nonreg_ro5.sh`, en chargeant le journal avant `tournee.lua`.
- La provenance « inconnue » (37 k appels) correspond aux valeurs calculées, et aux lectures sorties de l'anneau de 64 mots avant le talon.
- L'oracle d'attraction s'aligne sur des changements d'état et non sur l'instant exact : les variables dynamiques y diffèrent plus souvent que dans les manches synchronisées.
