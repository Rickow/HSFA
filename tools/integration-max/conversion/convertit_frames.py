#!/usr/bin/env python3
"""Blocs externes des persos MAX (session MAX, disposition ARCADE) -> disposition de l'image Upper, un binaire par bloc
externe du fork : ext_d40000.bin couvre $D40000-$D7FFFF (Eagle), ext_d80000.bin Maki, ext_dc0000.bin Yun,
ext_e00000.bin Ingrid. Chaque bloc fusionne, dans UN assemblage vasm (chaque fichier garde son org ; vasm comble les
trous de zéros et REFUSE tout chevauchement de sections) :

  frames_<p>.s      org +$00000  frames (mots) + « dc.l POSxx_n »
  anims_<p>.s       org +$20000  ANIM_xx ($2B0), ANIM_xx_2B4/_2B8/_2BC (mots relatifs), ANIM_xx_PTRS (12 longs, gabarit
                                 de $DD412 : 3 ismes × {$2B0,$2B8,$2B4,$2BC}), pas P<xx>_n de 20 o (+ reprise en +$14)
  fin_anims_<p>.s   org +$30000  FIN_ANIM_xx (banque d'acteurs de fin : mots relatifs) + pas FP<xx>_n

Règles (toutes mesurées dans l'image d'Upper, voir CONV-MAX.md §9) :
  * frames : mot = même adresse, inchangé ; long = moitiés échangées (« dc.l X » -> « dc.w X&$FFFF, X>>16 »).
  * tables de mots relatifs (ANIM_xx*, FIN_ANIM_xx) : mots NATIFS (image $AFA58 = arcade $1B6E0 : MOVE.W 0(A0,D0.W),D0 ;
    ADDA.W D0,A0 ; table $2B0 de Ryu dans l'image en $2319C0 : mêmes écarts que l'arcade $146218).
  * ANIM_xx_PTRS : longs à moitiés échangées (Ryu : image $2319A0 « B680 0079 » = PS2 $0079B680).
  * pas de 20 o : convertit_max.permute_bloc('pas') = règle de tables_explicites (octets $0-$3/$8-$13 échangés par mot,
    long $4 = frame SWAP, reprise $14 SWAP si bit 7 de l'octet $1) ; « dcb.b n,v » est développé.
Contrôles : taille <= $40000, aucun chevauchement (vasm), symboles assemblés = symboles_frames_max.s et
symboles_anims_max.s de la session MAX (le code MAX et les tables d'Upper emploient ces valeurs).
Usage : convertit_frames.py [dossier rosette_code] ; sorties dans sortie/."""
import os, re, sys, subprocess, hashlib

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import convertit_max as C

ROS = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/CLAUDE CODE/sfa3max-psp-widescreen/work/re/rosette_code")
SORTIE = os.environ.get("CONV_SORTIE") or os.path.join(ICI, "sortie")   # (agent_integration_max)
VASM = os.path.expanduser("~/outils/vasm/vasmm68k_mot")
PERSOS = [("eagle", 0x26, int(os.environ.get("BLOC_EAGLE", "D40000"), 16)),   # (agent_integration_max) bloc d'Eagle déplaçable
           ("maki", 0x27, 0xD80000), ("yun", 0x28, 0xDC0000), ("ingrid", 0x29, 0xE00000)]
TAILLE_BLOC = 0x40000
RX_DCL = re.compile(r'^(\s*)dc\.l\s+([^;]+?)\s*(;.*)?$', re.I)

# --------------------------------------------------------------------------------------------- frames
def convertit_frames(src, dst):
    n = 0
    with open(src) as f, open(dst, "w") as o:
        o.write("; CONVERTI par convertit_frames.py (disposition de l'image Upper : longs a moities echangees)\n")
        for l in f:
            m = RX_DCL.match(l.rstrip("\n"))
            if m:
                ind, vals, com = m.group(1), [v.strip() for v in m.group(2).split(",")], m.group(3) or ""
                mots = ", ".join("(%s)&$FFFF, ((%s)>>16)&$FFFF" % (v, v) for v in vals)
                o.write("%sdc.w    %s  ; dc.l %s (moities echangees)%s\n" % (ind, mots, m.group(2).strip(), " " + com if com else ""))
                n += len(vals)
            else:
                o.write(l)
    return n

