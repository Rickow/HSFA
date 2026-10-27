-- (etape 4) variante de donnees_lues.lua : tournee_arcade.lua (adversaires battus vite) -> les FINS sont atteintes (les
-- journaux u_lu_* de tournee_greffe.lua s'arretaient en combat avant 56 000 images : aucune donnee de fin)
-- (greffe_arcade, etape 2) DONNEES LUES PAR UPPER hors du combat proprement dit : prise de lecture sur les donnees du
-- module d'Upper dans l'image 68K (segment $A1000-$37AE20, bloc externe $C80000, fichier 390 en $B04000), active
-- sauf pendant les manches (A5+4 = 4, A5+8 = 6, A5+C = 2/4). Ecrit DLOG : adresses 68K lues (granularite 2 octets).
-- Charge tournee_greffe.lua (memes variables : PERSO, NF, OUT...).
dofile("<workspace>/work/greffe_arcade/lua/tournee_arcade.lua")   -- (etape 4) parties gagnees VITE jusqu'a la fin (SCENEA_PASSIF)
local cpu2 = manager.machine.devices[":maincpu"]; local mem2 = cpu2.spaces["program"]
local LU = {}
local RANGES = {{0xA1000, 0x37AE1F}, {0xC80000, 0xC80000 + 767647}, {0xB04000, 0xB04000 + 499531}}
local taps = nil
local function cb(o, d, m) LU[o >> 1] = true end
local function arme(on)
  if on and not taps then
    taps = {}
    for i, r in ipairs(RANGES) do taps[i] = mem2:install_read_tap(r[1], r[2], "dlog" .. i, cb) end
  elseif not on and taps then
    for _, t in ipairs(taps) do t:remove() end
    taps = nil
  end
end
local n = 0
emu.register_frame_done(function()
  n = n + 1
  local p4, p8, pc = mem2:read_u16(0xFF8004), mem2:read_u16(0xFF8008), mem2:read_u16(0xFF800C)
  local manche = (p4 == 4 and p8 == 6 and (pc == 2 or pc == 4))
  -- (etape 4) seulement les scenes >= 6 (continue, game over, FIN, sortie) : le reste est deja dans u_lu_* (et les
  -- prises de lecture ralentissent l'emulation d'un facteur ~10)
  arme(mem2:read_u16(0xFF8000) == 2 and not manche and p4 >= 6)
  if n == tonumber(os.getenv("NF") or "0") - 1 then
    local f = io.open(os.getenv("DLOG"), "w")
    for a, _ in pairs(LU) do f:write(string.format("%x\n", a * 2)) end
    f:close()
  end
end)
