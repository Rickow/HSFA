#!/usr/bin/env python3
"""tables_tsv.py : ecrit tables_par_decor.tsv (tables et routines par decor, Upper -> Hyper) et
correctifs_sfa2_hyper.tsv (58 correctifs de l'import SFA2 sur SFA3 -> sites d'Hyper / code d'Upper a greffer).
Donnees relevees par sites_a5.py, lecteurs.py, consts.py, gestionnaires.py, sites_injection.py ; adresses arcade
d'Upper : mediane de va_arcade.pkl (etude_upper_hyper)."""
import os, pickle
H = os.path.dirname(os.path.abspath(__file__))
VA = pickle.load(open("<workspace>/work/etude_upper_hyper/va_arcade.pkl", "rb"))
def arc(r):
    v = VA.get(r); return ("$%X" % v[2]) if v else "-"
T = [  # role, routines Upper, table Upper, n, routines Hyper, table Hyper, n, etat
 ("palettes scroll1", [0x4ABB0, 0x4BAD0], "0x70E560", 40, "0x60570, 0x61180", "A 0x660240 ($100+$C178)", 16, "present, 4 decors x 4 variantes"),
 ("palettes scroll2", [0x4AC50, 0x4BB70], "0x7147E0", 40, "0x61240", "B 0x661E60 ($100+$C178)", 16, "present (1 site)"),
 ("palettes scroll3", [0x4ACF0, 0x4BC10], "0x71D420", 40, "0x61300", "C 0x664280 ($100+$C178)", 16, "present (1 site)"),
 ("palettes sprites de decor ($90C1E0)", [0x4AA60, 0x4B930], "0x707D10", 40, "-", "-", 0, "absent"),
 ("type s1 + listes s1", [0x14F510], "0x747EE0 / 0x747F30", 40, "0x313A80", "0x695FF0 / 0x695FF8", 4, "present"),
 ("listes s2", [0x151270], "0x7480D4", 40, "0x3157E0", "0x696010", 4, "present"),
 ("listes s3", [0x151750], "0x748344", 40, "0x315C40", "0x696048", 4, "present"),
 ("bibliotheques s1 / super-tuiles / s2 / s3", [0x14FBA0], "0x69B830 (119) / 0x69F3B0 (3081) / 0x6CF5F0 (170) / 0x6EF3F0", 0, "0x314110...", "0x63DA20 (6) / 0x63DD20 (177) / 0x640960 (17) / 0x643C60", 0, "blocs d'Upper absents"),
 ("ordre de mise a jour des plans", [0x151B80], "T_6147B0 (2 cibles)", 40, "0x30EC10", "T_5C50D0", 4, "present"),
 ("gestionnaire scroll1", [0x151EA0], "T_614850 (16 cibles)", 40, "0x30EF00", "T_5C50E0 (3 cibles)", 4, "present ; gestionnaires d'Upper sans copie exacte"),
 ("gestionnaire scroll2", [0x155920], "T_6149B0 (2 cibles)", 40, "0x30FEE0", "T_5C5100", 4, "present"),
 ("gestionnaire scroll3", [0x157300], "T_614AD0 (14 cibles)", 40, "0x311550", "T_5C5180", 4, "present ; idem s1"),
 ("init X/Y des plans", [0x154280, 0x1586C0], "T_614600 / T_6146A0", 40, "0x30F240, 0x311AB0", "T_5C50B0 / T_5C50C0", 4, "present"),
 ("controle CPS-B", [0x15ACB0], "T_614CD0", 40, "0x313960", "T_5C51F0", 4, "present"),
 ("effet par decor + $C174/$C176", [0x13BB10], "T_6135A0 (9 cibles) + T_6134E0 / T_613530", 40, "0x391E50", "T_5C9E30 (2 cibles) + T_5C9E00 / T_5C9E08", 4, "present"),
 ("anneau scroll1 (widescreen)", [0x14FF50], "T_6145F0", 4, "0x3144C0", "T_5C5230", 4, "identique"),
 ("bornes $40/$44", [0x14F9B0, 0x151560, 0x1519B0], "constantes", 0, "0x313F20, 0x315A50, 0x315EA0", "constantes", 0, "identique, rien a faire"),
 ("init joueurs", [0x247D80, 0x247DB0, 0x247E40], "constantes", 0, "0x2C75E0, 0x2C7610, 0x2C76A0", "constantes", 0, "identique, rien a faire"),
 ("couleur de ROUND", [0xF29A0, 0xF2A30], "T_6112D0 + 0x73E330 / 0x73E630", 40, "0x37BDC0, 0x37BE50", "T_5C87D0 + 0x690800 / 0x690B00", 40, "present, 40 entrees identiques"),
 ("animation de palettes (D3 = $100)", [0xC8890, 0x1E4530], "donnees via objet", 0, "0x38D510", "idem", 0, "lecteur identique"),
 ("objets de decor", [0x4C1B0], "T_950CE0", 40, "-", "-", 0, "absent"),
 ("objet par decor", [0x105C70], "0x740B70", 40, "-", "-", 0, "absent"),
 ("animations des objets de decor", [0xFDC10], "0x971E70", 40, "-", "-", 0, "absent"),
 ("positions par decor ($172), masque $C0A00400", [0x196F50, 0x198A00], "-", 0, "-", "-", 0, "absent"),
 ("animations par decor ($100 x 4)", [0x199530, 0x199DA0], "-", 0, "-", "-", 0, "absent"),
 ("masque $3F60BDB3", [0x371920], "-", 0, "0x244C10 (modifiee, sans $100)", "-", 0, "absent"),
 ("musique par decor (VERSUS), cas $14/$04", [0x139AD0], "T_613380 / T_613350", 40, "-", "-", 0, "absent"),
 ("defilement du decor dans les scenes Arcade", [0x2CAC0], "T_60B400", 40, "-", "-", 0, "absent (avec les scenes)"),
 ("choix du decor Arcade", [0x24F020], "T_61BE10 (perso -> decor, 40)", 40, "0xA49E0", "T_5B6220 (id etendu -> 0/1/2, 128)", 128, "apparentee 52 %"),
 ("decor du rival", [0x24F020], "T_61B6D0", 40, "0xA49E0", "T_5B6030", 40, "identique"),
 ("defi intercale ($2A / $14)", [0x2489E0], "T_61B680", 40, "-", "-", 0, "absent"),
 ("init de match ($100 = $174)", [0x2615D0], "-", 0, "0x96690 (+ rotation $C178)", "-", 0, "remplacee"),
 ("attraction ($100 = T[$C314])", [0x263C10, 0x26F680], "T_61C110 (40)", 40, "0x98590, 0xA05C0", "T_5B5CB0 / T_5B5CC0 (8)", 8, "modifiee"),
]
o = open(os.path.join(H, "tables_par_decor.tsv"), "w")
o.write("role\troutines_upper(fichier)\tarcade_upper\ttable_upper(exec)\tentrees_upper\troutines_hyper(fichier)\ttable_hyper(exec)\tentrees_hyper\tetat_hyper\n")
for role, r5, t5, n5, r9, t9, n9, e in T:
    o.write("\t".join([role, ", ".join("0x%X" % r for r in r5), ", ".join(arc(r) for r in r5), t5, str(n5 or "-"), r9, t9, str(n9 or "-"), e]) + "\n")
