# Street Fighter Alpha HSFA sur Powkiddy RGB10X (ROCKNIX)

Ce dossier installe le cœur FinalBurn Neo « HSFA » sur une console RK3326 sous ROCKNIX : Powkiddy RGB10X, et aussi
RGB10, R36S, RG351… Avec ce cœur, RetroArch fait tourner les trois jeux retraduits de l'Anthology PS2 :

- Street Fighter Alpha 3 ;
- SFA3 Upper ;
- Hyper Street Fighter Alpha.

Il y a deux cœurs :

- **4:3 (384×224)** : il remplit l'écran 640×480 de la RGB10X, c'est le cœur conseillé ;
- **16:9 (448×224)** : il montre plus de décor, mais l'image est réduite et encadrée de bandes noires.

> Les cœurs sont compilés et vérifiés sur PC, mais **pas encore essayés sur une console**. Le §7 décrit un essai
> rapide par SSH qui mesure la vitesse réelle.

> **Version du 2026-10-16 (patchs FBNeo 1 à 10)** : ces cœurs lisent les musiques **Ogg Vorbis** du zip d'Hyper
> (zip de 201 Mo au lieu de 743 Mo) et contiennent la carte musique ZERO / ZERO 2 (désactivée tant que le zip n'a
> pas `hsfa_musique.bin`). Un zip construit avec `HSFA_FLUX_FORMAT=ogg` **demande ces cœurs** : un ancien cœur
> laisse ces musiques muettes. Les zips construits avant restent lisibles. Vérifiés sur PC sous émulation ARM
> (`qemu-aarch64`) : même match qu'au PC, son identique à ±1 près. Essai sur la console : §7 bis.
>
> **Version du 2026-10-16 (b), patch 11** : dans Hyper, la roulette (perso au hasard) passe sur **Select** (maintenir
> Select et valider sur la grille), Start reste aux EX et aux S-ISM. Select étant aussi la touche de raccourci de
> RetroArch sous ROCKNIX, vérifier que Select + bouton lance bien la roulette.

## 1. Contenu

| Fichier | Rôle |
|---|---|
| `fbneo_hsfa_libretro.so` + `.info` | cœur **« FinalBurn Neo HSFA »** (4:3) pour aarch64 |
| `fbneo_hsfaws_libretro.so` + `.info` | cœur **« FinalBurn Neo HSFA Widescreen »** (16:9) pour aarch64 |
| `jeux/sfa3hsfa.zip` | Street Fighter Alpha 3 (HSFA) |
| `jeux/sfa3uhsfa.zip` | Street Fighter Alpha 3 Upper (HSFA) |
| `jeux/sfa3umhsfa.zip` | Street Fighter Alpha 3 Upper MAX (HSFA) |
| `jeux/sfa3hhsfa.zip` | Hyper Street Fighter Alpha (HSFA) |
| `jeux/*_sources.txt` | date et empreinte md5 des fichiers mis dans chaque zip |
| `hsfa_flux_table.txt` | table des musiques PS2 (code du jeu → piste du `Y_DATA.BIN`) |
| `es_systems_hsfa.cfg` | ajoute un système **« Street Fighter Alpha HSFA »** dans EmulationStation |
| `gamelist.xml` | noms lisibles des trois jeux dans la liste |
| `essai_console/` | essai sans écran par SSH : vitesse et comparaison avec le PC (§7) |

**Il faut une version de ROCKNIX d'octobre 2024 ou plus récente.** Les cœurs demandent une glibc 2.38 ou plus
récente. ROCKNIX 20241029 a la glibc 2.40, et 20261001 (la version actuelle) la 2.41.

## 2. Accéder aux fichiers de la console

ROCKNIX range tout sous `/storage`. Voici les dossiers utilisés ici :

| Dossier sur la console | Partage réseau (Samba) | Contenu |
|---|---|---|
| `/storage/roms/` | `games-roms` | jeux et BIOS |
| `/storage/.config/` | `config` | réglages d'EmulationStation et de RetroArch |
| `/storage/cores/` | *(pas de partage)* | cœurs ajoutés par l'utilisateur |

Pour activer l'accès réseau :

1. Dans EmulationStation, ouvrir **Start → Network Settings**. Activer le Wi-Fi, puis **Samba** et **SSH**.
2. Noter l'**adresse IP**, affichée en haut du menu.
3. L'utilisateur est `root`. Le mot de passe se trouve dans **System Settings → Security**.

Vous pouvez ensuite vous connecter de trois façons :

- **Windows** : `\\<IP>\games-roms`, ou un client SFTP comme WinSCP (port 22) ;
- **macOS** : `smb://<IP>` ;
- **Linux** : `smb://<IP>`, ou `scp` et `sftp`.

