-- anim2.lua (sfa, oracle local) : CHRONOLOGIE image par image des animations de decor (STG), camera fixe au centre,
-- joueurs immobiles, images K0..K1-1 (defaut 2700..4100) ; journal de DELTAS -> OUT_chrono.txt :
--   o k slot classe sous etat cadre($20) duree($24)   objets du pool 1 ($FF9400, 32 x $80) quand le cadre change
--   p k i val     palettes scroll2 (512 mots) : mot i change
--   t k i val     tilemap scroll2 (8192 mots, code/attr) : mot i change
--   r k s2y b2    registre Y et base de scroll2 quand ils changent
--   c k n         nombre de passes de la boucle des objets (ecritures de #$20 dans $FF81B5, $1BA4C / $1BC0C) pendant
--                 l'image k : le jeu fait parfois 2 « tics » logiques par image (vitesse), les durees des tables sont
--                 en tics
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local K0, K1 = tonumber(os.getenv("K0") or "2700"), tonumber(os.getenv("K1") or "4100")
local k = 0
TAP_STG = mem:install_write_tap(0xFFAE00, 0xFFAE01, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
local ntic = 0
TAP_TIC = mem:install_write_tap(0xFF81B4, 0xFF81B5, "tic", function(o, d, m)
  if (m & 0x00ff) ~= 0 and (d & 0xff) == 0x20 then ntic = ntic + 1 end
end)
local function set(p, f, v) local x = ports[p].fields[f]; if x then x:set_value(v) end end
local f = io.open(OUT .. "_chrono.txt", "w")
local prev_o, prev_p, prev_t, prev_r = {}, {}, {}, ""
emu.register_frame_done(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  set(":IN0", "P1 Button 1", (k >= 900 and k < 2300 and k % 30 < 3) and 1 or 0)
  if k >= 2600 then
    mem:write_u16(0xFF8410, 0x1C0 - 96); mem:write_u16(0xFF8810, 0x1C0 + 96)
    for _, j in ipairs({0xFF8400, 0xFF8800}) do mem:write_u16(j + 0x40, 0x90); mem:write_u16(j + 0x42, 0x90) end
  end
  if k >= K0 and k < K1 then
    for s = 0, 31 do
      local a = 0xFF9400 + 0x80 * s
      local v = string.format("%02x %02x %02x %02x %08x %04x", mem:read_u8(a), mem:read_u8(a + 2), mem:read_u8(a + 3),
        mem:read_u8(a + 4), mem:read_u32(a + 0x20), mem:read_u16(a + 0x10))
      local cle = v:sub(1, 21)
      if mem:read_u8(a) ~= 0 and prev_o[s] ~= cle then f:write(string.format("o %d %d %s\n", k, s, v)) end
      prev_o[s] = (mem:read_u8(a) ~= 0) and cle or nil
    end
    local bp = (A:read_u16(0x0a) << 8) & 0x3ffff
    for i = 0, 0x1ff do local v = G:read_u16(bp + 0x800 + 2 * i); if prev_p[i] ~= v then f:write(string.format("p %d %d %04x\n", k, i, v)); prev_p[i] = v end end
    local bt = (A:read_u16(0x04) << 8) & 0x3ffff
    for i = 0, 0x1fff do local v = G:read_u16(bt + 2 * i); if prev_t[i] ~= v then f:write(string.format("t %d %d %04x\n", k, i, v)); prev_t[i] = v end end
    local r = string.format("%04x %04x", A:read_u16(0x12), A:read_u16(0x04))
    f:write(string.format("c %d %d\n", k, ntic))
    if r ~= prev_r then f:write(string.format("r %d %s\n", k, r)); prev_r = r end
  end
  ntic = 0
  if k == K1 then f:close(); manager.machine:exit() end
end)
