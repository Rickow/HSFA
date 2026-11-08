-- sonde.lua (sfa = SFA1 arcade, oracle local) : decor force (STG = valeur hexa de $FFAE00), partie 1 joueur, puis
--  A (images 2400-2699) : objets de decor = sprites de palette >= 24 (union code/palette/bloc) -> OUT_obj.txt ; capture
--      normale a 2690 ;
--  B (>= 2700) : scroll1 (HUD) et sprites retires ; balayage des joueurs (centre c, J1 = c - 96, J2 = c + 96) :
--      gauche, droite, centre, maintiens de 40 images ; registres a chaque image -> OUT_cam.txt ; a la fin de chaque
--      maintien : capture + vidage DMP1 (CPS-A, CPS-B, pens 0..$BFF, gfxram $30000, RAM $FF8000-$FF83FF, $FFAE00-7F).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local B = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local O1 = manager.machine.memory.shares[":objram1"]; local O2 = manager.machine.memory.shares[":objram2"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local fcam = io.open(OUT .. "_cam.txt", "w"); local fd = io.open(OUT .. "_dmp.bin", "wb")
local k = 0; local phaseB = false
TAP_STG = mem:install_write_tap(0xFFAE00, 0xFFAE01, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
TAP_LC = mem:install_write_tap(0x800166, 0x800167, "lc", function(o, d, m) if phaseB then return d & 0xfffd end end)
TAP_LC2 = mem:install_write_tap(0x804166, 0x804167, "lc2", function(o, d, m) if phaseB then return d & 0xfffd end end)
TAP_OBJ = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) if phaseB then return 0xff00 end end)
local function set(p, f, v) local x = ports[p].fields[f]; if x then x:set_value(v) end end
local objs = {}
local function scan_obj(O)
  for i = 0, 0x1ff8, 8 do
    local x, y, code, at = O:read_u16(i), O:read_u16(i + 2), O:read_u16(i + 4), O:read_u16(i + 6)
    if at == 0xff00 or y >= 0x8000 then break end
    local pal = at & 0x1f
    if pal >= 24 then
      local key = string.format("%04x %04x %02x %d %d", code, (y & 0x6000), pal, ((at >> 8) & 0xf) + 1, ((at >> 12) & 0xf) + 1)
      objs[key] = (objs[key] or 0) + 1
    end
  end
end
-- trajet du balayage (centre des joueurs)
local PATH = {{0x1C0, 20}, {0x040, 40}, {0x540, 40}, {0x1C0, 70}}
local seg, c, hold, ndump = 1, 0x1C0, 0, 0
local function dump(tag)
  local s = {string.pack(">c4I4c8", "DMP1", k, tag)}
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", B:read_u16(o)) end
  for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
  for o = 0, 0x2fffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
  for a = 0xFF8000, 0xFF83FE, 2 do s[#s+1] = string.pack(">I2", mem:read_u16(a)) end
  for a = 0xFFAE00, 0xFFAE7E, 2 do s[#s+1] = string.pack(">I2", mem:read_u16(a)) end
  fd:write(table.concat(s))
end
local prev = ""
emu.register_frame_done(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  set(":IN0", "P1 Button 1", (k >= 900 and k < 2300 and k % 30 < 3) and 1 or 0)
  if k >= 2400 and k < 2700 then scan_obj(O1); scan_obj(O2) end
  if k == 2690 then manager.machine.video:snapshot() end
  if k == 2700 then
    phaseB = true
    local f = io.open(OUT .. "_obj.txt", "w")
    for key, n in pairs(objs) do f:write(key .. " " .. n .. "\n") end
    f:close()
  end
  if k >= 2700 then
    local cible, duree = PATH[seg][1], PATH[seg][2]
    if c < cible then c = math.min(cible, c + 4) elseif c > cible then c = math.max(cible, c - 4) end
    if c == cible then hold = hold + 1 end
    mem:write_u16(0xFF8410, c - 96); mem:write_u16(0xFF8810, c + 96)
    local regs = string.format("%d %s c=%04x s1=%04x,%04x s2=%04x,%04x s3=%04x,%04x oth=%04x rso=%04x vc=%04x b2=%04x b3=%04x pal=%04x lc=%04x stg=%04x",
      k, string.char(64 + seg), c, A:read_u16(0x0c), A:read_u16(0x0e), A:read_u16(0x10), A:read_u16(0x12), A:read_u16(0x14),
      A:read_u16(0x16), A:read_u16(0x08), A:read_u16(0x20), A:read_u16(0x22), A:read_u16(0x04), A:read_u16(0x06),
      A:read_u16(0x0a), mem:read_u16(0xFF803A), mem:read_u16(0xFFAE00))
    fcam:write(regs .. " | " .. prev .. "\n"); prev = regs:sub(1, 40)
    if hold == duree then
      if seg > 1 then manager.machine.video:snapshot(); dump(string.format("%-8s", ({"", "gauche", "droite", "centre"})[seg])) end
      seg = seg + 1; hold = 0
      if seg > #PATH then fcam:close(); fd:close(); manager.machine:exit() end
    end
  end
end)
