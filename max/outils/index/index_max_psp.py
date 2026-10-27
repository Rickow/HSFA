"""Lignes de l'index des connaissances (re/connaissances/max_psp.tsv et champs PSP de champs.tsv) produites depuis les
tables de la session MAX (2026-10-17). Aucune donnée de jeu : adresses, noms, rôles, correspondances, sources.
Espace max_psp : adresse = va à base 0 de l'EBOOT EU ULES-00235 (va = décalage fichier − 0x74 ; mémoire = 0x08804000 + va).
Colonnes : adresse, adresse_autres, genre, nom, rôle, taille_type, mises_en_garde, source, confiance, score, outil.
Usage : python index_max_psp.py <dossier de sortie>  -> max_psp.tsv, champs_psp.tsv (à fusionner dans re/connaissances)."""
import os, sys, json, csv
ICI = os.path.dirname(os.path.abspath(__file__)); RC = os.path.join(ICI, "rosette_code")
sys.path.insert(0, RC); os.chdir(RC)
import traduire as T

COLS = ["adresse", "adresse_autres", "genre", "nom", "rôle", "taille_type", "mises_en_garde", "source", "confiance", "score", "outil"]
L = []


def ligne(adr, autres="", genre="", nom="", role="", taille="", garde="", source="", conf="mesuré", score="", outil=""):
    L.append(["0x%06X" % adr if isinstance(adr, int) else adr, autres, genre, nom, role, taille, garde, source, conf, score, outil])


# 1. API moteur PSP <-> arcade (Rosette du code ; votes : api_moteur.json, ajouts manuels commentés dans traduire.py)
mot = {int(x["psp"], 16): x for x in json.load(open("api_moteur.json"))}
for p, a in sorted(T.API.items()):
    x = mot.get(p)
    if x:
        ligne(p, "arcade:$%05X" % a, "fonction", "psp_%x" % p, x.get("role", "") or "fonction moteur appariée", "", "",
              "max/notes/max-rosette-code.md ; api_moteur.json", "mesuré",
              "%s (%s)" % (x.get("soutien", ""), x.get("methode", "")), "max/outils/rosette_code/rosette.py")
    else:
        ligne(p, "arcade:$%05X" % a, "fonction", "psp_%x" % p, "fonction moteur appariée à la main (pas à pas)", "", "",
              "max/outils/rosette_code/traduire.py (API.update commentés)", "déduit", "", "max/outils/rosette_code/traduire.py")
# 2. fonctions moteur des acteurs de fin
for p, a in sorted(json.load(open("api_acteurs.json")).items(), key=lambda k: int(k[0], 16)):
    ligne(int(p, 16), "arcade:%s" % a, "fonction", "psp_%x" % int(p, 16), "moteur des acteurs de fin", "", "",
          "max/outils/rosette_code/acteurs_fins.py", "déduit", "", "max/outils/rosette_code/appris_acteurs.py")
# 3. globales PSP -> décalage A5
for p, a in sorted(T.GLOB.items()):
    ligne(p, "arcade:$%X(A5)" % a, "variable", "", "globale PSP rangée en RAM A5 de l'arcade", "", "zone .data/.bss (segment 1)",
          "max/outils/rosette_code/traduire.py (GLOB)", "déduit", "", "max/outils/rosette_code/traduire.py")

