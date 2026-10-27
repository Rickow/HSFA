local started = false
local frames = 0
emu.register_frame_done(function()
  frames = frames + 1
  if not started then
    manager.machine.debugger:command("trace <workspace>/work/mame/instr.tr,maincpu,noloop")
    manager.machine.debugger:command("go")
    started = true
  end
  if frames >= 15 then manager.machine.debugger:command("traceoff maincpu"); manager.machine:exit() end
end)
