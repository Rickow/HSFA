local frames = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("OUT"), "w")
emu.register_frame_done(function()
  frames = frames + 1
  if frames % 50 == 0 then
    f:write(string.format("%4d : (A5)=%04x %04x %04x %04x  | FF0000=%04x %04x %04x %04x\n", frames,
      mem:read_u16(0xff8000), mem:read_u16(0xff8002), mem:read_u16(0xff8004), mem:read_u16(0xff8006),
      mem:read_u16(0xff0000), mem:read_u16(0xff0002), mem:read_u16(0xff0004), mem:read_u16(0xff0006)))
  end
  if frames == 1800 then f:close(); manager.machine:exit() end
end)
