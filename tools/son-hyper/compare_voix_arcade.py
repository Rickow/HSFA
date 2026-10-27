#!/usr/bin/env python3
"""Voix d'un perso dans Hyper (versions ZERO / ZERO 2 / ALPHA) comparees a l'arcade (SFA1 / SFA2), geste par geste.

La meme suite de gestes (GESTES) est jouee par J1 dans les deux jeux ; J2 garde (arriere tenu). Pour chaque geste, on
releve les voix du cote 1 envoyees par le 68K dans la fenetre du geste (coeur de diagnostic HSFA_QSLOG, voir
mesure_cris_arcade.py) et on les ramene a l'espace de l'arcade :
  Hyper $2000 + c / $3000 + c (rejeu)  -> c ;  $4000 + 8 v + n (cris par version) -> cible de la table du rejeu ;
  $0300-$053F (voix SFA3 gardee)       -> « SFA3:code ».
Ecart = un geste ou les deux jeux ne jouent pas les memes voix.

  compare_voix_arcade.py <joue_linux> <coeur_diag.so> <sfa.zip|sfa2.zip> <sfa3hhsfa.zip> <system> <sortie>
                         --jeu sfa1|sfa2 --grille X,Y --hyper 00.Z [--nom Ryu]
Sortie : <sortie>/<nom>.tsv (geste, voix arcade, voix Hyper, ecart) et les journaux.
"""
import argparse, collections, os, re, subprocess, zipfile

# directions pour J1 tourne vers la droite (port 0) : RetroPad B=0 Y=1 SELECT=2 START=3 HAUT=4 BAS=5 GAUCHE=6 DROITE=7 A=8 X=9 L=10 R=11
LP, MP, HP, LK, MK, HK = 1, 9, 10, 0, 8, 11
H, B, G, D = 4, 5, 6, 7


def seq(*pas):
    """pas : (duree, [boutons]) consecutifs -> liste (debut, fin, bouton) relative"""
    out, t = [], 0
    for duree, bts in pas:
        for b in bts: out.append((t, t + duree, b))
        t += duree
    return out


