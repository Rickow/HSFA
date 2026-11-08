"""(frame_data_max) Liste des coups des 4 persos MAX et scripts d'entrées, EN TOURS DE JEU (jetons « n:TOUCHES » du banc des coups :
U D F B = haut, bas, avant, arrière ; 1-6 = LP MP HP LK MK HK ; N = rien). Les manips tiennent 4 tours par direction (la PSP lit le pad
une fois par image : 3 tours seraient 2,25 images). Noms et commandes : docs/rapports/recherche/E-COUPS-MAX.md (dépôt).

Un coup = dict(id, perso, nom, cat, ismes, s (script J1), essais, dists, garde_bas, obs)
  cat : normal | proche | saut | commande | lancer | special | super | contre
  essais : w (à vide, J2 à 0xC0), h (au contact, mannequin sans garde), b (en garde, mannequin ALL GUARD / J2 tient arrière dans Upper)
  dists : distances candidates (px entre J1 et J2) pour h et b ; la 1re qui donne un contact sur PSP est imposée aux deux machines."""
B = {"LP": "1", "MP": "2", "HP": "3", "LK": "4", "MK": "5", "HK": "6"}
P3, K3 = ("LP", "MP", "HP"), ("LK", "MK", "HK")
MOT = {   # manip -> jetons avant l'appui (le dernier jeton reçoit le bouton)
    "QCF": ["4:D", "4:D+F", "3:F"], "QCB": ["4:D", "4:D+B", "3:B"], "DP": ["4:F", "4:D", "3:D+F"],
    "HCF": ["4:B", "4:D+B", "4:D", "4:D+F", "3:F"], "HCB": ["4:F", "4:D+F", "4:D", "4:D+B", "3:B"],
    "QCFx2": ["4:D", "4:D+F", "4:F", "4:D", "4:D+F", "3:F"], "QCBx2": ["4:D", "4:D+B", "4:B", "4:D", "4:D+B", "3:B"],
}
LOIN, CONTACT, PRES = 0xC0, [0x50, 0x40, 0x30, 0x60, 0x20], [0x20]
NORMAUX_D = [0x60, 0x50, 0x40, 0x30, 0x20]     # normaux : la plus GRANDE distance qui touche avec la même animation qu'à vide


def manip(m, bouton, apres="2:N"):
    t = list(MOT[m])
    n, k = t[-1].split(":")
    # direction finale tenue 4 tours PUIS le bouton (avec elle) : sans ce palier la PSP sort le spécial au lieu du super (mesuré)
    t[-1] = "4:%s 3:%s+%s" % (k, k, "+".join(B[x] for x in bouton.split("+")))
    return "2:N " + " ".join(t) + " " + apres


def coup(perso, nom, cat, s, essais="whb", dists=None, ismes="AXV", garde_bas=False, obs=None, note=""):
    obs = obs or (250 if cat in ("special", "lancer") else 150)
    return dict(perso=perso, nom=nom, cat=cat, s=s, essais=essais, dists=dists or CONTACT, ismes=ismes, garde_bas=garde_bas, obs=obs, note=note)


def normaux(perso):
    L = []
    for b in ("LP", "MP", "HP", "LK", "MK", "HK"):
        L.append(coup(perso, "debout %s" % b, "normal", "2:N 3:%s 2:N" % B[b], dists=NORMAUX_D))
        L.append(coup(perso, "proche %s" % b, "proche", "2:N 3:%s 2:N" % B[b], essais="hb", dists=PRES))
    for b in ("LP", "MP", "HP", "LK", "MK", "HK"):
        L.append(coup(perso, "accroupi %s" % b, "normal", "6:D 3:D+%s 30:D" % B[b], dists=NORMAUX_D, garde_bas=True))
    for b in ("LP", "MP", "HP", "LK", "MK", "HK"):
        L.append(coup(perso, "saut avant %s" % b, "saut", "3:U+F 9:N 3:%s 2:N" % B[b], essais="wh", dists=[0x70, 0x60, 0x80, 0x50, 0x40]))
    L.append(coup(perso, "prise avant + PP", "lancer", "2:N 1:F 3:F+1+2 2:N", essais="h", dists=PRES, obs=250))
    L.append(coup(perso, "prise avant + KK", "lancer", "2:N 1:F 3:F+4+5 2:N", essais="h", dists=PRES, obs=250))
    return L


def speciaux(perso, nom, m, boutons, **kw):
    return [coup(perso, "%s %s" % (nom, b), kw.pop("cat", "special") if False else kw.get("cat", "special"),
                 manip(m, b), **{k: v for k, v in kw.items() if k != "cat"}) for b in boutons]


def supers(perso, nom, m, groupe, ismes_x=True, suite=False, **kw):
    """A : niveau = force du bouton (LP/LK niv. 1, MP/MK niv. 2, HP/HK niv. 3) ; X : un seul niveau (bouton fort)"""
    bs = P3 if groupe == "P" else K3
    ap = lambda b: ("10:N 3:%s 2:N" % B[b]) if suite else "2:N"      # suite = second appui (Tesshinhou : course puis K)
    L = [coup(perso, "%s niv. %d" % (nom, i + 1), "super", manip(m, b, ap(b)), ismes="A", obs=400, **kw) for i, b in enumerate(bs)]
    if ismes_x:
        L.append(coup(perso, "%s (X)" % nom, "super", manip(m, bs[2], ap(bs[2])), ismes="X", obs=400, **kw))
    return L