# --------------------------------------------------------------------------------------------- décors de fin
RX_DCB4 = re.compile(r'^(\s*)dc\.b\s+([^,;]+),\s*([^,;]+),\s*([^,;]+),\s*([^,;]+?)\s*(;.*)?$', re.I)
def convertit_decor(src, dst):
    """(agent_integration_max, palier 4) decor_fin_<p>.s (session MAX, org +$38000, disposition ARCADE) -> image Upper :
    frames FD.. et listes de positions comme frames_<p>.s (longs à moitiés échangées) ; table FIN118_xx (mots relatifs)
    inchangée ; pas de 8 o (« dc.b d, f, x, y » + dc.l frame [+ dc.l reprise]) : octets échangés par paire (XOR 1)"""
    # (18/10 nuit, session MAX) UN fichier d'emplacement 4 par fin : table du modèle (N entrées) PUIS tuiles des FD ->
    # codes des FD décalés de N (DECOR_BASE="eagle:N,…") ; entrées des frames FD = lignes « dc.w code, attr » après
    # l'en-tête (4 mots) et le « dc.l PFD.. » d'une étiquette FDxx_n
    base = dict((k, int(v)) for k, v in (x.split(":") for x in os.environ.get("DECOR_BASE", "").split(",") if x)).get(
        re.sub(r"^decor_fin_|\.s$", "", os.path.basename(src)), 0)
    if base:
        L = open(src).read().split("\n"); dans = False; vu = 0
        for i, l in enumerate(L):
            if re.match(r"^FD[0-9A-Fa-f]{2}_\d+:", l): dans = True; continue
            if re.match(r"^\w+:", l): dans = False; continue
            m = re.match(r"^(\s+dc\.w\s+)\$([0-9a-fA-F]+),\s*(\$[0-9a-fA-F]+)\s*(;.*)?$", l)
            if dans and m:
                L[i] = "%s$%04x, %s  ; (agent_integration_max) code FD + %d (table du modèle)" % (m.group(1), int(m.group(2), 16) + base, m.group(3), base)
                vu += 1
        src2 = dst + ".src"; open(src2, "w").write("\n".join(L)); src = src2
        print("décor %s : %d entrées de frames FD décalées de %d" % (os.path.basename(dst), vu, base))
    tmp = dst + ".tmp"; n = convertit_frames(src, tmp); nb = 0
    with open(tmp) as f, open(dst, "w") as o:
        for l in f:
            m = RX_DCB4.match(l.rstrip("\n"))
            if m:
                ind, v = m.group(1), [m.group(k).strip() for k in range(2, 6)]
                o.write("%sdc.b    %s, %s, %s, %s  ; (octets échangés par paire)%s\n" % (ind, v[1], v[0], v[3], v[2], " " + m.group(6) if m.group(6) else ""))
                nb += 1
            else: o.write(l)
    os.remove(tmp)
    return n, nb

# --------------------------------------------------------------------------------------------- animations
def genre_anim(lab):
    if lab is None: return None
    if re.fullmatch(r'(FIN_)?ANIM_[0-9A-Fa-f]{2}(_2B[048C])?', lab): return 'mots'        # tables de mots relatifs
    if re.fullmatch(r'ANIM_[0-9A-Fa-f]{2}_PTRS', lab): return 'longs'                    # gabarit $DD412
    if re.fullmatch(r'F?P[0-9A-Fa-f]{2}_\w+', lab): return 'pas'                         # pas de 20 o
    return '?'

