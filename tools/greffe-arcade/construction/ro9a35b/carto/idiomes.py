#!/usr/bin/env python3
"""RECENSEMENT DES IDIOMES problematiques sur ro3 (HANDOFF §65-§103), compte sur ro3 / ro5 / ro9.
Deux sources independantes :
 A. motifs MIPS bruts (sans le traducteur) : acces octet a +1/+2/+3 d'une case registre, demi-registres hauts
    (lh/sh a +2), aiguillages par table (sll 1 / sll 2 sur l'index avant lecture d'une table de constantes),
    increments d'octet sur une case An (flux d'octets), constantes 32 bits IMPAIRES dans la plage des donnees,
    appels natifs (moteur PS2 / natives du module / setjmp-longjmp / jalr non constants).
 B. annotations du traducteur existant en mode cps2 (translate.py importe, rien n'est modifie), par routine."""
import os, sys, re, collections, json, pickle, struct
os.environ["MEMMODE"] = "cps2"
os.environ.setdefault("GRAIN", "routine")
import commun as C
import translate as T

SLOTS_D = {0x1124 + 4*n: 'D%d' % n for n in range(8)}; SLOTS_D[0x1144] = 'D8'
SLOTS_A = {0x1100 + 4*n: 'A%d' % n for n in range(8)}; SLOTS_A[0x1120] = 'A8'
SETJMP, LONGJMP = 0x119f48, 0x119fa0

def mips_patterns(mod):
    s0 = C.start68k(mod); hd = C.header(mod); e = hd['code_end']
    L = [x for x in C.instrs(mod) if x.va >= s0]
    natives = set()
    for a, b in C.funcs(mod):
        sg = C.seg(mod, a, b); n = C.is_native(sg)
        if n[0] and n[2] > 8: natives.add(a)
    R = collections.Counter(); ex = collections.defaultdict(list)
    lui = {}; slotval = {}
    lo_d, hi_d = C.BASE + e, hd['fin_exec']
    for i, x in enumerate(L):
        if x.m == 'lui': lui[x.rt] = x.imm
        # cases registre : base = lui 0x7000
        if x.m in ('lb', 'lbu', 'sb', 'lh', 'lhu', 'sh') and lui.get(x.rs) == 0x7000:
            off = x.imm
            for base, nm in list(SLOTS_D.items()) + list(SLOTS_A.items()):
                if base < off < base + 4:
                    k = off - base
                    if x.m in ('lb', 'lbu', 'sb'):
                        key = 'octet +%d d\'une case %s' % (k, 'D' if nm[0] == 'D' else 'A')
                    else:
                        key = 'demi-registre haut (%s +2) %s' % ('lh/lhu' if x.m != 'sh' else 'sh', 'D' if nm[0] == 'D' else 'A')
                    R[key] += 1; ex[key].append(x.va)
        # aiguillage : sll k sur un index puis addu avec une constante lui/addiu puis lw/lh puis jr/jalr
        if x.m == 'sll' and x.sa in (1, 2) and x.rd != 0:
            for j in range(i+1, min(i+8, len(L))):
                y = L[j]
                if y.m in ('jr', 'jalr') and y.rs != 31:
                    # la valeur sautee doit venir d'un lw dans l'intervalle
                    if any(z.m == 'lw' for z in L[i+1:j]):
                        key = 'aiguillage par table, index sll %d' % x.sa; R[key] += 1; ex[key].append(x.va)
                    break
        # constante 32 bits impaire dans la plage des donnees (lui + addiu/ori)
        if x.m in ('addiu', 'ori') and x.rs in lui and x.rs == x.rt:
            v = ((lui[x.rs] << 16) + (x.simm if x.m == 'addiu' else x.imm)) & 0xffffffff
            if lo_d <= v < hi_d and v & 1:
                R['constante impaire dans la plage des donnees'] += 1; ex['constante impaire dans la plage des donnees'].append(x.va)
        # appels
        if x.m == 'jal':
            t = x.tgt
            if t in (SETJMP, LONGJMP): R['setjmp/longjmp (branchement entre fonctions)'] += 1
            elif not (C.BASE + s0 <= t < C.BASE + e): R['appel moteur PS2 (jal hors module)'] += 1; ex['moteur'].append(x.va)
            elif (t - C.BASE) in natives: R['appel natif du module (jal)'] += 1
        if x.m == 'jalr':
            R['jalr (tous)'] += 1
        if x.m not in ('lui',) and x.op != 0 and x.m not in ('sb','sh','sw','sd','beq','bne','j','jal'):
            if x.rt in lui and x.m != 'addiu' and x.m != 'ori': lui.pop(x.rt, None)
    # flux d'octets : 'lw An ; addiu +1 ; sw An' (post-increment octet d'un registre d'adresse)
    for i in range(len(L) - 3):
        a_, b_, c_ = L[i], L[i+1], L[i+2]
        if a_.m == 'lw' and a_.imm in SLOTS_A and b_.m == 'addiu' and b_.simm in (1, -1) and b_.rs == a_.rt:
            for y in L[i+2:i+6]:
                if y.m == 'sw' and y.imm == a_.imm:
                    R['flux d\'octets (An +-1)'] += 1; ex['flux'].append(a_.va); break
    R['fonctions natives du module (>8 instr.)'] = len(natives)
    return R, ex

