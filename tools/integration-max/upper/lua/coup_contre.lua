-- (agent_integration_max) coup_etat.lua + mot « contre déclenché » ($8BAC(A5) = $FF0BAC) : journal JC des images où il vaut != 0
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local G = io.open(os.getenv("JC"), "w"); local n = 0
emu.register_frame_done(function()
  n = n + 1
  local v = m:read_u16(0xFF0BAC)
  if v ~= 0 then G:write(string.format("%d %04x\n", n, v)); G:flush() end
end)
