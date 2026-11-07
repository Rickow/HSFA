#!/usr/bin/env python3
"""Rendu des sequences MIDI de se_mid.pac (banque commune PSP) pour les codes $06, $0D, $2C.
Structure verifiee dans la section 0 (PPHD) : PPPG = 18 programmes de 1 ton, programme p -> ton p -> echantillon PPVA p
(I_ppp) ; tous les tons ont les memes reglages (volume $7F, ADSR1 $800F / ADSR2 $9FE0 : attaque immediate, maintien
plein, relachement le plus rapide). Echantillons sans boucle (drapeaux VAG 0/1/7).
Sequences (s05, s10, s37) : division 48, tempo 1 000 000 us/noire, programme P, note 60 vel 127 pendant 0x20 tics
(0,667 s), volume CC7 = 127. Rendu : I_P a sa hauteur d'origine (note 60 = note de reference : tous les bruitages
PSP sont ecrits sur cette note ; l'appariement cherche de toute facon la vitesse +-4 demi-tons), coupe a la fin de la
note (relachement immediat). Sorties : seq_XX.wav (22 050 Hz, 16 bits)."""
import os, sys, struct, wave
ICI = os.path.dirname(os.path.abspath(__file__))
SEQ = os.path.expanduser("~/.cache/sfa3max/converti/sons_communs/s%02d.mid")
INSTR = os.path.join(os.environ.get("SON_MAX_COMMUNS", "communs"), "psp", "I_%03d.wav")
CODES = {0x06: 5, 0x0D: 10, 0x2C: 37}            # code PSP -> sequence (table 43 de se_mid.pac, mot 2)


def lit_midi(f):
    d = open(f, "rb").read()
    assert d[:4] == b"MThd"
    div = struct.unpack_from(">H", d, 12)[0]
    o = 14; assert d[o:o + 4] == b"MTrk"
    n = struct.unpack_from(">I", d, o + 4)[0]; t = d[o + 8:o + 8 + n]
    i = 0; tic = 0; tempo = 500000; prog = None; notes = []; st = None; ouvertes = {}
    while i < len(t):
        v = 0
        while True:
            b = t[i]; i += 1; v = (v << 7) | (b & 0x7f)
            if b < 0x80: break
        tic += v
        b = t[i]
        if b == 0xFF:
            ty = t[i + 1]; ln = t[i + 2]
            if ty == 0x51: tempo = int.from_bytes(t[i + 3:i + 6], "big")
            i += 3 + ln; continue
        if b >= 0x80: st = b; i += 1
        k = st & 0xF0
        if k == 0xC0: prog = t[i]; i += 1
        elif k == 0xD0: i += 1
        elif k in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
            a, c = t[i], t[i + 1]; i += 2
            if k == 0x90 and c: ouvertes[a] = (tic, c)
            elif k in (0x80, 0x90) and a in ouvertes:
                t0, vel = ouvertes.pop(a); notes.append((t0, tic, a, vel))
    s = tempo / 1e6 / div
    return prog, [(t0 * s, t1 * s, a, vel) for t0, t1, a, vel in notes]


def rend(code):
    prog, notes = lit_midi(SEQ % CODES[code])
    w = wave.open(INSTR % prog); fr = w.getframerate()
    x = list(struct.unpack("<%dh" % w.getnframes(), w.readframes(w.getnframes())))
    assert len(notes) == 1 and notes[0][2] == 60, notes
    t0, t1, a, vel = notes[0]
    y = x[:int(round((t1 - t0) * fr))]
    f = os.path.join(os.environ.get("SON_MAX_SEQ", ICI), "seq_%02X.wav" % code)
    with wave.open(f, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(fr); o.writeframes(struct.pack("<%dh" % len(y), *y))
    return dict(code=code, sequence=CODES[code], programme=prog, instrument="I_%03d" % prog, note=a, vel=vel,
                duree_note=round(t1 - t0, 3), duree_instr=round(len(x) / fr, 3), duree_rendu=round(len(y) / fr, 3), wav=f)


if __name__ == "__main__":
    for c in CODES: print(rend(c))
