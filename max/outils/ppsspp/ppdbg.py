"""Client minimal du débogueur WebSocket de PPSSPP (bibliothèque standard seule).
Usage : from ppdbg import Dbg ; d = Dbg(port) ; d.req("cpu.status") ; d.r32(adr) ; d.boutons(...) ; d.capture(fichier)
Adresses : celles du PSP (les adresses « EBOOT » des outils + base du module, cf. base())."""
import socket, os, base64, json, struct, time
class Dbg:
    def __init__(s, port, hote="127.0.0.1"):
        s.k = socket.create_connection((hote, port), timeout=120); cle = base64.b64encode(os.urandom(16)).decode()
        s.k.sendall(("GET /debugger HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                     "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: debugger.ppsspp.org\r\n\r\n"
                     % (hote, port, cle)).encode())
        rep = b""
        while b"\r\n\r\n" not in rep: rep += s.k.recv(4096)
        if b" 101 " not in rep.split(b"\r\n")[0]: raise RuntimeError(rep[:200])
        s.tampon = rep.split(b"\r\n\r\n", 1)[1]; s.ticket = 0
    def _envoi(s, texte):
        d = texte.encode(); m = os.urandom(4); n = len(d)
        h = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n) if n < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", n))
        s.k.sendall(h + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))
    def _lire(s, n):
        while len(s.tampon) < n:
            x = s.k.recv(65536)
            if not x: raise ConnectionError("fermé")
            s.tampon += x
        r, s.tampon = s.tampon[:n], s.tampon[n:]; return r
    def _trame(s):
        """message complet (réassemble les fragments : FIN = bit 7, suite = opcode 0)"""
        fin, op, d = s._fragment()
        while not fin:
            fin, _, x = s._fragment(); d += x
        return op, d
    def _fragment(s):
        b0, b1 = s._lire(2); n = b1 & 0x7F
        if n == 126: n = struct.unpack(">H", s._lire(2))[0]
        elif n == 127: n = struct.unpack(">Q", s._lire(8))[0]
        m = s._lire(4) if b1 & 0x80 else None; d = s._lire(n)
        if m: d = bytes(b ^ m[i % 4] for i, b in enumerate(d))
        return bool(b0 & 0x80), b0 & 0x0F, d
    def req(s, evt, attendre=None, **kw):
        """attendre : nom d'un événement diffusé (sans ticket) qui vaut réponse (ex. cpu.stepping)"""
        s.ticket += 1; t = s.ticket; kw.update(event=evt, ticket=t); s._envoi(json.dumps(kw))
        while True:
            op, d = s._trame()
            if op == 8: raise ConnectionError("fermeture")
            if op != 1: continue
            m = json.loads(d)
            if m.get("ticket") == t or (attendre and m.get("event") == attendre and "ticket" not in m):
                if m.get("event") == "error": raise RuntimeError(m)
                return m
    def r32(s, a): return s.req("memory.read_u32", address=a)["uintValue"]
    def r16(s, a): return s.req("memory.read_u16", address=a)["uintValue"]
    def r8(s, a): return s.req("memory.read_u8", address=a)["uintValue"]
    def lire(s, a, n): return base64.b64decode(s.req("memory.read", address=a, size=n)["base64"])
    def pause(s):
        if s.req("cpu.status").get("stepping"): return None          # déjà en pause : aucun événement ne viendrait
        return s.req("cpu.stepping", attendre="cpu.stepping")
    def reprise(s):
        if not s.req("cpu.status").get("stepping"): return None
        return s.req("cpu.resume", attendre="cpu.resume")
    def capture(s, f, reprendre=True):
        s.pause()
        try: r = s.req("gpu.buffer.screenshot", type="uri")
        finally:
            if reprendre: s.reprise()
        d = r.get("uri", "").split(",", 1)[-1]; open(f, "wb").write(base64.b64decode(d)); return f
    def boutons(s, **b): return s.req("input.buttons.send", buttons=b)
    def appui(s, bouton, duree=0.1):
        s.req("input.buttons.press", button=bouton, duration=max(1, int(duree * 60)))
# Bases de relocation SFA3 MAX EU (ULES00235) : code (adresses EBOOT < fin du texte) +0x08804000 ; données +0x08AD8F30
# (mesuré sur les LUI/ADDIU relogés : 0xA3E7C6 -> 0x095176F6, 0x39C9E0 -> 0x08E75910, 0x87FCB0 -> 0x09358BE0)
CODE, DONNEES = 0x08804000, 0x08AD8F30
FIN_SEG0 = 0x2D4F30           # ELF : segment 0 (code + données en lecture seule) va 0..0x2D4F30, segment 1 au-delà
def adr(va): return va + (CODE if va < FIN_SEG0 else DONNEES)
