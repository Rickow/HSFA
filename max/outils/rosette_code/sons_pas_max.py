"""Tables « SONS PAR PAS » des persos MAX au format d'Upper (T_74C538[ID] = $E6 de l'objet), 2026-10-17.
Arcade $2A780 : octet $A du pas -> table $C0 du perso (4 o) -> octet 2 ($C6) = index de son -> table $E6 (8 o par index :
mot commande côté 1, mot commande côté 2 ($BC(A5)), 0, 0) -> $3938. PSP 0x5D75C : même index (octet 2 de l'entrée $C0)
-> table de MOTS « code son » en +0x90 du gabarit du perso (posée en +0x124 par 0x60B98) -> 0x78408 (code < $200 :
bruitage commun ; $2nn : voix n du pack). Gabarits : Eagle 0x2A3198, Maki 0x2A6268, Yun 0x2AD6DC, Ingrid 0x2B1EE0.
Index employés (octet 2 des entrées $C0) : Eagle 0-25, Maki 0-34, Yun 0-30, Ingrid 0-29 = longueur des tables PSP.
Correspondance des codes :
  - voix $2nn -> symbole de VOIX_xx[n] (moteur_max_main.s, symboles CMD_VOIX_xx_Exx de commandes_voix_max.s) ;
  - bruitages communs : Rosette des tables de sons (gabarit +0x90 PSP ↔ T_74C538 d'Upper, même index, 38 persos)
    pour $28/$29/$2A/$30/$22/$23 ; appariement acoustique d'agent_voix_max pour $20/$27/$2B/$36 ; sinon muet.
Sortie : sons_pas_max.s (SONS_PAS_MAX : 4 pointeurs ; SONS_PAS_26…29 : 8 o par index, commentaire = code PSP et confiance)."""
import os, re, struct, sys
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ICI)
from relocs import img, pointer_words

GABARITS = {0x26: 0x2A3198, 0x27: 0x2A6268, 0x28: 0x2AD6DC, 0x29: 0x2B1EE0}
NB = {0x26: 26, 0x27: 35, 0x28: 31, 0x29: 30}
# code PSP commun -> (commande côté 1, côté 2, confiance, source)
COMMUNS = {
    0x28: (0x220, 0x220, "forte", "Rosette 38/43 (index 1)"),
    0x29: (0x221, 0x221, "forte", "Rosette 38/39 (index 2)"),
    0x2A: (0x222, 0x222, "forte", "Rosette 33 ($0222, index 3 ; $0223 à l'index 4 chez les persos d'arcade)"),
    0x30: (0x22E, 0x22E, "forte", "Rosette 21 + agent_voix_max (forte)"),
    0x22: (0x230, 0x230, "forte", "Rosette 9 ; agent_voix_max : $0257, même échantillon que $0230"),
    0x23: (0x231, 0x231, "moyenne", "Rosette 3"),
    0x20: (0x239, 0x239, "forte", "Rosette 2 + agent_voix_max (forte)"),
    0x27: (0x263, 0x263, "moyenne", "agent_voix_max (moyenne) ; Rosette : $0238 (3) / $0263 (2)"),
    0x2B: (0x23E, 0x23E, "forte", "agent_voix_max (forte)"),
    0x36: (0x23B, 0x23B, "moyenne", "agent_voix_max (moyenne)"),
    0x0D: ("CMD_SEQ_0D", "CMD_SEQ_0D", "forte", "agent_son_max : séquence se_mid 10 / I_009 = bruitage arcade $020E"),
    0x2C: ("CMD_SEQ_2C", "CMD_SEQ_2C", "importée", "agent_son_max : séquence se_mid 37 / I_016"),
}
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}


def voix():
    """VOIX_xx[n] de moteur_max_main.s -> symbole ou 0"""
    t = open(os.path.join(ICI, "moteur_max_main.s")).read().split("\n"); V = {}
    for c in GABARITS:
        i = t.index(next(l for l in t if l.startswith("VOIX_%02X:" % c))) + 2; L = []
        while len(L) < 64:
            m = re.match(r"\s+dc\.w\s+(\S+)", t[i]); L.append(m.group(1)); i += 1
        V[c] = L
    return V


def main():
    P = pointer_words(); V = voix(); out = ["; sons par pas des persos MAX (format T_74C538 d'Upper) — généré par sons_pas_max.py",
                                         "SONS_PAS_MAX:", "        dc.l    SONS_PAS_26, SONS_PAS_27, SONS_PAS_28, SONS_PAS_29"]
    stats = {}
    for c, g in GABARITS.items():
        t = P[g + 0x90]; out.append("SONS_PAS_%02X:   ; %s : table PSP %#x (gabarit %#x + 0x90), %d index" % (c, NOMS[c], t, g, NB[c]))
        n_ok = n_muet = 0
        for k in range(NB[c]):
            code = struct.unpack_from("<H", img, t + 2 * k)[0]
            if code == 0: cmd, conf = "0", "muet (aussi sur PSP)"
            elif code >= 0x200:
                s = V[c][code - 0x200] if code - 0x200 < 64 else "0"
                cmd, conf = s, ("voix n° %d (VOIX_%02X)" % (code - 0x200, c)) if s != "0" else "voix n° %d : muette dans VOIX_%02X" % (code - 0x200, c)
            elif code in COMMUNS:
                a, b, f, src = COMMUNS[code]; cmd, conf = (a if isinstance(a, str) else "$%04x" % a), "%s : %s" % (f, src)
            else: cmd, conf = "0", "AUCUNE correspondance (code commun $%02X) : muet" % code
            n_ok += cmd != "0"; n_muet += cmd == "0"
            out.append("        dc.w    %s, %s, 0, 0     ; index %d : code PSP $%03X — %s" % (cmd, cmd, k, code, conf))
        stats[NOMS[c]] = (n_ok, n_muet)
    open(os.path.join(ICI, "sons_pas_max.s"), "w").write("\n".join(out) + "\n")
    return stats


if __name__ == "__main__":
    print(main())
