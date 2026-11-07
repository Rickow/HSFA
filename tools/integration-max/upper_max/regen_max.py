#!/usr/bin/env python3
"""regen_max.py -- (script_uppermax) régénération du cache MAX « v2 étirée » (converti/, fork/, s/, sources .s de
rosette_code) depuis l'ISO PSP EU et les sorties de hsfa_build, avec les outils PUBLIÉS de max/ et tools/max/.
Remplace regen_max.sh (bash) : même ordre d'étapes (pièges : RAPPORT §5), plus les « compléments » (scripts de fin,
jeux de palettes de fin, portraits de victoire, sauts / physique, parcours) et SANS programme d'arcade par défaut.

  python3 regen_max.py --dest R --sortie S --psp-iso ISO --depot DEPOT --gfx DOSSIER_GFX
                       [--parcours TABLE] [--traduire-acteurs FICHIER] [--sfa3ud DOSSIER] [--python PY]

  S       : sortie de hsfa_build (cache/psp/BOOT.BIN, cache/anims, cache/iso/X_DATA.BIN, cache/anthology_extract,
            travail/mame_ro5)
  DEPOT   : copie du dépôt (max/, tools/max/, src/hsfa/) ; recopiée dans R/depot (les outils écrivent à côté d'eux)
  --gfx   : dossier de la ROM graphique de SFA3 (sz3.13m-20m) que hsfa_build a mise dans cache/arcade/sfa3ud
            (reconstruite depuis l'ISO, ou --arcade)
  --sfa3ud: (DÉVELOPPEMENT) programme d'arcade du jeu MAME sfa3ud : refait aussi l'APPRENTISSAGE (Rosette du code,
            acteurs) au lieu de lire les tables apprises versionnées (rosette_code/*.json, rosette_donnees_appris.json)
  --traduire-acteurs : traduire.py à employer pour s/acteurs_fins_max.s (état 2b31 : traduire.py de max/ en d98c4f1)
Sans ISO PSP rien n'est fait ici. Les sorties sont dans R ; HOME = R/home (plusieurs outils écrivent « ~/.cache/sfa3max »
en dur) ; tous les sous-processus héritent de l'environnement donné plus les variables SFA3MAX_*.
"""
import argparse, json, os, shutil, struct, subprocess, sys, time, zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "..", "max"))       # tools/max du dépôt (iso_psp.py)
sys.path.insert(0, ICI)
import iso_psp

PRG = "sz3ud.03c sz3ud.04c sz3.05c sz3.06c sz3.07c sz3.08c sz3.09c sz3.10b".split()
GFX = ["sz3.%dm" % k for k in range(13, 21)]
HABILLAGE = ["palettes_max.py", "palettes_ingrid_upper.py", "textes_max.py", "portraits_max.py", "citations_max.py",
             "noms_max.py", "hud_max.py", "hud_noms_max.py", "fins_max.py", "bio_max.py", "prologue_max.py",
             "apercu_selection_max.py", "icones_max.py", "bandeau_noms_max.py", "frises_verticales_max.py",
             "carte_noms_max.py", "winner_noms_max.py", "portraits_fork.py"]
# Rosette du code : (outil, besoin du programme d'arcade). Sans lui, les sorties apprises sont celles versionnées dans
# max/outils/rosette_code (api_arcade_psp.json, champs_votes.json, tailles68.json, carte_champs.json, api_acteurs.json) ;
# evaluer / mouvements / champs_projectiles n'ont pas de sortie lue par la construction.
ROSETTE = [("frames_max.py", 0), ("anims_max.py", 0), ("tout.py", 1), ("tailles68.py", 1), ("arite.py", 0),
           ("evaluer.py", 1), ("tables_explicites.py", 0), ("brouillons.py", 0), ("projectiles_max.py", 0),
           ("brouillons.py", 0), ("mouvements.py", 1), ("champs_projectiles.py", 1), ("sons_pas_max.py", 0),
           ("appris_acteurs.py", 1), ("acteurs_fins.py", 0), ("anims_fins_max.py", 0), ("decor_fins_max.py", 0),
           ("sauts_max.py", 0)]
COPIES_S = ["brouillon_eagle", "brouillon_maki", "brouillon_yun", "brouillon_ingrid", "moteur_max_auto", "moteur_max_main",
            "frames_eagle", "frames_maki", "frames_yun", "frames_ingrid", "symboles_frames_max", "acteurs_fins_max"]
