-- (e34) enveloppe : charge VB_BASE (defaut graine_pc.lua) ; aux images V_IM="n,n" : capture + VRAM $900000-$92FFFF, registres
-- CPS-A / CPS-B (partages :cps_a_regs / :cps_b_regs) et $804200-$804206 -> V_DIR/v_<n>.bin (gros-boutiste)
dofile(os.getenv("VB_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mv = manager.machine.devices[":maincpu"].spaces["program"]
local IMS = {}; for x in string.gmatch(os.getenv("V_IM") or "", "%d+") do IMS[tonumber(x)] = true end
local kv = 0
emu.register_frame_done(function()
  kv = kv + 1; if not IMS[kv] then return end
  manager.machine.video:snapshot()
  local t = {}
  for a = 0x900000, 0x92FFFE, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
  local A = manager.machine.memory.shares[":cps_a_regs"]; local B = manager.machine.memory.shares[":cps_b_regs"]
  for o = 0, 0x3e, 2 do t[#t + 1] = string.pack(">I2", A:read_u16(o)) end
  for o = 0, 0x3e, 2 do t[#t + 1] = string.pack(">I2", B:read_u16(o)) end
  for a = 0x804200, 0x804206, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
  local f = io.open(string.format("%s/v_%d.bin", os.getenv("V_DIR"), kv), "wb"); f:write(table.concat(t)); f:close()
end)
