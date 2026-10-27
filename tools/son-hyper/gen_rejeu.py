#!<workspace>/venv/bin/python
"""Table du REJEU QSOUND (voie (b) du §12 de SON-HYPER-ROM.md) : les sons de SFA1 et SFA2 rejoues tels que leurs pilotes
Z80 les ont ecrits dans le QSound, sur un 2e QSound du fork (et plus tard du coeur FBNeo) dont la ROM d'echantillons
est lue dans le X_DATA.BIN de l'utilisateur (e222 = SFA1, 4 Mo ; e251 = SFA2, 4 Mo). Aucune donnee d'echantillon
dans la table : seulement les ecritures de registres (temps, registre, valeur), relevees au fork par les balayages
(journaux/bal_<jeu>.txt, une commande toutes les 240 images apres FF00, outils/balayages.sh) et l'initialisation du
pilote (journaux/init_<jeu>.txt, outils/init_qs.lua).

Codes (16 bits, poses par le 68K dans la boite aux lettres ; hors de la table PS2 0x0000-0x11FF et du Z80) :
  $2000 + c : commande c de SFA1 telle quelle (c < $300) ; $2500 + c : « cote 2 » de la commande c (le 68K d'Hyper
              ajoute $500 au code du joueur 2) = commande cote2(c) de SFA1 ;
  $3000 + c : commande c de SFA2 (c < $400) ; $3500 + c : cote2(c) de SFA2.
  cote2 (pilotes v1.05) : page 01 -> 02 (+$100) ; SFA2 $0300-$037F -> +$80 ; ailleurs (pages 00, 02, 03 haute) :
  meme commande (sons communs).
  Les codes de cris par version ($4000 + 8 v + n et leur cote 2 $4500 + ...) sont ajoutes par gen_redirection.py
  (ALIAS vers un code Z80 ou REF vers un code de rejeu).

Format de hsfa_rejeu_table.txt (texte, une directive par ligne, # = commentaire) :
  SOURCE <jeu> <decalage X_DATA hexa> <taille hexa> <banque de base hexa> <crc32 hexa>
      (le fork copie l'entree X_DATA dans sa ROM a partir de la banque de base, et verifie le CRC)
  INIT <jeu> <n>   puis n lignes « reg valeur » (hexa) : ecritures du pilote a la mise sous tension
  STOP <jeu> <n>   puis n lignes « reg valeur » : reponse du pilote a FF00 (tout arreter)
  CODE <code> <jeu> <commande source> <priorite> <n> [T]  puis n lignes « t_us reg valeur » (t_us = microsecondes
      depuis la commande) ; T = trace tronquee a la fenetre du balayage (la reponse STOP des voies du son est ajoutee)
  REF <code> <code cible>     ALIAS <code> <code Z80>
Le fork applique aux registres de banque (voix : reg & 7 = 0, reg < $80 ; ADPCM $CC/$D0/$D4) la banque de base du jeu.
"""
import os, sys, re, struct, zlib, json
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "outils"))
from z80v105 import Z80

XD = "<workspace>/work/xdata/X_DATA.BIN"
MANI = "<workspace>/anthology_extract/manifest.csv"
JEUX = {"sfa1": dict(entree=222, base=0x00, code=0x2000), "sfa2": dict(entree=251, base=0x40, code=0x3000)}
FENETRE = 0.0670          # FF00 est pose 4 images (0,067072 s) avant la commande suivante : rien de la reponse avant
MARGE_TRONQUE = 0.25      # une trace qui ecrit encore dans les 0,25 s avant la fin de la fenetre est dite tronquee


def canal(r):
    """voie (0-15 voix, 16-18 ADPCM) touchee par le registre r, ou -1 (registre global)"""
    if r < 0x80: return (((r >> 3) + 1) & 15) if (r & 7) == 0 else r >> 3
    if 0x80 <= r <= 0x8F: return r - 0x80
    if 0x90 <= r <= 0x92: return 16 + r - 0x90
    if 0xBA <= r <= 0xC9: return r - 0xBA
    if 0xCA <= r <= 0xD5: return 16 + ((r - 0xCA) >> 2)
    if 0xD6 <= r <= 0xD8: return 16 + r - 0xD6
    return -1


def cote2(jeu, c):
    if 0x100 <= c < 0x200: return c + 0x100
    if jeu == "sfa2" and 0x300 <= c < 0x380: return c + 0x80
    return c


