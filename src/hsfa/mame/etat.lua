local frames = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
emu.register_frame_done(function()
  frames = frames + 1
  if frames == 5 or frames == 100 then
    local f = io.open("<workspace>/work/mame/etat.txt", "a")
    f:write(string.format("== image %d ; CURSLOT=%04x FLAG=%04x SCHEDSP=%08x\n", frames, mem:read_u16(0x663884), mem:read_u16(0x663888), mem:read_u32(0x663880)))
    for s = 0, 15 do
      local t = 0xFF0184 + s*0x20
      local w = {}
      for k = 0, 15 do w[#w+1] = string.format("%04x", mem:read_u16(t + 2*k)) end
      f:write(string.format(" tache %2d : %s | noyau pile=%08x entree=%08x\n", s, table.concat(w, " "), mem:read_u32(0x663800+8*s), mem:read_u32(0x663804+8*s)))
    end
    f:close()
  end
  if frames == 100 then manager.machine:exit() end
end)
