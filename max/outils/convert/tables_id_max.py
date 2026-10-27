"""Valeurs par ID des persos MAX pour les tables « par perso » d'Upper (Q8 / Q9 de work/echanges/MAX.md, 2026-10-25/27).
Méthode : pour une table d'Upper indexée par ID, on cherche dans l'EBOOT la table dont les valeurs NATIVES (ID 0-31)
sont les mêmes (homolog_tables, recherche exacte puis approchée) ; on lit ensuite les ID PSP $26-$29 (Eagle, Maki, Yun,
Ingrid) pour les ID Upper $26, $27, $2D, $2E. Le contrôle réécrit à chaque génération l'accord natif (ID 0-31).
Lecture d'Upper : fichier ro5_usa_prog68k.bin = PS2 − 0x1F0000 ; ces tables sont lues par le code PS2 (lbu / lhu) :
octets TELS QUELS (pas de k ^ 1), mots petit-boutistes.
« sûre » = accord 100 % sur les ID 0-31 ; « probable » = accord partiel (voir la note de la ligne).
Sortie : <racine SFA3MAX_CACHE>/converti/tables_id/tables_id_max.s (commentaires : une ligne par table et par perso).
Usage : python tables_id_max.py"""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
VA, RB = 0x74, 0x1F0000
MAX = [("Eagle", 0x26, 0x26), ("Maki", 0x27, 0x27), ("Yun", 0x2D, 0x28), ("Ingrid", 0x2E, 0x29)]   # (nom, ID Upper, ID PSP)
# (table Upper, taille Upper, valeurs par ID, description, table PSP, taille PSP, signé, sûreté, note)
TABLES = [
    (0x748CA8, 2, 1, "mot, demi-largeur -> $A6", 0x21C19C, 1, False, "sûre", "R9 (97 %)"),
    (0x74C6D0, 1, 1, "octet, index de réglage de jauge", 0x21D3F4, 1, False, "sûre", "R9"),
    (0x74C6F8, 1, 1, "octet, index de réglage de jauge", 0x21D41E, 1, False, "sûre", "R9"),
    (0x617290, 2, 1, "mot, Y des étoiles d'étourdissement", 0x2753DC, 2, True, "sûre", "R9"),
    (0x615AC0, 2, 2, "2 mots dx,dy d'apparition d'effets par propriétaire", 0x220840, 2, True, "sûre", "R9"),
    (0x61AAD0, 2, 2, "2 mots dx,dy -> $12/$16 d'un objet", 0x2156DA, 2, True, "sûre", "R9"),
    (0x615790, 2, 2, "2 mots dx,dy d'un effet ($3D = $45/$46)", 0x220798, 2, True, "sûre", "27/10"),
    (0x6180F0, 2, 1, "mot, décalage X d'un objet attaché (signé selon le sens)", 0x220C80, 2, True, "sûre", "27/10"),
    (0x61A840, 2, 2, "2 mots, long signé selon le sens au début de manche", 0x2154E0, 2, True, "sûre", "27/10"),
    (0x61D9F0, 2, 1, "mot -> $6A", 0x281AC0, 1, False, "sûre", "27/10 ; PSP en octets ; = 2e rangée de 0x620E30"),
    (0x622D10, 2, 2, "2 mots dx,dy selon l'ID ADVERSE", 0x28C318, 1, True, "sûre", "27/10 ; PSP en octets signés"),
    (0x60C680, 1, 1, "octet -> $28F", 0x21E0D0, 1, False, "sûre", "27/10"),
    (0x615CA0, 1, 1, "octet par propriétaire -> routine 0x1337F", 0x220A00, 1, False, "sûre", "27/10"),
    (0x616180, 1, 1, "ID -> ID (natif) de référence pour un objet", 0x2260EC, 1, False, "sûre", "27/10 ; valeur = ID natif"),
    (0x61BD60, 1, 1, "ID -> $176(A5), variante 0-4 de fin / illustration", 0x20B1C4, 1, False, "sûre", "27/10"),
    (0x699458, 1, 1, "octet signé -> table 0x5F6030 x 128 (moteur de coups)", 0x219B88, 1, True, "sûre", "27/10"),
    (0x699480, 1, 1, "octet -> table 0x5F4F30 x 32 (moteur de coups)", 0x219BB2, 1, False, "sûre", "27/10"),
    (0x615570, 2, 2, "2 mots dx,dy d'un objet attaché créé par le perso", 0x220408, 1, True, "probable",
     "27/10 ; PSP en octets ; l'ordre diverge d'Upper dès l'ID $20 : valeurs MAX = défauts PSP"),
    (0x620E30, 2, 1, "mot -> $6A, 1re rangée (rangées de 40 mots ; la 2e = 0x61D9F0)", 0x2947D8, 2, True, "probable",
     "27/10 ; écarts natifs aux ID $20-$24"),
    (0x623E50, 2, 1, "mot selon l'ID ADVERSE, 1re rangée (3 rangées de 40 mots)", 0x262A6C, 2, True, "probable",
     "27/10 ; rangées PSP de 40 aussi : PAS d'entrée PSP pour Yun / Ingrid (0x28/0x29 = rangée suivante)"),
]
CARTE = {0x26: "(276, 886)   (fiche PSP FROM: Britain = Cammy $16)", 0x27: "(373, 910)   (fiche PSP FROM: Japon = Ryu / Sakura / Karin)",
         0x2D: "(352, 894)   (fiche PSP FROM: Hong Kong = Fei-Long / Gen)",
         0x2E: "aucune   (fiche PSP FROM: « ? » (Ingrid sans origine) : natif au choix)"}   # Q8 : positions de la carte


