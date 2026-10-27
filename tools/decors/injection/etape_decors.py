#!/usr/bin/env python3
"""ETAPE « DECORS » de la construction (INJECTION-FORK.md §8) : PSD rempli par l'utilisateur -> ROM programme traduite
corrigee + bloc externe + region graphique (mode « bases de plans ») pour le fork sfa3hx et le coeur FBNeo HSFA.

Enchainement, pour un module deja construit par mame_test.py (roms + carte_image.txt + ext_*.bin dans TRAVAIL) :
  1. memoire de decor rangee telle quelle : hsfa_plans.py (MODULE, HSFA_PLANS_VIDE15=1) -> <sortie>/hsfa_plans.bin ;
  2. pour chaque decor : emplacements de palettes surs (palettes_libres.py : tilemaps completes, relogement) puis
     reimport.py (PSD -> tuiles, palettes, carte etendue ; --zone 448 par defaut) -> <sortie>/reimport_<decor>/ ;
  3. injection_fork.py sur tous les decors en une passe -> <sortie>/roms/sfa3hx, <sortie>/ext/, hsfa_plans_decor.bin ;
  4. (option --anneau) table de l'anneau scroll1 corrigee pour le 448 (composition a gauche a -32 au lieu de -64) ;
  5. (option --zip) archive sfa3hsfa.zip du coeur FBNeo (config « plans= », hsfa_gfx.bin).
Lancement fork : HSFA_PLANS=300,340,3a0 HSFA_EXT=<sortie>/ext HSFA_GFX=<sortie>/hsfa_plans_decor.bin@3000000
                 cps2f sfa3hx -rompath <sortie>/roms ... (banc_plans.lua ecrit les bases ; banc_sprites.lua inchange)

Usage : ../venv/bin/python etape_decors.py --psd <PSD> --decor 0C=<export du pilote>[+28] [--decor ...]
        --travail <dossier du module (roms_tr, carte_image.txt, ext_*.bin)> --sortie <dossier> [--module ro3]
        [--zone 448|512|tout] [--tramage aucun|ordonne] [--anneau] [--zip]
"""
import os, sys, json, argparse, subprocess, struct, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
DW = os.path.dirname(HERE)                                   # decors_ws
PY = os.path.join(DW, "venv/bin/python")
sys.path.insert(0, os.path.join(HERE, "py"))
import image, blocs_tr as BT, palettes_libres as PL

SORTIE_ROMS = {"ro3": "roms_tr", "ro5": "roms_ro5", "ro9": "roms_ro9"}
ANNEAU_PS2 = {"ro3": None}                                   # table de l'anneau : reperee par motif (voir anneau())


def lance(cmd, env=None, log=None):
    print("  $", " ".join(cmd) if isinstance(cmd, list) else cmd)
    r = subprocess.run(cmd, env=dict(os.environ, **(env or {})), capture_output=True, text=True)
    if log: open(log, "w").write(r.stdout + r.stderr)
    if r.returncode: raise SystemExit("echec (%d) : %s\n%s" % (r.returncode, cmd, (r.stdout + r.stderr)[-3000:]))
    return r.stdout


