"""Tables de scripts passées PAR ADRESSE au moteur (psp_cfd9c : animation n d'une table explicite), converties en
données 68K. Format d'un pas 68K (ROM arcade, vérifié) : dc.b durée, drapeaux de fin, drapeau bas, drapeau haut ;
dc.l pointeur de frame ; 12 octets A/B/C = entrée de boîtes PSP telle quelle. Après un dernier pas « reprise »
(drapeaux bit 7) : dc.l pointeur du pas de reprise (lu en +$14 par l'arcade, 0x2A80A) = pas + écart (champ +6 du pas PSP).
Sorties : tables_explicites_<perso>.s (+ .json : adresses PSP des tables, pour le traducteur)."""
import sys, os, struct, json, collections
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max")); sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "src", "hsfa"))
import paths, modules
from relocs import img, TEXT_END
from mips import decode
from charcode2 import P
from plpac import split
from traduire import refs_code
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}
CIBLES = {0xCFD9C: 5, 0xCFB6C: 5}              # fonction -> registre de l'argument « table » (a1)
FORMAT = {0xCFD9C: "pas10", 0xCFB6C: "pas8"}   # pas standard (10 o) / petit pas d'objet fils (8 o, lu par 0x1D96C)
# (2026-10-07) tables désignées DANS une fonction moteur (et non passées par le module) : 0x79F88 (Yun) -> 0x220120
EXTRA = {0x28: [(0x220120, "pas8")]}
def appels_tables(cid):
    a0, e0 = modules.module_bounds()[cid]; ins = list(decode(img, a0, e0)); R = {}; out = set()
    for k, i in enumerate(ins):
        if i.m == "lui": R[i.rt] = i.imm << 16
        elif i.m == "addiu" and i.rs in R: R[i.rt] = (R[i.rs] + i.simm) & 0xFFFFFFFF
        elif i.m == "jal":
            nx = ins[k + 1]
            if nx.m == "addiu" and nx.rs in R: R[nx.rt] = (R[nx.rs] + nx.simm) & 0xFFFFFFFF
            r = CIBLES.get(i.tgt)
            if r and R.get(r) and TEXT_END <= R[r] < 0x2d5000: out.add((R[r], FORMAT[i.tgt]))
            R = {}
        elif i.op == 0 and i.rd in R: R.pop(i.rd)
    return sorted(out)
def boites(cid):
    b6 = split(open(os.path.join(paths.pac_dir(), "pl%02x_e.pac" % cid), "rb").read())[6][1]
    bx = 0x208 if cid == 0x28 else struct.unpack_from("<I", b6, 28)[0] + 0x208
    return b6, bx
def remap_ingrid():
    """même renumérotation que convert_max.merge_ingrid (pose k = haut k + bas k), sans tout reconvertir"""
    sys.path.insert(0, "../convert")
    from convert_max import INGRID_LOWER, INGRID_UPPER
    from frames import frames
    nF = len(frames(split(open(os.path.join(paths.pac_dir(), "pl29_e.pac"), "rb").read())[0][1]))
    remap = {}
    for k, (lo, up) in enumerate(zip(INGRID_LOWER, INGRID_UPPER)): remap[lo] = remap[up] = k
    n = len(INGRID_LOWER)
    for f in range(nF):
        if f not in remap: remap[f] = n; n += 1
    return remap
# (2026-10-17, projectile d'Ingrid sans dégâts) tables d'animations des PROJECTILES -> table de jeux de boîtes du tir
# (champ PSP +0x164 posé par l'état 0 du tir : 0x1B3F38, 0x1C13EC…, 0x1C797C ; lue par 0x72894 : octet 0 = index de la
# table $88 du tir, octet 1 = n° d'attaque $A0). Les pas d'un tir prennent leurs 12 octets de boîtes dans CETTE table, pas
# dans le jeu de boîtes du perso. Ordre : celui de la PSP, comme les jeux de boîtes des persos (anims_*.s) : PSP 0x6FF54 et
# 0x6C944 lisent l'octet 1 (attaque) du jeu +0x128 pour les tirs comme pour les persos. (2026-10-27, Q16.1 de l'intégration :
# l'ancien échange deux à deux des 12 octets faisait lire l'octet $88 comme attaque ; supprimé.)
BOITES_TIRS = {0x2A017C: 0x2A0184, 0x2AA05C: 0x2AA4AC, 0x2AEFDC: 0x2AF024}   # Eagle, Yun (table réservée à ses objets tirés), Ingrid

