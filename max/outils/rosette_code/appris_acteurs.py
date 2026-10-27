"""Apprentissage des fonctions du moteur d'ACTEURS DE FIN (PSP -> arcade), 2026-10-10.
Paires de gestionnaires homologues : sous-types 0-$4D de la classe $4B (arcade table $A75D4, PSP table 0x2B2358).
Chaque gestionnaire PSP est traduit (contexte acteur) puis aligné (LCS) sur la routine arcade ; une ligne « bsr/jsr
psp_X » alignée sur « bsr/jsr $Y » vote pour X -> Y. Résultat fusionné dans api_acteurs.json (lu par traduire.API)."""
import os, re, json, struct, collections
import traduire as T
from evaluer import norm68, explore
APPEL_ARC = re.compile(r"^(bsr|jsr|jmp)(?:\.[bwl])?\s+\$([0-9a-f]+)(?:\.l)?$")
APPEL_TR = re.compile(r"^(bsr|jsr|jmp|bra)\s+(psp_[0-9a-f]+)$")


def norm_arc(a):
    seen, _, _ = explore([a], a, a + 0x300); out = []
    for k in sorted(seen):
        i = seen[k]; brut = "%s %s" % (i.mnemonic, i.op_str); m = APPEL_ARC.match(brut.strip())
        if m: out.append("%s $%s" % ("bsr" if m.group(1) != "jmp" else "jmp", m.group(2))); continue
        x = norm68(brut)
        if x: out.append(x)
    return out


def norm_tr(lines):
    out = []
    for l in lines:
        x = l.strip(); m = APPEL_TR.match(x)
        if m: out.append("%s %s" % ("bsr" if m.group(1) in ("bsr", "jsr") else "jmp", m.group(2))); continue
        m = APPEL_ARC.match(x)
        if m: out.append("%s $%s" % ("bsr" if m.group(1) != "jmp" else "jmp", m.group(2))); continue
        y = norm68(x)
        if y: out.append(y)
    return out
ROMD = os.path.expanduser("~/.cache/sfa3max/sfa3ud_donnees.bin")
APPEL = re.compile(r"^(?:bsr|jmp)\s+(psp_[0-9a-f]+|\$[0-9a-f]+)$")


def cible(l):
    m = APPEL.match(l.strip())
    return m.group(1) if m else None


def egal(t, a):
    ct, ca = cible(t), cible(a)
    if ct and ca and t.split()[0] != a.split()[0]: return False, None     # bsr <-> bsr, jmp <-> jmp seulement
    if ct and ca:
        if ct.startswith("psp_") and ca.startswith("$"): return True, (int(ct[4:], 16), int(ca[1:].replace(".l", ""), 16))
        return ct == ca, None
    return re.sub(r"\bd\d\b", "dX", t) == re.sub(r"\bd\d\b", "dX", a), None


def aligner(A, P):
    n, m = len(A), len(P); D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            D[i + 1][j + 1] = D[i][j] + 1 if egal(P[j], A[i])[0] else max(D[i][j + 1], D[i + 1][j])
    out, i, j = [], n, m
    while i and j:
        ok, b = egal(P[j - 1], A[i - 1])
        if ok and D[i][j] == D[i - 1][j - 1] + 1:
            if b: out.append(b)
            i -= 1; j -= 1
        elif D[i - 1][j] >= D[i][j - 1]: i -= 1
        else: j -= 1
    return out


def table_psp(lignes):
    """entrées de la 1re table de sauts J_xxx de la traduction"""
    out, dedans = [], False
    for l in lignes:
        x = l.strip()
        if re.match(r"^J_[0-9a-f]+:$", x): dedans = True; continue
        if dedans:
            m = re.match(r"dc\.l\s+psp_([0-9a-f]+)", x)
            if m: out.append(int(m.group(1), 16))
            else: break
    return out


def table_arc(a, ao, n):
    """1re table de sauts relative au PC d'une routine arcade (move.w T(pc,d0.w),d1 ; jsr/jmp T(pc,d1.w))"""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000); md.skipdata = True
    b = open(ROMD, "rb").read()
    for i in md.disasm(ao[a:a + 0x200], a):
        m = re.match(r"\$([0-9a-f]+)\(pc, d0\.w\), d1", i.op_str)
        if i.mnemonic.startswith("move.w") and m:
            t = int(m.group(1), 16)
            return [t + struct.unpack_from(">h", b, t + 2 * k)[0] for k in range(n)]
        if i.mnemonic == "rts": break
    return []


if __name__ == "__main__":
    b = open(ROMD, "rb").read(); img = T.img
    A = [0xA75D4 + struct.unpack_from(">H", b, 0xA75D4 + 2 * k)[0] for k in range(78)]
    P = [struct.unpack_from("<I", img, 0x2B2358 + 4 * k)[0] for k in range(78)]
    T.MODE_MAX = True; T.CTX["acteur"] = True
    votes = collections.defaultdict(collections.Counter)
    ao = open(__import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "sfa3_prog.bin"), "rb").read()
    file, vus = list(zip(A, P)), set()
    while file:
        a, p = file.pop()
        if (a, p) in vus: continue
        vus.add((a, p))
        try: brut = T.traduire(p); tr = norm_tr(brut); ar = norm_arc(a)
        except Exception as e: continue
        for x, y in aligner(ar, tr): votes[x][y] += 1
        tp = table_psp(brut)
        if tp:
            ta = table_arc(a, ao, len(tp))
            if len(ta) == len(tp): file += list(zip(ta, tp))
    print(len(vus), "paires de routines comparées")
    res = {}
    for x, v in sorted(votes.items()):
        (y, n), tot = v.most_common(1)[0], sum(v.values())
        ok = n >= 2 and n / tot >= 0.6
        print("PSP %#x -> arcade $%X  %d/%d%s" % (x, y, n, tot, "" if ok else "  (rejeté)"))
        if ok: res["%#x" % x] = "$%X" % y
    json.dump(res, open("api_acteurs.json", "w"), indent=1)
