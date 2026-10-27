"""Blocs d'animations des FINS MAX (FIN_ANIM_26-FIN_ANIM_29) -> données 68K en DISPOSITION ARCADE, 2026-10-10.
PSP : les acteurs de fin prennent leur animation n dans la table +$110 de l'état de fin 0x87FCB0 (0x1D4C48, homologue
de $AA630), construite par le chargeur 0x1DB424 depuis le pac de la fin : +$110[n] = pas10 (section 0x20001) +
10 × index (0x20003)[n] ; boîtes = 0x20005 (+$114) ; (+$118 = pas8 0x20002 indexés par 0x20004 : images fixes).
Pour un acteur dont la banque est le perso MAX de la fin, les n° de frame désignent les FRAMES DE COMBAT du perso
(Eagle : ≤ 408 sur 723) -> symboles F%02X_n de frames_max.py (Ingrid : renumérotation remap_ingrid).
Intégration (HSFA, 2026-10-10) : la table des banques d'acteurs d'Upper (T_619b50, homologue de $AA644, lue
seulement par les acteurs) reçoit FIN_ANIM_26+k en $26+k ; le combat garde ANIM_xx. Banques 38-41 employées
uniquement dans la fin de leur perso (vérifié sur les 42 fins PSP).
Format = banque arcade : mots signés relatifs au début de la table, pas de 20 o, reprise en +$14.
Sortie : fin_anims_XX.s (bloc $D70000 + $40000 k), symboles dans symboles_anims_max.s (avec anims_max.py).
Usage : python3 anims_fins_max.py"""
import os, sys, re, json, struct
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
from anims_max import symboles_frames, NOMS
PAC = os.path.expanduser("~/.cache/sfa3max/data/textes/end%02x_e.pac")
BASES = {0x26: 0xD70000, 0x27: 0xDB0000, 0x28: 0xDF0000, 0x29: 0xE30000}
TAILLE = 0x10000


def remap(cid):
    if cid != 0x29: return {}
    from tables_explicites import remap_ingrid
    return remap_ingrid()


def employees(cid):
    """n° d'animation des acteurs de la banque du perso dans sa fin (enregistrements PSP, +3)"""
    sys.path.insert(0, os.path.join(ICI, "..", "convert"))
    import rosette_donnees as R
    return sorted({r[3] for g in R.groupes_psp(R.eboot(), cid) for r in g if r[0x1F] == cid})


def construire(cid, SF):
    D = {t: d for t, d in split(open(PAC % cid, "rb").read())}
    idx = list(struct.unpack_from("<%dH" % (len(D[0x20003]) // 2), D[0x20003]))
    idx = idx[:idx.index(0xFFFF)] if 0xFFFF in idx else idx
    st, bx = D[0x20001], D[0x20005]; rm = remap(cid); used = employees(cid)
    S, alertes = {}, []                                    # n° de pas -> (d, fl, frame, écart, col)
    for v in idx:
        for k in range(120):
            p = v + k
            if 10 * p + 10 > len(st): alertes.append("anim au pas %d : sort de la section" % v); break
            S.setdefault(p, struct.unpack_from("<5H", st, 10 * p))
            if S[p][0] & 0xC000: break
    base = BASES[cid]; nom = "FIN_ANIM_%02X" % cid; lab = lambda p: "FP%02X_%d" % (cid, p)
    b = bytearray(); adr = {}; fix = []
    asm = ["; animations de la fin $%02X (%s, table PSP +$110 du pac) — généré par anims_fins_max.py, DISPOSITION ARCADE"
           % (cid, NOMS[cid]), "; n° employés par les acteurs de la banque $%02X : %s" % (cid, used),
           "        org     $%06X" % base, "%s:" % nom]
    adr[nom] = base
    for n, v in enumerate(idx):
        fix.append((len(b), lab(v))); b += b"\0\0"
        asm.append("        dc.w    %s-%s%s" % (lab(v), nom, "          ; n° %d (acteurs)" % n if n in used else ""))
    for p in sorted(S):
        d, fl, fr, ec, col = S[p]; adr[lab(p)] = base + len(b)
        b += bytes([d & 0xFF, d >> 8, fl & 0xFF, fl >> 8])
        asm += ["%s:" % lab(p), "        dc.b    $%02x, $%02x, $%02x, $%02x" % (d & 0xFF, d >> 8, fl & 0xFF, fl >> 8)]
        f = "F%02X_%d" % (cid, rm.get(fr, fr))
        if fr == 0xFFFF: b += bytes(4); asm.append("        dc.l    0                  ; pas d'image")
        elif f in SF: b += struct.pack(">I", SF[f]); asm.append("        dc.l    %s                ; frame PSP %d" % (f, fr))
        else:
            b += bytes(4); asm.append("        dc.l    0                  ; ⚠ frame PSP %d hors des frames du perso" % fr)
            alertes.append("pas %d : frame %d absente" % (p, fr))
        abc = bx[12 * col: 12 * col + 12] if 12 * col + 12 <= len(bx) else bytes(12)
        if 12 * col + 12 > len(bx): alertes.append("pas %d : jeu de boîtes %d absent (0)" % (p, col))
        b += abc; asm.append("        dc.b    " + ", ".join("$%02x" % x for x in abc))
        if d & 0x8000:
            q = p + (ec - 0x10000 if ec >= 0x8000 else ec)
            if q not in S: alertes.append("pas %d : reprise %d hors des pas émis" % (p, q)); q = p
            fix.append((len(b), lab(q), True)); b += bytes(4); asm.append("        dc.l    %s                ; reprise" % lab(q))
        elif not d & 0x4000 and p + 1 not in S: alertes.append("pas %d : suite interrompue" % p)
    for x in fix:
        if len(x) == 3: struct.pack_into(">I", b, x[0], adr[x[1]])
        else:
            dv = adr[x[1]] - base; assert 0 <= dv <= 0x7FFF; struct.pack_into(">H", b, x[0], dv)
    assert len(b) <= TAILLE
    return bytes(b), adr, asm, alertes, len(idx), used


if __name__ == "__main__":
    SF = symboles_frames(); sym = []
    for cid in sorted(BASES):
        b, adr, asm, al, n, used = construire(cid, SF)
        open(os.path.join(ICI, "fin_anims_%s.s" % NOMS[cid]), "w").write("\n".join(asm) + "\n")
        open(os.path.expanduser("~/.cache/sfa3max/fin_anims_%02x.bin" % cid), "wb").write(b)
        sym.append("FIN_ANIM_%02X equ $%06X" % (cid, BASES[cid]))
        al_u = [a for a in al if "frame" not in a]
        print("$%02X %-6s : %d animations (acteurs : %s), %d octets%s" % (cid, NOMS[cid], n, used, len(b),
              "".join("\n    ⚠ " + x for x in al[:10])))
    f = os.path.join(ICI, "symboles_anims_max.s"); L = [l for l in open(f).read().splitlines() if not l.startswith("FIN_ANIM_")]
    open(f, "w").write("\n".join(L + sym) + "\n")
