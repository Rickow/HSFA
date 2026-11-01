-- (e25, nouveau challenger) DONNEES LUES PAR UPPER a partir de l'image DLOG_F0 (arrivee du 2e joueur), hors des manches
-- (A5+4 = 4, A5+8 = 6, A5+C = 2/4) : memes plages que donnees_lues2.lua. Charge LUA_BASE_L (ex. lua/defi.lua). DLOG.
dofile(os.getenv("LUA_BASE_L"))
local cpu3 = manager.machine.devices[":maincpu"]; local mem3 = cpu3.spaces["program"]
local LU3 = {}
local RANGES = {{0xA1000, 0x37AE1F}, {0xC80000, 0xC80000 + 767647}, {0xB04000, 0xB04000 + 499531}}
local taps3 = nil
local function cb3(o, d, m) LU3[o >> 1] = true end
local function arme3(on)
  if on and not taps3 then
    taps3 = {}
    for i, r in ipairs(RANGES) do taps3[i] = mem3:install_read_tap(r[1], r[2], "dlog3" .. i, cb3) end
  elseif not on and taps3 then
    for _, t in ipairs(taps3) do t:remove() end
    taps3 = nil
  end
end
local n3, F0, NF3 = 0, tonumber(os.getenv("DLOG_F0") or "0"), tonumber(os.getenv("NF") or "0")
emu.register_frame_done(function()
  n3 = n3 + 1
  local p4, p8, pc = mem3:read_u16(0xFF8004), mem3:read_u16(0xFF8008), mem3:read_u16(0xFF800C)
  local manche = (p4 == 4 and p8 == 6 and (pc == 2 or pc == 4))
  arme3(n3 >= F0 and mem3:read_u16(0xFF8000) == 2 and not manche)
  if n3 == NF3 - 1 then
    local f = io.open(os.getenv("DLOG"), "w"); local ks = {}
    for a in pairs(LU3) do ks[#ks + 1] = a end
    table.sort(ks); for _, a in ipairs(ks) do f:write(string.format("%x\n", a * 2)) end
    f:close()
  end
end)
