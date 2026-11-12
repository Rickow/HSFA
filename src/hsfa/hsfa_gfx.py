#!/usr/bin/env python3
"""(HANDOFF §116) ROM GRAPHIQUE ETENDUE du banc MAME derive (jeu sfa3hx, mame-fork) : les tuiles 16x16 des banques
du module ABSENTES de la ROM graphique de SFA3 (persos d'Upper, retouches...) sont dedoublonnees, numerotees a partir
du code $40000 (octet $2000000 de la region) et ecrites au FORMAT INTERNE de MAME (apres 'unshuffle', 128 octets par
tuile : ligne r = 8 octets, pixels 0-7 puis 8-15 ; 4 octets par groupe = plans du bit 0 au bit 3 ; pixel x au bit 7-x).
Les tables du banc (banques/f<N>.bin : local -> code) recoivent les nouveaux codes.

Usage : MODULE=ro5 hsfa_gfx.py [N...]   (defaut : banques de carte.txt)   -> <travail>/hsfa_gfx.bin, tables dans <banques>_hx/
IDEMPOTENT : chaque table etendue est recalculee depuis la table d'ORIGINE (<banques>/f<N>.bin), jamais depuis
<banques>_hx/ (deja completee par une execution precedente : relance, il n'y trouvait plus de tuile absente et
recrivait un hsfa_gfx.bin VIDE).
Verification de l'encodage : hsfa_gfx.py --verif <fichier de vidage de la region MAME> (tuiles SFA3)."""
import os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import banques, anthgfx, profils

EXT0 = 0x40000                      # premier code de la ROM etendue (region $2000000)
# (sfa3_restes, patch FBNeo 0025) SFA3 (MODULE=ro3) : tuiles d'objets du portage SANS correspondance dans la ROM d'arcade
# (ni exacte ni en miroir : dessins propres au portage dans les fins, ex. les poupees de Shadaloo), ajoutees telles quelles
# a partir du code $7F8C0 (octet $3FC6000 de la region) : sur 18 bits ce code vaut $3F8C0, et les tuiles $3F8C0-$3FFFF
# (1 856) de la ROM d'arcade comme de la ROM reconstruite depuis l'ISO sont TRANSPARENTES -> un pilote qui ignore les
# bits 18-19 (MAME d'origine, coeur sans le patch 0025) n'affiche rien a leur place (comme avant) au lieu d'autres tuiles.
# HSFA_GFX_CODE0 : autre premier code (essais). Upper / Hyper : $40000 (inchange).
if banques.MODULE == 'ro3':
    EXT0 = int(os.environ.get("HSFA_GFX_CODE0", "0x7F8C0"), 16)
    EXT_MAX = 0x80000                # au-dela, la tuile retomberait sur une tuile NON transparente de la ROM (18 bits)
else:
    EXT_MAX = None
VIDE = banques.VIDE
# (sfa3_qsound, patch FBNeo 0026) SFA3 : tuiles 32x32 de SCROLL3 du portage sans correspondance exacte dans la ROM d'arcade
# (redessinees : ex. ecran QSound, fin du « O » d'AUDIO sans le ™, local $858 ; intro, local $D4E). Sans tuile, la table
# f312 restait VIDE et le pilote affichait le repli « local + $0B00 » = une tuile quelconque (texte « nt N / rous » sur le
# logo QSound). Elles sont ajoutees TELLES QUELLES en ROM etendue : f312 = $4000 + ($C000 | j), j = $3F98, $3F99...
# Code de scroll3 a bits 14-15 = 11 : le coeur avec le patch 0026 (et hsfa_gfx.bin) lit la tuile a $2000000 + j * $200
# (octet j * $200 de hsfa_gfx.bin : fichier hsfa_gfx_s3.bin, place par paquet_fbneo.py en $7F3000) ; un pilote qui lit
# le code sur 14 bits (MAME, coeur sans 0026) affiche la tuile j de la ROM : $3F98-$3FFF sont TRANSPARENTES dans la ROM
# d'arcade comme dans la ROM reconstruite depuis l'ISO (rien a la place, au lieu d'une tuile parasite).
# SFA3_TUILES_S3=0 : f312 de banques_hx = celle de banques (v158), pas de hsfa_gfx_s3.bin.
S3_J0, S3_JFIN = 0x3F98, 0x4000
S3 = banques.MODULE == 'ro3' and os.environ.get("SFA3_TUILES_S3", "1") != "0"

