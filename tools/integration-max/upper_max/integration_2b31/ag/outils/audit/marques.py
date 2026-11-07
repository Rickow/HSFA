#!/usr/bin/env python3
"""(agent_audit_id) Listes terminées par une marque dans les copies agrandies (rel16 / rel16n) : les blocs MAX ajoutés
par agrandit_max.bloc_rel16 (suite += b + bourrage si impair) gardent-ils la marque de fin des blocs natifs ?

Pour chaque table rel16 copiée : blocs natifs = intervalles entre décalages distincts triés (le dernier : jusqu'à la
table suivante, ignoré) ; marque supposée = dernier octet / dernier mot commun à >= 90 % des blocs natifs.
Blocs MAX (entrées ajoutées) : octets jusqu'au bloc suivant de la copie (ou fin de copie) ; défaut si la marque manque
avant le bloc suivant (le lecteur déborde alors dans le bloc suivant)."""
import sys, os, struct, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import image as I
# (agent_integration_max) copie de agent_audit_id/outils/marques.py : banc en argument, code de sortie 1 si une marque manque
BANC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "@UM_AG@/banc_max17"
MAX = I.Banc(BANC)
AGR = []
for l in open(os.path.join(BANC, "max_agrandies.txt")):
    f = l.split()
    if len(f) > 4 and re.match(r"[0-9a-f]{6}$", f[0]) and f[1] in ("rel16", "rel16n"):
        AGR.append((int(f[0], 16), f[1], int(f[3], 16), int(f[4]), " ".join(f[7:])[:60]))
RANGS = {0x97AF50: 2}                                 # rel16 à rangées (agrandit_max.REL16_RANGS)
N_REL16N = {0x68DC72: 789, 0x960180: 12, 0x966740: 48, 0x9719C0: 25, 0x971CC0: 25}
out = []
for p, g, c, taille, role in AGR:
    N = N_REL16N.get(p, 40 * RANGS.get(p, 1))
    hn = struct.unpack("<%dH" % N, I.natif(p, 2 * N))
    pos = sorted(set(x for x in hn if 0 < x < 0x8000))
    nat_blocs = [I.natif(p + pos[k], pos[k + 1] - pos[k]) for k in range(len(pos) - 1)]
    fins1 = collections.Counter(b[-1] for b in nat_blocs if b)
    fins2 = collections.Counter(b[-2:] for b in nat_blocs if len(b) >= 2)
    # 1er décalage = 2N ?
    pre = 0
    blob = MAX.img(c, taille + 4)
    # nombre d'entrées de la copie : 1er décalage positif / 2
    h0 = struct.unpack_from("<H", blob, 0)[0]
    N2 = h0 // 2 if g == "rel16" else None
    if p in RANGS: N2 = 48 * RANGS[p]                   # (agent_integration_max) rel16 à rangées : en-tête de 48·R mots
    if g == "rel16n":
        hh = struct.unpack_from("<%dH" % (N + 8), blob, 0)
        N2 = min(x for x in hh if 0 < x < 0x8000) // 2
    hm = struct.unpack_from("<%dH" % N2, blob, 0)
    if g == "rel16":
        ajout = [i for i in range(N2) if i in (38, 39, 45, 46) or i >= 40]
    else:
        ajout = list(range(N, N2))
    posm = sorted(set(x for x in hm if 0 < x < 0x8000))
    for i in ajout:
        o = hm[i]
        if not (0 < o < 0x8000): continue
        k = posm.index(o)
        fin = posm[k + 1] if k + 1 < len(posm) else min(len(blob), o + 64)
        b = blob[o:fin]
        # entrée MAX propre = bloc hors de la zone recopiée (décalage >= fin du corps natif décalé)
        propre = o >= 2 * N2 + (max(pos) - 2 * N) if pos else True
        m1, n1 = fins1.most_common(1)[0] if fins1 else (None, 0)
        m2, n2 = fins2.most_common(1)[0] if fins2 else (None, 0)
        marque = None
        if nat_blocs and n1 >= 0.9 * len(nat_blocs): marque = bytes([m1])
        out.append((p, g, i, o, propre, len(b), b[:24].hex(), marque.hex() if marque else "?",
                    (b.endswith(marque) or (marque in b)) if marque else None, role))
print("ps2\tgenre\tentree\tdecal\tbloc_MAX\tlongueur\toctets\tmarque_native\tmarque_presente\trole")
for x in out:
    if not x[4]: continue
    print("%06x\t%s\t%d\t%04x\t%s\t%d\t%s\t%s\t%s\t%s" % x)
# défaut = bloc d'un perso MAX (rangs $26 / $27 / $2D / $2E de chaque rangée de 48, ou entrées ajoutées d'une rel16n) sans
# sa marque ; les pseudo-id 40-44 / 47 (copies du natif, souvent vides) ne sont pas des blocs MAX
defauts = [x for x in out if x[4] and x[8] is False and (x[1] == "rel16n" or x[2] % 48 in (38, 39, 45, 46))]
for x in defauts: sys.stderr.write("MARQUE DE FIN ABSENTE : %06x entrée %d (%s)\n" % (x[0], x[2], x[9]))
sys.exit(1 if defauts else 0)
