import rendu_anim as r, numpy as np
from PIL import Image
pal = [(v*17, v*17, v*17, 255) for v in range(16)]
lignes = []
for n in (0, 5):
    imgs = []
    for a, dur, fl, fr in r.pas(n)[:6]:
        t, o, im = r.rendu(fr, pal)
        im[0, :] = im[-1, :] = im[:, 0] = im[:, -1] = (255, 0, 0, 255)
        imgs.append(im)
    lignes.append(np.concatenate(imgs, 1))
Image.fromarray(np.concatenate(lignes, 0)).resize((960*2, 320*2), Image.NEAREST).save('<workspace>/work/agent_explosion/essai_gris.png')
