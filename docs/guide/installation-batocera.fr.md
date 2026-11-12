# Jouer à HSFA sous Batocera (v43)

**English: [installation-batocera.md](installation-batocera.md)**

Ce guide installe les cœurs **FinalBurn Neo HSFA** sous Batocera et y range les cinq jeux HSFA
(`sfa3hsfa`, `sfa3uhsfa`, `sfa3umhsfa`, `sfa3hhsfa`, `sfa3hahsfa`).

> **Essayé sur Batocera 43.1 PC (x86_64)**, image officielle, dans une machine virtuelle : les cinq jeux se lancent
> depuis la liste de jeux de Batocera et vont jusqu'au combat, en 4:3 et en 16:9, avec le son (musiques PS2
> d'Hyper comprises). L'installation survit au redémarrage et se retire proprement.
> Raspberry Pi 4/5 et consoles portables ARM 64 bits : **pas essayé sur une vraie machine** ; seule la compatibilité
> des fichiers a été vérifiée (voir « Machines »).

## 1. En bref

| Votre machine | `uname -m` | Dossier |
|---|---|---|
| PC (Batocera x86_64) | `x86_64` | `x86_64/` |
| Raspberry Pi 3 / 4 / 400 / 5, consoles portables ARM 64 bits (RK3326, H700, RK3566…) | `aarch64` | `aarch64/` |
| Raspberry Pi 0 / 1 / 2, Odroid XU4 (Batocera 32 bits) | `armv6l` / `armv7l` | **aucun** (voir §8) |

Chaque dossier contient deux cœurs :

| Cœur | Fichier | Image |
|---|---|---|
| FinalBurn Neo HSFA (par défaut) | `fbneo_hsfa_libretro.so` | 4:3, comme la borne |
| FinalBurn Neo HSFA Widescreen | `fbneo_hsfaws_libretro.so` | 16:9 (décor élargi) |

**Pourquoi un installeur.** Batocera ne charge un cœur libretro que depuis `/usr/lib/libretro/` (avec son fichier
`.info` dans `/usr/share/libretro/info/`, sinon il refuse de lancer le jeu). Ces dossiers font partie du système, qui
est en lecture seule et reconstruit à chaque démarrage. La doc de Batocera propose deux moyens de le compléter :
- `batocera-save-overlay` : la modification est **effacée à chaque mise à jour** de Batocera ;
- un **service** (Batocera v43 : `/userdata/system/services/<nom>`, qui remplace `custom.sh`) : un petit script
  lancé à chaque démarrage. C'est ce que fait l'installeur : il garde les cœurs sur la partition des données
  (`/userdata/system/hsfa/`) et le service `hsfa` les recopie dans `/usr/lib/libretro/` à chaque démarrage.
  **L'installation survit donc aux redémarrages et aux mises à jour de Batocera.**

## 2. Accéder à la machine (SSH)

1. Sur Batocera, notez l'adresse IP : **Menu (Start) → Réglages réseau**.
2. Depuis le PC : `ssh root@<IP>` (ou `ssh root@batocera`). Mot de passe d'origine de Batocera : `linux`.
   Sous Windows : PowerShell (`ssh` est intégré) ou PuTTY.
3. Vérifiez :
   ```sh
   uname -m                  # x86_64 ou aarch64
   ldd --version | head -1   # Batocera 42 et 43 : glibc 2.40 (il faut 2.27 ou plus)
   ```

## 3. Copier les fichiers

Le plus simple est le partage réseau : dans l'explorateur Windows, `\\BATOCERA\share` (ou `\\<IP>\share`) ; sous
Linux ou macOS, `smb://<IP>/share`, ou `scp`.

- copiez **tout le dossier livré** `hsfa-batocera/` dans `share/` : il devient `/userdata/hsfa-batocera/` ;
- mettez les cinq jeux dans `share/roms/hsfa/` (dossier à créer) : `sfa3hsfa.zip`, `sfa3uhsfa.zip`,
  `sfa3umhsfa.zip`, `sfa3hhsfa.zip`, `sfa3hahsfa.zip`. **Ne les renommez pas** : le nom du zip désigne le pilote du
  cœur. Ne les mettez pas dans `roms/fbneo/` : le FBNeo de Batocera ne connaît pas ces jeux.

