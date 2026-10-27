"""Variante HYPER (voie B) des tables d'animations des persos MAX : $2B8 à 144 entrées (3 sous-tables), 2026-10-11.
Hyper (ro9) lit $2B8 à l'index n + 48 × s (0x2B8E10, champs de la VICTIME) : s = 0 coup ZERO 3, s = 1 coup d'une version
ancienne ($328 ≠ 0, $28D = 0), s = 2 enchaînement de custom combo ($28D ≠ 0) (BLOC-HYPER.md, agent HSFA). Les sous-tables
1 et 2 pointent, pour une dizaine d'entrées, vers des COPIES de pas dont seul l'octet +8 (index du jeu de boîtes, 1er
octet de la ligne A/B/C) change ; Hyper ajoute pour cela deux jeux de boîtes PAR PERSO en fin de sa table $88 :
A = aucune boîte de corps, B = une seule boîte de corps (Ryu $74 / $75, Ken $6F / $70…). Règle mesurée sur les 33 blocs
distincts d'Hyper (rosette_construction/FORMAT-UPPER-HYPER.md) : REGLE ci-dessous (majorité).
Entrée : la sortie de anims_max.construire (inchangée) ; sortie : anims_hyper_XX.s = REMPLAÇANT de anims_XX.s pour
Hyper (mêmes étiquettes P%02X_…, ANIM_%02X…, ANIM_%02X_PTRS ; ANIM_%02X_2B8 = 144 entrées), copies H1_/H2_ ajoutées
après les pas d'origine ; symboles_anims_hyper_max.s (adresses, à inclure À LA PLACE de symboles_anims_max.s).
Symboles à définir à l'intégration (index des 2 jeux ajoutés à la table de boîtes du perso) : BOITES_A_%02X, BOITES_B_%02X.
Usage : python3 anims_hyper_max.py   (vérifie par vasm : assemblage sans erreur et sous-table 0 = $2B8 d'origine)"""
import os, re, subprocess, tempfile
import anims_max as AM
ICI = os.path.dirname(os.path.abspath(__file__))
VASM = os.path.expanduser("~/outils/vasm/vasmm68k_mot")
# (sous-table, entrée) -> (pas modifiés, nouvelle valeur) ; pas : "tous", "sauf1" (tous sauf le 1er), "dernier"
REGLE = {}
for n in (19, 23, 24, 28, 32): REGLE[(1, n)] = ("sauf1", "A")
REGLE[(1, 33)] = ("tous", "A"); REGLE[(1, 34)] = ("dernier", "A")
for n in (19, 23, 24, 28, 29, 32, 34): REGLE[(2, n)] = ("tous", "B")
REGLE[(2, 33)] = ("tous", "A")
for s in (1, 2): REGLE[(s, 22)] = ("sauf1", "$06"); REGLE[(s, 27)] = ("tous", "$06")


def pas_de(asm, lab):
    """[(étiquette, lignes)] des pas d'une animation à partir de lab, jusqu'au pas de fin (bit 6) ou à reprise (bit 7)"""
    k = asm.index(lab + ":"); out = []
    while True:
        l = asm[k]; assert l.endswith(":"), l
        corps = []; k += 1
        while k < len(asm) and not asm[k].endswith(":") and not asm[k].startswith("ANIM_"): corps.append(asm[k]); k += 1
        out.append((l[:-1], corps))
        d1 = int(corps[0].split(",")[1].strip().lstrip("$"), 16)
        if d1 & 0xC0: return out


def copier(cid, asm, lab, s, n):
    """lignes des pas copiés (ou None si la règle ne change rien) ; reprise vers un pas copié si elle vise l'animation"""
    quoi, val = REGLE[(s, n)]
    val = "BOITES_%s_%02X" % (val, cid) if val in "AB" else val
    P = pas_de(asm, lab); noms = {e: "H%d_%02X_%d_%d" % (s, cid, n, j) for j, (e, _) in enumerate(P)}
    idx = {"tous": range(len(P)), "sauf1": range(1, len(P)), "dernier": [len(P) - 1]}[quoi]
    out = []; change = False
    for j, (e, corps) in enumerate(P):
        c = list(corps); out.append(noms[e] + ":")
        if j in idx:
            bx = c[2].split("dc.b")[1].split(",")
            if bx[0].strip() != val: change = True
            c[2] = "        dc.b    " + ", ".join([val] + [x.strip() for x in bx[1:]]) + "   ; jeu de boîtes Hyper (s%d)" % s
        for i, l in enumerate(c):
            m = re.match(r"^(\s+dc\.l\s+)(P\w+)(\s+; reprise)$", l)
            if m and m.group(2) in noms: c[i] = m.group(1) + noms[m.group(2)] + m.group(3)
        out += c
    return out if change else None