QCF = lambda p: seq((3, [B]), (3, [B, D]), (2, [D]), (3, [D, p]))
QCB = lambda p: seq((3, [B]), (3, [B, G]), (2, [G]), (3, [G, p]))
DP = lambda p: seq((3, [D]), (3, [B]), (2, [B, D]), (3, [B, D, p]))
GESTES = [
    ("projection HP", seq((4, [D]), (4, [D, HP]))), ("projection HK", seq((4, [D]), (4, [D, HK]))),
    ("HP debout", seq((4, [HP]))), ("HK debout", seq((4, [HK]))), ("MP debout", seq((4, [MP]))),
    ("MK debout", seq((4, [MK]))), ("LP debout", seq((4, [LP]))), ("LK debout", seq((4, [LK]))),
    ("HP accroupi", seq((4, [B]), (4, [B, HP]))), ("HK accroupi", seq((4, [B]), (4, [B, HK]))),
    ("QCF+LP", QCF(LP)), ("QCF+HP", QCF(HP)), ("DP+LP", DP(LP)), ("DP+HP", DP(HP)),
    ("QCB+LK", QCB(LK)), ("QCB+HK", QCB(HK)), ("QCF+LK", QCF(LK)), ("QCF+HK", QCF(HK)),
    ("QCB+LP", QCB(LP)), ("QCB+HP", QCB(HP)), ("saut HP", seq((2, [H]), (20, []), (4, [HP]))),
    ("saut HK", seq((2, [H]), (20, []), (4, [HK]))), ("projection HP 2", seq((4, [D]), (4, [D, HP]))),
    ("charge arriere-avant+HP", seq((60, [G]), (3, [D]), (4, [D, HP]))),
    ("charge arriere-avant+HK", seq((60, [G]), (3, [D]), (4, [D, HK]))),
    ("charge bas-haut+HK", seq((60, [B]), (3, [H]), (4, [H, HK]))),
    ("charge bas-haut+HP", seq((60, [B]), (3, [H]), (4, [H, HP]))),
    ("360+HP", seq((3, [D]), (3, [D, B]), (3, [B]), (3, [B, G]), (3, [G]), (3, [G, H]), (3, [H, HP]))),
    ("DP inverse+HP", seq((3, [G]), (3, [B]), (2, [B, G]), (3, [B, G, HP]))),
    ("DP inverse+HK", seq((3, [G]), (3, [B]), (2, [B, G]), (3, [B, G, HK]))),
    ("HP repete", seq(*[(3, [HP]) if k % 2 == 0 else (3, []) for k in range(12)])),
    ("HK repete", seq(*[(3, [HK]) if k % 2 == 0 else (3, []) for k in range(12)])),
    ("demi-cercle avant+HP", seq((3, [G]), (3, [G, B]), (3, [B]), (3, [B, D]), (3, [D, HP]))),
    ("demi-cercle arriere+HK", seq((3, [D]), (3, [D, B]), (3, [B]), (3, [B, G]), (3, [G, HK]))),
    ("Start", seq((6, [3]))),
]
# super-coups (option --super : jauge remplie par un prelude de coups speciaux avant la sauvegarde de l'etat)
QCF2 = lambda p: seq((3, [B]), (3, [B, D]), (3, [D]), (3, [B]), (3, [B, D]), (2, [D]), (3, [D, p]))
QCB2 = lambda p: seq((3, [B]), (3, [B, G]), (3, [G]), (3, [B]), (3, [B, G]), (2, [G]), (3, [G, p]))
CH2 = lambda p: seq((60, [B, G]), (3, [D]), (3, [G]), (3, [D, p]))
SUPERS = [("super QCFx2+HP", QCF2(HP)), ("super QCFx2+HK", QCF2(HK)), ("super QCBx2+HP", QCB2(HP)),
          ("super QCBx2+HK", QCB2(HK)), ("super QCFx2+LP", QCF2(LP)), ("super QCFx2+LK", QCF2(LK)),
          ("super charge AR,AV,AR,AV+HP", CH2(HP)), ("super charge AR,AV,AR,AV+HK", CH2(HK)),
          ("super charge bas,haut-bas+HK", seq((60, [B, G]), (3, [B, D]), (3, [B, G]), (4, [H, D, HK]))),
          ("super 360x2+HP", seq(*[(3, [x]) for x in (D, B, G, H, D, B, G, H)], (4, [H, HP]))),
          ("super demi-cercle x2+HP", seq((3, [G]), (3, [B]), (3, [D]), (3, [G]), (3, [B]), (3, [D, HP])))]
PRELUDE = 1500                                             # images de coups speciaux avant la sauvegarde (jauge)


def prelude(debut, port=0):
    ev, t, k = [], debut, 0
    while t < debut + PRELUDE - 60:
        s = [QCF(HP), DP(HP), QCB(HK), seq((50, [G]), (3, [D]), (4, [D, HP])), seq((50, [B]), (3, [H]), (4, [H, HK]))][k % 5]
        for a, b, bt in s: ev.append((t + a, t + b, port, bt))
        t += 70 if k % 5 < 3 else 110; k += 1
    ev += [(debut, debut + PRELUDE, 1, D), (debut, debut + PRELUDE, 1, B)]      # J2 garde
    return ev


DUREE, APPROCHE = 180, 40
SANS_APPROCHE = ("QCF", "QCB", "DP", "saut", "charge", "demi", "Start", "super")              # coups speciaux et sauts : depuis la distance de depart


def gestes(liste=None):
    """-> lignes « g debut fin port bouton » : chaque geste repart de l'etat du debut du combat (joue_linux HSFA_GESTES)"""
    ev = []
    for g, (nom, s) in enumerate(liste or GESTES):
        t0 = 0
        if not nom.startswith(SANS_APPROCHE):
            ev.append((g, 0, APPROCHE, 0, D)); t0 = APPROCHE + 10            # marche avant, puis 10 images neutres
        for a, b, bt in s: ev.append((g, t0 + a, t0 + b, 0, bt))
        ev += [(g, 0, DUREE, 1, D), (g, 0, DUREE, 1, B)]                    # J2 garde accroupi
    return ev


