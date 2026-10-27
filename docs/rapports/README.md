# Rapports d'agents (anonymisés)

Rapports complets des études menées en parallèle (2026-10-07 au 2026-10-11). Le [journal](../journal/HANDOFF.md)
(§138-§146) en donne la synthèse ; les outils correspondants sont dans `tools/` (dossier indiqué, voir
[tools/README.md](../../tools/README.md)). Les chemins `<workspace>/work/…`
désignent le dossier de travail local (données de jeu, jamais publiées).

| Rapport | Sujet | Outils |
|---|---|---|
| [POINT-ETAPE-2026-10-21.md](POINT-ETAPE-2026-10-21.md) | **point d'étape transverse** : état des chantiers, code en retard sur le savoir, archives périmées, conflits, décisions à prendre | — |
| [GREFFE-ETAT.md](GREFFE-ETAT.md) | **voie B, état à lire en premier** : `ro9a7_fige` (60/85 fins), étape 7, fins restantes, place mémoire | `tools/greffe-arcade` |
| [BANC-COUPS.md](BANC-COUPS.md) | banc MAME des coups (SFA3, Upper, Hyper) : méthode, taux, défauts trouvés, frame data, non-régression MAX (sans le tableau du guide, hors dépôt) | non versés (`tools/sondes-recherche` pour le banc FBNeo) |
| [REORG-ETAPES-CD.md](REORG-ETAPES-CD.md) | réorganisation des données, étapes C et D (pointeurs des tables ROM, retrait des talons) ; mise de côté | non versés |
| [COUVERTURE-ARCADE.md](COUVERTURE-ARCADE.md) | couverture ROM arcade SFA3 ↔ traduction, zones système, pistes | non versés |
| [MISE-EN-ROUTE-ro9.md](MISE-EN-ROUTE-ro9.md), [BANQUES-ET-MODES-ro9.md](BANQUES-ET-MODES-ro9.md) | Hyper au banc puis au fork : profil `ro9`, RAM, bloc `$940000`, banques de sprites, modes et versions | `tools/hyper-etats` (en partie) |
| [PALETTES-PLANS-ro5.md](PALETTES-PLANS-ro5.md) | Upper : palettes et plans au banc (conteneur 32×32 `e525`, besoin d'une base par plan) | — |
| [HASARD.md](HASARD.md) | générateur aléatoire, divergence MAME/FBNeo | — |
| [ECARTS-UPPER.md](ECARTS-UPPER.md) | 509 écarts Upper ↔ arcade SFA3, tables étendues, champs déplacés | — |
| [ADRESSES-MAX-UPPER.md](ADRESSES-MAX-UPPER.md) | 113 routines du moteur appelées par MAX, retrouvées dans Upper | — |
| [TYPAGE-MAX.md](TYPAGE-MAX.md) | type mesuré dans Upper des 212 champs touchés par MAX | — |
| [CONV-MAX.md](CONV-MAX.md) | passe de conversion du code MAX (disposition arcade → image Upper) | `tools/integration-max/conversion` |
| [VOIX-MAX.md](VOIX-MAX.md) | voix MAX dans la ROM QSound, bruitages communs | `tools/integration-max/voix` |
| [INDEX-HYPER.md](INDEX-HYPER.md) | index statique d'Hyper (ids `$102`, bits de version, 45 tables, mécaniques) | — |
| [ETATS-HYPER.md](ETATS-HYPER.md) | machine à états, écran de mode, EX, script de partie | `tools/hyper-etats` |
| [SON-HYPER.md](SON-HYPER.md) | son d'Hyper sur PS2 (pilote natif, flux ADX de `Y_DATA.BIN`) | — |
| [FLUX.md](FLUX.md) | lecteur de flux musique ADX (fork MAME + cœur FBNeo) | `tools/flux` |
| [DECORS-WS.md](DECORS-WS.md) | export exact des décors en PSD (balayage de caméra, recollage) | `tools/decors/export` |
| [REIMPORT.md](REIMPORT.md) | réimportation PSD → tuiles CPS2, format des données de décor, blocs libres | `tools/decors/reimport` |
| [ETAPE-A.md](ETAPE-A.md) | réorganisation des données, étape A (journal des conversions, oracle RAM) | `tools/reorg` |
| [ZANGIEF.md](ZANGIEF.md) | blocs de couleur dans les décors d'Upper (tuile 32×32 vide opaque) | `tools/diagnostics/zangief` |
| [COUPS.md](COUPS.md) | Sakura 42 coups, super d'Akuma sans boule : deux pertes du traducteur | `tools/diagnostics/coups` |
| [BUILD.md](BUILD.md) | script de construction depuis l'ISO, reproductibilité | `scripts/construction`, `src/hsfa` |
| [CARTE-MODULES.md](CARTE-MODULES.md) | tous les modules de l'Anthology (SFA, SFA2 et variantes, Pocket Fighter, menu) | `tools/carto-modules` |
| [INJECTION-FORK.md](INJECTION-FORK.md) | injection des décors widescreen dans le programme traduit (fork, FBNeo) | `tools/decors/injection` |
| [SON-HYPER-ROM.md](SON-HYPER-ROM.md) | ROM son d'Hyper avec les voix SFA1/SFA2 par version | `tools/son-hyper` |
| [PLAN-SON-HYPER.md](PLAN-SON-HYPER.md) | musique d'Hyper : origine des flux (jeu A = *Super SF2*), partitions SFA1/SFA2/SSF2, compression du reste | `tools/son-hyper` |
| [PLAN-VORBIS.md](PLAN-VORBIS.md) | flux musique en Ogg Vorbis dans le cœur FBNeo (stb_vorbis, boucles, états, encodage) | `tools/flux`, `tools/fbneo-hsfa` |
| [PLAN-PARTITIONS-HYPER.md](PLAN-PARTITIONS-HYPER.md) | musiques ZERO / ZERO 2 d'Hyper par leurs pilotes d'origine (carte musique : 2ᵉ Z80 + 3ᵉ QSound) | `tools/son-hyper` |
| [PARTITIONS-HYPER.md](PARTITIONS-HYPER.md) | étude du 2026-10-14 : pilotes Z80 v1.04/v1.05, banc Z80, origine des variantes (jeu A = Super SF2) ; plan à jour : PLAN-SON-HYPER | `tools/son-hyper/partitions` |
| [FBNEO-HYPER.md](FBNEO-HYPER.md) | Hyper dans le cœur FBNeo HSFA (pilote `sfa3hhsfa`) | `tools/fbneo-hsfa` |
| [ETUDE-UPPER-HYPER.md](ETUDE-UPPER-HYPER.md) | voie A / voie B pour « Upper + modes d'Hyper » (décision : B) | `tools/etude-upper-hyper` |
| [DECOR-SFA2.md](DECOR-SFA2.md), [DECOR-SFA2-EXPORT.md](DECOR-SFA2-EXPORT.md) | import d'un décor de SFA2 dans SFA3 traduit, tirage par perso | `tools/decors/sfa2` |
| [ROCKNIX.md](ROCKNIX.md) | cœurs pour la RGB10X sous ROCKNIX (aarch64) | `tools/rocknix` |
| [DEFAUTS-HYPER.md](DEFAUTS-HYPER.md) | jauge de super du P2 sans plafond et plantage TRAINING d'Hyper : CMP mémoire-mémoire perdu (règle `CMPMM`) | `src/hsfa` |
| [REJEU-FBNEO.md](REJEU-FBNEO.md) | rejeu QSound des sons SFA1/SFA2 dans le cœur FBNeo, membres lus dans le zip du jeu | `tools/fbneo-hsfa` |
| [GREFFE-PREPARATION.md](GREFFE-PREPARATION.md), [GREFFE-DECORS.md](GREFFE-DECORS.md) | voie B : greffe du mode Arcade d'Upper sur Hyper (scènes, cœur à greffer, table A5, `$102`, décors) | `tools/greffe-arcade` |
| [EXPLOSION.md](EXPLOSION.md) | animation d'explosion arcade (`$2E50A0` n° 5) pour les fins MAX ; formats de frames `$12` / 6 | `tools/diagnostics/explosion` |
| [BANQUE-1A.md](BANQUE-1A.md) | champ `$1A` des acteurs : emplacements de banques graphiques (arcade, Upper, Hyper), fins MAX | `tools/diagnostics/banque-1a` |
| [PORTRAITS.md](PORTRAITS.md) | glitch du grand portrait au face-à-face d'Upper : chargement différé de l'emplacement 4 (banc, cœur) | `tools/diagnostics/portraits` |
| `BANDEAU-A.md` | texte « STREET FIGHTER ALPHA » du gros A qui défilait : flux d'octets `(An)+` à adresse paire (règle `FLUXEA`) | `tools/diagnostics/bandeau-a` |
| `VICTOIRE.md` | écran de victoire : réplique conforme, « PRESS START » clignotant voulu par le portage | `tools/diagnostics/victoire` |
| `EFFETS-UPPER.md` | griffe et masque de Vega (objets attachés), vraie table des blocs par perso d'Upper `T_749838` | `tools/diagnostics/effets-upper` |
| `OPTIONS.md` | écran d'options du portage (code C), réglages et leurs adresses, options du cœur FBNeo, retour au menu | `tools/options` |
| `ETAPE-B.md` | réorganisation des données, étape B : pointeurs de code relogés, −46 % de conversions ; course de cadence turbo | `tools/reorg/etape-b` |
| `GREFFE-ETAPE2.md` | voie B, étape 2 : l'Arcade d'Upper tourne dans Hyper augmenté (3 combats), place, tri, `$102→$116` | `tools/greffe-arcade` |
| `BLOC-HYPER.md` | Hyper : choix de la ligne du bloc par perso, sous-tables de `$2B8`, recette pour les persos MAX (places 38-41) | — |
| `GREFFE-ETAPE3.md` | voie B, étape 3 : combat = Hyper, partie Arcade complète jusqu'à la fin et au GAME OVER (Ryu Z3, Ryu ALPHA, Chun-Li Z2) | `tools/greffe-arcade` |
| `OPTIONS-HYPER-UPPER.md` | options d'Hyper comparées à Upper ; BGM de Hyper greffé dans Upper (option du cœur, `BGM_UPPER`) | `tools/options/hyper-upper` |
| `COEUR-BANQUES.md` | cœur FBNeo : registre des plans pour ro9a (patch 0008) ; place 68K : 7 trous libres de la carte CPS2 (5,08 Mo, patch 0009), banque commutée chiffrée | `patches/fbneo` |
| `DECOR-CAMMY.md` | décor de Cammy d'Upper et de SFA3 : scroll2 perdu (adresses vidéo hôte décalées de 8 dans une table, règle `VRAM_TABLE`) ; balayage des 40 décors | `src/hsfa` |
