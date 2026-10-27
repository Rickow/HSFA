local frames = 0
local space = manager.machine.devices[":maincpu"].spaces["program"]
emu.register_frame_done(function()
  frames = frames + 1
  if frames == 649 then
    local d = io.open(os.getenv("SRC"), "rb"):read("a")
    local o = 0x40
    for a = 0x900000, 0x92fffe, 2 do
      local hi, lo = d:byte(o + 1, o + 2); space:write_u16(a, hi * 256 + lo); o = o + 2
    end
  end
  if frames == 650 then manager.machine.video:snapshot() end
  if frames == 651 then manager.machine:exit() end
end)
