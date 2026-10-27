"""Palettes d'Ingrid (pl29) au schéma d'Upper : 6 groupes de 5 (2026-10-11, question 7 de l'agent d'intégration HSFA).
Upper copie 5 palettes par joueur : groupe = ((isme + 1) × 2 + $129) × 5 (notes max-palettes.md §2). Ingrid a 48 palettes
= 6 groupes de 8 (période 8 mesurée : palettes g·8 + k semblables d'un groupe à l'autre ; aucune ressemblance à la
période 5). Dans chaque groupe : 0-3 = palettes des sprites (attributs des frames d'Ingrid : sous-palettes 0, 1, 3, et 2
pour 56 objets ; jamais au-delà de 3) ; 4-7 = teintes bleues (claire : 4/5, foncée : 6/7) de 0 et 1, qu'aucune frame
n'emploie (effet de silhouette probable, à voir en jeu). On garde 0-4 de chaque groupe (la 4 remplit la 5e place).
Entrée : ~/.cache/sfa3max/converti/pl29/palettes_module.bin et palettes_cps2.bin (palettes_max.py) ;
sortie : palettes_module_upper.bin (30 palettes, mot 15 = n° 0-29) et palettes_cps2_upper.bin, même dossier."""
import os, struct
D = os.path.expanduser("~/.cache/sfa3max/converti/pl29")
GARDEES = [8 * g + k for g in range(6) for k in range(5)]
for nom, numero in (("palettes_module", True), ("palettes_cps2", False)):
    b = open(os.path.join(D, nom + ".bin"), "rb").read()
    assert len(b) == 48 * 32, "%s : %d palettes, 48 attendues" % (nom, len(b) // 32)
    out = bytearray()
    for n, i in enumerate(GARDEES):
        p = list(struct.unpack_from("<16H", b, 32 * i))
        if numero: p[15] = n                             # mot 15 = n° de la palette dans le perso (format module)
        out += struct.pack("<16H", *p)
    open(os.path.join(D, nom + "_upper.bin"), "wb").write(out)
    print(nom + "_upper.bin :", len(out) // 32, "palettes (anciens n° %s)" % GARDEES)
