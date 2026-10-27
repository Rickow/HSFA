-- (agent_integration_max) recharge ETAT ; à chaque image, objets actifs des réservoirs (classe/sous-type bruts image) ->
-- TRACE ; s'arrête sur une exception (PC dans $A00-$A80) ou après NTR images
local n, NTR = 0, tonumber(os.getenv("NTR") or "20")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("TRACE"), "w")
local POOLS = {{0xFFB000, 32, 0x80}, {0xFFC000, 16, 0x80}, {0xFFC800, 16, 0x80}, {0xFFD000, 7, 0x200}, {0xFFAC00, 8, 0x80}}
emu.register_frame_done(function()
  n = n + 1
  if n == 2 then manager.machine:load(os.getenv("ETAT")) end
  if n > 3 then
    local t = {}
    for _, P in ipairs(POOLS) do
      for k = 0, P[2] - 1 do
        local a = P[1] + k * P[3]
        if mem:read_u8(a + 1) ~= 0 then
          t[#t + 1] = string.format("%06x:c%02x s%02x 4=%04x 6=%04x 36=%04x 1c=%04x%04x", a, mem:read_u8(a + 3), mem:read_u8(a + 2), mem:read_u16(a + 4), mem:read_u16(a + 6), mem:read_u16(a + 0x36), mem:read_u16(a + 0x1e), mem:read_u16(a + 0x1c))
        end
      end
    end
    f:write(string.format("%d pc=%06x %s\n", n, cpu.state["PC"].value, table.concat(t, " | ")))
    local pc = cpu.state["PC"].value
    if (pc >= 0xA00 and pc < 0xA80) or n >= 4 + NTR then f:close(); manager.machine:exit() end
  end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
