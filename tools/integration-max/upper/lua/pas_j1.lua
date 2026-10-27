-- (agent_integration_max) tournee_max.lua + pas d'animation de J1 image par image (IMAGES=a-b) : pointeur de pas, 20 octets
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local a0, a1 = os.getenv("IMAGES"):match("(%d+)-(%d+)"); a0, a1 = tonumber(a0), tonumber(a1)
local F = io.open(os.getenv("JOURNAL"), "w"); local n = 0
local J = tonumber(os.getenv("JOUEUR") or "FF8400", 16)
emu.register_frame_done(function()
  n = n + 1
  if n >= a0 and n <= a1 then
    local p = (m:read_u16(J + 0x1E) << 16) | m:read_u16(J + 0x1C)
    local t = {}; for k = 0, 19 do t[#t + 1] = string.format("%02x", m:read_u8(p + k)) end
    F:write(string.format("%d pas=%08x %s\n", n, p, table.concat(t, " "))); F:flush()
  end
end)
