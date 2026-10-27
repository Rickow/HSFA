-- (agent_integration_max) tournee_max.lua + relevé d'un objet (OBJ, hexa) image par image : octets 0-$7F
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = tonumber(os.getenv("OBJ"), 16); local i0, i1 = (os.getenv("IMAGES") or "0-999999"):match("(%d+)-(%d+)")
i0, i1 = tonumber(i0), tonumber(i1)
local f = io.open(os.getenv("TRACE"), "w"); local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n >= i0 and n <= i1 then
    local t = {}
    for k = 0, 0x7E, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(A + k)) end
    f:write(string.format("%d %s | J2 vie=%04x x=%04x\n", n, table.concat(t, " "), mem:read_u16(0xFF8850), mem:read_u16(0xFF8810))); f:flush()
  end
end)
