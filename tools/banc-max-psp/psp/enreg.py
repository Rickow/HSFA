"""Enregistrement PSP d'un essai : joue un script d'entrées exprimé en TOURS DE JEU (ticks) sur PPSSPP et relève les deux joueurs à chaque image.

Temps : la PSP affiche 60 images/s mais le jeu tourne à 4 tours pour 3 images (compteur de tours = mot 16 bits en RAM 0x092E51C6, +1, +1, +2, ...) :
une image contient donc 1 ou 2 tours et la sonde de fin d'image ne voit que l'état du DERNIER tour. Les entrées sont lues une fois par image : on
applique à une image l'OU des touches de ses tours (le script en tours est converti en masques par image), et on rend les « tours effectifs » de chaque
image pour que le côté Upper rejoue exactement les mêmes touches tour par tour.
Indice de tour e : e = 1 est le 1er tour qui suit la fin de la phase d'attente (T0)."""
import struct
from psp_debug import masque
import sfa3max as S

ADR_TOURS = 0x092E51C6
BTN = {"1": "square", "2": "triangle", "3": "ltrigger", "4": "cross", "5": "circle", "6": "rtrigger", "S": "start", "U": "up", "D": "down"}
LEAD = 6          # images d'attente avant T0 (J2 immobile, positions posées)


def parse_script(texte):
    """'3:D 3:D+F 3:F+1 2:N' -> [(frozenset(touches), n_tours), ...]"""
    out = []
    for tok in texte.split():
        n, _, k = tok.partition(":")
        ks = frozenset(x for x in k.split("+") if x and x != "N")
        out.append((ks, int(n)))
    return out


def tours_par_tick(script, total):
    """liste K[e-1] (e = 1..total) de frozenset de touches"""
    K = []
    for ks, n in script:
        K += [ks] * n
    K += [frozenset()] * max(0, total - len(K))
    return K[:total]


BTN2 = {"D": 0x04, "U": 0x08, "1": 0x10, "2": 0x20, "3": 0x40, "4": 0x80, "5": 0x100, "6": 0x200}
PC_ENTREE_J2 = 0x08804000 + 0x55650        # entrée de la routine 0x55650 (a0 = joueur) : lit +0x2F0 (mot d'entrée) et le miroite selon le regard (+0xB) ; bits à l'entrée : gauche 1, droite 2 (écran), bas 4, haut 8, LP 10, MP 20, HP 40, LK 80, MK 100, HK 200


def mot_entree(touches, vers_gauche):
    """mot d'entrée écran : F / B résolus d'après le sens de J2 (vers_gauche : J2 regarde vers la gauche de l'écran)"""
    m = 0
    for t in touches:
        if t == "F":
            m |= 0x1 if vers_gauche else 0x2
        elif t == "B":
            m |= 0x2 if vers_gauche else 0x1
        else:
            m |= BTN2.get(t, 0)
    return m


def masque_psp(touches, cote_droit=True):
    bs = []
    for t in touches:
        if t == "F":
            bs.append("right" if cote_droit else "left")
        elif t == "B":
            bs.append("left" if cote_droit else "right")
        else:
            bs.append(BTN[t])
    return masque("+".join(bs)) if bs else 0


def champs(blob):
    x, y = struct.unpack_from("<ii", blob, 0x10)
    return dict(etat=blob[4:8].hex(), x=x / 65536.0, y=y / 65536.0, pas=struct.unpack_from("<I", blob, 0x1C)[0],
                vie=struct.unpack_from("<H", blob, 0x70)[0], cpt=struct.unpack_from("<H", blob, 0x48)[0], blob=blob)


POOLS = [(0x09510F28, 24), (0x09512170, 8), (0x09512770, 32), (0x09513F70, 16), (0x09514B70, 16), (0x09515770, 16)]   # réservoirs d'objets PSP (objets de 0xC0 o ; allocateurs 0x1EE74...0x1EF54)
POOLS_DEB, POOLS_LONG, TAILLE_OBJ = 0x09510F28, 0x09516370 - 0x09510F28, 0xC0


