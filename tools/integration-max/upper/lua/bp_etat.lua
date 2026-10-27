-- (agent_integration_max) recharge ETAT ; trace ; point d'arrêt BP (hexa) qui écrit l'expression TL (tracelog) puis repart
local n, NTR = 0, tonumber(os.getenv("NTR") or "4")
emu.register_frame_done(function()
  n = n + 1
  if n == 2 then manager.machine:load(os.getenv("ETAT")); return end
  if n == 4 then
    local d = manager.machine.debugger
    d:command("trace " .. os.getenv("TRACE") .. ",maincpu,noloop,{tracelog \"\"}")
    d:command("bpset " .. os.getenv("BP") .. ",1,{tracelog \"" .. os.getenv("TL") .. "\\n\"," .. os.getenv("TLV") .. "; g}")
  end
  if n == 4 + NTR then manager.machine.debugger:command("trace off"); manager.machine:exit() end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
