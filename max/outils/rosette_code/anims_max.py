"""Tables d'animations MAÎTRESSES des persos MAX (ANIM_26-ANIM_29) -> données 68K en DISPOSITION ARCADE, 2026-10-10.
Convention HSFA : ordre EXACT de animations.json (= numérotation PSP), une sous-table par table de coups.
Modèle arcade (vérifié sur sfa3ud) : init $2FC4A recopie depuis $DD412[perso] (3 ismes × 16 o) les longs
$2B0, $2B8, $2B4, $2BC ; Ryu = un seul bloc $146218 ($2B0 = début du bloc = banque $AA644[perso] des acteurs de fin).
Lancement $2A708…$2A762 / $1B6E0 : A0 = sous-table, D0 = n° -> lea (A0, mot[n]) : décalages en MOTS SIGNÉS RELATIFS
AU DÉBUT DE CHAQUE SOUS-TABLE (donc ≤ $7FFF).
Pas de 20 o (format de tables_explicites.py) : dc.b durée, drapeaux (bit 7 reprise, bit 6 fin), drapeau bas, drapeau
haut ; dc.l frame (F%02X_n) ; 12 o A/B/C (jeu de boîtes PSP tel quel) ; après un dernier pas à reprise : dc.l pas de
reprise (lu en +$14). Les pas sont émis par suites CONTIGUËS de la numérotation PSP : deux animations qui partagent la
fin d'une suite partagent les pas (comme dans le tableau PSP).
Bloc : moitié haute du bloc externe des frames ($D60000 / $DA0000 / $DE0000 / $E20000) ; symboles F%02X_n dans
symboles_frames_max.s. Sortie : anims_XX.s + symboles_anims_max.s (ANIM_xx… equ adresse), ~/.cache/sfa3max/anims_XX.bin.
Usage : python3 anims_max.py"""
import os, re, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
CONV = os.path.expanduser("~/.cache/sfa3max/converti")
BASES = {0x26: 0xD60000, 0x27: 0xDA0000, 0x28: 0xDE0000, 0x29: 0xE20000}
TAILLE = 0x20000
NOMS = {0x26: "eagle", 0x27: "maki", 0x28: "yun", 0x29: "ingrid"}
TABLES = ("$2B0", "$2B4", "$2B8", "$2BC")          # ordre de animations.json


def symboles_frames():
    s = {}
    for l in open(os.path.join(ICI, "symboles_frames_max.s")):
        m = re.match(r"^(F2[6-9]_\d+) equ \$([0-9A-F]+)", l)
        if m: s[m.group(1)] = int(m.group(2), 16)
    return s


