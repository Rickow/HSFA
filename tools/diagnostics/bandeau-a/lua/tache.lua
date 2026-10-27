-- journal par image des mots de la tache de transition ($FFDE00-$FFDE7F) quand elle est active ; puis tournee.lua
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("TOUT"), "w")
local kt, prev = 0, ""
emu.register_frame_done(function()
  kt = kt + 1
  local t = {}
  for a = 0xFFDE00, 0xFFDE7E, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
  local s = table.concat(t, " ")
  if s ~= prev then fo:write(kt .. " " .. s .. "\n"); fo:flush(); prev = s end
end)
dofile(os.getenv("BASE_LUA2") or "<workspace>/work/agent_bandeau_A/lua/trace_a.lua")
