#!/usr/bin/env python3
"""PERSOS MAX DANS LE BANC MAME (HANDOFF §99) : schema de banques du fork, version banc.

Entree : sorties du convertisseur de la session MAX (~/.cache/sfa3max/converti/plNN/ : bank.bin, frames.json).

1. BANQUE DE SPRITES. Le fork rangera chaque banque A LA SUITE de la ROM graphique (code global = base + local,
   HANDOFF §48/§82). Le banc MAME est limite aux 32 Mo de la CPS2, deja pleins : il loge les tuiles dans
   - les tuiles qu'aucune table du banc ne reference (libres),
   - puis les tuiles EXCLUSIVES de banques sacrifiees (persos absents du test, ex. e262 Chun-Li, e280 R. Mika),
   en reutilisant les tuiles deja presentes a l'identique. Sorties :
     work/mame/roms_max/sfa3ud/sz3.13m..20m  (ROM graphique modifiee ; lancer MAME avec -rompath "roms_max;roms_tr")
     work/mame/banques/plNN.bin               (table locale -> code CPS2, format des f<N>.bin)
2. BLOC DE DONNEES a adresse FIXE (positions + frames de type 2), servi au 68K par banc_mem.lua :
     work/mame/ext_<base>.bin  (mots gros-boutistes) ; base par perso : $B00000 + $40000 * (perso - $26)
   Une adresse hors des plages converties traverse la conversion des pointeurs inchangee (identite en 68K).
   Format de frame (note frames-anthology-emetteur.md) : u16 2, u16 T, u16 n-1, [align 4], u32 ptr positions,
   n x (u16 code, u16 attr) ; positions : n x (s16 dx, s16 dy).
   Index des frames -> adresse : work/mame/banques/plNN_frames.json

Usage : banques_max.py pl26 [--sacrifier 262,280]
"""
import os, sys, json, struct
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import cps2rom

CONV = os.path.expanduser("~/.cache/sfa3max/converti")
W = "<workspace>/work/mame"
ROMDIR = os.path.join(W, "roms", "sfa3ud")
OUTROM = os.path.join(W, "roms_max", "sfa3ud")
BANQ = os.path.join(W, "banques")
N = 262144
VIDE = 0xFFFFFFFF
BASES = {"pl26": 0xB00000, "pl27": 0xB40000, "pl28": 0xB80000, "pl29": 0xBC0000}

def tables_banc():
    """{nom: codes 16x16 references} pour toutes les tables du banc"""
    out = {}
    for f in sorted(os.listdir(BANQ)):
        if not f.endswith(".bin") or (f.startswith("pl") and f[2:4].isdigit()): continue   # banques MAX (plNN) exclues, pas plan1/plan2
        t = np.fromfile(os.path.join(BANQ, f), "<u4"); t = t[t != VIDE].astype(np.int64)
        if f == "f312.bin": t = np.concatenate([t * 4 + k for k in range(4)])
        if f == "plan1.bin": t = t // 2
        out[f] = np.unique(t % N)
    return out

def bank_tiles(pl):
    """bank.bin : tuiles 16x16 4 bpp lineaires, quartet bas a gauche, valeurs brutes CPS2 -> (n,16,16)"""
    b = np.fromfile(os.path.join(CONV, pl, "bank.bin"), np.uint8).reshape(-1, 16, 8)
    px = np.empty((b.shape[0], 16, 16), np.uint8)
    px[:, :, 0::2] = b & 15; px[:, :, 1::2] = b >> 4
    return px

