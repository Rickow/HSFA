-- (agent_integration_max) tournee_max.lua + objets actifs des réservoirs de projectiles dont le type ($3, image) = TYPE
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("TRACE"), "w"); local n = 0
local TY = tonumber(os.getenv("TYPE") or "2a", 16); local TOUS = os.getenv("TYPE") == "tous"
local POOLS = {{0xFFB000, 32, 0x80}, {0xFFC000, 16, 0x80}, {0xFFC800, 16, 0x80}, {0xFFAC00, 8, 0x80}}
emu.register_frame_done(function()
  n = n + 1
  local t = {}
  for _, P in ipairs(POOLS) do
    for k = 0, P[2] - 1 do
      local a = P[1] + k * P[3]
      if mem:read_u8(a + 1) ~= 0 and (TOUS or mem:read_u8(a + 3) == TY or mem:read_u8(a + 2) == TY) then
        t[#t + 1] = string.format("%06x:t%02x/%02x st=%04x %04x x=%04x y=%04x 1c=%04x%04x", a, mem:read_u8(a + 3), mem:read_u8(a + 2),
          mem:read_u16(a + 4), mem:read_u16(a + 6), mem:read_u16(a + 0x10), mem:read_u16(a + 0x14), mem:read_u16(a + 0x1e), mem:read_u16(a + 0x1c))
      end
    end
  end
  if #t > 0 then f:write(string.format("%d vieJ1=%04x vieJ2=%04x %s\n", n, mem:read_u16(0xFF8450), mem:read_u16(0xFF8850), table.concat(t, " | "))); f:flush() end
end)
