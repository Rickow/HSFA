local mem = manager.machine.devices[":maincpu"].spaces["program"]
local G = manager.machine.memory.shares[":gfxram"]
local k = 0
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load("combat_0C") return end
  if k == 5 then
    local r = mem:read_range(0x904000, 0x90401f, 16)
    local a = {}; for i = 1, #r do a[#a+1] = string.format("%02x", r:byte(i)) end
    print("RR", #r, table.concat(a, " "))
    local b = {}; for x = 0x904000, 0x90401e, 2 do b[#b+1] = string.format("%04x", mem:read_u16(x)) end
    print("U16", table.concat(b, " "))
    local c = {}; for x = 0x4000, 0x401e, 2 do c[#c+1] = string.format("%04x", G:read_u16(x)) end
    print("SH", table.concat(c, " "))
    local t0 = os.clock(); local s = 0
    for x = 0, 0xbffe, 2 do s = s + G:read_u16(x) end
    print("time 24k share reads", os.clock() - t0)
    t0 = os.clock(); for i = 1, 10 do r = mem:read_range(0x900000, 0x92ffff, 16) end
    print("time read_range x10", os.clock() - t0, #r)
    manager.machine:exit()
  end
end)
