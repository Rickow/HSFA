#!/usr/bin/env python3
"""BOUCLE DE DIAGNOSTIC MAME (HANDOFF §63) : reconstruit l'image SFA3 traduite (mame_test.py), la lance
dans MAME, detecte la premiere EXCEPTION (vecteurs -> boucles $A00+2n), puis relance avec une trace
instruction par instruction autour de cette image et affiche les N dernieres instructions avant la
faute, chacune avec son adresse MIPS d'origine et le mnemonique traduit (carte_image.txt).
Usage : diag.py [N=60] [--nobuild]"""
import sys, os, subprocess, re, bisect
W = "<workspace>/work/mame"
LUA = W                                            # scripts du banc (communs a tous les modules)
# (HANDOFF §114) module (MODULE=ro3|ro5, profils.py) : dossier de travail (carte, ext_*.bin) et ROM de sortie
import profils as _PR
W = _PR.P['travail']; ROMS = os.path.join(W, _PR.P['sortie'])
os.environ["BANC_DIR"] = W + "/"
D = os.path.dirname(os.path.abspath(__file__))
EXC = {2: "erreur de bus", 3: "erreur d'adresse", 4: "instruction illegale", 5: "division par zero",
       6: "CHK", 7: "TRAPV", 8: "privilege", 9: "trace", 10: "ligne A", 11: "ligne F",
       99: "PC hors du code (fin d'image)"}

LUA_DETECT = r'''
local frames = 0
local cpu = manager.machine.devices[":maincpu"]
emu.register_frame_done(function()
  frames = frames + 1
  local pc = cpu.state["PC"].value & 0xffffff
  if pc >= 0x400000 then                                 -- PC HORS DU CODE (execution partie dans le decor)
    local f = io.open("%(out)s", "w"); f:write(string.format("%%d 99\n", frames)); f:close()
    manager.machine:exit()
  end
  local em = manager.machine.devices[":maincpu"].spaces["program"]:read_u32(0x6638F0)   -- (HANDOFF §80) IRQ2
  if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0xA00 and pc < 0xA80 then
    local f = io.open("%(out)s", "w"); f:write(string.format("%%d %%d\n", frames, (pc-0xA00)//2)); f:close()
    manager.machine:exit()
  end
  if frames >= %(maxf)d then
    local f = io.open("%(out)s", "w"); f:write("0 0\n"); f:close(); manager.machine:exit()
  end
end)
'''
LUA_TRACE = r'''
local frames = 0
emu.register_frame_done(function()
  frames = frames + 1
  if frames == %(start)d then manager.machine.debugger:command("trace %(tr)s,maincpu,noloop") end
  if frames >= %(stop)d then manager.machine:exit() end
end)
'''

# (HANDOFF §80) sequence d'entrees optionnelle (meme format que mame/jeu.lua) : INPUTS="debut-fin:PORT:Champ;..."
LUA_INPUTS = r'''
local _ports = manager.machine.ioport.ports
local _seq = {}
for item in string.gmatch(os.getenv("INPUTS") or "", "[^;]+") do
  local a, b, p, f = string.match(item, "^(%d+)-(%d+):(:[%w]+):(.+)$")
  if a then table.insert(_seq, {tonumber(a), tonumber(b), p .. "|" .. f}) end
  local a2, b2, per, dur, p2, f2 = string.match(item, "^(%d+)-(%d+)%%(%d+),(%d+):(:[%w]+):(.+)$")   -- (HANDOFF §90)
  if a2 then table.insert(_seq, {tonumber(a2), tonumber(b2), p2 .. "|" .. f2, tonumber(per), tonumber(dur)}) end
end
local _fr = 0
emu.register_frame_done(function()
  _fr = _fr + 1
  local v = {}       -- cle = NOM port|champ (un objet champ Lua est recree a chaque acces : cles distinctes)
  for _, s in ipairs(_seq) do
    local on = _fr >= s[1] and _fr <= s[2] and (not s[4] or (_fr - s[1]) % s[4] < s[5])
    v[s[3]] = (v[s[3]] or 0) | (on and 1 or 0)
  end
  for k, x in pairs(v) do local p, f = string.match(k, "^(.-)|(.*)$"); _ports[p].fields[f]:set_value(x) end
end)
'''

def mame(script, debug=False, timeout=400):
    path = os.path.join(W, "_diag.lua"); open(path, "w").write('dofile("%s/banc_mem.lua")\n' % LUA + LUA_INPUTS + script)
    import tempfile                                       # (etape B) nvram/cfg propres a chaque lancement
    tmp = tempfile.mkdtemp(prefix="diag_", dir=W)
    cmd = ["mame", "sfa3ud", "-rompath", ROMS, "-video", "none", "-sound", "none",
           "-nvram_directory", os.path.join(tmp, "nv"), "-cfg_directory", os.path.join(tmp, "cfg"),
           "-nothrottle", "-skip_gameinfo", "-autoboot_script", path]
    if debug: cmd += ["-debug", "-debugger", "none"]
    try: subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, cwd=W)
    finally: __import__("shutil").rmtree(tmp, ignore_errors=True)

def carte():
    rows = []
    for l in open(os.path.join(W, "carte_image.txt")):
        a, va, mn = l.rstrip("\n").split(" ", 2)
        rows.append((int(a, 16), int(va, 16), mn))
    rows.sort(); return rows

def lookup(rows, keys, a):
    k = bisect.bisect_right(keys, a) - 1
    return rows[k] if k >= 0 else None

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 60
    if "--nobuild" not in sys.argv:
        subprocess.run([sys.executable, os.path.join(D, "mame_test.py")], check=True, stdout=subprocess.DEVNULL)
    out = os.path.join(W, "_diag.txt")
    mame(LUA_DETECT % {"out": out, "maxf": int(os.environ.get("MAXF", "1800"))}, timeout=900)
    frame, exc = map(int, open(out).read().split())
    if frame == 0:
        print("aucune exception sur %s images" % os.environ.get("MAXF", "1800")); return 0
    print("EXCEPTION %d (%s) a l'image %d" % (exc, EXC.get(exc, "?"), frame))
    tr = os.path.join(W, "_diag.tr")
    if os.path.exists(tr): os.remove(tr)
    mame(LUA_TRACE % {"start": max(1, frame - 1), "stop": frame + 1, "tr": tr}, debug=True)
    lines = open(tr, errors="replace").read().splitlines()
    if exc == 99:                                        # premiere instruction hors du code
        k = next((i for i, l in enumerate(lines) if re.match(r"^([0-9A-F]+):", l)
                  and 0x400000 <= int(l.split(":")[0], 16) & 0xffffff), len(lines))
    else:
        k = next((i for i, l in enumerate(lines) if re.match(r"^000A[0-7][0-9A-F]:", l)), len(lines))
    rows = carte(); keys = [r[0] for r in rows]
    print("dernieres instructions avant la faute :")
    for l in lines[max(0, k - n):k + 1]:
        m = re.match(r"^([0-9A-F]{6}):\s*(.*)$", l)
        if not m: continue
        a = int(m.group(1), 16); r = lookup(rows, keys, a) if a >= 0x1000 else None
        src = "mips %07x  %s" % (r[1], r[2][:60]) if r else ""
        print("  %06x  %-34s %s" % (a, m.group(2)[:34], src))
    os.remove(tr)
    return exc

if __name__ == "__main__":
    main()
