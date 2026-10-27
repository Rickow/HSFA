local frames=0; local started=false
emu.register_frame_done(function()
  frames=frames+1
  if not started then
    local d=manager.machine.debugger
    d:command('bpset 216be,1,{logerror "B1 f=%d D0=%x A4=%x\\n",frame,d0,a4;g}')
    d:command('bpset 216d4,1,{logerror "B2 f=%d D0=%x A0=%x\\n",frame,d0,a0;g}')
    d:command('bpset 216e4,1,{logerror "B3 f=%d D0=%x A0=%x\\n",frame,d0,a0;g}')
    d:command("go"); started=true
  end
  if frames>=732 then manager.machine:exit() end
end)
