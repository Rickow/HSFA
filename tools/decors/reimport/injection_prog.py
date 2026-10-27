#!/usr/bin/env python3
"""INJECTION PAR LES DONNEES DE DECOR (programme arcade sfa3ud) : a partir de la carte etendue produite par
reimport.py, fabrique les blocs de decor neufs et les listes modifiees (cf. REIMPORT.md §5-§6).

Pour chaque plan, les cases non d'origine (nouvelles / vides) sont rangees par position de bloc dans la liste du
decor (scroll1 : grille 4 x 2 blocs de 256 px, colonne bouclee modulo 4 par l'anneau ; scroll2 : 4 x 4 ; scroll3 :
8 x 8 — la tilemap boucle, donc l'extension droite au-dela de 1024 px retombe en colonne 0). Chaque position touchee
recoit un bloc NEUF = copie du bloc courant + cases nouvelles, a un numero LIBRE de la bibliotheque
(blocs_libres.json) ; scroll1 : super-tuiles neuves (dedoublonnees contre la bibliotheque) rangees dans la fin
libre de la ROM programme ($3C85D4+, indice 16 bits). La liste du decor est modifiee en place.

Sorties (dans --sortie) : prog_patch.json (adresse -> octets, programme 68000 en ordre naturel big-endian),
injection_prog.lua (pour essai_injection.lua), verification : recomposition des tilemaps depuis le programme corrige
= carte etendue (cases d'origine inchangees, cases nouvelles egales).
Usage : venv/bin/python reimport/injection_prog.py --sortie reimport/test_0C [--decor 0C]
"""
import os, sys, json, argparse, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import blocs as B
import numpy as np
import cpsenc as E

LIBRES = {1: [0x4B, 0x4C, 0x4D, 0x56, 0x5D], 2: [0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x82, 0x84],
          3: [0x8B, 0x8F] + list(range(0x91, 0x9F))}
