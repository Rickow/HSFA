#!/usr/bin/env python3
"""image programme 68K (gros-boutiste) reconstituee depuis un dossier roms*/sfa3ud ; image.py <dossier_rom> [sortie]"""
import os, sys, array
def image(d):
    names = [n for n in os.listdir(d) if not os.path.islink(os.path.join(d, n)) and n.split('.')[-1][:2] in ('03','04','05','06','07','08','09','10')]
    names = sorted(names, key=lambda n: int(n.split('.')[-1][:2]))
    b = b''.join(open(os.path.join(d, n), 'rb').read() for n in names); a = array.array('H', b); a.byteswap(); return a.tobytes()
if __name__ == "__main__":
    b = image(sys.argv[1])
    if len(sys.argv) > 2: open(sys.argv[2], 'wb').write(b)
    print(len(b))
