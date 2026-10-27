"""Textes des persos dans SFA3 MAX (PSP), en ASCII, enregistrements de 0x80 octets :
  octet 0 = nombre total de caractères des lignes ; puis, par ligne, 1 octet de position + texte terminé par 0.
Fichiers (ISO, dossier USRDIR/eur/data, extraits en lecture seule dans ~/.cache/sfa3max/data/textes) :
  winXX_e.pac entrée 5 (type 0x10002) : 8 citations de victoire (2 lignes) — mêmes textes que l'arcade chez Ryu ;
  opXX_e.pac  entrée 3 (type 0x10000) : biographie ; entrée 4 (0x10004) : fiche (PERSONAL DATA, taille, poids…) ;
  endXX_e.pac entrée 14 (type 0x10003) : dialogues du scénario (avant le boss) et de la fin.
Sortie : ~/.cache/sfa3max/converti/plXX/textes.json + textes.txt"""
import os, sys, json
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
import paths
from plpac import split
SRC = os.path.expanduser("~/.cache/sfa3max/data/textes")
def entree(f, typ):
    for t, d in split(open(os.path.join(SRC, f), "rb").read()):
        if t == typ: return d
    return None
def enregistrements(d, taille=0x80):
    out = []
    for r in range(0, len(d) - taille + 1, taille):
        rec = d[r:r + taille]
        if not rec[0]: out.append(None); continue
        lignes, i = [], 1
        while i < len(rec) and rec[i]:
            x = rec[i]; j = rec.index(0, i + 1) if 0 in rec[i + 1:] else len(rec)
            lignes.append({"x": x, "texte": rec[i + 1:j].decode("ascii", "replace")}); i = j + 1
        out.append({"total": rec[0], "lignes": lignes})
    return out
def fiche(d):
    return [s.decode("ascii", "replace").rstrip() for s in d.split(b"\0") if s.strip()]
def textes(cid):
    xx = "%02x" % cid
    return {"citations": enregistrements(entree(f"win{xx}_e.pac", 0x10002)),
            "bio": enregistrements(entree(f"op{xx}_e.pac", 0x10000)),
            "fiche": fiche(entree(f"op{xx}_e.pac", 0x10004)),
            "scenario_et_fin": enregistrements(entree(f"end{xx}_e.pac", 0x10003))}
if __name__ == "__main__":
    for cid in (0x26, 0x27, 0x28, 0x29):
        T = textes(cid); d = os.path.join(paths.CACHE, "converti", "pl%02x" % cid); os.makedirs(d, exist_ok=True)
        json.dump(T, open(os.path.join(d, "textes.json"), "w"), indent=1, ensure_ascii=False)
        with open(os.path.join(d, "textes.txt"), "w") as f:
            for fam in ("citations", "bio", "scenario_et_fin"):
                f.write(f"== {fam}\n")
                for k, r in enumerate(T[fam]):
                    if r: f.write("%3d  %s\n" % (k, " / ".join(l["texte"] for l in r["lignes"])))
            f.write("== fiche\n" + "\n".join(T["fiche"]) + "\n")
        print("pl%02x" % cid, {k: (len([r for r in v if r]) if k != "fiche" else len(v)) for k, v in T.items()})