def construire(cid, SF):
    A = json.load(open(os.path.join(CONV, "pl%02x" % cid, "animations.json")))
    cle = lambda x: x.get("pas_psp", x.get("eboot"))
    unite = lambda x: 1 if "pas_psp" in x else 10         # pas_psp = n° de pas ; eboot = adresse (10 o par pas)
    S = {}; reprises = {}; alertes = []                   # position absolue -> pas ; position -> position de reprise
    for t in TABLES:
        for x in A[t]:
            if not x["steps"]:
                alertes.append("%s n°%d : script illisible -> animation vide" % (t, x["n"])); continue
            v, u = cle(x), unite(x)
            for k, st in enumerate(x["steps"]): S.setdefault(v + u * k, st)
            if x.get("reprise") is not None: reprises[v + u * (len(x["steps"]) - 1)] = v + u * x["reprise"]
    lab = lambda p: "P%02X_%x" % (cid, p)
    base = BASES[cid]; b = bytearray(); adr = {}; asm = []; fix = []    # fix : (position octet, étiquette visée, relatif à)
    asm += ["; animations de combat du perso $%02X (%s) — généré par anims_max.py, DISPOSITION ARCADE" % (cid, NOMS[cid]),
            "        org     $%06X" % base]
    # sous-tables (ordre animations.json) ; ANIM_xx = $2B0 = banque des acteurs de fin
    vide = "P%02X_VIDE" % cid
    for t in TABLES:
        nom = "ANIM_%02X" % cid if t == "$2B0" else "ANIM_%02X_%s" % (cid, t[1:])
        adr[nom] = base + len(b); asm.append("%s:                ; table %s, %d animations" % (nom, t, len(A[t])))
        for x in A[t]:
            cible = lab(cle(x)) if x["steps"] else vide
            fix.append((len(b), cible, nom)); b += b"\0\0"
            asm.append("        dc.w    %s-%s" % (cible, nom))
    adr["ANIM_%02X_PTRS" % cid] = base + len(b)
    asm.append("ANIM_%02X_PTRS:                ; format $DD412 (×3 ismes) : $2B0, $2B8, $2B4, $2BC" % cid)
    for _ in range(3):
        for t in ("$2B0", "$2B8", "$2B4", "$2BC"):
            nom = "ANIM_%02X" % cid if t == "$2B0" else "ANIM_%02X_%s" % (cid, t[1:])
            fix.append((len(b), nom, None)); b += b"\0\0\0\0"; asm.append("        dc.l    %s" % nom)
    # animation vide (script illisible) : un pas sans image qui se termine
    adr[vide] = base + len(b); b += bytes([1, 0x40, 0, 0]) + bytes(16)
    asm += ["%s:" % vide, "        dc.b    $01, $40, $00, $00", "        dc.l    0", "        dcb.b   12, 0"]
    for p in sorted(S):
        st = S[p]; adr[lab(p)] = base + len(b)
        d, fl = st["ctl"] & 0xFFFF, st["ctl"] >> 16
        b += bytes([d & 0xFF, d >> 8, fl & 0xFF, fl >> 8])
        asm += ["%s:" % lab(p), "        dc.b    $%02x, $%02x, $%02x, $%02x" % (d & 0xFF, d >> 8, fl & 0xFF, fl >> 8)]
        fr = st["frame"]
        if fr == 0xFFFF: b += b"\0" * 4; asm.append("        dc.l    0                  ; pas d'image (PSP 0xFFFF)")
        else:
            f = "F%02X_%d" % (cid, fr)
            if f not in SF: alertes.append("%s absente de symboles_frames_max.s" % f)
            b += struct.pack(">I", SF.get(f, 0)); asm.append("        dc.l    %s" % f)
        abc = [st[k] for k in "ABC"]
        if None in abc: alertes.append("%s : boîtes A/B/C absentes" % lab(p)); abc = [0, 0, 0]
        r = struct.pack("<3I", *abc); b += r
        asm.append("        dc.b    " + ", ".join("$%02x" % x for x in r))
        if d & 0x8000:
            q = reprises.get(p, p)
            if q not in S: alertes.append("%s : reprise hors des pas émis" % lab(p)); q = p
            fix.append((len(b), lab(q), None)); b += b"\0" * 4; asm.append("        dc.l    %s                ; reprise" % lab(q))
        elif not d & 0x4000 and (p + (1 if cid != 0x28 else 10)) not in S:
            alertes.append("%s : suite interrompue (pas suivant non émis)" % lab(p))
    for o, cible, rel in fix:
        if rel is None: struct.pack_into(">I", b, o, adr[cible])
        else:
            dv = adr[cible] - adr[rel]
            assert 0 <= dv <= 0x7FFF, "%s-%s = %#x hors mot signé" % (cible, rel, dv)
            struct.pack_into(">H", b, o, dv)
    assert len(b) <= TAILLE, "perso $%02X : %d o > %d" % (cid, len(b), TAILLE)
    return bytes(b), adr, asm, alertes, len(S)


if __name__ == "__main__":
    SF = symboles_frames(); sym = ["; tables d'animations maîtresses MAX — généré par anims_max.py"]
    for cid in sorted(BASES):
        b, adr, asm, al, n = construire(cid, SF)
        open(os.path.join(ICI, "anims_%s.s" % NOMS[cid]), "w").write("\n".join(asm) + "\n")
        open(os.path.expanduser("~/.cache/sfa3max/anims_%02x.bin" % cid), "wb").write(b)
        sym += ["%s equ $%06X" % (k, v) for k, v in sorted(adr.items()) if k.startswith("ANIM_")]
        print("$%02X %-6s : %d pas, %6d octets (bloc $%06X)%s" % (cid, NOMS[cid], n, len(b), BASES[cid],
              "".join("\n    ⚠ " + x for x in al[:12]) + ("\n    … %d alertes" % len(al) if len(al) > 12 else "")))
    open(os.path.join(ICI, "symboles_anims_max.s"), "w").write("\n".join(sym) + "\n")
