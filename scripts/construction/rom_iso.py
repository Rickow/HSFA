#!/usr/bin/env python3
"""rom_iso.py -- reconstruit la ROM graphique CPS2 de SFA3 (sz3.13m-sz3.20m, 8 x 4 Mo, format MAME/FBNeo) a partir
des seules donnees de l'ISO PS2 de Street Fighter Alpha Anthology (X_DATA.BIN, groupe ro3). HANDOFF §45.

L'Anthology range la ROM graphique de SFA3 dans ses propres conteneurs (anthgfx.py), en valeurs BRUTES :
  - quart 1 (tuiles $10000-$1DFFF) : e255, A SA PLACE (8x8 dupliquees dans les deux moities, 32x32, 16x16) ;
  - quart 2 ($20000-$2FFFF)        : e257, a sa place ;
  - quart 3 ($30000-$3FFFF)        : e286, a sa place ;
  - quart 0 ($00000-$0FFFF) et fin du quart 1 ($1E000-$1FFFF) : seulement dans les BANQUES de sprites (e254 communs,
    e258-e285 persos), qui sont des sous-ensembles REORGANISES (ordre d'utilisation, HANDOFF §82) : le contenu est
    la, pas la position. Ces tuiles sont rangees ici dans les places libres, dans l'ordre des banques (e254, e258...
    e285, indice local croissant), chaque contenu une seule fois et seulement s'il n'est pas deja dans les quarts 1-3.
    Places restantes : tuile vide (valeur brute 15 = transparent).
Consequence : sz3.14m/16m/18m/20m (quarts 2-3) sont identiques a l'arcade ; sz3.13m/15m/17m/19m (quarts 0-1) ne le
sont pas (ordre des tuiles de sprites inconnu sans la ROM d'origine). La chaine HSFA (banques.py) retrouve chaque tuile
PAR SON CONTENU : les tables changent de codes, pas d'images (voir BUILD.md, « Voie ISO seule »).

Usage : rom_iso.py X_DATA.BIN manifest.csv DOSSIER_SORTIE [--arcade DOSSIER]   (numpy ; anthgfx/cps2rom de untranspile)
        --arcade : mesure seulement (comparaison tuile a tuile et md5 avec une ROM d'arcade), jamais lue pour construire.
"""
import csv, hashlib, json, os, sys
import numpy as np

QUART = 0x10000
POSITIONNELS = ((255, 1), (257, 2), (286, 3))          # conteneur GFX -> quart (indices relatifs au quart)
BANQUES = [254] + list(range(258, 286))                # communs, puis persos (ordre de rangement des tuiles libres)
FICHIERS = ["sz3.13m", "sz3.14m", "sz3.15m", "sz3.16m", "sz3.17m", "sz3.18m", "sz3.19m", "sz3.20m"]
TAILLE = 0x400000


def _outils():
    import anthgfx, cps2rom                            # sys.path : dossier untranspile (+ parent pour lz148778)
    return anthgfx, cps2rom


def lecteur(xdata, manifest):
    man = {int(r['idx']): (int(r['offset']), int(r['size'])) for r in csv.DictReader(open(manifest, newline=""))}
    f = open(xdata, "rb")
    def fichier(n):
        o, s = man[n]; f.seek(o); return f.read(s)
    return fichier


def reconstruit(xdata, manifest, journal=print):
    """-> (T : tableau (262144, 16, 16) uint8 de valeurs brutes, stats)"""
    anthgfx, cps2rom = _outils()
    fichier = lecteur(xdata, manifest)
    S = np.full((4 * QUART * 16, 16), 15, np.uint8)      # lignes de 16 px (« slots »), vides par defaut
    pris = np.zeros(4 * QUART * 16, bool)
    st = {"positionnels": {}, "echecs": 0}
    for n, q in POSITIONNELS:
        b = fichier(n); cnt = {}
        for k, m, px in anthgfx.tiles(b):
            w = anthgfx.SLOTS[k]; o = q * QUART * 16 + w * m
            if px is None:                             # entree 0 = tuile vide (toute a 15)
                cote = {0: 8, 1: 16, 2: 32}[k]; px = np.full((cote, cote), 15, np.uint8)
            S[o:o + w] = anthgfx.to_slots(k, px); pris[o:o + w] = True
            cnt[k] = cnt.get(k, 0) + 1
        # (anthgfx.tiles saute une entree illisible : on le compte)
        attendu = sum(c for _k, _f, c, _t in anthgfx.records(b))
        st["echecs"] += attendu - sum(cnt.values())
        st["positionnels"]["e%d" % n] = cnt
    T = S.reshape(-1, 16, 16)
    place = pris.reshape(-1, 16).all(1)
    st["tuiles_a_leur_place"] = int(place.sum())
    libres = np.where(~place)[0]
    st["places_libres"] = len(libres)
    connus = {T[c].tobytes() for c in np.where(place)[0]}
    vide = np.full((16, 16), 15, np.uint8).tobytes()
    a_ranger = []; vus = set(connus) | {vide}
    for n in BANQUES:
        for k, m, px in anthgfx.tiles(fichier(n)):
            if k != 1 or px is None: continue
            c = px.astype(np.uint8).tobytes()
            if c in vus: continue
            vus.add(c); a_ranger.append(c)
    st["contenus_de_banques_ranges"] = len(a_ranger)
    if len(a_ranger) > len(libres):
        raise SystemExit("rom_iso : %d tuiles de banques pour %d places libres" % (len(a_ranger), len(libres)))
    for c, code in zip(a_ranger, libres):
        T[code] = np.frombuffer(c, np.uint8).reshape(16, 16)
    st["places_vides_restantes"] = len(libres) - len(a_ranger)
    journal("rom_iso : %d tuiles a leur place (e255/e257/e286), %d places libres, %d contenus de banques ranges, "
            "%d places laissees vides, %d entrees illisibles" % (st["tuiles_a_leur_place"], len(libres), len(a_ranger),
                                                                st["places_vides_restantes"], st["echecs"]))
    return T, st


