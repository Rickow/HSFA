-- ESSAI D'INJECTION DE DECOR SUR LE FORK sfa3hx (programme TRADUIT de SFA3, ro3) : partie, Ryu, decor force
-- ($FF8100 = DEC), combat, camera aux deux butees, captures :
--   * ecran normal 384x224 ;
--   * « fenetre elargie » simulee : X de defilement des 3 plans (CPS-A $80410C/$804110/$804114) decales de -32 (butee
--     gauche) / +32 (butee droite) pendant quelques images = bande de 32 px qu'un ecran 448 montrerait de ce cote ;
--   * releve FRM0 (registres + palette + VRAM, format de decors_ws/py/recio.py).
-- L'injection elle-meme n'est PAS faite ici : ROM programme corrigee (-rompath), bloc externe (HSFA_EXT) et tuiles
-- (HSFA_GFX) sont charges par le fork au demarrage, comme en production.
-- Variables : OUT (prefixe), DEC (hexa, defaut 0C), LUA (dossier des couches du banc), SPRITES (0 = sans banc_sprites).
local LUA = os.getenv("LUA") or "<workspace>/work/decors_ws/injection_fork/lua/"
dofile(LUA .. "banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile(LUA .. "banc_sprites.lua") end
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local A = manager.machine.memory.shares[":cps_a_regs"]
local Bs = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local SC = manager.machine.screens[":screen"]
local DEC = tonumber(os.getenv("DEC") or "0C", 16)
local OUT = os.getenv("OUT")
local log = io.open(OUT .. "_log.txt", "w")
local fs = io.open(OUT .. "_scr.bin", "wb"); local fr = io.open(OUT .. "_frm.bin", "wb")
local J1, J2 = 0xFF8400, 0xFF8800
local XO = 0x12                                   -- traduction : X d'un objet en +$12 (arcade +$10)
local function u8(a) return mem:read_u8(a ~ 1) end -- traduction : octet a l'adresse ^ 1
local k, sel, stable = 0, 0, 0
local SHIFT = 0
local FTOUT = os.getenv("FRMTOUT") == "1"
local VIT = tonumber(os.getenv("VITESSE") or "2")       -- px/image de la camera pendant les trajets
local function L(s) log:write(s .. "\n"); log:flush() end

FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if k >= 1400 and d ~= 0 then
    if m == 0xffff then return DEC elseif m == 0x00ff then return DEC & 0xff elseif m == 0xff00 then return 0 end
  end
end)
SX = mem:install_write_tap(0x80410c, 0x804115, "sx", function(o, d, m)
  if SHIFT ~= 0 and (o == 0x80410c or o == 0x804110 or o == 0x804114) and m == 0xffff then
    return (d + SHIFT) & 0xffff
  end
end)

local function frm(t, c)
  local s = {string.pack(">c4I4I4", "FRM0", t, c)}
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", Bs:read_u16(o)) end
  for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
  for o = 0, 0xfffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
  fr:write(table.concat(s))
end
local function scr(tag)
  local px, w, h = SC:pixels()
  fs:write(string.pack(">c4I4I4I4", "SCR0", tag, w, h)); fs:write(px)
end

-- (fork) capture seulement si les palettes de decor sont nominales (pas d'assombrissement de super) : PALREF
local PALREF = os.getenv("PALREF") and dofile(os.getenv("PALREF")) or {}
local function pal_ok()
  for _, e in ipairs(PALREF) do if (P:pen_color(e[1]) & 0xffffff) ~= e[2] then return false end end
  return true
end
local attente = 0
local PATH = {{0x100, 50, 0, 1}, {0x100, 12, -32, 2}, {0x100, 20, 0, 0}, {0x400, 50, 0, 3}, {0x400, 12, 32, 4}, {0x280, 4, 0, 0}}
if os.getenv("ALLER_RETOUR") == "1" then                 -- trajets complets a 2 px/image dans les deux sens (anneau)
  PATH = {{0x100, 30, 0, 0}, {0x400, 30, 0, 0}, {0x100, 30, 0, 0}, {0x400, 4, 0, 0}}
end
local seg, hold, c = 1, 0, nil
local GAP = 0x60

emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  local jeu = u8(0xFF80A8)
  local mode = mem:read_u16(0xFF800C)
  local combat = mode == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2
  if stable < 120 then
    if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1") end
    if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
    local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
    if ecran_sel then sel = sel + 1 else sel = 0 end
    if ecran_sel and sel < 120 then mem:write_u8((J1 + 0x102) ~ 1, 0) end
    if k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
    if combat then stable = stable + 1 else stable = 0 end
    if stable == 120 then L(string.format("combat stable image %d decor %04X", k, mem:read_u16(0xFF8100))) end
  else
    if not c then c = mem:read_u16(J1 + XO) + GAP end
    local tg = PATH[seg]
    if tg then
      if c < tg[1] then c = math.min(tg[1], c + VIT) elseif c > tg[1] then c = math.max(tg[1], c - VIT)
      else
        hold = hold + 1
        SHIFT = tg[3]
        if tg[4] > 0 and hold == tg[2] - 2 then
          if not pal_ok() and attente < 900 then
            attente = attente + 1; hold = hold - 1
          else
            scr(tg[4]); frm(tg[4], c)
            L(string.format("capture %d image %d c=%04X s1x=%04X s2x=%04X s3x=%04X decalage %d attente %d palettes %s", tg[4], k, c,
              A:read_u16(0x0c), A:read_u16(0x10), A:read_u16(0x14), SHIFT, attente, tostring(pal_ok())))
            attente = 0
          end
        end
        if hold >= tg[2] then seg = seg + 1; hold = 0; SHIFT = 0 end
      end
    end
    mem:write_u16(J1 + XO, c - GAP); mem:write_u16(J2 + XO, c + GAP)
    if FTOUT then frm(1000 + seg, c) end         -- (FRMTOUT=1) releve de chaque image du trajet (anneau scroll1)
    if not PATH[seg] then fs:close(); fr:close(); L("FIN " .. k); log:close(); manager.machine:exit(); return end
  end
  if jeu & 1 == 1 then for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k > 14000 then L("TIMEOUT"); fs:close(); fr:close(); log:close(); manager.machine:exit() end
end)
