"""Dialogues d'avant / après combat (mode Arcade) des persos MAX au format d'Upper (2026-10-27, Q7 / R7 de
work/echanges/MAX.md).
PSP : textes = bdXX_e.pac (XX = 26-29), entrée 0x10001 : enregistrements de 0x80 o = [longueur][x][texte]0[x][texte]0 ;
scènes = gabarit du perso, mot 38 -> [table des scénarios, 0, …] ; scénario = liste de mots (bit 15 = l'ADVERSAIRE parle,
bit 14 = un 3e personnage de la scène, gardé : Upper l'emploie aussi, 47 mots ; bits 0-9 = n° de réplique, à partir de 1, dans le bd du perso), 0 = fin. Contrôle : Ryu (gabarit 0x23F8FC) donne les
scénarios 0-3 d'Upper mot pour mot, et bd00 ses répliques 1-20 (mêmes x, mêmes textes).
Upper : répliques = table 0x683C28 (version US, 0x61B570[$92(A5)] pour $92 = 1-3 : mots = décalages depuis la table,
755 répliques) ; réplique = [x][texte]0 répété (sans l'octet de longueur PSP) ; scénarios = 0x970F40 (rel16, 154
scénarios) -> mots (bit 15 = adversaire, bit 14 = 3e personnage, bits 0-9 = n° GLOBAL de réplique, 0 = fin) ; choix du scénario : 0x61B580
(avant combat) / 0x61B600 (après), octet [($13E(A5) − 8) / 2 × 40 + ID], $13E = 8 (1er combat spécial, rang 5),
10 (2e, rang 9), 12 (M. Bison) ; $FF = pas de dialogue.
Sortie : <racine SFA3MAX_CACHE>/converti/dialogues/dialogues_upper_max.s — répliques numérotées à partir de
--base (756 par défaut = suite de la table US), scénarios DLG_<ID>_<k> et proposition de rangées pour 0x61B580 / 0x61B600.
Usage : python dialogues_max.py [--base 756] [--scenario 154] | --controle"""
import os, sys, struct, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
VA = 0x74
MAX = [("Eagle", 0x26, 0x2A3198, "26"), ("Maki", 0x27, 0x2A6268, "27"), ("Yun", 0x2D, 0x2AD6DC, "28"), ("Ingrid", 0x2E, 0x2B1EE0, "29")]
# scénarios PSP (rang dans la table du mot 38) -> place dans Upper : (rangée $13E, avant / après) ; relevé sur les textes
# (R7) : 8 = 1er combat spécial, 10 = 2e, 12 = M. Bison. Plusieurs scénarios sur une même place = enchaînés.
PLACES = {
    "Eagle":  [(8, "avant"), (8, "après"), (10, "avant"), (10, "après"), (12, "avant")],   # Guile, Sagat, Balrog (*), Bison
    "Maki":   [(8, "avant"), (8, "après"), (10, "avant"), (10, "après"), (12, "avant")],   # adv. armé, Guy, Bison
    "Yun":    [(8, "avant"), (8, "après"), (10, "avant"), (10, "après"), (10, "après"), (12, "avant")],  # Dee Jay, Fei-Long, Bison
    "Ingrid": [(8, "avant"), (8, "après"), (10, "avant"), (10, "après"), (12, "avant")],   # Evil Ryu, Rose, Bison
}
NOTES = {"Eagle": "scénario 3 = face à Balrog (combat secret avant Bison) : placé après le 2e combat spécial",
         "Yun": "scénarios 3 et 4 = après Fei-Long (alliance, puis l'attaque de la base) : enchaînés"}


def lire_iso(chemin_iso, nom):
    return subprocess.run(["isoinfo", "-i", chemin_iso, "-x", "/PSP_GAME/USRDIR/eur/data/" + nom],
                          capture_output=True, check=True).stdout