def tuiles_s3(W, OUT):
    """f312 de <banques>_hx : tuiles 32x32 du portage absentes de la ROM -> codes $C000 | j ; hsfa_gfx_s3.bin"""
    src = os.path.join(banques.OUT, "f312.bin")
    if not os.path.exists(src): return
    t = np.fromfile(src, '<u4').copy()
    neuf, blob = {}, bytearray()
    for k, m, px in anthgfx.tiles(banques.fichier(banques.MOD['b32'])):
        if k != 2 or px is None or m >= len(t) or t[m] != VIDE: continue
        s = anthgfx.to_slots(2, px).astype(np.uint8)
        if (s == 15).all(): continue                  # tuile transparente : rien a afficher
        cle = s.tobytes()
        if cle not in neuf:
            j = S3_J0 + len(neuf)
            if j >= S3_JFIN: raise SystemExit("scroll3 : plus de %d tuiles du portage" % (S3_JFIN - S3_J0))
            neuf[cle] = j; blob += b"".join(encode(q) for q in s.reshape(4, 16, 16))
        t[m] = 0x4000 + (0xC000 | neuf[cle])
        print("f312 : local $%x -> tuile du portage j = $%x (code $%x)" % (m, neuf[cle], 0xC000 | neuf[cle]))
    t.astype('<u4').tofile(os.path.join(OUT, "f312.bin"))
    open(os.path.join(W, "hsfa_gfx_s3.bin"), "wb").write(blob)
    print("scroll3 : %d tuiles 32x32 du portage -> hsfa_gfx_s3.bin (%d octets, en $%x de hsfa_gfx.bin du paquet FBNeo)"
          % (len(neuf), len(blob), S3_J0 * 0x200))

def encode(px):
    """tuile 16x16 (valeurs 0-15) -> 128 octets au format interne de MAME"""
    px = np.asarray(px, np.uint8).reshape(16, 16)
    out = np.zeros((16, 2, 4), np.uint8)
    for h in range(2):
        blk = px[:, 8*h:8*h+8]                       # (16 lignes, 8 pixels)
        for b in range(4):                           # octet b = bit b de la valeur du pixel
            bits = (blk >> b) & 1
            out[:, h, b] = np.packbits(bits, axis=1)[:, 0]   # pixel 0 = bit de poids fort
    return out.tobytes()

