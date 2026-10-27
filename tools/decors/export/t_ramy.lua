local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local k, y0 = 0, nil
local J1, J2 = 0xFF8400, 0xFF8800
local snaps = {}
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load("combat_0C") return end
  if k < 4 then return end
  local t = k - 4
  if not y0 then y0 = mem:read_u16(J1 + 0x14) end
  local dy = (t >= 60) and 0x100 or 0
  mem:write_u16(J1 + 0x14, y0 + dy); mem:write_u16(J2 + 0x14, y0 + dy)
  mem:write_u16(J1 + 0x10, 0x250); mem:write_u16(J2 + 0x10, 0x2b0)
  if t == 50 or t == 150 then
    local f = io.open(string.format("cap/ram_%d.bin", t), "wb"); local s = {}
    for a = 0xFF0000, 0xFFFFFE, 2 do s[#s+1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(s)); f:close()
  end
  if t == 151 then manager.machine:exit() end
end)
