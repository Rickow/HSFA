# (decors_proto E1, work/decors_proto/CONCEPTION.md §4 "E1") DECORS_LOTS=1 : the SFA1 / SFA2 stage data are SERVED by the
# graft, nothing reads them yet. Called by etape3/greffe3.py (lines under `if DECORS_LOTS:`), no game data here : the
# lots and the tiles are made from the player's ISO by the stage converters (DECORS_DONNEES = folder of 6 files :
# <game>_lot.bin, <game>_obj.bin, <game>_plans.bin for sfa1 and sfa2).
#   - pose()        : stage zone body (68K $4E8000-$5D3FFF, tagged $01) = lot 1 (Upper stage objects, unchanged) + zeros
#                     + SFA1 lot at $537300 + zeros + SFA2 lot at $552000 ; directory lots + index $100 / 2 -> lot ;
#   - prolonge_e0() : slot 0 tables f545.bin AND f351.bin extended with the local OBJ codes of the lots ($8000-$9F6F SFA2,
#                     $A000-$A32F SFA1 -> global tiles); called AFTER max_banques (fait_gfx_max.py needs its MAX codes
#                     $7000+ to be beyond the length of f545 when it starts) ;
#   - tuiles()      : the 4 tile files copied to <construction>/decors_gfx/ with plan.tsv (name, address, size, md5),
#                     read by paquet/paquet_fbneo.py (hsfa_gfx.bin) and by the test benches (HSFA_GFX).
# The 8 program ROMs do not change (proof : work/decors_proto, E1 proofs 1.1 / 1.2 / 1.6).
import os, struct, hashlib, shutil

TAG = 0x01000000
CORPS = (0x4E8000, 0x5D4000)                         # = greffe3.ZONE_CORPS
# game, family, base (68K), budget end (excluded), first $100 of the game's stages, first local OBJ code (slot 0)
LOTS = (("sfa1", 4, 0x537300, 0x552000, 0xA0, 0xA000),
        ("sfa2", 3, 0x552000, 0x5D4000, 0x50, 0x8000))
# tile files : (name, graphics address, end of the reserved range, excluded) ; hsfa_gfx.bin = $2000000-$4FFFFFF
TUILES = (("sfa2_plans.bin", 0x2850000, 0x2B50000), ("sfa2_obj.bin", 0x2B50000, 0x2C50000),
          ("sfa1_plans.bin", 0x4C40000, 0x4D50000), ("sfa1_obj.bin", 0x4D50000, 0x4D70000))
OBJ_ADR = {"sfa1": 0x4D50000, "sfa2": 0x2B50000}     # graphics address of <game>_obj.bin (local code c0 + j -> tile adr / 128 + j)
E0_PLAGE = (0x8000, 0xC000)                          # slot 0 codes kept for the imported stages (re/allocations.tsv) ; MAX : $7000-$7FFF, $C000+
T = 128                                              # one 16 x 16 tile, MAME internal format
MAGIE, VERSION = b'HSFADC01', 2

def _lit(p):
    with open(p, 'rb') as f: return f.read()

def charge(dossier):
    """reads and checks the 6 files ; returns {game: dict(lot, obj, plans, ...)} (stops on any mismatch)"""
    assert os.path.isdir(dossier), "DECORS_DONNEES : %s is not a folder" % dossier
    D = {}
    for jeu, fam, base, budget, p100, code0 in LOTS:
        L = _lit(os.path.join(dossier, jeu + "_lot.bin")); o = _lit(os.path.join(dossier, jeu + "_obj.bin"))
        p = _lit(os.path.join(dossier, jeu + "_plans.bin"))
        assert L[:8] == MAGIE, "%s_lot.bin : magic %r" % (jeu, L[:8])
        ver, fam_, nb = struct.unpack_from('<HHH', L, 8)
        fin, obj, _a1, _a2, _a3, biais = struct.unpack_from('<IIHHHH', L, 16)
        assert ver == VERSION and fam_ == fam, "%s_lot.bin : version %d family %d (expected %d, %d)" % (jeu, ver, fam_, VERSION, fam)
        assert biais == p100, "%s_lot.bin : bias $%X (expected $%X)" % (jeu, biais, p100)
        assert obj == code0, "%s_lot.bin : first OBJ code $%X (expected $%X)" % (jeu, obj, code0)
        assert len(L) % 16 == 0 and base + len(L) <= budget, "%s_lot.bin : %d bytes, out of budget $%06X-$%06X" % (jeu, len(L), base, budget - 1)
        assert fin == TAG | (base + len(L)), "%s_lot.bin : end pointer $%08X : lot not made for base $%06X" % (jeu, fin, base)
        assert 0 < nb and p100 + 2 * nb <= 0x100, "%s_lot.bin : %d stages" % (jeu, nb)
        g = dict((n, (a, e)) for n, a, e in TUILES)
        assert len(o) % (16 * T) == 0 and OBJ_ADR[jeu] + len(o) <= g[jeu + "_obj.bin"][1], "%s_obj.bin : %d bytes" % (jeu, len(o))
        assert code0 + len(o) // T <= E0_PLAGE[1] and E0_PLAGE[0] <= code0, "%s_obj.bin : codes beyond $%04X" % (jeu, E0_PLAGE[1] - 1)
        assert len(p) % T == 0 and g[jeu + "_plans.bin"][0] + len(p) <= g[jeu + "_plans.bin"][1], "%s_plans.bin : %d bytes" % (jeu, len(p))
        D[jeu] = dict(fam=fam, base=base, p100=p100, nb=nb, code0=code0, lot=L, obj=o, plans=p, md5=hashlib.md5(L).hexdigest())
    return D

