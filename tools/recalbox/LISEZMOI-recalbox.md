# Jouer à HSFA sous Recalbox 10 (Raspberry Pi 3)

Ce guide installe les cœurs **FinalBurn Neo HSFA** sous Recalbox 10.x et y range les cinq jeux HSFA
(`sfa3hsfa`, `sfa3uhsfa`, `sfa3umhsfa`, `sfa3hhsfa`, `sfa3hahsfa`).

> **Essayé par l'utilisateur sur un Raspberry Pi 3B (Recalbox 10, cœur 32 bits `armhf`) : ça marche.** Le lancement
> depuis la liste de jeux de Recalbox ne marche pas encore : ouvrir le menu de RetroArch, charger le cœur (« Load
> Core ») puis le jeu. Hyper + Arcade rame un peu sur Pi 3 (options du cœur : Frameskip « Auto », Samplerate 32000).
> Si quelque chose ne marche pas, la partie « En cas de problème » dit quels fichiers renvoyer.

## 1. En bref

| Votre machine | `uname -m` | Dossier à utiliser |
|---|---|---|
| **Raspberry Pi 3 (B, B+)** ou Pi Zero 2 sous Recalbox 10 | `armv7l` | **`armhf/`** |
| Raspberry Pi 4 / 400 / 5 sous Recalbox 10 | `aarch64` | `aarch64/` |

Chaque dossier contient deux cœurs :

| Cœur | Fichier | Image |
|---|---|---|
| FinalBurn Neo HSFA (par défaut) | `fbneo_hsfa_libretro.so` | 4:3, comme la borne |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfaws_libretro.so` | 16:9 (décor élargi) |

**Pourquoi le cœur ROCKNIX ne marche pas sur le Pi 3.** Recalbox 10 pour Pi 3 est un système **32 bits** :
processeur Cortex-A53 en mode ARM 32 bits, noyau `bcm2709`, glibc 2.39. Le cœur ROCKNIX est en **64 bits**
(aarch64) : un système 32 bits ne peut pas le charger. Les sources sont en fin de guide.

## 2. Vérifier sa machine (SSH)

1. Sur la Recalbox, notez l'adresse IP : **Menu (Start) → Options réseau**.
2. Depuis le PC, ouvrez une session SSH. Utilisateur `root`, mot de passe `recalboxroot` (valeur d'origine) :
   ```sh
   ssh root@<IP>
   ```
   Sous Windows : PowerShell (`ssh` est intégré), ou PuTTY.
3. Tapez :
   ```sh
   uname -m
   ldd --version | head -1        # si « ldd » n'existe pas :  /lib/libc.so.6 | head -1
   ```
   - `armv7l` → dossier `armhf/` ; `aarch64` → dossier `aarch64/`.
   - Les cœurs demandent une **glibc 2.27 ou plus récente** (Recalbox 10 : 2.39). Une glibc plus ancienne veut dire
     que Recalbox n'est pas en version 10 : mettez-le à jour d'abord.

## 3. Copier les fichiers sur la Recalbox

Le plus simple est de passer par le partage réseau : dans l'explorateur Windows, ouvrez `\\RECALBOX\share`
(ou `\\<IP>\share`). Sous Linux ou macOS, utilisez `smb://<IP>/share`, ou `scp` :

- copiez **tout le dossier livré** (armhf, aarch64, `installer-hsfa.sh`, `systemlist.xml`, `gamelist.xml`…) dans
  `share/hsfa-recalbox/`, c'est-à-dire `/recalbox/share/hsfa-recalbox/` sur la Recalbox. La partition « share »
  survit aux mises à jour de Recalbox ;
- mettez les cinq jeux dans `share/roms/hsfa/` (dossier à créer) : `sfa3hsfa.zip`, `sfa3uhsfa.zip`,
  `sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`. **Ne les renommez pas** : le nom du zip désigne le pilote
  du cœur. Ne les mettez pas non plus dans `roms/fbneo/` : le FBNeo de Recalbox ne connaît pas ces jeux.

Les jeux se fabriquent depuis votre ISO de *Street Fighter Alpha Anthology* (voir le guide de construction du
dépôt). Aucun jeu n'est fourni.

## 4. Installer les cœurs

### Méthode A : le script (conseillée)

En SSH :

```sh
bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh
es restart
```

Le script :
1. choisit `armhf` ou `aarch64` d'après `uname -m` et vérifie la glibc ;
2. rend la partition système inscriptible (`mount -o remount,rw /`), copie les deux cœurs dans `/usr/lib/libretro/`
   (droits 644), puis la remet en lecture seule. S'il trouve un ancien cœur HSFA, il le sauvegarde d'abord dans
   `hsfa-recalbox/sauvegarde/` ;
3. installe `systemlist.xml` (le système « Street Fighter Alpha HSFA ») et `roms/hsfa/gamelist.xml` (des noms
   lisibles), **seulement s'ils n'existent pas déjà**. Il ne remplace jamais vos propres fichiers.

