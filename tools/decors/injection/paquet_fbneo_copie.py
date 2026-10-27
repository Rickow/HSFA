#!/usr/bin/env python3
"""Construit les archives de jeu du coeur FBNeo HSFA (pilotes sfa3hsfa et sfa3uhsfa) a partir du dossier de travail.

Reproduit le banc MAME du projet :
  - ROM programme traduite (8 x 512 Ko, mots echanges) : roms_tr/sfa3ud (SFA3), mame_ro5/roms_ro5/sfa3ud (Upper) ;
  - hsfa_ext.bin  : image de $A00000-$EFFFFF (5 Mo) avec les blocs ext_<adresse>.bin que sert banc_mem.lua
                    (bases fixes + ext_liste.txt du dossier du module), mots echanges comme la ROM programme ;
  - hsfa_tab.bin  : tables de banc_sprites.lua / banc_plans.lua (f<N>.bin, plan1, plan2, f312, carte.txt)
                    + parametres (banque commune, pointeur d'animation, fichier de l'intro, bases des plans) ;
  - hsfa_gfx.bin  : (Upper) region graphique $2000000-$3FFFFFF au format interne MAME : hsfa_gfx.bin en +0,
                    hsfa_plans.bin en +$1000000 (= HSFA_GFX=...hsfa_gfx.bin,...hsfa_plans.bin@3000000) ;
  - son : ROM d'origine de SFA3 (sfa3hsfa) ou ROM hybride d'Upper hx3.* (sfa3uhsfa, QSound 16 Mo) ;
  - ROM graphique sz3.13m-20m et cle phoenix.key de sfa3ud.
Les archives (donnees de jeu) restent dans le dossier de sortie, jamais dans un depot.

Usage : python3 paquet_fbneo.py [sfa3|upper ...]   (defaut : les deux)
Variables : HSFA_WORK (dossier work, defaut : dossier parent de ce script), HSFA_SORTIE (defaut : dossier du script).
"""
import hashlib, os, struct, sys, time, zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("HSFA_WORK", os.path.dirname(ICI))
SORTIE = os.environ.get("HSFA_SORTIE", ICI)

EXT_BASE, EXT_LEN = 0xA00000, 0x500000
TAB_LEN = 0x400000
GFX_LEN = 0x2000000
# bases fixes de banc_mem.lua (puis celles de ext_liste.txt)
EXT_FIXES = ["a04000", "b00000", "b40000", "b80000", "bc0000", "b04000", "c80000", "d40000", "d80000", "dc0000", "e00000"]
PRG = ["sz3ud.03c", "sz3ud.04c", "sz3.05c", "sz3.06c", "sz3.07c", "sz3.08c", "sz3.09c", "sz3.10b"]
GFX = ["sz3.13m", "sz3.15m", "sz3.17m", "sz3.19m", "sz3.14m", "sz3.16m", "sz3.18m", "sz3.20m"]

JEUX = {
    "sfa3": dict(nom="sfa3hsfa", dossier="mame", roms="mame/roms_tr/sfa3ud", banques="mame/banques",
                 son=("mame/roms_tr/sfa3ud", ["sz3.01", "sz3.02", "sz3.11m", "sz3.12m"]),
                 config={"commun": "254", "ptr_anim": "FF3E48", "gfx_intro": "456"}, gfx=None),
    "upper": dict(nom="sfa3uhsfa", dossier="mame_ro5", roms="mame_ro5/roms_ro5/sfa3ud", banques="mame_ro5/banques_hx",
                  son=("agent_son_ro5/hybride/roms_hybride", ["hx3.01", "hx3.02", "hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"]),
                  config={"commun": "351", "ptr_anim": "FF40BC", "gfx_intro": "456", "plans": "300,340,3a0"},
                  gfx=[("mame_ro5/hsfa_gfx.bin", 0x0000000), ("mame_ro5/hsfa_plans.bin", 0x1000000)]),
}

journal = []

def lit(chemin):
    """lit un fichier (stable : relu si modifie pendant la lecture) et note md5 / date"""
    for _ in range(10):
        st = os.stat(chemin)
        d = open(chemin, "rb").read()
        if os.stat(chemin).st_mtime == st.st_mtime and len(d) == st.st_size:
            break
        time.sleep(2)
    else:
        raise SystemExit("fichier instable (reconstruction en cours ?) : " + chemin)
    rel = os.path.relpath(os.path.realpath(chemin), WORK) if os.path.realpath(chemin).startswith(WORK) else os.path.basename(chemin)
    journal.append("%s  %s  %s  %d" % (hashlib.md5(d).hexdigest(), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), rel, len(d)))
    return d

def echange(d):
    """mots gros-boutistes -> format ROM_LOAD16_WORD_SWAP (octets de chaque mot echanges)"""
    b = bytearray(d)
    b[0::2], b[1::2] = d[1::2], d[0::2]
    return bytes(b)

