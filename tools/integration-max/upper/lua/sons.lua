-- (agent_integration_max) tournee_max.lua + journal des écritures du 68K dans la RAM partagée QSound ($618000-$619FFF)
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("SONS_OUT"), "w")
local n = 0
emu.register_frame_done(function() n = n + 1 end)
SONS_TAP = mem:install_write_tap(0x618000, 0x619fff, "sons", function(o, d, m)
  f:write(string.format("%d %06x %04x %04x pc=%06x\n", n, o, d, m, cpu.state["PC"].value))
end)
emu.register_stop(function() f:close() end)
