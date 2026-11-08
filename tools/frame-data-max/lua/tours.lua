-- (frame_data_max) LUA_EN_PLUS du banc des coups : relevé PAR TOUR DE JEU (équivalent du point d'arrêt PSP 0x55650).
-- Le 68000 écrit le compteur de tours $FF851C (copie $51A -> $51C) une fois par tour, AU DÉBUT du tour, avant le traitement
-- des joueurs : à cet instant, l'état de J1 / J2 est exactement « après le tour précédent ». Une prise de vue de fin d'image
-- (lignes F) peut au contraire tomber au milieu d'un tour quand le 68000 ralentit (tour plus long qu'une image).
-- Écrit « G id r k e1 e2 x1 y1 x2 vie2 ptr att vie1 d1 » (r = dernière image finie de l'essai, k = n° de tour depuis le
-- début du MAME, mêmes champs et mêmes conventions que les lignes F de banc_coups.lua).
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local REF = os.getenv("REF") == "1"
local J1, J2 = 0xFF8400, 0xFF8800
local XO, YO = REF and 0x10 or 0x12, REF and 0x14 or 0x16
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
local function u16(a) return mem:read_u16(a) end
local function u32(a) if REF then return mem:read_u32(a) else return (mem:read_u16(a + 2) << 16) | mem:read_u16(a) end end
local function etat(b) return string.format("%02x%02x%02x%02x", u8(b + 4), u8(b + 5), u8(b + 6), u8(b + 7)) end
local K = 0
_G.FD_TAP_TOURS = mem:install_write_tap(0xFF851C, 0xFF851D, "fd_tours", function(o, d, m)
  K = K + 1
  local id, r = _G.BANC_ID, _G.BANC_R
  if not id or not r or r < 7 then return end
  local p = u32(J1 + 0x1C) & 0xffffff
  _G.BANC_OUT:write(string.format("G %s %d %d %s %s %04x %04x %04x %04x %06x %02x %04x %02x\n", id, r, K, etat(J1), etat(J2),
    u16(J1 + XO), u16(J1 + YO), u16(J2 + XO), u16(J2 + 0x50), p, u8(p + 9), u16(J1 + 0x50), u8(J1 + 0x32)))
end)
