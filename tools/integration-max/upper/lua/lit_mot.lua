-- (agent_integration_max) tournee_max.lua + lecture de longs (ADRS=a,b,... hexa ; moitiés échangées) aux images IMAGES=a-b pas 10
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local i0, i1 = os.getenv("IMAGES"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local A = {}; for x in string.gmatch(os.getenv("ADRS"), "%x+") do A[#A + 1] = tonumber(x, 16) end
local F = io.open(os.getenv("JOURNAL"), "w"); local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n >= i0 and n <= i1 and n % 10 == 0 then
    local t = {}
    for _, a in ipairs(A) do t[#t + 1] = string.format("%06x=%04x%04x", a, m:read_u16(a + 2), m:read_u16(a)) end
    F:write(n .. " " .. table.concat(t, " ") .. " b133=" .. string.format("%02x", m:read_u8(0xFF8132)) .. "\n"); F:flush()
  end
end)
