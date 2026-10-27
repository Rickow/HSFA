# Transmission du 2026-10-21 : pour la reprise de samedi

À lire **avant** de lancer une session. Ce document vient de la session « recherche et bancs de coups », branche
`claude/zealous-darwin-4wgvrd`. Rien n'a été écrit sur `main` ni dans les dossiers des autres sessions.

> **État au 2026-10-26** : la branche a été fusionnée dans `main` (`4604615`), et le journal va depuis jusqu'au §176.
> Les §1 et §2 ci-dessous sont donc faits ou dépassés ; les §3 à §7 restent valables. Ajout du 2026-10-26 pour la
> session MAX : `docs/rapports/recherche/README.md` §5 (coups des persos MAX, exécutables de *CvS2* et de *CFE*).

## 1. Avant toute session : fusionner sans rien écraser

Ma branche a 14 commits d'avance sur `main`. `main` n'a pas bougé depuis le 2026-10-18 (`412456e`), et ma branche le
contient déjà. **Tant que `main` n'a pas bougé, la fusion est une simple avance rapide : aucun conflit possible.**

```sh
git fetch origin
git log --oneline origin/main -1          # doit afficher 412456e ; sinon voir plus bas
git checkout main && git merge --ff-only origin/claude/zealous-darwin-4wgvrd && git push origin main
```

La branche ne touche **ni** `src/`, `scripts/`, `patches/`, **ni** `max/` ou `tools/max/`. Elle ajoute ses propres
fichiers (`docs/rapports/recherche/`, `tools/guide-coups/`, `tools/sondes-recherche/`, les deux rapports du
2026-10-21) et modifie quelques fichiers partagés :

