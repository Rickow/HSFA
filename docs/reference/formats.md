# Formats de données

Point d'entrée vers les formats établis par le projet. Chaque ligne renvoie au document qui fait foi.

## 1. Fichiers produits par la chaîne

| Fichier | Format | Source |
|---|---|---|
| ROM programme (`sz3ud.03c…sz3.10b`) | 4 Mo découpés en 8 × 512 Ko, octets de chaque mot échangés (`ROM_LOAD16_WORD_SWAP`) | [OUTILS](../architecture/OUTILS.md) §5 |
| `ext_<adresse>.bin`, `ext_liste.txt` | octets à servir à partir de `$<adresse>`, mots gros-boutistes ; liste des bases | OUTILS §5 |
| `carte_image.txt` | `aaaaaa vvvvvvv mnémonique` : adresse 68K, va MIPS, instruction émise | OUTILS §5 |
| `chutes.json`, `mem_miss.json`, `audit_exacts.txt` | audits des pertes silencieuses du traducteur | OUTILS §5, journal §107, §132 |
| `banques/f<N>.bin`, `plan1.bin`, `plan2.bin`, `f312.bin`, `carte.txt` | u32 petit-boutiste par tuile locale = code CPS2 global (`0xFFFFFFFF` = vide) ; carte perso / animation → fichier | OUTILS §5 |
| `hsfa_gfx.bin` | tuiles 16×16 au format interne MAME (128 o), tuile k = code `$40000 + k` | OUTILS §5, [patches/mame-fork](../../patches/mame-fork/README.md) |
| `hsfa_plans.bin` | région à partir de `$3000000` : 8×8 en +0, 16×16 en `+$400000`, 32×32 en `+$A00000` | OUTILS §5 |
| archives du cœur (`*.zip`) | ROM, `hsfa_ext.bin`, `hsfa_tab.bin`, `hsfa_gfx.bin`, flux et rejeu stockés | [coeur-fbneo](../architecture/coeur-fbneo.md) §2 |
| `hooks_fork_<module>.json` | cibles natives du portage → sites d'appel | OUTILS §5 |

## 2. Données de l'Anthology

| Sujet | Résumé | Source |
|---|---|---|
| Module `roN_usa_prog68k.bin` | en-tête MWo3 ; malgré son nom, c'est du **MIPS** ; Z80 recompilé puis 68K recompilé, puis données | [traducteur](../architecture/traducteur.md) §2, [CARTE-MODULES](../rapports/CARTE-MODULES.md) |
| `X_DATA.BIN` | archive AFS de 553 entrées, groupes de jeu délimités par les modules MWo3, compression LZSS « MWo3 » | [BUILD](../rapports/BUILD.md) §1.1, `src/hsfa/mwo3_codec.py`, `extract_anthology.py` |
| `Y_DATA.BIN` | flux musique ADX (1,8 Go) | [FLUX](../rapports/FLUX.md) |
| Conteneurs graphiques | tuiles 4 bpp packées (2 pixels par octet), compression du moteur (`lz148778.py`) | `src/hsfa/anthgfx.py`, `gfx.py`, journal §45 |
| Frames de sprites | premier mot = TYPE, frames au mot près, type 2 courant ; types `$12` et 6 | [FRAMES-Anthology](FRAMES-Anthology.md), [EXPLOSION](../rapports/EXPLOSION.md) |
| Champ `$1A` des acteurs | emplacement de banque graphique | [BANQUE-1A](../rapports/BANQUE-1A.md) |

## 3. Décors

| Sujet | Résumé | Source |
|---|---|---|
| scroll1 / scroll2 / scroll3 | listes `$19146` / `$19272` / `$194A2`, bibliothèques de blocs `$367494` / `$391014` / `$3AC614` (adresses arcade de SFA3) ; équivalents ro3 / ro5 | [REIMPORT](../rapports/REIMPORT.md) §5 |
| Palettes de décor | 32 palettes copiées par plan, bloc souvent plus court : les places « libres » sont celles du décor suivant | REIMPORT §5.4 |
| Blocs libres de la ROM | fin libre `$3C8540-$3FFFFF` (SFA3 arcade), blocs libres SFA3 / Upper | REIMPORT §6, `tools/decors/reimport/blocs_libres.json` |
| Export PSD | balayage de caméra, recollage exact au pixel | [DECORS-WS](../rapports/DECORS-WS.md) |
| Injection widescreen | bloc externe, 18 `LEA`, 32 palettes par décor | [INJECTION-FORK](../rapports/INJECTION-FORK.md) |
| Décors de SFA2 | import dans SFA3 traduit, tirage par perso | [DECOR-SFA2](../rapports/DECOR-SFA2.md), [DECOR-SFA2-EXPORT](../rapports/DECOR-SFA2-EXPORT.md) |

## 4. Son

| Sujet | Résumé | Source |
|---|---|---|
| Protocole QSound du jeu | boîte aux lettres `$618000`, commandes du 68K vers le Z80 | journal §58, §79, §118 |
| ROM son hybride d'Upper | Z80 d'Upper + musiques de SFA3 | journal §127, `src/hsfa/gen_hybride.py` |
| Son natif d'Hyper sur PS2 | pilote natif, flux ADX | [SON-HYPER](../rapports/SON-HYPER.md) |
| Voix par version d'Hyper, rejeu | 2ᵉ QSound, table du rejeu, redirection dans le programme traduit | [SON-HYPER-ROM](../rapports/SON-HYPER-ROM.md), [REJEU-FBNEO](../rapports/REJEU-FBNEO.md) |
| Voix MAX | commandes `$02A4-$05FC`, renumérotation v2 | [VOIX-MAX](../rapports/VOIX-MAX.md) |
| Table des flux | code son → flux ADX (`hsfa_flux_table.txt`) | `tools/flux/gen_table_flux.py` |

## 5. SFA3 MAX (PSP)

Conteneurs des persos, tuiles, conversion vers la CPS2, modules de code : [MAX-Etude-Contenu-Persos](../MAX-Etude-Contenu-Persos.md)
et le dossier [`max/`](../../max/README.md) (session MAX).
