-- (etape 5) DONNEES LUES dans Hyper / ro9a : enveloppe de LUA_BASE ; prise de lecture sur LUS_PLAGES="a-b,c-d" (adresses
-- 68K, hexa), REINSTALLEE toutes les 120 images (les prises tombent quand le banc installe ses propres gestionnaires) ;
-- a l'image LUS_NF ecrit LUS_OUT (blocs de 256 o lus, une adresse par ligne).
dofile(os.getenv("LUA_BASE"))
local m = manager.machine.devices[":maincpu"].spaces["program"]
local LU = {}; local taps = {}; local PL = {}
for a, b in string.gmatch(os.getenv("LUS_PLAGES"), "(%x+)-(%x+)") do PL[#PL + 1] = {tonumber(a, 16), tonumber(b, 16)} end
local HORS = os.getenv("LUS_HORS_MANCHE") == "1"   -- armee seulement hors des manches (A5+4 = 4, A5+8 = 6, A5+C = 2/4)
local arme_ = true
local function arme()
  for _, t in ipairs(taps) do t:remove() end
  taps = {}
  for i, r in ipairs(PL) do taps[i] = m:install_read_tap(r[1], r[2], "lus" .. i, function(o, d, mk) if arme_ then LU[o >> 8] = true end end) end
end
local n = 0; local NFL = tonumber(os.getenv("LUS_NF"))
emu.register_frame_done(function()
  n = n + 1
  if n % 120 == 2 then arme() end
  if HORS then local p4, p8, pc = m:read_u16(0xFF8004), m:read_u16(0xFF8008), m:read_u16(0xFF800C); arme_ = not (p4 == 4 and p8 == 6 and (pc == 2 or pc == 4)) end
  if n == NFL then
    local f = io.open(os.getenv("LUS_OUT"), "w")
    for a, _ in pairs(LU) do f:write(string.format("%x\n", a << 8)) end
    f:close()
  end
end)