| Fichier partagé | Ce que la branche y change |
|---|---|
| `docs/journal/HANDOFF.md` | ajoute **§167 à §172** à la fin ; une ligne du §170 corrigée |
| `AGENTS.md` | une puce au §3 (méthode, §171) et un encadré en tête du §5 (point d'étape) |
| `docs/methodes/pieges-du-traducteur.md` | une ligne au tableau du §4 |
| `re/connaissances/sfa3_arcade.tsv` | 3 lignes ajoutées à la fin ; la ligne `$05DAEE` complétée |
| `docs/rapports/README.md` | une ligne en tête du tableau |
| `docs/architecture/coeur-fbneo.md` | 3 lignes ajoutées : le QSound de FBNeo est l'émulation de superctr ; comparer le son par tolérance entre le fork et le cœur |
| `docs/journal/SESSION-CLOUD-2026-10-16.md` | lignes de synthèse ajoutées pour les §167 à §169 |

**Si `main` a bougé entre-temps** : fusionner `main` dans la branche (`git merge origin/main`, jamais de rebase ni de
`--force`). Les seuls conflits possibles sont des ajouts en fin de `HANDOFF.md` ou de `sfa3_arcade.tsv` : garder
**les deux** blocs.

**Numérotation du journal** : §167 à §172 sont pris. **La prochaine section libre est §173.** Une session qui
écrirait un « §167 » depuis l'ancien `main` créerait un doublon : la renuméroter à la fusion.

## 2. Ce que chaque session lit en premier

Le détail est dans [`docs/rapports/POINT-ETAPE-2026-10-21.md`](../rapports/POINT-ETAPE-2026-10-21.md) (« le point »).
Chaque session n'en lit que sa part.

| Session | À lire | À faire d'abord |
|---|---|---|
| Traducteur / validation | point §0, §2.1, §2.3 ; journal §171 ; `D-SONDES.md` §4 | verser `EXG_PILE_D`, `AIDE_ROXR`, `BITOP_DN` et les aides `roxr`/`sbcd` (copie dans `work/agent_defauts_banc/`) ; réparer `valide_tout.sh` (`$S` non défini, chemins `work/`) ; après reconstruction : `paires_exg.py` doit rendre 0, et le Killer Bee Assault de Cammy faire 60 |
| MAX dans Upper | point §4.1, décisions D1-D2 | verser les crochets `MAX=1` (`integre_max.py`…) et l'entrée `upper_max` de `paquet_fbneo.py` ; réparer `tools/integration-max/upper/assembler.sh:7` ; reconstruire Upper + MAX après le traducteur |
| Greffe Arcade (voie B) | point §4.2, décisions D1-D4 | verser les outils et interrupteurs des étapes 4-6 et le diff du paquet ro9a ; mettre à jour `re/CONFLITS.md` (n° 1-2 réglés, `$FF7F00` à ajouter) ; refaire le rebase après le traducteur |
| Cœur / son / décors | point §2.2, §4.3, décisions D5-D6 | registre des cœurs et archives livrés (md5) ; fiches des patchs 0010-0011 ; vérification de la chaîne à 15 patchs ; noms de patchs périmés dans les rapports |
| Recherche / bancs (cette session) | point §5 | rien n'est en cours ; reprise possible : les 22 écarts de la matrice, ou les replays Fightcade pour un mode de difficulté |

**Ordre conseillé** :
1. traducteur, puis reconstruction et validation complète, une seule fois pour tous ;
2. ensuite MAX et la greffe, chacune dans son dossier.

Deux sessions qui reconstruisent en même temps dans le même `work/` s'écraseraient : en lancer une seule à la fois,
ou des dossiers de sortie séparés (`TRAVAIL=`).

## 3. Ce que l'utilisateur peut faire sans crédits

- D1 à D3 sont **décidées** (§5) : rien à faire avant samedi.
- Trancher **D4 à D7** quand l'occasion se présente : décor de l'Arcade greffée, jauges à 50 %, Vorbis par défaut,
  révision d'arcade de référence pour SFA3.
- Retrouver dans `work/agent_defauts_banc/` le diff des trois règles du traducteur et le rapport `DEFAUTS-BANC.md`.
- Essais sur appareil, si possible : Vorbis contre ADX, Android réel, vitesse sur RGB10X.

## 4. Ce qui n'a pas été fait

- Aucun correctif n'est livré. Le Killer Bee Assault est seulement **prouvé** par une rustine d'essai
  (`tools/sondes-recherche/rustine_angle.py`, sur une copie de l'archive d'Hyper). La correction se fait dans le
  traducteur.
- Les documents des autres sessions ne sont pas corrigés : le point les signale à leurs propriétaires.
- Pas de pull request vers `main` : la fusion est laissée à l'utilisateur (§1).

## 5. Décisions D1 à D3 (prises le 2026-10-21, à appliquer)

Détail, raisons et à qui elles reviennent : `re/CONFLITS.md`, section « Décisions du 2026-10-21 ».

- **D1, ids MAX dans Hyper** : Eagle `$26`, Maki `$27`, Yun `$28`, Ingrid `$29`. Upper garde `$26`, `$27`, `$2D`,
  `$2E`. La conversion vers Hyper a une table de correspondance unique, appliquée à chaque id.
- **D2, `$FF7F00`** : MAX garde `$FF7F00-$FF7FFF` dans les deux jeux. La greffe déplace son drapeau « partie Arcade »
  en `$FF7E00`. Ses relogés restent sous `$FF7E00`.
- **D3, `$3A0000-$3BFFFF` dans ro9a** : réservé au code MAX, comme dans Upper. La greffe abaisse de `$20000` ses
  tables d'animation natives (données), le surplus partant dans le bloc externe.


## 6. Chantier à ouvrir : verser l'arriéré dans l'index `re/`

Mesure du 2026-10-23 : plus de la moitié des adresses citées dans le journal et les rapports sont absentes de
`re/connaissances/` (journal 62 %, `INDEX-HYPER` 96 %, `ETATS-HYPER` 83 %, `GREFFE-*` 61-100 %, `ADRESSES-MAX-UPPER`
70 %, `ECARTS-UPPER` 65 %). Dans Upper, 188 fonctions seulement sur 2 933 ont un rôle nommé. Le versement se fait
rapport par rapport, outillé (adresse, phrase qui la décrit, source), puis relu et passé à `re/outils/verifie.py`.
Compter 2 à 4 sessions, **une seule à la fois** : toutes écrivent dans les mêmes TSV. C'est le préalable à toute source
annotée (« décompilation ») d'Upper.

## 7. Apports des pages TCRF et MobyGames (2026-10-25)

Détail : `docs/rapports/recherche/README.md` §4. Ce que chaque session peut en tirer :

- **Traducteur / validation (SFA3)** :
  - deux sondes de révision toutes faites. La projection de Karin (Yashiro Kuzushi) en mode **Saikyo** vide la barre de
    vie, et la Death Cross Dance de Juni et Juli en Saikyo (Dramatic Battle) fait 80 % de dégâts d'un coup ;
  - les deux bugs existent **avant la 980904**, donc dans les deux révisions de l'Anthology (980629, 980727). Une
    traduction juste doit les reproduire ; l'oracle `sfa3` (980904) ne les a pas ;
  - l'arcade européenne démarre en vitesse **Free 1**, la japonaise en Turbo 1 et l'américaine en Turbo 2 : une
    comparaison image par image doit imposer la même vitesse.
- **Hyper / greffe** : les mêmes sondes valent pour les ZERO 3 d'Hyper et d'Upper. Evil Ryu (ZERO 2) a, sur l'arcade
  d'export, des dialogues et une fin propres, qu'aucun portage localisé n'a repris : à vérifier dans Hyper et dans la
  greffe Arcade.
- **Cœur / options** : le réglage « Regulation » (sang rouge ou blanc), actif par défaut hors du Japon et gardé par
  l'Anthology, est un candidat pour les options du cœur.
- **SFA1** : un menu de test des personnages s'ouvre par FF8001 = `0A` dans le menu de test de l'arcade (à essayer sur
  la traduction, sans garantie).
- **Son** : le disque garde des musiques inutilisées en ADX (*Super Puzzle Fighter II Turbo* au complet, *Pocket
  Fighter* PS/Saturn, « Theme of Chun-Li » de *Marvel vs. Capcom*, « Killing Moon » de *3rd Strike*) : de la matière
  pour une option de musique.
