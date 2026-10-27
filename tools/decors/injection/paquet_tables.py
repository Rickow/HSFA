"""Archive sfa3hsfa.zip en mode « tables » (production actuelle de SFA3 : pas de plans=, pas de hsfa_gfx.bin)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
roms, ext, sortie = [os.path.abspath(x) for x in sys.argv[1:4]]
os.environ["HSFA_SORTIE"] = os.path.dirname(sortie)
import paquet_fbneo_copie as P
P.WORK = "/"; P.SORTIE = os.path.dirname(sortie)
P.JEUX["tab"] = dict(nom="sfa3hsfa", dossier=ext, roms=roms, banques="<workspace>/work/mame/banques",
                     son=(roms, ["sz3.01", "sz3.02", "sz3.11m", "sz3.12m"]),
                     config={"commun": "254", "ptr_anim": "FF3E48", "gfx_intro": "456"}, gfx=None)
P.construit("tab")
