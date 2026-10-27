-- (agent_integration_max) tournee_max.lua + journal des ÉCRITURES dans WP=debut-fin (hexa) pendant WP_IMAGES=a-b
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local a, b = os.getenv("WP"):match("(%x+)-(%x+)"); a, b = tonumber(a, 16), tonumber(b, 16)
local i0, i1 = (os.getenv("WP_IMAGES") or "0-99999999"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local f = io.open(os.getenv("TRACE"), "w")
local n = 0
emu.register_frame_done(function() n = n + 1 end)
WP_TAP = mem:install_write_tap(a, b, "wp", function(o, d, m)
  if n >= i0 and n <= i1 then f:write(string.format("%d %06x pc=%06x d=%04x m=%04x\n", n, o, cpu.state["PC"].value, d, m)); f:flush() end
end)
