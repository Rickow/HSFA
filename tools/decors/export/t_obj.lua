local mem = manager.machine.devices[":maincpu"].spaces["program"]
local n, k = 0, 0
local lo, hi = 0xffffff, 0
OT = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) n = n + 1; if o < lo then lo = o end; if o > hi then hi = o end; return 0xff00 end)
local O = manager.machine.memory.shares[":output"]
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load("combat_0C") return end
  if k > 3 and k < 8 then
    local s = {}; for o = 0, 10, 2 do s[#s+1] = string.format("%04x", O:read_u16(o)) end
    print("frame", k, "taps", n, string.format("%x-%x", lo, hi), "output", table.concat(s, " "), string.format("obj0 %04x %04x %04x %04x", mem:read_u16(0x700000), mem:read_u16(0x700002), mem:read_u16(0x708000), mem:read_u16(0x708002)))
    n = 0
  end
  if k == 8 then manager.machine:exit() end
end)
