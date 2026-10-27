#!/usr/bin/env python3
"""Rendu hors ligne des musiques ZERO (SFA1) et ZERO 2 (SFA2) d'Hyper par leurs pilotes son d'origine
(docs/rapports/PLAN-PARTITIONS-HYPER.md, etape 1).

Chaine, par morceau :
  1. le pilote Z80 d'origine tourne au banc (mesure_boucles.Banc : 8 MHz, IRQ 250 Hz, poignee de main, commande) ;
     toutes ses ecritures vers le QSound (D000/D001 donnee, D002 registre) sont enregistrees au cycle pres ;
  2. rendu_qsound (hsfa_qsound.h, le QSound du coeur) les rejoue sur la ROM d'echantillons -> WAV 24 038 Hz.
Duree : 240 s par morceau (au moins deux passages de boucle).
Controle automatique (colonnes du tableau affiche) : crete, RMS, echantillons satures, secondes de silence ;
periode de la musique detectee dans l'audio (enveloppe), et repetition : correlation des spectrogrammes entre un passage
et le suivant, a la periode audio et a la boucle mesuree au banc (mesures_z80.tsv), avec un temoin decale de 13 s. Une
forme d'onde ne se repete pas a l'identique (la phase du pilote par rapport aux echantillons du QSound change d'une
boucle a l'autre) : on compare des spectrogrammes. La boucle du banc est fausse pour quelques morceaux (03, 04, 07, 08 ;
mesure_boucles prend la plus longue des boucles de piste) : la periode audio fait foi.

Donnees (aucune dans le depot) :
  --zip sfa.zip / sfa2.zip / ssf2t.zip   ROM arcade : programme .01/.02 et echantillons .11m/.12m (octets echanges)
  --z80 IMAGE --qs ROM                   ou images deja faites (X_DATA : e221 + e222 pour SFA1, e250 + e251 pour SFA2)
Usage : rendu_partitions.py sfa  --zip sfa.zip  [--codes 41-4d] [--sortie dossier]
        rendu_partitions.py sfa2 --zip sfa2.zip [--codes 51-63]
Dependances : paquet Python z80, g++ (rendu_qsound compile une fois dans le dossier de sortie).
"""
import argparse, os, struct, subprocess, sys, zipfile

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import mesure_boucles as MB                                   # noqa: E402
from pilote import Pilote                                     # noqa: E402

# code Hyper -> code du pilote (PLAN-SON-HYPER §1, etabli)
HYPER = {"sfa": {**{0x41 + k: 0x01 + k for k in range(12)}, 0x4D: 0x32},
         "sfa2": {**{0x51 + k: 0x01 + k for k in range(18)}, 0x63: 0x35}}
FAMILLE = {"sfa": "ZERO", "sfa2": "ZERO2", "ssf2t": "SSF2"}
ZIP = {"sfa": ("sfz.01", "sfz.02", "sfz.11m", "sfz.12m"), "sfa2": ("sz2.01a", "sz2.02a", "sz2.11m", "sz2.12m"),
       "ssf2t": ("sfx.01", "sfx.02", "sfx.11m", "sfx.12m")}


def depuis_zip(jeu, chemin, dossier):
    """image Z80 (region audiocpu MAME) et ROM QSound (octets de chaque mot echanges, comme MAME) depuis le zip"""
    p1, p2, q1, q2 = ZIP[jeu]
    with zipfile.ZipFile(chemin) as z:
        r1, r2, s1, s2 = (z.read(n) for n in (p1, p2, q1, q2))
    img = bytearray(0x50000)
    img[0:0x8000] = r1[:0x8000]; img[0x10000:0x10000 + len(r1) - 0x8000] = r1[0x8000:]
    img[0x28000:0x28000 + len(r2)] = r2
    qs = bytearray(s1 + s2); qs[0::2], qs[1::2] = qs[1::2], qs[0::2]
    z80, rom = os.path.join(dossier, jeu + "_z80.bin"), os.path.join(dossier, jeu + "_qs.bin")
    open(z80, "wb").write(img); open(rom, "wb").write(qs)
    return z80, rom


