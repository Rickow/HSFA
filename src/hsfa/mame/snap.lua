local frames = 0
emu.register_frame_done(function()
  frames = frames + 1
  if frames == 900 or frames == 1800 then
    manager.machine.video:snapshot()
  end
  if frames == 1800 then manager.machine:exit() end
end)
