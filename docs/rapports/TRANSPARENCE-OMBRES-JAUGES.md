# Ombres et jauges « comme la PSP » : mesures et proposition (avant tout codage)

Agent `agent_alpha`, 2026-10-18. Mesures :

- cœur d'essai hors patch (`fbneo_mesure/`, `coeurs/essai_bit12_hsfa.so`), variables `HSFA_PAL_STATS` (objets de la
  palette 0x14 par état) et `HSFA_G_STATS` (code de tuile **global** et position) ;
- 7 parties, 178 000 images (`tests/mesure_pal.sh`) : nonreg SFA3, Upper et Hyper, Hyper « large » (15 VERSUS des
  persos 02-1F en ZERO 3), Upper MAX Eagle et Maki, ro9a Arcade (23 manches) ;
- analyses : `outils/analyse_pal14.py`, `outils/analyse_g14.py`, `psp/g14_analyse.txt` ;
- contrôles visuels : palette forcée à 50 % ou en soustractif, image par image.

## 1. Côté PSP (rappel, dumps GE)

- **Ombres** : CLUT `0x040CB400` (emplacement 32), couleur de sommet `C0000000`, donc **noir à 75 %** : le résultat
  vaut dst × 0,25, quelle que soit la couleur de la palette. Une primitive par morceau d'ombre, au sol.
- **« Jauges à 50 % » : CORRECTION (2026-10-24).** Les deux rectangles à 50 % ne sont **jamais visibles**.
  - Géométrie : J1 (80,16)-(224,24) et J2 (256,16)-(400,24), sur l'écran PSP de 480 px.
  - Couleur de sommet : `80007800` (vert), `80004878` (orange, J2 touché) ou `80000000` (assombrissement des supers).
  - Les UV valent (0,0) aux quatre sommets : chaque pixel lit le texel (0,0), qui est l'**index 0** de la CLUT (`0x40CB200` / `0x40CB240`). Ce texel vaut `0x4340`, d'**alpha nul** (bit 15 = 0).
  - Avec la texture en MODULATE + alpha et le test alpha `> 0`, le GE **rejette chaque pixel**.
  - Vérification : les pixels de la zone sont identiques au pixel près entre une capture « J2 vert » et une capture « J2 orange ».
- **Ce qui est visible sur PSP, c'est le remplissage des barres de vie, en dégradé horizontal** (lignes 22-28 de l'écran PSP).
  - J1 à pleine vie : (57,239,0) vert à gauche → (107,239,0) → (165,231,0) → (214,231,0) jaune à droite.
  - J2 à pleine vie : le même dégradé, en miroir.
  - J2 touché (Deejay, chrono 98) : (247,206,0) → (247,189,0) → (247,173,0) → (247,165,0), du jaune-orange.
  - La barre arcade CPS2 est d'un jaune uni. Ce n'est pas une transparence : ce sont les couleurs de remplissage choisies par le PSP (sans doute selon la vie).
  - **Décision de l'utilisateur (2026-10-24) : abandonné**, les barres restent jaunes comme sur l'arcade.

## 2. Ombres côté CPS2 : palette, objets, scène

- Les ombres sont des **objets** (pas du scroll1), en **palette OBJ 0x14**, dans SFA3, Upper, Hyper et ro9a. Elles
  sont dessinées à chaque image, sans clignotement.
- **La palette 0x14 n'est pas réservée aux ombres**. En combat, elle sert aussi à des éléments de décor, par exemple
  les poteaux du premier plan du décor de Cammy (codes globaux `3EFCF`, `3F000-3F011`), ou `3F0CD`, `3F0F0-3F102`,
  `3E17C-3E19A`. Hors combat, elle sert à des écrans (sélection : `05875`, `2320F`, `3E3xx`). **Un mode « palette
  0x14 » rendrait ces objets transparents par erreur.**
- **Les tuiles d'ombre ont le même code GLOBAL dans les quatre jeux.** Ce sont les graphismes de SFA3 ; les codes
  locaux de la banque commune, eux, diffèrent : SFA3 `4264…`, Upper `45FF…`, Hyper `20E0…`.

| code global | où | contrôle |
|---|---|---|
| `305DF`-`30613` | SFA3, Upper, Hyper, ro9a, MAX : toutes les tailles d'ombre vues (30 persos de ZERO 3 dans Hyper « large ») | image : seules les ombres changent |
| `50888`-`5088A` | Hyper (persos ZERO et ZERO 2) | image : seules les ombres changent (Ryu / Ken, décor de la Muraille) |
| `0284A` | SFA3 : bout de bande d'ombre, contigu à `305F5` / `305F4` | positions contiguës au sol |

- **Scène** : dans les 178 000 images, ces codes n'apparaissent que dans les combats, y compris ceux de la démo
  (`$FF8000` = `$10` / `$14`). Jamais à la sélection, sur les portraits, au VS, sur la carte ni au classement.
  - Les **fins** n'ont pas été mesurées : peut-être une ombre dans une scène de fin, ce qui resterait correct.
- **SFA3 (ro3) tourne en mode 1 du cœur** : les registres de 0010 n'y agissent pas. L'option doit couvrir le mode 1
  aussi.

## 3. Proposition (patch 0011, rien codé en dur avant ton accord)

**Option du cœur** : « Ombres transparentes (PSP) » (DIP, comme les options 0003), **activée par défaut**, en modes 1
et 2 (SFA3, Upper, Hyper, ro9a). Entièrement **côté cœur**, sans signal du programme.

**Règle** : une tuile d'objet est une ombre si **palette OBJ = 0x14 ET code global de la tuile ∈ {`0284A`,
`305DF`-`30613`, `50888`-`5088A`}**. Le code global est celui que `Cps2ObjDraw` a déjà en main (`nCpstTile` avant
`<<7`), et le test se fait par tuile, en quelques comparaisons. Les décors en palette 0x14 ne sont pas touchés. Pas
besoin de test d'état : les codes ne servent qu'aux ombres.

- Variante plus prudente : ajouter le test `$FF8000 = 2 && $FF8004 = 4`, commun aux quatre jeux d'après les mesures.
  Mais alors les ombres des combats de démo resteraient opaques. Je ne la recommande pas.

**Mode** : nouveau mode **5 = « noir à 75 % »** (dst × 0,25, `alpha_blend(d, 0, 0xC0)`), identique à la PSP. Le mode
3 (alpha 75 % de la couleur de palette) donnerait une ombre teintée par la palette 0x14.

**Priorité** : bit 12 avec `$804240` ≠ 0 > registre de palette ≠ 0 > option ombres > opaque. Le programme garde la
main.

**Banc MAME** (copie du fork) : même règle dans `cps2_render_sprites` (le code de la tuile y est aussi), dans
l'écran RGB (`HSFA_MELANGE=1`), avec une variable `HSFA_OMBRES=1`.

**Vérifications prévues** :

- option désactivée : nonreg 32 / 16 bits, 4:3 / 16:9, identique au pixel près ;
- option activée : nonreg avec captures avant / après. Contrôle automatique : **tous** les pixels modifiés doivent
  tomber sur une tuile d'ombre (masque calculé à partir de `HSFA_G_STATS` sur les mêmes images). Captures d'un combat
  sur le décor aux poteaux (ombres transparentes, poteaux intacts) et dans Hyper ZERO.

**Jauges** : rien à faire. Les rectangles PSP sont invisibles (§1, correction). Les couleurs de remplissage en
dégradé ont été abandonnées par l'utilisateur.
