#!/usr/bin/env python3
"""(agent_integration_max) Liste des tables d'Upper indexées par l'ID du perso (40 entrées) à AGRANDIR pour $28/$29 :
cartographies work/carto_persos/combat/tables_combat.json et hors_combat/tables_hors_combat.json (lecture seule),
étape B (tables de code relogées), et cas particuliers. Classement :
  simple : entrée i à T + e*i (valeurs absolues : octets, mots, longs, pointeurs) -> 48 entrées
  rel16  : décalages u16 RELATIFS à la table vers des données qui la suivent -> en-tête de 48, données décalées
  code   : table de code relogée par l'étape B (adresses 68K)
Sortie : tables_par_id.json"""
import json, struct, os
C = "<workspace>/work/carto_persos/"
buf = open("<workspace>/anthology_extract/decompressed/ro5_usa_prog68k.bin", "rb").read()
RB = 0x1F0000
ETAPEB = {int(l.split()[1].split("-")[0], 16) for l in open("<workspace>/work/agent_integration_max/banc_ref/etapeB_reloge.txt") if l.startswith("table")}
EXCLUS = {0x6F72B0: "palettes (déplacée à part)", 0x700540: "palettes d'effets (déplacée à part)",
          0x674C00: "poses des portraits (structure à part)", 0x61BFB0: "grille (64 cases)"}
T = {}
def ajoute(ps2, n, e, role, src):
    if ps2 in T or ps2 in EXCLUS: return
    T[ps2] = dict(ps2="%06x" % ps2, n=n, e=e, role=role, src=src)
d = json.load(open(C + "combat/tables_combat.json"))
for t in d["tables"]:
    if t.get("ro5") and t.get("n_ro5") == 40: ajoute(int(t["ro5"], 16) + RB, 40, t["element"], t["role"], "combat")
h = json.load(open(C + "hors_combat/tables_hors_combat.json"))
for t in h["tables"]:
    ind = str(t.get("indice", ""))
    if t.get("ro5") not in (None, "None") and str(t.get("entrees_ro5")) == "40" and (ind.startswith("ID") or ind in ("$132(A5) gagnant", "$146(A5)=ID")):
        ajoute(int(t["ro5"], 16) + RB, 40, int(t["octets_par_entree"]), t["role"], "hors combat " + t["nom"])
for b in ETAPEB:
    n = None
    for l in open("<workspace>/work/agent_integration_max/banc_ref/etapeB_reloge.txt"):
        if l.startswith("table %06x" % b): n = int(l.split()[4])
    if n == 40: ajoute(b, 40, 4, "table de code (étape B)", "etapeB")
# multi-rangées (constante de rangée dans le code) et tables à base décalée : traitées à part (MULTI)
MULTI = {0x616850: "noms graphiques : 2 x 40 (ID, ID + $28 selon $90(A5)) -- constante de rangée dans le code",
         0x61B6D0: "décor imposé aux combats 8 / 9 : 2 x 40 -- constante de rangée",
         0x61B580: "scénarios de dialogue spéciaux : 3 x 40", 0x61B600: "idem (2)",
         0x967BF0: "mot par perso, index = ID + $18 (24 entrées non-perso avant)"}
for b, r in MULTI.items():
    if b in T: T[b]["kind_force"] = "multi"; T[b]["note"] = r
if 0x967BF0 in T: T[0x967BF0].update(kind_force="simple", n=64, note=MULTI[0x967BF0])     # 24 entrées non-perso + 40
u16 = lambda a: struct.unpack_from("<H", buf, a - RB)[0]
tous = sorted(T)
for k, b in enumerate(tous):
    t = T[b]; t["kind"] = "code" if b in ETAPEB else "simple"
    if t.get("kind_force"): t["kind"] = t.pop("kind_force"); continue
    if t["e"] == 2 and b not in ETAPEB:
        v = [u16(b + 2 * i) for i in range(40)]
        if v[0] == 0x50 and min(v) >= 0x50 and max(v) < 0x8000:     # en-tête de 40 décalages relatifs (0x50 = 40 x 2)
            t["kind"] = "rel16"; t["off_min"], t["off_max"] = min(v), max(v)
            o = sorted(set(v)); gap = max([o[i + 1] - o[i] for i in range(len(o) - 1)] + [0x100])
            fin = b + max(v) + gap
            if k + 1 < len(tous) and b + max(v) < tous[k + 1] < fin: fin = tous[k + 1]
            t["region"] = fin - b
    t["suivante"] = "%06x" % tous[k + 1] if k + 1 < len(tous) else None
json.dump(sorted(T.values(), key=lambda t: t["ps2"]), open("tables_par_id.json", "w"), indent=1, ensure_ascii=False)
import collections
print(collections.Counter(t["kind"] for t in T.values()), len(T))
for t in sorted(T.values(), key=lambda t: t["ps2"]):
    print(t["ps2"], t["e"], t["kind"], t.get("off_min", ""), t.get("off_max", ""), t["role"][:70])
