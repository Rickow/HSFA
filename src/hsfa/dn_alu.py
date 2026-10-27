"""(HANDOFF §107) ECRITURES DE REGISTRE D PERDUES : formes MIPS -> 68K non reconnues ailleurs dans translate.py.
Appele en sortie du bloc 'ecriture d'une case Dn' quand rien n'a ete emis. Rend (mots, mnemonique) ou None.
Formes : OP.x T(PC,Dk),Dn (ADD/SUB/AND/OR d'une valeur de table) ; decalages variables (LSL/ASR/LSR Dm,Dn) ;
ADDI #c,Dn (constante lui/ori, ou chaine d'addiu) ; ANDI.L #masque (dsll32/dsrl32) ; ADD.x Dn,Dn ; MULS.W #k,Dn
(x*5 << s, x = Dn.W signe)."""
SZN = {'B': 0, 'W': 1, 'L': 2}
LOADS = ('lw', 'lh', 'lhu', 'lb', 'lbu')
LSZ = {'lw': 'L', 'lh': 'W', 'lhu': 'W', 'lb': 'B', 'lbu': 'B'}

def _prod(L, i, r, lim=10):
    for j in range(i - 1, max(-1, i - lim), -1):
        x = L[j]
        if x.m in ('jal', 'jalr', 'jr', 'beq', 'bne', 'bgez', 'bltz', 'blez', 'bgtz', 'j', 'b'): return None
        d = _dest(x)
        if d == r: return j
    return None

def _dest(x):
    if x.m in ('sw', 'sh', 'sb', 'sd', 'beq', 'bne', 'j', 'jr', 'nop'): return None
    if x.m in ('addu', 'subu', 'and', 'or', 'xor', 'sllv', 'srav', 'srlv', 'sll', 'sra', 'srl', 'dsll32', 'dsra32',
               'dsrl32', 'slt', 'sltu', 'nor', 'daddu'): return x.rd
    return x.rt

def _orig(L, j, keep_masks=True):
    """remonte les extensions de signe (dsll32/dsra32 meme decalage) et les masques andi 0xff/0xffff"""
    while j is not None:
        x = L[j]
        if x.m in ('dsll32', 'dsra32') or (keep_masks and x.m == 'andi' and x.imm in (0xff, 0xffff)):
            j = _prod(L, j, x.rt if x.m != 'andi' else x.rs); continue
        return j
    return None

def _slot_d(L, j):
    """chargement d'une case Dn (base lui 0x7000) -> (n, taille) ou None"""
    if j is None: return None
    x = L[j]
    if x.m not in LOADS or not (0x1124 <= x.imm < 0x1144) or (x.imm - 0x1124) % 4: return None
    b = _prod(L, j, x.rs, 16)
    if b is None or L[b].m != 'lui' or L[b].imm != 0x7000: return None
    return (x.imm - 0x1124) // 4, LSZ[x.m]

def _const(L, j):
    if j is None: return None
    x = L[j]
    if x.m == 'lui': return (x.imm << 16) & 0xffffffff
    if x.m == 'ori':
        b = _prod(L, j, x.rs)
        if x.rs == 0: return x.imm
        if b is not None and L[b].m == 'lui': return ((L[b].imm << 16) | x.imm) & 0xffffffff
    if x.m == 'addiu':
        if x.rs == 0: return x.simm & 0xffffffff
        b = _prod(L, j, x.rs)
        if b is not None and L[b].m == 'lui': return ((L[b].imm << 16) + x.simm) & 0xffffffff
    return None

def _imm(size, v):
    v &= {'B': 0xff, 'W': 0xffff, 'L': 0xffffffff}[size]
    return [v & 0xffff] if size != 'L' else [(v >> 16) & 0xffff, v & 0xffff]

def _ext_kind(L, j):
    """remonte les extensions d'un registre : (indice du chargement, 's' signe 16 bits | 'u' non signe 16 bits | None)"""
    kind = None
    while j is not None:
        x = L[j]
        if x.m in ('dsll32', 'dsra32') and x.sa == 16:
            kind = kind or 's'; j = _prod(L, j, x.rt); continue
        if x.m == 'andi' and x.imm == 0xffff:
            kind = 'u'; j = _prod(L, j, x.rs); continue
        if x.m in ('lh',): return j, kind or 's'
        if x.m in ('lhu',): return j, kind or 'u'
        return j, kind
    return None, None