o.close()
C = [  # role ro3 (rapport.json), n, Upper, Hyper (va MIPS / image ro9 du 2026-10-10), verdict
 ("bibliotheque blocs scroll1", 4, "0x14FBE4 0x150448 0x150968 0x150A0C", "0x314154 $0787C2 ; 0x3149B8 $07890E ; 0x314ED8 $0789C0 ; 0x314F7C $0789D8", "Hyper, 4"),
 ("super-tuiles scroll1", 3, "0x150250 0x150724 0x150AA0", "0x3147C0 $0788AC ; 0x314C94 $078954 ; 0x315010 $0789EC", "Hyper, 3"),
 ("bibliotheque blocs scroll2", 1, "0x15163C", "0x315B2C $078B58", "Hyper, 1"),
 ("bibliotheque blocs scroll3", 1, "0x151A7C", "0x315F6C $078C24", "Hyper, 1"),
 ("type scroll1", 1, "0x14F554", "0x313AC4 $07867E", "Hyper, 1"),
 ("type scroll2 / scroll3", 2, "constante 0 (0x151270, 0x151750)", "constante 0 (0x3157E0, 0x315C40)", "rien"),
 ("longs $40/$44 scroll1/2/3", 6, "constantes", "constantes (0x313F20, 0x315A50, 0x315EA0)", "rien"),
 ("controle CPS-B", 2, "T_614CD0 (0x15ACB0)", "T_5C51F0 / T_5C51F2 (0x313960)", "Hyper, 2"),
 ("couleur ROUND", 2, "T_6112D0 (0xF29A0, 0xF2A30)", "T_5C87D0 (0x37BDC0, 0x37BE50), deja 40 entrees", "Hyper, 2 (au-dela de $4E seulement)"),
 ("init joueur ($F, $18/$D0, X/Y)", 5, "constantes (0x247D80, 0x247DB0, 0x247E40)", "constantes (0x2C75E0, 0x2C7610, 0x2C76A0)", "rien"),
 ("positions par decor", 2, "0x196F50 / 0x198A00", "absent", "code Upper greffe"),
 ("listes scroll1/2/3", 3, "0x14F590 0x1512A4 0x151784", "0x313B00 $07869A ; 0x315814 $078AD0 ; 0x315C74 $078B9C", "Hyper, 3"),
 ("palettes scroll1/2/3", 6, "0x4ABD8 0x4BAF8 / 0x4AC78 0x4BB98 / 0x4AD18 0x4BC38", "A 0x605B8 $009234, 0x611C8 $00942C ; B 0x61288 $00944A ; C 0x61348 $009468", "Hyper, 4 (+ variantes $C178)"),
 ("palettes sprites de decor", 2, "0x4AA88 0x4B958", "absent", "code Upper greffe"),
 ("objets de decor", 2, "0x4C1B0 (T_950CE0)", "absent", "code Upper greffe"),
 ("ordre des plans (table de sauts)", 1, "0x151B80 (T_6147B0)", "0x30EC10 (T_5C50D0)", "Hyper, 1"),
 ("gestionnaires scroll1/2/3 (tables de sauts)", 3, "0x151EA0 / 0x155920 / 0x157300", "0x30EF00 / 0x30FEE0 / 0x311550", "Hyper, 3 (+ T_5C50B0/T_5C50C0 : 2)"),
 ("effet par decor (table de sauts)", 1, "0x13BB10 (T_6135A0 + T_6134E0/T_613530)", "0x391E50 (T_5C9E30 + T_5C9E00/T_5C9E08)", "Hyper, 1 (+ 2 tables de mots)"),
 ("ordre des plans (fins)", 1, "moteur des fins (scene A)", "absent", "code Upper greffe"),
 ("alias : animation par decor", 2, "0x199530 / 0x199DA0", "absent", "code Upper greffe"),
 ("alias : animations des objets / donnees par decor", 2, "0xFDC10 (0x971E70) / 0x105C70 (0x740B70)", "absent", "code Upper greffe"),
 ("alias : masques par decor", 2, "0x196F50, 0x198A00 ($C0A00400) ; 0x371920 ($3F60BDB3)", "absent", "code Upper greffe"),
 ("alias : animation de palettes", 2, "0xC8890, 0x1E4530", "0x38D510 (identique)", "Hyper, 1"),
 ("musique (decor >= $50)", 1, "0x139AD0 (VERSUS, par decor)", "absent ; musique d'Hyper non etudiee", "a refaire"),
 ("selection Arcade (tirage)", 1, "0x24F2F4 ($174, 0x24F020)", "0xA4A68 ($174, 0xA49E0) ou site greffe", "Hyper ou greffe, 1"),
]
o = open(os.path.join(H, "correctifs_sfa2_hyper.tsv"), "w")
o.write("role (rapport.json ro3)\tn_ro3\tUpper (va MIPS)\tHyper (va MIPS / image)\tou le refaire\n")
for r in C: o.write("\t".join(str(x) for x in r) + "\n")
o.close()
print(sum(r[1] for r in C), "correctifs ro3 repartis")