## 3. Installer les cœurs

ROCKNIX lance les cœurs depuis `/tmp/cores`. Ce dossier superpose deux autres dossiers :

- les cœurs livrés avec le système, dans `/usr/lib/libretro`, en lecture seule ;
- les cœurs de l'utilisateur, dans **`/storage/cores`**.

Un fichier copié dans `/tmp/cores` est donc en réalité enregistré dans `/storage/cores` : il est conservé au
redémarrage et lors des mises à jour.

**Méthode SSH ou SCP (conseillée)**, à lancer depuis le dossier `livraison/` sur le PC :

```sh
scp fbneo_hsfa_libretro.so fbneo_hsfa_libretro.info \
    fbneo_hsfaws_libretro.so fbneo_hsfaws_libretro.info root@<IP>:/tmp/cores/
```

Avec WinSCP, déposer les quatre fichiers dans `/tmp/cores/`. Si vous les mettez plutôt dans `/storage/cores/`,
redémarrez la console.

**Sans SSH** :

1. Copier les fichiers `.so` dans `games-roms` (par exemple dans `roms/hsfa/`).
2. Lancer un jeu, ouvrir le menu de RetroArch, puis **Menu principal → Charger un cœur → Installer ou restaurer un
   cœur**.
3. Choisir le fichier `.so`. RetroArch l'installe dans `/tmp/cores`, donc dans `/storage/cores`.

**Ne pas renommer les cœurs.** EmulationStation appelle `/tmp/cores/<nom>_libretro.so`, et les noms `fbneo_hsfa` et
`fbneo_hsfaws` sont ceux qu'utilise `es_systems_hsfa.cfg`. Ils ne remplacent pas le FBNeo de ROCKNIX (`fbneo`), qui
reste disponible pour les autres jeux.

## 4. Mettre les jeux

1. Créer le dossier **`/storage/roms/hsfa/`** (partage `games-roms`, dossier `hsfa`).
2. Y copier `sfa3hsfa.zip`, `sfa3uhsfa.zip`, `sfa3umhsfa.zip` et `sfa3hhsfa.zip`, ainsi que `gamelist.xml` si vous voulez des noms
   lisibles.
3. **Ne pas renommer les zips** : c'est leur nom qui désigne le jeu. Le zip `sfa3.zip` d'origine n'est pas nécessaire.

Les zips ne pèsent que 23 à 37 Mo et tiennent sur n'importe quelle carte.

## 5. Ajouter le système dans EmulationStation

Les menus d'EmulationStation ne proposent que les cœurs déclarés pour chaque système. Le fichier
`es_systems_hsfa.cfg` crée donc un système à part, **« Street Fighter Alpha HSFA »** :

- dossier `/storage/roms/hsfa` ;
- émulateur RetroArch ;
- cœurs `fbneo_hsfa` (par défaut) et `fbneo_hsfaws`.

Les systèmes existants ne sont pas modifiés.

1. Copier `es_systems_hsfa.cfg` dans **`/storage/.config/emulationstation/`** (partage `config`, dossier
   `emulationstation`).
2. Redémarrer EmulationStation : **Start → Quit → Restart EmulationStation**, ou redémarrer la console.
3. Le système apparaît avec le thème « CPS-II ». Si les jeux n'apparaissent pas : **Start → Game Settings → Update
   Gamelists**.

**Choisir le cœur 4:3 ou 16:9 :**

- **pour un seul jeu** : ouvrir les options du jeu depuis la liste. Selon la version, c'est un appui long sur le
  bouton de validation ou la touche Select. Dans les réglages avancés du jeu (**Advanced Game Options**), régler
  **Emulator / Core** sur `retroarch / fbneo_hsfaws` ;
- **pour tout le système** : sur la liste des systèmes, **Start → Game Settings → Per System Advanced
  Configuration → Street Fighter Alpha HSFA → Emulator / Core** ;
- **pour avoir les deux à la fois** : copier chaque zip une seconde fois, sous un nom de dossier différent. Le zip
  lui-même ne doit pas être renommé, par exemple `roms/hsfa/16-9/sfa3hhsfa.zip`. Choisissez ensuite le cœur 16:9
  pour ces copies.

*Solution de rechange* : on peut aussi ranger les zips dans `roms/cps2` et ajouter les cœurs au système CPS-II.
Il faudrait alors un `es_systems_cps2.cfg` qui répète **toute** la liste des cœurs CPS-II de ROCKNIX : `fbneo`,
`mame2003_plus`, `mame2010`, `fbalpha2012` et `AdvanceMame`. En effet, un fichier `es_systems_*.cfg` remplace
toute la balise `<emulators>`. Le système séparé est plus simple et ne risque rien lors des mises à jour.

