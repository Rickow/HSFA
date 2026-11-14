#!/usr/bin/env python3
"""(L2 des MAX dans la greffe, work/l2_max_greffe/CONCEPTION.md §4, §6) prep_max_ro9.py : PRÉPARATION du code et des
données MAX pour la greffe ro9a (pilote sfa3hamhsfa), sur le modèle de um_prog.py d'Upper MAX (étapes 1 à 3).

  prep_max_ro9.py --dest DIR --base BASE --depot DEPOT --rosette ROSETTE --cache-max CACHE --upper MAME_RO5
                  --extract EXT --anims ANIMS --xdata X_DATA.BIN --eboot BOOT.BIN --pac PAC [--vasm VASM]

  BASE    = construction de la BASE MAX de la greffe (MAX_ZONES=1 : b9/carte_image.txt, b9/roms_ro9/sfa3ud, greffe.json) ;
  ROSETTE = sources MAX régénérées depuis l'ISO PSP (regen_max.py : CACHE/depot/max/outils/rosette_code) : le code de jeu
            converti n'est JAMAIS au dépôt, il est refait à chaque construction (décision du 12/11).

1. matérialise la copie figée de l'intégration d'Upper MAX (tools/integration-max/upper_max/integration_2b31, fige.py)
   dans DIR/outils_max, puis y applique les ADAPTATIONS ro9a ci-dessous (remplacements contrôlés : chaque motif doit être
   trouvé le nombre de fois attendu, sinon arrêt) ; la copie figée du dépôt n'est pas modifiée ;
2. banc de référence = la base MAX (carte + 8 ROM programme) ;
3. correspondances du moteur (correspondances_hyper_ro9a.tsv, adresses seulement) rendues pour CETTE base : va d'Hyper
   telles quelles, va des copies d'Upper traduites par greffe.json « blocs » ; toutes contrôlées dans la carte ;
4. prepare_max.py (adapté) : conversion, non-résolus admis, blocs des frames, assemblage -> DIR/outils_max/ag/prep
   (code_3a0000.bin, blocs/ext_*.bin, symboles.json).
Adaptations ro9a (CONCEPTION §4.2) : données MAX en T4 $710000 et bloc d'Eagle (frames, animations) en T5 $810000,
assemblés ÉTIQUETÉS $01 (zones 68K directes de la greffe : le traducteur et RETAG24 les rendent tels quels) ; IA hors L2
(MAX_IA=0) ; CONV_An du module ro9 (base des données $5AF140)."""
import argparse, csv, json, os, re, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI); import plan_commun_max as PC   # base de l'habillage dans plan2 : une seule source
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
T4, T5 = 0x01710000, 0x01810000                     # zones 68K directes de la greffe (greffe3.py MAX_ZONES), étiquetées
ENV_MAX = {"MAX_FINS": "0", "MAX_CONTRES": "0", "BANC": "banc", "MAX_IA": "0"}   # L2 : fins (L3), contres et IA coupés (CONCEPTION §4.4 e)