class Enregistreur(MB.Banc):
    """banc de mesure_boucles qui enregistre les ecritures QSound (cycle Z80, registre, valeur)"""
    def __init__(self, image):
        super().__init__(image)
        self.ecr = []; self.hi = self.lo = 0; self.cyc = 0; self.q = 0
        self.m.mark_addrs(0xD000, 8, self.m.READ_MARK | self.m.WRITE_MARK)

    def ecrit(self, a, v):
        if a == 0xD000: self.hi = v
        elif a == 0xD001: self.lo = v
        elif a == 0xD002:
            self.ecr.append((self.cyc + self.q - self.m.ticks_to_stop, v, (self.hi << 8) | self.lo))
        else: super().ecrit(a, v)

    def tourne(self, n_irq):
        m = self.m
        for _ in range(n_irq):
            reste, attente = MB.PAS, True
            while reste > 0:
                if attente and m.on_handle_active_int(): attente = False
                self.q = q = min(256 if attente else reste, reste)
                m.ticks_to_stop = q
                while True:
                    m.run()
                    if m.ticks_to_stop == 0: break
                reste -= q; self.cyc += q
            self.t += 1


def durees(jeu):
    """{code: (intro, boucle)} depuis mesures_z80.tsv"""
    out, actif = {}, None
    for l in open(os.path.join(ICI, "mesures_z80.tsv"), encoding="utf-8"):
        if l.startswith("# jeu="): actif = l[6:].split()[0]; continue
        c = l.rstrip("\n").split("\t")
        if actif == jeu and len(c) >= 5 and c[0] != "code" and c[3] != "-":
            out[int(c[0], 16)] = (float(c[2]), float(c[3]))
    return out


