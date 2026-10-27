local frames = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
emu.register_frame_done(function()
  frames = frames + 1
  if frames == 900 then
    local f = io.open(os.getenv("OUT"), "w")
    for base = 0x900000, 0x92ffff, 0x4000 do
      local nz = 0
      for a = base, base + 0x3ffe, 2 do if mem:read_u16(a) ~= 0 then nz = nz + 1 end end
      f:write(string.format("VRAM %06x : %5d mots non nuls\n", base, nz))
    end
    for _, base in ipairs({0x700000, 0x708000, 0xff0000, 0xff8000}) do
      local nz = 0
      for a = base, base + 0x1ffe, 2 do if mem:read_u16(a) ~= 0 then nz = nz + 1 end end
      f:write(string.format("zone %06x : %5d mots non nuls\n", base, nz))
    end
    f:close(); manager.machine:exit()
  end
end)
