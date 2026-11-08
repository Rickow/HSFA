-- sonde_defil.lua = sonde_sfa2.lua + (agent decors_restes, 07/11) : à chaque image du balayage, la ligne de OUT_cam.txt
-- reçoit en plus « | ram » : longs $FF8250 $FF8254 (décalages s1), $FF8350 $FF8354, mots $FF8358 $FF835A (s3),
-- $FF8258 $FF825A, $FF823C $FF8260 (minuterie / indice s1), $FF833C $FF8360 (s3), $FF8398 (sol), $FF82A0 $FF8288 $FF82A4
-- $FF828C (caméra s2 et origines), $FF814E, $FF8125, $FF8102, $FF8200 (état s1). POKE="adr=val[,…]" (hexa, mots)
-- écrit à chaque image dès l'image 700 (ex. $FF8102 = 1 : 2e manche).
local POKES = {}
for a, v in string.gmatch(os.getenv("POKE") or "", "(%x+)=(%x+)") do POKES[#POKES+1] = {tonumber(a, 16), tonumber(v, 16)} end
local kp = 0
FS_POKE = emu.add_machine_frame_notifier(function()
  kp = kp + 1
  if kp >= 700 then for _, p in ipairs(POKES) do manager.machine.devices[":maincpu"].spaces["program"]:write_u16(p[1], p[2]) end end
end)
local function ramdef(mem)
  return string.format(" | ram %08x %08x %08x %08x %04x %04x %04x %04x %04x %04x %04x %04x %04x %08x %08x %08x %08x %04x %02x %04x %02x",
    mem:read_u32(0xFF8250), mem:read_u32(0xFF8254), mem:read_u32(0xFF8350), mem:read_u32(0xFF8354), mem:read_u16(0xFF8358),
    mem:read_u16(0xFF835A), mem:read_u16(0xFF8258), mem:read_u16(0xFF825A), mem:read_u16(0xFF823C), mem:read_u16(0xFF8260),
    mem:read_u16(0xFF833C), mem:read_u16(0xFF8360), mem:read_u16(0xFF8398), mem:read_u32(0xFF82A0), mem:read_u32(0xFF8288),
    mem:read_u32(0xFF82A4), mem:read_u32(0xFF828C), mem:read_u16(0xFF814E), mem:read_u8(0xFF8125), mem:read_u16(0xFF8102), mem:read_u8(0xFF8200))
end
-- sonde_sfa2.lua (sfa2u = SFA2 arcade USA 960430, ORACLE local ; adapté de decors_sfa1/mame/lua/sonde.lua et des
-- adresses de decors_sfa2/export) : décor forcé (STG = valeur hexa de $FF8100) dès l'image 700, partie 1 joueur (Ryu),
--  A (combat détecté + 300 images) : objets de décor = sprites de palette 0-6 (union code/palette/bloc) -> OUT_obj.txt ;
--      capture « en jeu » (sprites et HUD) ;
--  B : sprites retirés (objram) ; balayage des joueurs (centre c, J1 = c - 96, J2 = c + 96, vies maintenues) :
--      gauche, droite, centre (maintiens) ; registres à chaque image -> OUT_cam.txt ; animations (mots de VRAM des
--      tilemaps et couleurs des palettes qui changent pendant les maintiens) -> OUT_anim.txt ; à la fin de chaque
--      maintien : capture + vidages DMP1 des images t-1 et t (CPS-A, CPS-B, pens 0..$BFF, gfxram $30000,
--      RAM $FF8000-$FF83FF, $FFB000-$FFB07F).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local B = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local O1 = manager.machine.memory.shares[":objram1"]; local O2 = manager.machine.memory.shares[":objram2"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local HOLD = tonumber(os.getenv("HOLD") or "90")
local fcam = io.open(OUT .. "_cam.txt", "w"); local fd = io.open(OUT .. "_dmp.bin", "wb")
local fan = io.open(OUT .. "_anim.txt", "w"); local flog = io.open(OUT .. ".log", "w")
local k = 0; local phaseB = false; local combat = 0; local kA = nil
TAP_STG = mem:install_write_tap(0xFF8100, 0xFF8101, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
-- caméra Y figée pendant le balayage (pas de sauts dans les vues ; même prise que decors_sfa2/export « cup »)
TAP_CAMY = mem:install_write_tap(0xFF82A4, 0xFF82A5, "camy", function(o, d, m) if phaseB then return 0 end end)
TAP_OBJ = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) if phaseB then return 0xff00 end end)
local function set(p, f, v) local x = ports[p] and ports[p].fields[f]; if x then x:set_value(v) end end
local objs = {}
local function scan_obj(O)
  for i = 0, 0x1ff8, 8 do
    local x, y, code, at = O:read_u16(i), O:read_u16(i + 2), O:read_u16(i + 4), O:read_u16(i + 6)
    if at == 0xff00 or (at & 0xff00) == 0xff00 then break end
    local pal = at & 0x1f
    if pal < 7 then
      local c = code + ((y & 0x6000) << 3)
      local key = string.format("%05x %02x %d %d", c, pal, ((at >> 8) & 0xf) + 1, ((at >> 12) & 0xf) + 1)
      objs[key] = (objs[key] or 0) + 1
    end
  end
end
-- trajet du balayage (centre des joueurs) : caméra = centre - $C0, butées $100-$280 (DECOR-SFA2-EXPORT §3)
local PATH = {{0x280, 20, ""}, {0x180, HOLD, "gauche"}, {0x380, HOLD, "droite"}, {0x280, HOLD * 2, "centre"}}
-- ANIM=1 : passe longue (maintiens de 300/300/900 images), union des codes vus dans les tilemaps et des valeurs de chaque
-- couleur (pens $000-$07F, $200-$7FF) -> OUT_codes.txt, OUT_pals.txt (pas de vidage DMP1)
local ANIM = os.getenv("ANIM") == "1"
if ANIM then PATH = {{0x280, 20, ""}, {0x180, 300, "gauche"}, {0x380, 300, "droite"}, {0x280, 900, "centre"}} end
local CODES = {{}, {}, {}}; local PALS = {}
local seg, c, hold = 1, 0x280, 0
local function dump(tag)
  local s = {string.pack(">c4I4c8", "DMP1", k, string.format("%-8s", tag))}
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", B:read_u16(o)) end
  for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
  for o = 0, 0x2fffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
  for a = 0xFF8000, 0xFF83FE, 2 do s[#s+1] = string.pack(">I2", mem:read_u16(a)) end
  for a = 0xFFB000, 0xFFB07E, 2 do s[#s+1] = string.pack(">I2", mem:read_u16(a)) end
  return table.concat(s)
end
-- animations : copie des mots des tilemaps (bases CPS-A) et des pens de plans/objets de décor
local prevT, prevP = nil, nil
local function etat()
  local t = {}
  for n, r in ipairs({0x02, 0x04, 0x06}) do
    local base = ((A:read_u16(r) << 8) & 0x3c000)
    local tt = {}
    for o = 0, 0x3ffe, 2 do tt[o] = G:read_u16(base + o) end
    t[n] = tt
  end
  local p = {}
  for i = 0, 0x7ff do p[i] = P:pen_color(i) end
  return t, p
end
local prevdump = nil
local prev = ""
FS_SFA2 = {}
FS_SFA2.cb = emu.add_machine_frame_notifier(function()
  k = k + 1
  if k % 1000 == 0 then flog:write(string.format("image %d etat %04x %02x %02x %04x decor %04x\n", k, mem:read_u16(0xFF800C), mem:read_u8(0xFF8404), mem:read_u8(0xFF8804), mem:read_u16(0xFF80A8), mem:read_u16(0xFF8100))); flog:flush() end
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  if not kA then
    set(":IN0", "P1 Button 1", (k >= 900 and k % 30 < 3) and 1 or 0)
    local st = mem:read_u16(0xFF800C); local j1 = mem:read_u8(0xFF8404); local j2 = mem:read_u8(0xFF8804)
    if k > 900 and st == 2 and j1 == 2 and j2 == 2 and mem:read_u16(0xFF80A8) == 0x0100 then combat = combat + 1 else combat = 0 end
    if combat == 120 then kA = k; flog:write(string.format("combat a l'image %d, decor %04x\n", k, mem:read_u16(0xFF8100))) end
    if k > 9000 then flog:write("ECHEC : pas de combat\n"); flog:close(); manager.machine:exit() end
    return
  end
  set(":IN0", "P1 Button 1", 0)
  mem:write_u16(0xFF8450, 0x90); mem:write_u16(0xFF8850, 0x90)
  if k < kA + 300 then scan_obj(O1); scan_obj(O2); if k == kA + 290 then manager.machine.video:snapshot() end; return end
  if k == kA + 300 then
    phaseB = true
    local f = io.open(OUT .. "_obj.txt", "w")
    for key, n in pairs(objs) do f:write(key .. " " .. n .. "\n") end
    f:close()
  end
  local cible, duree, tag = PATH[seg][1], PATH[seg][2], PATH[seg][3]
  if c < cible then c = math.min(cible, c + 4) elseif c > cible then c = math.max(cible, c - 4) end
  if c == cible then hold = hold + 1 end
  mem:write_u16(0xFF8410, c - 96); mem:write_u16(0xFF8810, c + 96)
  local regs = string.format("%d %s c=%04x s1=%04x,%04x s2=%04x,%04x s3=%04x,%04x oth=%04x rso=%04x vc=%04x b1=%04x b2=%04x b3=%04x lc=%04x cam=%04x,%04x stg=%04x",
    k, string.char(64 + seg), c, A:read_u16(0x0c), A:read_u16(0x0e), A:read_u16(0x10), A:read_u16(0x12), A:read_u16(0x14),
    A:read_u16(0x16), A:read_u16(0x08), A:read_u16(0x20), A:read_u16(0x22), A:read_u16(0x02), A:read_u16(0x04), A:read_u16(0x06),
    B:read_u16(0x26), mem:read_u16(0xFF8290), mem:read_u16(0xFF82A4), mem:read_u16(0xFF8100))
  fcam:write(regs .. ramdef(mem) .. "\n")
  if hold >= 2 then
    local t, p = etat()
    if ANIM then
      for n = 1, 3 do for o, v in pairs(t[n]) do if o % 4 == 0 then CODES[n][v] = (CODES[n][v] or 0) + 1 end end end
      for i = 0, 0x7ff do if i < 0x80 or i >= 0x200 then local q = PALS[i] or {}; q[p[i]] = true; PALS[i] = q end end
    end
    if prevT then
      local s = {}
      for n = 1, 3 do
        local nb, ex = 0, ""
        for o, v in pairs(t[n]) do if prevT[n][o] ~= v then nb = nb + 1; if nb <= 6 then ex = ex .. string.format(" %04x:%04x>%04x", o // 2, prevT[n][o], v) end end end
        if nb > 0 then s[#s+1] = string.format("s%d %d%s", n, nb, ex) end
      end
      local np, exp = 0, ""
      for i = 0, 0x7ff do if prevP[i] ~= p[i] then np = np + 1; if np <= 8 then exp = exp .. string.format(" %03x", i) end end end
      if np > 0 then s[#s+1] = string.format("pal %d%s", np, exp) end
      if #s > 0 then fan:write(string.format("%d %s %s\n", k, tag, table.concat(s, " | "))) end
    end
    prevT, prevP = t, p
  else prevT = nil end
  if seg > 1 and hold == duree - 1 and not ANIM then prevdump = dump(tag .. "-1") end
  if hold == duree then
    if seg > 1 and not ANIM then manager.machine.video:snapshot(); fd:write(prevdump); fd:write(dump(tag)) end
    seg = seg + 1; hold = 0; prevT = nil
    if seg > #PATH then
      if ANIM then
        local fc = io.open(OUT .. "_codes.txt", "w")
        for n = 1, 3 do for v, c in pairs(CODES[n]) do fc:write(string.format("s%d %04x %d\n", n, v, c)) end end
        fc:close()
        local fp = io.open(OUT .. "_pals.txt", "w")
        for i, q in pairs(PALS) do local l = {}; for v, _ in pairs(q) do l[#l+1] = string.format("%06x", v) end
          if #l > 1 then fp:write(string.format("%03x %d %s\n", i, #l, table.concat(l, " "))) end end
        fp:close()
      end
      fcam:close(); fd:close(); fan:close(); flog:close(); manager.machine:exit()
    end
  end
end)
