#!/usr/bin/env python3
"""um_prog.py -- étape « prog_uppermax » de hsfa_build.py : programme d'Upper AVEC les persos MAX (construction MAX=1
de l'intégration, état du lot 2b31), depuis les sorties de hsfa_build (Upper sans MAX, banques, extraction de l'ISO
PS2) et les données MAX régénérées depuis l'ISO PSP (regen_max.py).

  python3 um_prog.py --dest DIR --upper W/mame_ro5 --extract EXT --anims ANIMS --xdata X_DATA.BIN --cache-max CACHE
                     --rosette CACHE/depot/max/outils/rosette_code --eboot BOOT.BIN --pac PAC_DIR --depot DEPOT --vasm VASM
Enchaîne (= construit_max.sh de l'intégration, BANC=banc_max52, MAX_FINS=1, MAX_CONTRES=1) :
  1. matérialise integration_2b31/ (marques @UM_*@) dans DIR/outils_max ; max_trad/rosette_code = sources régénérées ;
  2. banc de référence = Upper SANS MAX produit par hsfa_build (carte_image.txt + 8 ROM programme) ;
  3. prepare_max.py (conversion du code MAX, vasm) ; 4. banques MAX (perso 38+k -> 3838+k) ;
  5. mame_test.py MAX=1 (traducteur de l'intégration) ; 6. contrôle des marques de fin (outils/audit/marques.py).
Sortie : DIR/banc (roms_ro5/sfa3ud, ext_*.bin, banques_hx/, max_plus_gfx.bin, sfa3max_cache.txt).
Audit (développement) : si UM_AUDIT_DIR est défini, PYTHONPATH et UM_* sont transmis aux outils.
Base d'Upper : n'importe quelle version du traducteur, pourvu que la copie figée (ag/untranspile) soit la même : la
préparation relit carte_image.txt de --upper, et integre_max.py tire ses sites de l'image (motifs uniques, sauts décodés)
et les recoupe avec les va MIPS de la carte ; aucune adresse d'image n'est écrite en dur (v161). --env VAR=VAL
(développement) passe un interrupteur du traducteur aux outils (ex. base v160 : tous les interrupteurs v161 à 0).
"""
import argparse, json, os, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import fige

PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
ENV_MAX = {"MAX_FINS": "1", "MAX_CONTRES": "1", "BANC": "banc"}   # = commande du lot 2b31 (ETAT de l'intégration)


