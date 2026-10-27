-- (banc_max_psp) LUA_EN_PLUS du banc des coups : a chaque image d'essai, ecrit dans le journal commun (_G.BANC_OUT) :
--   E id r y2 x2           position de J2 (Y2 absent du journal de base)
--   Q id r adr b0 typ etat x y   chaque objet actif des zones $FF8800+ (pas $100) hors J1 / J2   (SCANOBJ=1 : toute la zone $FF8C00-$FFC000)
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local XO, YO = 0x12, 0x16
local function u8(a) return mem:read_u8(a ~ 1) end
local function u16(a) return mem:read_u16(a) end
local J2 = 0xFF8800
local ZONES = {}
if os.getenv("SCANOBJ") == "1" then
  for a = 0xFF8C00, 0xFFBF00, 0x100 do ZONES[#ZONES + 1] = a end
else
  for _, base in ipairs({0xFF9400, 0xFFA000}) do for i = 0, 11 do ZONES[#ZONES + 1] = base + i * 0x100 end end
end
-- X1REL = distance de J1 au mur gauche (defaut : 144 = depart naturel) ; J1 part de (X de depart - 144 + X1REL), J2 a la meme distance qu'avant
local X1REL = tonumber(os.getenv("X1REL") or "")
local J1 = 0xFF8400
emu.register_frame_done(function()
  local id, r = _G.BANC_ID, _G.BANC_R
  if not id or not r or not _G.BANC_OUT then return end
  if X1REL and r <= 6 then
    local a, b = u16(J1 + XO), u16(J2 + XO)
    local n = a - 144 + X1REL
    mem:write_u16(J1 + XO, n); mem:write_u16(J2 + XO, n + (b - a))
  end
  _G.BANC_OUT:write(string.format("E %s %d %04x %04x\n", id, r, u16(J2 + YO), u16(J2 + XO)))
  for _, o in ipairs(ZONES) do
    if u8(o) ~= 0 then
      _G.BANC_OUT:write(string.format("Q %s %d %06x %02x %02x%02x %02x%02x%02x%02x %04x %04x\n", id, r, o, u8(o), u8(o + 2), u8(o + 3),
        u8(o + 4), u8(o + 5), u8(o + 6), u8(o + 7), u16(o + XO), u16(o + YO)))
    end
  end
end)