Les jeux se fabriquent depuis votre ISO de *Street Fighter Alpha Anthology* (voir le guide de construction du
dépôt). Aucun jeu n'est fourni.

## 4. Installer

En SSH :

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh
batocera-es-swissknife --restart        # relance l'interface
```

Le script :
1. choisit `x86_64/` ou `aarch64/` d'après `uname -m` et vérifie la glibc ;
2. range les deux cœurs et leurs `.info` dans `/userdata/system/hsfa/` ;
3. installe le service `/userdata/system/services/hsfa`, l'active (`batocera-services enable hsfa`) et le lance :
   les cœurs sont aussitôt en place dans `/usr/lib/libretro/` (il est aussi visible dans
   **Menu → Réglages système → Services**) ;
4. pose `/userdata/system/configs/emulationstation/es_systems_hsfa.cfg` : le système « Street Fighter Alpha HSFA »
   (dossier `roms/hsfa`, extensions `.zip .7z`). S'il existait déjà un fichier de ce nom, il en garde une copie
   (`.avant-hsfa`) ;
5. écrit dans `/userdata/system/batocera.conf`, seulement si ces réglages n'y sont pas :
   `hsfa.emulator=libretro`, `hsfa.core=fbneo_hsfa` (cœur par défaut : Batocera ignore le `default="true"` des
   fichiers es_systems) et `hsfa.bezel=none` (pas de décor, voir §5) ;
6. crée `roms/hsfa/` et y met `gamelist.xml` (des noms lisibles) s'il n'y en a pas.

Il ne touche à rien d'autre : ni aux jeux, ni aux sauvegardes, ni aux autres systèmes.

**Sans SSH**, à la main par le partage réseau : les deux `.so` du bon dossier dans `system/hsfa/cores/`, les deux
`.info` dans `system/hsfa/info/`, le fichier `hsfa` dans `system/services/`, `es_systems_hsfa.cfg` dans
`system/configs/emulationstation/` ; ajoutez les trois lignes du point 5 à la fin de `system/batocera.conf`, puis
activez le service dans **Menu → Réglages système → Services** et redémarrez.

> Ne nommez jamais le fichier du système `es_systems_custom.cfg` : sous ce nom, Batocera remplace **toute** sa liste
> de systèmes par ce fichier.

## 5. Jouer

Le système **Street Fighter Alpha HSFA** apparaît dans la liste (logo FinalBurn Neo), avec les cinq jeux.

- **Pièce = Select, Start = Start** (manette configurée par Batocera). Quitter le jeu : Hotkey + Start.
- **SFA3, Upper, Upper MAX** : pièce, Start, puis choix du personnage.
- **Hyper** : le jeu n'a que le mode **Versus** : il faut **deux manettes** (chaque joueur choisit son personnage).
- **Hyper + Arcade** : sur l'écran titre, choisissez le mode avec **gauche / droite** (ARCADE, VERSUS, TRAINING,
  OPTION), puis Start.
- Le son est là, y compris les musiques PS2 d'Hyper, lues dans le zip du jeu.

### 16:9 (cœur Widescreen)

Ajoutez à la fin de `/userdata/system/batocera.conf` (partage : `system/batocera.conf`), une ligne par jeu :

```
hsfa["sfa3hsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3uhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3umhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3hhsfa.zip"].core=fbneo_hsfaws
hsfa["sfa3hahsfa.zip"].core=fbneo_hsfaws
```

ou, pour tous les jeux d'un coup, remplacez `hsfa.core=fbneo_hsfa` par `hsfa.core=fbneo_hsfaws`. Le choix vaut au
prochain lancement, pas besoin de redémarrer. (Le même réglage existe dans les options avancées du jeu de
l'interface, « Émulateur / Cœur » ; c'est la ligne `batocera.conf` ci-dessus qui a été essayée.)

**Le décor (bezel) doit rester sur « aucun »** (`hsfa.bezel=none`, posé par l'installeur) : avec le décor de
Batocera, l'image 16:9 est écrasée dans le cadre 4:3 du décor. Si vous voulez le décor pour les jeux en 4:3
seulement, retirez `hsfa.bezel=none` et ajoutez `hsfa["<jeu>.zip"].bezel=none` pour chaque jeu en 16:9.

## 6. Mises à jour

- **Batocera se met à jour** : rien à refaire (le service et les cœurs sont sur la partition des données).
- **Nouveaux cœurs HSFA** : copiez le nouveau dossier `hsfa-batocera/` et relancez l'installeur (il remplace les
  cœurs et garde vos réglages).

## 7. Désinstaller

```sh
bash /userdata/hsfa-batocera/installer-hsfa-batocera.sh retirer
batocera-es-swissknife --restart
```

Retire le service, les cœurs, `es_systems_hsfa.cfg` (et remet votre ancien fichier s'il y en avait un) et tous les
réglages `hsfa.…` / `hsfa["…"]…` de `batocera.conf` (copie de l'ancien fichier : `batocera.conf.avant-retrait-hsfa`).
Les jeux de `roms/hsfa/` et les sauvegardes restent : supprimez-les à la main si vous le voulez.

## 8. Machines : ce qui a été vérifié

Glibc lue dans les images officielles de Batocera (sans les exécuter) :

| Image officielle | Version | glibc | Cœurs HSFA |
|---|---|---|---|
| x86_64 (PC) | 43.1 | 2.40 | `x86_64/` : **essayé en entier** (machine virtuelle) |
| bcm2711 (Raspberry Pi 4/400) | 43.1 | 2.40 | `aarch64/` (glibc 2.27 demandée) : compatible, pas essayé |
| rk3326 (consoles portables) | 42 | 2.40 | `aarch64/` : compatible, pas essayé |
| odroidxu4 (ARM 32 bits) | 43.1 | 2.40 | **incompatible** : le cœur `armhf` (fait pour le Pi 3 de Recalbox) contient des instructions ARMv8 (`vmaxnm`, `crc32`, `lda`) que l'ARMv7 de l'XU4 n'a pas |
| bcm2835 (Pi 0/1, ARMv6) | 43 | — | incompatible (processeur ARMv6) |

Sous Batocera, le Raspberry Pi 3 utilise l'image 64 bits (`bcm2837`) : dossier `aarch64/`.

**Le cœur Linux x86_64 doit être celui du dossier `hsfa-batocera/x86_64/`**, pas celui du dossier `linux/` des
livraisons antérieures : ce dernier demande la glibc 2.43 et Batocera (2.40) le refuse
(`version 'GLIBC_2.43' not found`).

## 9. En cas de problème

| Symptôme | Que faire |
|---|---|
| Le système HSFA n'apparaît pas | Il faut au moins un jeu dans `roms/hsfa/` ; relancez l'interface ; vérifiez `system/configs/emulationstation/es_systems_hsfa.cfg`. |
| Retour immédiat à la liste au lancement | `batocera-services status hsfa` doit dire « en place » pour les deux cœurs ; sinon `batocera-services start hsfa`. |
| Écran noir / message de cœur manquant | Regardez `/userdata/system/logs/es_launch_stderr.log` (`GLIBC_… not found` = mauvais cœur). |
| Image 16:9 écrasée dans un cadre | Le décor est actif : `hsfa.bezel=none` (§5). |

Fichiers à renvoyer : `es_launch_stdout.log`, `es_launch_stderr.log` (dans `/userdata/system/logs/`), la sortie de
l'installeur, et `uname -m`.

## Sources (documentation officielle de Batocera)

- Systèmes personnalisés : wiki.batocera.org/emulationstation:customize_systems
- Overlay et lecture seule : wiki.batocera.org/modify_the_system_while_it_s_running
- Services (v43, `custom.sh` aboli) : wiki.batocera.org/launch_a_script
- SSH : wiki.batocera.org/access_the_batocera_via_ssh
- Code de Batocera 43.1 (dépôt batocera-linux/batocera.linux, branche `batocera-43.1`) :
  `configgen/generators/libretro/libretroGenerator.py` (chemin des cœurs et `.info` obligatoire),
  `libretroPaths.py`.
