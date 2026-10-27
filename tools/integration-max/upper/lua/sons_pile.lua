-- (agent_integration_max) tournee_max.lua + écritures QSound $618000 dont l'octet bas = HI (hexa) : PC et 8 longs de pile
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("SONS_OUT"), "w"); local HI = tonumber(os.getenv("HI") or "1", 16)
local n = 0
emu.register_frame_done(function() n = n + 1 end)
SONS_TAP = mem:install_write_tap(0x618000, 0x618001, "sons", function(o, d, m)
  if (d & 0xff) == HI and n > 2600 then
    local sp = cpu.state["SP"].value; local t = {}
    for k = 0, 9 do t[#t + 1] = string.format("%08x", mem:read_u32(sp + 4 * k)) end
    f:write(string.format("%d %04x pc=%06x pile %s\n", n, d, cpu.state["PC"].value, table.concat(t, " ")))
  end
end)
emu.register_stop(function() f:close() end)
