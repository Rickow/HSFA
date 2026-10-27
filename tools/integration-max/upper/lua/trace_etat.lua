-- (agent_integration_max) recharge un état (ETAT, dans -state_directory) puis trace le 68000 pendant NTR images
-- (trace du débogueur dans TRACE) ; à lancer avec -debug -debugger none (jamais -state en ligne de commande).
local n, NTR = 0, tonumber(os.getenv("NTR") or "4")
local fait = false
emu.register_frame_done(function()
  n = n + 1
  if n == 2 and not fait then manager.machine:load(os.getenv("ETAT")); fait = true; return end
  if n == 4 then manager.machine.debugger:command("trace " .. os.getenv("TRACE") .. ",maincpu,noloop") end
  if n == 4 + NTR then manager.machine.debugger:command("trace off"); manager.machine:exit() end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
