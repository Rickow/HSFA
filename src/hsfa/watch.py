#!/usr/bin/env python3
"""POINT D'OBSERVATION MAME (HANDOFF §63) : liste les ecritures a une adresse (image, PC 68K -> va MIPS +
mnemonique traduit, valeur ecrite). Usage : watch.py ADRESSE_HEX [taille=2] [images=200] [max_lignes=40]"""
import sys, os, subprocess, re, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import carte, lookup, W

LUA = r'''
dofile("<workspace>/work/mame/banc_mem.lua")
local frames = 0
local started = false
emu.register_frame_done(function()
  frames = frames + 1
  if not started then
    manager.machine.debugger:command('wpset %(a)x,%(sz)d,w,1,{logerror "WP image=%%d pc=%%x val=%%x\\n",frame,pc,wpdata;g}')
    manager.machine.debugger:command("go")
    started = true
  end
  if frames >= %(nf)d then manager.machine:exit() end
end)
'''

def main():
    a = int(sys.argv[1], 16); sz = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    nf = int(sys.argv[3]) if len(sys.argv) > 3 else 200; mx = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    path = os.path.join(W, "_watch.lua"); open(path, "w").write(LUA % {"a": a, "sz": sz, "nf": nf})
    r = subprocess.run(["mame", "sfa3ud", "-rompath", os.path.join(W, "roms_tr"), "-video", "none", "-sound", "none",
                        "-nothrottle", "-skip_gameinfo", "-debug", "-debugger", "none", "-oslog", "-autoboot_script", path],
                       capture_output=True, text=True, timeout=600, cwd=W)
    rows = carte(); keys = [x[0] for x in rows]
    hits = re.findall(r"WP image=(\d+) pc=([0-9a-f]+) val=([0-9a-f]+)", r.stdout + r.stderr)
    print("%d ecritures en $%06x sur %d images" % (len(hits), a, nf))
    for fr, pc, v in hits[:mx]:
        p = int(pc, 16); x = lookup(rows, keys, p) if p >= 0x1000 else None
        print("  image %4s  pc %06x  <- %-8s %s" % (fr, p, v, ("mips %07x %s" % (x[1], x[2][:50])) if x else ""))

if __name__ == "__main__":
    main()
