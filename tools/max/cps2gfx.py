#!/usr/bin/env python3
"""cps2gfx - decodeur/encodeur de tiles graphiques CPS2 (port de FBNeo cps.cpp).

Tiles 16x16, 4bpp planar. Le decodage suit exactement Cps2LoadTiles ->
Cps2LoadOne -> Cps2Load100000 + Separate() de FBNeo.

Sortie d'un tile = 256 octets (16x16, 1 octet/pixel = index palette 0..15).

Usage:
  python cps2gfx.py decode <rom_dir_or_zip> <game> [--tiles N] [--out preview.png]
"""
import sys, struct

# --- Separate() : eclate les 8 bits d'un octet sur 4 plans (1 bit / octet) ---
def separate(b):
    a = b
    a = ((a & 0x000000F0) << 12) | (a & 0x0000000F)
    a = ((a & 0x000C000C) <<  6) | (a & 0x00030003)
    a = ((a & 0x02020202) <<  3) | (a & 0x01010101)
    return a & 0xFFFFFFFF

SEP = [separate(255 - i) for i in range(256)]   # SepTable[i] = Separate(255-i)

# --- Conversion couleur CPS2 -> RGB (port exact de cps_pal.cpp) ---
def cps2_color_to_rgb(pal):
    """pal = u16 BGR444 + brightness. Retourne (r,g,b) 0..255.
    Bright = 0x0f + ((pal>>12)<<1) ; comp = nibble * 0x11 * Bright / 0x2d."""
    bright = 0x0f + ((pal >> 12) << 1)
    r = ((pal >> 8) & 0x0f) * 0x11 * bright // 0x2d
    g = ((pal >> 4) & 0x0f) * 0x11 * bright // 0x2d
    b = ((pal >> 0) & 0x0f) * 0x11 * bright // 0x2d
    return (min(r,255), min(g,255), min(b,255))

def load_palette_raw(path, offset, count=16):
    """Lit 'count' couleurs u16 LE depuis un fichier binaire a 'offset'.
    Retourne liste de (r,g,b)."""
    with open(path, "rb") as f:
        f.seek(offset)
        raw = f.read(count*2)
    out = []
    for i in range(count):
        v = raw[i*2] | (raw[i*2+1] << 8)
        out.append(cps2_color_to_rgb(v))
    return out

def decode_gfx(roms):
    """Reproduit FIDELEMENT Cps2LoadTiles (NON-turbo) de FBNeo.
    'roms' = liste de 8 buffers gfx dans l'ordre FBNeo (13m,15m,17m,19m,14m,16m,18m,20m).
    Les roms sont traitees par GROUPES DE 4 (Cps2LoadTiles, nLoadedRoms=4).
    Retourne le buffer Tile (4bpp packed, 128 o / tile 16x16)."""
    rom_len = len(roms[0])
    ngroups = len(roms) // 4
    # taille Tile : chaque groupe de 4 roms -> rom_len*4 octets de Tile
    Tile = bytearray(rom_len * 4 * ngroups)

    def load100000(tile_off, src, src_off, nShift):
        pt = tile_off; ps = src_off; end = tile_off + 0x100000
        while pt < end:
            Pix = SEP[src[ps]] | (SEP[src[ps+1]] << 1)
            Pix = (Pix << nShift) & 0xFFFFFFFF
            cur = Tile[pt] | (Tile[pt+1]<<8) | (Tile[pt+2]<<16) | (Tile[pt+3]<<24)
            cur |= Pix
            Tile[pt]=cur&0xFF; Tile[pt+1]=(cur>>8)&0xFF; Tile[pt+2]=(cur>>16)&0xFF; Tile[pt+3]=(cur>>24)&0xFF
            pt += 8; ps += 4

    def load_one(tile_base, rom, nShift):
        # Cps2LoadOne nWord=1 : blocs de 0x100000, Cps2Load100000(pt,pr,sh);pt+=0x100000;(pt,pr+2,sh);pr+=0x80000
        pt = tile_base; pr = 0
        for b in range(len(rom) >> 19):
            load100000(pt, rom, pr, nShift); pt += 0x100000
            load100000(pt, rom, pr+2, nShift); pt += 0x100000
            pr += 0x80000

    for g in range(ngroups):
        r = roms[g*4 : g*4+4]
        tbase = g * (rom_len * 4)
        # Cps2LoadTiles : (Tile,+0,sh0)(Tile,+1,sh2)(Tile+4,+2,sh0)(Tile+4,+3,sh2)
        load_one(tbase + 0, r[0], 0)
        load_one(tbase + 0, r[1], 2)
        load_one(tbase + 4, r[2], 0)
        load_one(tbase + 4, r[3], 2)
    return Tile