# 4. routines, tables et structures relevées (notes MAX, 2026-10-04 -> 2026-10-17)
N = "max/notes/max-integration-upper.md"; FU = "max/outils/rosette_construction/FORMAT-UPPER-HYPER.md"
RC_ = "max/outils/rosette_construction/README.md"
for a, aut, g, nom, role, taille, garde, src, conf, outil in [
    (0x215040, "", "table", "racines_persos", "racine (routine d'init) par ID perso, 42 entrées ; ordre des modules dans .text", "42 × ptr", "", "max/notes/max-portage-code.md", "mesuré", "tools/max/modules.py"),
    (0x6AB48, "", "fonction", "gabarit_remplir", "remplit le gabarit du perso : 21 appels à 0x6A638 selon une liste d'éléments", "", "Yun ne l'appelle pas", "max/outils/rosette_code/yun_entree6.md", "mesuré", "ghidra_decomp.py"),
    (0x6A638, "", "fonction", "gabarit_element", "élément n du sous-en-tête de [6] (décalage +8+4n, nombre +0x108+4n) -> pointeurs", "", "", "max/outils/rosette_code/yun_entree6.md", "mesuré", "ghidra_decomp.py"),
    (0x1BF944, "", "fonction", "yun_gabarit", "init de Yun : 17 appels directs à 0x6A638 ; élément = standard − 5", "", "+0x84 rempli deux fois, +0x88 jamais", "max/outils/rosette_code/yun_entree6.md", "mesuré", "ghidra_decomp.py"),
    (0x2A3198, "", "table", "gabarit_eagle", "gabarit d'Eagle (39 longs recopiés à l'init)", "39 × u32", "", N, "mesuré", ""),
    (0x2A3234, "", "table", "elements_eagle", "liste des 21 éléments de [6] passée à 0x6AB48", "21 × u8", "", "max/outils/rosette_code/yun_entree6.md", "mesuré", ""),
    (0x1B3668, "upper:T_749838[$26]", "fonction", "racine_eagle", "racine d'Eagle ($26)", "", "gestionnaires rangés AVANT (0x1B0238-0x1B3668)", N, "mesuré", "max/outils/rosette_code/brouillons.py"),
    (0x1B9E68, "", "fonction", "racine_maki", "racine de Maki ($27)", "", "gestionnaires avant la racine", N, "mesuré", "max/outils/rosette_code/brouillons.py"),
    (0x1BF3EC, "", "fonction", "racine_yun", "racine de Yun ($28 PSP)", "", "Yun = $2D dans Upper", N, "mesuré", "max/outils/rosette_code/brouillons.py"),
    (0x1C619C, "", "fonction", "racine_ingrid", "racine d'Ingrid ($29 PSP)", "", "Ingrid = $2E dans Upper", N, "mesuré", "max/outils/rosette_code/brouillons.py"),
    (0x1B0238, "", "fonction", "gestionnaires_eagle", "début des gestionnaires d'Eagle (fin du code atteint de Balrog (alt) : 0x1B0088)", "", "dans le « module » $25", N, "mesuré", "max/outils/rosette_code/brouillons.py"),
    (0x1B3450, "", "fonction", "creneau_delai_1b3450", "PAS une fonction : créneau de délai d'un jal pointé par le mot de données 0x2C8ED0", "", "PAS un début de fonction (coupait psp_1b33c8)", "tools/max/charcode2.py", "mesuré", "tools/max/charcode2.py"),
    (0x150450, "", "fonction", "creneau_delai_150450", "PAS une fonction : créneau de délai pointé par une donnée", "", "PAS un début de fonction", "tools/max/charcode2.py", "mesuré", "tools/max/charcode2.py"),
    (0x5D63C, "arcade:$2A708", "fonction", "lancer_anim_2b0", "lance l'animation n de la table $2B0 (a0 objet, a1 n)", "", "", RC_, "mesuré", "max/outils/rosette_construction/chaine_code.py"),
    (0x5D674, "arcade:$2A710", "fonction", "lancer_anim_2bc", "lance l'animation n de $2BC", "", "", RC_, "mesuré", "max/outils/rosette_construction/chaine_code.py"),
    (0x5D6EC, "arcade:$2A758", "fonction", "lancer_anim_2b4", "lance l'animation n de $2B4", "", "", RC_, "mesuré", "max/outils/rosette_construction/chaine_code.py"),
    (0x5D724, "arcade:$2A75E", "fonction", "lancer_anim_2b8", "lance l'animation n de $2B8", "", "", RC_, "mesuré", "max/outils/rosette_construction/chaine_code.py"),
    (0x183A38, "arcade:classes $13/$14", "fonction", "objet_attache", "objet attaché au corps (griffe / masque de Vega) : octet +10/+11 du pas -> 0x28FD8C", "", "", RC_ + " (règle 5)", "mesuré", "ghidra_decomp.py"),
    (0x183AB8, "", "fonction", "objet_attache_2", "objet attaché (suite)", "", "", RC_, "mesuré", "ghidra_decomp.py"),
    (0x183E10, "", "fonction", "objet_attache_3", "objet attaché (suite)", "", "", RC_, "mesuré", "ghidra_decomp.py"),
    (0x28FD8C, "", "table", "vega_indices", "indice de calque par octet du pas (×4)", "", "", RC_, "mesuré", ""),
    (0x28EE30, "upper:0x655F48", "table", "vega_masque", "frames du masque de Vega par calque ($8000 = rien)", "", "", RC_, "mesuré", ""),
    (0x28F0E2, "upper:0x656CE8", "table", "vega_griffe", "frames de la griffe de Vega par calque", "", "", RC_, "mesuré", ""),
    (0x1DB424, "arcade:$2FC4A", "fonction", "fin_chargeur", "chargeur des fins (descripteur 0x20184C)", "", "", "max/notes/max-tables-animation.md", "mesuré", "max/outils/rosette_code/anims_fins_max.py"),
    (0x1D4C48, "arcade:$AA630", "fonction", "fin_acteur_pas", "lit +$110[n] (pas d'animation de fin), copie la palette du joueur si banque = perso", "", "cas particulier Ingrid", "max/notes/max-tables-animation.md", "mesuré", ""),
    (0x2830AA, "arcade:$72DE8 (sfa3ud)", "table", "hadoken_attaques", "attaques du Hadoken de Ryu (32 o)", "6 × 32 o", "octets $12/$14 ×2 dans l'arcade", N, "mesuré", "max/outils/rosette_code/projectiles_max.py"),
    (0x6099C, "", "fonction", "jauges_init", "pose garde (+0x2BD) et seuil d'étourdissement (+0x22C) depuis 0x21D3A0 / 0x21D3CA[+0x152]", "", "ajustements : isme ±8, $318&$200 −8, ÷2 si +0x134", N, "mesuré", "ghidra_decomp.py"),
    (0x21D3A0, "upper:0x74C680", "table", "garde_par_perso", "longueur de la jauge de garde par ID", "42 × u8", "= Upper lu dans l'ordre BRUT du fichier (pas XOR 1)", N, "mesuré", ""),
    (0x21D3CA, "upper:0x74C6A8", "table", "seuil_etourdissement", "seuil d'étourdissement par ID", "42 × u8", "= Upper (ordre brut) sauf places 36, 38, 39", N, "mesuré", ""),
    (0x8B0EC, "upper:0x12DEC0", "fonction", "hud_visages", "visage J1 = frame 0x17D + 0x222D76[perso], J2 = 0x1AA + … (pit_e.pac) ; jauge 0x222D4C + 0xF6 / 0x125", "", "", N, "mesuré", "max/outils/convert/hud_max.py"),
    (0x222D76, "upper:0x95C8E0", "table", "hud_visage_index", "indice du visage de barre de vie par ID ($26-$29 -> 40-43)", "42 × u8", "", N, "mesuré", "max/outils/convert/hud_max.py"),
    (0x222D4C, "", "table", "hud_jauge_index", "frame de la jauge d'étourdissement (longueur) par ID", "42 × u8", "ce n'est PAS le nom", N, "mesuré", ""),
    (0x99074, "upper:0x18A6F8", "fonction", "apercu_selection", "aperçu de sélection : animation 0x2256C0[perso], palette 0x538 + perso × 6 + couleur", "", "Ingrid ($29) : 2 palettes par couleur", N, "mesuré", "max/outils/convert/apercu_selection_max.py"),
    (0x2256C0, "upper:T_97CA90", "table", "apercu_anims", "animations d'aperçu par ID (pas de 8 o : durée|$8000 boucle, drapeaux, frame select_e jeu 0, saut)", "42 × ptr", "$25 -> $15", N, "mesuré", "max/outils/convert/apercu_selection_max.py"),
]:
    ligne(a, aut, g, nom, role, taille, garde, src, conf, "", outil)