## 6. Musiques PS2 (dossier système)

Les musiques que le son arcade ne connaît pas viennent du disque PS2 de l'Anthology. Elles ne sont pas dans les
zips. Il s'agit :

- des pistes de Guile, Fei-Long, Dee Jay et T.Hawk dans Upper ;
- des musiques ZERO, ZERO 2 et ALPHA dans Hyper.

Le dossier système de RetroArch sous ROCKNIX est `/storage/roms/bios`. Le cœur cherche donc ses fichiers dans
**`/storage/roms/bios/fbneo/hsfa/`** (partage `games-roms`, dossier `bios/fbneo/hsfa`).

1. Créer `bios/fbneo/hsfa/`. Respecter les minuscules et les majuscules : le système de fichiers de Linux les
   distingue.
2. Y copier `hsfa_flux_table.txt`.
3. Y mettre **une seule** des trois sources suivantes :
   - **`Y_DATA.BIN`**, extrait de l'ISO de l'Anthology avec 7-Zip par exemple (1,8 Go). **C'est la solution
     conseillée** : le fichier passe même sur une carte en FAT32 ;
   - l'ISO entière, renommée **`anthology.iso`**. Elle pèse 4,4 Go et **ne tient donc pas sur une partition FAT32**
     (limite de 4 Go) : il faut de l'exFAT ou de l'ext4 ;
   - un fichier texte **`ydata.txt`** qui contient le chemin complet du `Y_DATA.BIN` ou de l'ISO, par exemple
     `/storage/roms/ps2/anthology.iso`.

Sans ces fichiers, les jeux fonctionnent quand même, mais sans les musiques en question. La musique précédente
peut alors continuer à leur place.

**Réglage** : dans **Options du cœur → DIP switches**, l'option « PS2 music (ADX streams, Y_DATA.BIN) » propose
trois valeurs : `Off`, `Missing tracks only` et `All tracks`. `All tracks` est la valeur par défaut pour Hyper.

## 7. Essai par SSH (facultatif, conseillé au premier essai)

Cet essai lance chaque jeu sans écran pendant 3 000 images. Il affiche la vitesse en images par seconde et compare
6 captures par jeu avec celles du PC.

```sh
scp -r essai_console root@<IP>:/storage/hsfa_essai
ssh root@<IP>
cd /storage/hsfa_essai && sh essai_hsfa.sh
```

Le script lit les cœurs dans `/storage/cores` et les zips dans `/storage/roms/hsfa`. On peut changer ces dossiers
avec les variables `COEURS=` et `ZIPS=`.

Comment lire le résultat :

- **Vitesse** : le jeu tourne à 59,6 images/s. Il faut donc nettement plus de 60 images/s, idéalement 80 ou plus.
  Sur PC (Ryzen 5 5600X), les trois jeux font environ 1 030 à 1 100 images/s, soit à peu près autant que le *Street
  Fighter Alpha 3* arcade d'origine (sfa3) dans le même cœur. HSFA ne coûte donc pratiquement rien de plus que le
  CPS2 normal, et celui-ci tourne à pleine vitesse sur RK3326.
- **« captures identiques à la référence PC : 36 / 36 »** veut dire que le cœur ARM donne exactement les mêmes images
  que le PC. Un écart signale un problème de compilation, sauf si le script annonce que les zips diffèrent de ceux de
  la référence.

Supprimer ensuite le dossier : `rm -r /storage/hsfa_essai`.


## 7 bis. Essai du son d'Hyper par SSH (version du 2026-10-16)

Le dossier `essai_son/` rejoue sans écran un VERSUS d'Hyper piloté (Ryu A-ISM contre Ryu X-ISM, 8 000 images,
environ 2 min 15 s de jeu) avec chacun des deux cœurs. Il mesure la vitesse et vérifie que les bonnes musiques
démarrent (`0002` sélection, `0181` combat, `0192` vie basse, `0004` fin de match).

```sh
scp -r essai_son root@<IP>:/storage/hsfa_essai_son
ssh root@<IP>
cd /storage/hsfa_essai_son && sh essai_son_hyper.sh
```

- Quitter RetroArch avant, pour que la mesure de vitesse ne soit pas faussée.
- Le script lit les cœurs dans `/storage/cores` et le zip dans `/storage/roms/hsfa` (sinon :
  `sh essai_son_hyper.sh <dossier_coeurs> <dossier_zips>`).
