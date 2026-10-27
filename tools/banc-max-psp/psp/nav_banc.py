"""Navigation PSP du banc MAX : de l'écran de sélection de l'ENTRAÎNEMENT (etats/selection_training.ppst) jusqu'au début d'un combat
<perso MAX> (J1, ISM choisi) contre un adversaire natif (J2, ID PSP imposé par écriture de J2+0x152), à la VITESSE voulue.
Écran de sélection : après la 1re validation (état J1 03010000), haut = ISM suivant (A -> X -> V) ; la barre SPEED (état 07010000)
change avec haut (TURBO2 -> TURBO1 -> NORMAL)."""
import os
from psp_debug import plan
import sfa3max as S

ICI = os.path.dirname(os.path.abspath(__file__))
ETAT_SELECTION = os.path.join(ICI, "..", "etats", "selection_training.ppst")
ID_PSP = {"eagle": 0x26, "maki": 0x27, "yun": 0x28, "ingrid": 0x29, "ryu": 0x00, "ken": 0x01, "mika": 0x1A, "r. mika": 0x1A}
CURSEUR = ("eagle", "maki", "yun", "ingrid")     # persos atteints par le curseur ; les autres : ID imposé par écriture (comme tournee.lua)
ISM_HAUT = {"A": 0, "X": 1, "V": 2}      # nombre d'appuis « haut » à l'écran ISM (A -> X -> V)
ISM_OCTET = {"A": 0x00, "X": 0xFF, "V": 0x01}
VITESSE_HAUT = {"turbo2": 0, "turbo1": 1, "normal": 2}


def aller_combat(b, perso="eagle", adversaire="ryu", ism="A", vitesse="normal"):
    """b = Banc chargé sur selection_training.ppst. Séquence mesurée (états J1 : 01010000 curseur, 03010000 ISM, 07 00/01 J2 puis SPEED,
    08010000 STAGE, puis combat). Renvoie (j1, j2) ; la main est rendue ~480 images après le lancement (annonce FIGHT terminée)."""
    pid, aid = ID_PSP[perso], ID_PSP[adversaire]
    j1, j2 = S.adresses_joueurs(b)
    force1 = perso not in CURSEUR
    def pas(t):
        b.ecrire8(j2 + 0x152, aid)
        if force1:
            b.ecrire8(j1 + 0x152, pid)
        b.images(t[1], entrees=plan([t]))
    for tok in [("right", 3), ("-", 12)] + [("down", 3), ("-", 12)] * 5:
        b.images(tok[1], entrees=plan([tok]))
    for _ in range(6 if not force1 else 0):                  # rangée du bas : Eagle, Maki, ?, Yun, Ingrid
        if b.lire8(j1 + 0x152) == pid:
            break
        b.images(15, entrees=plan([("right", 3), ("-", 12)]))
    assert force1 or b.lire8(j1 + 0x152) == pid, "curseur non trouvé"
    for t in [("cross", 3), ("-", 40)]:                      # perso validé -> écran ISM
        pas(t)
    for _ in range(ISM_HAUT[ism]):
        b.images(23, entrees=plan([("up", 3), ("-", 20)]))
    assert b.lire8(j1 + 0x182) == ISM_OCTET[ism], "ISM %02x" % b.lire8(j1 + 0x182)
    for t in [("cross", 3), ("-", 60), ("cross", 3), ("-", 60), ("cross", 3), ("-", 60)]:
        pas(t)                                               # J1 ISM, J2 perso, J2 ISM -> barre SPEED (J1 07010000)
    for _ in range(VITESSE_HAUT[vitesse]):
        b.images(23, entrees=plan([("up", 3), ("-", 20)]))
    for t in [("cross", 3), ("-", 60), ("-", 200), ("cross", 3), ("-", 60), ("-", 300), ("-", 300)]:
        pas(t)                                               # SPEED validé, STAGE, lancement
    assert b.lire8(j1 + 0x152) == pid and b.lire8(j2 + 0x152) == aid
    return j1, j2


def ouvrir(etat=ETAT_SELECTION, essais=4, **kw):
    """Banc.lancer avec nouvelles tentatives (le port tiré au hasard peut être pris par un autre agent entre le tirage et le bind)."""
    from psp_debug import Banc, ErreurBanc
    derniere = None
    # dossier de travail PROPRE AU PROCESSUS (HOME, carte mémoire, journaux) : deux PPSSPP qui partagent le même dossier se bloquent mutuellement
    # (débogueur muet, réponse jamais envoyée : observé à chaque fois que deux bancs tournaient ensemble)
    kw.setdefault("dossier", os.path.join(ICI, "..", "run", "w%d" % os.getpid()))
    for _ in range(essais):
        try:
            return Banc.lancer(etat=etat, attente=40, **kw)
        except ErreurBanc as e:
            derniere = e
    raise derniere
