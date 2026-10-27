# Frames de sprites de l'Anthology (SFA3, `ro3`) : ce que dit la routine d'affichage

Note de la session HSFA (banc MAME, traduction du module `ro3` en 68K), 2026-10-03.
Elle complète l'étude `sfa3max-psp-widescreen/work/re/frames289/README.md` (format retrouvé via Ryu).
Source : la routine qui transforme une frame en entrées de la liste d'objets CPS2, lue dans la traduction 68K
(`hsfa/work/mame/carte_image.txt`) et vérifiée statistiquement sur le module.

**Conventions d'adresses**
- `fichier` = décalage dans `ro3_usa_prog68k.bin` ;
- `exécution` = `fichier + 0x1F0000` (valeur des pointeurs du module) ;
- les mots 16 bits sont petit-boutistes (PS2).

## 1. Le premier mot d'une frame est son TYPE (pas d'en-tête aux moitiés échangées)

La routine fait :
```
A0 = pas d'animation courant ; A0 = pointeur de frame (mot 32 bits n°2 du pas, +4)
D0 = u16 (A0)+                        ; TYPE
saut par la table T_58BC30 (exécution 0x58BC30 = fichier 0x39BC30, 16 entrées de 32 bits, index = TYPE/2)
```
- Les frames sont **rangées les unes contre les autres, au mot près** : une frame peut commencer à une adresse
  ≡ 2 (mod 4).
- Avant de lire un pointeur 32 bits, la routine se **réaligne** : `A0 ← (A0 + 3) & ~3`.
- Lire les frames comme des suites de u32 alignés donne donc l'illusion de « moitiés échangées ».

**Exemple — garde de Ryu** : la frame est en fichier **`0x4DB32A`**, pas `0x4DB328`.
- En `0x4DB328`, il y a une **frame vide** : type `0x0012`, un seul mot, rien n'est affiché.
- La frame de garde suit immédiatement.
- Des pas d'animation visent les deux adresses : 70 pointeurs vers `0x6CB328`, 37 vers `0x6CB32A`.

## 2. Type 2 : le format courant (14 421 frames, toutes avec pointeur vers le fichier 289)

```
+0   u16  type = 0x0002
+2   u16  T = nombre TOTAL de tuiles 16×16 de la frame = Σ (largeur × hauteur)   [vérifié : 14 421 / 14 421]
+4   u16  n − 1                                   (n = nombre d'objets)
     bourrage jusqu'au multiple de 4 suivant
     u32  pointeur → fichier 289 (chargé à 0xA04000) : n × (s16 dx, s16 dy)
     n × (u16 code, u16 attributs)                (= u32 (attr << 16) | code, comme dans l'étude)
```
- `T` sert de budget : `CMP T,D7 ; BCS rien ; SUB T,D7`. D7 est la place restante dans la liste d'objets ; la frame
  n'est pas affichée s'il n'y a plus de place.
- Ce sont les « numéros croissants 0x17..0x1A » vus dans l'étude. Pour la garde : 1 + 12 + 1 + 2 + 9 = 25 = `0x19`.
- Position écran de chaque objet :
  - X = (dx + origine X) & 0x3FF, puis OR avec le mot `$18` de l'objet ;
  - Y = (dy + origine Y) & 0x3FF, puis OR avec le mot `$1A` de l'objet.
- Entrée CPS2 écrite : X, Y, code, attributs.

## 3. Les autres types (lecture de la routine ; mots relatifs au début de la frame)

| type | disposition | particularités |
|---|---|---|
| `00` | `type, N, attr commun, [align], ptr 289, N × u16 code` | même attribut pour tous les objets ; `N` = nombre d'objets et budget |
| `02` | voir §2 | |
| `04` | `type, N, attr commun, dx0, dy0, N × (u16 idx, u16 code)` | pas de fichier 289 : position = table fixe `0x58B790` (exécution) en `idx` / `idx+2`, plus (dx0, dy0) |
| `06` | `type, T, n−1, dx0, dy0, n × (u16 idx, u16 code, u16 attr)` | comme `04`, attribut par objet |
| `08` | `type, T, n−1, puis n × 12 octets` (mot sauté, 2 mots, mot sauté, 2 mots…) | pas de fichier 289 ; entrées écrites en longs ; Y \| `0x2000`, code + `0x1600` (`ADDI.L #$16000000`) |
| `0A` | `type, T, n−1, attr commun, [align], ptr 289, n × u16 code` | Y \| `0x2000`, **code + `0x1600`** |
| `0C` | `type, T, n−1, [align], ptr 289, n × (code, attr)` | comme `02`, mais Y \| `0x2000` et **code + `0x1600`** (sprites communs / effets) |
| `0E` | `type, T, n−1, attr commun, [align], ptr 289, n × u16 code` | appelle `0x2F7650` (échelle = attr >> 8) ; bornage X ∈ [−0x240, 0x1C0], Y ∈ [−0x310, 0xF0] ; code + `0x1600` |
| `10` | `type, T, n−1, [align], ptr 289, n × (code, attr)` | comme `0E`, échelle lue dans le mot d'attributs de chaque objet |
| `14` | comme `08` | miroir H/V selon le sens du personnage (`$A(A6)`, bits 5-6 des attributs) |
| `16` | `type, T, n−1, attr commun, [align], ptr 289, n × u16 code` | miroir selon `$A(A6)` ; palette ajustable (`$C/$D(A6)`) ; code + `0x1600` |
| `12`, `18`, `1A`, `1C`, `1E` | un seul mot | **frame vide** : rien n'est affiché |

- Les types `00/02/04/06` gardent le code **local** à la banque du personnage (e256/e258…).
- Les types `0A/0C/0E/10/16` (et `08/14`) ajoutent `0x1600` : codes d'une banque commune.

## 4. Conséquences pour la conversion des persos MAX

- Écrire les frames en **type 2** suffit pour des persos (format de 14 421 frames sur ~14 500).
- Mettre à jour `T` (somme des tuiles), sinon la frame peut être refusée faute de place ou déborder la liste.
- Respecter le réalignement : le pointeur 289 est au premier multiple de 4 après les 3 mots d'en-tête.
- Une frame vide d'un seul mot (`0x0012`) est disponible pour les pas « invisibles ».

## Vérification rapide (Python)
```python
import struct
b = open(".../anthology_extract/decompressed/ro3_usa_prog68k.bin", "rb").read()
def frame(o):                                    # o = décalage fichier, type 2
    t, T, n1 = struct.unpack_from("<3H", b, o)
    p = (o + 6 + 3) & ~3
    ptr = struct.unpack_from("<I", b, p)[0]      # -> fichier 289 (0xA04000)
    objs = struct.unpack_from("<%dH" % (2 * (n1 + 1)), b, p + 4)
    return t, T, n1 + 1, hex(ptr), list(zip(objs[0::2], (hex(a) for a in objs[1::2])))
print(frame(0x4DB32A))   # (2, 25, 5, '0xa13a98', [(10,'0x0'), (1,'0x2300'), (5,'0x0'), (9,'0x1000'), (6,'0x2200')])
```
