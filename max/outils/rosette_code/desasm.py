"""Désassemblage annoté d'une fonction PSP (EBOOT) : python desasm.py <adresse hex> [fin hex]
Annote : appels (équivalent arcade connu via traduire.API, statut dans api_a_fournir.json), champs d'objet (carte
PSP -> 68K de traduire.champ) sur les accès via a0/s0..., cibles de branchement en étiquettes."""
import sys, json
from traduire import img, decode, REG, fend, API, champ
INV = {int(f["psp"], 16): f for f in json.load(open("api_a_fournir.json"))}
def statut(t):
    if t in API: return "= arcade $%X" % API[t]
    f = INV.get(t)
    if f: return "moteur PSP (%s, arité %s)" % ("auto" if f.get("auto") else "main" if f.get("main") else "À ÉCRIRE", f.get("arite"))
    return "?"
def liste(f, end=None):
    end = end or fend(f); ins = list(decode(img, f, end))
    cibles = {i.va + 4 + i.simm * 4 for i in ins if i.m.startswith("b") and i.m not in ("break",)}
    out = []
    for i in ins:
        s = repr(i); note = ""
        if i.m == "jal": note = statut(i.tgt)
        elif i.m in ("lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw") and REG[i.rs] in ("a0", "s0", "s1", "s2", "s3"):
            try:
                t, o = champ(i.simm, {"lb": 1, "lbu": 1, "sb": 1, "lh": 2, "lhu": 2, "sh": 2}.get(i.m, 4))
                if o is not None: note = "champ PSP %#x -> 68K $%X (%s)" % (i.simm, o, t)
            except Exception: pass
        lab = "L%x:" % i.va if i.va in cibles else ""
        out.append("%-8s %6x  %-34s %s" % (lab, i.va, s, ("; " + note) if note else ""))
    return "\n".join(out)
if __name__ == "__main__":
    f = int(sys.argv[1], 16); end = int(sys.argv[2], 16) if len(sys.argv) > 2 else None
    print(liste(f, end))