def tiles_to_png_color(Tile, ntiles, out, palettes, cols=32):
    """Comme tiles_to_png mais avec de VRAIES couleurs.
    palettes = liste de palettes, chacune = liste de 16 (r,g,b).
    Chaque tile utilise palettes[tile_index % len(palettes)] (heuristique d'apercu)."""
    from PIL import Image
    rows = (ntiles + cols - 1) // cols
    W, H = cols*16, rows*16
    img = Image.new("RGB", (W, H))
    px = img.load()
    npal = len(palettes)
    for t in range(ntiles):
        base = t*128
        tx = (t % cols)*16; ty = (t // cols)*16
        pal = palettes[(t // cols) % npal]   # 1 palette par RANGEE (pour voir l'effet)
        for y in range(16):
            row = base + y*8
            for half in (0,4):
                b = Tile[row+half] | (Tile[row+half+1]<<8) | (Tile[row+half+2]<<16) | (Tile[row+half+3]<<24)
                for px_i in range(8):
                    idx = (b>>28)&0xF; b=(b<<4)&0xFFFFFFFF
                    xx = tx + (0 if half==0 else 8) + px_i
                    px[xx, ty+y] = pal[idx]
    img.save(out)
    print(f"  PNG couleur ecrit: {out} ({W}x{H})")

def tiles_to_png(Tile, ntiles, out, cols=32):
    """Range les tiles 16x16 (256 o chacun) en grille PNG, palette grayscale 16."""
    from PIL import Image
    rows = (ntiles + cols - 1) // cols
    W, H = cols*16, rows*16
    img = Image.new("P", (W, H))
    # palette grise 16 niveaux (index 0..15)
    pal = []
    for i in range(16):
        v = i*17
        pal += [v, v, v]
    pal += [0,0,0]*(256-16)
    img.putpalette(pal)
    px = img.load()
    # Organisation REELLE (ctv_do.h) : tile 16x16 = 16 lignes de 8 octets
    # (nCtvTileAdd=8). Chaque ligne : u32@+0 = 8 px gauche, u32@+4 = 8 px droite,
    # 4bpp PACKED : pixel = (b >> 28) en lisant b<<=4 a chaque pixel (MSB first).
    # Donc octet d'un u32 little-endian : on lit b = u32 LE, puis pixels = nibbles
    # depuis le MSB. 1 tile = 16*8 = 128 octets.
    TILE_BYTES = 128
    for t in range(ntiles):
        base = t*TILE_BYTES
        tx = (t % cols)*16
        ty = (t // cols)*16
        for y in range(16):
            row = base + y*8
            # 8 px gauche depuis u32 @ row+0, 8 px droite depuis u32 @ row+4
            for half in (0, 4):
                b = Tile[row+half] | (Tile[row+half+1]<<8) | (Tile[row+half+2]<<16) | (Tile[row+half+3]<<24)
                for px_i in range(8):
                    idx = (b >> 28) & 0xF
                    b = (b << 4) & 0xFFFFFFFF
                    xx = tx + (0 if half==0 else 8) + px_i
                    px[xx, ty+y] = idx
    img.save(out)
    print(f"  PNG ecrit: {out} ({W}x{H}, {ntiles} tiles)")

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "decode":
        print(__doc__); return
    # charger les roms gfx SFA3 depuis le zip
    import zipfile
    zpath = sys.argv[2]
    game = sys.argv[3] if len(sys.argv) > 3 else "sfa3"
    ntiles = 1024
    out = "preview.png"
    if "--tiles" in sys.argv: ntiles = int(sys.argv[sys.argv.index("--tiles")+1])
    if "--out" in sys.argv: out = sys.argv[sys.argv.index("--out")+1]

    # SFA3 gfx roms = sz3.13m..20m (8 roms de 4Mo). Ordre FBNeo.
    gfx_roms = ["sz3.13m","sz3.15m","sz3.17m","sz3.19m","sz3.14m","sz3.16m","sz3.18m","sz3.20m"]
    zf = zipfile.ZipFile(zpath)
    have = set(zf.namelist())
    roms = []
    used = []
    for r in gfx_roms:
        if r in have:
            roms.append(zf.read(r)); used.append(r)
    print(f"gfx roms utilisees ({len(roms)}): {used}")
    if len(roms) < 4:
        print("Pas assez de roms gfx (besoin de groupes de 4)"); return
    # tronquer a un multiple de 4
    roms = roms[:(len(roms)//4)*4]
    Tile = decode_gfx(roms)
    print(f"buffer Tile decode: {len(Tile):,} octets ({len(Tile)//128:,} tiles)")
    tiles_to_png(Tile, ntiles, out)

if __name__ == "__main__":
    main()
