"""Relecture du PSD (psd-tools) : arbre, visibilites, egalite pixel des calques de plans avec les PNG, composite."""
import sys, numpy as np
from psd_tools import PSDImage
from PIL import Image
P = "<workspace>/work/decors_ws/out/decors_sfa3.psd"
D = "<workspace>/work/decors_ws/out/decor0C_temple_cloche/"
p = PSDImage.open(P)
print("PSD %dx%d, %d calques/groupes" % (p.width, p.height, len(list(p.descendants()))))
def dump(g, ind=0):
    for l in reversed(list(g)):
        print("  " * ind + ("[G] " if l.is_group() else "    ") + l.name + ("" if l.visible else "  (masqué)"))
        if l.is_group(): dump(l, ind + 1)
dump(p)
ok = True
for L, key in ((1, "avant-plan"), (2, "fond (scroll2"), (3, "plan médian")):
    lay = [x for x in p.descendants() if not x.is_group() and x.name.startswith(key)][0]
    same = np.array_equal(np.array(lay.topil()), np.array(Image.open(D + "plan_scroll%d.png" % L)))
    ok &= same; print("calque", key, "== plan_scroll%d.png :" % L, same)
c = np.array(p.composite()); Image.fromarray(c).save(D + "apercu_relu_psdtools.png")
m = np.array(Image.open(D + "apercu_psd_fusion.png"))
print("composite psd-tools vs fusion interne : ecart max", int(np.abs(c[:, :, :3].astype(int) - m[:, :, :3]).max()))
print("RELECTURE OK" if ok else "RELECTURE ECHEC")
