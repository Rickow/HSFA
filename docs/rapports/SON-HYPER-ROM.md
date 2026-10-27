# Son propre à Hyper : voix et sons d'origine par version (SFA1 pour ZERO, SFA2 pour ZERO 2 et ALPHA)

Agent `agent_son_hyper_rom`, 2026-10-10 (deux passes : prototype QSound, puis reprise). J'ai écrit seulement dans
`<workspace>/work/agent_son_hyper_rom/`.
- Lecture seule ailleurs : `agent_voix_max/roms_voix` (v2, `hx3.01` md5 `922642bf…`), `agent_flux/mame-fork-flux`,
  `mame_ro9`, `src/hsfa`, le module `ro9` et X_DATA n'ont été que lus.
- MAME : `nice -n 19`, NVRAM et config dans ce dossier, jamais `-state`, au plus 3 instances à moi en même temps.
  `mame_ro5` (validation d'une autre session) n'a pas été touché. Aucun binaire partagé remplacé : le fork modifié est
  une copie, `mame-fork-son/`.
- La construction `ro9` d'essai a été faite **dans ce dossier** (`b9_ctl/`, `b9_son/`), avec une copie du traducteur
  (`untranspile_son/`), comme l'avait fait `agent_coups`. Rien n'a été écrit dans `mame_ro9` ni dans `scripts/`.

## 0. En bref

**Décisions de l'utilisateur appliquées** : voix d'origine par version ; viser tout (voix, cris, K.O., annonceur,
bruitages) ; pas de variante « trous » (`roms_hyper_trous/` supprimé, option marquée abandonnée) ; agrandir la capacité
est accepté ; redirection par le programme traduit.

1. **ROM QSound reconstruite sur `roms_voix` v2** (§11.1). `roms_hyper/` est à jour et reproductible (md5 identiques
   d'une génération à l'autre).
   - Les 202 commandes sont **les mêmes numéros** qu'avant ; aucune ne touche une voix MAX v2 (ni à ±`$500`).
   - 202/202 commandes conformes registre par registre, corrélation médiane 0,985.
   - Non-régression sur 2 292 commandes : journaux QSound **identiques** à `roms_voix`, 0 lecture dans les banques
     ajoutées.
2. **Place récupérable dans les 16 Mo** (§11.2, `outils/inventaire.py`) : **presque rien**, avec les critères stricts de
   `numeros.py` appliqués aux échantillons.
   - Les 2 310 commandes non vides du Z80 sont **toutes atteignables** : aucun échantillon ni morceau à libérer par ce
     biais.
   - Seules 48 entrées d'échantillons ne sont jamais résolues par aucune commande, pour 0,47 Mo. Elles rendent libres
     **4 banques entières** (`D6`, `E0`, `E5`, `E9`, 256 Ko).
   - Total utilisable sans changer aucune lecture : 256 Ko + 17 Ko restants. Il faudrait **≈ 2,8 Mo** pour tout loger
     (voix restantes, annonceurs, bruitages simples et en séquence).
   - **Il ne reste aucun numéro de commande libre** au sens strict : les 762 numéros vides sont tous envoyables.
3. **Capacité au-delà de 16 Mo** (§12) : la voie retenue est le **rejeu QSound**, prototypée et validée dans une copie
   du fork (`mame-fork-son/cps2f`).
   - Principe : chaque son de SFA1 ou SFA2 est rejoué sur un **2ᵉ QSound** (HLE de MAME), dont la ROM de 8 Mo est lue
     dans le `X_DATA.BIN` de l'utilisateur (e222, e251).
   - Le son est décrit par les écritures de registres que son pilote Z80 d'origine fait, relevées au fork. Aucun
     échantillon n'est copié.
   - **1 323 sons** : toutes les commandes non musicales de SFA1 et SFA2, séquences comprises.
   - Priorité et coupure de voie selon la règle des pilotes Capcom.
   - Contre le pilote d'origine : niveau identique (écart médian 0,00 dB), corrélation des enveloppes 0,99.
   - Non-régression : avec le rejeu actif, 259 commandes donnent des journaux et un WAV **identiques à l'octet près** au
     fork flux.
4. **Spécification de la redirection par le programme traduit** (§13) : écrite, générée, vérifiée et **essayée dans une
   construction ro9 complète** (dans ce dossier).
   - **8 mots MIPS** changés (routines des cris `$08C2AE` et `$08C274`) et **62 pointeurs** de `0x6AE614`.
   - Un bloc de données de 19 712 octets, servi en exécution `$E70000`. Le traducteur demande **un ajout de ~20 lignes**
     pour le servir.
   - En jeu (Ryu/Ken ZERO, ZERO 2, ALPHA), la ROM construite donne **exactement les mêmes sons** que le prototype Lua,
     aux mêmes instants. Elle ajoute les cris par version (`$4xxx`), sans aucune exception.
   - **Piège trouvé** : on ne peut pas ajouter les données à la suite du module. Le mot 6 de l'en-tête fixe aussi
     l'emplacement des variables du portage (§13.3).
5. **Défaut du prototype QSound pour la voie « programme »** : le 68K ajoute `$500` au code du joueur 2.
   - Sur les 202 commandes de `roms_hyper`, le côté 2 tomberait sur un autre son existant pour 80 d'entre elles, sur une
     autre de mes voix pour 71, et sur une commande vide pour 51.
   - `roms_hyper` ne marche donc qu'avec l'interception (Lua ou fork), qui rend la même commande des deux côtés.
   - Le rejeu n'a pas ce problème : `$2500 + c` et `$3500 + c` sont définis.

## 1. Sources et données

| jeu | Z80 | QSound | provenance | fichiers ici |
|---|---|---|---|---|
| SFA1 (Zero) | `e221` (0x48000) | `e222` (4 Mo) | X_DATA | `src/sfa1_z80.bin`, `src/sfa1_qs.bin` |
| SFA2 (Zero 2) | `e250` = `sz2.01a/02a` | `e251` = swap(`sz2.11m+12m`) | X_DATA, recoupé avec `sfa2u.zip` | `src/sfa2_*`, `src/arc_sfa2u_*` |
| Zero 2 Alpha | `sza.01/02` = `sz2.01a/02a` | `sza.11m/12m` = `sz2.11m/12m` | `sfz2al.zip` (mêmes CRC) | `src/arc_sfz2al_*` |
| Alpha 2 Gold (`ro6`) | `e532` | `e533` (4 Mo, sans musique) | X_DATA | `src/ro6_*` |

- Le balayage `ro6` donne, commande par commande, les mêmes voix que SFA2. Seuls 4 bruitages de la page 01
  diffèrent.
- Format pour le fork (`HSFA_SON`) : `roms/sfa1`, `roms/sfa2` et `roms/ro6` contiennent des `hx3.*`. Ils servent
  aux balayages.

## 2. Pilotes Z80 SFA1 / SFA2 (v1.05)

Code : `src/*_z80.asm` (unidasm) et `outils/z80v105.py`.

| élément | SFA1 / SFA2 (v1.05) | SFA3 / Upper (v1.71) |
|---|---|---|
| en-tête | `$9000`, banque 0 (région 0x11000) | `$3800/$3C00` |
| nombre de commandes N (`c mod N`) | SFA1 `$300`, SFA2 `$400` | `$C00` |
| table des commandes | `$9006 + 4c` : `[b, H, L, x]` → linéaire 24 bits | `$8C06 + 4c` |
| adressage | linéaire L → région L (L < 0x8000), sinon L + 0x8000 ; banque = (L>>14) − 2 (`$0A9C`) | idem |
| morceau | octet 0 = priorité (0 → musique `$04B6`, ≥ `$80` → spéciale `$0563`), puis 16 décalages BE (voies 0-15) | idem |
| piste de voix | `05 HH LL` (tempo **16 bits**), `06 FF`, `07 VV`, `08 II` ou `1F NN`, `09 03`, note, `17` | `05 TT` (8 bits) … |
| côté 2 | **+$100** (pages 01 → 02) ; SFA2 page 03 : **+$80** | +$500 (`$3938`) |
| fréquence des voix | SFA1 20 188 / 24 038 Hz ; **SFA2 12 019 Hz** | 12 019 Hz |

**Où sont les voix.** Une voix est une commande « simple » (une note, un échantillon, une voie). Le K.O. termine
chaque bloc par une séquence (voix + écho ou bruitage).

| | SFA1 | SFA2 (= Alpha, = `ro6`) |
|---|---|---|
| voix des persos, côté 1 | `0160-01F3` (voie 12) | `0180-01FC` (9 persos) et `0300-037E` (8 persos) (voie 12) |
| côté 2 | `0260-02F3` (voie 14) | `0280-02FC`, `0380-03FE` (voie 14) |
| cri par perso (ordre des ids) | `01E7 + id` | `0060-006F` |
| annonceur | `00E0-00F2` (19 échantillons d'environ 1 s, voie 11) : **attribution probable, à écouter** | `00A1-00BE` |
| autres | — | `00C0-00D3` : voix ajoutées (Zangief, Gen, Dan, Dhalsim) |
| bruitages | `0100-0141` (voie 13) / `0200-0241`, plus la page 00 | page 01 `0100-017F` / page 02 |

**Blocs par perso** (`outils/sources.py`). L'appariement DTW est sans ambiguïté (`outils/assigne.py`) :
- SFA2 : Ryu 0180, Ken 018B, Akuma 0199, Charlie 01A4, Chun-Li 01B0, Adon 01C0, Sodom 01CF, Guy 01DC, Birdie 01EA,
  Rose 0300, Bison 0310, Sagat 031D, Dan 032C, Sakura 0340, Rolento 0354, Dhalsim 0364, Zangief 0373.
  - C'est l'ordre des ids SFA3 `$00-$10`.
  - Gen n'a pas de bloc : ses voix SFA2 (`00C4-00CB`) sont **identiques** à celles de SFA3.
- SFA1 : Ryu 0160-0168, Ken 0169-0173, Guy 0174-017F, Charlie 0180-0188, Sagat 0189-0193, Chun-Li 0194-01A1,
  Rose 01A2-01AC, Adon 01AD-01B7, Sodom 01B8-01C0, Bison 01C3-01CB, Akuma 01CC-01D2, Birdie 01D3-01DE, Dan 01E5-01E6.
  - Dan est incertain. `01DF-01E4` sont les échantillons de l'annonceur probable.

**Bruitages** (`bruitages_sfa1.tsv`, `bruitages_sfa2.tsv`) : pour chaque commande non vocale, j'indique le genre, les
voies, les échantillons et s'il y a une vraie boucle.
- « simple » : un échantillon, une hauteur, une voie. **Transplantable** tel quel, avec la même méthode que les
  voix : SFA1 109, SFA2 202.
- « séquence » : plusieurs notes, voies ou échantillons, échos (fireballs, impacts doublés, jingles). **À convertir
  plus tard** : SFA1 27, SFA2 83.
  - Il faut traduire le format de piste v1.05 vers v1.71 (`05 HH LL` → `05 TT`, et les opcodes à vérifier un par
    un), ou rejouer les notes une à une.
  - La liste se trouve dans les TSV. Ces séquences ne sont pas traitées ici.

## 3. Voix extraites (WAV)

- `voix/<jeu>/<id>_<perso>/<commande>.wav` : échantillon brut à sa fréquence d'origine, 8 bits → 16 bits.
- `voix/<jeu>/<id>_<perso>.wav` : toutes les voix du perso enchaînées.
- `voix/<jeu>/annonceur*.wav`.
- 444 fichiers en tout.
- Catalogue complet (toutes les commandes, notes et échantillons) : `catalogue/<jeu>.json` et `wav/<jeu>/ech_*.wav`.
  - SFA1 : 205 échantillons ; SFA2 : 374 ; ro6 : 388 ; SFA3 + MAX : 850.

## 4. Côté Hyper : quels codes, pour quelle version

### 4.1 Mécanisme (vérifié dans `ro9` et `mame_ro9/carte_image.txt`)

- **Voix « par pas »** (coups spéciaux, super, souffles)
  - Routine 68K `$08BCCE` / `$08BCFA` : c'est l'arcade `$38E4/$390E`, sans le test `$BC(A5)`.
  - Elle calcule `code = mot 0 de [$E6(A6) + 8·index]`.
  - `$E6` est posé en `$06DF98` à partir de la **table de pointeurs `0x6AE614` (exéc.) indexée par `$102`** (128
    entrées).
  - Les entrées sont de 8 octets `[code, code_alt, 0, 0]`, en mots LE dans le module.
  - Tables extraites : `catalogue/tables_hyper.json`.
  - **ZERO, ZERO 2 et ALPHA pointent sur la table ZERO 3 de leur perso de base**, sauf `$78` (EX Bison ALPHA) et
    `$7E` (Cammy ALPHA), qui ont leur propre table.
- **Cris et K.O.** (`n = 0..6`)
  - Routine 68K `$08C274` / `$08C2AE` : base = `T_5c9a90[$117(A6)]`, ou 38 si `$102 = $7E`. Ensuite `+ n`.
  - Table `0x3D9A90` (40 mots). Évil Ryu prend la base de Ryu `0300`, Shin Akuma celle d'Akuma, Cammy ALPHA `0540`.
- **Côté 2** : `+$500` (bit 0 de `$59`), joueur J2.
- **Version d'un joueur** : `read_u8((J + $102) ~ 1)`, avec J1 = `$FF8400` et J2 = `$FF8800`.

### 4.2 Codes par version

- Une version envoie les codes du bloc `0x300 + base·0x20 + n` (côté 1) de son perso de base.
- Le détail par version est dans `catalogue/tables_hyper.json` (codes « par pas ») ; les cris vont de `n = 0` à `6`.
- Vu en jeu (`essais/*.son`) :

  | version | code | rôle |
  |---|---|---|
  | Ryu ZERO | `0309` | Hadoken |
  | Ryu ZERO | `0300` / `0800` | K.O. |
  | Ken ZERO | `0329` | Hadoken |
  | Ken ZERO | `0335` | |
  | Ken ZERO 2 | `0820` | K.O. |

  Les cris `0301/0302/0303/0323` sont relevés par l'agent `agent_hyper_son`.

### 4.3 Défauts relevés

**Cammy ALPHA dit les répliques de Maki avec `roms_voix`** (v1 ; **corrigé par la v2** de VOIX-MAX §9 : ces numéros
sont redevenus vides, Cammy ALPHA est muette au QSound).
- `$7E` envoie `0546 0548-054D 054F-0551 0553-0556 055D 055E` (sa table propre), plus les cris `0540-0546`.
- Sur PS2, ces codes jouent la banque `e344`, propre à Hyper (Cammy de Gold).
- Dans `roms_voix`, `0549-055F` = voix de Maki. VOIX-MAX croyait ces cases « de remplissage, jamais envoyées ».
- Codes de Cammy ALPHA qui tombent sur Maki : `0549-054D`, `054F-0551`, `0553-0556`, `055D`, `055E`.
- Pour corriger : déplacer Maki (session MAX), ou rediriger Cammy ALPHA vers ses vraies voix. Celles-ci sont à
  extraire de la banque SCEI `e344` (ADPCM VAG), ce qui n'est pas fait.

**`flux_journal.lua`** (agent_flux) journalise la version avec `(J+$103)~1`, qui donne toujours 0. Il faut
`(J+$102)~1`.

**Cris de dégâts et K.O. faux (relevé par l'utilisateur le 2026-10-16, Ryu ALPHA 1 en J2 en TRAINING, corrigé)**
- Cause : les cris « par version » (`$4000 + 8v + n`, §13) avaient été choisis par **ressemblance** avec le cri SFA3
  (§5, DTW), pas d'après ce que joue l'arcade. Ryu SFA1 disait `0165` / `0166` en prenant un coup ; l'arcade joue
  `0167`. Une partie des K.O. et des cris de ZERO 2 / ALPHA restaient aussi en SFA3.
- Mesure (`tools/son-hyper/mesure_cris_arcade.py`, cœur de diagnostic qui journalise les commandes son du 68K) :
  SFA1, SFA2 et SFA3 arcade, le perso de J1 se fait frapper. SFA3 : coups reçus = `n` 1 et 2 (alternés), parfois 3 ;
  K.O. = 0. SFA1 : **un seul cri de dégâts** par perso, quel que soit le coup. SFA2 : un cri fréquent et un rare.
  Résultats : `tools/son-hyper/cris_arcade.tsv` (10 persos SFA1 mesurés, Akuma / Bison / Dan déduits ; 18 SFA2).
- Correctif : `tools/son-hyper/corrige_cris.py` réécrit, dans la table du rejeu, `n` = 0 et 4 (K.O.), 1 et 2 (cri de
  dégâts), 3 (SFA1 : le même ; SFA2 : le rare), côtés 1 et 2 ; `n` = 5 et 6 inchangés. 404 lignes. Seules les
  versions déjà redirigées sont touchées : **pas de retraduction**. Appliqué par défaut par `paquet_fbneo.py`
  (`HSFA_CRIS_ARCADE=0` pour s'en passer) ; `corrige_cris.py <zip> <sortie.zip>` corrige un zip déjà construit.
- Vérifié en jeu (J2 frappé) : Ryu ZERO `0267` (= `0167` côté 2) / K.O. `0268` ; Chun-Li ZERO `029D` / `02A1` ; Ryu
  ZERO 2 `0287` + `0288` / `028A` ; Ken ZERO 2 `0295` + `0296` / `0298` ; Zangief ZERO 2 `00C0` + `00C1` / `00C3` ;
  Ryu ALPHA comme Ryu ZERO 2. Zangief : l'arcade joue la page `00` (`00C0-00C3`), pas le bloc `0373` du §2.
- Reste à faire : mesurer Akuma, Bison et Dan de SFA1 (persos cachés) ; rôle des `n` = 5 et 6.
- **Voix « par pas » (tables `$E6`) vérifiées sur l'arcade, 2026-10-16** (demande de l'utilisateur) :
  - Méthode : `compare_voix_arcade.py` (35 gestes : projections, coups normaux, quarts de cercle, Shoryuken, charges,
    360°, demi-cercles, coups répétés, Start), joués par J1 dans l'arcade et dans Hyper **depuis le même état sauvé**
    (frontal `joue_linux`, `HSFA_GESTES`), J2 en garde accroupie ; puis `marque_voix.py` : un code marqueur par entrée
    de la table de la version (copie du zip), ce qui rattache chaque voix à son code SFA3 d'origine ;
    `fusionne_voix_arcade.py` → `tools/son-hyper/voix_arcade.tsv`. 46 versions : ALPHA 1 (10 persos de SFA1),
    ALPHA 2 et ALPHA 2 Gold (18 persos de SFA2). Données : `tools/son-hyper/mesures_voix/`.
  - Résultat (131 codes) : **112 justes** (dont les voix SFA3 « identiques », même échantillon que l'arcade : Ken
    ALPHA 2, Sagat, Akuma, Zangief, Gen…), **6 fausses** (projections de Ken, Rose, Sagat ALPHA 1 ; Charlie, Chun-Li,
    Akuma ALPHA 2 : la projection de Chun-Li ALPHA 2 disait son cri de dégâts), **12 voix SFA3 gardées** alors que
    l'arcade a la sienne (Birdie 360°, Charlie Sonic Boom ALPHA 1, Guy projection ALPHA 1, Rose Soul Reflect, Sodom…),
    1 conflit (Adon ALPHA 1 : un seul code SFA3 pour deux projections que SFA1 distingue ; voix actuelle gardée).
  - Correctif : `tools/son-hyper/corrige_voix.py` réécrit les tables dans `hsfa_ext.bin` (bloc de la redirection,
    localisé par son contenu) : 36 mots, **sans retraduction** ; `paquet_fbneo.py` l'applique (`HSFA_VOIX_ARCADE=0`
    pour s'en passer) ; `gen_redirection.py` lit aussi `voix_arcade.tsv`, pour qu'une retraduction donne les mêmes
    tables. Après correction : plus aucun écart hors voix SFA3 identiques et 4 cas sans remède par table (Adon, voix
    de provocation de Guy sans équivalent en arcade, 2ᵉ voix du 360° de Sodom ALPHA 2 non déclenchée, 2 voix en plus
    de Rose ALPHA 2 Gold).
  - Gen et Zangief ALPHA 2 / Gold pointent sur la table du module (partagée avec ZERO 3) : leurs voix SFA3 y sont
    identiques à celles de SFA2, rien à corriger.
  - **Suite du 2026-10-16** :
    - **Rôle des cris** (SFA3 arcade, Ryu frappé, puis gardant tout) : `n` = 0 / 4 K.O. ; 1 / 2 coup reçu ;
      **3 = projeté** ; **5 = garde brisée** (après le son `073B`, barre GUARD vide, « DANGER ») ; 6 jamais vu. Le son
      « `$08C274` » (`T_V2_V`) est ce cri `n` = 5. SFA1 et SFA2 n'ont pas de garde brisée : rien à copier ; les 15
      versions redirigées gardent un cri de dégâts.
    - **Super-coups** (`--super`, 11 supers, 46 versions + Akuma / Bison / Dan) : 4 corrections (2ᵉ voix du super de
      Ken et du super chargé de Chun-Li ALPHA 1, super pied de Sagat ALPHA 1 et d'Adon ALPHA 2).
    - **Akuma, Bison, Dan d'ALPHA 1** : mesurés en forçant le perso (`$FF84A2`) ; cris d'Akuma `01D1` / `01D2`, Bison
      `01CA` / `01CB` (comme déduit), **Dan `0167` / `0168` : les cris de Ryu** (SFA1 lui prête ceux de Ryu, et la voix
      `0174` de Guy pour sa projection) ; 7 voix « par pas » corrigées.
    - Bilan : `voix_arcade.tsv` 158 codes : 128 justes, 8 faux, 21 SFA3 gardés à tort, 1 conflit (Adon) ; zip :
      65 mots de tables + 408 lignes de cris. Tournée de 151 VERSUS inchangée.
    - **Référence SFZ2 Alpha** (`sfz2al.zip` fourni par l'utilisateur, piste du projet SFZ2A-DASH-CPS2,
      `docs/reference/sfz2a-dash-cps2.md`) : ROM son (`sza.11m`, `sza.12m`) et Z80 (`sza.01`, `sza.02`) **identiques à
      l'octet à SFA2** : le rejeu (sons de SFA2) vaut aussi pour les versions ALPHA. 18 persos ALPHA comparés à SFZ2
      Alpha (gestes et supers, `tools/son-hyper/mesures_voix/sfz2a/`) : mêmes voix qu'en SFA2, sauf Rose (projection
      HK et coup chargé HK : `0305`), que Hyper joue déjà — les « 2 voix en plus » de Rose ALPHA étaient donc justes.
    - **Versions EX d'ALPHA** (Start tenu à la version : `$72`, `$74`, `$75`, `$76`, `$78`, `$79`, `$7A`, `$7B`) comparées
      aux variantes de SFZ2 Alpha (Start tapé sur le perso, `compare_voix_arcade.py --start N`) : toutes leurs voix
      SFA3 sont le même échantillon que l'arcade, sauf la projection HK de `$74` (Akuma) : `034C` au lieu de `019C`
      (même défaut qu'Akuma ALPHA 2). `$74` a la table du module (partagée avec ZERO 3) : correction à la
      retraduction (`gen_redirection.py` l'applique via `voix_arcade.tsv`).
  - `roms_hyper` (ROM QSound prototype, §6) : n'est pas dans les zips livrés (Hyper prend la ROM hybride d'Upper).
    prend la ROM hybride d'Upper) : sans effet.

## 5. Correspondance code SFA3 → voix d'origine (`outils/correspondance.py`, `correspondance.tsv`)

**Empreintes** : 12 kHz, silences rognés, MFCC 12 coefficients avec CMN ; DTW cosinus en C (`outils/libdtw.so`).

**Décision par échantillon SFA3** (les codes qui jouent le même échantillon ont la même décision) :
- **identique** si d < 0,03 : SFA3 joue déjà l'échantillon d'origine, rien à faire ;
- **K.O.** (`n = 0` et `4`) : cri de fin de bloc de la source ;
- **voix** (≥ 0,45 s) : d ≤ 0,20, ou d ≤ 0,27 avec appariement mutuel, et rapport des durées entre 0,5 et 2 ;
- **cri** (< 0,45 s) : meilleur cri court de la source si d ≤ 0,40 ;
- sinon **aucun** : la voix SFA3 est gardée.

Repères : les mots identiques entre enregistrements différents tombent à 0,10-0,15 (Hadoken, Shoryuken et
Tatsumaki de Ryu SFA1 → SFA3 : 0,10-0,13). Des mots différents sont au-dessus de 0,25.

**Limites**
- La DTW entre voix d'acteurs différents reste approximative. Ken SFA1, par exemple, a un autre comédien que SFA3 :
  beaucoup de ses codes restent en « aucun ».
- **À valider à l'oreille** avec `ecoute/correspondance_<jeu>_<perso>_SFA3_puis_origine.wav` : pour chaque voix
  remplacée, on entend la voix SFA3 puis la voix d'origine choisie.
- `correspondance.tsv` se corrige à la main : changer la colonne `decision`, puis relancer `gen_son_hyper.py`.

## 6. Place et prototype (`gen_son_hyper.py`, environ 1 s, déterministe)

**Ressources libres dans `roms_voix`**

| ressource | libre | consommation |
|---|---|---|
| QSound, banques entières jamais référencées (règle VOIX-MAX) | 20 banques = 1,31 Mo | voix en 8 bits, sans gain |
| zone fixe Z80 (entrées d'échantillons `$4975+8n`, programmes) | `$77D5-$7974` + `$797D-$7FFF` = 2 083 o | 8 o par entrée + 4 o par programme → **172 voix au plus** |
| tables de programmes | `NEWPT[22]` (Ingrid) à compléter (index 29-127) + `NEWPT[23]` (seul pointeur libre ; `op 08` limité à 128) | |
| commandes | 256 numéros vides partout (Z80, table PS2 « - », journaux) | 1 par voix et par morceau |
| morceaux (copie du morceau SFA3 remplacé) | banque 6 `0x29B55-0x2BBFF`, banque 15 `0x4DE9A-0x4FFFF` | environ 47 o |

**Besoin** : 218 échantillons (SFA1 98, SFA2 120).
- Aux fréquences d'origine : 1,77 Mo. Avec SFA1 ramené à 12 019 Hz : environ 1,4-1,6 Mo.
- **Ça ne tient pas en entier.**

**Choix du prototype**
- **SFA1 rééchantillonné à 12 019 Hz** : la fréquence des voix SFA2 et SFA3. `HSFA_HZ_SFA1` permet de changer.
- Les échantillons SFA2 sont **recopiés à l'octet près**.
- Silences de début et de fin retirés.
- Le niveau est rattrapé par l'octet de volume (`07 VV`) : on prend le rapport des RMS avec la voix SFA3 remplacée,
  et on règle le tempo de la note sur la durée de la voix.
- **Priorités** : Ryu et Ken d'abord, puis les K.O., puis les voix longues, puis les cris.

| ROM | voix ajoutées | QSound | commandes | redirections | non placées |
|---|---|---|---|---|---|
| **`roms_hyper/`** (règle stricte) | **144** | 1,23 Mo | 202 | 496 lignes, 66 versions | 74 : surtout des cris SFA2, plus 9 voix de Rolento et Sakura |
| ~~`roms_hyper_trous/`~~ (`HSFA_TROUS=1`, **abandonnée et supprimée** le 2026-10-10) | 171 | 1,40 Mo | 243 | 564 lignes | 47 (limite de la zone fixe) |

**Placement** : tous les K.O. et presque toutes les voix longues sont placés ; ce sont des cris qui manquent.

**Variante `roms_hyper_trous/`**
- Elle écrit aussi dans les trous non référencés des banques déjà utilisées : 4,2 Mo, surtout des copies mortes de
  `e288`.
- Effet décrit dans VOIX-MAX (découverte 2) : la lecture transitoire (ancienne banque, nouveau début) lit nos données
  au lieu d'autres données mortes. Rien d'audible, mais la ROM n'est plus identique à l'octet près.
- Non-régression non relancée sur cette variante.

**Pour tout loger**
- Libérer de la zone fixe Z80 ou des banques : les voix MAX occupent 2,48 Mo à 22,7 kHz.
- Ou accepter les trous.
- Le QSound est plafonné à 16 Mo : la banque tient sur un octet dans l'entrée d'échantillon.

**`roms_hyper/md5.txt`** (reconstruite sur `roms_voix` v2, §11.1)
- `hx3.01` `46c9c6f8…` (v1 : `5ca6953a…`), `hx3.02` `a7e1c494…`, `hx3.14m` `45251e32…` ;
- `hx3.11m/12m/13m` = `roms_voix`.

**Autres fichiers de `roms_hyper/`**
- `attribution.json` : par voix, l'échantillon, l'adresse, la hauteur et les commandes ; plus la correspondance.
- `redirection.txt` : `version code_SFA3 nouvelle`, côté 1. Le côté 2 (`code + $500`) donne la **même** nouvelle
  commande : je n'ai pas créé de double `+$500`, car le Z80 joue le même morceau des deux côtés.
- `redirection_hyper.tsv` : la même table, lisible.
- `tables_par_version.json` : les tables `$E6` par version et les cris, pour la voie du §7.

## 7. Redirection : prototype et voie recommandée

> **Mise à jour du 2026-10-10** : la voie « programme traduit » est maintenant spécifiée, générée et essayée (§13),
> avec le rejeu du §12 au lieu des commandes QSound de `roms_hyper`. Celles-ci ne conviennent pas au côté 2 (§0
> point 5). Le texte ci-dessous est celui de la 1ʳᵉ passe.

**Prototype** : `lua/redirection.lua` + `lance_hyper.sh`.
- Au moment où le 68K écrit `$61801F = 0`, si le code est une voix de perso (`$0300-$06FF` ou `$0800-$0BFF`), le
  script lit la version du joueur de ce côté et remplace `$618001/3` d'après `REDIR`.
- C'est exactement ce que ferait une interception dans le fork, au même endroit que le lecteur de flux
  (`hsfa_qsound_w`, crochet FBNeo `CPSQSoundC0WriteByte`).

**Voie recommandée : dans les données et le programme traduit.**
1. **Voix « par pas »** : une table `$E6` par version (famille × perso), où les codes remplacés deviennent les
   nouvelles commandes.
   - Il suffit de faire pointer les entrées de `0x6AE614[$102]` vers ces tables.
   - Capcom fait déjà la même chose pour `$78` et `$7E`.
   - Aucune instruction à changer. Les tables sont prêtes dans `tables_par_version.json` (57 versions).
2. **Cris et K.O.** : en `$08C274/$08C2AE`, indexer la table des bases par `$102` au lieu de `$117`. Le jeu le fait
   déjà pour `$7E`.
   - Il faut alors un bloc de 7 commandes **consécutives** par famille et par perso.
   - Il y a 26 blocs à loger dans les 256 numéros libres : faisable en réservant les plages `0780-07A3`, `07C1-07FC`,
     `0082-009F`, `00E6-00FD`…
   - Autre choix : garder seulement les cris en interception.

**Pourquoi cette voie**
- Tout reste dans le jeu de ROM ; le comportement est identique au fork MAME, dans FBNeo et ailleurs.
- On ne lit pas la RAM depuis l'émulateur, ce qui est fragile si la disposition change.
- C'est le mécanisme natif.

**Inconvénient** : il faut une reconstruction `ro9` par le traducteur (autre session), avec la place pour 57 tables
d'environ 40 × 8 o en données étendues.

**L'interception au fork reste la voie rapide** : elle est déjà validée par le Lua, ne demande aucune
reconstruction, et la table est un fichier texte comme `hsfa_flux_table.txt`. Elle doit en revanche être codée deux
fois (MAME et FBNeo).

## 8. Validation

**1. Injection des 202 nouvelles commandes** (`journaux/nouvelles.*`, `outils/valide_nouvelles.py`,
`validation_nouvelles.tsv`)
- Registres : **202/202** conformes (banque, début, fin).
- Corrélation avec l'échantillon d'origine (canal gauche, recalé) : médiane **0,984**, minimum 0,709.
  - Les valeurs basses viennent des cris SFA1 ramenés de 20 à 12 kHz et des K.O. avec écho.
- Niveau actif : médiane −27,6 dBFS (−34,8 à −22,4). Les voix SFA3 et MAX sont vers −30 : environ 2 dB de plus,
  à écouter.

**2. Non-régression** (`outils/nonreg.sh`) : `codes.txt` de l'hybride + 989 codes SFA3 `0200-06FF`, soit 1 248
commandes.
- Journaux de registres QSound `roms_voix` / `roms_hyper` **identiques**.
- Tap de lecture : **0 lecture** dans les 20 banques ajoutées.

**3. En jeu** (`lance_hyper.sh`, `tournee_hyper.lua`, VERSUS, `CONTOURNE_E=1`, 3-4 matchs, WAV)
- Chaque essai est doublé d'un témoin `REDIR=` vide (même partie, déterministe).
- `outils/valide_combat.py` mesure à chaque commande la corrélation avec l'échantillon attendu et avec l'échantillon
  SFA3.

| essai | événement | attendu / SFA3 (avec) | attendu / SFA3 (témoin) |
|---|---|---|---|
| `ryuZ_kenZ2` (J1 Ryu ZERO `$30`, J2 Ken ZERO 2 `$41`) | Hadoken `0309` → `0786` (SFA1 `0160`), ×12 | 0,28-0,31 / 0,05-0,08 | 0,04 / 0,24-0,28 |
| | K.O. de Ken ZERO 2 `0820` | non redirigé : l'échantillon SFA3 est celui de SFA2 | |
| `kenZ2_ryuZ` (J2 Ryu ZERO) | K.O. `0800` → `0780` (SFA1 `0168`) | 0,24-0,27 / 0,04 | 0,09 / 0,30 |
| (J1 Ken ZERO `$31`, J2 Ryu ZERO 2 `$40`) | Hadoken de Ken ZERO `0329` → `078A` (SFA1 `0169`) | 0,40-0,53 / 0,05 | 0,06-0,13 / 0,34-0,38 |
| | `0335` → `078F` (SFA1 `016F`) | 0,92 / 0,06 | 0,09 / 0,85-0,90 |
| | K.O. de Ryu ZERO 2 `0800` → `0784` (SFA2 `018A`) | 0,23-0,26 / 0,04 | 0,10 / 0,30 |

- 27 événements redirigés mesurables sur 27 (12 + 15) classés « voix d'origine », aucun échec. Le 28ᵉ tombe à la fin
  du WAV et n'est pas mesurable.
- Les corrélations brutes (environ 0,3) sont faibles à cause des bruitages mêlés (boule de feu, coups). Le contraste
  avec le témoin est net.

**WAV d'écoute**
- `ecoute/combat_ryuZ_kenZ2_SFA3_puis_origine.wav` et `ecoute/combat_kenZ2_ryuZ_SFA3_puis_origine.wav` : pour chaque
  voix redirigée, l'extrait du témoin (SFA3), puis le même moment avec la ROM d'Hyper.
- `essais/*_voix.wav` : les moments redirigés seuls.
- `ecoute/<jeu>_<perso>_origine_puis_fork.wav` : source, puis fork, pour chaque nouvelle commande.
- `ecoute/correspondance_*.wav` (§5).

## 9. Ce qui reste

1. **Intégration par la session principale** (§13.5) :
   - appliquer le correctif du module (`redirection_68k/correctif_module.tsv`) ;
   - ajouter au traducteur le service du bloc `$E70000` (`patchs/traducteur-bloc-son.diff`) ;
   - reconstruire `ro9` ;
   - intégrer le rejeu au fork (`patchs/rejeu-sur-fork-flux.patch`) ;
   - lancer la non-régression habituelle.
2. **FBNeo** : porter le rejeu (§12.5). Il faut un 2ᵉ QSound, un crochet dans `CPSQSoundC0WriteByte` et l'état
   sauvegardé. Hyper n'existe pas encore dans FBNeo.
3. **Écoute de l'utilisateur**
   - `ecoute/combat_rejeu_SFA3_puis_origine.wav` (§12.4), la correspondance (§5), l'annonceur SFA1 probable.
   - Les 19 sons « tronqués » du rejeu (sons en boucle) et les 19 sons signalés par `compare_rejeu.py` (§12.4).
4. **Bruitages par version** : le rejeu les sait jouer (codes `$2000 + c`, `$3000 + c`), mais rien ne les envoie.
   - Il faut une correspondance bruitage SFA3 → SFA1/SFA2 (comme §5 pour les voix).
   - Il faut aussi trouver, côté 68K, où chaque bruitage est choisi : la plupart ne passent ni par `$E6` ni par les
     cris.
5. **Annonceur** : même chose, aucun lien avec la version côté 68K.
6. **Cammy ALPHA** (`$7E`) et Cammy ZERO 2 (`$5E`) : voix dans la banque PS2 `e344` (SCEI, ADPCM VAG), pas dans SFA1 ni
   SFA2. Elles pourraient passer par le même rejeu avec une 3ᵉ source, ce qui demande un décodeur VAG.
7. **Sort de `roms_hyper`** : il fait double emploi avec le rejeu et ne convient pas à la voie « programme » (§0 point
   5). Je propose de le garder comme repli sans ISO (interception Lua ou fork), ou de l'abandonner.

## 10. Fichiers

| fichier | rôle |
|---|---|
| `gen_son_hyper.py` | ROM QSound `roms_hyper/` (+ `redirection.txt`) avec vérification statique |
| `outils/inventaire.py` → `catalogue/inventaire.json` | §11.2 : place récupérable (critères stricts) |
| `outils/init_qs.lua` → `journaux/init_sfa{1,2}.txt` | écritures QSound des pilotes SFA1/SFA2 à la mise sous tension |
| `gen_rejeu.py` → `rejeu/hsfa_rejeu_table.txt`, `rejeu/bilan.json` | table du rejeu (§12.2) |
| `rejeu/hsfa_rejeu.h` | lecteur du rejeu, en-tête seul C++98 (MAME, FBNeo) |
| `mame-fork-son/` (copie de `agent_flux/mame-fork-flux`), `patchs/rejeu-sur-fork-flux.patch` | fork avec 2ᵉ QSound et rejeu ; patch contre le fork flux |
| `outils/valide_rejeu.sh`, `outils/compare_rejeu.py` → `essais_rejeu/validation_rejeu_{sfa1,sfa2}.tsv` | référence contre rejeu, son par son |
| `outils/valide_rejeu_jeu.py` → `essais/*_validation.tsv` | rejeu en jeu contre référence et témoin |
| `gen_redirection.py` → `redirection_68k/` | données et correctif de la redirection par le programme (§13) |
| `outils/verifie_redirection.py` | vérification statique de la redirection (§13.4) |
| `untranspile_son/`, `patchs/traducteur-bloc-son.diff` | copie du traducteur + service du bloc `$E70000` |
| `modules_son/`, `modules_ctl/` | modules (liens) dont `ro9` corrigé / d'origine |
| `b9_ctl/`, `b9_son/`, `b9_rp/` | constructions ro9 témoin et corrigée ; rompath de la corrigée |
| `lua/redirection.lua`, `lance_hyper.sh` | Hyper au fork (variables `CPS2F`, `RP9`, `BANC9`, `REDIR`, `HSFA_REJEU_*`) |
| `outils/lance_inj.sh` (variable `CPS2F`) | banc d'injection |
| `ecoute/combat_rejeu_SFA3_puis_origine.wav` | écoute : témoin puis rejeu, pour chaque son redirigé |

Le reste est inchangé (§1-§8). **Supprimables** :
- `essais_rejeu/*.wav` (1,4 Go ; `valide_rejeu.sh` les refait en ~40 min, mais `valide_rejeu_jeu.py` lit `ref_*.wav`) ;
- `essais/` (WAV) ;
- `mame-fork-son/build` (1,9 Go en tout, mais il faut le garder pour recompiler vite) ;
- `wav/`, `nvram/`, `journaux/nouvelles.wav`.

## 11. Reprise du 2026-10-10 : ROM QSound sur `roms_voix` v2 et place récupérable

### 11.1 Reconstruction (`gen_son_hyper.py`)

La reconstruction sur la v2 était faite (13 h 54) avec sa validation ; je l'ai vérifiée.

- Régénérée deux fois dans un dossier temporaire : **md5 identiques** à `roms_hyper/md5.txt`, `redirection.txt`
  identique.
  - `hx3.01` `46c9c6f8…` ; `hx3.02` `a7e1c494…` ; `hx3.14m` `45251e32…` ;
  - `hx3.11m`, `hx3.12m`, `hx3.13m` = `roms_voix`.
- Les 202 commandes sont celles de la 1ʳᵉ version : la v2 de VOIX-MAX a été calculée en les évitant (`numeros.py`,
  critère 4). Aucune ne coïncide avec une voix MAX v2 ni à ±`$500` : le générateur ne prend que des commandes vides du
  Z80, et chaque voix MAX occupe c et c + `$500`.
- **Validation de l'injection** (`validation_nouvelles.tsv`) : 202/202 conformes registre par registre ; corrélation
  avec l'échantillon d'origine médiane 0,985, minimum 0,710.
- **Non-régression** (`outils/nonreg.sh`, `journaux/nonreg.log`) : 2 292 commandes (`codes.txt` de l'hybride + toutes
  les commandes non vides `0100-0BFF` de la v2) ; journaux de registres QSound **identiques** à `roms_voix` ; **0
  lecture** dans les banques ajoutées.

### 11.2 Inventaire de la place (`outils/inventaire.py` → `catalogue/inventaire.json`)

**Commande atteignable** : les critères de `numeros.py`, appliqués à **toutes** les commandes `0000-0BFF` et durcis.
- a. Table native PS2 : contenu réel pour un code x tel que x mod `$C00` = c.
  - Le Z80 réduit modulo `$C00`, et la table PS2 a `0x1200` entrées.
  - ADX : toujours du contenu. Banques communes : `o4` présent dans e345/e346.
  - Banque de perso : `o4` présent dans **n'importe laquelle** des banques e314-e344. C'est plus strict que
    `numeros.py`, qui ne regarde que la banque du perso du type.
- b. Tables « sons par pas » de tous les programmes (sfa3ud, ro3, ro5, ro9) et les 128 tables d'Hyper.
- c. Cris et K.O. : base + 0..6 (40 bases et tout début de bloc `$300 + $20k`).
- d. Journaux 68K en jeu des agents.
- e. ±`$500` (modulo `$C00`).
- f. **Pages 00 et 01 et leur côté 2 (05, 06) toujours atteignables** : musique, système, annonceur, bruitages communs.
  Ils sont envoyés par des immédiats que a-e ne voient pas.
- g. Voix MAX et commandes de `roms_hyper`.

**Échantillon libérable** : seulement si aucune entrée atteinte par une commande atteignable (ni une sentinelle du
pilote, `$600` et `$7F00`) ne couvre ses octets. Les plages sont calculées en ordre signé.

**Résultats**

| élément | résultat |
|---|---|
| commandes non vides | 2 310, **toutes atteignables** (la table PS2 suffit presque toujours : seules 30 ne sont justifiées que par elle) |
| échantillons ou morceaux Z80 libérables par commande inatteignable | **0** |
| entrées d'échantillons jamais résolues par aucune commande (dans les plages que l'hybride gardait par prudence) | 48 (Upper 39, SFA3 musique 9), 487 730 o |
| … dont banques entières rendues libres | **4 : `D6`, `E0`, `E5`, `E9`** (restes de e288), 262 144 o utilisables selon la règle de VOIX-MAX |
| … dont octets épars dans des banques encore lues | 417 241 o : utilisables seulement en acceptant un changement de la lecture transitoire (VOIX-MAX, découverte 2) |
| échantillons en double à des adresses différentes | 2 groupes, 16 Ko (négligeable) |
| numéros de commande vides et non envoyables | **0** sur 762 vides (avec les critères de `numeros.py` seuls, il en restait une dizaine de paires) |

**Besoin pour « tout »**, en octets d'échantillons QSound :

| poste | taille |
|---|---|
| 74 voix non placées | 0,35 Mo |
| annonceurs (SFA1 19 échantillons à 20 kHz, SFA2 26) | 0,72 Mo |
| bruitages simples (SFA1 48, SFA2 80 échantillons) | 1,13 Mo |
| bruitages en séquence | 0,58 Mo |
| **total** | **≈ 2,8 Mo** |

**Conclusion** : 0,27 Mo propres, pas un numéro de commande, et la zone fixe du Z80 est presque pleine. Tout ajout au
QSound principal demande donc une autre capacité (§12).

## 12. Au-delà de 16 Mo : comparaison, choix, prototype

### 12.1 Comparaison

| critère | (a) banques QSound étendues | (b) lecteur de sons hors Z80 : **rejeu QSound** (retenu) |
|---|---|---|
| échantillons | la ROM QSound principale passe à 32 Mo | ROM séparée de 8 Mo (2ᵉ QSound) lue dans le `X_DATA.BIN` de l'utilisateur, comme la musique dans `Y_DATA.BIN` ; rien à redistribuer |
| pilote Z80 | **à modifier** : l'entrée d'échantillon n'a qu'un octet de banque (`$80:banque`, `$1466-$148E`), il faut un bit de plus (par ex. bit 7 du paramètre) | inchangé |
| numéros de commande | **aucun de libre** (§11.2) ; il faudrait étendre le modulo `$C00` (`$050D`) et la table des commandes (`$8C06`, qui touche les données en `$BC06`) | illimités : codes `$2000+` hors table PS2 ; le fork transmet au Z80 un code vide (`0000`) |
| entrées et programmes Z80 | zone fixe pleine (~170 entrées) ; `NEWPT` n'a plus de place (24 pointeurs, `op 08` limité à 128) | sans objet |
| côté 2 (+`$500` du 68K) | il faut des **paires** libres (c, c + `$500` mod `$C00`) ; il n'y en a plus | entrées `$2500 + c` / `$3500 + c` dans la table |
| fidélité | rééchantillonnage SFA1 (20-24 → 12 kHz) pour tenir ; séquences à **convertir** de v1.05 en v1.71 | **exacte** : les écritures du pilote d'origine, séquences, échos, enveloppes et panoramiques compris, aux fréquences d'origine |
| priorité et coupure | gérées par le Z80, partagées avec SFA3 | règle du pilote (`cp (ix+prio) ; jp c` : v1.05 `$046E`, v1.71 `$05AF`) appliquée par voie du 2ᵉ QSound ; pas d'interaction avec les sons SFA3 du Z80 (voir 12.6) |
| MAME | `qsound_device` est en `device_rom_interface<24>` : passer à 25 bits (fichier partagé `src/devices/sound`) | un 2ᵉ `qsound_hle_device` (déjà compilé) et un petit périphérique ; ~170 lignes dans `cps2.cpp` |
| FBNeo | `qs_c.cpp` masque par la taille de la ROM : agrandir `nCpsQSamLen` | 2ᵉ instance du QSound (code statique global à dupliquer, ou HLE porté dans l'en-tête), crochet déjà présent (`CPSQSoundC0WriteByte`) |
| états sauvegardés | rien de plus | état du rejeu (instances, voies) + état du 2ᵉ QSound |

**Pourquoi (b)**
- (a) se heurte à trois murs dans le pilote : il n'y a ni numéros libres, ni entrées libres, ni bit de banque. Il
  demande donc une chirurgie du Z80 en plus des deux émulateurs.
- (b) ne touche ni le Z80 ni la ROM son. Il garde le son exact des jeux d'origine et réutilise le mécanisme du lecteur de
  flux : interception à `$61801F = 0`, fichiers de l'utilisateur, table texte.

Variante écartée : un lecteur d'échantillons « maison » (PCM mixé directement). Il faudrait réécrire volume, panoramique,
écho et séquences ; le 2ᵉ QSound les fait déjà.

### 12.2 Table (`gen_rejeu.py` → `rejeu/hsfa_rejeu_table.txt`, 3,2 Mo de texte)

- **Source** : les balayages du §2 (`journaux/bal_sfa{1,2}.txt`). Chaque commande y est posée 4 images après `FF00`, avec
  toutes les écritures QSound et leur temps.
- **Fenêtre d'une commande** : de la commande à 0,0670 s avant la suivante (moment où `FF00` est posé). La réponse
  à `FF00` (bloc `STOP`) vient du début du fichier ; l'initialisation du pilote (`INIT`, 82 écritures) vient de
  `outils/init_qs.lua`.
- **Contenu** : 457 sons SFA1 (`$2000 + c`) et 866 SFA2 (`$3000 + c`), plus 1 317 entrées « côté 2 » (`REF $2500 + c` →
  commande côté 2 d'origine : page 01 → 02, SFA2 `$0300-$037F` → +`$80`). Les sections `REF`/`ALIAS` des cris par
  version (§13) sont ajoutées par `gen_redirection.py`.
- **19 sons tronqués** (`T`, sons en boucle plus longs que la fenêtre) : on leur ajoute la réponse `STOP` de leurs
  voies.
- `SOURCE` donne le décalage et le CRC des entrées X_DATA ; le fork refuse une source différente.

### 12.3 Lecteur (`rejeu/hsfa_rejeu.h`) et fork (`mame-fork-son/`, `patchs/rejeu-sur-fork-flux.patch`)

**En-tête seul, C++98**, sans dépendance, pour MAME et FBNeo.
- Lecture de la table.
- Chargement des sources depuis `X_DATA.BIN`, une ISO (recherche ISO9660) ou `fichier@décalage`, avec contrôle du
  CRC.
- 32 sons simultanés au plus, 19 voies (16 PCM + 3 ADPCM).
- Priorité par voie, comme le pilote. Une voie occupée par un son de priorité plus haute n'est pas prise ; sinon le son
  en cours y est coupé (ses écritures suivantes sur cette voie sont abandonnées). La voie se libère à la dernière
  écriture du son.
- `FF00` arrête tout (réponse d'origine) et passe aussi au Z80. `ALIAS` remplace le code transmis au Z80.
- Banque du jeu ajoutée aux registres de banque : SFA2 en `$40`.
- État en types simples.

**Dans `cps2.cpp` (copie)**
- `qsound_hle_device` « `qsound_hsfa` » (région de 8 Mo remplie depuis X_DATA, routée au haut-parleur, même volume
  numérique que le QSound principal).
- Périphérique `hsfa_rejeu_device` : minuterie à la prochaine écriture, états sauvegardés.
- Appel dans `hsfa_qsound_w` après le lecteur de flux.

**Variables** : `HSFA_REJEU_TABLE` (sans elle, rien ne change), `HSFA_XDATA` (défaut `HSFA_YDATA` si c'est l'ISO),
`HSFA_REJEU_LOG`.

Compilation incrémentale ≈ 20 s (commande de FLUX.md §2).

### 12.4 Validation

| essai | résultat |
|---|---|
| **référence contre rejeu, son par son** (`outils/valide_rejeu.sh`, `compare_rejeu.py`) : chaque commande jouée par son pilote d'origine (fork d'origine, `HSFA_SON=roms/sfa1` ou `roms/sfa2`), puis `$2000+c` / `$3000+c` en rejeu, aux mêmes instants | SFA1 : 441 sons (16 muets en référence). Écart de niveau médian **0,00 dB** (5ᵉ-95ᵉ centile ±0,01). Corrélation des enveloppes médiane **0,991** ; forme d'onde médiane 0,984 à gauche et 0,992 à droite |
| | SFA2 : 857 sons (9 muets). Écart **0,00 dB** (±0,02). Enveloppes **0,990** ; forme d'onde 0,974 / 0,991 |
| | Sons à écouter (enveloppe < 0,9) : SFA1 4 (`011A`, `021A`, `0234` tronqués ; `0241`) ; SFA2 15. Niveau identique pour tous ; les écarts viennent du calage de quelques ms et de la phase des sons à deux voies ou à écho (QSound HLE contre LLE) |
| le Z80 principal pendant le rejeu | **0 écriture** QSound (il reçoit `0000`) |
| **non-régression** : 259 commandes (`codes.txt` de l'hybride), fork flux d'origine contre copie avec rejeu **actif** | journaux de registres **identiques**, WAV **identique à l'octet près** |
| **en jeu, prototype Lua** (Hyper, VERSUS : Ryu ZERO/Ken ZERO 2, Ken ZERO/Ryu ZERO 2, Ryu ZERO 2/Ken ALPHA ; 12 000 images ; `rejeu/redirection_rejeu.txt`) | 17 sons rejoués (Hadoken SFA1 `0160`, Ken SFA1 `0169`/`016F`, Ryu SFA2 `0180`, K.O. SFA2 côté 2 `028A`). Corrélation avec la référence du pilote d'origine **0,49-1,00** (médiane 0,66, bruitages mêlés) ; témoin sans redirection 0,04-0,13 |
| **en jeu, redirection par le programme** (§13, ROM `b9_son`, aucune redirection Lua) | **mêmes sons aux mêmes instants (±1 µs)** que le prototype Lua. Le K.O. côté 2 passe par `$4700` (cris par version) ; les cris non redirigés de Ken ZERO 2 / ALPHA passent par `ALIAS` vers `0820`, comme avant. WAV : corrélation 0,9996 avec le prototype Lua ; mêmes mesures (0,66 contre 0,055) ; 0 exception |

Écoute : `ecoute/combat_rejeu_SFA3_puis_origine.wav`. Pour chaque son rejoué : le témoin (SFA3), puis le rejeu.

### 12.5 Pour FBNeo (non fait)

- `hsfa_rejeu.h` est prêt (C++98, VFS libretro comme `hsfa_flux.h`).
- Il manque un 2ᵉ QSound. Deux possibilités :
  - dupliquer l'état de `qs_c.cpp`, qui est global ;
  - porter `qsoundhle.cpp` (BSD-3, ~630 lignes) dans un en-tête instanciable, solution que je recommande.
- Il manque aussi l'appel dans le crochet `CPSQSoundC0WriteByte` (déjà utilisé par le flux), les écritures datées (la
  trame est rendue d'un bloc : découper le rendu aux instants des écritures) et `HsfaScan`.

### 12.6 Limites

- **Pas d'interaction avec les sons SFA3 du Z80** : un son rejoué ne coupe pas une voix SFA3 sur la voie 11, et
  inversement. Dans SFA1/SFA2, les deux joueurs ont de toute façon des voies séparées (12 et 14).
  - Cela peut s'entendre quand un perso mêle des voix SFA3 gardées (« aucun » au §5) et des voix rejouées.
  - Remède possible : faire envoyer au Z80, au lieu de `0000`, une courte commande « silence voie 11, priorité `$0A` ».
    Il faut pour cela un numéro, à prendre parmi ceux de `roms_hyper` si on l'abandonne.
- **Fenêtre des traces** : 2,5 s en validation et 4 s dans les balayages. Les 19 sons plus longs sont coupés proprement
  (`STOP`).
- **Temps** : les écritures sont rejouées au même décalage qu'à l'origine. Le temps de réaction du Z80 (quelques ms)
  est donc inclus.
- Le `X_DATA.BIN` de l'ISO « WORK » n'a pas été essayé ; seul `work/xdata/X_DATA.BIN` l'a été. Le CRC protège contre
  une autre version.

## 13. Spécification : redirection par le programme traduit

### 13.1 Ce qui change dans le jeu

| mécanisme 68K | d'origine | après correctif |
|---|---|---|
| voix « par pas » (`$08BCCE`/`$08BCFA` mot 0 ; `$06C192`/`$06C342` mot 1 si `$BD(A5)`) | `$E6(A6)` = `0x6AE614[$102]` : ZERO, ZERO 2 et ALPHA ont la table ZERO 3 de leur perso de base | 62 pointeurs vers 30 tables propres. Ce sont des copies de la zone d'origine (80 entrées), où les codes remplacés deviennent `$2000 + c` (SFA1) ou `$3000 + c` (SFA2) ; mots 0 **et** 1 ; le 68K ajoute `$500` côté 2 |
| cris et K.O. (`$08C2AE` : n = 0/4 K.O., 1-2, 3, 6 ; appelants `$08C230`-`$08C2A4`) | `T_5c9a90[$117]` (perso de base), `$7E` → indice 38 | `T_CRIS_V[$102]` (128 mots) : `$4000 + 8v` pour les 68 versions redirigées, sinon la valeur d'origine |
| son de `$08C274` (appelé en `$06ACE4`, `$06AED6`) | `T_5c9a40[$117]`, `$7E` → 38 | `T_V2_V[$102]` : code de rejeu pour 15 versions, sinon la valeur d'origine |

**Codes `$4000 + 8v + n`** (et `$4500 + …` côté 2), dans la table du rejeu :
- `REF` vers le son d'origine (côté 2 : la commande côté 2 d'origine) ;
- ou `ALIAS` vers le code SFA3 (base + n, côté 2 + `$500`) quand la voix est gardée.

**Chiffres**
- 70 versions redirigées : 62 tables `$E6`, dont 30 contenus distincts.
- 841 couples (version, code) ; 3 028 contrôles « par pas », 840 cris.

### 13.2 Correctif du module (`redirection_68k/correctif_module.tsv`, 70 lignes)

Toutes les adresses sont des **décalages fichier** de `ro9_usa_prog68k.bin` (exéc. = fichier + `0x1F0000`), mots LE.

| décalage | ancien | nouveau | rôle |
|---|---|---|---|
| `38A788` | `80640116` | `80640102` | `$08C2AE` : `lb a0,$116` (perso de base) → `lb a0,$102` (version) |
| `38A794` | `2412007E` | `24120080` | `$08C2AE` : cas Cammy ALPHA neutralisé (`$80` n'est jamais une version) |
| `38A898` / `38A89C` | `3C03005D` / `24639A90` | `3C0300E7` / `24630000` | `$08C2AE` : table `0x5C9A90` → `0xE70000` |
| `38A57C` | `80430116` | `80430102` | `$08C274` : idem |
| `38A588` | `2412007E` | `24120080` | `$08C274` : idem |
| `38A68C` / `38A690` | `3C02005D` / `24429A40` | `3C0200E7` / `24420100` | `$08C274` : table `0x5C9A40` → `0xE70100` |
| `4BE614 + 4v` (62 versions) | pointeur d'origine | `0xE70200 + 640·k` | tables `$E6` |

- Les `T_CRIS_V` et `T_V2_V` sont **complètes** (valeurs d'origine pour les versions non redirigées). Le correctif
  n'a donc **pas de repli** : il indexe par la version au lieu du perso de base.
  - Pour les versions non redirigées, c'est équivalent si le perso de base `$117` est fonction de la version, ce que
    dit `ids_102.tsv` pour les 128 versions.
  - Je n'ai pas retrouvé dans la carte l'écriture de `$117` d'un joueur (sans doute par un mot ou un long) : à
    confirmer par la session principale.
  - Si l'on préfère un repli, la forme 68K équivalente est : `MOVE.B $0103(A6),D1 ; ADD.W D1,D1 ; MOVE.W T(D1),D1 ;
    BNE fin ; <code d'origine>`.
- `redirection_68k/ro9_usa_prog68k_son.bin` est le module corrigé, avec un en-tête **inchangé** (taille identique).

### 13.3 Données ajoutées (`redirection_68k/donnees.bin`, 19 712 octets, format du module)

| exéc. | contenu |
|---|---|
| `0xE70000` | `T_CRIS_V[128]` (mots LE) |
| `0xE70100` | `T_V2_V[128]` |
| `0xE70200` | 30 tables `$E6` de 640 octets (80 entrées de 8 octets) |

- **Piège (vérifié par construction)** : il ne faut pas ajouter ces données à la fin du fichier en allongeant le mot 6
  de l'en-tête.
  - Le traducteur place les variables du portage (`PORT_RAM`) à partir de cette borne, et la RAM 68K (`RAM_HI`) à
    l'arrondi supérieur.
  - Mon premier essai (données en `0xB67200`) déplaçait 124 lignes de la carte, par exemple `CLR.L $f002f8` →
    `$bce4f8`. Les tables recouvraient les variables du portage.
- **Choix** : une plage d'exécution **hors du module et de sa RAM**. Elle doit tenir sur **6 chiffres hexa**, car
  `assemble.py` lit `T_xxxxxx` sur 6 chiffres : avec `0x1000000`, la table était lue au mauvais endroit.
  - Je prends `0xE70000`.
  - Aucune instruction `lui` du module ne vise `0xE6-0xE8`.
  - Les 10 mots du module qui tombent dans `[0xE70000, +19 712)` sont des paires d'octets, pas des pointeurs
    (`0x5B4B10`…).
- **Service par le traducteur** (`patchs/traducteur-bloc-son.diff`, ~20 lignes, essayé) :
  - `translate._addr_to_68k` : `[SON_X, SON_X + len)` → `DATA_EXT + (DATA_END_RT − DATA_SPLIT) + (v − SON_X)`,
    c'est-à-dire **à la suite du bloc externe** `ext_940000.bin` : `$BCE200` ;
  - `mame_test.py` : le bloc, mots échangés, est ajouté à `ext_940000.bin` ;
  - une plage est ajoutée à la conversion des pointeurs (`build_conv`), pour les pointeurs `$E6` lus en mémoire puis
    convertis (`CONV_A3`) ;
  - variables `HSFA_SON_DONNEES`, `HSFA_SON_X`.

  `banc_mem.lua` sert déjà tout le fichier `ext_940000.bin` : rien à changer au banc.

### 13.4 Vérifications faites

- **Statique** (`outils/verifie_redirection.py`) : chaque entrée des 62 tables, chaque cri (n = 0, 1, 2, 3, 4, 6) et le
  son `$08C274`, des deux côtés, sont résolus dans la table du rejeu. Résultat : 3 028 + 3 028 + 840 + 140 contrôles
  conformes à la correspondance ; 58 versions non redirigées gardent la valeur d'origine ; **0 erreur**.
- **Construction** (copie du traducteur, `MODULE=ro9`, `TRAVAIL` = ce dossier) :
  - témoin `b9_ctl` : **identique** à `mame_ro9/roms_ro9` ;
  - corrigée `b9_son` : `non résolus 0`, même taille de code, `ext_940000.bin` + 19 712 octets. Dans la carte, **seules 6
    lignes changent** (`MOVE.B $0103(A6),D1`, `CMPI.B #$80`, `T_e70000` / `T_e70100`, ×2). Les tables sont lues par
    `LEA $1BCE200.L,A0 ; MOVE.W (A0,D1.W),D1`.
- **En jeu** (§12.4) : identique au prototype Lua.

### 13.5 Intégration (session principale)

1. Appliquer `correctif_module.tsv` au module, ou prendre `ro9_usa_prog68k_son.bin` (vérifier d'abord que le module de
   référence n'a pas changé : les anciens mots sont dans le TSV).
2. Appliquer `patchs/traducteur-bloc-son.diff` à `src/hsfa`. Il est inactif sans `HSFA_SON_DONNEES` : les
   constructions de ro3 et ro5 ne changent pas.
3. Construire ro9 avec `HSFA_SON_DONNEES=…/redirection_68k/donnees.bin`.
4. Fork : `patchs/rejeu-sur-fork-flux.patch` (contre `mame-fork-flux`) ; livrer `hsfa_rejeu_table.txt`.
5. Régénération : `gen_rejeu.py`, puis `gen_redirection.py`, qui ajoute la section des cris à la table, puis
   `outils/verifie_redirection.py`. Pour changer une décision de correspondance : `correspondance.tsv` / `.json` (§5),
   puis ces deux scripts.
6. Non-régression : `nonreg.sh` habituel, plus un essai ZERO, ZERO 2 et ALPHA en jeu (`lance_hyper.sh` avec `RP9`,
   `BANC9`, `HSFA_REJEU_TABLE`, `HSFA_XDATA`).
