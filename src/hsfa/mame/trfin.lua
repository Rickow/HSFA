-- TRACE AVEC ENTREES (HANDOFF §80) : INPUTS (format jeu.lua), F..F+N tracees dans OUT, registres A6/A0/D0
dofile("<workspace>/work/mame/banc_mem.lua")
local ports = manager.machine.ioport.ports
local seq = {}
for item in string.gmatch(os.getenv("INPUTS") or "", "[^;]+") do
  local a, b, p, f = string.match(item, "^(%d+)-(%d+):(:[%w]+):(.+)$")
  if a then table.insert(seq, {tonumber(a), tonumber(b), ports[p].fields[f]}) end
end
local F=tonumber(os.getenv("F")); local N=tonumber(os.getenv("N") or "1")
local frames=0
emu.register_frame_done(function()
  frames=frames+1
  local v={}
  for _, s in ipairs(seq) do v[s[3]] = (v[s[3]] or 0) | ((frames >= s[1] and frames <= s[2]) and 1 or 0) end
  for f, x in pairs(v) do f:set_value(x) end
  if frames==F then manager.machine.debugger:command('trace '..os.getenv("OUT")..',maincpu,noloop,{tracelog "A6=%06x A0=%06x D0=%08x ",a6&ffffff,a0,d0}') end
  if frames==F+N then manager.machine.debugger:command("trace off") end
  if frames>=F+N+1 then manager.machine:exit() end
end)
