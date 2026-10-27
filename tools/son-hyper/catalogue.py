#!<workspace>/venv/bin/python
"""Catalogue des commandes d'un jeu a partir du balayage (journaux/bal_<jeu>.txt) et de l'image QSound :
pour chaque commande, les notes (voie, echantillon, hauteur) ; classement « simple » (une seule note, ou la meme
note repetee sur une voie = un echantillon transplantable tel quel) / « sequence » (plusieurs echantillons, hauteurs
ou voies) ; extraction des echantillons distincts en WAV (8 bits signes -> 16 bits, a leur frequence de lecture).
Usage : catalogue.py <jeu> (sfa1|sfa2|ro6|sfa3)  -> catalogue/<jeu>.json, wav/<jeu>/ech_<banque><debut>.wav"""
import sys, os, json, wave, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notes import notes
D = "<workspace>/work/agent_son_hyper_rom"
QS_HZ = 60e6 / 2 / 1248

def image_qs(jeu):
    if jeu == "sfa3":
        q = bytearray()
        for n in ("hx3.11m", "hx3.12m", "hx3.13m", "hx3.14m"):
            b = open("<workspace>/work/agent_voix_max/roms_voix/" + n, "rb").read()
            s = bytearray(len(b)); s[0::2] = b[1::2]; s[1::2] = b[0::2]; q += s
        return bytes(q)
    return open(os.path.join(D, "src", jeu + "_qs.bin"), "rb").read()

def pcm(q, banque, debut, fin):
    base = (banque & 0xff) << 16
    if base >= len(q): return np.zeros(0, np.int8)
    if fin >= debut: b = q[base + debut: base + fin + 1]
    else: b = q[base + debut: base + 0x10000] + q[base: base + fin + 1]
    return np.frombuffer(bytes(b), np.int8)

def ecrit_wav(f, x8, hz):
    w = wave.open(f, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(int(round(hz)))
    w.writeframes((x8.astype(np.int16) * 256).astype("<i2").tobytes()); w.close()

def main(jeu):
    q = image_qs(jeu)
    N = notes(os.path.join(D, "journaux", "bal_%s.txt" % jeu))
    ech, cmds = {}, {}
    os.makedirs(os.path.join(D, "wav", jeu), exist_ok=True)
    for c, L in sorted(N.items()):
        cles = []
        for n in L:
            k = "%02x%04x" % (n["banque"] & 0xff, n["debut"])
            if k not in ech:
                x = pcm(q, n["banque"], n["debut"], n["fin"])
                ech[k] = dict(banque=n["banque"] & 0xff, debut=n["debut"], fin=n["fin"], boucle=n["boucle"], octets=len(x),
                              hauteurs=[], cmds=[])
            e = ech[k]
            if n["hauteur"] not in e["hauteurs"]: e["hauteurs"].append(n["hauteur"])
            if c not in e["cmds"]: e["cmds"].append(c)
            cles.append((k, n["hauteur"], n["v"]))
        distinct = sorted(set(cles))
        voies = sorted(set(v for _, _, v in cles))
        if not cles: genre = "muet"
        elif len(distinct) == 1: genre = "simple"
        elif len(set(k for k, _, _ in cles)) == 1 and len(voies) == 1: genre = "simple_hauteurs"
        else: genre = "sequence"
        cmds[c] = dict(genre=genre, notes=len(cles), echantillons=sorted(set(k for k, _, _ in cles)), voies=voies,
                       hauteur=cles[0][1] if cles else 0, t0=L[0]["t"] if L else None)
    for k, e in ech.items():
        h = e["hauteurs"][0] if e["hauteurs"] else 0x1000
        e["hz"] = round(QS_HZ * h / 4096, 1) if h else 0
        e["duree"] = round(e["octets"] / e["hz"], 3) if e["hz"] else 0
        e["boucle_reelle"] = e["boucle"] > 0x20 and e["boucle"] < e["octets"] - 4      # vraie boucle (pas 1 octet nul)
        if e["hz"]: ecrit_wav(os.path.join(D, "wav", jeu, "ech_%s.wav" % k), pcm(q, e["banque"], e["debut"], e["fin"]), e["hz"])
    os.makedirs(os.path.join(D, "catalogue"), exist_ok=True)
    json.dump(dict(commandes={"%04x" % c: v for c, v in cmds.items()}, echantillons=ech),
              open(os.path.join(D, "catalogue", jeu + ".json"), "w"), indent=0)
    from collections import Counter
    print(jeu, len(cmds), "commandes", Counter(v["genre"] for v in cmds.values()), len(ech), "echantillons")

if __name__ == "__main__":
    main(sys.argv[1])
