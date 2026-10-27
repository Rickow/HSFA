-- agent_zangief : decor force (STG hex, defaut 20 = usine de Zangief) via prise sur $FF8100, puis tournee.lua ;
-- vidages (VRAM $900000-$93FFFF, regs CPS-A/B, palette MAME) + capture aux images DUMPAT (liste) apres le debut du combat
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local STG = tonumber(os.getenv("STG") or "20", 16)
local D = os.getenv("DDIR") or "<workspace>/work/agent_zangief/dump/"
local k, last = 0, -1
FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if d ~= 0 then
    if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
  end
end)
local liste = {}
for v in string.gmatch(os.getenv("DUMPAT") or "", "%d+") do liste[tonumber(v)] = true end
local comb = 0
local ISO = tonumber(os.getenv("ISO") or "")
if ISO then   -- (comme decors_ws/rec.lua) un plan seul, objets supprimes
  local en = ({[0] = 0x0e, [1] = 0x02, [2] = 0x04, [3] = 0x08})[ISO]
  LT = mem:install_write_tap(0x804166, 0x804167, "lay", function(o, d, m) if comb > 0 then return (d & ~0x3e) | en end end)
  OT1 = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) if comb > 0 then return 0xff00 end end)
end
emu.register_frame_done(function()
  k = k + 1
  local s = mem:read_u16(0xFF8100)
  if s ~= last then print(string.format("S %d %04x", k, s)); last = s end
  if mem:read_u16(0xFF800C) == 6 then comb = comb + 1 else comb = 0 end
  if liste[comb] then
    local tag = string.format("%s_c%d", os.getenv("TAG") or "u", comb)
    local f = io.open(D .. tag .. ".vram", "wb"); local t = {}
    for a = 0x900000, 0x93FFFE, 2 do t[#t+1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(t)); f:close()
    f = io.open(D .. tag .. ".regs", "wb"); t = {}
    local A = manager.machine.memory.shares[":cps_a_regs"]; local B = manager.machine.memory.shares[":cps_b_regs"]
    for o = 0, 0x3e, 2 do t[#t+1] = string.pack(">I2", A:read_u16(o)) end
    for o = 0, 0x3e, 2 do t[#t+1] = string.pack(">I2", B:read_u16(o)) end
    for a = 0x804200, 0x804206, 2 do t[#t+1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(t)); f:close()
    f = io.open(D .. tag .. ".ram", "wb"); t = {}
    for a = 0xFF0000, 0xFFFFFE, 2 do t[#t+1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(t)); f:close()
    local pal = manager.machine.palettes[":palette"]
    f = io.open(D .. tag .. ".pal", "wb"); t = {}
    for i = 0, 0xBFF do t[#t+1] = string.pack(">I4", pal:pen_color(i)) end
    f:write(table.concat(t)); f:close()
    manager.machine.video:snapshot()
    print(string.format("DUMP %s image %d", tag, k))
  end
end)
dofile("<workspace>/work/mame/tournee.lua")
