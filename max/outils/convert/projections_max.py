"""Positions de l'adversaire pendant une projection / saisie (2026-10-18, chope du bond de Maki décalée).
Arcade : $2F9BE / $2FA36 (tenue de la victime, chaque image) lisent $DD212[attaquant $102] -> bloc : un mot par victime
($102 de la victime ; décalage depuis le bloc), puis des fiches de 8 o indexées par l'octet +$10 du pas courant de
l'attaquant : dx.w (signe selon $B), dy.w, octet (bit 7 -> $CD de la victime), octet (& 3, xor $B -> $B de la victime),
pose.w (-> $2FC36). Upper : table `7495b8` ; pour les persos MAX, HSFA y avait mis une COPIE de la ligne de Ryu.
PSP : FUN_00069DCC (homologue) lit l'espace de travail +0x24 -> pointeurs par victime (0x152), fiche = pas +8 × 8 o :
dx, dy, mot de drapeaux (< 0 -> 0x105 = $FF ; octet bas & 3 = sens), pose (FUN_0006A238). L'espace de travail est rempli
à l'init (FUN_0006AB48, octet $C de la table du perso = section s du répertoire de l'entrée 0x11 du pac plXX, celle de
42 entrées : 21 en général, 16 chez Yun ; données à +0x208) : un u32 par victime (n° de sous-table), sous-table k =
section s + 1 + k.
Conversion (contrôle : fiches des victimes 0-$1F identiques à l'arcade, voir controle()) : dx, dy tels quels ; octet 1 = $80 si
drapeaux < 0 ; octet 2 = drapeaux & $FF ; pose arcade = 20 × pose PSP.
Colonnes de victimes : 0-$27 = victimes PSP 0-$27 ; $2D (Yun) = PSP $28 ; $2E (Ingrid) = PSP $29 ; les pseudo-ID
d'Upper ($28-$2C, $2F) prennent la colonne de Ryu (PSEUDO). Les lignes natives d'Upper (7495b8) n'ont que 40 colonnes
(victimes 0-$27) : une victime $2D / $2E y lit hors table (à étendre côté HSFA, données PSP disponibles).
Sortie : rosette_code/projections_max.s (PROJ_POS_26 / 27 / 2D / 2E, à mettre dans `7495b8` aux lignes $26/$27/$2D/$2E).
Usage : python projections_max.py [controle]"""
import os, sys, struct
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
PAC = os.path.expanduser("~/.cache/sfa3max/pac/%s_e.pac")
ROM = os.path.expanduser("~/.cache/sfa3max/sfa3ud_donnees.bin")
SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rosette_code", "projections_max.s")
PERSOS = [("26", "pl26", "Eagle"), ("27", "pl27", "Maki"), ("2D", "pl28", "Yun"), ("2E", "pl29", "Ingrid")]
PSEUDO = {u: 0x00 for u in (0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2F)}   # pseudo-ID Upper -> victime PSP (jamais victimes : colonne de Ryu)


