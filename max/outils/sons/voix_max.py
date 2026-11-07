"""Voix des persos MAX (2026-10-07) : banque PSP du pack plXX_e.pac = section « PPHD » (table PPVA : entrées de 16 o =
décalage, fréquence, taille, -1) + section suivante = données ADPCM PSP (blocs VAG de 16 o). Décodage PS-ADPCM -> WAV
16 bits dans ~/.cache/sfa3max/converti/plXX/voix/vNN.wav + voix.json (n° = index PPVA = code PSP $200 | n, cf. 0x78408).
python voix_max.py [pl26 ...]"""
import os, sys, struct, json, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "max"))
from plpac import split
import paths
COEF = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
def vag(b):
    out, s1, s2 = [], 0, 0
    for k in range(len(b) // 16):
        blk = b[16 * k:16 * k + 16]
        pr, sh, fl = blk[0] >> 4, blk[0] & 15, blk[1]
        if fl == 7: break
        c1, c2 = COEF[pr] if pr < 5 else (0, 0)
        for x in blk[2:]:
            for n in (x & 15, x >> 4):
                v = (n - 16 if n >= 8 else n) << 12
                v = (v >> sh) + ((s1 * c1 + s2 * c2) >> 6)
                v = max(-32768, min(32767, v)); out.append(v); s2, s1 = s1, v
    return out
def banque(pl):
    S = split(open(os.path.join(paths.pac_dir(), "%s_e.pac" % pl), "rb").read())
    b = [s[1] if isinstance(s, tuple) else s for s in S]
    i = next(k for k, x in enumerate(b) if x[:4] == b"PPHD")
    h, data = b[i], b[i + 1]
    va = h.find(b"PPVA")
    n = struct.unpack_from("<I", h, va + 0x14)[0] + 1             # dernier n° d'entrée + 1
    ent = []
    for k in range(n):
        off, fr, taille, m1 = struct.unpack_from("<IIIi", h, va + 0x20 + 16 * k)
        ent.append(None if off == 0xFFFFFFFF or off + taille > len(data) else (off, fr, taille))   # entrée vide
    return ent, data
def table_sons(pl):
    """table de sons du perso (section de 1024 o après PPHD + données : 64 entrées de 16 o, 8 mots) : n° de voix ->
    échantillon. Mot 0 = type (0 : échantillon de la banque du perso = mot 2 − $300 ; $400+ : autre banque, mot 2 =
    n° dans celle-ci ; −1 : aucun son, aussi muet sur PSP), mot 1 = priorité ?, mot 3 = 8 (volume ?). Lu par 0x60BC."""
    S = split(open(os.path.join(paths.pac_dir(), "%s_e.pac" % pl), "rb").read())
    b = [s[1] if isinstance(s, tuple) else s for s in S]
    i = next(k for k, x in enumerate(b) if x[:4] == b"PPHD")
    t = b[i + 2]
    assert len(t) == 1024, (pl, len(t))
    out = []
    for n in range(64):
        e = struct.unpack_from("<8h", t, 16 * n)
        if e[0] == -1: out.append({"n": n, "muet": True})
        elif e[0] == 0 and e[2] >= 0x300: out.append({"n": n, "echantillon": e[2] - 0x300, "priorite": e[1]})
        else: out.append({"n": n, "type": e[0], "autre_banque": e[2], "priorite": e[1]})
    return out
if __name__ == "__main__":
    for pl in (sys.argv[1:] or ["pl26", "pl27", "pl28", "pl29"]):
        ent, data = banque(pl)
        d = os.path.join(os.path.expanduser("~/.cache/sfa3max/converti"), pl, "voix"); os.makedirs(d, exist_ok=True)
        info = []
        for n, e in enumerate(ent):
            if e is None: info.append({"n": n, "vide": True}); continue
            off, fr, taille = e
            pcm = vag(data[off:off + taille])
            with wave.open(os.path.join(d, "v%02d.wav" % n), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(fr); w.writeframes(struct.pack("<%dh" % len(pcm), *pcm))
            info.append({"n": n, "frequence": fr, "echantillons": len(pcm), "duree_s": round(len(pcm) / fr, 3)})
        json.dump({"echantillons": info, "table_sons": table_sons(pl)}, open(os.path.join(d, "voix.json"), "w"), indent=0)
        print(pl, sum(1 for e in ent if e), "voix sur", len(ent), "n°,", "%.1f s" % sum(x.get("duree_s", 0) for x in info), "->", d)
