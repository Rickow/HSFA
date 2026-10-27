local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local k, F = 0, nil
local ADR = tonumber(os.getenv("ADR") or "FF8294", 16)
CY = mem:install_write_tap(ADR, ADR + 1, "camy", function(o, d, m) if F then return F & 0xffff end end)
local seq = {0x10, 0x20, 0x30, 0x40, 0x60, 0xfff8, 0xfff0, 0xffe0}
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load("combat_0C") return end
  if k < 4 then return end
  local t = k - 4
  F = seq[t // 40 + 1]
  if not F then manager.machine:exit() return end
  mem:write_u16(ADR, F)
  if t % 40 == 39 then print(string.format("F=%04x  ram=%04x s1y=%04x s2y=%04x s3y=%04x rso=%04x", F, mem:read_u16(ADR), A:read_u16(0x0e), A:read_u16(0x12), A:read_u16(0x16), A:read_u16(0x20))) end
end)
