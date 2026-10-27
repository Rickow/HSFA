local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local k = 0
local cands = {0xFF8214, 0xFF8224, 0xFF822C, 0xFF8024, 0xFF8028, 0xFF802C, 0xFF802E, 0xFF82A4, 0xFF82AC, 0xFF8314, 0xFF8394}
local cur = nil
local taps = {}
for i, a in ipairs(cands) do
  taps[i] = mem:install_write_tap(a, a + 1, "c" .. i, function(o, d, m) if cur == a then return 0x30 end end)
end
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load("combat_0C") return end
  if k < 4 then return end
  local t = k - 4
  local i = t // 60 + 1
  cur = cands[i]
  if not cur then manager.machine:exit() return end
  mem:write_u16(cur, 0x30)
  if t % 60 == 59 then print(string.format("%x : s1y=%04x s2y=%04x s3y=%04x rso=%04x s3x=%04x", cur, A:read_u16(0x0e), A:read_u16(0x12), A:read_u16(0x16), A:read_u16(0x20), A:read_u16(0x14))) end
end)
