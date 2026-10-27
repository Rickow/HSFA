-- (agent_integration_max) coup.lua + journal par image de J1 : octets $04-$07, $A8, $AB, $3D et pointeur d'animation $1C-$1F
dofile("<workspace>/work/agent_integration_max/lua/coup.lua")
local mem2 = manager.machine.devices[":maincpu"].spaces["program"]
local F = io.open(os.getenv("JOURNAL"), "w")
local k = 0
emu.register_frame_done(function()
  if mem2:read_u16(0xFF800C) ~= 6 then return end
  k = k + 1
  F:write(string.format("%d %02x%02x%02x%02x a8=%02x ab=%02x 3d=%02x anim=%04x%04x x=%04x i=%04x,%04x,%04x,%04x f=%08x%08x o=%02x g=%d\n", k,
    mem2:read_u8(0xFF8404), mem2:read_u8(0xFF8405), mem2:read_u8(0xFF8406), mem2:read_u8(0xFF8407),
    mem2:read_u8(0xFF84A8), mem2:read_u8(0xFF84AB), mem2:read_u8(0xFF843D),
    mem2:read_u16(0xFF841E), mem2:read_u16(0xFF841C), mem2:read_u16(0xFF8410), mem2:read_u16(0xFF8770), mem2:read_u16(0xFF8778), mem2:read_u16(0xFF877A), mem2:read_u16(0xFF877C), mem2:read_u32(0xFF8588), mem2:read_u32(0xFF858C), mem2:read_u8(0xFF840A), manager.machine.screens[":screen"]:frame_number()))
end)
