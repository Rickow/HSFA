local frames = 0
emu.register_frame_done(function()
  frames = frames + 1
  if frames == 100 then
    manager.machine.debugger:command("trace <workspace>/work/mame/instr2.tr,maincpu,noloop")
  end
  if frames >= 102 then manager.machine.debugger:command("traceoff maincpu"); manager.machine:exit() end
end)
