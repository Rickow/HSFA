-- COUPS (agent_coups) : partie VERSUS a 2 joueurs (comme commandes.lua), J1 = PERSO (hex, +$102), J2 = PERSO2 (passif),
-- jauge super de J1 forcee pleine ($11E = JAUGE, defaut $90), puis manipulations scriptees de J1 (ACTS) ; journal par
-- image : etats des joueurs, vie de J2, jauge de J1, objets actifs des reservoirs de projectiles ($FF9400 et $FFA000,
-- 12 x $100) vides en brut (mots). REF=1 : ROM arcade ; sinon traduction (octets XOR 1).
-- ACTS="60:qcf:1,300:qcfqcf:1" : a l'image relative r, manipulation (qcf, qcb, hcb, hcf, qcfqcf, qcbqcb, hcbhcb, dp) + bouton n.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local REF = os.getenv("REF") == "1"
local out = io.open(os.getenv("OUT"), "w")
local PERSO = tonumber(os.getenv("PERSO") or "", 16)
local PERSO2 = tonumber(os.getenv("PERSO2") or "", 16)
local JAUGE = tonumber(os.getenv("JAUGE") or "90", 16)
local FIN = tonumber(os.getenv("FIN") or "900")
local DUMPOBJ = os.getenv("DUMPOBJ") ~= "0"
local k, t0, sel, stable = 0, nil, 0, 0
local J1, J2 = 0xFF8400, 0xFF8800
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
local function w8(a, v) mem:write_u8(REF and a or (a ~ 1), v) end
local function J(p, s) return {":IN0", "P" .. p .. " " .. s} end
local function B(p, n)
  if n <= 3 then return {":IN0", "P" .. p .. " Button " .. n} end
  if p == 2 and n == 6 then return {":IN2", "P2 Button 6"} end
  return {":IN1", "P" .. p .. " Button " .. n}
