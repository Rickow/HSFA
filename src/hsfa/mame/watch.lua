local frames = 0
local started = false
emu.register_frame_done(function()
  frames = frames + 1
  if not started then
    manager.machine.debugger:command("trace <workspace>/work/mame/watch.tr,maincpu,noloop")
    manager.machine.debugger:command("traceoff maincpu")
    manager.machine.debugger:command('wpset ff8000,2,w,1,{tracelog "image=%d pc=%x ecrit=%x\\n",frame,pc,wpdata;g}')
    manager.machine.debugger:command("go")
    started = true
  end
  if frames >= 400 then manager.machine:exit() end
end)
