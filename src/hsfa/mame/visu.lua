-- VISUALISEUR D'ETAT PS2 (HANDOFF §89) : rend dans MAME un etat PCSX2 du portage SFA3, converti comme le fera le fork.
-- ROM programme minimale (roms_vis : SR=$2700, boucle sur place) : le CPU ne touche a rien ; on injecte
--   RAM de jeu PS2 0x900000-0x90FFFF -> $FF0000 (mot a la meme adresse), registres CPS-A/B (copies du portage en RAM),
--   memoire video 0x920000-0x94FFFF -> $900000 (codes de plans convertis par banc_plans.lua),
--   liste d'objets du moteur natif (scratchpad 0x2000) -> $700000/$708000 (convertie par banc_sprites.lua).
-- ETAT=chemin sans extension (fichiers .bin = eeMemory, .sp = scratchpad) ; IMG = image de la capture (defaut 40).
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local etat = os.getenv("ETAT")
local IMG = tonumber(os.getenv("IMG") or "40")
local function lit(p) local h = assert(io.open(p, "rb")); local d = h:read("a"); h:close(); return d end
local ee = lit(etat .. ".bin")
local sp = lit(etat .. ".sp")
local function h16(a) return string.unpack("<I2", ee, a + 1) end
local function h32(a) return string.unpack("<I4", ee, a + 1) end
local R = 0x900000                                       -- base RAM du module (= $FF0000)
dofile("<workspace>/work/mame/banc_plans.lua")
dofile("<workspace>/work/mame/banc_sprites.lua")
local function ps2_vers_68k(a) return a - R - 0x20000 + 0x900000 end   -- memoire video
local function injecte()
  -- RAM de jeu (variables lues par le banc de sprites : persos $FF8503/$FF8903, animation $BE48)
  for o = 0, 0xfffe, 2 do mem:write_u16(0xff0000 + o, h16(R + o)) end
  -- bases CPS-A : copies du portage (pointeurs PS2 32 bits) a A5-$40BC.. = 0x903F44..
  local bases = {}
  for k = 0, 4 do bases[k] = ps2_vers_68k(h32(R + 0x3f44 + 4 * k)) end
  for k = 0, 4 do mem:write_u16(0x804102 + 2 * k, (bases[k] >> 8) & 0xffff) end
  -- memoire video (plans convertis au passage par banc_plans, palettes)
  for o = 0, 0x2fffe, 2 do mem:write_u16(0x900000 + o, h16(R + 0x20000 + o)) end
  -- registres de defilement / video / couches / palettes (copies du portage : HWREG de translate.py)
  for k = 0, 11 do mem:write_u16(0x80410c + 2 * k, h16(R + 0x62118 + 2 * k)) end
  mem:write_u16(0x804166, h16(R + 0x62146))
  for k = 0, 4 do mem:write_u16(0x400002 + 2 * k, h16(R + 0x62184 + 2 * k)) end   -- decalages des objets
  mem:write_u16(0x8040e0, h16(R + 0x621a0))
  mem:write_u16(0x804170, h16(R + 0x62150))
  mem:write_u16(0x80410a, (bases[4] >> 8) & 0xffff)      -- base de palette en dernier : declenche la copie
  -- objets : liste du moteur natif (scratchpad), vers les deux pages ; le marqueur de fin declenche l'eclatement
  for _, page in ipairs({0x700000, 0x708000}) do
    for k = 0, 0x1ff8, 8 do
      local x, y, c, a = string.unpack("<I2I2I2I2", sp, 0x2000 + k + 1)
      mem:write_u16(page + k, x); mem:write_u16(page + k + 4, c); mem:write_u16(page + k + 6, a)
      mem:write_u16(page + k + 2, y)
      if x == 0x8000 and y == 0x8000 then break end   -- fin = 1er marqueur (au-dela : restes de listes plus longues)
    end
  end
end
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n >= 20 and n <= IMG then
    local ok, err = pcall(injecte)
    if not ok then print("visu : " .. tostring(err)) end
  end
  if n == IMG + 1 then manager.machine.video:snapshot() end
  if n == IMG + 3 then manager.machine:exit() end
end)
