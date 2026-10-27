"""Citations de victoire des 4 persos MAX au format d'Upper (module ro5).
Upper : table 0x48E2A0 (fichier ro5) = 40 u16 décalages (relatifs à la table) → bloc par ID ; bloc = 8 u16 décalages
(relatifs au bloc) + 2 octets nuls + 8 citations « [x] texte 0 [x] texte 0 », bourrage à un nombre pair d'octets.
Vérifié : le bloc reconstruit depuis winXX_e.pac (PSP) est identique octet pour octet à celui d'Upper pour Ryu, Ken et
Adon (Sagat : une coquille corrigée sur PSP). Sortie ~/.cache/sfa3max/converti/plXX/citations_upper.bin."""
import os, struct, json
import textes_max as T
def bloc(cid):
    C = T.textes(cid)["citations"]
    corps = [b"".join(bytes([l["x"]]) + l["texte"].encode("ascii") + b"\0" for l in r["lignes"]) for r in C]
    assert len(corps) == 8
    offs, pos = [], 18
    for c in corps: offs.append(pos); pos += len(c)
    b = struct.pack("<8H", *offs) + b"\0\0" + b"".join(corps)
    return b + (b"\0" if len(b) % 2 else b"")
if __name__ == "__main__":
    B = open(os.path.join(os.environ["ANTHOLOGY_DIR"], "decompressed", "ro5_usa_prog68k.bin"), "rb").read()
    offs = struct.unpack_from("<40H", B, 0x48E2A0); fin = max(0x48E2A0 + o for o in offs)
    autorises = set(B[0x48E2F0:fin + 0x200])          # caractères déjà présents dans les citations d'Upper
    for cid in (0x26, 0x27, 0x28, 0x29):
        b = bloc(cid); d = os.path.expanduser("~/.cache/sfa3max/converti/pl%02x" % cid)
        open(os.path.join(d, "citations_upper.bin"), "wb").write(b)
        manquants = {chr(c) for c in b[18:] if c >= 0x20 and c not in autorises}
        print("pl%02x : %d octets, caractères absents d'Upper : %s" % (cid, len(b), manquants or "aucun"))