def lit_bal(f):
    """-> (stop, {code: [(t, reg, val)]}, tronque) ; t relatif a la commande"""
    blocs, cur, tc, stop = [], None, None, []
    lignes = open(f).read().split("\n")
    evs = []
    for l in lignes:
        t = l.split()
        if not t: continue
        if t[0] == "C": evs.append(("C", float(t[1]), int(t[2], 16)))
        elif t[0] == "Q": evs.append(("Q", float(t[1]), int(t[2], 16), int(t[3], 16)))
        elif t[0] == "FIN": evs.append(("F", 1e9))
    cs = [i for i, e in enumerate(evs) if e[0] == "C"]
    stop = [(e[2], e[3]) for e in evs[:cs[0]] if e[0] == "Q"]
    traces, tronq = {}, {}
    for k, i in enumerate(cs):
        tc, code = evs[i][1], evs[i][2]
        tfin = (evs[cs[k + 1]][1] - FENETRE) if k + 1 < len(cs) else 1e9
        tr = []
        for e in evs[i + 1:(cs[k + 1] if k + 1 < len(cs) else len(evs))]:
            if e[0] == "Q" and e[1] < tfin: tr.append((e[1] - tc, e[2], e[3]))
        if code in traces: continue
        traces[code] = tr
        tronq[code] = bool(tr) and k + 1 < len(cs) and tr[-1][0] > (tfin - tc) - MARGE_TRONQUE
    return stop, traces, tronq


def main():
    out = os.path.join(ICI, "rejeu"); os.makedirs(out, exist_ok=True)
    man = {}
    for l in open(MANI).read().splitlines()[1:]:
        i, off, n, kind, name = l.split(",", 4); man[int(i)] = (int(off), int(n))
    L = ["# hsfa_rejeu_table.txt : rejeu QSound des sons de SFA1 et SFA2 (gen_rejeu.py, SON-HYPER-ROM.md §12)",
         "# aucune donnee d'echantillon ici : la ROM QSound est lue dans le X_DATA.BIN de l'utilisateur",
         "VIDE 0000"]
    bilan = {}
    with open(XD, "rb") as fx:
        for jeu, J in JEUX.items():
            off, n = man[J["entree"]]
            fx.seek(off); data = fx.read(n)
            L.append("SOURCE %s %X %X %02X %08X" % (jeu, off, n, J["base"], zlib.crc32(data) & 0xffffffff))
    for jeu, J in JEUX.items():
        z = Z80(os.path.join(ICI, "src", jeu + "_z80.bin"))
        ini = [l.split() for l in open(os.path.join(ICI, "journaux", "init_%s.txt" % jeu)) if l.startswith("Q ")]
        L.append("INIT %s %d" % (jeu, len(ini)))
        L += ["%02x %04x" % (int(t[2], 16), int(t[3], 16)) for t in ini]
        stop, traces, tronq = lit_bal(os.path.join(ICI, "journaux", "bal_%s.txt" % jeu))
        L.append("STOP %s %d" % (jeu, len(stop)))
        L += ["%02x %04x" % rv for rv in stop]
        stop_par_voie = {}
        for r, v in stop:
            stop_par_voie.setdefault(canal(r), []).append((r, v))
        nb = dict(codes=0, tronques=0, vides=0, lignes=0)
        defini = {}
        for c in sorted(traces):
            m = z.morceau(c)
            if m is None or m["prio"] == 0 or m["prio"] >= 0x80: continue      # musique, commande speciale
            tr = traces[c]
            if not tr: nb["vides"] += 1; continue
            voies = sorted({canal(r) for _, r, _ in tr if canal(r) >= 0})
            corps = ["%d %02x %04x" % (round(t * 1e6), r, v) for t, r, v in tr]
            if tronq[c]:
                tf = round(tr[-1][0] * 1e6) + 1000
                for vo in voies:
                    corps += ["%d %02x %04x" % (tf, r, v) for r, v in stop_par_voie.get(vo, [])]
                nb["tronques"] += 1
            code = J["code"] + c
            L.append("CODE %04X %s %04X %02X %d%s" % (code, jeu, c, m["prio"], len(corps), " T" if tronq[c] else ""))
            L += corps
            defini[c] = code
            nb["codes"] += 1; nb["lignes"] += len(corps)
        # cote 2 : $x500 + c -> cote2(c)
        n2 = 0
        for c in sorted(defini):
            c2 = cote2(jeu, c)
            if c2 in defini:
                L.append("REF %04X %04X" % (J["code"] + 0x500 + c, defini[c2])); n2 += 1
        nb["cote2"] = n2
        bilan[jeu] = nb
    open(os.path.join(out, "hsfa_rejeu_table.txt"), "w").write("\n".join(L) + "\n")
    json.dump(bilan, open(os.path.join(out, "bilan.json"), "w"), indent=1)
    print(bilan, "->", os.path.join(out, "hsfa_rejeu_table.txt"), os.path.getsize(os.path.join(out, "hsfa_rejeu_table.txt")), "o")


if __name__ == "__main__":
    main()
