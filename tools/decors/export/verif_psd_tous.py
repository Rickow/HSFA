"""Relecture du PSD complet (psd-tools) : groupes, calques de plans == PNG de chaque decor (pixel a pixel, alpha compris)."""
import re, json, numpy as np
from psd_tools import PSDImage
from PIL import Image
D = "<workspace>/work/decors_ws/out"
p = PSDImage.open(D + "/decors_sfa3.psd")
R = {r["titre"]: r for r in json.load(open(D + "/decors/recap.json"))}
print("PSD %dx%d, %d groupes de decor, %d elements" % (p.width, p.height, len(list(p)), len(list(p.descendants()))))
ok = True
for g in p:
    r = R[g.name]; CW, CH = r["canevas"]
    nl = sum(1 for _ in g.descendants())
    res = []
    for L in (1, 2, 3):
        lay = [x for x in g.descendants() if not x.is_group() and re.match(r"^(fond|plan médian|avant-plan|plan inactif) \(scroll%d " % L, x.name)][0]
        im = np.zeros((p.height, p.width, 4), np.uint8)
        a = np.array(lay.topil().convert("RGBA"))
        im[lay.top:lay.top + a.shape[0], lay.left:lay.left + a.shape[1]] = a
        ref = np.array(Image.open(D + "/decors/decor%s/plan_scroll%d.png" % (r["id"], L)).convert("RGBA"))
        same = np.array_equal(im[:CH, :CW], ref) and not im[CH:].any() and not im[:, CW:].any()
        ok &= same; res.append("s%d %s" % (L, "=" if same else "DIFFERENT"))
    print("%-60s %3d calques  %s  %s" % (g.name[:60], nl, " ".join(res), "visible" if g.visible else "masque"))
print("RELECTURE OK" if ok else "RELECTURE ECHEC")