def _lin(L, j, r, depth):
    """valeur du registre r produit en L[j] (ou avant) = k * x, x = Dn.W etendu : (k, n, 's'|'u') ou None"""
    if depth > 8: return None
    q = j if (j is not None and _dest(L[j]) == r) else _prod(L, j + 1 if j is not None else 0, r)
    if q is None: return None
    x = L[q]
    if x.m == 'sll' and 0 < x.sa < 16:
        a = _lin(L, q - 1, x.rt, depth + 1)
        return (a[0] << x.sa, a[1], a[2]) if a else None
    if x.m in ('addu', 'subu') and x.rs and x.rt:
        a = _lin(L, q - 1, x.rs, depth + 1); b = _lin(L, q - 1, x.rt, depth + 1)
        if a and b and a[1] == b[1] and a[2] == b[2]:
            return (a[0] + b[0] if x.m == 'addu' else a[0] - b[0], a[1], a[2])
        return None
    lj, kind = _ext_kind(L, q)
    s = _slot_d(L, lj)
    if s and kind:
        return (1, s[0], kind)
    return None

def dn_alu(L, i, n, size, tbl_ok):
    x = L[i]
    p = _orig(L, _prod(L, i, x.rt), False)          # la valeur rangee peut passer par une extension de signe
    if p is None: return None
    P = L[p]
    # --- addiu en chaine depuis Dn : ADDI #somme,Dn
    if P.m == 'addiu' and P.rs != 0:
        tot, q = 0, p
        while q is not None and L[q].m == 'addiu' and L[q].rs != 0:
            tot += L[q].simm; q = _prod(L, q, L[q].rs)
        s = _slot_d(L, _orig(L, q, False))
        if s and s[0] == n and tot and q is not None and L[q].m in LOADS:
            sz = size
            return [0x0600 | (SZN[sz] << 6) | n] + _imm(sz, tot), "ADDI.%s #$%x,D%d  [chaine d'addiu]" % (sz, tot & 0xffffffff, n)
        return None
    # --- masque par decalages : dsll32 k ; dsrl32 k -> ANDI.L #(2^(32-k)-1)
    if P.m == 'dsrl32':
        q = _prod(L, p, P.rt)
        if q is not None and L[q].m == 'dsll32' and L[q].sa == P.sa and size == 'L':
            s = _slot_d(L, _prod(L, q, L[q].rt))
            if s and s[0] == n:
                msk = (1 << (32 - P.sa)) - 1
                return [0x0280 | n] + _imm('L', msk), "ANDI.L #$%x,D%d  [dsll32/dsrl32]" % (msk, n)
        return None
    # --- (HANDOFF §137) multiplication par constante decomposee (sll/addu/subu) d'un Dn.W etendu : MULS/MULU.W #k,Dn
    #     (Hyper : x*3<<1 = x6 a 0x11691C, (x<<4-x)<<3 = x120 a 0x2F3CD4, x*3 a 0x1B1B7C...)
    if P.m in ('sll', 'addu', 'subu') and size == 'L':
        lin = _lin(L, p, P.rd if P.m != 'sll' else P.rd, 0)
        if lin and lin[1] == n and lin[0] not in (0, 1) and -32768 <= lin[0] <= 32767 and lin[2] in ('s', 'u'):
            k, _, kind = lin
            if kind == 'u' and k > 0:
                return [0xc0fc | (n << 9), k & 0xffff], "MULU.W #%d,D%d  [multiplication decomposee]" % (k, n)
            if kind == 's':
                return [0xc1fc | (n << 9), k & 0xffff], "MULS.W #%d,D%d  [multiplication decomposee]" % (k, n)
    # --- x*5 << s (x = Dn.W signe) : MULS.W #k,Dn
    if P.m == 'sll' and size == 'L':
        q = _prod(L, p, P.rt)
        if q is not None and L[q].m == 'addu':
            a, b = L[q].rs, L[q].rt
            for r1, r2 in ((a, b), (b, a)):
                t = _prod(L, q, r1)
                if t is not None and L[t].m == 'sll' and L[t].sa == 2 and L[t].rt == r2:
                    s = _slot_d(L, _orig(L, _prod(L, q, r2), False))
                    if s and s[0] == n:
                        k = 5 << P.sa
                        return [0xc1fc | (n << 9), k], "MULS.W #%d,D%d  [x*5<<%d]" % (k, n, P.sa)
        return None
    # --- decalages variables
    if P.m in ('sllv', 'srav', 'srlv'):
        sv = _slot_d(L, _orig(L, _prod(L, p, P.rt)))
        sc = _slot_d(L, _orig(L, _prod(L, p, P.rs)))
        if sv and sc and sv[0] == n and size in ('W', 'L'):
            mreg = sc[0]
            left, typ = (P.m == 'sllv'), (0 if P.m == 'srav' else 1)
            w = 0xe000 | (mreg << 9) | (int(left) << 8) | (SZN[size] << 6) | 0x20 | (typ << 3) | n
            nm_ = {('sllv'): 'LSL', 'srav': 'ASR', 'srlv': 'LSR'}[P.m]
            return [w], "%s.%s D%d,D%d  [decalage variable]" % (nm_, size, mreg, n)
        return None
    if P.m not in ('addu', 'subu', 'and', 'or'): return None
    ops = [(P.rs, P.rt), (P.rt, P.rs)] if P.m != 'subu' else [(P.rs, P.rt)]
    for rd_, ro in ops:
        s = _slot_d(L, _orig(L, _prod(L, p, rd_)))
        if not s or s[0] != n: continue
        jo = _prod(L, p, ro)
        # --- ADD.x Dn,Dn
        so = _slot_d(L, _orig(L, jo))
        if so and so[0] == n and P.m == 'addu':
            return [0xd000 | (n << 9) | (SZN[size] << 6) | n], "ADD.%s D%d,D%d" % (size, n, n)
        # --- constante : ADDI / ANDI / ORI #c,Dn
        c = _const(L, jo)
        if c is not None and P.m in ('addu', 'and', 'or'):
            base, nm_ = {'addu': (0x0600, 'ADDI'), 'and': (0x0200, 'ANDI'), 'or': (0x0000, 'ORI')}[P.m]
            return [base | (SZN[size] << 6) | n] + _imm(size, c), "%s.%s #$%x,D%d  [constante]" % (nm_, size, c, n)
        # --- valeur de table : OP.x T(PC,Dk),Dn
        jl = _orig(L, jo, False)
        if jl is None or L[jl].m not in LOADS or LSZ[L[jl].m] != size: continue
        ja = _prod(L, jl, L[jl].rs); off = L[jl].simm
        while ja is not None and L[ja].m == 'addiu' and L[ja].rs != 0:   # T + index + decalage
            off += L[ja].simm; ja = _prod(L, ja, L[ja].rs)
        if ja is None or L[ja].m != 'addu': continue
        for ri, rt_ in ((L[ja].rs, L[ja].rt), (L[ja].rt, L[ja].rs)):
            tb = _const(L, _prod(L, ja, rt_))
            sk = _slot_d(L, _orig(L, _prod(L, ja, ri)))
            if tb is None or not sk: continue
            k, ksz = sk
            tb = (tb + off) & 0xffffffff
            if not tbl_ok(tb): continue
            base = {'addu': 0xd000, 'subu': 0x9000, 'and': 0xc000, 'or': 0x8000}[P.m]
            nm_ = {'addu': 'ADD', 'subu': 'SUB', 'and': 'AND', 'or': 'OR'}[P.m]
            ext = (k << 12) | (0x800 if ksz == 'L' else 0)
            ws = [base | (n << 9) | (SZN[size] << 6) | 0x3b, ext]
            mn = "%s.%s T_%06x(PC,D%d.%s),D%d  [valeur de table]" % (nm_, size, tb, k, 'L' if ksz == 'L' else 'W', n)
            if size == 'L':
                if P.m not in ('and', 'or'): return None          # long echange : seuls AND/OR commutent avec SWAP
                ws = [0x4840 | n] + ws + [0x4840 | n]; mn = "SWAP D%d ; %s ; SWAP D%d" % (n, mn, n)
            return ws, mn
    return None

