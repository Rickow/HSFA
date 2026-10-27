"""Ébauches 68K des 4 persos MAX : code du MODULE du perso uniquement (gestionnaires, aides locales, tables de saut).
Les fonctions du moteur PSP sans équivalent arcade connu ne sont PAS traduites automatiquement (conventions d'appel
différentes : a0 n'y est pas toujours un objet) : elles forment l'inventaire `api_a_fournir.json` / `.md`."""
import sys, collections, json
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import modules
from charcode2 import S, fend
from traduire import Trad, ARITE, traduire_trad, mortes
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}
B = modules.module_bounds()
LO, HI = min(a for a, _ in B.values()), max(e for _, e in B.values())
SOURCES_MAIN = ("moteur_max_main.s", "gestionnaires_main.s")


def fonctions_main():
    import re as _re
    return {int(x, 16) for f in SOURCES_MAIN for x in _re.findall(r"^psp_([0-9a-f]+):", open(f).read(), _re.M)}


def bornes_max():
    """(2026-10-11, rapport agent_integration_max) Chez les persos MAX, les GESTIONNAIRES sont rangés AVANT la racine :
    le « module » [racine(c), racine(c+1)) contient la racine de c, son code atteint, PUIS les gestionnaires de c+1.
    Coupure = fin de la dernière fonction ATTEINTE depuis la racine en restant dans le module (appels, chargements
    d'adresses, tables de données) : Balrog (alt) $25 -> 0x1B0088 (0x1B0090 = début des gestionnaires d'Eagle)."""
    import bisect
    from charcode2 import P, PA, W, jal, s16, fstart, TEXT_END, img, data_span
    def atteint(r, lo, hi):
        vf, vd, todo = set(), set(), [r]
        while todo:
            a = todo.pop()
            if a < TEXT_END:
                if not (lo <= a < hi): continue
                f = fstart(a)
                if f in vf: continue
                vf.add(f); e = fend(f)
                for k in range(f // 4, e // 4):
                    w = W[k]
                    if w >> 26 == 3: todo.append(jal(w))
                    elif w >> 26 == 0x0F:
                        rt, h = (w >> 16) & 31, w & 0xFFFF
                        for m in range(k + 1, min(k + 8, e // 4)):
                            x = W[m]
                            if (x >> 21) & 31 == rt and x >> 26 in (0x09, 0x23, 0x21, 0x25, 0x20, 0x24):
                                va = ((h << 16) + s16(x & 0xFFFF)) & 0xFFFFFFFF
                                if TEXT_END <= va < len(img): todo.append(va)
                                break
            else:
                if a in vd: continue
                vd.add(a); i = bisect.bisect_left(PA, a); h_ = data_span(a)
                while i < len(PA) and PA[i] < h_:
                    t = P[PA[i]]
                    if t >= TEXT_END or lo <= t < hi: todo.append(t)
                    i += 1
        return vf
    coupe = {c: fend(max(atteint(B[c][0], *B[c]))) for c in (0x25, 0x26, 0x27, 0x28)}
    return {c: (coupe[c - 1], coupe[c] if c < 0x29 else B[c][1]) for c in NOMS}


BM = bornes_max()
def brouillon(cid, inv):
    a0, e0 = BM[cid]
    out, st = [], collections.Counter()
    main = fonctions_main()
    # (2026-10-07) cas de switch internes : traduits comme étiquettes locales de leur routine parente -> alias
    cas_de = {}
    for g in [f for f in S if a0 <= f < e0]:
        if g in main or g in mortes(): continue
        try: t, _ = traduire_trad(g)
        except Exception: continue
        for c in t.cases:
            if c != g and any(l == "L_%x:" % c for l in t.out): cas_de.setdefault(c, g)
    for g in [f for f in S if a0 <= f < e0]:
        if g in cas_de and g not in main:
            out.append("psp_%x equ L_%x       ; cas du switch de psp_%x" % (g, g, cas_de[g])); st["cas de switch"] += 1; continue
        if g in main: out.append("; psp_%x : écrite à la main (moteur_max_main.s)" % g); st["à la main"] += 1; continue
        if g in mortes():
            out += ["psp_%x:    ; effet de décor d'Ingrid (type 13) : neutralisé, jamais exécuté" % g, "        rts"]
            st["neutralisées"] += 1; continue
        try: t, L = traduire_trad(g)
        except Exception as ex: out.append("; psp_%x : échec %s" % (g, ex)); st["échecs"] += 1; continue
        out.append("psp_%x:" % g); out += L
        st["fonctions"] += 1
        st["lignes"] += sum(1 for l in L if l.strip() and not l.endswith(":") and "dc.w" not in l)
        st["??"] += sum("??" in l for l in L); st["son"] += sum("SON" in l for l in L); st["tables de saut"] += len(t.tables)
        for h in t.sous:
            if not (a0 <= h < e0):
                inv[h][NOMS[cid]] += sum(l.count("psp_%x" % h) for l in L if "bsr" in l or "bra" in l)
    return out, st
if __name__ == "__main__":
  for _passe in (1, 2):              # (2026-10-17) 2e passe si le relevé des tailles d'accès PSP (traduire.ACCES) a changé
    inv = collections.defaultdict(collections.Counter)
    for cid, nom in NOMS.items():
        out, st = brouillon(cid, inv)
        open(f"brouillon_{nom}.s", "w").write("; ÉBAUCHE 68K (code du module du perso) générée par traduire.py — à relire\n"
                                              "; « bsr/bra psp_xxxxxx » hors module : fonction moteur à fournir (api_a_fournir.md)\n" + "\n".join(out) + "\n")
        print(nom, dict(st), "-> %.0f %% de lignes traduites" % (100 * (1 - st["??"] / st["lignes"])))
    rows = sorted(((sum(v.values()), h, dict(v)) for h, v in inv.items()), reverse=True)
    # tri : traduisibles automatiquement (objet en a0, aucun « ?? ») / à écrire à la main
    sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
    from relocs import img
    from mips import decode
    def a0_objet(f):
        """a0 est un objet si son PREMIER emploi (avant d'être écrasé) est une base d'accès ou une copie (or rX,a0,zero)"""
        for i in decode(img, f, fend(f)):
            if i.m in ("lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw") and i.rs == 4: return True
            if i.m == "or" and i.fn == 0x25 and 4 in (i.rs, i.rt) and 0 in (i.rs, i.rt): return True
            if i.m == "jal": return True                     # transmis tel quel à une fonction (objet)
            lit = (i.op == 0 and 4 in (i.rs, i.rt)) or (i.op != 0 and i.rs == 4 and i.m not in ("sw", "sh", "sb"))
            if lit: return False
            ecrit = (i.op == 0 and i.rd == 4) or (i.op != 0 and i.rt == 4 and i.m not in ("sw", "sh", "sb", "beq", "bne"))
            if ecrit: return True                            # a0 écrasé sans avoir été lu : rien n'indique un nombre
        return True
    import re as _re
    main = fonctions_main()
    # (2026-10-07) fonctions du module d'un AUTRE perso MAX (Maki appelle du code rangé dans le module de Yun, Yun dans
    # celui d'Ingrid) : déjà traduites dans l'ébauche de ce perso -> ni à écrire ni à traduire ici
    module = set()
    for _n in ("eagle", "maki", "yun", "ingrid"):
        module |= {int(x, 16) for x in _re.findall(r"^psp_([0-9a-f]+)(?::| equ)", open("brouillon_%s.s" % _n).read(), _re.M)}
    rows = [r for r in rows if r[1] not in module]
    auto, sortie = set(), []
    # (2026-10-07) fermeture transitive : fonctions appelées par les fonctions moteur traduites (et par le code à la main)
    connus = {h for _, h, _ in rows} | main | module
    texte_main = "".join(open(f).read() for f in SOURCES_MAIN)
    a_voir = list(rows) + [(0, int(x, 16), {}) for x in set(_re.findall(r"\b(?:bsr|bra|jsr|jmp)\s+psp_([0-9a-f]+)", texte_main))
                           if int(x, 16) not in connus]
    connus |= {h for _, h, _ in a_voir}
    k_ = 0
    while k_ < len(a_voir):
        n, h, v = a_voir[k_]; k_ += 1
        if h in main: continue                              # écrite à la main (moteur_max_main.s) : fait foi
        try: t_, L = traduire_trad(h)
        except Exception: continue
        if not any("??" in l for l in L) and a0_objet(h):
            auto.add(h); sortie += ["psp_%x:    ; fonction moteur PSP traduite automatiquement (%d appels)" % (h, n)] + L
            for g_ in t_.sous:
                if g_ not in connus and g_ < 0x1F8000: connus.add(g_); a_voir.append((0, g_, {}))
    rows = [r for r in a_voir if r[1] not in main or r in rows]
    open("moteur_max_auto.s", "w").write("; Fonctions moteur PSP des persos MAX traduites automatiquement (objet en a0, aucun « ?? ») — à relire\n" + "\n".join(sortie) + "\n")
    json.dump([{"psp": "%x" % h, "appels": n, "par_perso": v, "arite": ARITE.get(h), "taille": fend(h) - h,
                "moteur_commun": LO > h or h >= HI, "auto": h in auto, "main": h in main} for n, h, v in rows], open("api_a_fournir.json", "w"), indent=0)
    with open("api_a_fournir.md", "w") as f:
        f.write("# Fonctions PSP appelées par les persos MAX sans équivalent arcade connu\n\n"
                "« auto » = traduite automatiquement dans `moteur_max_auto.s` ; sinon à écrire à la main.\n\n"
                "| PSP | appels | Eagle | Maki | Yun | Ingrid | arité | taille (o) | traduction |\n|---|---|---|---|---|---|---|---|---|\n")
        for n, h, v in rows:
            f.write("| `%x` | %d | %s | %s | %s | %s | %s | %d | %s |\n" % (h, n, v.get("eagle", ""), v.get("maki", ""), v.get("yun", ""), v.get("ingrid", ""), ARITE.get(h, "?"), fend(h) - h, "auto" if h in auto else ("main (moteur_max_main.s)" if h in main else "**à écrire**")))
    reste = [(n, h) for n, h, v in rows if h not in auto and h not in main]
    from traduire import ecrire_donnees
    print("tables de données PSP recopiées (donnees_max.s) :", ecrire_donnees())
    print("auto : %d (%d appels) ; à la main : %d (%d appels) ; à écrire : %d (%d appels, %.1f Ko)" % (len(auto), sum(n for n, h, v in rows if h in auto),
          len(main & {h for _, h, _ in rows}), sum(n for n, h, v in rows if h in main), len(reste), sum(n for n, h in reste), sum(fend(h) - h for n, h in reste) / 1024))
    print("fonctions à fournir :", len(rows), "; appelées par >= 2 persos :", sum(1 for n, h, v in rows if len(v) >= 2),
          "; taille totale %.1f Ko" % (sum(fend(h) - h for n, h, v in rows) / 1024))
    import traduire as _T
    if not _T.sauver_acces(): break
    print("relevé des tailles d'accès PSP changé (acces_psp.json) : 2e passe")
