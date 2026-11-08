#!/usr/bin/env python3
"""pine.py : client PINE minimal (PCSX2). Socket : $PINE_SOCK (défaut $PS2_DIR/run/pcsx2.sock).
Usage : pine.py r8|r16|r32 ADR  ;  pine.py w8|w16 ADR VAL  ;  pine.py status
Écritures permises (décision du 07/11) : vie de l'adversaire et niveau de jauge, pour ces essais seulement."""
import socket, struct, sys, os
SOCK = os.environ.get('PINE_SOCK') or os.path.join(os.environ.get('PS2_DIR', 'ps2'), 'run', 'pcsx2.sock')
def req(op, payload=b''):
    s = socket.socket(socket.AF_UNIX); s.connect(SOCK)
    m = bytes([op]) + payload; s.sendall(struct.pack('<I', len(m) + 4) + m)
    h = s.recv(4); n = struct.unpack('<I', h)[0]; d = b''
    while len(d) < n - 4: d += s.recv(n - 4 - len(d))
    s.close(); return d
def r(sz, a):
    op = {8: 0, 16: 1, 32: 2}[sz]; d = req(op, struct.pack('<I', a))
    assert d[0] == 0, 'PINE echec'; return int.from_bytes(d[1:1 + sz // 8], 'little')
def w(sz, a, v):
    op = {8: 4, 16: 5}[sz]; d = req(op, struct.pack('<I', a) + v.to_bytes(sz // 8, 'little')); assert d[0] == 0
def status():
    d = req(0xF); return struct.unpack('<I', d[1:5])[0]   # 0 marche, 1 pause, 2 arrêt
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'status': print(status())
    elif c[0] == 'r': print('%x' % r(int(c[1:]), int(sys.argv[2], 16)))
    elif c[0] == 'w': w(int(c[1:]), int(sys.argv[2], 16), int(sys.argv[3], 16))
