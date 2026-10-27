-- ESSAI DU DECOR SFA2 IMPORTE (fork sfa3hx, programme TRADUIT de SFA3 corrige par construit.py) :
-- partie Arcade, J1 = PERSO (defaut Ryu), decor force par prise d'ecriture sur $FF8100 (= DEC, defaut $50) a partir de
-- l'image 1400, combat ; camera aux deux butees puis au centre (X des joueurs imposes) ; captures ecran (snapshots
-- MAME) + releve FRM0 (registres CPS-A/B, palette, VRAM : format decors_ws/py/recio.py) ; puis (COMBAT=1) le combat
-- continue jusqu'a NF images avec captures periodiques.
-- Gardes : exception (PC hors ROM ou dans les vecteurs $A00-$A80, comme tournee.lua) ; lecteurs de $FF8100 quand le
-- decor vaut >= $50 dont le PC n'est pas dans la liste des sites traites (LECT : journal OUT .. "_lect.txt").
-- Variables : OUT (prefixe), DEC (hexa), PERSO (hexa), NF, COMBAT, ISO (1/2/3 : un seul plan, sprites masques).
local LUA = "<workspace>/work/mame/"
dofile(LUA .. "banc_mem.lua"); dofile(LUA .. "banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile(LUA .. "banc_sprites.lua") end
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local A = manager.machine.memory.shares[":cps_a_regs"]
local Bs = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local DEC = tonumber(os.getenv("DEC") or "50", 16)
local PERSO = tonumber(os.getenv("PERSO") or "0", 16)
local OUT = os.getenv("OUT")
local NF = tonumber(os.getenv("NF") or "9000")
local COMBAT = os.getenv("COMBAT") == "1"
local ISO = tonumber(os.getenv("ISO") or "0")
local log = io.open(OUT .. "_log.txt", "w")
local fr = io.open(OUT .. "_frm.bin", "wb")
local J1, J2 = 0xFF8400, 0xFF8800
local XO = 0x12
local function u8(a) return mem:read_u8(a ~ 1) end
local k, sel, stable = 0, 0, 0
local function L(s) log:write(s .. "\n"); log:flush() end

FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if k >= 1400 and d ~= 0 and DEC >= 0 then
    if m == 0xffff then return DEC elseif m == 0x00ff then return DEC & 0xff elseif m == 0xff00 then return 0 end
  end
end)
-- lecteurs de $FF8100 (sites connus : construit.py / format/sites100_tr.txt, PC = instruction + 2..6)
local CONNUS = {}
for l in io.lines("<workspace>/work/decors_sfa2/format/sites100_tr.txt") do
  local a = tonumber(string.match(l, "^(%x+):"), 16); for d = 2, 8, 2 do CONNUS[a + d] = true end
end
for a = 0x93200, 0x93800, 2 do CONNUS[a] = true end
for a = 0xC40, 0xC50, 2 do CONNUS[a] = true end
local lect, lj = {}, io.open(OUT .. "_lect.txt", "w")
LT = mem:install_read_tap(0xFF8100, 0xFF8101, "lect", function(o, d, m)
  if not DANS_LUA and d >= 0x50 and m == 0xffff then
    local pc = cpu.state["PC"].value & 0xffffff
    if not CONNUS[pc] and not lect[pc] then lect[pc] = k; lj:write(string.format("image %d PC %06x\n", k, pc)); lj:flush() end
  end
end)
if ISO > 0 then
  -- un seul plan (CPS-B layer control $804166 reecrit) et sprites supprimes (objram)
  LC = mem:install_write_tap(0x804166, 0x804167, "lc", function(o, d, m)
    if stable >= 120 then
      local en = ({[1] = 0x02, [2] = 0x04, [3] = 0x08})[ISO]
      return (d & ~0x3e) | en
    end
  end)
end

local function frm(t, c)
  local s = {string.pack(">c4I4I4", "FRM0", t, c)}
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", Bs:read_u16(o)) end
  for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
  for o = 0, 0xfffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
  fr:write(table.concat(s))
end
local PATH = {{0x100, 60, 1}, {0x400, 60, 2}, {0x280, 60, 3}}
local seg, hold, c = 1, 0, nil
local GAP = 0x60
local fin_cam = false

emu.register_frame_done(function()
  DANS_LUA = true
  k = k + 1
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  local jeu = u8(0xFF80A8)
  local mode = mem:read_u16(0xFF800C)
  local combat = mode == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2
  -- exception (comme tournee.lua)
  local pc = cpu.state["PC"].value & 0xffffff
  local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then
    L(string.format("EXCEPTION %d pc=%x", k, pc)); fr:close(); manager.machine:exit(); return
  end
  if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1") end
  if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if ecran_sel and sel < 120 then mem:write_u8((J1 + 0x102) ~ 1, PERSO) end
  if not fin_cam then
    if k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
    if combat then stable = stable + 1 else stable = 0 end
    if stable == 120 then L(string.format("combat stable image %d decor %04X", k, mem:read_u16(0xFF8100))) end
    if stable > 120 then
      if not c then c = mem:read_u16(J1 + XO) + GAP end
      local tg = PATH[seg]
      if tg then
        if c < tg[1] then c = math.min(tg[1], c + 2) elseif c > tg[1] then c = math.max(tg[1], c - 2)
        else
          hold = hold + 1
          if hold == tg[2] - 2 then
            manager.machine.video:snapshot(); frm(tg[3], c)
            L(string.format("capture %d image %d c=%04X s1=%04X,%04X s2=%04X,%04X s3=%04X,%04X lc=%04X", tg[3], k, c,
              A:read_u16(0x0c), A:read_u16(0x0e), A:read_u16(0x10), A:read_u16(0x12), A:read_u16(0x14), A:read_u16(0x16),
              Bs:read_u16(0x26)))
          end
          if hold >= tg[2] then seg = seg + 1; hold = 0 end
        end
        mem:write_u16(J1 + XO, c - GAP); mem:write_u16(J2 + XO, c + GAP)
      else
        fin_cam = true; L("FIN CAMERA " .. k)
        if not COMBAT then fr:close(); log:close(); manager.machine:exit(); return end
      end
    end
  else
    -- combat libre : J1 attaque (boules de feu), vie de J1 maintenue ; captures toutes les 300 images
    stable = stable + 1
    local t = k % 40
    local av = (mem:read_u16(J1 + XO) < mem:read_u16(J2 + XO)) and "Right" or "Left"
    if t < 3 then on(":IN0", "P1 Down") elseif t < 6 then on(":IN0", "P1 Down"); on(":IN0", "P1 " .. av)
    elseif t < 10 then on(":IN0", "P1 " .. av); if t >= 7 then on(":IN0", "P1 Button 1") end end
    if k % 25 < 3 and not combat then on(":IN0", "P1 Button 1") end
    if k % 300 == 0 then manager.machine.video:snapshot(); L(string.format("snap %d mode %04x %04x %04x decor %04x", k,
      mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), mode, mem:read_u16(0xFF8100))) end
  end
  if jeu & 1 == 1 then mem:write_u16(J1 + 0x50, 0x90); mem:write_u16(J1 + 0x52, 0x90) end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k >= NF then L("FIN " .. k); fr:close(); log:close(); manager.machine:exit() end
end)
emu.register_frame_done(function() DANS_LUA = false end)
