#!/usr/bin/env python3
"""Inventaire des 43 conteneurs plXX : types d'entrées, nombre de palettes, tuiles, volume CPS2."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import json
from plpac import split
from cmp_tiles import psp_tiles
names = json.load(open(paths.MAPPING))
print(f"{'fichier':<8}{'perso':<15}{'palettes':>9}{'tuiles':>8}{'uniques':>9}{'Mo CPS2':>9}{'entrée[0]':>11}")
for k, n in names.items():
    E = split(open(os.path.join(paths.pac_dir(), f"pl{k}_e.pac"), "rb").read())
    T = psp_tiles(f"pl{k}"); u = {t for t in T if any(t)}
    print(f"pl{k:<6}{n:<15}{len(E[2][1])//32:9}{len(T):8}{len(u):9}{len(u)*128/1048576:9.2f}{len(E[0][1]):11}")