def par_geste(log):
    """journal du coeur -> {geste: [commandes]}"""
    out, g = collections.defaultdict(list), None
    for l in open(log, errors="replace"):
        t = l.split()
        if not t: continue
        if t[0] == "GESTE": g = None if t[1] == "FIN" else int(t[1])
        elif "QSCMD" in t[0] and g is not None and len(t) >= 3: out[g].append(int(t[2], 16))
    return out


def commandes(log):
    """journal du coeur -> [(image, commande)]"""
    out = []
    for l in open(log, errors="replace"):
        t = l.split()
        if len(t) >= 3 and "QSCMD" in t[0]: out.append((int(t[1]), int(t[2], 16)))
    return out


def table_rejeu(zip_hyper):
    ref = {}
    for l in zipfile.ZipFile(zip_hyper).read("hsfa_rejeu_table.txt").decode().split("\n"):
        m = re.match(r"(REF|ALIAS) ([0-9A-F]{4}) ([0-9A-F]{4})", l)
        if m: ref[int(m.group(2), 16)] = (m.group(1), int(m.group(3), 16))
    return ref


def voix_arcade(c, jeu):
    if jeu == "sfa1": return 0x160 <= c < 0x1F4
    return 0x180 <= c < 0x1FD or 0x300 <= c < 0x37F or 0xC0 <= c < 0xD4


def voix_hyper(c, ref):
    """-> etiquette ou None (bruitages, cote 2, musique ignores)"""
    if 0x2000 <= c < 0x2200 or 0x3000 <= c < 0x3200 or 0x3300 <= c < 0x3380: return "%04X" % (c & 0xFFF)
    if 0x4000 <= c < 0x4500 and c in ref:
        g, x = ref[c]
        return "%04X" % (x & 0xFFF) if g == "REF" else "SFA3:%04X" % x
    if 0x300 <= c < 0x540: return "SFA3:%04X" % c
    return None


def lance(cmd, env, d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "err.log"), "w") as e:
        subprocess.run(cmd, env=dict(os.environ, **env), cwd=d, stdout=subprocess.DEVNULL, stderr=e, timeout=1800)