end
-- manipulations : suites de directions (av = avant, ar = arriere), 3 images chacune, bouton sur la derniere
local MANIPS = {
  qcf = {"D", "DF", "F"}, qcb = {"D", "DB", "B"}, hcb = {"F", "DF", "D", "DB", "B"}, hcf = {"B", "DB", "D", "DF", "F"},
  dp = {"F", "D", "DF"}, qcfqcf = {"D", "DF", "F", "D", "DF", "F"}, qcbqcb = {"D", "DB", "B", "D", "DB", "B"},
  hcbhcb = {"F", "DF", "D", "DB", "B", "F", "DF", "D", "DB", "B"}, rien = {"N"},
  chdu = {"D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "D", "U"},
  chbf = {"B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "F"},
}
local seq = {}
for r, m, b in string.gmatch(os.getenv("ACTS") or "", "(%d+):(%a+):(%d)") do
  r, b = tonumber(r), tonumber(b)
  local L = MANIPS[m]
  for i, d in ipairs(L) do seq[#seq + 1] = {r + (i - 1) * 3, r + i * 3 - 1, d, (i == #L) and b or nil} end
  out:write(string.format("A %d %s %d\n", r, m, b)); RESETS = RESETS or {}; RESETS[r - 30] = true
end
local function etat(b)
  return string.format("%02x%02x%02x%02x x=%04x y=%04x vie=%04x", u8(b + 4), u8(b + 5), u8(b + 6), u8(b + 7),
    mem:read_u16(b + (REF and 0x10 or 0x12)), mem:read_u16(b + (REF and 0x14 or 0x16)), mem:read_u16(b + 0x50))
end
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(f) v[f[1] .. "|" .. f[2]] = 1 end
  local jeu = u8(0xFF80A8)
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if t0 == nil then
    if k % 500 == 0 then out:write(string.format("S %d %04x %04x %04x %02x %s %s\n", k, mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), mem:read_u16(0xFF800C), jeu, etat(J1), etat(J2))) end
    if k >= 1500 and k < 1860 and k % 60 < 8 then on({":IN2", "Coin 1"}) end
    if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on({":IN2", "1 Player Start"}) end
    if k >= 2000 and k % 40 >= 20 and k % 40 < 26 and jeu & 1 == 1 and jeu & 2 == 0 then on({":IN2", "2 Players Start"}) end
    if PERSO and ecran_sel and sel < 120 then w8(J1 + 0x102, PERSO) end
    if PERSO2 and ecran_sel and sel < 120 then w8(J2 + 0x102, PERSO2) end
    local combat = mem:read_u16(0xFF800C) == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2
    if k >= 2100 and k % 24 < 4 and jeu == 3 and not combat and (not ecran_sel or sel >= 120) then on(B(1, 1)); on(B(2, 1)) end
    if k > 2100 and combat and u8(J1 + 7) == 2 and u8(J2 + 7) == 2 then
      stable = stable + 1
      if stable == 30 then t0 = k; out:write(string.format("T0 %d perso %02x %02x\n", k, u8(J1 + 0x102), u8(J2 + 0x102))) end
    else stable = 0 end
  else
    local r = k - t0; COUPS_R = r
    if os.getenv("SNAPREL") and string.find("," .. os.getenv("SNAPREL") .. ",", "," .. r .. ",", 1, true) then manager.machine.video:snapshot() end
    -- J1 a gauche au depart : avant = Right
    local av = (mem:read_u16(J1 + (REF and 0x10 or 0x12)) < mem:read_u16(J2 + (REF and 0x10 or 0x12))) and "Right" or "Left"
    local ar = (av == "Right") and "Left" or "Right"
    for _, s in ipairs(seq) do
      if r >= s[1] and r <= s[2] then
        local d = s[3]
        if string.find(d, "D") then on(J(1, "Down")) end
        if string.find(d, "F") then on(J(1, av)) end
        if string.find(d, "B") then on(J(1, ar)) end
        if string.find(d, "U") then on(J(1, "Up")) end
        if s[4] and r >= s[2] - 1 then on(B(1, s[4])) end
      end
    end
    if os.getenv("DUMPAT") and string.find("," .. os.getenv("DUMPAT") .. ",", "," .. r .. ",", 1, true) then
      local f = io.open(os.getenv("OUT") .. ".ram" .. r, "wb"); local t = {}
      for a = 0xFF0000, 0xFFFFFE, 2 do t[#t + 1] = string.pack(">I2", mem:read_u16(a)) end
      f:write(table.concat(t)); f:close()
    end
    if RESETS and RESETS[r] and os.getenv("RESETPOS") ~= "0" then
      local XO = REF and 0x10 or 0x12
      local cam = mem:read_u16(REF and 0xFF8290 or 0xFF8292)
      mem:write_u16(J1 + XO, cam + 0x60 + tonumber(os.getenv("DX1") or "0", 16)); mem:write_u16(J2 + XO, cam + 0x60 + tonumber(os.getenv("DIST") or "60", 16))
    end
    if os.getenv("PTRAT") and string.find("," .. os.getenv("PTRAT") .. ",", "," .. r .. ",", 1, true) then
      for _, off in ipairs({0x1C, 0x60}) do
        local p = REF and mem:read_u32(J1 + off) or ((mem:read_u16(J1 + off + 2) << 16) | mem:read_u16(J1 + off))
        local t = {}
        for a = p - 0x10, p + 0x3E, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
        out:write(string.format("P %d %02x %06x %s\n", r, off, p, table.concat(t, " ")))
      end
    end
    for m0, m1, mb in string.gmatch(os.getenv("MASH") or "", "(%d+):(%d+):(%d)") do
      if r >= tonumber(m0) and r <= tonumber(m1) and r % 4 < 2 then on(B(1, tonumber(mb))) end
    end
    if JAUGE > 0 then mem:write_u16(J1 + 0x11E, JAUGE) end
    mem:write_u16(J1 + 0x50, 0x90); mem:write_u16(J1 + 0x52, 0x90)
    if r % 150 == 0 then mem:write_u16(J2 + 0x50, 0x90); mem:write_u16(J2 + 0x52, 0x90) end
    out:write(string.format("F %d J1 %s j=%04x J2 %s c=%02x/%02x i=%02x\n", r, etat(J1), mem:read_u16(J1 + 0x11E), etat(J2), u8(J1 + 0x329), u8(J2 + 0x5E), u8(J1 + 0x132)))
    for _, base in ipairs({0xFF9400, 0xFFA000}) do
      for i = 0, 11 do
        local o = base + i * 0x100
        if u8(o) ~= 0 then
          if DUMPOBJ then
            local t = {}
            for a = o, o + 0xFE, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
            out:write(string.format("O %d %06x %s\n", r, o, table.concat(t, " ")))
          else
            out:write(string.format("O %d %06x typ=%02x st=%02x%02x%02x%02x dc=%02x x=%04x\n", r, o, u8(o + 2), u8(o + 4), u8(o + 5), u8(o + 6), u8(o + 7), u8(o + 0xdc), mem:read_u16(o + (REF and 0x10 or 0x12))))
          end
        end
      end
    end
    if r >= FIN then out:close(); manager.machine:exit() end
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k > 30000 then out:write("PAS DE COMBAT\n"); out:close(); manager.machine:exit() end
end)
if not REF then
  dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
  if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end
end