### Méthode B : à la main

```sh
mount -o remount,rw /
cp /recalbox/share/hsfa-recalbox/armhf/fbneo_hsfa_libretro.so   /usr/lib/libretro/
cp /recalbox/share/hsfa-recalbox/armhf/fbneo_hsfaws_libretro.so /usr/lib/libretro/
chmod 644 /usr/lib/libretro/fbneo_hsfa*_libretro.so
sync
mount -o remount,ro /
```
(Remplacez `armhf` par `aarch64` sur Pi 4 ou Pi 5.) Ne renommez pas les cœurs : Recalbox charge
`/usr/lib/libretro/<cœur>_libretro.so`, où `<cœur>` est le nom déclaré dans `systemlist.xml`.

Ensuite, déclarez le système :

```sh
mkdir -p /recalbox/share/system/.emulationstation
cp /recalbox/share/hsfa-recalbox/systemlist.xml /recalbox/share/system/.emulationstation/
cp /recalbox/share/hsfa-recalbox/gamelist.xml   /recalbox/share/roms/hsfa/
es restart
```

**Si `/recalbox/share/system/.emulationstation/systemlist.xml` existe déjà** (parce que vous avez déjà ajouté un
système), ne l'écrasez pas : copiez-y seulement le bloc `<system uuid="813874de-…" name="hsfa" …> … </system>`, à
l'intérieur de `<systemList>`.

Les fichiers `.info` ne servent pas à Recalbox, qui ne les lit pas pour lancer un cœur : ils sont là pour
RetroArch sur d'autres machines.

### Pourquoi déclarer un système ?

Recalbox n'accepte, pour un jeu, que les cœurs déclarés dans la liste de son système. Le système « fbneo » de
Recalbox ne connaît que `fbneo`. Le fichier `systemlist.xml` ajoute donc un système **« Street Fighter Alpha
HSFA »** : son dossier est `roms/hsfa/`, son cœur par défaut `fbneo_hsfa` (4:3), et il propose aussi
`fbneo_hsfaws` (16:9). L'interface lit ce fichier utilisateur en plus de la liste d'origine de Recalbox. Le système
n'apparaît que si `roms/hsfa/` contient des jeux.

## 5. Choisir le cœur 4:3 ou 16:9

Par défaut, les cinq jeux s'ouvrent avec **`fbneo_hsfa` (4:3)**. Pour le 16:9, quatre possibilités, de la plus
générale à la plus précise. Recalbox les applique dans cet ordre, et la dernière trouvée l'emporte :

1. **Tout le système**, dans `/recalbox/share/system/recalbox.conf` (ou par le menu de l'interface :
   *Paramètres avancés → Configuration avancée de l'émulateur → Street Fighter Alpha HSFA*) :
   ```ini
   hsfa.emulator=libretro
   hsfa.core=fbneo_hsfaws
   ```
2. **Un jeu, par le menu** : sur le jeu, menu *Modifier le jeu → Émulateur / Cœur → libretro / fbneo_hsfaws*.
3. **Un dossier entier** : un fichier `.recalbox.conf` placé dans le dossier, par exemple
   `roms/hsfa/16-9/.recalbox.conf` (et les jeux 16:9 dans `roms/hsfa/16-9/`, sans les renommer) :
   ```ini
   global.emulator=libretro
   global.core=fbneo_hsfaws
   ```
4. **Un seul jeu, par fichier** : à côté du zip, un fichier au nom du zip suivi de `.recalbox.conf`, par exemple
   `roms/hsfa/sfa3hhsfa.zip.recalbox.conf` :
   ```ini
   hsfa.emulator=libretro
   hsfa.core=fbneo_hsfaws
   ```

Indiquez toujours **les deux clés** (`emulator` et `core`). Un nom de cœur absent de `systemlist.xml` est ignoré.

## 6. Musiques du disque PS2

Les archives de jeu récentes contiennent les musiques. Sinon, le cœur les cherche dans le dossier « système » de
RetroArch, sous `fbneo/hsfa/`. Sur Recalbox, c'est `/recalbox/share/bios/fbneo/hsfa/` (partage :
`share/bios/fbneo/hsfa/`) : `hsfa_flux_table.txt` + `Y_DATA.BIN` (ou `anthology.iso`, ou `ydata.txt`).

## 7. Mises à jour de Recalbox et retour en arrière

**Ce qui est perdu à chaque mise à jour.** Sous Recalbox, `/` (dont `/usr/lib/libretro/`) est une image en lecture
seule, recouverte d'une couche modifiable : la partition « OVERLAY ». Vos ajouts y sont rangés et survivent aux
redémarrages. Mais une mise à jour vide cette couche (elle la déplace dans `/overlay/upper.old`). **Les deux cœurs
disparaissent donc de `/usr/lib/libretro/`.** Recalbox vide aussi cette couche après plusieurs démarrages ratés
d'affilée.

