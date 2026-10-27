-- trace des images F .. F+N-1 (compteur Lua : l'image F est celle qui suit le F-ieme frame_done)
dofile("<workspace>/work/mame/banc_mem.lua")
local frames=0
local F=tonumber(os.getenv("F")); local N=tonumber(os.getenv("N") or "1")
emu.register_frame_done(function()
  frames=frames+1
  if frames == F then manager.machine.debugger:command("trace "..os.getenv("OUT")..",maincpu,noloop") end
  if frames == F+N then manager.machine.debugger:command("trace off") end
  if frames >= F+N+1 then manager.machine:exit() end
end)