def main():
    E = open(paths.eboot(), "rb").read()
    UP = open(os.path.join(paths.anthology(), "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
    def up(t, e, i):
        a = t - RB + e * i
        return UP[a] if e == 1 else struct.unpack_from("<H", UP, a)[0]
    def psp(o, s, sg, i):
        return struct.unpack_from({1: "bB", 2: "hH"}[s][not sg], E, VA + o + s * i)[0]
    accords = {}
    for t, e, per, _, o, s, sg, _, _ in TABLES:
        m = 1 << (8 * s)
        ok = sum((up(t, e, per * i + k) - psp(o, s, sg, per * i + k)) % m == 0 for i in range(32) for k in range(per))
        accords[t] = "%d/%d" % (ok, 32 * per)
    L = ["; valeurs par id des persos MAX pour les tables d'Upper (Q8 / Q9 de work/echanges/MAX.md) — max/outils/convert/tables_id_max.py",
         "; une ligne par (table Upper, id Upper) : à poser à table + taille × id ; source = table PSP homologue (même suite native ;",
         "; accord = valeurs natives identiques sur les ID 0-31) ; « probable » : voir la note", ""]
    for nom, uid, pid in MAX:
        L.append("; ---- %s (Upper $%02X, PSP $%02X)" % (nom, uid, pid))
        for t, e, per, desc, o, s, sg, surete, note in TABLES:
            if t == 0x623E50 and pid >= 0x28: v = "aucune"
            else:
                v = [psp(o, s, sg, per * pid + k) for k in range(per)]
                v = str(v[0]) if per == 1 else "(%s)" % ", ".join(map(str, v))
            L.append("        ; 0x%06X (%s)[$%02X] = %s   (PSP 0x%06X, accord %s, %s%s)" % (
                t, desc, uid, v, o, accords[t], surete, " ; " + note if surete != "sûre" else ""))
        L.append("        ; 0x616B30 / 0x616B32 (x, y carte)[$%02X] = %s" % (uid, CARTE[uid]))
        L.append("")
    d = os.path.join(paths.CACHE, "converti", "tables_id"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "tables_id_max.s"), "w").write("\n".join(L))
    print("écrit", os.path.join(d, "tables_id_max.s"))
    for t, e, per, desc, o, s, sg, surete, note in TABLES: print("  0x%06X -> PSP 0x%06X : %s (%s)" % (t, o, accords[t], surete))


if __name__ == "__main__":
    main()