def pose(D, zbuf):
    """zone body + lots : returns (new body, directory lots [(family, flags, tagged base, size, origin)], index
    {$100 / 2: tagged base of the lot}) ; lots in address order, zeros in between"""
    z = bytearray(zbuf); lots, index = [], {}
    for jeu, fam, base, budget, p100, code0 in sorted(LOTS, key=lambda l_: l_[2]):
        d = D[jeu]
        assert CORPS[0] + len(z) <= base, "stage zone already used up to $%06X (lot %s at $%06X)" % (CORPS[0] + len(z), jeu, base)
        z += bytes(base - CORPS[0] - len(z)); z += d['lot']
        lots.append((fam, 0, TAG | base, len(d['lot']), 0))
        for k in range(d['nb']): index[(p100 >> 1) + k] = TAG | base
    assert CORPS[0] + len(z) <= CORPS[1], "stage zone full"
    return bytes(z), lots, index

def prolonge_e0(D, dossier):
    """f545.bin and f351.bin of banques_hx : local OBJ codes of the lots -> global tiles ; holes $FFFFFFFF ; the entries
    already there are kept ; the file is removed then rewritten (never write through a link)"""
    res = {}
    for n in ("f545", "f351"):
        f = os.path.join(dossier, n + ".bin"); d = _lit(f)
        V = list(struct.unpack('<%dI' % (len(d) // 4), d)); n0 = len(V)
        pris = [i for i in range(E0_PLAGE[0], min(E0_PLAGE[1], n0)) if V[i] != 0xFFFFFFFF]
        assert not pris, "%s.bin : %d codes already used in $%04X-$%04X (first $%04X)" % (n, len(pris), E0_PLAGE[0], E0_PLAGE[1] - 1, pris[0])
        for jeu in sorted(D, key=lambda j_: D[j_]['code0']):
            c0 = D[jeu]['code0']; k = len(D[jeu]['obj']) // T
            if len(V) < c0 + k: V += [0xFFFFFFFF] * (c0 + k - len(V))
            for j in range(k): V[c0 + j] = OBJ_ADR[jeu] // T + j
        b = struct.pack('<%dI' % len(V), *V); assert b[:len(d)] == d or n0 > E0_PLAGE[0]
        if os.path.lexists(f): os.remove(f)
        with open(f, 'wb') as w: w.write(b)
        res[n] = (n0, len(V))
    return res

def tuiles(D, construction):
    """<construction>/decors_gfx/ : copies of the 4 tile files + plan.tsv (name, graphics address, size, md5)"""
    S = os.path.join(construction, "decors_gfx")
    if os.path.isdir(S): shutil.rmtree(S)
    os.makedirs(S)
    lignes = ["# name\taddress\tsize\tmd5 (E1 : slot 0 objects and planes of the SFA1 / SFA2 stages, hsfa_gfx.bin)"]
    for nom, adr, fin in TUILES:
        jeu, quoi = nom[:-4].split("_")
        d = D[jeu]['obj' if quoi == 'obj' else 'plans']; assert adr + len(d) <= fin
        with open(os.path.join(S, nom), 'wb') as w: w.write(d)
        lignes.append("%s\t%07X\t%d\t%s" % (nom, adr, len(d), hashlib.md5(d).hexdigest()))
    with open(os.path.join(S, "plan.tsv"), 'w', encoding='utf-8', newline='\n') as w: w.write("\n".join(lignes) + "\n")
    return S
