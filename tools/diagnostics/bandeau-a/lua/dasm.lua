local f=0
emu.register_frame_done(function() f=f+1; if f==2 then
  manager.machine.debugger:command("dasm " .. os.getenv("DOUT") .. "," .. os.getenv("DA") .. "," .. os.getenv("DL"))
  manager.machine:exit() end end)