def objets(blob):
    """objets actifs (octet 0 non nul) des 5 réservoirs : liste de dict(cle=(pool, idx), hdr=12 premiers octets en hexa, x, y)"""
    out = []
    for base, n in POOLS:
        for i in range(n):
            o = blob[base - POOLS_DEB + i * TAILLE_OBJ: base - POOLS_DEB + (i + 1) * TAILLE_OBJ]
            if o[0]:
                x, y = struct.unpack_from("<ii", o, 0x10)
                out.append(dict(cle=(base, i), hdr=o[:12].hex(), x=x / 65536.0, y=y / 65536.0))
    return out


def jouer(b, j1, j2, script, total_ticks, x1=544.0, dist=0x40, extra_sondes=(), poser=None, script2=None):
    """Joue `script` (liste (touches, n_tours)) sur `total_ticks` tours après T0. Renvoie (records, info).
    record = dict(img, T, e0, e1 (tours de l'image : e0+1..e1, relatifs à T0), masque, touches, j1, j2, extra)"""
    b.ecrire32(j1 + 0x10, int(x1 * 65536)); b.ecrire32(j2 + 0x10, int((x1 + dist) * 65536))
    b.ecrire16(j1 + 0x70, 0x90); b.ecrire16(j2 + 0x70, 0x90)
    if poser:
        poser(b, j1, j2)
    sondes = [(j1, S.TAILLE_JOUEUR), (j2, S.TAILLE_JOUEUR), (ADR_TOURS, 2), (POOLS_DEB, POOLS_LONG)] + list(extra_sondes)
    inc, T = [], None
    for _ in range(LEAD):
        r = b.images(1, entrees=[0], sondes=sondes)
        t = struct.unpack("<H", r["releves"][0][2])[0]
        if T is not None:
            inc.append((t - T) & 0xFFFF)
        T = t
    T0 = T
    base = dict(j1=champs(r["releves"][0][0]), j2=champs(r["releves"][0][1]))
    obj0 = {o["cle"]: o["hdr"] for o in objets(r["releves"][0][3])}
    droite = True
    K = tours_par_tick(script, total_ticks + 3)
    K2 = tours_par_tick(script2, total_ticks + 3) if script2 else None
    if K2:
        # J2 piloté : point d'arrêt d'exécution (conditionnel, J2 seulement) sur l'écriture du mot d'entrée ; on y force a0 puis on continue
        b.point_arret_exec(PC_ENTREE_J2, condition="a0 == 0x%x" % j2)
    recs, e = [], 0
    pred_faux = 0
    while e < total_ticks:
        # prédiction du nombre de tours de l'image : cycle 1, 1, 2
        d = 1 if (inc[-1] == 2 or (len(inc) > 1 and inc[-2] == 2)) else 2
        touches = K[e]          # touches du 1er tour de l'image (échantillonnage au début de l'image) ; un OU créait des diagonales + bouton parasites
        m = masque_psp(touches, droite)
        hits = 0
        while True:
            r = b.images(1, entrees=[m], sondes=sondes)
            if r["arret"] != "break":
                break
            # J2 : un passage par tour de jeu ; le tour courant est e + hits
            w = mot_entree(K2[min(e + hits, len(K2) - 1)], not droite)
            b.ecrire16(j2 + 0x2F0, w)
            b.ecrire16(j2 + 0x2FC, w)
            hits += 1
            if hits > 8:
                raise RuntimeError("trop d'arrêts J2 dans une image")
        rel = r["releves"][0]
        t = struct.unpack("<H", rel[2])[0]
        dd = (t - T) & 0xFFFF
        if dd != d:
            pred_faux += 1
        T = t
        droite = champs(rel[0])["x"] <= champs(rel[1])["x"]
        inc.append(dd)
        recs.append(dict(img=len(recs) + 1, T=T, e0=e, e1=e + dd, masque=m, touches=touches, j1=champs(rel[0]), j2=champs(rel[1]),
                         objs=[o for o in objets(rel[3]) if obj0.get(o["cle"]) != o["hdr"]], extra=rel[4:]))
        e += dd
    if K2:
        b.retirer_tous_points_arret()
    return recs, dict(T0=T0, pred_faux=pred_faux, base=base)


def tours_effectifs(recs):
    """touches réellement tenues à chaque tour e = 1..N d'après les images (pour rejouer côté Upper) : liste de frozenset."""
    out = []
    for r in recs:
        out += [r["touches"]] * (r["e1"] - r["e0"])
    return out