def lance(cmd, cwd, env, log):
    with open(log, "a") as f:
        f.write("\n=== %s (cwd %s)\n" % (" ".join(cmd), cwd)); f.flush()
        pre = ["nice", "-n", "19"] if os.name == "posix" and shutil.which("nice") else []
        r = subprocess.run(pre + cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    if r.returncode: sys.exit("échec (%d) : %s ; voir %s" % (r.returncode, " ".join(cmd), log))


def banques(ag, banc, upper_banques, cache):
    """= bloc Python de construit_max.sh : copie des banques d'Upper + une banque par perso MAX actif"""
    B = os.path.join(banc, "banques_hx")
    if os.path.exists(B): shutil.rmtree(B)
    shutil.copytree(upper_banques, B)
    P = json.load(open(os.path.join(ag, "outils", "persos_max.json")))
    act = [k for k, v in P.items() if not k.startswith("_") and v.get("actif")]
    L = open(os.path.join(B, "carte.txt")).read().splitlines()
    MP = os.path.join(ag, "prep", "max_plus.json")
    EF = json.load(open(MP)).get("efct", {}) if os.path.exists(MP) else {}
    for p in act:
        i = int(p, 16); n = 3800 + i
        L = [l for l in L if l.split()[:2] != ["perso", str(i)]] + ["perso %d %d" % (i, n)]
        src = os.path.join(cache, "fork", "pl%s_hx.bin" % P[p]["suffixe"])
        for e in EF.values():
            if e["pl"] == "pl" + P[p]["suffixe"]: src = os.path.join(ag, "prep", e["table"])
        shutil.copyfile(src, os.path.join(B, "f%d.bin" % n))
    open(os.path.join(B, "carte.txt"), "w").write("\n".join(L) + "\n")
    return act


def main():
    ap = argparse.ArgumentParser()
    for k in ("dest", "upper", "extract", "anims", "xdata", "cache_max", "rosette", "eboot", "pac", "depot"):
        ap.add_argument("--" + k.replace("_", "-"), required=True)
    ap.add_argument("--vasm", default="", help="vasmm68k_mot : seulement avec HSFA_ASM=vasm ou compare (sinon hsfa_asm68k)")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--env", action="append", default=[], metavar="VAR=VAL",
                    help="variable transmise aux outils (developpement : interrupteurs du traducteur, ex. A8_ENTREE=0)")
    a = ap.parse_args()
    D = os.path.abspath(a.dest); O = os.path.join(D, "outils_max"); AG = os.path.join(O, "ag"); BANC = os.path.join(D, "banc")
    for d in (O, BANC):
        if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(os.path.join(D, "mame_vide", "roms", "sfa3ud"), exist_ok=True)   # aucun lien vers une ROM d'atelier
    absp = os.path.abspath
    # 1. copie figée + sources MAX régénérées
    n = fige.materialiser(O, {"@UM_AG@": AG, "@UM_RELEVES@": os.path.join(O, "releves"), "@UM_EBOOT@": absp(a.eboot),
                              "@UM_DEPOT@": absp(a.depot), "@UM_EXTRACT@": absp(a.extract), "@UM_ANIMS@": absp(a.anims),
                              "@UM_XDATA@": absp(a.xdata), "@UM_MAME_RO5@": absp(a.upper),
                              "@UM_MAME@": os.path.join(D, "mame_vide"), "@UM_VASM@": absp(a.vasm) if a.vasm else "vasm-non-fourni"})
    RC = os.path.join(AG, "max_trad", "rosette_code")
    shutil.copytree(absp(a.rosette), RC, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("intégration 2b31 : %d fichiers ; sources MAX : %s" % (n, a.rosette))
    # 2. banc de référence = Upper sans MAX (hsfa_build prog_upper)
    R = os.path.join(AG, "banc_ref"); os.makedirs(os.path.join(R, "roms_ro5", "sfa3ud"), exist_ok=True)
    shutil.copyfile(os.path.join(a.upper, "carte_image.txt"), os.path.join(R, "carte_image.txt"))
    for n in PRG:
        shutil.copyfile(os.path.join(a.upper, "roms_ro5", "sfa3ud", n), os.path.join(R, "roms_ro5", "sfa3ud", n))
    # Windows : USERPROFILE (« ~ »), TEMP / TMP (sinon dossier temporaire = C:\Windows) ; constructeur tout-en-un :
    # _PYI_* (chargeur PyInstaller : sinon chaque etape re-extrait l'executable, dans ce dossier temporaire)
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT",
                                                        "USERPROFILE", "TEMP", "TMP", "HSFA_ASM", "HSFA_VASM",
                                                        "HSFA_SANS_LIENS", "PYTHONUTF8") or k.startswith("_PYI_")}
    env.update(ENV_MAX, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", MAX_RACINE=AG,
               SFA3MAX_CACHE=absp(a.cache_max), SFA3MAX_EBOOT=absp(a.eboot), SFA3MAX_PAC_DIR=absp(a.pac),
               PYTHONPATH=os.path.join(absp(a.depot), "src", "hsfa"))          # mwo3_codec
    env.update(dict(kv.split("=", 1) for kv in a.env))
    if os.environ.get("UM_AUDIT_DIR"):                                         # (développement) audit des lectures
        env.update({k: v for k, v in os.environ.items() if k.startswith("UM_")})
        env["PYTHONPATH"] = os.environ.get("PYTHONPATH", "") + os.pathsep + env["PYTHONPATH"]
    log = os.path.join(D, "um_prog.log"); py = a.python
    if os.path.exists(log): os.remove(log)
    # 3. préparation MAX
    lance([py, "prepare_max.py"], os.path.join(AG, "outils"), env, log)
    # 4. banques
    act = banques(AG, BANC, os.path.join(a.upper, "banques_hx"), absp(a.cache_max))
    open(os.path.join(BANC, "sfa3max_cache.txt"), "w").write(absp(a.cache_max) + "\n")
    # 5. traduction MAX=1
    lance([py, "mame_test.py"], os.path.join(AG, "untranspile"), dict(env, MAX="1", MODULE="ro5", TRAVAIL=BANC,
          XDATA=absp(a.xdata), ANIM_CACHE=absp(a.anims)), os.path.join(BANC, "construction.log"))
    # 6. marques de fin des blocs ajoutés (piège 0x960090)
    with open(os.path.join(BANC, "marques.tsv"), "w") as f:
        r = subprocess.run([py, os.path.join(AG, "outils", "audit", "marques.py"), BANC], env=env, stdout=f, stdin=subprocess.DEVNULL)
    if r.returncode: sys.exit("ÉCHEC : marque de fin absente (marques.tsv)")
    print("prog_uppermax : persos %s ; banc %s" % (",".join(act), BANC))


if __name__ == "__main__":
    main()
