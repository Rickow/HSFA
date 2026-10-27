-- (agent_integration_max) coup_etat.lua + objets actifs d'un réservoir (ZONE=debut:fin:pas) aux images IMAGES=a-b
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local a, b, p = os.getenv("ZONE"):match("(%x+):(%x+):(%x+)"); a, b, p = tonumber(a, 16), tonumber(b, 16), tonumber(p, 16)
local i0, i1 = os.getenv("IMAGES"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local G = io.open(os.getenv("JT"), "w"); local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n < i0 or n > i1 then return end
  for o = a, b, p do if m:read_u8(o + 1) ~= 0 then
    local t = {}; for k = 0, 0x1F do t[#t + 1] = string.format("%02x", m:read_u8(o + k)) end
    G:write(string.format("%d %06x %s\n", n, o, table.concat(t, " "))) end end
end)