NBX = {1: 4, 2: 4, 3: 8}; NT = {1: 32, 2: 16, 3: 8}; WT = {1: 128, 2: 64, 3: 64}; HT = {1: 64, 2: 64, 3: 64}
ST_LIBRE = 0x3C85D4                                  # 1re super-tuile alignee dans la fin $FF de la ROM ($3C8540-)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--decor", default="0C")
    ap.add_argument("--gfx", default=os.path.join(os.path.dirname(HERE), "gfx/gfx_region.bin"))
    ap.add_argument("--export", default=os.path.join(os.path.dirname(HERE), "out/decor0C_temple_cloche"))
    a = ap.parse_args()
    dec = int(a.decor, 16)
    prog = bytearray(open(B.PROG, "rb").read())
    orig = bytes(prog)
    ce = json.load(open(os.path.join(a.sortie, "carte_etendue.json")))
    patch = {}
    # region gfx corrigee + palettes (pour reconnaitre une case « nouvelle » identique a ce que le programme a deja)
    reg = bytearray(open(a.gfx, "rb").read())
    for b in json.load(open(os.path.join(a.sortie, "blocs.json"))):
        o = int(b["decalage_region"][1:], 16); data = open(os.path.join(a.sortie, b["fichier"]), "rb").read()
        reg[o:o + len(data)] = data
    pj = json.load(open(os.path.join(a.export, "palettes.json")))["plans"]
    pn = json.load(open(os.path.join(a.sortie, "palettes_nouvelles.json")))

    def rendu(L, code, attr, col):
        t = E.flip(E.decode_tile(reg, L, code, col), attr & 0x20, attr & 0x40)
        p = E.PAL0[L] + (attr & 0x1F); k = "$%02X" % p
        mots = pn.get("scroll%d" % L, {}).get(k)
        rgb = E.cps_rgb([int(x, 16) for x in mots]) if mots else \
            np.array([[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in pj["scroll%d" % L][k]["rgb_ref"]], np.uint8)
        return np.where((t != 15)[:, :, None], rgb[t], 0), t == 15
    deja = {1: 0, 2: 0, 3: 0}
    CH = ce["canevas_psd"][1]

    def ecrit(adr, data):
        for i, b in enumerate(data):
            assert adr + i < len(prog)
            prog[adr + i] = b
        patch[adr] = bytes(data)

    resume = {}
    for L in (1, 2, 3):
        cp = ce["plans"]["scroll%d" % L]; ts = cp["taille_tuile"]
        c0 = cp["monde_tilemap_px"]["x0"] // ts; r0 = cp["monde_tilemap_px"]["y0"] // ts
        typ, lst, adr_liste = B.liste(prog, L, dec)
        T0 = B.cases_tilemap(orig, L, dec)
        nbx = NBX[L]
        neuves = {}                                     # position de liste -> {(col, rang) dans le bloc: (code, attr)}
        for r, row in enumerate(cp["cases"]):
            for c, e in enumerate(row):
                if e[6] not in "nr": continue          # 'v' (vide, jamais vue) : on garde le contenu du programme
                col = (c0 + c) % WT[L]; rg = (r0 + r) % HT[L]
                v0 = T0.get((col, rg))
                if v0 is not None:                       # deja dans le programme a l'identique (cases « completees
                    a1, m1 = rendu(L, e[0], e[5], c0 + c)  # par colonne » du pilote, null dans carte_tuiles.json) ?
                    a2, m2 = rendu(L, v0[0], v0[1], c0 + c)
                    h = max(0, min(ts, CH - (cp["origine_dans_canevas_psd"][1] + r * ts)))   # lignes dans le canevas
                    if (m1[:h] == m2[:h]).all() and (a1[:h] == a2[:h]).all():
                        deja[L] += 1; continue
                bx, by = (col // NT[L]) % nbx, rg // NT[L]
                assert e[5] <= 0xFF or L == 1, "attribut > 8 bits non stockable dans un bloc scroll%d" % L
                neuves.setdefault(by * nbx + bx, {})[(col % NT[L], rg % NT[L])] = (e[0], e[5])
        libres = list(LIBRES[L]); st_next = ST_LIBRE; info = []
        for pos, cases in sorted(neuves.items()):
            ancien = lst[pos]
            num = libres.pop(0)
            cur = B.bloc(prog, L, ancien)
            cur.update(cases)
            if L == 1:
                # 8 x 8 super-tuiles (4 x 4 tuiles) ; reutilise une super-tuile identique de la bibliotheque
                lib = {}
                nst = (B.B2 - B.ST1) // 0x40
                for i in range(nst):
                    lib.setdefault(bytes(prog[B.ST1 + 0x40 * i:B.ST1 + 0x40 * i + 0x40]), i)
                idx = []
                for k in range(64):
                    scol, srow = k >> 3, k & 7
                    raw = b"".join(struct.pack(">HH", *cur[(scol * 4 + (j >> 2), srow * 4 + (j & 3))]) for j in range(16))
                    if raw in lib: i = lib[raw]
                    else:
                        assert all(x == 0xFF for x in prog[st_next:st_next + 0x40]), "fin de ROM non libre"
                        i = (st_next - B.ST1) // 0x40; assert i < 0x10000
                        ecrit(st_next, raw); lib[raw] = i; st_next += 0x40
                    idx.append(i)
                ecrit(B.B1 + num * 0x80, b"".join(struct.pack(">H", i) for i in idx))
            else:
                nb = 256 if L == 2 else 64; sh = 4 if L == 2 else 3; msk = (1 << sh) - 1
                codes = b"".join(struct.pack(">H", (cur[(k >> sh, k & msk)][0] - B.ADD[L]) & 0xFFFF) for k in range(nb))
                attrs = bytes(cur[(k >> sh, k & msk)][1] & 0xFF for k in range(nb))
                base = B.B2 if L == 2 else B.B3
                ecrit(base + num * B.TAILLE[L], codes + attrs)
            ecrit(adr_liste + pos, bytes([num]))
            info.append(dict(position=pos, bloc_avant="$%02X" % ancien, bloc_neuf="$%02X" % num, cases=len(cases)))
        resume["scroll%d" % L] = dict(cases_deja_identiques_dans_le_programme=deja[L], liste="$%06X" % adr_liste, type=typ, blocs=info,
                                      supertuiles_neuves=(st_next - ST_LIBRE) // 0x40 if L == 1 else None)
        print("scroll%d : liste $%06X ; %d cases deja identiques ; %s" % (L, adr_liste, deja[L], info))

    # ---- palettes nouvelles : bloc de 32 palettes 0RGB du plan pour ce decor (routine $1FD40) ----
    resume["palettes"] = {}
    for L in (1, 2, 3):
        for k, mots in sorted(pn.get("scroll%d" % L, {}).items()):
            p = int(k[1:], 16) - E.PAL0[L]
            base, npropres = B.palettes_bloc(orig, L, dec)
            assert p < npropres, "palette %s hors du bloc propre du decor (%d palettes) : ecrirait celles d'un autre decor" % (k, npropres)
            adr = base + 32 * p
            assert all(int(m, 16) >> 12 == 0xF for m in mots[:15]), "palette %s : luminosite != F" % k
            ecrit(adr, b"".join(struct.pack(">H", int(m, 16) & 0x0FFF) for m in mots))
            resume["palettes"][k] = "$%06X" % adr
    if resume["palettes"]: print("palettes ecrites :", resume["palettes"])

    # ---- verification : tilemaps recomposees depuis le programme corrige ----
    verif = {}
    for L in (1, 2, 3):
        cp = ce["plans"]["scroll%d" % L]; ts = cp["taille_tuile"]
        c0 = cp["monde_tilemap_px"]["x0"] // ts; r0 = cp["monde_tilemap_px"]["y0"] // ts
        T = B.cases_tilemap(prog, L, dec); T0 = B.cases_tilemap(orig, L, dec)
        ok = ko = 0; o_ok = o_ko = 0
        for r, row in enumerate(cp["cases"]):
            for c, e in enumerate(row):
                k = ((c0 + c) % WT[L], (r0 + r) % HT[L])
                v = T.get(k)
                if e[6] in "nr":                      # case nouvelle : = carte etendue (ou rendu identique)
                    if v and v[0] == e[0] and (v[1] & 0xFF) == (e[5] & 0xFF): ok += 1
                    elif v and all((x[:max(0, CH - r * ts)] == y[:max(0, CH - r * ts)]).all()
                                   for x, y in zip(rendu(L, e[0], e[5], c0 + c), rendu(L, v[0], v[1], c0 + c))): ok += 1
                    else: ko += 1
                elif True:                            # case d'origine ou vide : inchangee dans le programme
                    if v == T0.get(k): o_ok += 1
                    else: o_ko += 1
        # hors monde exporte : rien d'autre ne change dans la tilemap
        dom = {((c0 + c) % WT[L], (r0 + r) % HT[L]) for r in range(len(cp["cases"])) for c in range(len(cp["cases"][0]))}
        autres = sum(1 for k in T if k not in dom and T[k] != T0.get(k))
        verif["scroll%d" % L] = dict(cases_nouvelles_egales=ok, cases_nouvelles_differentes=ko, cases_origine_inchangees=o_ok,
                                     cases_origine_modifiees=o_ko, cases_hors_monde_modifiees=autres)
    print("VERIFICATION", verif)
    out = dict(decor="$%02X" % dec, resume=resume, verification=verif,
               patch={"$%06X" % k: v.hex() for k, v in sorted(patch.items())})
    json.dump(out, open(os.path.join(a.sortie, "prog_patch.json"), "w"), indent=1)
    with open(os.path.join(a.sortie, "injection_prog.lua"), "w") as f:
        f.write("-- genere par injection_prog.py : octets du programme 68000 (adresse, hexa big-endian)\nreturn {\n")
        for k, v in sorted(patch.items()):
            f.write(' {adr=0x%06X, hex="%s"},\n' % (k, v.hex()))
        f.write("}\n")
    # aussi : programme corrige complet (pour les cœurs qui chargent une image)
    open(os.path.join(a.sortie, "sfa3ud_prog_corrige.bin"), "wb").write(bytes(prog))
    nd = sum(1 for x, y in zip(orig, prog) if x != y)
    print("octets du programme modifies : %d" % nd)
    return 0 if all(v["cases_nouvelles_differentes"] == v["cases_origine_modifiees"] == v["cases_hors_monde_modifiees"] == 0
                    for v in verif.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
