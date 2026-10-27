#!/usr/bin/env python3
"""Donnees de la REDIRECTION PAR LE PROGRAMME TRADUIT (SON-HYPER-ROM.md §13) : voix d'origine par version d'Hyper.

  gen_redirection.py [--module RO9] [--ids ids_102.tsv] [--correspondance correspondance.tsv] [--sortie DIR]
                     [--table-rejeu TABLE [--table-sortie FICHIER]] [--voix-arcade TSV|non] [--base E70000]

Entrees (le depot ne contient que des tables : identifiants, adresses, correspondances) :
  --module         module ro9 DECOMPRESSE, extrait de l'ISO de l'utilisateur (hsfa_build.py : cache/anthology_extract/
                   decompressed/ro9_usa_prog68k.bin ; defaut $HSFA_MODULE_RO9) : table de pointeurs 0x6AE614, tables $E6,
                   T_5c9a90, T_5c9a40, et les mots MIPS corriges ;
  --ids            ids_102.tsv (versions d'Hyper : id $102, famille, perso de base, nom ; INDEX-HYPER.md) ;
  --correspondance correspondance.tsv (code SFA3 du bloc du perso de base -> commande source SFA1 / SFA2 et decision,
                   §5) ; le catalogue/correspondance.json d'origine (memes 695 lignes) est encore accepte ;
  --voix-arcade    voix_arcade.tsv (voix « par pas » mesurees sur l'arcade, 2026-10-16) ; « non » pour s'en passer.
                   La livraison v151 a ete construite SANS (le paquet applique ces voix ensuite : corrige_voix.py) :
                   hsfa_build.py passe « non ».
Le nombre d'entrees de chaque table $E6 est relu dans le module (meme regle que tables_hyper.py) : plus besoin de
catalogue/tables_hyper.json.

Nouveau code d'un son remplace (voie du rejeu, gen_rejeu.py) : $2000 + commande SFA1 (cote 1), $3000 + commande SFA2 ;
le 68K ajoute $500 cote 2 (=> $2500 + c / $3500 + c, definis par gen_rejeu.py).

Sorties (--sortie, defaut redirection_68k/ a cote de ce script) :
  donnees.bin   : bloc a ajouter aux donnees du module (mots LE, format du module), a l'adresse d'execution BASE
                  (HSFA_BASE / --base, defaut 0xE70000 : plage d'execution libre, hors du module et de sa RAM, que le
                  traducteur sert a la suite du bloc externe de fin des donnees, cf. SON-HYPER-ROM.md §13) :
                    +0x000 T_CRIS_V[128] (mots) : base des cris par version ($4000 + 8 v si redirigee, sinon la valeur
                           d'origine T_5c9a90[perso de base], $7E : T_5c9a90[38])
                    +0x100 T_V2_V[128]   (mots) : code du son « $08C274 » par version (code de rejeu si redirige, sinon
                           T_5c9a40[perso de base], $7E : T_5c9a40[38])
                    +0x200 tables $E6 par version (80 entrees de 8 o = copie de la zone d'origine, codes remplaces dans
                           les entrees de la table), une seule copie par contenu
                  Il contient des copies de zones du module : il est REGENERE a chaque construction depuis l'ISO de
                  l'utilisateur et n'est jamais publie.
  ro9_usa_prog68k_son.bin : module corrige (correctif_module.tsv applique ; en-tete inchange). Idem : jamais publie.
  correctif_module.tsv, pointeurs.tsv, donnees.json : listes de controle.
  cris_par_version.txt : section « cris par version » de la table du rejeu (REF / ALIAS des codes $4000 + 8 v + n et
                  $4500 + 8 v + n).
  redirection_rejeu.txt : « version code_SFA3 nouveau » pour le banc Lua (lua/redirection.lua, REDIR_REJEU=1).
  --table-rejeu T : la section des cris de T est remplacee par cris_par_version.txt, resultat dans --table-sortie
                  (defaut : T lui-meme).
"""
import argparse, os, sys, json, csv, struct
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
from gen_rejeu import cote2
MOD = os.environ.get("HSFA_MODULE_RO9", "<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin")
B = 0x1F0000
BASE = int(os.environ.get("HSFA_BASE", "E70000"), 16)   # hors du module ET de sa RAM (cf. §13 : pas a la suite des donnees)
FAM = {"ZERO": "sfa1", "ZERO 2": "sfa2", "ZERO 2 ALPHA": "sfa2"}
CB = {"sfa1": 0x2000, "sfa2": 0x3000}
NENT = 80
CRIS_N = (0, 1, 2, 3, 4, 5, 6)
SECTION_CRIS = "# --- cris par version (gen_redirection.py)"