def image_ext(dossier):
    img = bytearray(EXT_LEN)
    pris = bytearray(EXT_LEN)
    bases = list(EXT_FIXES)
    lst = os.path.join(dossier, "ext_liste.txt")
    if os.path.exists(lst):
        for l in lit(lst).decode().split():
            if l and l not in bases:
                bases.append(l)
    n = 0
    for nom in bases:
        p = os.path.join(dossier, "ext_%s.bin" % nom)
        if not os.path.exists(p):
            continue
        d = lit(p)
        base = int(nom, 16)
        if base < EXT_BASE or base + len(d) > EXT_BASE + EXT_LEN:
            raise SystemExit("bloc hors de $A00000-$EFFFFF : %s ($%x, %d o)" % (p, base, len(d)))
        o = base - EXT_BASE
        if any(pris[o:o + len(d)]):
            print("  ATTENTION : %s chevauche un bloc precedent (le dernier l'emporte)" % p)
        img[o:o + len(d)] = d
        pris[o:o + len(d)] = b"\1" * len(d)
        print("  bloc $%06x : %d o" % (base, len(d)))
        n += 1
    if n == 0:
        raise SystemExit("aucun bloc ext_*.bin dans " + dossier)
    return echange(bytes(img))

def tables(dossier, config):
    ent = [("config", "".join("%s=%s\n" % kv for kv in config.items()).encode())]
    ent.append(("carte", lit(os.path.join(dossier, "carte.txt"))))
    for f in sorted(os.listdir(dossier)):
        if f.endswith(".bin"):
            nom = f[:-4]
            if len(nom) > 23:
                raise SystemExit("nom de table trop long : " + f)
            ent.append((nom, lit(os.path.join(dossier, f))))
    tete = bytearray(b"HSFATAB1" + struct.pack("<II", len(ent), 0))
    o = 16 + 32 * len(ent)
    corps = bytearray()
    for nom, d in ent:
        tete += nom.encode().ljust(24, b"\0") + struct.pack("<II", o + len(corps), len(d))
        corps += d
        corps += bytes((-len(corps)) % 4)
    blob = bytes(tete + corps)
    if len(blob) > TAB_LEN:
        raise SystemExit("tables : %d o > %d (agrandir hsfa_tab.bin dans le pilote)" % (len(blob), TAB_LEN))
    print("  tables : %d entrees, %d o" % (len(ent), len(blob)))
    return blob + bytes(TAB_LEN - len(blob))

def image_gfx(liste):
    img = bytearray(GFX_LEN)
    for rel, o in liste:
        d = lit(os.path.join(WORK, rel))
        if o + len(d) > GFX_LEN:
            raise SystemExit("%s depasse la region etendue" % rel)
        if o == 0 and len(d) > 0x1000000:
            print("  ATTENTION : hsfa_gfx.bin > 16 Mo, recouvert par hsfa_plans.bin en $3000000")
        img[o:o + len(d)] = d
        print("  %s -> $%07x (%d o)" % (rel, 0x2000000 + o, len(d)))
    return bytes(img)

def construit(cle):
    J = JEUX[cle]
    journal.clear()
    print("== %s (%s)" % (J["nom"], cle))
    roms = os.path.join(WORK, J["roms"])
    fichiers = []
    for f in PRG + GFX + ["phoenix.key"]:
        fichiers.append((f, lit(os.path.join(roms, f))))
    sd, sl = J["son"]
    for f in sl:
        fichiers.append((f, lit(os.path.join(WORK, sd, f))))
    fichiers.append(("hsfa_ext.bin", image_ext(os.path.join(WORK, J["dossier"]))))
    fichiers.append(("hsfa_tab.bin", tables(os.path.join(WORK, J["banques"]), J["config"])))
    if J["gfx"]:
        fichiers.append(("hsfa_gfx.bin", image_gfx(J["gfx"])))
    info = "Archive %s construite le %s par paquet_fbneo.py\nmd5  date  fichier source  taille\n%s\n" % (
        J["nom"], time.strftime("%Y-%m-%d %H:%M:%S"), "\n".join(journal))
    sortie = os.path.join(SORTIE, J["nom"] + ".zip")
    tmp = sortie + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f, d in fichiers:
            z.writestr(f, d)
        z.writestr("hsfa_info.txt", info)
    os.replace(tmp, sortie)
    open(os.path.join(SORTIE, J["nom"] + "_sources.txt"), "w").write(info)
    print("  -> %s (%.1f Mo)" % (sortie, os.path.getsize(sortie) / 2**20))

if __name__ == "__main__":
    for c in (sys.argv[1:] or ["sfa3", "upper"]):
        construit(c)
