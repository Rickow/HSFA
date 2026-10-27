#!<workspace>/venv/bin/python3
"""DÉMO DE BOUT EN BOUT, sans fenêtre : Eagle (J1) marche vers Ken puis joue « DP + poing »
(bas, bas-avant, bas-avant + carré) ; relevé de l'état des DEUX joueurs à CHAQUE image
(structure joueur PSP, 0x498 octets chacun), captures d'écran, empreinte RAM finale.

Usage : python3 exemple_eagle.py [--sortie DOSSIER] [--cpu jit|interp|ir] [--etat FICHIER.ppst]
Sorties : <sortie>/releves.tsv (une ligne par image), structures.bin (octets bruts, 2 x 0x498 par image),
          captures/*.png + planche.png, resume.txt (empreintes : relevés, structures, captures, RAM+VRAM)."""
import argparse, hashlib, io, os, struct, sys, time
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from psp_debug import Banc, plan
import sfa3max

ap = argparse.ArgumentParser()
ap.add_argument("--sortie", default=os.path.join(ICI, "demo_eagle"))
ap.add_argument("--cpu", default="jit")
ap.add_argument("--etat", default=os.path.join(ICI, "etats", "combat_eagle_ken.ppst"))
a = ap.parse_args()
os.makedirs(os.path.join(a.sortie, "captures"), exist_ok=True)

# Le coup : 10 images de repos, marche vers Ken (droite) 55 images, repos, puis bas / bas+droite / bas+droite+carré.
SCRIPT = [("-", 10), ("right", 55), ("-", 5), ("right", 3), ("down", 3), ("down+right+square", 3), ("-", 120)]
masques = plan(SCRIPT)
CAPTURES = {64, 72, 80, 88, 96, 104, 112, 124, 150, 190}      # images (depuis 1) après lesquelles on capture

t0 = time.time()
with Banc.lancer(etat=a.etat, cpu=a.cpu) as b:
    j1, j2 = sfa3max.adresses_joueurs(b)
    sondes = [(j1, sfa3max.TAILLE_JOUEUR), (j2, sfa3max.TAILLE_JOUEUR)]
    releves, png, fait = [], {}, 0
    for fin in sorted(CAPTURES) + [len(masques)]:
        if fin <= fait:
            continue
        r = b.images(fin - fait, entrees=masques[fait:], sondes=sondes)
        assert r["arret"] == "frames"
        releves += r["releves"]
        fait = fin
        if fin in CAPTURES:
            png[fin] = b.capture(os.path.join(a.sortie, "captures", "image_%03d.png" % fin))
    ram = b.empreinte_ram()
dt = time.time() - t0

# Relevés lisibles
cols = ["x", "y", "pas", "etat", "compteur", "vie", "mot54"]
with open(os.path.join(a.sortie, "releves.tsv"), "w") as f, open(os.path.join(a.sortie, "structures.bin"), "wb") as g:
    f.write("image\t" + "\t".join("j1_" + c for c in cols) + "\t" + "\t".join("j2_" + c for c in cols) + "\n")
    for i, (s1, s2) in enumerate(releves, 1):
        d1, d2 = sfa3max.decoder(s1), sfa3max.decoder(s2)
        f.write("%d\t" % i + "\t".join(("%08x" % d1[c]) if c == "pas" else str(d1[c]) for c in cols) + "\t"
                + "\t".join(("%08x" % d2[c]) if c == "pas" else str(d2[c]) for c in cols) + "\n")
        g.write(s1 + s2)

# Planche de captures
from PIL import Image
ims = [Image.open(io.BytesIO(png[k])).convert("RGB") for k in sorted(png)]
W, H = ims[0].size
cols_n = 5
sh = Image.new("RGB", (W * cols_n, H * ((len(ims) + cols_n - 1) // cols_n)))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols_n) * W, (i // cols_n) * H))
sh.save(os.path.join(a.sortie, "planche.png"))

h = lambda d: hashlib.md5(d).hexdigest()
with open(os.path.join(a.sortie, "resume.txt"), "w") as f:
    f.write("images %d en %.1f s (%s)\n" % (len(releves), dt, a.cpu))
    f.write("md5 releves.tsv  %s\n" % h(open(os.path.join(a.sortie, "releves.tsv"), "rb").read()))
    f.write("md5 structures   %s\n" % h(open(os.path.join(a.sortie, "structures.bin"), "rb").read()))
    f.write("md5 captures     %s\n" % h(b"".join(png[k] for k in sorted(png))))
    f.write("md5 RAM+VRAM     %s\n" % ram)
print(open(os.path.join(a.sortie, "resume.txt")).read())
