#!/usr/bin/env python3
"""gen_table_flux.py : table code son -> flux Y_DATA pour le lecteur de flux HSFA (fork MAME sfa3hx, coeur FBNeo HSFA).

Source : la table native des commandes son du module PS2 (0x1200 x 8 octets, exec. 0x5CB300 pour ro9 ; identique
dans ro3/ro5/ro9, cf. agent_hyper_son/SON-HYPER.md §1.2), soit lue dans le module decompresse (--module), soit dans le
CSV deja decode (table_son_ro9.csv de agent_hyper_son, par defaut). On garde les entrees de type 1 (flux ADX de
Y_DATA, fid = (o6&0x7F)<<8 | o4, o5 = volume) dont le fid n'est pas nul.

Drapeaux ecrits :
  q : le Z80 QSound (ROM hybride HSFA_SON, = Z80 de SFA3) joue aussi ce code (0x0001-0x002F) ; en mode 1
      (complement) le code reste au Z80, en mode 2 (musique PS2) il passe au flux ;
  p : demarrage en pause (o6 & 0x80 : le pilote PS2 attend FF06) ;
  x : jamais en flux : 0x0001, musique de l'intro, dont le Z80 donne les reperes $618021 qui cadencent l'intro.

Format de sortie (texte, une ligne par code) : 'CODE(hexa) FID VOLUME DRAPEAUX  # commentaire'.
Usage : gen_table_flux.py [--csv table_son_ro9.csv | --module ro9] [--toc ydata_toc.csv] [-o hsfa_flux_table.txt]
"""
import argparse, csv, os, sys

SON = "<workspace>/work/agent_hyper_son"


def familles(code):
    if code == 0x0001: return "intro"
    if 0x0002 <= code <= 0x002F: return "ZERO 3 (SFA3)"
    if 0x0030 <= code <= 0x0036: return "ZERO 3 persos d'Upper"
    if 0x0041 <= code <= 0x004D: return "ZERO (SFA1)"
    if 0x0051 <= code <= 0x0063: return "ZERO 2 (SFA2)"
    if 0x006C <= code <= 0x007F: return "non envoye par Hyper"
    if 0x0141 <= code <= 0x0169: return "module ro1"
    if 0x0180 <= code <= 0x01FF: return "variantes ZERO 3 / EX"
    if 0x0280 <= code <= 0x02FC: return "ALPHA / module ro6"
    if code >= 0x1100: return "autres modules"
    return "?"


def entrees_csv(chemin):
    for r in csv.DictReader(open(chemin)):
        if r["genre"] != "ADX": continue
        yield int(r["cmd"], 16), int(r["a"]), int(r["b"]), int(r["c"])


def entrees_module(mod):
    sys.path.insert(0, SON)
    import table_son
    d, p, tab, perso, ents, pt = table_son.charger(mod)
    for c, e in enumerate(ents):
        if e[0] & 0x7F == 1:
            yield c, ((e[6] & 0x7F) << 8) | e[4], e[5], e[6] >> 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(SON, "table_son_ro9.csv"))
    ap.add_argument("--module")
    ap.add_argument("--toc", default=os.path.join(SON, "ydata_toc.csv"))
    ap.add_argument("-o", default="hsfa_flux_table.txt")
    a = ap.parse_args()
    toc = {}
    if a.toc and os.path.exists(a.toc):
        for r in csv.DictReader(open(a.toc)):
            if r["duree_s"]:
                toc[int(r["idx"])] = (float(r["duree_s"]), r["boucle"] == "1")
    src = entrees_module(a.module) if a.module else entrees_csv(a.csv)
    lignes, n = [], 0
    for code, fid, vol, var in src:
        if fid == 0: continue
        dr = ""
        if 0x0001 <= code <= 0x002F: dr += "q"
        if var: dr += "p"
        if code == 0x0001: dr += "x"
        info = toc.get(fid)
        com = familles(code) + ("" if not info else " ; %.1f s%s" % (info[0], " boucle" if info[1] else ""))
        lignes.append("%04X %d %d %s  # %s" % (code, fid, vol, dr or "-", com))
        n += 1
    with open(a.o, "w") as f:
        f.write("# HSFA lecteur de flux : code son (hexa) -> entree de Y_DATA.BIN (AFS), volume (0-127+), drapeaux\n")
        f.write("# drapeaux : q = joue aussi par le Z80 QSound ; p = demarre en pause ; x = jamais en flux ; - = aucun\n")
        f.write("# genere par gen_table_flux.py depuis la table native PS2 (exec. 0x5CB300, ro9 = ro5 = ro3)\n")
        f.write("\n".join(lignes) + "\n")
    print("%s : %d codes" % (a.o, n))


if __name__ == "__main__":
    main()