def liste(perso):
    p = perso
    L = normaux(p)
    if p == "eagle":
        L += speciaux(p, "Manchester Black", "QCB", P3)
        L += speciaux(p, "Canterbury Blue", "QCF", P3)
        L += speciaux(p, "Oxford Red", "HCF", K3)
        L += speciaux(p, "Liverpool White", "QCB", K3)
        L += speciaux(p, "St. Andrew's Green", "DP", P3)
        L += supers(p, "Manchester Gold", "QCBx2", "P")
        L += supers(p, "Union Jack Platinum", "QCFx2", "P")
    elif p == "maki":
        L.append(coup(p, "Hiji Otoshi (saut, bas + MP)", "saut", "3:U+F 9:N 3:D+2 2:N", essais="wh", dists=[0x70, 0x60, 0x80]))
        L += speciaux(p, "Genko", "QCF", P3)
        for b, n in (("LK", "arrêt"), ("MK", "Kage Sukui"), ("HK", "Kubikari")):
            L.append(coup(p, "Hayagake > %s (%s)" % (n, b), "special", manip("QCF", "MK", "10:N 3:%s 2:N" % B[b]), dists=[0x60, 0x50, 0x70, 0x40, 0x30, 0x80, 0x90]))
        L.append(coup(p, "Reppukyaku (KKK)", "special", "2:N 3:4+5+6 2:N"))
        L += supers(p, "Bushin Gouraiha", "QCFx2", "P")
        L += supers(p, "Tesshinhou", "QCFx2", "K", ismes_x=False, suite=True, dists=[0x50, 0x40, 0x60, 0x30, 0x70, 0x80])
    elif p == "yun":
        L.append(coup(p, "Senpuu Kyaku (avant + MK)", "commande", "2:N 3:F+5 2:N", dists=NORMAUX_D))
        for b in K3:
            L.append(coup(p, "Raigeki Shuu %s (saut, bas-avant + K)" % b, "saut", "3:U+F 9:N 3:D+F+%s 2:N" % B[b], essais="wh", dists=[0x70, 0x60, 0x80]))
        L += speciaux(p, "Tetsuzankou", "DP", P3)
        L += speciaux(p, "Zesshou Hohou", "QCF", P3)
        L += speciaux(p, "Senkyutai", "QCF", K3)
        L += speciaux(p, "Kobokushi", "QCB", P3)
        L.append(coup(p, "Fake Kobokushi (QCB + PP)", "special", manip("QCB", "LP+MP"), essais="w"))
        L.append(coup(p, "Zenpou Tenshin (LK)", "lancer", manip("HCB", "LK"), essais="h", dists=PRES, obs=250))
        L += supers(p, "Sourai Rengeki", "QCFx2", "P")
        L += supers(p, "You Hou", "QCBx2", "P", ismes_x=False)
        for i, b in enumerate(K3):
            L.append(coup(p, "Hiten Souryujin niv. %d (saut)" % (i + 1), "super", "3:U 2:N 4:D 4:D+B 4:B 4:D 4:D+B 3:B+%s 2:N" % B[b], ismes="A",
                          essais="wh", dists=[0x50, 0x40, 0x60], obs=400))
    elif p == "ingrid":
        L.append(coup(p, "Sunbright (avant + MP)", "commande", "2:N 3:F+2 2:N", dists=NORMAUX_D))
        L.append(coup(p, "Easy Step (avant + MK)", "commande", "2:N 3:F+5 2:N", dists=NORMAUX_D))
        L.append(coup(p, "Little Lag (bas-avant + MK)", "commande", "2:N 3:D+F+5 2:N", dists=[0x60, 0x50, 0x40], garde_bas=True))
        L += speciaux(p, "Sun Shot", "QCF", P3, dists=[0x60, 0x80, 0x40, 0xA0])
        L += speciaux(p, "Sun Rise", "QCF", K3)
        L += speciaux(p, "Sun Arch", "DP", K3)
        L += speciaux(p, "Sun Upper (contre)", "QCB", P3, essais="w")
        L += speciaux(p, "Sun Lower (contre)", "QCB", K3, essais="w")
        for b in K3:
            L.append(coup(p, "Sun Dive %s (saut)" % b, "special", "3:U+F 3:N 4:D 4:D+B 3:B+%s 2:N" % B[b], essais="wh", dists=[0x70, 0x60, 0x80]))
        L += supers(p, "Sunburst", "QCFx2", "P", ismes_x=False, dists=[0x60, 0x80, 0x40, 0xA0])
        L += supers(p, "Sunshine", "QCBx2", "K", ismes_x=False)
        L += supers(p, "Sun Delta", "QCBx2", "P", dists=[0x30, 0x20, 0x40])
        L.append(coup(p, "Wrap Around (MP+HK)", "special", "2:N 3:2+6 2:N", ismes="XV", essais="w"))
    for i, c in enumerate(L, 1):
        c["id"] = "%s%02d" % (p[0].upper(), i)
    return L


def pour_ism(perso, ism):
    """A : tout ; X : normaux, spéciaux, supers X ; V : normaux et spéciaux (pas de super en V)"""
    return [c for c in liste(perso) if ism in c["ismes"]]


if __name__ == "__main__":
    import sys
    for p in ("eagle", "maki", "yun", "ingrid"):
        for i in "AXV":
            print(p, i, len(pour_ism(p, i)), sum(len(c["essais"]) for c in pour_ism(p, i)))
