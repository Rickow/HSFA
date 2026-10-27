#!/usr/bin/env python3
"""Registres SUPPLEMENTAIRES du recompilateur (A8 = case 0x1120, D8 = 0x1144 ; HANDOFF §53) :
pour chaque fonction qui les utilise, un registre 68K du meme type LIBRE dans la fonction ET dans
toutes les fonctions qu'elle appelle (fermeture du graphe d'appels directs ; un appel indirect
= inconnu, donc prudence). Rend {debut_fonction: {0x1120: ('A',k), 0x1144: ('D',k)}}."""
import sys, os, struct, bisect, collections
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from mips import decode
EXTRA = {0x1120: 'A', 0x1144: 'D'}
A8_HOME_PLAN = os.environ.get("A8_HOME", "87e0") != "none"   # (HANDOFF §80) A8 a un domicile memoire
MERGE_IFELSE = os.environ.get("MERGE_IFELSE", "1") != "0"   # (HANDOFF §114)
MERGED = [0]
BACK_AFTER = os.environ.get("BACK_AFTER", "1") != "0"   # (agent_ro9) retour de boucle sur la restauration
BACK_AFTER_N = [0]
EARLY_CLOSE = set()          # (case, debut) des zones refermees juste apres leur derniere instruction
# (HANDOFF §126) portee du retour de boucle place APRES le dernier acces (0x40 jusque-la) : la boucle des decors de
# SURVIVAL (Upper mips 0x2505EC-0x2506C4 : 'D8 = (A8)+ ; si T[D8] = 0 : (A2)+ = (A3)+') depasse 0x40 -> zones de A8 et
# D8 refusees, lectures perdues. Les refus (appel, registre occupe, entree/sortie laterale) restent verifies ensuite.
PARTIAL_LIVE = os.environ.get("PARTIAL_LIVE", "0") != "0"   # (HANDOFF §126) essai : moins de zones, D8 a deja son domicile
LATERAL_OK = os.environ.get("LATERAL", "1") != "0"   # (HANDOFF §130)
D8_EARLY = os.environ.get("D8_EARLY", "1") != "0"   # (HANDOFF §132)
LATERAL = {}; LATERAL_N = [0]   # (case, debut de zone) -> va MIPS des branchements de sortie laterale
DBG_PLAN = tuple(int(x, 16) for x in os.environ["DBG_PLAN"].split("-")) if os.environ.get("DBG_PLAN") else None
LOOP_EXT = int(os.environ.get("LOOP_EXT", "0x100"), 16)
POOL = {'A': [4, 3, 2, 1, 0, 6], 'D': [7, 6, 5, 4, 3, 2, 1, 0]}     # A5 (globales) jamais preté

def analyse(buf, runtime_base=0x1f0000):
    end = struct.unpack_from('<I', buf, 12)[0]
    c0 = 0x22de0 if end == 0x3bf140 else 0x22b00
    L = list(decode(buf, c0, end))
    starts = sorted({x.tgt - runtime_base for x in L if x.m == 'jal'} | {c0})
    starts = [s for s in starts if c0 <= s < end]
    fof = lambda va: starts[bisect.bisect_right(starts, va) - 1]
    used = collections.defaultdict(set); calls = collections.defaultdict(set); indirect = set(); l7 = set()
    for x in L:
        if x.m == 'lui': (l7.add if x.imm == 0x7000 else l7.discard)(x.rt); continue
        if x.m in ('lw', 'lh', 'lb', 'lbu', 'lhu', 'sw', 'sh', 'sb') and x.rs in l7 and 0x1100 <= x.imm < 0x1150:
            used[fof(x.va)].add(x.imm)
        if x.m == 'jal':
            t = x.tgt - runtime_base
            if c0 <= t < end: calls[fof(x.va)].add(t)
        if x.m == 'jalr': indirect.add(fof(x.va))
    # fermeture iterative (graphe avec cycles)
    clo = {f: set(used[f]) for f in starts}
    changed = True
    while changed:
        changed = False
        for f in starts:
            for c in calls[f]:
                if not clo[c] <= clo[f]: clo[f] |= clo[c]; changed = True
    alloc = {}; stats = collections.Counter()
    for f in starts:
        u = used[f]
        if not any(s in u for s in EXTRA): continue
        m = {}
        for s, kind in EXTRA.items():
            if s not in u: continue
            base = 0x1100 if kind == 'A' else 0x1124
            taken = {r for r in POOL[kind] if base + 4*r in clo[f]} | {k for _, k in m.values() if _ == kind}
            free = [r for r in POOL[kind] if r not in taken]
            if free and f not in indirect: m[s] = (kind, free[0]); stats[(kind, 'sur')] += 1
            elif free: m[s] = (kind, free[0]); stats[(kind, 'appel indirect : a verifier')] += 1
            else: stats[(kind, 'aucun registre libre')] += 1
        if m: alloc[f] = m
    return alloc, stats

