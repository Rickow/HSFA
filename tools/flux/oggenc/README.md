# hsfa_oggenc — Ogg Vorbis portable (mêmes octets sur tous les systèmes)

`hsfa_oggenc` encode la musique d'Upper et d'Hyper (PCM issu des flux ADX de l'ISO) en Ogg Vorbis pour le cœur.
Il remplace ffmpeg depuis `flux_ogg.py` VERSION 3. Un même PCM donne **le même fichier Ogg à l'octet**, que l'on
construise sous Linux (x86_64, ARM), Windows, macOS ou en WebAssembly (future version web). Les zips d'Upper,
d'Upper MAX et d'Hyper ont donc les mêmes empreintes partout.

## Pourquoi un encodeur à nous

libvorbis donne des octets différents selon le compilateur, le processeur et la bibliothèque C. Avec ffmpeg, on avait
les mêmes Ogg seulement sur Linux x86_64 avec gcc et la glibc. Il y a quatre causes :

1. `-ffast-math` (que le configure de libvorbis ajoute) autorise le compilateur à réordonner les calculs et à appeler
   la libmvec de la glibc.
2. Les FMA implicites : gcc fusionne `a*b+c` sur ARM par défaut.
3. Les fonctions mathématiques de la bibliothèque C (glibc, msvcrt / ucrt, libSystem, musl) diffèrent au dernier bit.
   `qsort` range les éléments égaux dans un ordre qui dépend aussi de la bibliothèque.
4. `os.h` de libvorbis arrondit autrement sur x86_64 (SSE2, au pair) qu'ailleurs (`floor(x+.5)`). Il redéfinit aussi
   `rint` sous Windows.

Ce que fait le kit :

- il compile en IEEE strict (`-O2 -fno-fast-math -ffp-contract=off`) ;
- `hsfa_portable.h`, inclus de force, remplace `sin cos exp log pow atan acos floor ceil rint ldexp qsort` par une
  seule implémentation compilée avec le programme : les fonctions fdlibm de **musl 1.1.21** (MIT), sans FMA, et un
  tri fusion stable ;
- il rustine `os.h` (`construit_oggenc.py`, `RUSTINES_OS_H`) : `vorbis_ftoi` générique partout, pas de `rint`
  propre à Windows.

## Fabrication

```
python3 construit_oggenc.py --sources DIR --telecharge [--sortie hsfa_oggenc] [--cc "zig cc -target …" | --wasm WASI_SDK]
python3 construit_oggenc.py --verifie hsfa_oggenc        # signal d'essai : md5 387bd0bdb0b85f2b7fad207e3459c45c
```

Les sources sont officielles et vérifiées par SHA-256 : libogg 1.3.6 et libvorbis 1.3.7 (xiph.org, BSD-3), musl
1.1.21 (musl.libc.org, MIT). Il ne faut que le compilateur C. `flux_ogg.py` compile l'encodeur dans le cache (`gcc`,
ou `$CC`), depuis `HSFA_OGGENC_SOURCES`. On peut aussi lui donner un binaire préconstruit par `HSFA_OGGENC`, comme
le fait le constructeur tout-en-un. Dans tous les cas, `flux_ogg.py` refuse un encodeur dont le signal d'essai
n'a pas l'empreinte de référence.

`hsfa_oggenc --signal x.ogg` encode un signal synthétique calculé en entiers (silence, carrés, scies, bruit,
impulsions, pleine échelle) : il ne contient aucune donnée de jeu.

## Preuves (08/11/2026)

Le signal d'essai a donné le même md5 `387bd0bd…` avec 11 chaînes :
- gcc 15 en -O0, -O2 et -O3 ;
- clang 21 ;
- gcc et clang aarch64 (qemu-aarch64) ;
- mingw-w64 gcc (Windows, wine) ;
- zig 0.17.1 (clang 22) : x86_64-linux-musl, aarch64-linux-musl (qemu) et x86_64-windows (wine) ;
- WebAssembly (wasi-sdk 34, wasmtime 50).

Le témoin compte : le même code compilé pour aarch64 **sans** `-ffp-contract=off` donne `4a915e91…`. Le test
détecte donc les écarts. La CI (`.github/workflows/constructeur.yml`) refait la vérification sur de vrais Windows,
macOS arm64 et Linux aarch64. Sur la vraie musique, les résultats sont dans le journal (§206).
