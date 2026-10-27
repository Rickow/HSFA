#!/usr/bin/env python3
"""Archive sfa3hsfa.zip du coeur FBNeo HSFA en mode « bases de plans » (decors widescreen injectes) :
reprend paquet_fbneo.py (copie locale) avec : ROM programme corrigee, dossier des blocs externes (ext_*.bin +
ext_liste.txt, dont le bloc de decor), config « plans=300,340,3a0 » et hsfa_gfx.bin = hsfa_plans[_decor].bin en +$1000000.
Usage : paquet_decor.py <roms/sfa3hx> <dossier ext> <hsfa_plans*.bin> <sortie.zip>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
roms, ext, plans, sortie = [os.path.abspath(x) for x in sys.argv[1:5]]
os.environ["HSFA_SORTIE"] = os.path.dirname(sortie)
import paquet_fbneo_copie as P
P.WORK = "/"
nom = os.path.splitext(os.path.basename(sortie))[0]
P.JEUX["decor"] = dict(nom=nom, dossier=ext, roms=roms, banques="<workspace>/work/mame/banques",
                       son=(roms, ["sz3.01", "sz3.02", "sz3.11m", "sz3.12m"]),
                       config={"commun": "254", "ptr_anim": "FF3E48", "gfx_intro": "456", "plans": "300,340,3a0"},
                       gfx=[(plans, 0x1000000)])
P.SORTIE = os.path.dirname(sortie)
P.construit("decor")
