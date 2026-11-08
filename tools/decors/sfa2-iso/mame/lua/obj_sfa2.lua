-- obj_sfa2.lua (sfa2u, ORACLE local ; agent decors_restes, 07/11) : POSITIONS des sprites de decor au pixel contre l'OBJ.
-- Decor force (STG = valeur hexa de $FF8100), partie 1 joueur ; des que le combat est etabli (kA, comme anim_sfa2.lua),
-- vies maintenues et balayage du centre des joueurs c : $280 -> $100 -> $400 -> $280 (4 px/image) : la camera parcourt
-- sa course (deux bouts + milieu). Journal OUT_pos.txt, N images a partir de kA + D0 :
--   d k pool fente classe sous cadre($1C) X Y $8 $A $B $C $D $E $F $144 $26 $18 $1A $20 $22 $24 d0 s14e
--     cam1x cam1y cam2x cam2y cam3x cam3y D4 x,y,code,attr;...
--     = CHAQUE dessin d'un objet des pools de decor A ($FFA100, 40), B ($FFB500, 4), C ($FFB700, 16) par les poseurs
--       $129B4-$12E00 : etat de l'objet et des plans a la 1re entree, ancre D4 du jeu ($13028 : Y0 << 16 | X0), puis les
--       entrees OBJ reellement ecrites (DERNIERE valeur ecrite a chaque adresse pendant l'image : la memoire OBJ relue
--       par MAME peut retarder d'une image) ; prefixe X si un dessin posterieur de l'image a recouvert ces adresses ;
--       d0 = correction de rowscroll de $13028 (plan 8, $26(A6) != 0) calculee comme le jeu ; s14e = $14E(A5).
--     ATTENTION : les lignes d portent le n de la derniere image FINIE (le dessin a lieu pendant l'image suivante).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local D0, N = tonumber(os.getenv("D0") or "60"), tonumber(os.getenv("N") or "1400")
local k = 0; local kA = nil; local combat = 0; local fen = false
TAP_STG = mem:install_write_tap(0xFF8100, 0xFF8101, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
local f = io.open(OUT .. "_pos.txt", "w"); local flog = io.open(OUT .. ".log", "w")
local dessins, cur, ombre, proprio = {}, {}, {}, {}
local function s16(v) if v >= 0x8000 then return v - 0x10000 end return v end
TAP_OBJ = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m)
  if not fen then return end
  ombre[o] = d
  if (o & 7) ~= 6 then return end
  local pc = cpu.state["PC"].value
  if pc < 0x129b4 or pc >= 0x12e00 then return end
  local a6 = cpu.state["A6"].value & 0xffffff
  if a6 < 0xFFA100 or a6 >= 0xFFBF00 then return end
  local c = cur[a6]
  if c and c.o + 8 == o and c.pc == pc then c.o = o; c.e[#c.e + 1] = o
  else
    c = {o = o, pc = pc, e = {o}, n = #dessins + 1}; cur[a6] = c; dessins[#dessins + 1] = c
    local pool, slot
    if a6 < 0xFFB500 then pool, slot = "A", (a6 - 0xFFA100) // 0x80
    elseif a6 < 0xFFB700 then pool, slot = "B", (a6 - 0xFFB500) // 0x80 else pool, slot = "C", (a6 - 0xFFB700) // 0x80 end
    local d0 = 0
    if mem:read_u8(a6 + 0xe) == 8 and mem:read_u16(a6 + 0x26) ~= 0 then
      local d1 = s16(mem:read_u16(a6 + 0x26)) * 2
      local base = mem:read_u32(0xFF8380); local i = (mem:read_u16(0xFF83A0) - d1) & 0xffff
      d0 = s16(mem:read_u16(base + s16(i))) - 0xC0
    end
    c.t = string.format("d %d %s %d %02x %02x %08x %04x %04x %02x %02x %02x %02x %02x %02x %02x %04x %04x %04x %04x %04x %04x %04x %d %04x %04x %04x %04x %04x %04x %04x %08x",
      k, pool, slot, mem:read_u8(a6 + 2), mem:read_u8(a6 + 3), mem:read_u32(a6 + 0x1c), mem:read_u16(a6 + 0x10), mem:read_u16(a6 + 0x14),
      mem:read_u8(a6 + 8), mem:read_u8(a6 + 0xa), mem:read_u8(a6 + 0xb), mem:read_u8(a6 + 0xc), mem:read_u8(a6 + 0xd),
      mem:read_u8(a6 + 0xe), mem:read_u8(a6 + 0xf), mem:read_u16(a6 + 0x144), mem:read_u16(a6 + 0x26), mem:read_u16(a6 + 0x18),
      mem:read_u16(a6 + 0x1a), mem:read_u16(a6 + 0x20), mem:read_u16(a6 + 0x22), mem:read_u16(a6 + 0x24), d0, mem:read_u16(0xFF814E),
      mem:read_u16(0xFF8210), mem:read_u16(0xFF8214), mem:read_u16(0xFF8290), mem:read_u16(0xFF8294), mem:read_u16(0xFF8310),
      mem:read_u16(0xFF8314), cpu.state["D4"].value & 0xffffffff)
  end
  proprio[o] = c.n
end)
local function set(p, fl, v) local x = ports[p] and ports[p].fields[fl]; if x then x:set_value(v) end end
local PATH = {{0x280, 20}, {0x100, 40}, {0x400, 40}, {0x280, 40}}
local seg, c, hold = 1, 0x280, 0
FS_OBJ = emu.add_machine_frame_notifier(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  if not kA then
    set(":IN0", "P1 Button 1", (k >= 900 and k % 30 < 3) and 1 or 0)
    local st = mem:read_u16(0xFF800C); local j1 = mem:read_u8(0xFF8404); local j2 = mem:read_u8(0xFF8804)
    if k > 900 and st == 2 and j1 == 2 and j2 == 2 and mem:read_u16(0xFF80A8) == 0x0100 then combat = combat + 1 else combat = 0 end
    if combat == 120 then kA = k; flog:write(string.format("combat a l'image %d, decor %04x\n", k, mem:read_u16(0xFF8100))); flog:flush() end
    if k > 9000 then flog:write("ECHEC : pas de combat\n"); flog:close(); manager.machine:exit() end
    return
  end
  set(":IN0", "P1 Button 1", 0)
  mem:write_u16(0xFF8450, 0x90); mem:write_u16(0xFF8850, 0x90)
  local j = k - kA - D0
  if j >= 0 then
    local cible, duree = PATH[seg][1], PATH[seg][2]
    if c < cible then c = math.min(cible, c + 4) elseif c > cible then c = math.max(cible, c - 4) end
    if c == cible then hold = hold + 1 end
    if hold >= duree and seg < #PATH then seg = seg + 1; hold = 0 end
  end
  mem:write_u16(0xFF8410, c - 96); mem:write_u16(0xFF8810, c + 96)
  if fen then
    for _, d in ipairs(dessins) do
      local t = {}; local ok = true
      for _, o in ipairs(d.e) do
        if proprio[o] ~= d.n then ok = false end
        t[#t + 1] = string.format("%04x,%04x,%04x,%04x", ombre[o - 6] or 0xffff, ombre[o - 4] or 0xffff, ombre[o - 2] or 0xffff, ombre[o] or 0xffff)
      end
      f:write(d.t .. " " .. (ok and "" or "X") .. table.concat(t, ";") .. "\n")
    end
  end
  dessins, cur, ombre, proprio = {}, {}, {}, {}
  fen = (j >= 0 and j < N)
  if j >= N then f:close(); flog:write("fini\n"); flog:close(); manager.machine:exit() end
end)
