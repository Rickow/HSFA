-- anim.lua (sfa, oracle local) : animations d'un decor (STG), camera fixe au centre, joueurs immobiles :
-- images 2700-3899, une sur deux : palettes (OBJ 24-31, scroll2, scroll3) et tilemaps scroll2 / scroll3 comparees a
-- l'image 2700 ; base et Y de scroll2 ; -> OUT_anim.txt (indices changes, nombre de valeurs, premiere / derniere image)
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local k = 0
TAP_STG = mem:install_write_tap(0xFFAE00, 0xFFAE01, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
local function set(p, f, v) local x = ports[p].fields[f]; if x then x:set_value(v) end end
local zones = {}   -- nom -> {reg, off, n}
local ref, vals, first, last = {}, {}, {}, {}
local regs = {}
local function lire(nom, z)
  local b = (A:read_u16(z[1]) << 8) & 0x3ffff
  local t = {}
  for i = 0, z[3] - 1 do t[i] = G:read_u16(b + z[2] + 2 * i) end
  return t
end
local Z = {pal_obj24 = {0x0a, 0x300, 0x100}, pal_s2 = {0x0a, 0x800, 0x200}, pal_s3 = {0x0a, 0xc00, 0x200},
           s2 = {0x04, 0, 0x2000}, s3 = {0x06, 0, 0x2000}}
emu.register_frame_done(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  set(":IN0", "P1 Button 1", (k >= 900 and k < 2300 and k % 30 < 3) and 1 or 0)
  if k >= 2600 then
    mem:write_u16(0xFF8410, 0x1C0 - 96); mem:write_u16(0xFF8810, 0x1C0 + 96)
    for _, j in ipairs({0xFF8400, 0xFF8800}) do mem:write_u16(j + 0x40, 0x90); mem:write_u16(j + 0x42, 0x90) end
  end
  if k >= 2700 and k < 3900 and k % 2 == 0 then
    local r = string.format("b2=%04x s2y=%04x", A:read_u16(0x04), A:read_u16(0x12)); regs[r] = (regs[r] or 0) + 1
    for nom, z in pairs(Z) do
      local t = lire(nom, z)
      if not ref[nom] then ref[nom] = t; vals[nom] = {}; first[nom] = {}; last[nom] = {}
      else
        for i = 0, z[3] - 1 do
          if t[i] ~= ref[nom][i] then
            local v = vals[nom][i]; if not v then v = {}; vals[nom][i] = v; first[nom][i] = k end
            v[t[i]] = true; last[nom][i] = k
          end
        end
      end
    end
  end
  if k == 3900 then
    local f = io.open(OUT .. "_anim.txt", "w")
    for r, n in pairs(regs) do f:write("regs " .. r .. " " .. n .. "\n") end
    for nom, _ in pairs(Z) do
      for i, v in pairs(vals[nom]) do
        local n = 0; for _ in pairs(v) do n = n + 1 end
        local l = {}; for x, _ in pairs(v) do l[#l+1] = string.format("%04x", x) end
        f:write(string.format("%s %04x ref=%04x nval=%d de=%d a=%d v=%s\n", nom, i, ref[nom][i], n + 1, first[nom][i], last[nom][i], table.concat(l, ",")))
      end
    end
    f:close(); manager.machine:exit()
  end
end)
