local frames=0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("OUT"), "w")
local a0 = tonumber(os.getenv("F0")); local a1 = tonumber(os.getenv("F1"))
emu.register_frame_done(function()
  frames=frames+1
  if frames>=a0 and frames<=a1 then
    local s = string.format("%5d :", frames)
    for a=0xff8400,0xff840e,2 do s = s .. string.format(" %04x", mem:read_u16(a)) end
    s = s .. " | 8800:"
    for a=0xff8800,0xff880e,2 do s = s .. string.format(" %04x", mem:read_u16(a)) end
    s = s .. string.format(" | mode %04x %04x %04x", mem:read_u16(0xff8000), mem:read_u16(0xff8002), mem:read_u16(0xff8004))
    f:write(s .. "\n")
  end
  if frames>a1 then f:close(); manager.machine:exit() end
end)