# 5. champs PSP -> arcade (structure joueur 0x498 o -> $400)
C = []
for p, (a, meth) in sorted(json.load(open("carte_champs.json")).items(), key=lambda k: int(k[0], 16)):
    C.append(["max_psp:joueur+0x%X" % int(p, 16), "arcade:joueur+$%s" % a.upper(), "champ", "", "champ apparié (%s)" % meth,
              "", "", "max/outils/rosette_code/champs.py ; carte_champs.json", "mesuré", "", "max/outils/rosette_code/traduire.py"])
for p, a in sorted(T.HORS_MAX.items()):
    C.append(["max_psp:joueur+0x%X" % p, "arcade:joueur+$%X" % a, "champ", "", "allocation PROPRE aux persos MAX (union de travail)",
              "", "à ne pas confondre avec un champ arcade", "max/outils/rosette_code/traduire.py (HORS_MAX)", "déduit", "", "max/outils/rosette_code/traduire.py"])
for p in sorted(T.JOUEUR_SANS):
    C.append(["max_psp:joueur+0x%X" % p, "", "champ", "", "champ PSP sans équivalent arcade : écritures et lectures omises",
              "", "", "docs/methodes/pieges-du-traducteur.md §9", "déduit", "", "max/outils/rosette_code/traduire.py"])

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    for nom, rows in (("max_psp.tsv", L), ("champs_psp.tsv", C)):
        with open(os.path.join(d, nom), "w", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(COLS); w.writerows(rows)
        print(nom, len(rows), "lignes")