def controle(wav, intro, boucle):
    """(crete, rms, satures, silence_s, periode_audio_s, cor_audio, cor_mesure, cor_temoin)

    periode_audio : periode de l'enveloppe (~10 ms) entre 10 et 200 s, la plus courte a au moins 90 % du meilleur score
    (pour ne pas prendre un multiple). cor_* : correlation des spectrogrammes (50 Hz-4,7 kHz) entre un passage et le
    suivant, a la periode audio et a la boucle mesuree au banc, chacune affinee a +-30 ms ; temoin : decalage de 13 s.
    """
    import wave
    import numpy as np
    w = wave.open(wav); fr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2).astype(float)
    m = x.mean(1)
    sec = [np.sqrt((m[i * fr:(i + 1) * fr] ** 2).mean()) for i in range(len(m) // fr)]
    base = (int(abs(x).max()), float(np.sqrt((x ** 2).mean())), int((abs(x) >= 32767).sum()), sum(v < 20 for v in sec))
    h = fr // 100
    env = np.array([np.sqrt((m[i:i + h] ** 2).mean()) for i in range(0, len(m) - h, h)]); env -= env.mean()
    pas = h / fr                                  # duree d'une case d'enveloppe (240 / 24 038 = 9,98 ms)
    d0 = int((intro + 1) / pas); n = min(int(40 / pas), (len(env) - d0) // 2)
    a = env[d0:d0 + n]
    sc = []
    for k in range(int(10 / pas), min(int(200 / pas), len(env) - d0 - n)):
        b = env[d0 + k:d0 + k + n]
        sc.append((float(np.dot(a, b) / (np.sqrt(np.dot(a, a) * np.dot(b, b)) + 1e-9)), k))
    if not sc: return base + (None, None, None, None)
    top = max(r for r, k in sc)
    per = min(k for r, k in sc if r >= 0.90 * top) * pas
    def sp(s):
        f = np.array([np.abs(np.fft.rfft(s[i:i + 1024] * np.hanning(1024))) for i in range(0, len(s) - 1024, 512)])
        return np.log1p(f[:, 2:200]).ravel()
    s0, ns = int((intro + 1) * fr), int(min(40.0, n * pas) * fr)
    A = sp(m[s0:s0 + ns])
    def cor(p):
        if p is None or s0 + int((p + .05) * fr) + ns > len(m): return None
        lag = max(range(int((p - .03) * fr), int((p + .03) * fr), 4), key=lambda k: np.dot(m[s0:s0 + ns:8], m[s0 + k:s0 + k + ns:8]))
        return float(np.corrcoef(A, sp(m[s0 + lag:s0 + lag + ns]))[0, 1])
    return base + (per, cor(per), cor(boucle), cor(13.0))


def rend(jeu, z80, rom, code, secondes, sortie, outil):
    if secondes > 500: raise ValueError("500 s au plus (instants sur 32 bits en cycles a 8 MHz)")
    b = Enregistreur(open(z80, "rb").read())
    mem = b.m.memory
    b.tourne(MB.HZ_IRQ // 10)
    mem[0xCFFD] = 0x88; mem[0xCFFF] = 0xFF; mem[0xC00F] = 0xFF
    b.tourne(MB.HZ_IRQ)                                       # initialisation du pilote, ecritures QSound comprises
    t0 = b.cyc
    mem[0xC000] = code >> 8; mem[0xC001] = code & 0xFF; mem[0xC00F] = 0
    b.tourne(int(secondes * MB.HZ_IRQ))
    ecr = os.path.join(os.path.dirname(sortie), "ecritures.bin")
    with open(ecr, "wb") as f:                                # temps ramenes au depart de la commande ; init a t = 0
        for c, r, v in b.ecr:
            f.write(struct.pack("<IBBH", max(0, c - t0), r, 0, v))
    r = subprocess.run([outil, rom, ecr, "%.3f" % secondes, sortie], capture_output=True, text=True, check=True)
    os.remove(ecr)
    return len(b.ecr), r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jeu", choices=sorted(ZIP)); ap.add_argument("--zip"); ap.add_argument("--z80"); ap.add_argument("--qs")
    ap.add_argument("--codes", help="codes Hyper (hexa, ex. 41-4d) ou, pour ssf2t, codes du pilote")
    ap.add_argument("--sortie", default="rendu_partitions")
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    if a.zip: z80, rom = depuis_zip(a.jeu, a.zip, a.sortie)
    elif a.z80 and a.qs: z80, rom = a.z80, a.qs
    else: sys.exit("--zip, ou --z80 et --qs")
    outil = os.path.join(a.sortie, "rendu_qsound")
    subprocess.run(["g++", "-O2", "-I", ICI, "-o", outil, os.path.join(ICI, "rendu_qsound.cpp")], check=True)
    table = HYPER.get(a.jeu) or {}
    if a.codes:
        sel = [int(x, 16) for p in a.codes.split(",") for x in
               ([p] if "-" not in p else ["%x" % i for i in range(int(p.split("-")[0], 16), int(p.split("-")[1], 16) + 1)])]
    else:
        sel = sorted(table)
    du = durees(a.jeu)
    print("code_hyper\tcode_pilote\tduree_s\tecritures\tcrete\trms\tsatures\tsilence_s\tboucle_banc_s\tperiode_audio_s"
          "\tcor_audio\tcor_banc\tcor_temoin\tfichier")
    f3 = lambda v: "-" if v is None else "%.3f" % v
    for h in sel:
        c = table.get(h, h)
        intro, boucle = du.get(c, (0.0, None))
        s = 240.0                                     # assez pour 2 passages, meme si la boucle mesuree est fausse
        nom = os.path.join(a.sortie, "%s_%04X_%s_%02X.wav" % (FAMILLE[a.jeu], h, a.jeu, c))
        n, msg = rend(a.jeu, z80, rom, c, s, nom, outil)
        k = controle(nom, intro, boucle)
        print("%04X\t%02X\t%.1f\t%d\t%d\t%.0f\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s" % ((h, c, s, n) + k[:4] + (
              f3(boucle), f3(k[4]), f3(k[5]), f3(k[6]), f3(k[7]), os.path.basename(nom))), flush=True)


if __name__ == "__main__":
    main()
