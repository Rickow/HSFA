# Fork MAME du banc (jeu `sfa3hx`)

Patchs contre MAME **0.285** (tag `mame0285`) : jeu `sfa3hx`, clone de `sfa3ud` (journal §109, §116, §120).
Architecture : [docs/architecture/banc-mame.md](../../docs/architecture/banc-mame.md).

## Patchs, dans l'ordre

| Patch | Contre | Contenu |
|---|---|---|
| `sfa3hx-mame0285.patch` | `mame0285` | le fork de base (ci-dessous) |
| `sfa3hx-flux-mame0285.patch` | `mame0285` | fork de base **+ lecteur de flux ADX** en un seul patch ; remplace le précédent ([FLUX](../../docs/rapports/FLUX.md)) |
| `flux-sur-fork-sfa3hx.patch` | fork de base | le lecteur de flux seul (`cps2.cpp`, `hsfa_flux.h`) |
| `rejeu-sur-fork-flux.patch` | fork avec flux | 2ᵉ QSound et rejeu des sons SFA1/SFA2 d'Hyper ([SON-HYPER-ROM](../../docs/rapports/SON-HYPER-ROM.md) §12) |
| `hsfa_flux_h-pour-mame.diff`, `hsfa_rejeu_h-pour-mame.diff` | en-têtes du fork | mise à niveau des en-têtes partagés avec le cœur FBNeo (changements compatibles, [REJEU-FBNEO](../../docs/rapports/REJEU-FBNEO.md)) ; non compilés dans MAME |

## Le fork de base

- ROM graphique de **128 Mo** : `HSFA_GFX` = fichier de tuiles 16×16 au format interne de MAME, chargé en `$2000000`
  (code de tuile `$40000` et plus) ; code d'objet sur 20 bits : bits 16-17 = bits 13-14 de Y (comme la CPS2),
  bits 18-19 = **bits 10-11 de X** (le bit 15 de Y reste le marqueur de fin de liste).
- **Données externes** `$A00000-$CFFFFF` en ROM : `HSFA_EXT` = dossier des `ext_<adresse>.bin` (remplace `banc_mem.lua`).
- **Bases des plans** scroll1/2/3 : registres `$804200-$804205` (unités de 64 Ko de la région ; 0 = mappage CPS
  d'origine) ; le code brut de la tilemap devient un indice local à partir de la base (éléments de 64 / 128 / 512 o).
- `HSFA_GFX` accepte une liste `fichier[@décalage hexa],…` (défaut `$2000000`).
- Horloge du 68000 : `HSFA_CLOCK` (défaut 0,7375 comme MAME ; plus grand = surcadençage).
- **Son** : région `qsound` de **16 Mo** (sans `HSFA_SON`, les 8 Mo hauts recopient les 8 Mo bas = miroir de la
  région de 8 Mo d'origine, rien ne change). `HSFA_SON=<dossier>` charge la ROM son **hybride** d'Upper (Z80 d'Upper
  + musiques de SFA3, `src/hsfa/gen_hybride.py`) : `hx3.01` + `hx3.02` → `audiocpu` ; `hx3.11m`…`hx3.14m` (mots
  échangés) → `qsound` 0-16 Mo.

## Construire

```bash
git clone --depth 1 --branch mame0285 https://github.com/mamedev/mame.git && cd mame
git apply <depot>/patches/mame-fork/sfa3hx-flux-mame0285.patch      # ou sfa3hx-mame0285.patch sans le flux
git apply <depot>/patches/mame-fork/rejeu-sur-fork-flux.patch        # facultatif : rejeu d'Hyper
make SUBTARGET=cps2f SOURCES=src/mame/capcom/cps2.cpp TOOLS=0 USE_QTDEBUG=0 NO_USE_PORTAUDIO=1 NO_USE_PIPEWIRE=1 -j12
```
Les ROM se cherchent dans `<rompath>/sfa3hx` (lien vers le dossier `sfa3ud` de la traduction).

Vérifié le 2026-10-11 (`git apply --check` sur `mame0285`) : les deux patchs complets s'appliquent, `flux-sur-fork-sfa3hx.patch`
par-dessus `sfa3hx-mame0285.patch`, et `rejeu-sur-fork-flux.patch` par-dessus `sfa3hx-flux-mame0285.patch`.
