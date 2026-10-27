-- (agent_integration_max) coup_etat.lua + points d'arrêt comptés (BPS="adr,adr,..." hexa) écrits dans TRACE_BP
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n == 5 then
    local d = manager.machine.debugger
    d:command("trace " .. os.getenv("TRACE_BP") .. ",maincpu,noloop,{tracelog \"\"}")
    for a in string.gmatch(os.getenv("BPS"), "[^,]+") do
      d:command("bpset " .. a .. ",1,{tracelog \"BP " .. a .. " f=%d d0=%x\\n\",frame,d0; g}")
    end
  end
end)