def repliques_psp(bd):
    """-> liste de répliques, chacune = [(x, texte)]"""
    t = dict(split(bd))[0x10001]; out = []
    for k in range(len(t) // 0x80):
        r = t[0x80 * k:0x80 * k + 0x80]; n = r[0]; p = 1; lignes = []
        while p < n and r[p]:
            x = r[p]; e = r.index(0, p + 1); lignes.append((x, r[p + 1:e].decode("ascii"))); p = e + 1
        out.append(lignes)
    return out


def scenarios_psp(E, g, nrep):
    u = lambda o: struct.unpack_from("<I", E, VA + o)[0]
    w = lambda o: struct.unpack_from("<H", E, VA + o)[0]
    t = u(u(g + 38 * 4)); scen = []; vus = set()
    for i in range(16):
        a = u(t + 4 * i); ws = []
        if not 0x200000 < a < 0x2C0000: break
        while w(a + 2 * len(ws)): ws.append(w(a + 2 * len(ws)))
        if not ws or any(not 1 <= (x & 0x3FF) <= nrep or x & 0x3C00 for x in ws): break
        scen.append(ws); vus |= {x & 0x3FF for x in ws}
        if vus == set(range(1, nrep + 1)): break
    assert vus == set(range(1, nrep + 1)), "répliques non couvertes : %s" % sorted(set(range(1, nrep + 1)) - vus)
    return scen


def controle():
    """Ryu : bd00 + gabarit 0x23F8FC doivent redonner les scénarios 0-3 et les répliques 1-20 d'Upper"""
    UP = open(os.path.join(paths.anthology(), "decompressed", "ro5_usa_prog68k.bin"), "rb").read(); RB = 0x1F0000
    uw = lambda a: struct.unpack_from("<H", UP, a - RB)[0]
    E = open(paths.eboot(), "rb").read(); R = repliques_psp(lire_iso(paths.iso(), "bd00_e.pac"))
    S = scenarios_psp(E, 0x23F8FC, len(R)); ok = True
    for k, ws in enumerate(S):
        a = 0x970F40 + uw(0x970F40 + 2 * k); U = []
        while uw(a + 2 * len(U)): U.append(uw(a + 2 * len(U)))
        ok &= U == ws; print("  scénario %d : %s" % (k, "identique" if U == ws else "DIFFÉRENT %s / %s" % (ws, U)))
    T = 0x683C28
    for n, lignes in enumerate(R, 1):
        a, b = T + uw(T + 2 * (n - 1)), T + uw(T + 2 * n)
        brut = b"".join(bytes([x]) + t.encode("ascii") + b"\0" for x, t in lignes)
        if UP[a - RB:a - RB + len(brut)] != brut: ok = False; print("  réplique %d DIFFÉRENTE" % n)
    print("contrôle Ryu :", "OK (scénarios 0-3 et répliques 1-20 identiques à Upper)" if ok else "ÉCARTS")


def main():
    if "--controle" in sys.argv: return controle()
    base = int(sys.argv[sys.argv.index("--base") + 1]) if "--base" in sys.argv else 756
    s0 = int(sys.argv[sys.argv.index("--scenario") + 1]) if "--scenario" in sys.argv else 154
    E = open(paths.eboot(), "rb").read(); iso = paths.iso()
    L = ["; dialogues d'avant / après combat des persos MAX au format d'Upper — max/outils/convert/dialogues_max.py",
         "; répliques : à ajouter à la table US 0x683C28 (mots = décalages depuis la table) sous les n° %d et suivants ;" % base,
         "; scénarios : à ajouter à 0x970F40 (rel16) sous les n° %d et suivants ; mots = bit 15 adversaire | n° de réplique" % s0,
         "; DISPOSITION ARCADE (octets dans l'ordre de lecture du texte ; mots grand-boutistes)", ""]
    rep_lignes, scen_lignes, choix = [], [], []
    n_rep, n_scen = base, s0
    for nom, uid, g, pl in MAX:
        R = repliques_psp(lire_iso(iso, "bd%s_e.pac" % pl))
        S = scenarios_psp(E, g, len(R))
        assert len(S) == len(PLACES[nom]), (nom, len(S))
        rep_lignes.append("; ---- %s (ID $%02X) : %d répliques, n° %d-%d" % (nom, uid, len(R), n_rep, n_rep + len(R) - 1))
        for k, lignes in enumerate(R):
            rep_lignes.append("DLG_R%d:     ; %s %d" % (n_rep + k, nom, k + 1))
            for x, txt in lignes:
                rep_lignes.append('        dc.b    $%02X, "%s", 0' % (x, txt.replace('"', '""')))
        # scénarios par place (enchaînés si plusieurs scénarios PSP vont au même endroit)
        par_place = {}
        for k, ws in enumerate(S): par_place.setdefault(PLACES[nom][k], []).extend(ws)
        for (st, quand), ws in sorted(par_place.items(), key=lambda kv: (kv[0][0], kv[0][1] != "avant")):
            mots = [(x & 0xC000) | (n_rep + (x & 0x3FF) - 1) for x in ws]
            scen_lignes += ["        even", "DLG_S%d:     ; %s, $13E = %d, %s combat" % (n_scen, nom, st, quand),
                            "        dc.w    " + ", ".join("$%04X" % m for m in mots) + ", 0"]
            choix.append((uid, st, quand, n_scen)); n_scen += 1
        if nom in NOTES: scen_lignes.append("        ; %s : %s" % (nom, NOTES[nom]))
        n_rep += len(R)
    L += rep_lignes + [""] + scen_lignes + ["", "; choix des scénarios (octet = n° de scénario ; $FF ailleurs) :"]
    for uid, st, quand, n in choix:
        T = 0x61B580 if quand == "avant" else 0x61B600
        L.append(";   0x%06X[(%d - 8) / 2 * 40 + $%02X] = %d    (%s combat, $13E = %d)" % (T, st, uid, n, quand, st))
    d = os.path.join(paths.CACHE, "converti", "dialogues"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "dialogues_upper_max.s"), "w").write("\n".join(L) + "\n")
    print("écrit", os.path.join(d, "dialogues_upper_max.s"), ": répliques %d-%d, scénarios %d-%d" % (base, n_rep - 1, s0, n_scen - 1))


if __name__ == "__main__":
    main()