if __name__ == "__main__":
    mod = os.environ.get("MODULE", "ro3")
    buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, 'rb').read()
    alloc, stats = analyse(buf)
    print(mod, dict(stats))

BR = ('beq', 'bne', 'bgez', 'bltz', 'blez', 'bgtz', 'beql', 'bnel')
def plan(buf, runtime_base=0x1f0000):
    """Plan de traduction SUR de A8/D8 : pour chaque (fonction, case), une zone [debut, fin] (va MIPS)
    - sans appel (jal/jalr) a l'interieur ;
    - a entree et sortie uniques : aucun branchement de l'exterieur vers l'interieur (sauf son debut),
      aucun de l'interieur vers l'exterieur (sauf juste apres sa fin) ;
    - registre 68K du meme type NON utilise dans toute la fonction (A5 jamais) ;
    traduite par MOVE.L Rk,-(SP) avant / MOVE.L (SP)+,Rk apres. Rend (plan, refus)."""
    end = struct.unpack_from('<I', buf, 12)[0]
    c0 = 0x22de0 if end == 0x3bf140 else 0x22b00
    L = [x for x in decode(buf, c0, end) if not (x.m == 'sll' and x.w == 0)]
    vas = [x.va for x in L]
    starts = sorted({x.tgt - runtime_base for x in L if x.m == 'jal'} | {c0})
    starts = [s for s in starts if c0 <= s < end]
    fof = lambda va: starts[bisect.bisect_right(starts, va) - 1]
    used = collections.defaultdict(set); acc = collections.defaultdict(list); usedva = collections.defaultdict(list)
    calls = collections.defaultdict(list); brs = collections.defaultdict(list); l7 = set()
    for x in L:
        f = fof(x.va)
        if x.m == 'lui': (l7.add if x.imm == 0x7000 else l7.discard)(x.rt); continue
        if x.m in ('lw', 'lh', 'lb', 'lbu', 'lhu', 'sw', 'sh', 'sb') and x.rs in l7 and 0x1100 <= x.imm < 0x1150:
            used[f].add(x.imm); usedva[f].append((x.va, x.imm))
            if x.imm in EXTRA: acc[(f, x.imm)].append(x.va)
        if x.m in ('jal', 'jalr'): calls[f].append(x.va)
        if x.m in BR and not (x.rs == 0 and x.rt == 0 and x.m == 'beq' and False):
            brs[f].append((x.va, x.va + 4 + x.simm * 4))
    # decoupage en DUREES DE VIE : une ecriture qui ne derive pas d'une lecture recente de la meme
    # case (ex. le decrement d'un compteur de boucle en derive) ouvre une nouvelle duree de vie
    pos = {va: i for i, va in enumerate(vas)}
    ranges = []
    for (f, s), v in acc.items():
        v = sorted(v); cur = [v[0]]
        for va in v[1:]:
            x = L[pos[va]]
            fresh = False
            # (HANDOFF §126) une ecriture PARTIELLE (sb/sh) garde le reste de la case : jamais une nouvelle duree de vie
            # (Upper mips 0x2505E8 'D8 = 0' puis 0x250610 'D8.b = (A8)+' : l'effacement etait perdu)
            if x.m == 'sw' or (x.m in ('sh', 'sb') and not PARTIAL_LIVE):
                win = L[max(0, pos[va] - 8):pos[va]]
                fresh = not any(y.m in ('lw', 'lh', 'lb', 'lbu', 'lhu') and y.imm == s for y in win)
            if fresh: ranges.append((f, s, cur)); cur = [va]
            else: cur.append(va)
        ranges.append((f, s, cur))
    # (HANDOFF §114) « si / sinon » sur la case : 'A8 = T1 ; si c : A8 = T2 ; lire A8'. Le branchement qui saute
    # la 2e ecriture atterrit DANS la 2e duree de vie (entree laterale -> zone refusee, lectures perdues : objet
    # d'Upper mips 0x1CB854 / 0x1CB898). On fusionne les deux durees de vie quand un branchement parti de
    # [debut de la 1re, debut de la 2e[ vise ]debut de la 2e, fin de la 2e].
    if MERGE_IFELSE:
        merged = []
        for f, s, v in ranges:
            if merged and merged[-1][0] == f and merged[-1][1] == s:
                pv = merged[-1][2]
                if any(min(pv) <= b_ < min(v) and min(v) < t_ <= max(v) for b_, t_ in brs[f]) \
                   and not any(min(pv) < c < min(v) for c in calls[f]):
                    merged[-1] = (f, s, sorted(pv + v)); MERGED[0] += 1; continue
            merged.append((f, s, v))
        ranges = merged
    if A8_HOME_PLAN:
        # (HANDOFF §80) A8 a un DOMICILE memoire (copie exacte de la case 0x1120 du portage) : une duree de vie
        # qui traverse un appel est decoupee en zones de part et d'autre de chaque appel (l'appele lit/ecrit
        # le domicile comme le portage lit/ecrit la case). Ex. creation des objets de l'ecran VS (mips 0x1FA230)
        split = []
        for f, s, v in ranges:
            if s != 0x1120: split.append((f, s, v)); continue
            cs = sorted(calls[f]); cur = [v[0]]
            for va in v[1:]:
                if any(cur[-1] < c < va for c in cs): split.append((f, s, cur)); cur = [va]
                else: cur.append(va)
            split.append((f, s, cur))
        ranges = split
    out = collections.defaultdict(list); refus = collections.Counter()
    for f, s, v in ranges:
        kind = EXTRA[s]; lo, hi = min(v), max(v)
        # EXTENSION de la zone : retour de boucle place apres le dernier acces (le test porte sur la
        # valeur decrementee gardee dans un registre MIPS) ; sortie vers l'avant toute proche
        for _ in range(8):
            grow = False
            for b_, t_ in brs[f]:
                if b_ > hi and lo < t_ <= hi and b_ - hi <= LOOP_EXT: hi = b_; grow = True
                if lo <= b_ <= hi and t_ > hi and t_ - hi <= 0x40: hi = t_ - 4; grow = True
                # (HANDOFF §80) boucle dont la tete precede le premier acces (test en tete, retour place
                # apres le dernier acces) : copie « TST.W (A8) ; BMI fin ; MOVE.W (A8)+,(A0)+ ; BRA »
                if A8_HOME_PLAN and s == 0x1120 and b_ >= lo and t_ < lo and lo - t_ <= 0x40 and b_ - hi <= 0x40:
                    lo = t_; hi = max(hi, b_); grow = True
            if not grow: break
        # (HANDOFF §66) la valeur LUE dans la case vit encore dans des registres MIPS derives (extension de
        # signe, adresse de table...) : la zone doit couvrir leur derniere utilisation, sinon le registre
        # 68K prete est deja restaure quand l'instruction traduite s'en sert comme index.
        for va in v:
            k0 = pos[va]; x0 = L[k0]
            if x0.m not in ('lw', 'lh', 'lb', 'lbu', 'lhu'): continue
            live = {x0.rt}
            for y in L[k0+1:k0+24]:
                if y.m in BR:                       # (HANDOFF §73) le branchement LIT la valeur derivee (DBRA
                    if live & ({y.rs, y.rt} - {0}): hi = max(hi, y.va)   #  sur D8) : il fait partie de la zone
                    break
                if y.m in ('jal', 'jalr', 'jr'): break
                reads = {y.rs, y.rt} if y.m not in ('lui',) else set()
                if y.m in ('sw', 'sh', 'sb'): reads = {y.rs, y.rt}
                RT = ('addu','subu','and','or','xor','nor','slt','sltu','daddu','dsubu','sll','srl','sra','sllv',
                      'srlv','srav','dsll','dsrl','dsra','dsll32','dsrl32','dsra32')
                dest = None if y.m in ('sw', 'sh', 'sb') else (y.rd if y.m in RT else y.rt)
                if y.m in ('sll','srl','sra','dsll','dsrl','dsra','dsll32','dsrl32','dsra32'): reads = {y.rt}
                if live & (reads - {0}):
                    hi = max(hi, y.va)
                    if dest: live.add(dest)
                elif dest in live: live.discard(dest)
                if not live: break
        _dbg = DBG_PLAN and DBG_PLAN[0] <= lo <= DBG_PLAN[1]
        if any(lo < c < hi for c in calls[f]):
            if _dbg: print("PLAN refus appel", hex(f), hex(s), hex(lo), hex(hi))
            refus['appel pendant la duree de vie'] += 1; continue
        if hi not in pos: hi = vas[bisect.bisect_right(vas, hi) - 1]
        k = bisect.bisect_right(vas, hi)
        after = vas[k] if k < len(vas) else hi + 4
        bad = False; resto = False; back = False; lat = []
        for b, t in brs[f]:
            inside_b = lo <= b <= hi; inside_t = lo <= t <= hi
            if not inside_b and inside_t and t != lo: bad = True; break      # entree laterale
            if inside_b and not inside_t and t != after:                     # sortie laterale
                # (HANDOFF §130) acceptee : translate restaure le registre prete sur le chemin pris (test inverse,
                # restauration, BRA) ; avant, la zone etait refusee et les lectures de A8/D8 perdues (combat miroir)
                if LATERAL_OK: lat.append(b); continue
                bad = True; break
            if not inside_b and t == after and not (b > hi): resto = True     # saut exterieur sur la restauration
            # (agent_ro9) retour de boucle venu d'APRES la zone et visant 'after' : la restauration emise sur 'after'
            # serait rejouee a chaque tour (pile desequilibree, domicile de A8 ecrase par le registre restaure).
            # Hyper mips 0x33C408-0x33C46C (A8 = table 0x5C6960 + 4*perso, boucle 0x33C470 <- 0x33C5A4).
            if BACK_AFTER and not inside_b and t == after and b > hi: resto = True; back = True; BACK_AFTER_N[0] += 1
        if resto and not bad:
            # (HANDOFF §80) restauration emise JUSTE APRES la derniere instruction de la zone (et non sur la
            # cible 'after', atteinte de l'exterieur) : possible si aucun branchement interne ne sort vers 'after'
            # (agent_ro9) D8 aussi quand c'est un retour de boucle : sa restauration (domicile D8, sauvegarde fixe) ne
            # touche pas la pile ; la refuser renvoyait la zone au repli memoire, qui perdait 'LSL.W #2' et l'ADDA (0x33C42C)
            _int = [b for b, t in brs[f] if lo <= b <= hi and t == after]
            # (HANDOFF §132) D8 aussi : sa sauvegarde est FIXE (domicile + $87F8), pas sur la pile -> fermeture anticipee
            # sure (SFA3 mips 0x1F3118 : 'D8 = D0 ; LSL #2 ; OR.L T(D8),D2' refusee -> LSL et OR perdus)
            _ok8 = s == 0x1120 or back or (s == 0x1144 and D8_EARLY)
            if A8_HOME_PLAN and _ok8 and not _int:
                EARLY_CLOSE.add((s, lo))
            elif A8_HOME_PLAN and _ok8 and LATERAL_OK:
                # (HANDOFF §130) branchements internes vers 'after' (aussi atteint de l'exterieur) : traites en sorties
                # laterales (restauration sur leur chemin) + fermeture anticipee (Upper mips 0x26D8DC, A8)
                lat.extend(_int); EARLY_CLOSE.add((s, lo))
            else: bad = True
        if not bad and any(x.m == 'jr' for x in L[pos[lo]:pos.get(hi, pos[lo]) + 1]): bad = True
        if bad:
            if _dbg: print("PLAN refus entrees/sorties", hex(f), hex(s), hex(lo), hex(hi), [(hex(b), hex(t)) for b, t in brs[f] if (lo <= b <= hi) != (lo <= t <= hi)][:6])
            refus['zone a plusieurs entrees/sorties'] += 1; continue
        base = 0x1100 if kind == 'A' else 0x1124
        taken = {r for r in POOL[kind] if base + 4*r in used[f]} | {r for (kk, r, ss, a0, a1) in out[f]
                                                                    if kk == kind and not (a1 < lo or a0 > hi)}
        free = [r for r in POOL[kind] if r not in taken]
        if not free:
            # (HANDOFF §65) le registre prete est SAUVE puis RESTAURE autour de la zone : il suffit qu'il
            # ne soit pas utilise DANS la zone (sans appel). Ex. remplissage video $92A000 : D0-D7 servent
            # dans la fonction, mais la boucle interne sur D8 n'en lit aucun.
            zt = {r for r in POOL[kind] if any(lo <= va <= hi and sl == base + 4*r for va, sl in usedva[f])}
            zt |= {r for (kk, r, ss, a0, a1) in out[f] if kk == kind and not (a1 < lo or a0 > hi)}
            free = [r for r in POOL[kind] if r not in zt]
            if free: refus['registre libre dans la zone seulement (sauve/restaure)'] += 1
        if not free:
            if _dbg: print("PLAN refus registre", hex(f), hex(s), hex(lo), hex(hi))
            refus['aucun registre libre dans la fonction'] += 1; continue
        out[f].append((kind, free[0], s, lo, hi))
        if lat: LATERAL[(s, lo)] = sorted(set(lat)); LATERAL_N[0] += len(set(lat))
    return dict(out), refus

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "plan":
    mod = os.environ.get("MODULE", "ro3")
    buf = open("<workspace>/anthology_extract/decompressed/%s_usa_prog68k.bin" % mod, 'rb').read()
    p, r = plan(buf)
    print(mod, "zones traduisibles :", sum(len(v) for v in p.values()), " refus :", dict(r))