ANNOT = [("index brut double", "aiguillage index brut (echelle 4, §102)"),
         ("flux d'octets", "flux d'octets (A)+ adresse exacte (§65)"),
         ("octet indexe", "octet indexe d8(An,Xn) (§66)"),
         ("octet via A apres ADDA", "octet via An apres ADDA (§97)"),
         ("mot a octets inverses", "mot a octets inverses bswap16 (§92/§100)"),
         ("octets inverses par moitie", "long rangé octet par octet bswap32 (§90)"),
         ("moitie haute du registre", "moitie haute d'un registre"),
         ("octet bas d'un lh", "octet bas d'un lh"),
         ("aide du recompilateur", "appel d'une aide du recompilateur (§83)"),
         ("prete", "registre A8/D8 prete (§54)"),
         ("pile privee 0x114C", "pile privee 0x114C (§72)"),
         ("drapeaux rendus a l'appelant", "drapeaux rendus a l'appelant (§66/§87/§93)"),
         ("hors carte", "cible/adresse HORS CARTE"),
         ("ZONE NON CONVERTIE", "adresse PS2 non convertie"),
         ("registre CPS-A", "registre CPS-A elargi par le portage"),
         ("realignement du portage", "realignement du portage"),
         ("long echange", "operation sur long echange (recette cps2)"),
         ("pointeur de code", "pointeur de code (converti a l'usage, §76)"),
         ("resultat natif du portage suppose nul", "resultat natif suppose nul"),
         ("DBRA du recompilateur", "DBRA du recompilateur (§74)"),
         ("appel terminal vers un RTS partage", "appel terminal vers RTS partage (§47)")]

def annotations(mod):
    buf = C.load(mod); cnt = collections.Counter(); err = 0; n_out = 0
    T.DATA_BASE = 0x200000
    for a, b in C.funcs(mod):
        try:
            out, _ = T.translate(buf, a, b)
        except Exception as e:
            err += 1; continue
        for va, mn, ws in out:
            n_out += 1
            for k, lab in ANNOT:
                if k in mn: cnt[lab] += 1
    return cnt, err, n_out

if __name__ == "__main__":
    res = {}
    for mod in ('ro3', 'ro5', 'ro9'):
        R, ex = mips_patterns(mod)
        A, err, n = annotations(mod)
        res[mod] = dict(mips=R, annotations=A, erreurs=err, instr68k=n,
                        exemples={k: ['%x' % v for v in vs[:12]] for k, vs in ex.items()})
        print("== %s : %d instructions 68K emises, %d routines en exception" % (mod, n, err), flush=True)
    keys = sorted(set().union(*(res[m]['mips'] for m in res)))
    print("\nA. motifs MIPS bruts            ro3     ro5     ro9")
    for k in keys: print("   %-52s %6d  %6d  %6d" % (k, res['ro3']['mips'][k], res['ro5']['mips'][k], res['ro9']['mips'][k]))
    keys = [lab for _, lab in ANNOT]
    print("\nB. annotations du traducteur (mode cps2)")
    for k in keys: print("   %-52s %6d  %6d  %6d" % (k, res['ro3']['annotations'][k], res['ro5']['annotations'][k], res['ro9']['annotations'][k]))
    json.dump(res, open(os.path.join(C.OUT, "idiomes.json"), "w"), indent=1)
    for m in ('ro9',):
        for k, v in res[m]['exemples'].items(): print("   ex. %s %s : %s" % (m, k, ' '.join(v[:8])))
