-- (agent_integration_max) tournee_max.lua + écritures dans WP avec la valeur VAL : PC et 8 longs de la pile
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local a, b = os.getenv("WP"):match("(%x+)-(%x+)"); a, b = tonumber(a, 16), tonumber(b, 16)
local V = tonumber(os.getenv("VAL"), 16)
local f = io.open(os.getenv("TRACE"), "w"); local n = 0
emu.register_frame_done(function() n = n + 1 end)
WP_TAP = mem:install_write_tap(a, b, "wpp", function(o, d, m)
  if d == V then
    local sp = cpu.state["SP"].value; local t = {}
    for k = 0, 11 do t[#t + 1] = string.format("%08x", mem:read_u32(sp + 4 * k)) end
    f:write(string.format("%d %06x pc=%06x sp=%06x %s\n", n, o, cpu.state["PC"].value, sp, table.concat(t, " "))); f:flush()
  end
end)
