-- (palettes MAX) VERIFICATION DES PALETTES, EN LECTURE SEULE : charge le test 2 joueurs (commandes.lua) et
-- releve toutes les 100 images de combat ($FF800C = 6) les 10 premieres palettes d'objets ($90C000 : J1 = 0-4,
-- J2 = 5-9), l'ID, l'ism et la couleur de chaque joueur. Aucune prise, aucune ecriture. Sortie : PALOUT.
dofile("<workspace>/work/mame/commandes.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local REF = os.getenv("REF") == "1"
local x = REF and 0 or 1                     -- octet ROM X <-> octet traduction X ^ 1
local f = io.open(os.getenv("PALOUT"), "w")
local k = 0
emu.register_frame_done(function()
  k = k + 1
  if k % 100 ~= 0 or mem:read_u16(0xFF800C) ~= 6 then return end
  local function j(b) return string.format("id=%02x ism=%02x col=%02x", mem:read_u8(b + (0x102 ~ x)),
    mem:read_u8(b + (0x132 ~ x)), mem:read_u8(b + (0x128 ~ x))) end
  local t = {}
  for p = 0, 9 do for i = 0, 15 do t[#t + 1] = string.format("%04x", mem:read_u16(0x90C000 + 32 * p + 2 * i)) end end
  f:write(string.format("K %d J1 %s J2 %s\nP %s\n", k, j(0xFF8400), j(0xFF8800), table.concat(t, " ")))
  f:flush()
end)