# (fichier de l'intégration matérialisée, motif, remplacement, nombre attendu)
ADAPTATIONS = [
    ("ag/outils/prepare_max.py", "MAX_ORG = 0xB80000 ", "MAX_ORG = 0x%08X " % T4, 1),
    ("ag/outils/prepare_max.py", "BLOC_EAGLE = 0xE40000 ", "BLOC_EAGLE = 0x%08X " % T5, 1),
    ("ag/outils/prepare_max.py", "assert MAX_ORG + len(donnees) <= 0xC00000,",
     "assert MAX_ORG + len(donnees) <= 0x%08X," % (T4 + 0xF0000), 1),          # T4 : $710000-$7FFFFF
    ("ag/outils/prepare_max.py", '"ext_%06x.bin" % MAX_ORG', '"ext_%06x.bin" % (MAX_ORG & 0xFFFFFF)', 1),
    ("ag/outils/prepare_max.py", '{"%06x" % MAX_ORG}', '{"%06x" % (MAX_ORG & 0xFFFFFF)}', 1),
    # (D10) types de projectile d'Hyper tous pris (0x5C3AA0, 48) : table recopiée à 64 dans le bloc MAX (MAX_T_PROJ)
    ("ag/outils/prepare_max.py", '"MAX_T_EFFETS:", "        ds.l    64",',
     '"MAX_T_EFFETS:", "        ds.l    64",\n          "; (L2) table des types de projectile d\'Hyper (0x5C3AA0, 48) recopiée à 64 (MAX_T_PROJ)",'
     '\n          "MAX_T_PROJ:", "        ds.l    64",', 1),
    # attaques d'Hyper en 40 o (32 o d'Upper + 8 octets nuls, mesuré sur Ryu) : en-tête de combat au format d'Hyper
    ("ag/outils/donnees_joueur_max.py", "        if 28 <= b[i + 9] <= 32: b[i + 9] += 12\n    return swapw(bytes(b))",
     "        if 28 <= b[i + 9] <= 32: b[i + 9] += 12\n"
     "    assert len(b) % 32 == 0\n"
     "    b = b\"\".join(bytes(b[i:i + 32]) + bytes(8) for i in range(0, len(b), 32))   # (L2) Hyper : attaques de 40 o\n"
     "    return swapw(bytes(b))", 1),
    # enveloppes des classes d'effets MAX : pas d'inscription à l'affichage si le pas courant n'a pas de frame (pointeur
    # nul : calques permanents d'Eagle $33 / $34 au pas de fin) ; le rendu d'Hyper ($959E4 sur ro9a39)
    # lit le type de frame sans contrôle (relevé 13/11 : saut hors table, instruction illégale, image 1178 Eagle-Ryu)
    ("ag/outils/prepare_max.py", '''"        tst.b   (a6)", "        beq.s   .r", "        move.b  #$10, $9(a6)"]''',
     '''"        tst.b   (a6)", "        beq.s   .r"] + GARDE_FRAME + ["        move.b  #$10, $9(a6)"]''', 1),
    ("ag/outils/prepare_max.py", "def integration():\n",
     '''# (L2, greffe ro9a) garde : frame du pas courant ($1C, long à moitiés échangées ; pas +4 idem) nulle -> pas d'inscription
GARDE_FRAME = ["        move.l  a0, -(sp)", "        movea.l $1c(a6), a0", "        exg     d0, a0", "        swap    d0",
               "        exg     d0, a0", "        jsr     $400.w", "        tst.l   4(a0)", "        movea.l (sp)+, a0",
               "        beq.s   .r"]
def integration():\n''', 1),
    # (A2, R1) types de recul (13/11, 2e décision, MESURÉE) : les types PSP 28-32 (Eagle : 30 et 31, 27 attaques) gardés en
    # types natifs d'Hyper lisaient les séquences d'Hyper $1B / $1C (18 images chacune) au lieu des séquences MAX S27 / S28
    # (50 et 42 images, reculs différents) : supers à coups multiples différents d'Upper MAX
    # (banc eagle_A, coups_A_g_1 : recul de J2 absent, un coup de plus). Comme Upper MAX : types 28-32 -> 40-44 (le +12 de
    # donnees_joueur_max et RECUL_MAX restent), table des types = COPIE de celle d'Hyper (0x5C2330, 80 octets : types 0-34
    # natifs) + types 40-44 -> séquences 64-68 ; tables rel16 des séquences recopiées et prolongées (RECUL_S25-S29) par
    # integre_max_ro9.recul_tables (LEA de 0x5C2330 -> MAX_RECUL_TYPES ; LEA des tables 0x66A260 / 0x66A5AE -> copies).
    ("ag/outils/prepare_max.py",
     'b = open("@EXT@/decompressed/ro5_usa_prog68k.bin", "rb").read()\n'
     '    o = 0x61B460 - 0x1F0000\n    ps2 = bytearray(b[o:o + 64]) + bytearray(96 - 64)\n'
     '    for typ, sq in zip(range(28, 33), range(25, 30)):\n',
     'b = open("@EXT@/decompressed/ro9_usa_prog68k.bin", "rb").read()   # (L2) Hyper\n'
     '    o = 0x5C2330 - 0x1F0000\n    ps2 = bytearray(b[o:o + 80]) + bytearray(96 - 80)   # (L2) 0x5C2330 : types 0-34 + 4 nuls\n'
     '    for typ, sq in zip(range(28, 33), range(64, 69)):   # (L2) séquences MAX n° 64-68 (integre_max_ro9.recul_tables)\n', 1),
    # (pas 8) aperçu de sélection : comme Upper MAX, emplacement 0 (banque commune prolongée, codes locaux $7000+ de
    # hud_apercu_max tels quels ; la table prolongée est f545 de la greffe : fait_gfx_max.py) : aucun talon
    # (pas 8, écart 15) codes d'habillage (portraits, noms, HUD) : emplacement 1 comme Upper MAX, mais dans la suite de plan2
    # jamais employée par la greffe (plan_commun_max.P2_BASE) au lieu de « plan2 prolongé » (plan2 de la greffe est plein) ;
    # code de frame = P2_BASE + g - G0 - $1000 (correspondance AFFINE, ne dépend que du cache, pas de PB1)
    ("ag/outils/hud_apercu_max.py", "def code_plan2(g): return PB1 + (g - G0) - 0x1C00\n",
     "def code_plan2(g): return 0x%04X + g - G0 - 0x1000" % PC.P2_BASE + "   # (L2) emplacement 1, suite libre de plan2 (plan_commun_max)\n", 1),
    ("ag/outils/prepare_max.py", "def code_plan2(g): return PB1 + (g - G0) - 0x1C00",
     "def code_plan2(g): return 0x%04X + g - G0 - 0x1000" % PC.P2_BASE + "   # (L2) emplacement 1, suite libre de plan2 (plan_commun_max) ;", 1),
    # (pas 8) pointeurs d'Upper vers la structure des noms (0x961AF0 et suivantes : tables de positions des cartouches et
    # bandeaux) dans les frames d'habillage -> mêmes tables d'Hyper (0x697ED0 : décalage constant, contenu contrôlé à l'octet)
    ("ag/outils/prepare_max.py", '    tout_s = "\\n".join(tout)\n',
     '    tout_s = "\\n".join(tout)\n    import l2_sources; tout_s = l2_sources.adapte_tout(tout_s)   # (L2, greffe ro9a)\n', 1),
    # tables d'animation ajoutées pour Hyper (ANIM_26_2B8H, ANIM_26_PTRS_H) : mêmes genres que leurs modèles
    ("ag/conv/convertit_frames.py", "(_2B[048C])?', lab): return 'mots'", "(_2B[048C]H?)?', lab): return 'mots'", 1),
    ("ag/conv/convertit_frames.py", "_PTRS', lab): return 'longs'", "_PTRS(_H)?', lab): return 'longs'", 1),
]
def lance(cmd, cwd, env, log):
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n=== %s (cwd %s)\n" % (" ".join(cmd), cwd)); f.flush()
        pre = ["nice", "-n", "19"] if os.name == "posix" and shutil.which("nice") else []
        r = subprocess.run(pre + cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode: sys.exit("échec (%d) : %s ; voir %s" % (r.returncode, " ".join(cmd), log))


def adapte(O, ext):
    ext = ext.replace('\\', '/')   # (portabilité) chemin écrit avec « / », comme les marques de fige.py
    for f, a, b, n in ADAPTATIONS:
        a, b = a.replace("@EXT@", ext), b.replace("@EXT@", ext)   # chemin de l'extraction de l'Anthology (materialise par fige)
        p = os.path.join(O, f); t = open(p, encoding="utf-8").read()
        k = t.count(a)
        assert k == n, "%s : motif %r trouvé %d fois (attendu %d)" % (f, a[:60], k, n)
        open(p, "w", encoding="utf-8").write(t.replace(a, b))
    # sources MAX : adaptations appliquées par prepare_max.sources() APRÈS la copie des sources et du cache (l2_sources.py)
    shutil.copy(os.path.join(ICI, "l2_sources.py"), os.path.join(O, "ag", "outils", "l2_sources.py"))
    p = os.path.join(O, "ag", "outils", "prepare_max.py"); t = open(p, encoding="utf-8").read()
    a_ = "    return src\n\ndef renumerote"
    assert t.count(a_) == 1, "prepare_max.py : fin de sources() introuvable"
    open(p, "w", encoding="utf-8").write(t.replace(a_, "    import l2_sources; l2_sources.adapte(src)   # (L2, greffe ro9a)\n" + a_))
    # CONV_An : repère des talons dans l'image (« MOVE SR,-(A7) ; CMPA.L #base,An ») ; Upper : base $60ACC0, module ro9 :
    # base des données $5AF140 (même ajout que la copie max_hyper/conversion/conv du 08/11)
    p = os.path.join(O, "ag", "conv", "convertit_max.py"); t = open(p, encoding="utf-8").read()
    a_ = "        p = img.find(motif, 0, 0x10000)\n"
    assert t.count(a_) == 1, "convertit_max.py : repère CONV_An introuvable"
    t = t.replace(a_, a_ + "        if p < 0:   # (L2, greffe ro9a) base des données $5AF140 (CMPA.L #$5AF140,An)\n"
                  "            p = img.find(bytes([0x40, 0xE7, 0xB1 | (n << 1), 0xFC, 0x00, 0x5A, 0xF1, 0x40]), 0, 0x10000)\n")
    open(p, "w", encoding="utf-8").write(t)


def correspondances(base, sortie):
    """correspondances_hyper_ro9a.tsv -> format de agent_max_upper/correspondances.tsv, pour la base donnée"""
    carte = {}
    for l in open(os.path.join(base, "b9", "carte_image.txt"), errors="replace", encoding="utf-8"):
        p = l.split(None, 2)
        try: carte.setdefault(int(p[1], 16), int(p[0], 16))
        except (ValueError, IndexError): pass
    blocs = [tuple(int(x, 16) for x in b) for b in json.load(open(os.path.join(base, "greffe.json"), encoding="utf-8"))["blocs"]]
    L = [l for l in open(os.path.join(ICI, "correspondances_hyper_ro9a.tsv"), encoding="utf-8").read().splitlines()
         if l and not l.startswith("#")]
    rows = list(csv.DictReader(L, delimiter="\t")); out = []; n = {"ok": 0, "non resolu": 0}
    for r in rows:
        va = None
        if r["genre"] == "hyper": va = int(r["va"], 16)
        elif r["genre"] == "greffe":
            v5 = int(r["va"], 16); va = next((c + v5 - a for a, b, c in blocs if a <= v5 < b), None)
            assert va is not None, "%s : va d'Upper %x hors des blocs de la greffe" % (r["arcade"], v5)
        if va is not None:
            assert va in carte, "%s : va %x absente de la carte de la base" % (r["arcade"], va)
            n["ok"] += 1
        else: n["non resolu"] += 1
        out.append(dict(arcade=r["arcade"], nom=r["nom"], upper_68k="-", va_mips_instr=("0x%x" % va) if va is not None else "",
                        va_mips_entree="", statut=r["statut"], remarque=r["remarque"], upper_68k_image_12h56="-",
                        source="greffe/max/correspondances_hyper_ro9a.tsv (%s)" % r["genre"]))
    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    cols = ["arcade", "nom", "upper_68k", "va_mips_instr", "va_mips_entree", "statut", "remarque", "upper_68k_image_12h56", "source"]
    w = csv.DictWriter(open(sortie, "w", encoding="utf-8", newline=""), cols, delimiter="\t"); w.writeheader(); w.writerows(out)
    print("correspondances ro9a : %d résolues, %d non résolues" % (n["ok"], n["non resolu"]))


def main():
    ap = argparse.ArgumentParser()
    for k in ("dest", "base", "depot", "rosette", "cache_max", "upper", "extract", "anims", "xdata", "eboot", "pac"):
        ap.add_argument("--" + k.replace("_", "-"), required=True)
    ap.add_argument("--vasm", default="")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--env", action="append", default=[], metavar="VAR=VAL")
    a = ap.parse_args()
    absp = os.path.abspath
    D = absp(a.dest); O = os.path.join(D, "outils_max"); AG = os.path.join(O, "ag")
    if os.path.exists(O): shutil.rmtree(O)
    os.makedirs(os.path.join(D, "mame_vide", "roms", "sfa3ud"), exist_ok=True)
    UM = os.path.join(absp(a.depot), "tools", "integration-max", "upper_max")
    sys.path.insert(0, UM); import fige
    n = fige.materialiser(O, {"@UM_AG@": AG, "@UM_RELEVES@": os.path.join(O, "releves"), "@UM_EBOOT@": absp(a.eboot),
                              "@UM_DEPOT@": absp(a.depot), "@UM_EXTRACT@": absp(a.extract), "@UM_ANIMS@": absp(a.anims),
                              "@UM_XDATA@": absp(a.xdata), "@UM_MAME_RO5@": absp(a.upper),
                              "@UM_MAME@": os.path.join(D, "mame_vide"), "@UM_VASM@": absp(a.vasm) if a.vasm else "vasm-non-fourni"})
    shutil.copytree(absp(a.rosette), os.path.join(AG, "max_trad", "rosette_code"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    adapte(O, absp(a.extract))
    print("intégration 2b31 matérialisée et adaptée (ro9a) : %d fichiers ; sources MAX : %s" % (n, a.rosette))
    R = os.path.join(AG, "banc_ref"); os.makedirs(os.path.join(R, "roms_ro5", "sfa3ud"), exist_ok=True)
    B = absp(a.base)
    shutil.copyfile(os.path.join(B, "b9", "carte_image.txt"), os.path.join(R, "carte_image.txt"))
    for p in PRG: shutil.copyfile(os.path.join(B, "b9", "roms_ro9", "sfa3ud", p), os.path.join(R, "roms_ro5", "sfa3ud", p))
    correspondances(B, os.path.join(O, "releves", "agent_max_upper", "correspondances.tsv"))
    open(os.path.join(AG, "conv", "correspondances_complement.tsv"), "w", encoding="utf-8").write("arcade\tnom\tva_mips_instr\tstatut\tsource\n")
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT",
                                                        "USERPROFILE", "TEMP", "TMP", "HSFA_ASM", "HSFA_VASM",
                                                        "HSFA_SANS_LIENS", "PYTHONUTF8") or k.startswith("_PYI_")}
    env.update(ENV_MAX, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", MAX_RACINE=AG,
               SFA3MAX_CACHE=absp(a.cache_max), SFA3MAX_EBOOT=absp(a.eboot), SFA3MAX_PAC_DIR=absp(a.pac),
               PYTHONPATH=os.path.join(absp(a.depot), "src", "hsfa"), L2_EXTRACT=absp(a.extract))
    env.update(dict(kv.split("=", 1) for kv in a.env))
    log = os.path.join(D, "prep_max_ro9.log")
    if os.path.exists(log): os.remove(log)
    lance([a.python, "prepare_max.py"], os.path.join(AG, "outils"), env, log)
    print("préparation MAX ro9a : %s" % os.path.join(AG, "prep"))


if __name__ == "__main__":
    main()