def lit_correspondance(chemin):
    """[{jeu, base (int), code, src, decision}] depuis correspondance.tsv (ou l'ancien correspondance.json)"""
    if chemin.endswith(".json"):
        return json.load(open(chemin))
    return [dict(jeu=r["source"].lower(), base=int(r["base"], 16), code=r["code_SFA3"], src=r["code_source"],
                 decision=r["decision"]) for r in csv.DictReader(open(chemin, encoding="utf-8"), delimiter="\t")]


def lit_voix_arcade(chemin):
    """voix « par pas » mesurees sur l'arcade (marque_voix.py, fusionne_voix_arcade.py) : statut a_corriger / voix_SFA3"""
    if not chemin or chemin == "non" or not os.path.exists(chemin):
        return {}
    return {(r["jeu"], int(r["base"], 16), int(r["code_SFA3"], 16)): int(r["arcade"], 16)
            for r in csv.DictReader(open(chemin, encoding="utf-8"), delimiter="\t")
            if r["statut"] in ("a_corriger", "voix_SFA3")}


def nb_codes(d, p):
    """nombre d'entrees de la table $E6 en p (exec) : regle de tables_hyper.py"""
    o, n = p - B, 0
    for k in range(80):
        c, a, z1, z2 = struct.unpack_from("<4H", d, o + 8 * k)
        if z1 or z2 or not (c == 0 or 0x200 <= c <= 0x6ff) or not (a == 0 or 0x200 <= a <= 0x6ff): break
        n += 1
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description="redirection des voix d'Hyper par version (SON-HYPER-ROM.md §13)")
    ap.add_argument("--module", default=MOD)
    ap.add_argument("--ids", default=os.path.join(ICI, "ids_102.tsv"))
    ap.add_argument("--correspondance", default=os.path.join(ICI, "correspondance.tsv"))
    ap.add_argument("--voix-arcade", default=os.path.join(ICI, "voix_arcade.tsv"))
    ap.add_argument("--sortie", default=os.path.join(ICI, "redirection_68k"))
    ap.add_argument("--table-rejeu", help="hsfa_rejeu_table.txt dont remplacer la section des cris")
    ap.add_argument("--table-sortie", help="table complete ecrite ici (defaut : --table-rejeu lui-meme)")
    ap.add_argument("--base", default="%X" % BASE, help="adresse d'execution du bloc (hexa, 6 chiffres)")
    a = ap.parse_args(argv)
    base = int(a.base, 16)
    d = open(a.module, "rb").read()
    w = lambda x: struct.unpack_from("<H", d, x - B)[0]
    P1 = [struct.unpack_from("<I", d, 0x6AE614 - B + 4 * i)[0] for i in range(128)]
    P2 = [struct.unpack_from("<I", d, 0x6AE814 - B + 4 * i)[0] for i in range(128)]
    bornes = sorted(set(P1 + P2) - {0xFFFFFFFF})
    corr = lit_correspondance(a.correspondance)
    VOIX_ARCADE = lit_voix_arcade(a.voix_arcade)
    ids = list(csv.DictReader(open(a.ids, encoding="utf-8"), delimiter="\t"))
    T90 = [w(0x5C9A90 + 2 * i) for i in range(40)]
    T40 = [w(0x5C9A40 + 2 * i) for i in range(40)]
    # tables COMPLETES (128 versions) : valeur d'origine T_5c9a90 / T_5c9a40 [perso de base] ($7E : entree 38) pour
    # les versions non redirigees -> utilisables telles quelles par le correctif MIPS minimal (index $102 sans repli)
    cris_v, v2_v = [0] * 128, [0] * 128
    for row in ids:
        v = int(row["id"][1:], 16)
        bb = int(row["base"][1:], 16) if row["base"].startswith("$") else 0
        cris_v[v] = T90[38] if v == 0x7E else T90[bb]; v2_v[v] = T40[38] if v == 0x7E else T40[bb]
    tables, contenus, info, rej, cris_lignes = [], {}, {}, [], []
    for row in ids:
        v = int(row["id"][1:], 16); fam = row["version"].strip(); jeu = FAM.get(fam)
        if not jeu or not row["base"].startswith("$"): continue
        b = int(row["base"][1:], 16)
        M = {int(r["code"], 16): CB[jeu] + int(r["src"], 16) for r in corr
             if r["jeu"] == jeu and r["base"] == b and r["decision"] in ("voix", "cri", "ko")}
        for (j_, b_, c3), x in VOIX_ARCADE.items():       # voix mesurees sur l'arcade (2026-10-16) : priment
            if j_ == jeu and b_ == b: M[c3] = CB[jeu] + x
        if not M: continue
        for c, n in sorted(M.items()): rej.append("%02x %04x %04x" % (v, c, n))
        # --- table $E6
        p = P1[v]
        nh = nb_codes(d, p)
        suiv = [q for q in bornes if q > p]
        nt = min(nh, (suiv[0] - p) // 8) if suiv else nh
        zone = bytearray(d[p - B:p - B + 8 * NENT])
        nrep = 0
        for k in range(nt):
            for m in (0, 1):
                c = struct.unpack_from("<H", zone, 8 * k + 2 * m)[0]
                if c in M: struct.pack_into("<H", zone, 8 * k + 2 * m, M[c]); nrep += 1
        iv = dict(famille=fam, nom=row["nom"], base=b, jeu=jeu, table_origine="%06X" % p, entrees=nt, codes_table_remplaces=nrep)
        if nrep:
            z = bytes(zone)
            if z not in contenus: contenus[z] = len(tables); tables.append(z)
            iv["table"] = contenus[z]
        # --- cris : base + n ; son de T_5c9a40
        bc = T90[38] if v == 0x7E else T90[b] if b < 40 else 0
        if bc and any(bc + n in M for n in CRIS_N):
            nb = 0x4000 + 8 * v
            cris_v[v] = nb
            for n in CRIS_N:
                c = bc + n
                if c in M:
                    s2 = CB[jeu] + cote2(jeu, M[c] - CB[jeu])          # cible finale (CODE) du cote 2
                    cris_lignes += ["REF %04X %04X" % (nb + n, M[c]), "REF %04X %04X" % (nb + 0x500 + n, s2)]
                else:
                    cris_lignes += ["ALIAS %04X %04X" % (nb + n, c), "ALIAS %04X %04X" % (nb + 0x500 + n, c + 0x500)]
            iv["cris"] = dict(base_origine="%04X" % bc, nouvelle_base="%04X" % nb,
                              remplaces=["%04X->%04X" % (bc + n, M[bc + n]) for n in CRIS_N if bc + n in M])
        c2 = T40[38] if v == 0x7E else T40[b] if b < 40 else 0
        if c2 in M:
            v2_v[v] = M[c2]; iv["son_08C274"] = "%04X->%04X" % (c2, M[c2])
        info["%02X" % v] = iv
    out = a.sortie; os.makedirs(out, exist_ok=True)
    blob = bytearray(struct.pack("<128H", *cris_v) + struct.pack("<128H", *v2_v))
    for z in tables: blob += z
    open(os.path.join(out, "donnees.bin"), "wb").write(blob)
    tsv = ["version\tnom\tpointeur_origine\tnouveau_pointeur"]
    for k, iv in sorted(info.items()):
        if "table" in iv:
            np_ = base + 0x200 + 8 * NENT * iv["table"]
            iv["nouveau_pointeur"] = "%06X" % np_
            tsv.append("%s\t%s\t%s\t%06X" % (k, iv["nom"], iv["table_origine"], np_))
    open(os.path.join(out, "pointeurs.tsv"), "w").write("\n".join(tsv) + "\n")
    json.dump(dict(base_exec="%06X" % base, taille=len(blob), t_cris_v="%06X" % base, t_v2_v="%06X" % (base + 0x100),
                   tables="%06X" % (base + 0x200), taille_table=8 * NENT, nb_tables=len(tables), versions=info),
              open(os.path.join(out, "donnees.json"), "w"), indent=1)

    # --- correctif du module (variante « au niveau du module », avant traduction) : 8 mots MIPS, 62 pointeurs, en-tete
    def mot(x): return struct.unpack_from("<I", d, x)[0]
    def hi_lo(x):
        lo = x & 0xFFFF; hi = (x >> 16) + (1 if lo >= 0x8000 else 0)
        return hi & 0xFFFF, lo
    corr_m = []
    for nom, lb, cmp7e, lui, t_old, t_new in (
            ("cris $08C2AE (mips 0x38A760)", 0x38A788, 0x38A794, 0x38A898, 0x5C9A90, base),
            ("son $08C274 (mips 0x38A540)", 0x38A57C, 0x38A588, 0x38A68C, 0x5C9A40, base + 0x100)):
        o = mot(lb); assert o & 0xFFFF == 0x116 and (o >> 26) == 0x20, hex(o)
        corr_m.append((lb, o, (o & 0xFFFF0000) | 0x102, nom + " : lb ...,$116 (perso de base) -> lb ...,$102 (version)"))
        o = mot(cmp7e); assert o & 0xFFFF == 0x7E, hex(o)
        corr_m.append((cmp7e, o, (o & 0xFFFF0000) | 0x80, nom + " : cas Cammy ALPHA ($7E -> indice 38) neutralise (une version vaut <= $7F)"))
        o1, o2 = mot(lui), mot(lui + 4)
        assert (o1 >> 26) == 0x0F and (o2 >> 26) == 0x09 and ((o1 & 0xFFFF) << 16) + ((o2 & 0xFFFF) - ((o2 & 0x8000) << 1)) == t_old
        h, l = hi_lo(t_new)
        corr_m.append((lui, o1, (o1 & 0xFFFF0000) | h, nom + " : lui (table %06X -> %06X)" % (t_old, t_new)))
        corr_m.append((lui + 4, o2, (o2 & 0xFFFF0000) | l, nom + " : addiu (table %06X -> %06X)" % (t_old, t_new)))
    lignes_c = ["decalage_fichier\tancien_mot\tnouveau_mot\trole"]
    lignes_c += ["%06X\t%08X\t%08X\t%s" % x for x in corr_m]
    for k, iv in sorted(info.items()):
        if "table" in iv:
            x = 0x6AE614 - B + 4 * int(k, 16)
            lignes_c.append("%06X\t%08X\t%08X\tpointeur $E6 de la version $%s (%s)" % (x, mot(x), int(iv["nouveau_pointeur"], 16), k, iv["nom"]))
    open(os.path.join(out, "correctif_module.tsv"), "w").write("\n".join(lignes_c) + "\n")
    m = bytearray(d)
    for l in lignes_c[1:]:
        t = l.split("\t"); struct.pack_into("<I", m, int(t[0], 16), int(t[2], 16))
    # le bloc donnees.bin n'est PAS ajoute au fichier : l'en-tete (mot 6 = fin des donnees) fixe aussi la RAM du portage
    open(os.path.join(out, "ro9_usa_prog68k_son.bin"), "wb").write(m)
    # --- section de la table de rejeu
    open(os.path.join(out, "cris_par_version.txt"), "w").write("\n".join([SECTION_CRIS] + cris_lignes) + "\n")
    if a.table_rejeu:
        L = open(a.table_rejeu).read().split("\n")
        if SECTION_CRIS in L: L = L[:L.index(SECTION_CRIS)]
        while L and not L[-1]: L.pop()
        L += [SECTION_CRIS] + cris_lignes
        open(a.table_sortie or a.table_rejeu, "w").write("\n".join(L) + "\n")
    open(os.path.join(out, "redirection_rejeu.txt"), "w").write(
        "# version($102) code_SFA3(cote 1) code_rejeu (cote 2 : code + $500 -> code_rejeu + $500)\n" + "\n".join(rej) + "\n")
    nv = sum(1 for iv in info.values() if "table" in iv)
    print("versions redirigees : %d (tables $E6 : %d, contenus distincts %d) ; cris : %d versions ; son $08C274 : %d ; "
          "bloc %d o a l'exec %06X ; %d lignes de redirection (banc Lua) ; voix d'arcade : %d" %
          (len(info), nv, len(tables), sum(1 for x in cris_v if x >= 0x4000), sum(1 for x in v2_v if x >= 0x2000), len(blob),
           base, len(rej), len(VOIX_ARCADE)))


if __name__ == "__main__":
    main()