def section_victimes(pl):
    D = dict(split(open(PAC % pl, "rb").read())); h = D[0x11]; b = h[0x208:]
    offs = struct.unpack_from("<64i", h, 8); cnt = struct.unpack_from("<64i", h, 0x108)
    s = cnt.index(42)                         # section des victimes (21 chez la plupart, 16 chez Yun ; octet $C de la table du perso)
    idx = [struct.unpack_from("<I", b, offs[s] + 4 * k)[0] for k in range(cnt[s])]
    subs = {}
    for k in sorted(set(idx)):
        p = offs[s + 1 + k]; q = next(o for o in offs[s + 2 + k:] + (len(b),) if o > p)
        subs[k] = [struct.unpack_from("<4h", b, p + 8 * j) for j in range((q - p) // 8)]
    return idx, subs


def fiche_arcade(e):
    dx, dy, fl, pose = e
    return dx, dy, (0x80 if fl < 0 else 0) << 8 | (fl & 0xFF), 20 * pose


def controle():
    rom = open(ROM, "rb").read()
    for pl, cid in (("pl00", 0), ("pl01", 1), ("pl04", 4), ("pl0b", 0x0B)):
        idx, subs = section_victimes(pl); t = struct.unpack_from(">I", rom, 0xDD212 + 4 * cid)[0]; ok = tot = 0
        for v in range(0x20):                # la ligne arcade n'a que 32 victimes
            off = struct.unpack_from(">h", rom, t + 2 * v)[0]
            for j, e in enumerate(subs[idx[v]]):
                a = struct.unpack_from(">hhHh", rom, t + off + 8 * j); tot += 1; ok += a == fiche_arcade(e)
        print("%s : %d / %d fiches identiques à l'arcade ($DD212[$%02X])" % (pl, ok, tot, cid))


def main():
    L = ["; Positions de l'adversaire pendant les projections / saisies des persos MAX (format arcade $DD212, Upper 7495b8)",
         "; généré par convert/projections_max.py depuis la section des victimes (entrée 0x11) des pac PSP — ne pas éditer", ""]
    for uid, pl, nom in PERSOS:
        idx, subs = section_victimes(pl)
        col = [idx[v] if v < 0x28 else None for v in range(0x30)]
        col[0x2D] = idx[0x28]; col[0x2E] = idx[0x29]
        for u, p in PSEUDO.items(): col[u] = idx[p]
        lab = "PROJ_POS_%s" % uid
        L += ["        even", "%s:                ; %s (%s) : %d victimes PSP, %d sous-tables" % (lab, nom, pl, len(idx), len(subs))]
        for v in range(0, 0x30, 8):
            L.append("        dc.w    " + ", ".join("%s_S%d-%s" % (lab, col[w], lab) for w in range(v, v + 8)) + "   ; victimes $%02X-$%02X" % (v, v + 7))
        for k, F in sorted(subs.items()):
            L.append("%s_S%d:" % (lab, k))
            for j, e in enumerate(F):
                L.append("        dc.w    %d, %d, $%04x, %d   ; fiche %d (PSP %s)" % (fiche_arcade(e) + (j, e)))
        L.append("")
    open(SORTIE, "w").write("\n".join(L) + "\n")
    print("écrit", os.path.normpath(SORTIE))
    for uid, pl, nom in PERSOS:
        idx, subs = section_victimes(pl)
        print("%s : victime Ryu -> sous-table %d (%d fiches) ; sous-tables %d" % (nom, idx[0], len(subs[idx[0]]), len(subs)))


UPPER = __import__("os").path.join(__import__("os").environ.get("ANTHOLOGY_DIR", "anthology_extract"), "decompressed", "ro5_usa_prog68k.bin")
RB, T_UPPER = 0x1F0000, 0x7495B8
SORTIE_NAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rosette_code", "projections_natifs_max.s")


def natifs():
    """lignes NATIVES d'Upper (attaquants $00-$25, 40 colonnes) étendues à 48 : par ligne d'Upper distincte, une copie
    du bloc d'origine (en-tête de 40 mots + sous-tables, données d'Upper inchangées) précédée d'un en-tête de 48 mots par
    attaquant qui la partage ; colonnes 0-$25 = celles d'Upper ; $26 / $27 (Eagle / Maki) et $2D / $2E (Yun / Ingrid) =
    sous-tables PSP de l'attaquant (victimes PSP $26-$29, ajoutées après le bloc) ; pseudo-ID = colonne 0."""
    u = open(UPPER, "rb").read(); w = lambda a: struct.unpack_from("<h", u, a - RB)[0]
    ptr = [struct.unpack_from("<I", u, T_UPPER - RB + 4 * a)[0] for a in range(0x30)]
    tous = sorted(set(ptr[:0x26]))
    L = ["; Lignes NATIVES de la table des positions de projection d'Upper (7495b8, attaquants $00-$25) étendues à 48 colonnes",
         "; (victimes MAX $26 / $27 / $2D / $2E = données PSP de l'attaquant). Généré par convert/projections_max.py natifs.",
         "; Mettre PROJ_NAT_xx dans 7495b8[$xx] (xx = $00-$25). Copie du bloc d'origine : décalages relatifs gardés (< 32 Ko).", ""]
    groupes = {}
    for a in range(0x26): groupes.setdefault(ptr[a], []).append(a)
    total = 0
    for t, ats in sorted(groupes.items()):
        offs = [w(t + 2 * v) for v in range(40)]
        psp = {a: section_victimes("pl%02x" % a) for a in ats}
        lmax = max(len(f) for i, s in psp.values() for f in s.values())
        nxt = [x for x in tous if x > t]
        fin = min(nxt[0] - t if nxt else 1 << 30, max(offs) + 8 * lmax)
        B = "PROJ_BLOC_%06X" % t
        L.append("        even")
        for a in ats:
            idx, subs = psp[a]; lab = "PROJ_NAT_%02X" % a
            col = ["%s+%d-%s" % (B, offs[v], lab) for v in range(0x26)] + [None] * 10
            for v, p in ((0x26, 0x26), (0x27, 0x27), (0x2D, 0x28), (0x2E, 0x29)): col[v] = "%s_V%02X-%s" % (lab, p, lab)
            for v in (0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2F): col[v] = col[0]
            L.append("%s:                ; attaquant $%02X (pl%02x), ligne Upper $%06X" % (lab, a, a, t))
            for v in range(0, 0x30, 4): L.append("        dc.w    " + ", ".join(col[v:v + 4]) + "   ; victimes $%02X-$%02X" % (v, v + 3))
        L.append("%s:                ; copie de la ligne Upper $%06X (%d o)" % (B, t, fin))
        for o in range(0, fin, 16):
            ws = struct.unpack_from("<%dH" % (min(16, fin - o) // 2), u, t - RB + o)
            L.append("        dc.w    " + ", ".join("$%04x" % x for x in ws))
        total += fin
        for a in ats:
            idx, subs = psp[a]; lab = "PROJ_NAT_%02X" % a
            for p in (0x26, 0x27, 0x28, 0x29):
                L.append("%s_V%02X:                ; victime PSP $%02X : sous-table %d (%d fiches)" % (lab, p, p, idx[p], len(subs[idx[p]])))
                for e in subs[idx[p]]: L.append("        dc.w    %d, %d, $%04x, %d" % fiche_arcade(e)); total += 8
            total += 96
        L.append("")
    open(SORTIE_NAT, "w").write("\n".join(L) + "\n")
    print("écrit %s : %d groupes, ~%d o" % (os.path.normpath(SORTIE_NAT), len(groupes), total))


if __name__ == "__main__":
    {"controle": controle, "natifs": natifs}.get(sys.argv[1] if sys.argv[1:] else "", main)()
