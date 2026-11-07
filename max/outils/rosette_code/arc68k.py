"""Désassemblage récursif (capstone) du code 68K arcade de SFA3 (sfa3ud déchiffré, sfa3_prog.bin).
Suit branches, BSR/JSR (dans la région), et tables de saut Capcom :
  MOVE.W tab(PC,Dn.W),Dm ; JMP/JSR tab(PC,Dm.W)   (table de décalages 16 bits relatifs à tab)."""
import struct, re, capstone
_P = __import__("os").path.join(__import__("os").environ.get("HSFA_WORK", "work"), "cps2", "sfa3_prog.bin")
# (2026-11-07) sans programme d'arcade (construction depuis les seuls disques) : B vide. Les outils d'APPRENTISSAGE (tout,
# tailles68, evaluer, appris_acteurs, mouvements, champs_projectiles) en ont besoin ; les autres l'importent seulement
# (brouillons, tables_explicites, projectiles_max, acteurs_fins, anims_fins_max : 0 octet lu) et lisent les tables
# apprises versionnées de ce dossier (api_arcade_psp.json, champs_votes.json, tailles68.json, carte_champs.json,
# api_acteurs.json).
B = open(_P, "rb").read() if __import__("os").path.exists(_P) else b""
L = lambda a: struct.unpack_from(">I", B, a)[0]; Ws = lambda a: struct.unpack_from(">h", B, a)[0]
md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000)
md.detail = False
def one(a):
    for i in md.disasm(B[a:a+10], a): return i
    return None
TERM = {"rts", "rte", "jmp", "bra", "bra.b", "bra.w", "bra.s"}
def explore(entries, lo, hi):
    """-> (instructions {addr: ins}, tables {addr: [cibles]}, appels externes {cible: n})"""
    seen, tables, ext, todo = {}, {}, {}, list(entries)
    while todo:
        a = todo.pop()
        prev = None
        while lo <= a < hi and a not in seen:
            i = one(a)
            if i is None: break
            seen[a] = i; m, op = i.mnemonic, i.op_str
            mt = re.match(r"\$([0-9a-f]+)\(pc, d(\d)\.w\)", op)
            if m in ("jmp", "jsr") and mt and prev is not None and prev.mnemonic == "move.w":
                pt = re.match(r"\$([0-9a-f]+)\(pc, d\d\.w\), d(\d)", prev.op_str)
                if pt:
                    t = int(pt.group(1), 16); base = int(mt.group(1), 16)
                    if t == base and t not in tables:
                        tg, k, lim = [], 0, hi
                        while t + 2*k < lim:
                            o = Ws(t + 2*k); x = base + o
                            if not (lo <= x < hi) or x % 2: break
                            tg.append(x); lim = min(lim, x); k += 1
                        tables[t] = tg; todo += tg
            if m in ("bsr", "bsr.b", "bsr.w", "bsr.s", "jsr") or m.startswith("b") and m not in ("btst", "bset", "bclr", "bchg") or m in ("jmp", "dbra") or m.startswith("db"):
                mm = re.search(r"\$([0-9a-f]+)(\.l)?$", op)
                if mm and "(" not in op:
                    x = int(mm.group(1), 16)
                    if lo <= x < hi: todo.append(x)
                    elif m in ("jsr", "jmp", "bsr", "bsr.w", "bsr.b"): ext[x] = ext.get(x, 0) + 1
            if m in TERM: break
            prev = i; a += i.size
    return seen, tables, ext