def convertit_anims(src, dst, journal):
    nom = os.path.basename(src)
    lignes = open(src).read().split('\n')
    if lignes and lignes[-1] == '': lignes.pop()
    blocs = []; cur = [None, [], 1]
    for k, l in enumerate(lignes, 1):
        ins, _ = C.analyse_ligne(nom, k, l, '')
        if ins.labels and not ins.equ:
            blocs.append(cur); cur = [ins.labels[0], [l], k]
        else:
            cur[1].append(l)
    blocs.append(cur)
    out = ["; CONVERTI par convertit_frames.py (disposition de l'image Upper ; source : %s, disposition arcade)" % nom]
    st = {'mots': 0, 'longs': 0, 'pas': 0, 'NON RÉSOLU': 0}
    def nr(k0, raison, L):
        journal.append((nom, k0, 'NON RÉSOLU', raison)); st['NON RÉSOLU'] += 1
        out.extend(x + '  ; ⚠ CONV NON RÉSOLU : ' + raison if j == 0 else x for j, x in enumerate(L))
    for lab, L, k0 in blocs:
        g = genre_anim(lab)
        if g is None:
            out.extend(L); continue
        if g == '?':
            nr(k0, 'étiquette de genre inconnu %s' % lab, L); continue
        elems = []; ok = True
        for j, l in enumerate(L):
            ins, _ = C.analyse_ligne(nom, k0 + j, l, '')
            if ins.mn is None: continue
            if ins.mn == 'dc' and isinstance(ins.sz, int):
                for t in C.split_ops(ins.ops[0]): elems.append((ins.sz, t, ins.com, k0 + j))
            elif ins.mn == 'dcb' and ins.sz == 1:
                p = C.split_ops(ins.ops[0]); n = C.num(p[0]); v = p[1] if len(p) > 1 else '0'
                if n is None: ok = False; break
                elems += [(1, v, '', k0 + j)] * n
            else:
                ok = False; break
        if not ok:
            nr(k0, 'directive inattendue dans %s' % lab, L); continue
        if g == 'mots':
            if any(t != 2 for t, *_ in elems): nr(k0, '%s : élément non mot' % lab, L); continue
            out.extend(L); st['mots'] += len(elems)           # mots natifs : recopiés tels quels
            continue
        if g == 'longs':
            if any(t != 4 for t, *_ in elems): nr(k0, '%s : élément non long' % lab, L); continue
            out.append(L[0] + '   ; conv : longs a moities echangees (gabarit $DD412)')
            out.extend('        dc.l    %s' % C.perm_expr(t, 'swap') for _, t, _, _ in elems)
            st['longs'] += len(elems); continue
        try:
            nouv = C.Convertisseur.permute_bloc(None, 'pas', elems)
        except C.NonResolu as e:
            nr(k0, '%s : %s' % (lab, e), L); continue
        out.append(L[0] + '   ; conv : format PS2 (pas)')
        out.extend(nouv); st['pas'] += 1
    open(dst, 'w').write('\n'.join(out) + '\n')
    return st

# --------------------------------------------------------------------------------------------- symboles
def lit_equ(f):
    d = {}
    if not os.path.exists(f): return d
    for l in open(f):
        m = re.match(r'^\s*([A-Za-z_]\w*)\s+equ\s+\$([0-9A-Fa-f]+)', l)
        if m: d[m.group(1)] = int(m.group(2), 16)
    return d

def lit_liste(f):
    d = {}; dans = False
    for l in open(f, errors='replace'):
        if l.startswith('Symbols by name'): dans = True; continue
        if l.startswith('Symbols by value'): break
        if dans:
            m = re.match(r'^(\S+)\s+A:([0-9A-Fa-f]{8})', l)
            if m: d[m.group(1)] = int(m.group(2), 16)
    return d

