#!/usr/bin/env python3
"""
pine_linux.py — client PINE pour PCSX2 SOUS LINUX (socket UNIX, pas TCP).
Même protocole que pine_lab.py (Windows/TCP) mais transport AF_UNIX.

PCSX2 Linux crée le socket dans $TMPDIR (ou /tmp) : 'pcsx2.sock' pour le slot par
défaut 28011, sinon 'pcsx2.sock.<slot>'. On auto-détecte.

Usage : from pine_linux import Pine ; p=Pine(); p.rd32(0xb88000)
"""
import socket, struct, os, glob

def _candidates(slot=28011):
    dirs = [os.environ.get("TMPDIR"), os.environ.get("XDG_RUNTIME_DIR"),
            "/run/user/%d" % os.getuid(), "/tmp"]
    names = ["pcsx2.sock", "pcsx2.sock.%d" % slot]
    out = []
    for d in dirs:
        if not d:
            continue
        for n in names:
            out.append(os.path.join(d, n))
    # + tout pcsx2*.sock trouvé
    for d in dirs:
        if d:
            out += glob.glob(os.path.join(d, "*pcsx2*.sock*"))
    seen = set(); uniq = []
    for p in out:
        if p not in seen and os.path.exists(p):
            seen.add(p); uniq.append(p)
    return uniq

class Pine:
    def __init__(s, path=None, slot=28011):
        cands = [path] if path else _candidates(slot)
        last = None
        for c in cands:
            if not c:
                continue
            try:
                sk = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sk.settimeout(5); sk.connect(c)
                s.sock = sk; s.path = c; return
            except Exception as e:
                last = e
        raise ConnectionError("aucun socket PINE trouvé (candidats: %s ; dernière err: %r)"
                              % (cands, last))
    def _req(s, op, addr, payload=b''):
        msg = struct.pack('<IBI', 9 + len(payload), op, addr) + payload
        s.sock.send(msg)
        hdr = s.sock.recv(5); size, res = struct.unpack('<IB', hdr)
        data = b''
        while len(data) < size - 5:
            data += s.sock.recv(size - 5 - len(data))
        return res, data
    def rd8(s, a):  return s._req(0, a)[1][0]
    def rd16(s, a): return struct.unpack('<H', s._req(1, a)[1])[0]
    def rd32(s, a): return struct.unpack('<I', s._req(2, a)[1])[0]
    def rdblk(s, a, n):
        return b''.join(struct.pack('<I', s.rd32(a + i)) for i in range(0, n, 4))
    def wr8(s, a, v):  return s._req(4, a, struct.pack('<B', v))[0]
    def wr16(s, a, v): return s._req(5, a, struct.pack('<H', v))[0]
    def wr32(s, a, v): return s._req(6, a, struct.pack('<I', v))[0]

if __name__ == "__main__":
    print("sockets candidats:", _candidates())
    try:
        p = Pine()
        print("connecté:", p.path)
        b = p.rd32(0x1dc2e4)
        print("bank 0x1dc2e4 = %#x (%s)" % (b, "z9/Hyper" if b == 0xdb4000 else "z5/Upper" if b == 0xd35800 else "?"))
    except Exception as e:
        print("échec:", e)