def convertir(cid):
    """pas standard (10 o : durée, drapeau, frame, écart, boîtes) et petits pas d'objets fils (8 o : durée,
    drapeaux, 2 octets, frame u16, écart s16) -> pas 68K de 20 o ; étiquette par pas (P_<adresse PSP>) ; reprise =
    pas + écart (validé 166/166 sur Ryu pour le format standard)"""
    b6, bx = boites(cid); refs = refs_code()
    rm = remap_ingrid() if cid == 0x29 else {}
    lignes, js, scripts, alertes = [], {}, {}, collections.Counter()
    for t, fmt in appels_tables(cid) + EXTRA.get(cid, []):
        ent, k = [], 0
        while (t + 4 * k) in P and not (k and (t + 4 * k) in refs): ent.append(P[t + 4 * k]); k += 1
        js["%x" % t] = {"format": fmt, "scripts": ["%x" % e for e in ent]}
        lignes.append("TAB_%x:                ; table PSP %#x (%d scripts, %s)" % (t, t, len(ent), fmt))
        lignes += ["        dc.l    P_%x" % e for e in ent]
        for e in ent: scripts[e] = (fmt, BOITES_TIRS.get(t))
    faits = set()
    for s0, (fmt, btir) in sorted(scripts.items()):
        taille = 10 if fmt == "pas10" else 8
        a = s0
        for n in range(120):
            if a in faits: lignes.append("        ; (suite déjà émise : P_%x)" % a); break
            faits.add(a)
            if fmt == "pas10":
                d, fl, fr, ecart, col = struct.unpack_from("<5H", img, a)
                abc = img[btir + 12 * col: btir + 12 * col + 12] if btir else b6[bx + 12 * col: bx + 12 * col + 12]
            else:
                d, fl = struct.unpack_from("<2H", img, a); fr, ecart = struct.unpack_from("<Hh", img, a + 4)
                abc = bytes(12)
            ecart = ecart - 0x10000 if ecart >= 0x8000 else ecart
            lignes.append("P_%x:" % a)
            lignes.append("        dc.b    $%02x, $%02x, $%02x, $%02x" % (d & 0xFF, d >> 8, fl & 0xFF, fl >> 8))
            if fr == 0xFFFF: lignes.append("        dc.l    0                  ; pas d'image (PSP 0xFFFF)")
            else: lignes.append("        dc.l    F%02X_%d                ; frame PSP %d (index frames.json du perso $%02X)" % (cid, rm.get(fr, fr), fr, cid))
            lignes.append("        dc.b    " + ", ".join("$%02x" % x for x in abc) + ("" if fmt == "pas10" else "   ; ⚠ boîtes A/B/C absentes du format PSP"))
            if d & 0x8000: lignes.append("        dc.l    P_%x                ; reprise (écart %d)" % (a + taille * ecart, ecart)); break
            if d & 0x4000: break
            if ecart != 1: alertes["écart != 1 hors fin"] += 1
            a += taille * ecart
    if alertes: lignes.insert(0, "; ⚠ " + str(dict(alertes)) + " : pas non consécutifs, ordre 68K à vérifier")
    return lignes, js

if __name__ == "__main__":
    tout = {}
    for cid, nom in NOMS.items():
        L, js = convertir(cid); tout.update(js)
        open("tables_explicites_%s.s" % nom, "w").write("; Tables de scripts passées par adresse (psp_cfd9c), converties en pas 68K — %s\n" % nom + "\n".join(L) + "\n")
        print(nom, len(js), "tables,", sum(len(v["scripts"]) for v in js.values()), "scripts", {k: v["format"] for k, v in js.items()})
    json.dump(tout, open("tables_explicites.json", "w"), indent=0)
