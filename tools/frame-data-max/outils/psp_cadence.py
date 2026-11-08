#!<workspace>/venv/bin/python3
"""(frame_data_max) psp_cadence.py <perso> <ism> <id essai>... : CONTRÔLE des ralentissements côté PSP (lecture seule des caches).
Rejoue sur PSP les essais demandés (script effectif, distance et mannequin du cache psp_cache/<perso>_<ism>.json) et relève, image par
image, le nombre de tours de jeu joués (compteur 0x092E51C6). Cadence normale : 4 tours pour 3 images (motif 1,1,2). Une image à 0 tour
serait un ralentissement PSP. Vérifie aussi que le relevé tour par tour (point d'arrêt 0x55650) n'a pas de trou dans le compteur, et
qu'il redonne la trace du cache. À lancer par lance_emu (une place) : lance_emu --generique --agent frame_data -- psp_cadence.py …"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import fd, psp_fd as P

perso, ism, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
res = json.load(open(os.path.join(fd.ICI, "psp_cache", "%s_%s.json" % (perso, ism))))
b = P.ouvrir()
try:
    etats = {g: P.etat_combat(b, perso, "ryu", ism, g) for g in ("ng", "ag")}
    for tid in ids:
        r = res[tid]
        b.etat_charger(etats[r["garde"]]); b.pause()
        j1, j2 = P.S.adresses_joueurs(b)
        s = fd.parse(r["script"])
        tours, images = P.jouer(b, j1, j2, s, len(r["tr"]) + 4, dist=r["dist"], arret=0)
        dd = [im["e1"] - im["e0"] for im in images]
        T = [t["T"] for t in tours]
        trous = sum(1 for a, c in zip(T, T[1:]) if (c - a) & 0xFFFF != 1)
        meme = sum(1 for a, c in zip(fd.compact_psp(tours), r["tr"]) if a == c)
        print("%s %s %s : %d images, tours par image %s, images à 0 tour %d ; relevé %d tours, trous du compteur %d ; "
              "identique au cache %d / %d" % (perso, ism, tid, len(dd), dict(collections.Counter(dd)), dd.count(0), len(T), trous, meme,
                                               min(len(r["tr"]), len(tours))), flush=True)
finally:
    b.arreter()