def main():
    os.makedirs(SORTIE, exist_ok=True)
    attendus = lit_equ(os.path.join(ROS, 'symboles_frames_max.s'))
    attendus.update(lit_equ(os.path.join(ROS, 'symboles_anims_max.s')))
    journal = []; erreur = False
    for nom, nn, org in PERSOS:
        parts = []
        src = os.path.join(ROS, "frames_%s.s" % nom)
        if not os.path.exists(src):
            print("absent : %s" % src); continue
        dst = os.path.join(SORTIE, "frames_%s_upper.s" % nom)
        nl = convertit_frames(src, dst); parts.append(dst)
        res = []
        for pre in ('anims', 'fin_anims'):
            s2 = os.path.join(ROS, "%s_%s.s" % (pre, nom))
            if not os.path.exists(s2): res.append('%s absent' % pre); continue
            d2 = os.path.join(SORTIE, "%s_%s_upper.s" % (pre, nom))
            st = convertit_anims(s2, d2, journal); parts.append(d2)
            res.append('%s %d mots / %d longs / %d blocs de pas%s' % (pre, st['mots'], st['longs'], st['pas'],
                       (' / %d NON RÉSOLU' % st['NON RÉSOLU']) if st['NON RÉSOLU'] else ''))
            erreur |= st['NON RÉSOLU'] > 0
        s3 = os.path.join(ROS, "decor_fin_%s.s" % nom)            # (agent_integration_max, palier 4) décors de fin
        if os.path.exists(s3) and os.environ.get("MAX_DECORS", os.environ.get("MAX_P4", "1")) == "1":
            d3 = os.path.join(SORTIE, "decor_fin_%s_upper.s" % nom)
            nl3, nb3 = convertit_decor(s3, d3); parts.append(d3)
            res.append('décor de fin %d longs / %d pas' % (nl3, nb3))
        bloc = os.path.join(SORTIE, "bloc_%06x.s" % org)
        with open(bloc, 'w') as o:
            o.write('; bloc externe $%06X-$%06X (%s) : assemblage unique, chaque partie à son org\n' % (org, org + TAILLE_BLOC - 1, nom))
            for p in parts: o.write(open(p).read())
        binf = os.path.join(SORTIE, "ext_%06x.bin" % org); lst = os.path.join(SORTIE, "bloc_%06x.lst" % org)
        r = subprocess.run([VASM, "-m68000", "-spaces", "-Fbin", "-quiet", "-L", lst, "-o", binf, bloc], capture_output=True, text=True)
        if r.returncode != 0:
            print("%s : ERREUR vasm (chevauchement ou symbole manquant)\n%s" % (nom, (r.stdout + r.stderr)[-3000:])); sys.exit(1)
        t = os.path.getsize(binf)
        syms = lit_liste(lst)
        bas = min(syms.values()) if syms else org
        if t > TAILLE_BLOC or bas != org or bas + t > org + TAILLE_BLOC:
            print("%s : binaire $%06X + %d octets hors du bloc $%06X-$%06X" % (nom, bas, t, org, org + TAILLE_BLOC - 1)); sys.exit(1)
        # contrôle des symboles publiés par la session MAX (le code MAX et les tables d'Upper emploient ces valeurs)
        pre = '%02X' % nn
        diff = [(k, hex(v), hex(syms[k])) for k, v in attendus.items() if k in syms and syms[k] != v]
        manq = [k for k in attendus if re.match(r'(F|ANIM_|FIN_ANIM_)%s(_|$)' % pre, k) and k not in syms]
        if diff or manq:
            print("%s : symboles différents de symboles_*_max.s : %s ; absents : %s" % (nom, diff[:5], manq[:5])); sys.exit(1)
        nsym = sum(1 for k in attendus if k in syms)
        print("%-7s $%06X : %d o (%.0f %%), md5 %s ; frames %d longs ; %s ; %d symboles conformes" % (
            nom, org, t, 100.0 * t / TAILLE_BLOC, hashlib.md5(open(binf, "rb").read()).hexdigest()[:12], nl,
            ' ; '.join(res), nsym))
    with open(os.path.join(SORTIE, 'journal_blocs.tsv'), 'w') as f:
        f.write('fichier\tligne\tstatut\traison\n')
        for j in journal: f.write('\t'.join(str(x) for x in j) + '\n')
    if journal:
        print('NON RÉSOLU dans les blocs externes : %d (sortie/journal_blocs.tsv)' % len(journal))
    sys.exit(1 if erreur else 0)

if __name__ == "__main__":
    main()