def main():
    p = argparse.ArgumentParser()
    for x in ("joue", "coeur", "zip_arcade", "zip_hyper", "sys", "sortie"): p.add_argument(x)
    p.add_argument("--jeu", required=True); p.add_argument("--grille", required=True); p.add_argument("--hyper", required=True)
    p.add_argument("--nom", default="perso")
    p.add_argument("--super", action="store_true", help="super-coups, jauge remplie par un prelude")
    p.add_argument("--start", type=int, default=0, help="Start tapes sur le perso avant validation (variantes de SFZ2 Alpha)")
    p.add_argument("--poke", default="", help="HSFA_POKE de l'arcade (ex. 800-960:FF84A2:02 : Akuma de SFA1, cache)")
    a = p.parse_args()
    LISTE = SUPERS if a.super else GESTES
    gx, gy = (int(v) for v in a.grille.split(","))
    lg = "".join("%d %d %d %d %d\n" % e for e in gestes(LISTE))
    # --- arcade : selection par entrees, combat en gestes
    pre = [(600, 605, 0, 2), (624, 629, 1, 2)] + ([(612, 617, 0, 2), (636, 641, 1, 2)] if a.jeu == "sfa2" else [])
    pre += [(660, 665, 0, 3), (700, 705, 1, 3)]
    f = 760
    for _ in range(gx): pre.append((f, f + 3, 0, D)); f += 12
    for _ in range(gy): pre.append((f, f + 3, 0, B)); f += 12
    pre += [(850 + 20 * k, 853 + 20 * k, 0, 3) for k in range(a.start)]
    pre += [(900, 904, 0, LP), (930, 934, 1, LP), (960, 964, 0, LP), (990, 994, 1, LP)]
    deb_a = 1560 if a.jeu == "sfa1" else 1700
    if a.super: pre += prelude(deb_a); deb_a += PRELUDE
    da = os.path.join(a.sortie, a.nom, "arcade"); os.makedirs(da, exist_ok=True)
    open(os.path.join(da, "e.txt"), "w").write("".join("%d %d %d %d\n" % e for e in pre))
    open(os.path.join(da, "g.txt"), "w").write(lg)
    lance([a.joue, a.coeur, a.zip_arcade, a.sys, str(deb_a + 1), os.devnull, str(deb_a)],
          dict(HSFA_QSLOG="1", HSFA_ENTREES="e.txt", HSFA_GESTES="g.txt", HSFA_GESTES_DEBUT=str(deb_a), HSFA_GESTES_DUREE=str(DUREE),
               HSFA_POKE=a.poke), da)
    # --- Hyper : selection par le pilote, combat en gestes ; depart = musique du combat + 25 images (sonde)
    dh = os.path.join(a.sortie, a.nom, "hyper"); os.makedirs(dh, exist_ok=True)
    env_h = dict(HSFA_QSLOG="1", HSFA_TOURNEE="%s/00.Z3.iA" % a.hyper, HSFA_TOURNEE_PASSIF="1", HSFA_TOURNEE_PV="1",
                 HSFA_TOURNEE_LOG="t.log")
    lance([a.joue, a.coeur, a.zip_hyper, a.sys, "1700", os.devnull], env_h, dh)
    cs = commandes(os.path.join(dh, "err.log"))            # musique du combat : fondu FF07 suivi d'un code de musique
    mus = [cs[i + 1][0] for i in range(len(cs) - 1) if cs[i][0] > 1100 and cs[i][1] == 0xFF07
           and (0x01 <= cs[i + 1][1] < 0x60 or 0x180 <= cs[i + 1][1] < 0x300)]
    deb_h = (mus[0] + 25) if mus else 1340
    eh = []
    if a.super:
        eh = prelude(deb_h); deb_h += PRELUDE
    open(os.path.join(dh, "e.txt"), "w").write("".join("%d %d %d %d\n" % e for e in eh))
    open(os.path.join(dh, "g.txt"), "w").write(lg)
    lance([a.joue, a.coeur, a.zip_hyper, a.sys, str(deb_h + 1), os.devnull],
          dict(env_h, HSFA_ENTREES="e.txt", HSFA_GESTES="g.txt", HSFA_GESTES_DEBUT=str(deb_h), HSFA_GESTES_DUREE=str(DUREE)), dh)
    ref = table_rejeu(a.zip_hyper)
    ca, ch = par_geste(os.path.join(da, "err.log")), par_geste(os.path.join(dh, "err.log"))
    lignes = ["geste\tarcade\thyper\tecart"]
    necart = 0
    for g, (nom, _) in enumerate(LISTE):
        va = ["%04X" % c for c in ca.get(g, []) if voix_arcade(c, a.jeu)]
        vh = [x for x in (voix_hyper(c, ref) for c in ch.get(g, [])) if x]
        e = sorted(set(va)) != sorted(set(vh))
        necart += e
        lignes.append("%s\t%s\t%s\t%s" % (nom, " ".join(va) or "-", " ".join(vh) or "-", "ECART" if e else ""))
    choix = [l for l in open(os.path.join(dh, "t.log")) if l.startswith(("CHOIX J1", "MANCHE 1"))]
    lignes.append("# hyper : depart des gestes %d ; " % deb_h + " | ".join(x.strip() for x in choix))
    open(os.path.join(a.sortie, a.nom + (".super" if a.super else "") + ".tsv"), "w").write("\n".join(lignes) + "\n")
    print("%s (%s %s / Hyper %s) : %d ecart(s) sur %d gestes" % (a.nom, a.jeu, a.grille, a.hyper, necart, len(LISTE)))


if __name__ == "__main__":
    main()
