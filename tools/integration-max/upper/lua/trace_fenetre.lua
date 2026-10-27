-- (agent_integration_max) coup_contre.lua + trace du débogueur entre les images T0 et T1 (fichier TRACEF) ;
-- lancer avec EXTRA="-debug -debugger none"
dofile("<workspace>/work/agent_integration_max/lua/coup_contre.lua")
local n = 0
local T0, T1 = tonumber(os.getenv("T0")), tonumber(os.getenv("T1"))
emu.register_frame_done(function()
  n = n + 1
  local d = manager.machine.debugger
  if n == T0 then d:command("trace " .. os.getenv("TRACEF") .. ",maincpu,noloop") end
  if n == T1 then d:command("trace off,maincpu") end
end)