def anneau(img):
    """table (D2, D3) par sens de l'anneau scroll1 : 8 mots FFC0 0120 FFC0 FFC0 FFC0 0120 01A0 0120 (arcade $18BA6,
    ro3 $9C1E0) ; composition a gauche a -32 au lieu de -64 -> plus de colonne perimee dans la bande droite en 448"""
    motif = bytes.fromhex("ffc00120ffc0ffc0ffc0012001a00120")
    i = img.find(motif)
    assert i > 0 and img.find(motif, i + 1) < 0, "table de l'anneau introuvable ou multiple"
    for a in (i, i + 8):
        struct.pack_into(">H", img, a, 0xFFE0)
    return i


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--psd", required=True)
    ap.add_argument("--decor", action="append", required=True, help="0C=<dossier d'export du pilote>[+28...]")
    ap.add_argument("--travail", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--module", default="ro3")
    ap.add_argument("--zone", default="448")
    ap.add_argument("--tramage", default="aucun")
    ap.add_argument("--ext-base", default="C80000")
    ap.add_argument("--anneau", action="store_true")
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--untranspile", default=os.path.join(HERE, "untranspile"))
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    roms = os.path.join(a.travail, SORTIE_ROMS[a.module], "sfa3ud")
    carte = os.path.join(a.travail, "carte_image.txt")
    M = BT.depuis_carte(carte, a.module)
    img = image.lit(roms)
    # 1. memoire de decor du fork
    plans = os.path.join(a.sortie, "hsfa_plans.bin")
    if not os.path.exists(plans):
        tmp = os.path.join(a.sortie, "plans_tmp"); os.makedirs(os.path.join(tmp, "banques"), exist_ok=True)
        lance([PY, "-W", "ignore", os.path.join(a.untranspile, "hsfa_plans.py")],
              env=dict(MODULE=a.module, TRAVAIL=tmp, BANQUES_OUT=os.path.join(tmp, "banques"), HSFA_PLANS_VIDE15="1",
                       PYTHONPATH="<workspace>/scripts"), log=os.path.join(a.sortie, "hsfa_plans.log"))
        shutil.move(os.path.join(tmp, "hsfa_plans.bin"), plans)
    # 2. reimport par decor
    specs = []
    for d in a.decor:
        tete, exp = d.split("=", 1)
        lies = []
        if "+" in exp.rsplit("/", 1)[-1]:
            exp, l_ = exp.rsplit("+", 1); lies = l_.split("+")
        ds = [int(tete, 16)] + [int(x, 16) for x in lies]
        lib = None
        for dd in ds:                                            # emplacements surs pour le decor ET ses decors lies
            r = PL.libres(img, M, dd, reloge=True)
            s = {p for L in (1, 2, 3) for p in r[L]}
            lib = s if lib is None else lib & s
        so = os.path.join(a.sortie, "reimport_%02X" % ds[0])
        lance([PY, "-W", "ignore", os.path.join(DW, "reimport/reimport.py"), "--psd", a.psd, "--groupe", "$%02X" % ds[0],
               "--export", exp, "--decor", "%02X" % ds[0], "--sortie", so, "--zone", a.zone, "--tramage", a.tramage,
               "--palettes-libres", ",".join("%02X" % p for p in sorted(lib))], log=so + ".log")
        specs.append("%s:%s" % (so, "+".join("%02X" % x for x in ds)))
    # 3. injection
    cmd = [PY, "-W", "ignore", os.path.join(HERE, "injection_fork.py"), "--sortie", a.sortie, "--module", a.module,
           "--roms", roms, "--carte-image", carte, "--plans", plans, "--ext-base", a.ext_base]
    for s in specs: cmd += ["--decor-spec", s]
    out = lance(cmd, log=os.path.join(a.sortie, "injection_fork.log"))
    print("\n".join(l for l in out.splitlines() if l.startswith(("programme", "OK", "ECARTS"))))
    # 4. anneau
    if a.anneau:
        rom = os.path.join(a.sortie, "roms", "sfa3hx")
        im = image.lit(rom); i = anneau(im); image.ecrit(im, rom)
        print("  anneau scroll1 : table $%06X corrigee (FFC0 -> FFE0 en +0 et +8)" % i)
    # 5. archive FBNeo
    if a.zip:
        os.makedirs(os.path.join(a.sortie, "fbneo"), exist_ok=True)
        lance([PY, "-W", "ignore", os.path.join(HERE, "py/paquet_decor.py"), os.path.join(a.sortie, "roms/sfa3hx"),
               os.path.join(a.sortie, "ext"), os.path.join(a.sortie, "hsfa_plans_decor.bin"),
               os.path.join(a.sortie, "fbneo", "sfa3hsfa.zip")])
    print("FIN : HSFA_PLANS=300,340,3a0 HSFA_EXT=%s HSFA_GFX=%s@3000000 cps2f sfa3hx -rompath %s" % (
        os.path.join(a.sortie, "ext"), os.path.join(a.sortie, "hsfa_plans_decor.bin"), os.path.join(a.sortie, "roms")))


if __name__ == "__main__":
    main()