def ecrit(T, dossier):
    _a, cps2rom = _outils()
    os.makedirs(dossier, exist_ok=True)
    roms = cps2rom.encode(T, TAILLE)
    md5 = {}
    for n in FICHIERS:
        d = roms[n[4:]]
        tmp = os.path.join(dossier, n + ".tmp")
        open(tmp, "wb").write(d); os.replace(tmp, os.path.join(dossier, n))
        md5[n] = hashlib.md5(d).hexdigest()
    return md5


def compare(T, md5, arcade, journal=print):
    """mesure seulement : ecarts avec une ROM d'arcade (tuile a tuile, par quart, par fichier, et par contenu)"""
    _a, cps2rom = _outils()
    roms = {n[4:]: open(os.path.join(arcade, n), "rb").read() for n in FICHIERS}
    A = cps2rom.decode(roms)
    eg = (A == T).all((1, 2))
    r = {"md5": {}, "quarts": {}}
    for n in FICHIERS:
        ma = hashlib.md5(roms[n[4:]]).hexdigest()
        enc = cps2rom.encode(T, TAILLE)[n[4:]]
        oct_eg = int(np.sum(np.frombuffer(enc, np.uint8) == np.frombuffer(roms[n[4:]], np.uint8)))
        r["md5"][n] = dict(iso=md5[n], arcade=ma, identique=md5[n] == ma, octets_egaux=oct_eg)
        journal("%s : iso %s arcade %s %s (%.2f %% des octets egaux)" % (n, md5[n], ma, "IDENTIQUE" if md5[n] == ma
                else "different", 100.0 * oct_eg / TAILLE))
    videA = (A == 15).all((1, 2))
    for q in range(4):
        s = slice(q * QUART, (q + 1) * QUART)
        r["quarts"][q] = dict(egales=int(eg[s].sum()), vides_arcade=int(videA[s].sum()))
        journal("quart %d : %d / %d tuiles identiques a leur place (arcade : %d vides)" % (q, eg[s].sum(), QUART, videA[s].sum()))
    cont_iso = {T[c].tobytes() for c in range(len(T))}
    manq = [c for c in range(len(A)) if A[c].tobytes() not in cont_iso]
    cont_arc = {A[c].tobytes() for c in range(len(A))}
    en_plus = len(cont_iso - cont_arc)
    r["codes_arcade_dont_le_contenu_manque"] = ["%05x" % c for c in manq]
    r["contenus_iso_absents_de_l_arcade"] = en_plus
    journal("contenus : %d codes de l'arcade dont le contenu manque a la reconstruction (%s) ; %d contenus de la "
            "reconstruction absents de l'arcade (tuiles propres a l'Anthology)" % (len(manq), " ".join(r["codes_arcade_dont_le_contenu_manque"][:16]), en_plus))
    return r


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    arcade = sys.argv[sys.argv.index("--arcade") + 1] if "--arcade" in sys.argv else None
    if arcade in a: a.remove(arcade)
    xdata, manifest, sortie = a[:3]
    T, st = reconstruit(xdata, manifest)
    md5 = ecrit(T, sortie)
    st["md5"] = md5
    for n in FICHIERS: print("%s  %s" % (md5[n], n))
    if arcade:
        st["comparaison"] = compare(T, md5, arcade)
    json.dump(st, open(os.path.join(sortie, "rom_iso.json"), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    D = "<workspace>/scripts/untranspile"
    if D not in sys.path: sys.path.insert(0, os.environ.get("HSFA_OUTILS_UNTRANSPILE", D))
    main()
