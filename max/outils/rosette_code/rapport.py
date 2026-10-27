"""Produit api_moteur.json (paires + soutien + rôle) et le tableau Markdown de README.md."""
import json, collections
ROLES = {
 0x2a708: "lancer l'animation n (table `$2B0`) → pas courant `$1C`",
 0x2a758: "lancer l'animation n (table `$2B4`)",
 0x2a710: "lancer l'animation n (table `$2BC`) + octets par perso/ism → `$23E`, `$293`",
 0x2a7ea: "avancer l'animation (décompte `$32`, pas suivant)",
 0x2a83c: "lancer l'animation n d'un AUTRE objet (A4)",
 0x2f728: "force du poing pressé (boutons `$378|$37A`, bits 0-2 → 0/2/4)",
 0x2f74c: "force du pied pressé (bits 4-6 → 0/2/4)",
 0x2f980: "lecture d'une combinaison de boutons (`$378|$37A & $7700`)",
 0x2f796: "remise à l'état neutre (efface/positionne `$D6`, `$AB`, `$2A0`, `$BA`, `$E2`, `$E4`…)",
 0x2e7f2: "prise : adversaire (`$38`) mis en état projeté, attaque n de la table `$A0`",
 0x2e970: "prise (variante), attaque n de la table `$A0`",
 0x2e3fe: "déclenchement d'un coup (`$32F` = n), selon l'état `$4/$6`",
 0x2e636: "déclenchement d'un coup (variante, teste l'adversaire `$38`)",
 0x0804da: "création d'un objet fils (projectile/effet) A4",
 0x080b70: "création d'un objet fils lié à l'attaque n (table `$A0`)",
 0x020674: "réaction console/son ? (`$AC(A5)`, `$125`)",
 0x02068c: "idem, selon la force `$82` (pose `$216`)",
 0x00369c: "son/voix propre au perso (table de bits par ID)",
 0x02f52c: "pose `$291`=1, `$2A0`=10 puis neutre",
 0x01bd5c: "table choisie par `$E` (côté/sens)",
}
C = {int(a, 16): int(p, 16) for a, p in json.load(open("api_arcade_psp.json")).items()}
V1 = {int(a, 16): {int(k, 16): n for k, n in v.items()} for a, v in json.load(open("votes_passe1.json")).items()}
INTERP = {0x2a770: 0x5d75c, 0x2a7f0: 0x5d900, 0x2a83c: 0x5da38, 0x2a8ca: 0x5dbe8, 0x2a98c: 0x5dedc, 0x2af7a: 0x5f2c4,
          0x2b0c4: 0x5f748, 0x2e5f0: 0x66d10, 0x2e614: 0x66d68, 0x2f728: 0x69b94, 0x2f74c: 0x69be8, 0x2f770: 0x69c3c,
          0x2f796: 0x69c78, 0x2f980: 0x69d68, 0x2faae: 0x69fc4, 0x2fb96: 0x6a17c}
rows = []
for a, p in sorted(C.items()):
    v = V1.get(a, {}); rows.append({"arcade": "%06x" % a, "psp": "%06x" % p, "methode": "arguments+alignement",
        "soutien": "%d/%d" % (v.get(p, 0), sum(v.values())), "role": ROLES.get(a, "")})
for a, p in sorted(INTERP.items()):
    rows.append({"arcade": "%06x" % a, "psp": "%06x" % p, "methode": "interpolation (ordre)", "soutien": "-", "role": ROLES.get(a, "")})
json.dump(rows, open("api_moteur.json", "w"), indent=1, ensure_ascii=False)
print("| arcade 68K | PSP | méthode | soutien | rôle (lu dans le 68K) |\n|---|---|---|---|---|")
for r in rows: print("| `%s` | `%s` | %s | %s | %s |" % (r["arcade"], r["psp"], r["methode"], r["soutien"], r["role"]))
