-- (agent_integration_max) tournee_max.lua + écritures UNIQUES (adresse, pc, valeur) dans WP pendant WP_IMAGES
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local a, b = os.getenv("WP"):match("(%x+)-(%x+)"); a, b = tonumber(a, 16), tonumber(b, 16)
local i0, i1 = (os.getenv("WP_IMAGES") or "0-99999999"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local vu, n = {}, 0
emu.register_frame_done(function() n = n + 1 end)
WP_TAP = mem:install_write_tap(a, b, "wpu", function(o, d, m)
  if n >= i0 and n <= i1 then
    local k = string.format("%06x %06x", o, cpu.state["PC"].value)
    if not vu[k] then vu[k] = string.format("%d %04x %04x", n, d, m) end
  end
end)
emu.register_stop(function()
  local f = io.open(os.getenv("TRACE"), "w")
  local t = {}
  for k, v in pairs(vu) do t[#t + 1] = k .. " " .. v end
  table.sort(t); for _, l in ipairs(t) do f:write(l .. "\n") end; f:close()
end)