- On attend **plus de 60 images/s** et « musiques : conformes » pour les deux cœurs. Lancer l'essai une fois avec
  le zip ADX, une fois avec le zip Ogg, permet de mesurer le coût du décodage Vorbis.
- `resultats/<cœur>/son.wav` est à écouter sur le PC. Son md5 dépend du zip (version des voix et des musiques) : il
  ne sert qu'à comparer deux essais faits avec le même zip.
- Le programme `joue_arm` n'est pas dans le dépôt (binaire) : il se compile par
  `aarch64-linux-gnu-gcc -O2 -o joue_arm tools/fbneo-hsfa/essais/joue_linux.c -ldl -lm`.

## 8. Réglages conseillés pour le RK3326

Les réglages de ROCKNIX pour la RGB10X conviennent déjà. Les voici, à garder ou à vérifier.

**Dans EmulationStation**, système « Street Fighter Alpha HSFA », Advanced Configuration :

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Aspect ratio (Ratio) | **Core provided** (`core`, valeur par défaut) | le cœur annonce 4:3 ou 16:9 lui-même |
| Run-ahead / Latency reduction | **Off** | le run-ahead fait tourner le jeu deux fois ou plus par image : le Cortex-A35 n'en a pas les moyens |
| Rewind | Off | coûte du temps et de la mémoire |
| Shader | Aucun | le GPU Mali-G31 est juste |
| Integer scale | Off | 224 lignes → 480 donne ×2,14 ; en entier, l'image serait plus petite (×2) avec un cadre |
| Smooth (lissage bilinéaire) | au choix | à ×2,14, Off donne des pixels inégaux et On une image un peu floue |
| CPU governor | **Performance** si ça ralentit | |

**Image 16:9 sur l'écran 4:3** : le cœur 16:9 affiche 448×224 au format 16:9, soit 640×360 sur la RGB10X, avec
des bandes noires en haut et en bas. Laissez le ratio sur **Core provided**. Un ratio 4:3 forcé écraserait l'image
horizontalement.

**Dans RetroArch**, réglages de ROCKNIX à garder :

- vidéo `gl`, en mode « threaded » (vidéo dans un fil séparé), avec vsync ;
- audio `alsathread` à 48 000 Hz, latence 32 ms.

Si le son craque, monter la latence à 64 ms : **Réglages → Audio → Sortie → Latence**. Enregistrez ensuite la
modification avec **Menu rapide → Substitutions → Enregistrer les substitutions du cœur**. Sous ROCKNIX,
`config_save_on_exit` est désactivé : sans cette substitution, la modification est perdue.

**Options du cœur** (Menu rapide → Options du cœur) :

| Option | Valeur | Remarque |
|---|---|---|
| CPU clock | **100 %** | le tirage au sort du jeu dépend du nombre exact de cycles |
| Samplerate | 48000 | même fréquence que la sortie de ROCKNIX : aucun rééchantillonnage en plus |
| Use 32-bits color depth | Enabled (par défaut). En cas de ralentissement : **Disabled** | le mode 16 bits consomme moins de bande passante, avec un rendu à peine différent |
| Frameskip | Disabled. En dernier recours : Auto | |
| PS2 music | All tracks (Hyper), ou au choix | voir §6 |

Les options sont enregistrées dans les dossiers `/storage/.config/retroarch/config/FinalBurn Neo HSFA/` et
`…/FinalBurn Neo HSFA Widescreen/`.

**Mémoire** : Hyper occupe environ 145 Mo une fois chargé (mesure sur PC), ce qui laisse une large marge sur le
1 Go de la RGB10X.

## 9. Commandes, jeu et limites

Les commandes sont celles de FBNeo pour le CPS2 à 6 boutons :

| Manette | Jeu |
|---|---|
| Select | pièce |
| Start | Start |
| Y / X / L | poing faible / moyen / fort |
| B / A / R | pied faible / moyen / fort |

Sur ROCKNIX, Select sert aussi de touche de raccourci, combinée à un autre bouton (Select + Start deux fois pour
quitter). Seul, il met normalement une pièce.

Hyper a ses particularités : persos EX en maintenant Start, modes cachés d'ALPHA3, roulette sur Start, TRAINING qui
peut se figer. Elles sont décrites dans le `LISEZMOI-hyper.md` de la livraison Hyper et ne changent pas sous
ROCKNIX.

**Limite du cœur 16:9 sans le patch « décors widescreen »** : sur certains écrans, les 32 pixels ajoutés de chaque
côté montrent des morceaux de décor incomplets ou une bande claire. On le voit par exemple dans l'introduction
d'Upper. Ce patch n'est pas inclus dans cette version.