def construire_hyper(cid, SF):
    b, adr, asm, al, npas = AM.construire(cid, SF)
    t0 = asm.index(next(l for l in asm if l.startswith("ANIM_%02X_2B8:" % cid)))
    ent = [re.search(r"dc\.w\s+(\w+)-", asm[t0 + 1 + i]).group(1) for i in range(48)]
    copies = []; table = []
    for s in range(3):
        for n, lab in enumerate(ent):
            cible = lab
            if s and (s, n) in REGLE:
                c = copier(cid, asm, lab, s, n)
                if c: copies += c; cible = "H%d_%02X_%d_0" % (s, cid, n)
            table.append("        dc.w    %s-ANIM_%02X_2B8%s" % (cible, cid, "" if n else "        ; sous-table %d" % s))
    sortie = asm[:t0] + ["ANIM_%02X_2B8:                ; table $2B8 HYPER, 3 × 48 animations (n + 48 × s)" % cid] + table \
        + asm[t0 + 49:] + ["; ---- copies de pas des sous-tables 1-2 (Hyper ; octet de jeu de boîtes changé)"] + copies
    sortie[0] = sortie[0].replace("généré par anims_max.py", "généré par anims_hyper_max.py (variante Hyper de anims_max.py)")
    return sortie, len(copies)


def assembler(cid, lignes):
    """assemble (vasm) avec des valeurs d'essai des jeux de boîtes ; -> (binaire, symboles ANIM_…)"""
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "t.s")
        open(src, "w").write("\n".join(open(os.path.join(ICI, "symboles_frames_max.s")).read().split("\n")
                                       + ["BOITES_A_%02X equ $FE" % cid, "BOITES_B_%02X equ $FF" % cid] + lignes) + "\n")
        r = subprocess.run([VASM, "-m68000", "-spaces", "-Fbin", "-quiet", "-L", os.path.join(d, "l.txt"), "-o",
                            os.path.join(d, "t.bin"), src], capture_output=True, text=True)
        if r.returncode: raise SystemExit("vasm : " + (r.stdout + r.stderr)[-2000:])
        sym = {}
        for l in open(os.path.join(d, "l.txt"), errors="replace"):
            m = re.match(r"^(ANIM_\w+)\s+(?:LAB|ABS)?\s*\(?0x([0-9A-Fa-f]+)", l.strip()) or \
                re.match(r"^([0-9A-Fa-f]+)\s+(?:\w+\s+)?(ANIM_\w+)$", l.strip())
            if m:
                a, bb = m.groups()
                if a.startswith("ANIM_"): sym[a] = int(bb, 16)
                else: sym[bb] = int(a, 16)
        return open(os.path.join(d, "t.bin"), "rb").read(), sym


if __name__ == "__main__":
    import struct
    SF = AM.symboles_frames(); symb = ["; tables d'animations maîtresses MAX, VARIANTE HYPER — généré par anims_hyper_max.py",
                                       "; jeux de boîtes ajoutés (à définir à l'intégration) : BOITES_A_xx (aucune boîte de corps), "
                                       "BOITES_B_xx (une seule boîte de corps)"]
    for cid in sorted(AM.BASES):
        lignes, nc = construire_hyper(cid, SF)
        open(os.path.join(ICI, "anims_hyper_%s.s" % AM.NOMS[cid]), "w").write("\n".join(lignes) + "\n")
        bin_, sym = assembler(cid, lignes)
        base = AM.BASES[cid]; orig = open(os.path.expanduser("~/.cache/sfa3max/anims_%02x.bin" % cid), "rb").read()
        t = sym["ANIM_%02X_2B8" % cid] - base
        # contrôle : chaque entrée de la sous-table 0 mène au même pas (mêmes 20 octets) que la table d'origine
        so = AM.construire(cid, SF)[1]["ANIM_%02X_2B8" % cid] - base
        ok = sum(bin_[t + struct.unpack_from(">h", bin_, t + 2 * i)[0]:][:20] == orig[so + struct.unpack_from(">h", orig, so + 2 * i)[0]:][:20]
                 for i in range(48))
        diff = sum(struct.unpack_from(">h", bin_, t + 2 * (48 * s + i))[0] != struct.unpack_from(">h", bin_, t + 2 * i)[0]
                   for s in (1, 2) for i in range(48))
        symb += ["%s equ $%06X" % (k, v) for k, v in sorted(sym.items())]
        print("$%02X %-6s : %6d octets (+%d), sous-table 0 = origine %d/48, entrées copiées s1+s2 : %d, lignes de pas copiées %d"
              % (cid, AM.NOMS[cid], len(bin_), len(bin_) - len(orig), ok, diff, nc))
    open(os.path.join(ICI, "symboles_anims_hyper_max.s"), "w").write("\n".join(symb) + "\n")
