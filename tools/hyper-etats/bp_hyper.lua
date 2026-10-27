-- (agent_hyper_etats) commandes du debogueur (BPS, separees par |) a l'image TA ; fin a TB ; avec hyper.lua (entrees)
local fr = 0
local A, Bf = tonumber(os.getenv("TA")), tonumber(os.getenv("TB"))
emu.register_frame_done(function()
  fr = fr + 1
  if fr == A then for cmd in string.gmatch(os.getenv("BPS"), "[^|]+") do manager.machine.debugger:command(cmd) end end
  if fr >= Bf then manager.machine:exit() end
end)
dofile("<workspace>/work/agent_hyper_etats/lua/hyper.lua")
