local frames=0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("OUT"), "w")
local a0 = tonumber(os.getenv("F0")); local a1 = tonumber(os.getenv("F1")); local B = tonumber(os.getenv("OBJ") or "0xff8400")
emu.register_frame_done(function()
  frames=frames+1
  if frames>=a0 and frames<=a1 then
    local s = string.format("%5d : ", frames)
    for o=0,0x13 do s = s .. string.format("%02x", mem:read_u8(B+o)) end
    s = s .. " | 200:"
    for o=0x200,0x20b do s = s .. string.format("%02x", mem:read_u8(B+o)) end
    s = s .. string.format(" | 220=%08x 230=%08x 1c=%08x", mem:read_u32(B+0x220), mem:read_u32(B+0x230), mem:read_u32(B+0x1c))
    f:write(s .. "\n")
  end
  if frames>a1 then f:close(); manager.machine:exit() end
end)
