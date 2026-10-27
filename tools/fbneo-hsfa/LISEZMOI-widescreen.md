# SFA3 / SFA3 Upper (HSFA) en 16:9 — cœur « FinalBurn Neo HSFA Widescreen »

Variante du cœur HSFA qui affiche les deux jeux retraduits en **448×224, format 16:9**, au lieu de 384×224 (4:3).
Le décor existe au-delà des 384 px : le cœur l'affiche, sans étirer l'image. Personnages et interface restent au centre
(l'image centrale est identique au pixel près à celle du cœur 4:3).

| Fichier | À quoi il sert |
|---|---|
| `fbneo_hsfa_ws_libretro_android.so` | cœur Android 64 bits (RG477M, Retroid Pocket Nova…) |
| `fbneo_hsfa_ws_libretro.so` | même cœur pour Linux x86_64 (PC) |
| `captures/` | captures de contrôle 448×224 (attraction, combats SFA3 et Upper, planches) |
| `fbneo-hsfa-widescreen.patch` | la modification du code (branche locale `widescreen` du clone) |

## Jeux : les zips habituels, sans rien changer

Le cœur widescreen utilise **les mêmes noms de jeux** que le cœur HSFA : `sfa3hsfa.zip` et `sfa3uhsfa.zip`
(dossier parent, `work/fbneo/`) marchent tels quels. Ne pas les renommer. Une mise à jour des zips sert aux deux cœurs.

## Installation sur la console

1. Copier `fbneo_hsfa_ws_libretro_android.so` sur la console (par exemple dans `Download/`).
2. RetroArch : **Menu principal → Charger un cœur → Installer ou restaurer un cœur** → choisir ce fichier.
   Le cœur apparaît sous le nom **« FinalBurn Neo HSFA Widescreen »**.
3. **Charger un contenu** → `sfa3hsfa.zip` ou `sfa3uhsfa.zip` → choisir **FinalBurn Neo HSFA Widescreen**.

Il cohabite avec le cœur HSFA 4:3 (« FinalBurn Neo HSFA ») et avec le FBNeo officiel : nom de fichier et nom de cœur
différents, donc options et réglages séparés. Pour jouer en 4:3, il suffit de choisir l'autre cœur au lancement.

Si l'image reste en 4:3 ou paraît étirée : **Réglages → Vidéo → Échelle → Rapport d'aspect = « Fourni par le cœur »**
(et vérifier qu'aucune surcharge de configuration ne force le 4:3 pour ce cœur). Commandes et réglages : comme le
cœur HSFA (voir `../LISEZMOI.md`).

## Défauts connus (le jeu est conçu pour le 4:3)

- **Bords vides aux extrémités du décor** : quand la caméra arrive au bout du stage, une bande noire (une partie des
  plans, souvent le haut du décor) peut apparaître sur 32 px du côté du bout. Vu sur des stages de SFA3 (métro,
  jungle de Blanka) ; pas vu sur les stages d'Upper essayés (Mika, usine de Zangief). Au milieu du stage, décor complet.
- **Objets coupés aux bords** : le jeu ne dessine que ce qui est dans la zone 4:3 ; un objet (barrière, effet, nom
  défilant) peut s'arrêter net ou disparaître à 32 px du bord.
- **Écrans hors combat** (histoire, citation de victoire, continue, menus) : composés pour le 4:3, ils ont parfois des
  bandes noires ou incomplètes sur les côtés.
- Les autres jeux CPS1/CPS2 que ce cœur sait lancer restent en 4:3.
