# Techniques d'optimisation des images, anciennes et récentes, appliquées aux tuiles CPS-2 (2026-11-10)

Mesures sur la ROM `sfa3` de l'utilisateur (hors dépôt), outils `tools/sondes-recherche/tuiles_cps2*.py`.

| technique | où elle vient | gain mesuré sur *Alpha 3* | perte | sur vraie CPS-2 |
|---|---|---|---|---|
| dédoublonnage exact | toutes les chaînes de conversion (rgbgfx `-u`, SuperFamiconv, rescomp de SGDK) ; Capcom le faisait déjà | référence : 250 442 tuiles uniques | aucune | oui |
| dédoublonnage au miroir | rgbgfx `-m`, SuperFamiconv (par défaut), rescomp (images) | 0,4 % | aucune | oui |
| identité à la palette près | conversions avec cartes d'attributs | < 2,1 % | aucune | oui, mais une palette par tuile |
| découpage libre des images en sprites | « métasprites » NES, découpage de sprites de rescomp (Mega Drive) | 4 à 6 % au plus | aucune | oui, routine de dessin à réécrire |
| rapiéçage (différences entre images) | compression d'animations par différence | non mesuré | aucune | oui, plus d'objets (liste de 1 024) |
| retrait des tuiles jamais affichées | nettoyage des données mortes | inconnu (à journaliser en jeu) | aucune si la couverture est complète | oui |
| fusion des tuiles presque identiques | quantification vectorielle, regroupement de tuiles | voisine à ≤ 1 px : 1,6 % ; ≤ 2 px : 2,9 % ; ≤ 4 px : 5,1 % des tuiles (gain ≈ moitié) | 1 à 4 pixels par tuile | oui |
| dictionnaire de blocs 4×4, LZ4W, ZX0 | Mega Drive (UFTC, SGDK), Neo Geo CD | ≈ 50 % sur Mega Drive | aucune | **non** : demande une mémoire vidéo de tuiles |
| morceaux de 8×8 | NES, Game Boy, SNES | ≈ 32 % | aucune | **non** : objets en 16×16 |
| réduction d'images d'animation | portages PlayStation, Saturn, GBA | au choix | visible | oui |
| retouche par IA (redessin, agrandissement) | outils récents | — | redessin | sans objet ici (écarté par l'auteur) |

Lecture : les techniques sans perte possibles sur la carte, cumulées, restent sous les 9 % qui manquent à Upper,
sauf si le journal des tuiles réellement affichées révèle beaucoup de données mortes (inconnu, peu coûteux à mesurer).
La fusion de tuiles presque identiques (quelques pixels) ajouterait 1 à 3 %, au prix d'écarts minimes mais réels avec
l'arcade, contraire à la règle du projet sauf décision de l'auteur.

Sources : [rgbgfx](https://rgbds.gbdev.io/docs/v0.4.2/rgbgfx.1) ; [SuperFamiconv](https://raw.githubusercontent.com/Optiroc/SuperFamiconv/main/README.md) ;
[rescomp de SGDK](https://stephane-d.github.io/SGDK/md__s_g_d_k_2bin_2rescomp.html) et [ticket sur les sprites](https://www.github.com/Stephane-D/SGDK/issues/68) ;
[métasprites NES](https://nesdev.nes.science/f21/t18539.xhtml) ; [UFTC](https://plutiedev.com/format-uftc) ; [LZ4W](https://gendev.spritesmind.net/forum/viewtopic.php?t=2479).
