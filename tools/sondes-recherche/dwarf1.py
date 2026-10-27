# Lecteur DWARF 1 minimal (MetroWerks MIPS) : structures et membres avec décalages.
import struct, sys
d = open(sys.argv[1], 'rb').read()
want = sys.argv[2] if len(sys.argv) > 2 else None
def parse_loc(b):
    i, st = 0, []
    while i < len(b):
        op = b[i]; i += 1
        if op in (1, 2, 3, 4):
            st.append(struct.unpack_from('<I', b, i)[0]); i += 4
        elif op == 7 and len(st) >= 1:
            pass
    return st[-1] if st else None
off, stack, structs = 0, [], {}
cur = None
while off + 4 <= len(d):
    ln = struct.unpack_from('<I', d, off)[0]
    if ln < 8:
        off += max(ln, 4); continue
    end = off + ln
    tag = struct.unpack_from('<H', d, off + 4)[0]
    p = off + 6; at = {}
    while p + 2 <= end:
        a = struct.unpack_from('<H', d, p)[0]; p += 2; f = a & 0xf
        if f in (1, 2, 6): v = struct.unpack_from('<I', d, p)[0]; p += 4
        elif f == 5: v = struct.unpack_from('<H', d, p)[0]; p += 2
        elif f == 7: v = d[p:p+8]; p += 8
        elif f == 3: n = struct.unpack_from('<H', d, p)[0]; v = d[p+2:p+2+n]; p += 2 + n
        elif f == 4: n = struct.unpack_from('<I', d, p)[0]; v = d[p+4:p+4+n]; p += 4 + n
        elif f == 8:
            q = d.index(b'\0', p); v = d[p:q].decode('latin1'); p = q + 1
        else: break
        at[a] = v
    while stack and off >= stack[-1][1]: stack.pop()
    if tag in (0x13, 0x17):  # structure / union
        cur = [at.get(0x38, '?'), at.get(0xb6), []]
        structs.setdefault(cur[0], []).append(cur)
        stack.append((cur, at.get(0x12, end)))
    elif tag == 0x0d and stack:
        loc = at.get(0x23)
        stack[-1][0][2].append((parse_loc(loc) if isinstance(loc, bytes) else None, at.get(0x38, '?')))
    off = end
if want:
    for s in structs.get(want, [])[:1]:
        print(s[0], 'taille', s[1])
        for o, n in s[2]: print('  +%04X %s' % (o if o is not None else 0xFFFF, n))
else:
    for k, v in structs.items():
        if v[0][2]: print(k, v[0][1], len(v[0][2]))
