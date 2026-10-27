-- (agent_integration_max) tournee_max.lua + écritures en RAM faites par le code MAX ($3A0000-$3BFFFF) d'une valeur VAL
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local V = tonumber(os.getenv("VAL"), 16); local f = io.open(os.getenv("TRACE"), "w"); local n = 0
emu.register_frame_done(function() n = n + 1 end)
WP_TAP = mem:install_write_tap(0xFF0000, 0xFFFFFF, "wpm", function(o, d, m)
  local pc = cpu.state["PC"].value
  if pc >= 0x3A0000 and pc < 0x3C0000 and ((d & 0xFF) == V or (d >> 8) == V) then
    f:write(string.format("%d %06x pc=%06x d=%04x m=%04x\n", n, o, pc, d, m)); f:flush()
  end
end)