**Ce qui reste.** Tout `/recalbox/share` : jeux, `systemlist.xml`, `recalbox.conf`, fichiers `.recalbox.conf`,
sauvegardes, musiques, et le dossier `hsfa-recalbox/`.

**Après une mise à jour**, relancez simplement :
```sh
bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh && es restart
```
Si une version de Recalbox 10.x changeait de glibc ou passait le Pi 3 en 64 bits, refaites la vérification du §2.

**Revenir en arrière** :
- à l'ancien cœur HSFA : le script garde la version précédente dans
  `/recalbox/share/hsfa-recalbox/sauvegarde/*.precedent`. Rendez `/` inscriptible, recopiez-la dans
  `/usr/lib/libretro/` en retirant `.precedent`, puis remettez `/` en lecture seule (méthode B). Juste après une
  mise à jour, les cœurs d'avant se trouvent aussi dans `/overlay/upper.old/usr/lib/libretro/`, jusqu'à la mise à
  jour suivante ;
- **tout retirer** : `bash /recalbox/share/hsfa-recalbox/installer-hsfa.sh retirer`, puis retirez le bloc `hsfa`
  de `systemlist.xml` (ou supprimez ce fichier s'il ne contient que lui) et `es restart`. Le FBNeo de Recalbox
  n'a jamais été touché : il n'y a rien à restaurer de ce côté.

## 8. En cas de problème

- **Le système n'apparaît pas** : vérifiez que `roms/hsfa/` contient les zips et que `systemlist.xml` est au bon
  endroit (`/recalbox/share/system/.emulationstation/`), puis `es restart`.
- **Le jeu revient aussitôt au menu** : envoyez ces trois éléments :
  ```sh
  uname -m; ldd --version | head -1
  ls -l /usr/lib/libretro/fbneo_hsfa*
  tail -50 /recalbox/share/system/logs/es_launch_stderr.log
  ```
  ainsi que `es_launch_stdout.log`, dans le même dossier.
- **Lenteurs sur Pi 3** : le cœur HSFA émule le 68000 en C (Musashi), pas avec Cyclone, le moteur en assembleur
  ARM du FBNeo de Recalbox. Il décode aussi les musiques Ogg et fait tourner un second QSound. Le Pi 3 n'a pas
  encore été mesuré. Si l'image ou le son saccadent, essayez d'abord le cœur 4:3, puis signalez-le : une version
  avec Cyclone pourra être étudiée.

## Sources

- Configuration Pi 3 de Recalbox 10.1.1 (`BR2_arm`, `BR2_cortex_a53`, noyau `bcm2709`, glibc de buildroot, mot de
  passe `recalboxroot`) :
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/configs/recalbox-rpi3_defconfig>. Les configurations Pi 4 et
  Pi 5 sont en `_64` (aarch64).
- Buildroot utilisé par Recalbox 10.0 à 10.1.1 : sous-module `buildroot` au commit `e4a5ab3b` (« Update for
  2024.05.3 »), qui fournit la glibc `2.39-74` :
  <https://gitlab.com/buildroot.org/buildroot/-/blob/e4a5ab3b319753f41e2b5cf22e90b6b0304ca225/package/glibc/glibc.mk>.
- Les cœurs vont dans `/usr/lib/libretro/<cœur>_libretro.so` (paquet FBNeo, configgen) :
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/package/libretro-fbneo/libretro-fbneo.mk>,
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/projects/configgen/configgen/recalboxFiles.py>.
- Liste des systèmes (fichier d'origine `/recalbox/share_init/…/systemlist.xml` et fichier utilisateur
  `/recalbox/share/system/.emulationstation/systemlist.xml`), et cœur accepté seulement s'il est déclaré dans le
  système :
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/projects/frontend/es-app/src/systems/SystemDeserializer.h>,
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/projects/frontend/es-app/src/emulators/EmulatorManager.cpp>.
- Surcharges `.recalbox.conf` par dossier et par jeu :
  <https://wiki.recalbox.com/fr/advanced-usage/configuration-override>.
- Partition système en écriture et commandes SSH :
  <https://wiki.recalbox.com/fr/tutorials/system/access/remount-partition-with-write-access>,
  <https://wiki.recalbox.com/fr/tutorials/system/access/folders-and-ssh-commands>.
- Couche OVERLAY vidée à la mise à jour (`do_clean_overlay`) :
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/package/recalbox-initramfs/init>.
- Dossier système de RetroArch (`/recalbox/share/bios/`) et journaux de lancement :
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/board/recalbox/fsoverlay/recalbox/share_init/system/configs/retroarch/retroarchcustom.cfg.origin>,
  <https://gitlab.com/recalbox/recalbox/-/blob/10.1.1/projects/frontend/es-app/src/emulators/run/GameRunner.cpp>.
