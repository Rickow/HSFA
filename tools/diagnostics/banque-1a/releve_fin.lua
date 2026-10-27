-- RELEVE DES ACTEURS PENDANT UNE FIN (agent_banque_1a) : charge tournee.lua (partie Arcade jusqu'a la fin), puis,
-- pendant la sequence de fin ($FF8004 = $000A), releve toutes les RELEVE_P images :
--  - les objets actifs du reservoir des acteurs $3000(A5) = $FFB000 (32 x $80) : classe, sous-type, $1A, $18, perso $7F,
--    n° d'animation $70 ;
--  - (traduction) les emplacements de banque (bits 13-15 de Y) de la liste d'objets BRUTE du jeu (BANC_OMBRE) ;
--  - le pointeur d'animation native $FF40BC (Upper) et les persos de J1/J2.
-- Sortie : RELEVE (fichier texte). Lecture seule de la RAM.
dofile("<workspace>/work/mame/tournee.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local REF = os.getenv("REF") == "1"
local P = tonumber(os.getenv("RELEVE_P") or "20")
local f = io.open(os.getenv("RELEVE"), "w")
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
local vus, img, nfin = {}, 0, 0
local emp = {}
emu.register_frame_done(function()
  img = img + 1
  if mem:read_u16(0xFF8004) ~= 0x000A then return end
  nfin = nfin + 1
  if nfin % P ~= 1 then return end
  local ptr = REF and 0 or mem:read_u32(0xFF40BC)   -- brut, comme banc_sprites.lua et carte.txt
  local j1, j2 = u8(0xFF8502), u8(0xFF8902)
  for o = 0xFFB000, 0xFFBF80, 0x80 do
    if u8(o) ~= 0 then
      local cl, st = u8(o + 2), u8(o + 3)
      local k = string.format("cl=%02X st=%02X 1A=%04X 18=%04X 7F=%02X 70=%02X | J1=%02X J2=%02X ptrC0BC=%08X",
        cl, st, mem:read_u16(o + 0x1A), mem:read_u16(o + 0x18), u8(o + 0x7F), u8(o + 0x70), j1, j2, ptr)
      if not vus[k] then vus[k] = 1; f:write(string.format("%6d fin+%5d obj %06X %s\n", img, nfin, o, k)) else vus[k] = vus[k] + 1 end
    end
  end
  if BANC_OMBRE then
    local h = {}
    for page = 0x700000, 0x708000, 0x8000 do
      for a = page, page + 0x2000 - 8, 8 do
        local x, y = BANC_OMBRE[a] or 0, BANC_OMBRE[a + 2] or 0
        if x == 0x8000 and y == 0x8000 then break end
        local e = (y >> 13) & 7; h[e] = (h[e] or 0) + 1
      end
    end
    local s = ""
    for e = 0, 7 do s = s .. string.format(" e%d=%d", e, h[e] or 0) end
    f:write(string.format("%6d fin+%5d liste brute :%s ptrC0BC=%08X\n", img, nfin, s, ptr))
  end
  f:flush()
end)
