-- anim_sfa2.lua (sfa2u = SFA2 arcade USA 960430, ORACLE local ; adapté de decors_sfa1/mame/lua/anim2.lua) :
-- CHRONOLOGIE image par image des animations du décor STG (valeur hexa de $FF8100), caméra fixe (joueurs maintenus à
-- c -/+ 96, c = $280), images kA+D0 .. kA+D0+N-1 (kA = combat établi). Journal de DELTAS -> OUT_chrono.txt :
--   o k pool slot actif cls sub cadre($1C) duree($32) x($10) y($14)   objets des pools A ($FFA100, 40 x $80) et
--                                                                    B ($FFB500, 4 x $80), C ($FFB700, 16 x $80, créés par $196DA) quand cls/sub/cadre change
--   t k plan i val      tilemaps s1/s2/s3 (8192 mots chacune, bases CPS-A) : mot i change
--   p k i val           palettes (mots $000-$0DF sprites de décor, $200-$7FF plans ; base CPS-A $0A) : mot i change
--   l k i val           rowscroll (1024 mots, base CPS-A $08) : mot i change
--   r k regs            registres CPS-A ($02-$16, $20, $22) quand ils changent
--   c k n               nombre de tics (écritures de #$28 dans $FF80B5, boucle des objets $1E30C) pendant l'image k
-- À la fin : « w pc zone objet(A6:classe.sous) nchang ntot ex » = écrivains de la gfxram (PC courant) par zone, pendant la fenêtre.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local D0, N = tonumber(os.getenv("D0") or "200"), tonumber(os.getenv("N") or "1600")
local k = 0; local kA = nil; local combat = 0
TAP_STG = mem:install_write_tap(0xFF8100, 0xFF8101, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
local ntic = 0
TAP_TIC = mem:install_write_tap(0xFF80B4, 0xFF80B5, "tic", function(o, d, m)
  if (m & 0x00ff) ~= 0 and (d & 0xff) == 0x28 then ntic = ntic + 1 end
end)
local fen = false
local W = {}
local zb = {}
local function zone(off)
  for _, z in ipairs(zb) do if off >= z[2] and off < z[3] then return z[1], off - z[2] end end
  return nil
end
TAP_G = mem:install_write_tap(0x900000, 0x92ffff, "gfx", function(o, d, m)
  if not fen then return end
  local off = o - 0x900000
  local z, r = zone(off)
  if not z then return end
  local pc = cpu.state["CURPC"].value
  local a6 = cpu.state["A6"].value & 0xffffff
  local ob = "-"
  if a6 >= 0xFF8000 and a6 < 0xFFC000 then ob = string.format("%04x:%02x.%02x", a6 & 0xffff, mem:read_u8(a6 + 2), mem:read_u8(a6 + 3)) end
  local key = string.format("%06x %s %s", pc, z, ob)
  local e = W[key]; if not e then e = {0, 0, r}; W[key] = e end
  e[2] = e[2] + 1
  if (mem:read_u16(o & ~1) & m) ~= (d & m) then e[1] = e[1] + 1 end
end)
local function set(p, f, v) local x = ports[p] and ports[p].fields[f]; if x then x:set_value(v) end end
local f = io.open(OUT .. "_chrono.txt", "w"); local flog = io.open(OUT .. ".log", "w")
local prev_o, prev_t, prev_p, prev_l, prev_r = {}, {{}, {}, {}}, {}, {}, ""
local POOLS = {{"A", 0xFFA100, 40}, {"B", 0xFFB500, 4}, {"C", 0xFFB700, 16}}
FS_ANIM = emu.add_machine_frame_notifier(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  if not kA then
    set(":IN0", "P1 Button 1", (k >= 900 and k % 30 < 3) and 1 or 0)
    local st = mem:read_u16(0xFF800C); local j1 = mem:read_u8(0xFF8404); local j2 = mem:read_u8(0xFF8804)
    if k > 900 and st == 2 and j1 == 2 and j2 == 2 and mem:read_u16(0xFF80A8) == 0x0100 then combat = combat + 1 else combat = 0 end
    if combat == 120 then kA = k; flog:write(string.format("combat a l'image %d, decor %04x\n", k, mem:read_u16(0xFF8100))); flog:flush() end
    if k > 9000 then flog:write("ECHEC : pas de combat\n"); flog:close(); manager.machine:exit() end
    ntic = 0
    return
  end
  set(":IN0", "P1 Button 1", 0)
  mem:write_u16(0xFF8410, 0x280 - 96); mem:write_u16(0xFF8810, 0x280 + 96)
  mem:write_u16(0xFF8450, 0x90); mem:write_u16(0xFF8850, 0x90)
  local j = k - kA - D0
  if j >= 0 and j < N then
    for _, P in ipairs(POOLS) do
      for s = 0, P[3] - 1 do
        local a = P[2] + 0x80 * s
        local act = mem:read_u8(a)
        local cle = string.format("%02x %02x %02x %08x", act, mem:read_u8(a + 2), mem:read_u8(a + 3), mem:read_u32(a + 0x1c))
        local id = P[1] .. s
        if act ~= 0 and prev_o[id] ~= cle then
          f:write(string.format("o %d %s %d %s %04x %04x %04x\n", k, P[1], s, cle, mem:read_u16(a + 0x32), mem:read_u16(a + 0x10), mem:read_u16(a + 0x14)))
        end
        prev_o[id] = (act ~= 0) and cle or nil
      end
    end
    for n, r in ipairs({0x02, 0x04, 0x06}) do
      local bt = (A:read_u16(r) << 8) & 0x3ffff; local pt = prev_t[n]
      for i = 0, 0x1fff do local v = G:read_u16(bt + 2 * i); if pt[i] ~= v then f:write(string.format("t %d %d %d %04x\n", k, n, i, v)); pt[i] = v end end
    end
    local bp = (A:read_u16(0x0a) << 8) & 0x3ffff
    for i = 0, 0x7ff do
      if i < 0xe0 or i >= 0x200 then local v = G:read_u16(bp + 2 * i); if prev_p[i] ~= v then f:write(string.format("p %d %d %04x\n", k, i, v)); prev_p[i] = v end end
    end
    local bl = (A:read_u16(0x08) << 8) & 0x3ffff
    for i = 0, 0x3ff do local v = G:read_u16(bl + 2 * i); if prev_l[i] ~= v then f:write(string.format("l %d %d %04x\n", k, i, v)); prev_l[i] = v end end
    local rs = {}
    for _, o in ipairs({0x02, 0x04, 0x06, 0x08, 0x0a, 0x0c, 0x0e, 0x10, 0x12, 0x14, 0x16, 0x20, 0x22}) do rs[#rs + 1] = string.format("%04x", A:read_u16(o)) end
    local r = table.concat(rs, " ")
    f:write(string.format("c %d %d\n", k, ntic))
    if r ~= prev_r then f:write(string.format("r %d %s\n", k, r)); prev_r = r end
    -- zones des écrivains pour l'image suivante (bases courantes)
    zb = {}
    for n, r2 in ipairs({0x02, 0x04, 0x06}) do local b = (A:read_u16(r2) << 8) & 0x3ffff; zb[#zb + 1] = {"s" .. n, b, b + 0x4000} end
    zb[#zb + 1] = {"pal", bp, bp + 0x1000}; zb[#zb + 1] = {"row", bl, bl + 0x800}
    zb[#zb + 1] = {"pal_src", 0xc000, 0xd000}
    fen = true
  end
  ntic = 0
  if j == N then
    fen = false
    for key, e in pairs(W) do f:write(string.format("w %s %d %d %d\n", key, e[1], e[2], e[3])) end
    f:close(); flog:write("fini\n"); flog:close(); manager.machine:exit()
  end
end)