NOMS_ID = {0x03: "KEN", 0x07: "GUY", 0x09: "ROSE", 0x0A: "M.BISON", 0x0B: "SAGAT", 0x0D: "SAKURA", 0x15: "BALROG",
           0x17: "EVIL RYU", 0x20: "GUILE", 0x21: "FEI-LONG", 0x22: "DEE JAY"}
RIVAL, BOSS, RANG5 = 0x20A784, 0x20A7AE, 0x20A7D8   # EBOOT (image) : octet par id PSP (parcours Arcade, rangs 9, 10, 5)


class Regen:
    def __init__(s, a):
        s.a = a; s.R = os.path.abspath(a.dest); s.S = os.path.abspath(a.sortie); s.py = a.python
        s.O = os.path.join(s.R, "depot", "max", "outils"); s.journal = []
        s.eboot = os.path.join(s.S, "cache", "psp", "BOOT.BIN")
        s.hsfa_gfx = os.path.join(s.S, "travail", "mame_ro5", "hsfa_gfx.bin")

    def log(s, m):
        l = "%s %s" % (time.strftime("%H:%M:%S"), m); print(l, flush=True); s.journal.append(l)

    def env(s, **k):
        R = s.R
        e = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HOME=os.path.join(R, "home"), SFA3MAX_CACHE=R,
                 SFA3MAX_PAC_DIR=os.path.join(R, "psp", "pac"), SFA3MAX_EBOOT=s.eboot,
                 SFA3MAX_EFCT_DIR=os.path.join(R, "psp", "data"), SFA3MAX_ISO=os.path.abspath(s.a.psp_iso),
                 SFA3_ZIP=os.path.join(R, "sfa3_gfx.zip"), ANTHOLOGY_DIR=os.path.join(s.S, "cache", "anthology_extract"),
                 HSFA_WORK=os.path.join(R, "work"), HSFA_GFX=s.hsfa_gfx,
                 SFA3MAX_ETIRE="pl26,pl27,pl28,pl29")
        pp = [os.path.join(R, "depot", "tools", "max")] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])
        e["PYTHONPATH"] = os.pathsep.join(pp); e.update(k); return e

    def etape(s, dossier, args, nom=None, env=None, cwd=None, echec_admis=False):
        nom = nom or "_".join([os.path.splitext(args[0])[0]] + [x.replace("/", "_") for x in args[1:]])
        j = os.path.join(s.R, "journaux", nom + ".log"); t = time.time()
        with open(j, "w") as f:
            r = subprocess.run([s.py] + args, cwd=cwd or os.path.join(s.O, dossier), env=env or s.env(), stdout=f, stderr=subprocess.STDOUT)
        der = open(j, errors="replace").read().strip().splitlines()[-1:] or [""]
        s.log("%s/%s : code %d (%.0f s) %s" % (dossier, " ".join(args), r.returncode, time.time() - t, der[0][:110]))
        if r.returncode and not echec_admis: raise SystemExit("regen_max : échec de %s %s (journal %s)" % (dossier, " ".join(args), j))

    def preparer(s):
        R, S = s.R, s.S
        for d in ("journaux", "home/.cache", "work/cps2/anims", "work/xdata", "psp/pac", "psp/data/textes"):
            os.makedirs(os.path.join(R, d), exist_ok=True)
        lien = lambda cible, l: os.path.lexists(l) or os.symlink(cible, l)
        lien(R, os.path.join(R, "home", ".cache", "sfa3max"))
        lien(os.path.join(R, "psp", "pac"), os.path.join(R, "pac")); lien(os.path.join(R, "psp", "data"), os.path.join(R, "data"))
        if os.path.exists(os.path.join(R, "depot")): shutil.rmtree(os.path.join(R, "depot"))
        for sous in ("max", os.path.join("tools", "max"), os.path.join("src", "hsfa")):
            shutil.copytree(os.path.join(s.a.depot, sous), os.path.join(R, "depot", sous),
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # données PSP : DATA de l'ISO (minuscules ; plXX_e.pac -> pac/, le reste -> data/ et data/textes/)
        L = iso_psp.liste(s.a.psp_iso, "PSP_GAME/USRDIR/EUR/DATA")
        for nom in sorted(L):
            low = nom.lower(); sous = "pac" if low.startswith("pl") and low.endswith("_e.pac") else "data"
            p = os.path.join(R, "psp", sous, low)
            if not os.path.exists(p): open(p, "wb").write(iso_psp.lit(s.a.psp_iso, "PSP_GAME/USRDIR/EUR/DATA/" + nom))
            if sous == "data": lien("../" + low, os.path.join(R, "psp", "data", "textes", low))
        s.log("données PSP : %d fichiers de DATA" % len(L))
        for f in sorted(os.listdir(os.path.join(S, "cache", "anims"))):
            if f.endswith(".bin") and not os.path.exists(os.path.join(R, "work", "cps2", "anims", f)):
                shutil.copyfile(os.path.join(S, "cache", "anims", f), os.path.join(R, "work", "cps2", "anims", f))
        lien(os.path.join(S, "travail", "mame_ro5"), os.path.join(R, "work", "mame_ro5"))
        lien(os.path.join(S, "cache", "iso", "X_DATA.BIN"), os.path.join(R, "work", "xdata", "X_DATA.BIN"))
        # anim f289 (X_DATA) : hsfa_build ne la produit pas
        code = ("import assets_natifs as A; A.EXTRACT=%r; A.CACHE=A.CACHE_ECRIT=%r; A.fichier(289)"
                % (os.path.join(S, "cache", "anthology_extract"), os.path.join(R, "work", "cps2", "anims")))
        subprocess.run([s.py, "-c", code], cwd=os.path.join(R, "depot", "src", "hsfa"), check=True,
                       env=s.env(XDATA=os.path.join(S, "cache", "iso", "X_DATA.BIN")), stdout=subprocess.DEVNULL)
        # tuiles d'Upper (HSFA_GFX) : les outils MAX numérotent les tuiles neuves à partir de $40000 + tuiles d'Upper ;
        # l'intégration et le paquet les placent en G_MAX (max_cache.py, $4DAAB = arcade). En voie ISO seule, Upper a
        # moins de tuiles propres (celles de l'Anthology sont dans la ROM reconstruite) : on complète de tuiles nulles
        # jusqu'à G_MAX, sans quoi les codes MAX tombent à côté (07/11 : $4D872 au lieu de $4DAAB).
        if s.a.g_max:
            g = int(s.a.g_max, 16); up = open(s.hsfa_gfx, "rb").read(); n = len(up) // 128
            if n > g - 0x40000: raise SystemExit("hsfa_gfx d'Upper : %d tuiles > G_MAX $%X" % (n, g))
            s.hsfa_gfx = os.path.join(R, "hsfa_gfx_upper.bin")
            open(s.hsfa_gfx, "wb").write(up + bytes(128 * (g - 0x40000 - n)))
            s.log("tuiles d'Upper : %d (+ %d nulles jusqu'à G_MAX $%X)" % (n, g - 0x40000 - n, g))
        # ROM graphique de SFA3 (gfx_fork : dédoublonnage des tuiles) ; programme d'arcade seulement avec --sfa3ud
        z = os.path.join(R, "sfa3_gfx.zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as Z:
            for n in GFX: Z.write(os.path.join(s.a.gfx, n), n)
        if s.a.sfa3ud:
            d = b"".join(open(os.path.join(s.a.sfa3ud, f), "rb").read() for f in PRG)
            b = bytearray(d); b[0::2], b[1::2] = d[1::2], d[0::2]
            for p in ("work/cps2/sfa3_prog.bin", "work/cps2/sfa3ud_prog.bin", "sfa3ud_donnees.bin"):
                open(os.path.join(R, p), "wb").write(b)
            s.log("DÉVELOPPEMENT : programme d'arcade sfa3ud fourni (apprentissage refait)")

    def parcours(s):
        """converti/arcade/parcours_max.json : tirage relevé (table de décision, ids) + rang 5, rival, boss de l'EBOOT"""
        img = open(s.eboot, "rb").read()[0x74:]; T = json.load(open(s.a.parcours)); out = {}
        nom = lambda i: "%02x %s" % (i, NOMS_ID.get(i, "?"))
        for cle, d in T.items():
            if cle.startswith("_"): continue
            pid = int(d["id_psp"], 16); rel = [int(x, 16) for x in d["releve_psp"]]
            if rel[-1] != img[BOSS + pid]: raise SystemExit("parcours %s : boss %02x <> EBOOT %02x" % (cle, rel[-1], img[BOSS + pid]))
            e = {"releve_psp": d["releve_psp"], "rang5": nom(img[RANG5 + pid]), "rang9": nom(img[RIVAL + pid])}
            if d.get("combat_secret"): e["combat_secret"] = nom(int(d["combat_secret"], 16))
            e["boss"] = nom(img[BOSS + pid]); out[cle] = e
        os.makedirs(os.path.join(s.R, "converti", "arcade"), exist_ok=True)
        json.dump(out, open(os.path.join(s.R, "converti", "arcade", "parcours_max.json"), "w"), indent=1)
        s.log("parcours Arcade : %s" % ", ".join(out))

    def acteurs_2b31(s):
        """s/acteurs_fins_max.s de l'état 2b31 : acteurs_fins.py actuel avec un autre traduire.py (copie temporaire)"""
        RC = os.path.join(s.O, "rosette_code"); T = os.path.join(s.R, "acteurs_2b31")
        if os.path.exists(T): shutil.rmtree(T)
        shutil.copytree(os.path.join(s.R, "depot"), T, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(s.a.traduire_acteurs, os.path.join(T, "max", "outils", "rosette_code", "traduire.py"))
        s.etape("rosette_code", ["acteurs_fins.py"], nom="acteurs_fins_2b31", cwd=os.path.join(T, "max", "outils", "rosette_code"))
        shutil.copyfile(os.path.join(T, "max", "outils", "rosette_code", "acteurs_fins_max.s"), os.path.join(s.R, "s", "acteurs_fins_max.s"))
        shutil.rmtree(T)

    def lancer(s):
        t0 = time.time(); s.preparer(); arc = bool(s.a.sfa3ud)
        s.etape("convert", ["convert_max.py", "pl26", "pl27", "pl29"])
        # Yun d'abord SANS l'onde d'efct (gfx_fork la voit sans), puis convert pl28 + efct_fork (ordre de l'atelier)
        s.etape("convert", ["-c", "import convert_max as C; C.EFCT = {}; C.export('pl28')"], nom="convert_pl28_sans_efct")
        s.etape("convert", ["gfx_fork.py"])
        for o in HABILLAGE:     # noms_max.py : 1er passage en échec (dossier noms/ absent), comme dans l'atelier
            s.etape("convert", [o], echec_admis=(o == "noms_max.py"))
        s.etape("convert", ["noms_max.py"], nom="noms_max_2")              # 1er passage : dossier noms/ absent
        s.etape("convert", ["portraits_fork.py"], nom="portraits_fork_2")  # APRÈS l'habillage
        for o in ("bandeau_noms_max.py", "carte_noms_max.py", "winner_noms_max.py"): s.etape("convert", [o, "source"])
        for o in ("recul_max.py", "flammes_max.py", "tables_id_max.py", "ia_max.py", "dialogues_max.py"): s.etape("convert", [o])
        s.etape("convert", ["convert_max.py", "pl28"]); s.etape("convert", ["efct_fork.py", "pl28"])
        for o, besoin in ROSETTE:
            if besoin and not arc: continue
            s.etape("rosette_code", [o])
        if arc: s.etape("convert", ["rosette_donnees.py", "acteurs"])
        s.etape("convert", ["rosette_donnees.py", "acteurs_max"])
        s.etape("convert", ["projections_max.py"]); s.etape("convert", ["projections_max.py", "natifs"])
        # compléments (07/11) : jeux de palettes et scripts des fins
        s.etape("convert", ["jeux_palettes_fin.py"]); s.etape("convert", ["convertir_fin.py", "ecrire"])
        os.makedirs(os.path.join(s.R, "s"), exist_ok=True)
        for f in COPIES_S: shutil.copyfile(os.path.join(s.O, "rosette_code", f + ".s"), os.path.join(s.R, "s", f + ".s"))
        if s.a.traduire_acteurs: s.acteurs_2b31()
        if s.a.parcours: s.parcours()
        s.log("régénération : %.0f s" % (time.time() - t0))


def main():
    ap = argparse.ArgumentParser()
    for k in ("dest", "sortie", "psp_iso", "depot", "gfx"): ap.add_argument("--" + k.replace("_", "-"), required=True)
    ap.add_argument("--parcours"); ap.add_argument("--traduire-acteurs"); ap.add_argument("--sfa3ud")
    ap.add_argument("--g-max", help="code (hex) de la 1re tuile MAX dans la région graphique (max_cache.G_MAX, état 2b31 : 4DAAB)")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    Regen(a).lancer()


if __name__ == "__main__":
    main()