def verif(dump):
    """compare l'encodage de tuiles SFA3 (cps2rom.decode) au vidage de la region 'gfx' de MAME"""
    import cps2rom
    roms = {s: open(os.path.join(banques.ROMDIR, "sz3.%s" % s), "rb").read() for g in cps2rom.GROUPS for s in g}
    T = cps2rom.decode(roms)
    d = open(dump, "rb").read()
    ok = 0; n = 0
    for c in range(0, min(len(T), len(d) // 128), 997):
        n += 1; ok += encode(T[c]) == d[128*c:128*c+128]
    print("encodage : %d/%d tuiles identiques au vidage MAME" % (ok, n))

# (ombre_iso, 11/11) OMBRES AUX CODES DU COEUR. Le patch FBNeo 0011 (« ombres transparentes (PSP) ») reconnait une
# ombre par la palette OBJ 0x14 ET le CODE global de la tuile : 0284A, 305DF-30613 (ROM de base) et 50888-5088A (Hyper :
# ombres des persos ZERO et ZERO 2, en ROM etendue). Les codes de la ROM etendue sont des RANGS d'apparition des tuiles
# absentes de la ROM de base : avec la ROM reconstruite depuis l'ISO (autres tuiles, retouches de l'Anthology), il y a
# moins de tuiles absentes et les trois ombres tombaient en 50648-5064A (contenu identique, hors de la liste du coeur) :
# ombre OPAQUE en voie ISO seule, transparente avec la ROM d'arcade. Regle : les tuiles du banc commun d'Hyper (e545,
# donnees du disque) aux numeros locaux 2F29, 2F2A, 2F2B (ombres ZERO, une seule couleur 14 sur fond 15) sont placees aux
# codes 50888, 50889, 5088A du coeur : par ECHANGE avec la tuile qui y est (contenu et tables), ou, si la ROM etendue est
# plus courte, en la prolongeant par des tuiles transparentes (la tuile d'origine reste en place, sans renvoi). Avec la
# ROM d'arcade, elles y sont deja : rien ne change. HSFA_OMBRE_CODES=0 : sortie d'avant a l'octet.
OMBRE_CODES = os.environ.get("HSFA_OMBRE_CODES", "1") != "0" and banques.MODULE == 'ro9'
OMBRES_COEUR = ((545, 0x2F29, 0x50888), (545, 0x2F2A, 0x50889), (545, 0x2F2B, 0x5088A))
CODE_MASQUE = 0x0FFFFFFF                             # bits 29-30 : drapeaux de miroir (SFA3 seul)

def ombres_aux_codes_du_coeur(blob, tables):
    """deplace les tuiles d'ombre ZERO d'Hyper aux codes du patch 0011 (blob et tables modifies en place)"""
    def tab(n):
        return next((t for p, t in tables.items() if os.path.basename(p) == "f%d.bin" % n), None)
    vide = encode(np.full((16, 16), 15, np.uint8))
    for n, local, cible in OMBRES_COEUR:
        t = tab(n)
        if t is None or local >= len(t) or t[local] == VIDE:
            print("ombres : f%d local $%x absent, rien a faire" % (n, local)); continue
        src = int(t[local]) & CODE_MASQUE
        if src < EXT0:
            print("ombres : f%d local $%x en ROM de base ($%x), rien a faire" % (n, local, src)); continue
        ks, kc = src - EXT0, cible - EXT0
        px = np.unpackbits(np.frombuffer(bytes(blob[128*ks:128*ks+128]), np.uint8).reshape(16, 2, 4, 1), axis=-1)
        px = (px.astype(np.uint8) << np.arange(4, dtype=np.uint8).reshape(1, 1, 4, 1)).sum(2).astype(np.uint8).reshape(16, 16)
        if set(np.unique(px).tolist()) != {14, 15}:
            print("!! ombres : f%d local $%x ($%x) n'est pas une ombre (couleurs %s), rien a faire"
                  % (n, local, src, sorted(set(np.unique(px).tolist())))); continue
        if src == cible: continue
        if kc * 128 < len(blob):                      # echange des deux tuiles, et des codes dans toutes les tables
            a, b = bytes(blob[128*ks:128*ks+128]), bytes(blob[128*kc:128*kc+128])
            blob[128*ks:128*ks+128], blob[128*kc:128*kc+128] = b, a
            for u in tables.values():
                c = u & CODE_MASQUE; ok = u != VIDE
                ma, mb = ok & (c == src), ok & (c == cible)
                u[ma] = (u[ma] & ~np.uint32(CODE_MASQUE)) | cible
                u[mb] = (u[mb] & ~np.uint32(CODE_MASQUE)) | src
            print("ombres : f%d local $%x : tuile $%x <-> $%x (code du coeur 0011)" % (n, local, src, cible))
        else:                                         # ROM etendue plus courte : prolongee par des tuiles transparentes
            a = bytes(blob[128*ks:128*ks+128])
            while len(blob) < 128 * kc: blob += vide
            blob += a
            for u in tables.values():
                c = u & CODE_MASQUE; ma = (u != VIDE) & (c == src)
                u[ma] = (u[ma] & ~np.uint32(CODE_MASQUE)) | cible
            print("ombres : f%d local $%x : tuile $%x -> $%x (ROM etendue prolongee, code du coeur 0011)" % (n, local, src, cible))

def main():
    if sys.argv[1:2] == ["--verif"]: verif(sys.argv[2]); return
    W = profils.P['travail']
    # tables etendues dans un dossier a part (les tables d'origine restent valables pour MAME stock)
    import shutil
    OUT = banques.OUT.rstrip('/') + '_hx'
    # (idempotence) <banques>_hx = copie FRAICHE de <banques> a chaque execution (carte.txt, plan1, f312... a jour si
    # banques.py a ete relance), sauf plan2.bin deja ecrite par hsfa_plans.py ; les tables f<N> sont recalculees ci-dessous
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(banques.OUT)):
        if f == "plan2.bin" and os.path.exists(os.path.join(OUT, f)): continue
        if os.path.isfile(os.path.join(banques.OUT, f)): shutil.copyfile(os.path.join(banques.OUT, f), os.path.join(OUT, f))
    noms = [int(a) for a in sys.argv[1:]] or banques.carte()
    idx = banques.index_rom()
    neuf = {}                                        # contenu -> code etendu
    blob = bytearray()
    tables = {}                                      # (ombre_iso) tables etendues, ecrites apres ombres_aux_codes_du_coeur
    base = os.environ.get("HSFA_GFX_BASE")           # (agent_ro9) ROM etendue existante (ex. celle d'Upper) reprise EN TETE :
    if base:                                         # ses tuiles gardent leurs codes, seules les absentes sont ajoutees apres
        b0 = open(base, "rb").read(); b0 = b0[:len(b0) // 128 * 128]
        a = np.unpackbits(np.frombuffer(b0, np.uint8).reshape(-1, 16, 2, 4, 1), axis=-1)   # (N, ligne, moitie, plan, pixel)
        px0 = (a.astype(np.uint8) << np.arange(4, dtype=np.uint8).reshape(1, 1, 1, 4, 1)).sum(3).astype(np.uint8).reshape(-1, 16, 16)
        for k in range(len(px0)): neuf.setdefault(px0[k].tobytes(), EXT0 + k)
        assert all(encode(px0[k]) == b0[128*k:128*k+128] for k in range(0, len(px0), 997)), "decodage de HSFA_GFX_BASE"
        blob += b0; n0 = len(px0)
        print("HSFA_GFX_BASE : %d tuiles reprises (codes $%x-$%x)" % (n0, EXT0, EXT0 + n0 - 1))
    for n in noms:
        src = os.path.join(banques.OUT, "f%d.bin" % n)          # table d'origine (banques.py), pas celle de _hx
        p = os.path.join(OUT, "f%d.bin" % n)
        if not os.path.exists(src): continue
        t = np.fromfile(src, '<u4').copy()
        buf = banques.fichier(n); ajout = 0
        for k, m, px in anthgfx.tiles(buf):
            if k != 1 or px is None or m >= len(t) or t[m] != VIDE: continue
            cle = px.astype(np.uint8).tobytes()
            if cle in idx: t[m] = idx[cle][0]; continue
            if not np.any(px): continue               # tuile vide : rien a afficher
            if cle not in neuf:
                neuf[cle] = EXT0 + len(blob) // 128; blob += encode(px)   # (= EXT0 + len(neuf) sans HSFA_GFX_BASE)
            t[m] = neuf[cle]; ajout += 1
        if ajout: print("f%d : %d tuiles vers la ROM etendue" % (n, ajout))
        tables[p] = t
    if OMBRE_CODES: ombres_aux_codes_du_coeur(blob, tables)
    for p, t in tables.items(): t.astype('<u4').tofile(p)
    if EXT_MAX is not None and EXT0 + len(blob) // 128 > EXT_MAX:
        raise SystemExit("ROM etendue SFA3 : %d tuiles depassent la zone $%x-$%x" % (len(blob) // 128, EXT0, EXT_MAX - 1))
    open(os.path.join(W, "hsfa_gfx.bin"), "wb").write(blob)
    if S3: tuiles_s3(W, OUT)                         # (sfa3_qsound, patch 0026) scroll3 32x32 du portage
    elif os.path.exists(os.path.join(W, "hsfa_gfx_s3.bin")): os.remove(os.path.join(W, "hsfa_gfx_s3.bin"))   # (relance)
    if EXT0 != 0x40000:                              # (sfa3_restes) decalage dans la region pour le banc / le paquet
        print("premier code $%x : HSFA_GFX=%s@%x (fork MAME), decalage $%x dans hsfa_gfx.bin du paquet FBNeo"
              % (EXT0, os.path.join(W, "hsfa_gfx.bin"), 0x2000000 + (EXT0 - 0x40000) * 128, (EXT0 - 0x40000) * 128))
    print("ROM etendue : %d tuiles uniques, %.2f Mo (place : %.0f Mo)" % (len(neuf), len(blob) / 2**20, 96))
    if len(blob) > 0x1000000: print("ATTENTION : plus de 16 Mo -> chevauche hsfa_plans.bin en $3000000 (deplacer les plans)")   # (agent_ro9)

if __name__ == "__main__":
    main()
