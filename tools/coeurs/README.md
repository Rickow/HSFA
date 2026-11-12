# Lot des 12 cœurs FBNeo HSFA

Chaîne de construction et de contrôle des cœurs livrés : Linux, Windows, Android, ROCKNIX, Recalbox armhf / aarch64,
chacun en 4:3 (`hsfa`) et 16:9 (`hsfaws`), plus 2 cœurs x86 de contrôle. Ce sont les drapeaux des lots du 05/11 au 09/11.
Chaîne de patchs : [`patches/fbneo/README.md`](../../patches/fbneo/README.md) ; livraisons : `docs/guide/LIVRAISONS.md`.

| fichier | rôle |
|---|---|
| `construire_tout.sh` | les 14 cœurs, en 3 chaînes parallèles (`nice -n 19`) |
| `build_std.sh linux\|windows\|android\|x86arm` | Linux (`make platform=unix` ; glibc ≤ 2.27 par défaut, voir plus bas), Windows (`tools/windows/build_win.sh`), Android (`tools/android/build_android.sh`, `NDK`), x86 aux drapeaux ARM |
| `build_arm.sh recalbox-armhf\|recalbox-aarch64\|rocknix hsfa\|hsfaws <sortie>` | ARM croisés : `-O3`, `HSFA_NO_FLOAT_STORE=1` (patch 0021c), LTO en une partition, glibc ≤ 2.27 pour Recalbox. Ces drapeaux ont été validés sur Pi 3. Plus récent que `tools/recalbox/build.sh` et `tools/rocknix/build.sh`, gardés comme références de la v0.1. |
| `controle.sh <cœurs> <lot de référence>` | contrôles statiques : architecture, attributs ARM, GLIBC max, NEEDED / DLL, exports `retro_*`, version GIT, options, octet par défaut du Dip A (`dipdef.py`), taille ; chaînes personnelles (`HSFA_MOTIFS_PERSO`) |

```sh
export LOT=<dossier du lot>        # arbres fbneo, fbneo_win, fbneo_and, fbneo_r32, fbneo_r64, fbneo_rk, fbneo_x86 (patchés)
tools/coeurs/construire_tout.sh    # -> $LOT/sortie/{linux,windows,android,rocknix,recalbox/armhf,recalbox/aarch64,x86}
HSFA_MOTIFS_PERSO='<vos motifs>' tools/coeurs/controle.sh $LOT/sortie <lot précédent>
```
Licence des cœurs : `patches/fbneo/LICENSE-FBNeo.txt`, à joindre à toute archive.

**Cœur Linux x86_64 et glibc** (depuis le lot du 11/11) : construit sur Ubuntu 26.04 sans précaution, le cœur exige
la glibc 2.43 : Batocera 43 (glibc 2.40) et la plupart des distributions le refusent. `build_std.sh linux`
(`HSFA_GLIBC_ANCIENNE=1`, défaut) appelle donc [`tools/linux/build_x86_glibc_ancienne.sh`](../linux/README.md) :
mêmes drapeaux du Makefile, versions de symboles anciennes (GLIBC 2.27 au plus, vérifié à la construction ;
GLIBCXX 3.4.21 au plus), mêmes images et même son que sans la recette (lot du 11/11 : 6 jeux × 4:3 / 16:9).
`HSFA_GLIBC_ANCIENNE=0` : construction des lots du 03/11 au 10/11.
