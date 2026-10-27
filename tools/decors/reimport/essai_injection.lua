-- ESSAI D'INJECTION (MAME sfa3ud standard) : tuiles neuves dans la region :gfx + blocs/listes de decor dans le
-- programme (region :maincpu), AVANT le chargement du decor ; partie, Ryu, decor force ($FF8100 = DEC), combat,
-- camera aux deux butees, captures :
--   * ecran normal 384x224 ;
--   * « fenetre elargie » : les registres de defilement X des 3 plans (CPS-A $80410C/$804110/$804114) sont decales
--     de -32 (butee gauche) / +32 (butee droite) pendant quelques images : MAME montre alors la bande de 32 px qu'un
--     ecran 448 afficherait de ce cote (le jeu, lui, compose toujours pour sa camera reelle) ;
--   * releve FRM0 (registres + palette + VRAM, format de py/recio.py) des images capturees, pour un rendu 448 hors ligne.
-- Variables : INJ_GFX, INJ_PROG (fichiers .lua generes ; vides = essai temoin sans injection), OUT (prefixe), DEC.
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
local k, sel, stable = 0, 0, 0
local SHIFT = 0
local function L(s) log:write(s .. "\n"); log:flush() end

-- ---------- injection ----------
local function hexbytes(h) local t = {}; for i = 1, #h, 2 do t[#t + 1] = tonumber(h:sub(i, i + 1), 16) end; return t end
local function injecte()
  local rg = manager.machine.memory.regions[":gfx"]
  local rp = manager.machine.memory.regions[":maincpu"]
  local fg, fp = os.getenv("INJ_GFX"), os.getenv("INJ_PROG")
  local n = 0
  if fg and fg ~= "" then
    local d = dofile(fg)
    for _, b in ipairs(d.blocs) do
      local t = hexbytes(b.hex)
      for i, v in ipairs(t) do rg:write_u8(b.off + i - 1, v) end
      n = n + #t
    end
    -- controle : relecture
    local b = d.blocs[1]; local t = hexbytes(b.hex); local ok = true
    for i = 1, math.min(#t, 64) do if rg:read_u8(b.off + i - 1) ~= t[i] then ok = false end end
    L(string.format("gfx : %d octets ecrits, relecture %s", n, tostring(ok)))
  end
  if fp and fp ~= "" then
    local d = dofile(fp); n = 0
    for _, b in ipairs(d) do
      local t = hexbytes(b.hex)
      -- region de 16 bits gros-boutiste vue par octets : write_u8 a l'adresse 68000 (la region gere l'ordre)
      for i, v in ipairs(t) do rp:write_u8(b.adr + i - 1, v) end
      n = n + #t
    end
    local b = d[1]; local t = hexbytes(b.hex)
    local lu = mem:read_u16(b.adr & ~1)
    L(string.format("programme : %d octets ecrits ; controle $%06X : bus=%04X attendu=%02X%02X", n, b.adr, lu, t[1], t[2] or 0))
  end
end

FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if k >= 1400 and d ~= 0 then
    if m == 0xffff then return DEC elseif m == 0x00ff then return DEC & 0xff elseif m == 0xff00 then return 0 end
  end
end)
-- decalage des X de defilement (fenetre elargie simulee)
SX = mem:install_write_tap(0x80410c, 0x804115, "sx", function(o, d, m)
  if SHIFT ~= 0 and (o == 0x80410c or o == 0x804110 or o == 0x804114) and m == 0xffff then
    return (d + SHIFT) & 0xffff
  end
end)

-- TAP_PAL=1 : qui lit les palettes de plans du decor $0C en ROM ($33D314 / $341BD4 / $348114, 32 x 32 o) ?
if os.getenv("TAP_PAL") == "1" then
  local vus = {}
  for _, b in ipairs({0x33D314, 0x341BD4, 0x348114}) do
    TP = TP or {}
    TP[#TP + 1] = mem:install_read_tap(b, b + 0x3ff, "pal" .. b, function(o, d, m)
      local pc = cpu.state["PC"].value
      local key = string.format("%06X", pc)
      if not vus[key] then vus[key] = true
        L(string.format("lecture palette ROM $%06X par PC=$%06X image %d A0=%08X A1=%08X", o, pc, k,
          cpu.state["A0"].value, cpu.state["A1"].value)) end
    end)
  end
end

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

-- trajet de camera apres stabilisation : (cible, maintien, decalage pendant le maintien, etiquette)
local PATH = {{0x100, 50, 0, 1}, {0x100, 12, -32, 2}, {0x100, 20, 0, 0}, {0x400, 50, 0, 3}, {0x400, 12, 32, 4}, {0x280, 4, 0, 0}}
local seg, hold, c = 1, 0, nil
local GAP = 0x60

emu.register_frame_done(function()
  k = k + 1
  if k == 1 then injecte() end
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  local jeu = mem:read_u8(0xFF80A8)
  local mode = mem:read_u16(0xFF800C)
  local combat = mode == 6 and mem:read_u8(J1 + 4) == 2 and mem:read_u8(J2 + 4) == 2
  if stable < 120 then
    if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1") end
    if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
    local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
    if ecran_sel then sel = sel + 1 else sel = 0 end
    if ecran_sel and sel < 120 then mem:write_u8(J1 + 0x102, 0) end
    if k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
    if combat then stable = stable + 1 else stable = 0 end
    if stable == 120 then L(string.format("combat stable image %d decor %04X", k, mem:read_u16(0xFF8100))) end
  else
    if not c then c = mem:read_u16(J1 + 0x10) + GAP end
    local tg = PATH[seg]
    if tg then
      if c < tg[1] then c = math.min(tg[1], c + 2) elseif c > tg[1] then c = math.max(tg[1], c - 2)
      else
        hold = hold + 1
        SHIFT = tg[3]
        if tg[4] > 0 and hold == tg[2] - 2 then
          scr(tg[4]); frm(tg[4], c)
          L(string.format("capture %d image %d c=%04X s1x=%04X s2x=%04X s3x=%04X decalage %d", tg[4], k, c,
            A:read_u16(0x0c), A:read_u16(0x10), A:read_u16(0x14), SHIFT))
        end
        if hold >= tg[2] then seg = seg + 1; hold = 0; SHIFT = 0 end
      end
    end
    mem:write_u16(J1 + 0x10, c - GAP); mem:write_u16(J2 + 0x10, c + GAP)
    if not PATH[seg] then fs:close(); fr:close(); L("FIN " .. k); log:close(); manager.machine:exit(); return end
  end
  if jeu & 1 == 1 then for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k > 12000 then L("TIMEOUT"); fs:close(); fr:close(); log:close(); manager.machine:exit() end
end)