def banque(pl, sacrifier):
    roms = {s: open(os.path.join(ROMDIR, "sz3." + s), "rb").read() for g in cps2rom.GROUPS for s in g}
    L = len(roms["13m"])
    T = cps2rom.decode(roms).copy()
    tabs = tables_banc()
    cnt = np.zeros(N, np.int32)
    for u in tabs.values(): cnt[u] += 1
    libre = cnt == 0
    for n in sacrifier:
        u = tabs["f%d.bin" % n]; libre[u[cnt[u] == 1]] = True
    libre[0] = False
    places = list(np.nonzero(libre)[0])
    index = {}
    for c in range(N):
        if not libre[c]: index.setdefault(T[c].tobytes(), c)
    px = bank_tiles(pl)
    tab = np.full(len(px), VIDE, np.uint32); reut = 0; k = 0
    for l in range(len(px)):
        cle = px[l].tobytes()
        if not px[l].any():                      # tuile vide : jamais dessinee utilement
            continue
        if cle in index: tab[l] = index[cle]; reut += 1; continue
        if k >= len(places): raise SystemExit("plus de place : %d tuiles posees sur %d" % (l, len(px)))
        c = places[k]; k += 1
        T[c] = px[l]; tab[l] = c; index[cle] = c
    os.makedirs(OUTROM, exist_ok=True)
    for s, d in cps2rom.encode(T, L).items():
        open(os.path.join(OUTROM, "sz3." + s), "wb").write(d)
    tab.astype("<u4").tofile(os.path.join(BANQ, pl + ".bin"))
    print("%s : %d tuiles, %d reutilisees (contenu deja en ROM), %d posees, %d places disponibles (libres + %s)"
          % (pl, len(px), reut, k, len(places), ",".join("e%d" % n for n in sacrifier)))

def bloc(pl):
    """positions + frames de type 2 a l'adresse fixe du perso"""
    base = BASES[pl]
    frames = json.load(open(os.path.join(CONV, pl, "frames.json")))
    pos = bytearray(); fr = bytearray(); adr = []
    npos = sum(len(f["objs"]) for f in frames) * 4
    fbase = base + ((npos + 15) & ~15)
    for f in frames:
        objs = f["objs"]; n = len(objs)
        pptr = base + len(pos)
        for dx, dy, code, at in objs: pos += struct.pack("<hh", dx, dy)
        a = fbase + len(fr); adr.append(a)
        rec = struct.pack("<HHH", 2, f["T"], n - 1)
        rec += bytes((-(a + 6)) & 3)              # bourrage jusqu'au multiple de 4 (A0 <- (A0+3) & ~3)
        rec += struct.pack("<I", pptr)
        for dx, dy, code, at in objs: rec += struct.pack("<HH", code & 0xffff, at & 0xffff)
        fr += rec
        if len(fr) & 1: fr += b"\0"
    pos += bytes(fbase - base - len(pos))
    d = bytes(pos + fr)
    if len(d) & 1: d += b"\0"
    assert len(d) <= 0x40000, "bloc %s trop grand" % pl
    open(os.path.join(W, "ext_%06x.bin" % base), "wb").write(bytes(b for i in range(0, len(d), 2) for b in (d[i+1], d[i])))
    json.dump(adr, open(os.path.join(BANQ, pl + "_frames.json"), "w"))
    print("%s : %d frames, bloc de %d octets en $%06x" % (pl, len(frames), len(d), base))

# (HANDOFF §129) FORK + module (MODULE=ro5) : pas de pose de tuiles (le fork lit max_gfx.bin + la table plNN_hx.bin de la
# session MAX) ; seul le bloc de frames est ecrit, dans le dossier de travail du module. Upper : $B04000 est pris par un
# bloc de frames du jeu (jusqu'a $B7DF4C) -> blocs MAX apres la fin des donnees externes ($C80000-$D3B6A0).
BASES_RO5 = {"pl26": 0xD40000, "pl27": 0xD80000, "pl28": 0xDC0000, "pl29": 0xE00000}

if __name__ == "__main__":
    pl = sys.argv[1] if len(sys.argv) > 1 else "pl26"
    if "--fork" in sys.argv:
        import profils
        W = profils.P['travail']; BANQ = os.path.join(W, "banques")
        if profils.NOM == "ro5": BASES = BASES_RO5
        os.makedirs(BANQ, exist_ok=True)
        bloc(pl); sys.exit(0)
    sac = [262, 280]
    if "--sacrifier" in sys.argv: sac = [int(x) for x in sys.argv[sys.argv.index("--sacrifier") + 1].split(",")]
    banque(pl, sac)
    bloc(pl)
