# Partitions pour la musique d'Hyper

Outils de [PARTITIONS-HYPER](../../../docs/rapports/PARTITIONS-HYPER.md) (résultats) et de
[PLAN-SON-HYPER](../../../docs/rapports/PLAN-SON-HYPER.md) (plan d'action).

**Aucune donnée de jeu ici.** Les scripts lisent les zips MAME et l'ISO de l'utilisateur ; les images Z80 qu'ils
produisent restent dans son dossier de travail. `resultats/` ne contient que des codes et des durées mesurées.

## Dépendances

- Python 3.8 ou plus récent.
- `pip install z80` pour les deux bancs (`mesure_boucles.py`, `mesure_cps1.py`) : émulateur Z80 en C++, facultatif,
  hors `requirements.txt`.
- `scipy` facultatif (`compare_variantes.py` : affectation un pour un ; sinon plus proche voisin).
- `parcours_v10x.py` importe la grille d'opcodes de `src/hsfa/z80son.py`.

## Chaîne

```bash
cd tools/son-hyper/partitions
python3 image_z80.py ssf2 ~/roms/ssf2.zip /tmp/ssf2_z80.bin           # sfa, sfa2, ssf2, ssf2t, hsf2, ffight, sf2hf
python3 parcours_v10x.py ssf2 /tmp/ssf2_z80.bin                       # contrôle de la grille d'opcodes
python3 mesure_boucles.py ssf2 /tmp/ssf2_z80.bin 01-3f,c1 > resultats/mesures_ssf2.tsv
python3 compare_variantes.py resultats/mesures_ssf2.tsv --sortie resultats/variantes_ssf2.tsv
# CPS-1 (non calibré) :
python3 mesure_cps1.py /tmp/ffight_z80.bin 40-5f > resultats/mesures_ffight.tsv
# Par les packs VGM et l'ISO (sans émulation) :
python3 -I apparie_vgm.py Y_DATA.BIN packs/ --tol 0.4
```

| fichier | rôle |
|---|---|
| `image_z80.py` | image Z80 (disposition MAME) depuis le zip de l'utilisateur |
| `pilote_v10x.py` | table de commandes et en-têtes de morceaux, pilotes v1.04 / v1.05 / v1.06b |
| `parcours_v10x.py` | parcours des pistes (grille v1.71, `05` sur 2 octets) |
| `mesure_boucles.py` | banc Z80 QSound : intro et boucle de chaque morceau (calibré sur ZERO / ZERO 2) |
| `mesure_cps1.py` | banc Z80 CPS-1 (YM2151 + OKI) : période des key-on — **non calibré** ; vraisemblable sur Final Fight (v2.00), **non fiable** sur SF2 Hyper Fighting (v4.25) |
| `compare_variantes.py` | appariement des flux d'Hyper avec les morceaux mesurés |
| `apparie_vgm.py` | appariement flux ADX ↔ VGM par durée de boucle (testé sur fichiers synthétiques seulement) |
| `resultats/` | `mesures_{sfa,sfa2,ssf2,ssf2t,ffight,sf2hf}.tsv` (sf2hf non fiable), `variantes_ssf2.tsv` |
