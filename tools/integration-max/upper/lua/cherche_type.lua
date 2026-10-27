-- (agent_integration_max) coup_etat.lua + recherche d'objets dont l'octet image +3 (classe / type) = TYPE dans des
-- réservoirs (ZONES="debut:fin:pas,..." hexa) ; journal JT : image, adresse, 16 premiers octets
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local TY = tonumber(os.getenv("TYPE"), 16)
local Z = {}; for a, b, p in string.gmatch(os.getenv("ZONES"), "(%x+):(%x+):(%x+)") do Z[#Z + 1] = {tonumber(a, 16), tonumber(b, 16), tonumber(p, 16)} end
local G = io.open(os.getenv("JT"), "w"); local n = 0
emu.register_frame_done(function()
  n = n + 1
  for _, z in ipairs(Z) do for o = z[1], z[2], z[3] do
    if m:read_u8(o + 3) == TY and m:read_u8(o + 1) ~= 0 then
      local t = {}; for k = 0, 63 do t[#t + 1] = string.format("%02x", m:read_u8(o + k)) end
      G:write(string.format("%d %06x %s\n", n, o, table.concat(t, " "))) end end end
end)