def _slot_a(L, j):
    """chargement d'une case An (lw 0x1100+4n, base lui 0x7000) -> n ou None"""
    if j is None: return None
    x = L[j]
    if x.m != 'lw' or not (0x1100 <= x.imm < 0x111c) or (x.imm - 0x1100) % 4: return None
    b = _prod(L, j, x.rs, 16)
    if b is None or L[b].m != 'lui' or L[b].imm != 0x7000: return None
    return (x.imm - 0x1100) // 4

def a_alu(L, i, am, bswap16_of):
    """(HANDOFF §107) ecritures de registre An perdues : SUBA.L Dk,Am ; LEA d16(An),Am + ADDA.W Dk,Am (decalage hors
    d8) ; ADDA.L d'un mot a octets inverses (bswap16 d'un champ, octets 68K d^1 / d) via D0 sauve."""
    x = L[i]
    p = _prod(L, i, x.rt)
    if p is None: return None
    P = L[p]
    if P.m == 'subu':
        a = _slot_a(L, _prod(L, p, P.rs)); s = _slot_d(L, _orig(L, _prod(L, p, P.rt)))
        if a == am and s and s[1] == 'L':
            return [0x91c0 | (am << 9) | s[0]], "SUBA.L D%d,A%d" % (s[0], am)
        return None
    if P.m == 'addiu' and P.rs != 0:                      # An + Dk.W + d16
        q = _prod(L, p, P.rs)
        if q is not None and L[q].m == 'addu':
            for ra, rd_ in ((L[q].rs, L[q].rt), (L[q].rt, L[q].rs)):
                a = _slot_a(L, _prod(L, q, ra)); s = _slot_d(L, _orig(L, _prod(L, q, rd_)))
                if a is not None and s and s[1] in ('W', 'L'):
                    d = P.simm & 0xffff
                    return ([0x41e8 | (am << 9) | a, d, (0xd1c0 if s[1] == 'L' else 0xd0c0) | (am << 9) | s[0]],
                            "LEA $%04x(A%d),A%d ; ADDA.%s D%d,A%d" % (d, a, am, s[1], s[0], am))
        return None
    if P.m == 'addu':
        for ra, rv in ((P.rs, P.rt), (P.rt, P.rs)):
            if _slot_a(L, _prod(L, p, ra)) != am: continue
            jo = _prod(L, p, rv)
            if jo is None or L[jo].m != 'or': continue
            bs = bswap16_of(L, jo)
            if not bs or bs[0] != 'mem': continue
            _, disp, base_slot = bs
            n = base_slot if isinstance(base_slot, int) and 0 <= base_slot < 7 else None   # bswap16_of rend l'indice An
            if n is None: continue
            d = disp & 0xffff
            ws = [0x2f00, 0x7000, 0x1028 | n, (d ^ 1) & 0xffff, 0xe148, 0x1028 | n, d,   # MOVE.L D0,-(SP) ; MOVEQ #0,D0 ;
                  0xd1c0 | (am << 9), 0x4cdf, 0x0001]                                     # MOVE.B d^1 ; LSL.W #8 ; MOVE.B d ;
            return ws, "ADDA.L (mot $%04x(A%d) a octets inverses),A%d  [via D0]" % (d, n, am)   # ADDA.L D0,Am ; MOVEM
    return None

