"""Scénarios SFA3 MAX (PSP) sur la classe Banc : portage image par image de nav_arcade.py, tournee_psp.py et super_bp.py de
work/re/ppsspp/ (session MAX), qui utilisaient des temps réels. Ici tout est en images exactes, donc rejouable à l'identique.

    from psp_debug import Banc ; import scenarios_max as sc
    with Banc.lancer() as b:
        sc.aller_arcade(b, "ingrid")                       # démarrage -> début d'un combat d'Arcade avec Ingrid
        sc.tournee(b, "run/tournee", images=3000, periode=120)   # joue (vie J1 max, CPU à 1), captures périodiques
        sc.points_arret(b, "right:20 down:3", [0x1D4C48])        # relevé de registres aux points d'arrêt
"""
import os
import sfa3max
from psp_debug import masque, plan


def _id(perso):
    return perso if isinstance(perso, int) else sfa3max.ID_PERSO[perso.lower()] if not perso.startswith("0x") else int(perso, 16)


def aller_menu_modes(b):
    """Démarrage à froid -> menu des modes (curseur sur ARCADE). ~2 300 images, déterministe."""
    nav = sfa3max.NAV_SELECTION[:-7] + [("-", 60)]
    b.images(sum(n for _, n in nav), entrees=plan(nav))


def en_combat(b, perso_id=None):
    """Vrai si une partie est en cours : J1 posé au sol (Y = 40), vie 0x90 aux deux joueurs (et ID de J1 si fourni)."""
    j1, j2 = sfa3max.adresses_joueurs(b)
    d1, d2 = sfa3max.decoder(b.lire(j1, 0x153)), sfa3max.decoder(b.lire(j2, 0x153))
    return d1["y"] == 40.0 and d1["x"] > 0 and d1["vie"] == 0x90 and d2["vie"] == 0x90 and (perso_id is None or d1["id"] == perso_id)


def aller_arcade(b, perso, max_images=6000):
    """Menu des modes -> ARCADE -> perso imposé (écriture de J1+0x152 sur l'écran de sélection, comme tournee.lua) -> début du
    premier combat. Renvoie le nombre d'images écoulées. perso : 'eagle'|'maki'|'yun'|'ingrid'|'ken'|'ryu'|ID entier."""
    pid = _id(perso)
    aller_menu_modes(b)
    b.images(123, entrees=plan([("cross", 3), ("-", 120)]))                 # ARCADE -> sélection
    j1, _ = sfa3max.adresses_joueurs(b)
    ecoule = 0
    for k in range(max_images // 60):
        b.ecrire8(j1 + 0x152, pid)
        b.images(60, entrees=plan([("cross", 3), ("-", 57)]))               # valide perso, ISM, vitesse, passe les écrans
        ecoule += 60
        if k > 4 and en_combat(b, pid):
            return ecoule
    raise RuntimeError("combat non atteint")


def aller_entrainement(b, perso, adversaire="ken"):
    """Menu des modes -> ENTRAÎNEMENT -> perso (curseur, comme un joueur) contre Ken -> début du combat. Eagle : ~1500 images."""
    pid = _id(perso)
    aller_menu_modes(b)
    b.images(sum(n for _, n in [("down", 3), ("-", 15), ("down", 3), ("-", 15), ("cross", 3), ("-", 90)]),
             entrees=plan([("down", 3), ("-", 15), ("down", 3), ("-", 15), ("cross", 3), ("-", 90)]))
    j1, _ = sfa3max.adresses_joueurs(b)
    for tok in [("right", 3), ("-", 12)] + [("down", 3), ("-", 12)] * 5:
        b.images(tok[1], entrees=plan([tok]))
    for _ in range(6):                                                      # rangée du bas : Eagle, Maki, ?, Yun, Ingrid
        if b.lire8(j1 + 0x152) == pid:
            break
        b.images(15, entrees=plan([("right", 3), ("-", 12)]))
    assert b.lire8(j1 + 0x152) == pid, "curseur non trouvé"
    nav = [("cross", 3), ("-", 40), ("cross", 3), ("-", 60), ("cross", 3), ("-", 60), ("cross", 3), ("-", 60), ("cross", 3), ("-", 60),
           ("-", 200), ("cross", 3), ("-", 60), ("-", 300), ("-", 300)]
    b.images(sum(n for _, n in nav), entrees=plan(nav))


def tournee(b, dossier, images=3000, periode=120, vie_j1=0x90):
    """Joue (équivalent de tournee_psp.py) : toutes les 8 images, vie de J1 remise au maximum, vie du CPU ramenée à 1 si 1 < vie < 0x8000
    (jamais relevée après un K.O.), croix/carré en alternance ; capture toutes les `periode` images. Renvoie les chemins des captures."""
    os.makedirs(dossier, exist_ok=True)
    j1, j2 = sfa3max.adresses_joueurs(b)
    out, haut = [], False
    for k in range(0, images, 8):
        v = b.lire16(j2 + 0x70)
        if 1 < v < 0x8000:
            b.ecrire16(j2 + 0x70, 1)
        b.ecrire16(j1 + 0x70, vie_j1)
        haut = not haut
        b.images(8, entrees=plan([("cross" if haut else "square", 4), ("-", 4)]))
        if (k // 8) % max(1, periode // 8) == 0:
            f = os.path.join(dossier, "%05d.png" % len(out))
            b.capture(f)
            out.append(f)
    return out


def points_arret(b, sequence, adresses_va, forcages=(), capture=None):
    """Joue `sequence` ('bouton+bouton:n …' ou plan) image par image avec points d'arrêt d'EXÉCUTION sur des adresses du module (VA de code,
    ex. 0x1DC32C -> RAM 0x08804000+VA) ; relève a0-a3, v0, ra à chaque passage. forcages : [(va, 'v0', valeur)] : le registre est forcé
    au passage. Renvoie la liste des relevés {image, pc_va, a0..a3, v0, ra_va}."""
    if isinstance(sequence, str):
        et = []
        for tok in sequence.split():
            bt, _, n = tok.partition(":")
            et.append((bt, int(n or 1)))
        masques = plan(et)
    else:
        masques = list(sequence)
    base = sfa3max.BASE_MODULE
    for va in list(adresses_va) + [f[0] for f in forcages]:
        b.point_arret_exec(base + va)
    force = {base + va: (reg, v) for va, reg, v in forcages}
    rel, k = [], 0
    try:
        while k < len(masques):
            # k = image en cours (ses entrées sont déjà posées). Après un arrêt, images() relance et termine l'image k (comptée pour 1).
            r = b.images(len(masques) - k, entrees=masques[k:])
            if r["arret"] != "break":
                break
            g = b.registres()
            rel.append({"image": k + r["images"], "pc_va": r["pc"] - base, **{x: g[x] for x in ("a0", "a1", "a2", "a3", "v0")},
                        "ra_va": g["ra"] - base})
            if r["pc"] in force:
                reg, v = force[r["pc"]]
                b.definir_registre(reg, v)
                rel[-1]["force"] = (reg, v)
            k += r["images"]
            if len(rel) > 100000:
                raise RuntimeError("trop d'arrêts")
    finally:
        b.retirer_tous_points_arret()
    if capture:
        b.capture(capture)
    return rel