def mem_fix(L, out, inplace_long, abs_addr, addr_to_68k):
    """(HANDOFF §107) ECRITURES MEMOIRE PERDUES (aucune trace dans la sortie) : on insere l'instruction 68K a sa
    place (apres le dernier element de va inferieure). Formes :
      long d(An) += somme d'addiu / &= masque (dsll32/dsrl32) / ^|& constante  -> inplace_long (long echange)
      mot abs &= constante (lh abs ; and ; sh abs)                           -> ANDI.W #c,abs.L
      constante longue a une adresse paire non alignee sur 4 (swr/swl)       -> MOVE.L #c(mots echanges),abs.L"""
    vas = {va for va, mn, ws in out}
    add = []
    for i, x in enumerate(L):
        if x.va in vas or x.m not in ('sw', 'sh', 'swr'): continue
        r = None
        b = _prod(L, i, x.rs, 16)
        if x.m == 'sw' and b is not None and _slot_a(L, b) is not None:
            n = _slot_a(L, b); d = x.simm
            p = _prod(L, i, x.rt)
            if p is not None:
                P = L[p]
                def _src_is_field(j):
                    j = _prod(L, j, L[j].rs) if L[j].m in ('addiu',) else j
                    return j
                if P.m == 'addiu' and P.rs != 0:
                    tot, q = 0, p
                    while q is not None and L[q].m == 'addiu' and L[q].rs != 0:
                        tot += L[q].simm; q = _prod(L, q, L[q].rs)
                    if q is not None and L[q].m == 'lw' and L[q].simm == d and _slot_a(L, _prod(L, q, L[q].rs, 16)) == n:
                        r = inplace_long('add', n, d & 0xffff, ('imm', tot))
                elif P.m == 'dsrl32':
                    q = _prod(L, p, P.rt)
                    if q is not None and L[q].m == 'dsll32' and L[q].sa == P.sa:
                        s = _prod(L, q, L[q].rt)
                        if s is not None and L[s].m == 'lw' and L[s].simm == d and _slot_a(L, _prod(L, s, L[s].rs, 16)) == n:
                            r = inplace_long('logic_and', n, d & 0xffff, ('imm', (1 << (32 - P.sa)) - 1))
                elif P.m in ('xor', 'or', 'and'):
                    for rv, rc in ((P.rs, P.rt), (P.rt, P.rs)):
                        q = _prod(L, p, rv); c = _const(L, _prod(L, p, rc))
                        if c is not None and q is not None and L[q].m == 'lw' and L[q].simm == d \
                           and _slot_a(L, _prod(L, q, L[q].rs, 16)) == n:
                            r = inplace_long('logic_' + P.m, n, d & 0xffff, ('imm', c)); break
        elif x.m in ('sh', 'sb') and b is not None and _slot_a(L, b) is not None:
            # octet SIGNE d'une table -> champ d'une structure (positions X/Y d'une table, mips 0x1F65FC...) :
            # MOVE.L Dt,-(SP) ; MOVE.B T(PC,Dk.W),Dt ; [EXT.W Dt] ; MOVE.x Dt,d(An) ; MOVEM.L (SP)+,Dt
            n = _slot_a(L, b); d = x.simm & 0xffff
            jl = _orig(L, _prod(L, i, x.rt), False)
            if jl is not None and L[jl].m == 'lb':
                ja = _prod(L, jl, L[jl].rs); off = L[jl].simm
                while ja is not None and L[ja].m == 'addiu' and L[ja].rs != 0:
                    off += L[ja].simm; ja = _prod(L, ja, L[ja].rs)
                if ja is not None and L[ja].m == 'addu':
                    for ri, rt_ in ((L[ja].rs, L[ja].rt), (L[ja].rt, L[ja].rs)):
                        tb = _const(L, _prod(L, ja, rt_)); sk = _slot_d(L, _orig(L, _prod(L, ja, ri)))
                        if tb is None or not sk or addr_to_68k((tb + off) & 0xffffffff) is None: continue
                        k = sk[0]; t = 2 if k == 1 else 1; tb = (tb + off) & 0xffffffff
                        sz = 'W' if x.m == 'sh' else 'B'
                        st = (0x3000 if sz == 'W' else 0x1000) | ((n & 7) << 9) | (5 << 6) | t
                        r = [([0x2f00 | t], "MOVE.L D%d,-(SP)  [registre de travail]" % t),
                             ([0x103b | (t << 9), (k << 12)], "MOVE.B T_%06x(PC,D%d.W),D%d" % (tb, k, t)),
                             (([0x4880 | t] if sz == 'W' else []) + [st, d, 0x4cdf, 1 << t],
                              "%sMOVE.%s D%d,$%04x(A%d) ; MOVEM.L (SP)+,D%d" % ("EXT.W D%d ; " % t if sz == 'W' else "", sz, t, d, n, t))]
                        break
        elif x.m == 'sh' and b is not None and L[b].m == 'lui' and L[b].imm != 0x7000:
            host = ((L[b].imm << 16) + x.simm) & 0xffffffff
            p = _prod(L, i, x.rt)
            if p is not None and L[p].m == 'and':
                for rv, rc in ((L[p].rs, L[p].rt), (L[p].rt, L[p].rs)):
                    q = _prod(L, p, rv); c = _const(L, _prod(L, p, rc))
                    if c is not None and q is not None and L[q].m in ('lh', 'lhu'):
                        bq = _prod(L, q, L[q].rs)
                        if bq is not None and L[bq].m == 'lui' and ((L[bq].imm << 16) + L[q].simm) & 0xffffffff == host:
                            a, note = abs_addr(host, 'W')
                            r = ([0x0279, c & 0xffff, (a >> 16) & 0xffff, a & 0xffff], "ANDI.W #$%x,$%06x.L%s" % (c & 0xffff, a & 0xffffff, note)); break
        elif x.m == 'swr' and b is not None and L[b].m == 'lui' and i + 2 < len(L):
            host = ((L[b].imm << 16) + x.simm) & 0xffffffff
            c = _const(L, _prod(L, i, x.rt))
            if c is not None and host % 2 == 0 and host % 4 == 2 and addr_to_68k(host) is not None:
                a = addr_to_68k(host)
                v = ((c & 0xffff) << 16) | (c >> 16)          # mots dans l'ordre 68K : bas a l'adresse paire
                r = ([0x23fc, (v >> 16) & 0xffff, v & 0xffff, (a >> 16) & 0xffff, a & 0xffff],
                     "MOVE.L #$%08x,$%06x.L  [long non aligne swr/swl]" % (v, a & 0xffffff))
        if r: add.append((x.va, r))
    if not add: return out, 0
    res = list(out)
    for va, r in sorted(add, key=lambda e: e[0]):
        k = 0
        while k < len(res) and res[k][0] < va: k += 1
        seq = r if isinstance(r, list) else [r]                 # une ou plusieurs instructions
        for q, (ws, mn) in enumerate(seq):
            res.insert(k + q, (va, mn + ("  [ecriture memoire retrouvee]" if q == len(seq) - 1 else ""), ws))
    return res, len(add)
