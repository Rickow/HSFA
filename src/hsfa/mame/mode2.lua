local frames = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("OUT"), "w")
local last = ""
emu.register_frame_done(function()
  frames = frames + 1
  local s = string.format("%04x %04x %04x %04x %04x %04x %04x %04x", mem:read_u16(0xff8000), mem:read_u16(0xff8002), mem:read_u16(0xff8004),
     mem:read_u16(0xff8006), mem:read_u16(0xff8008), mem:read_u16(0xff800a), mem:read_u16(0xff800c), mem:read_u16(0xff800e))
  local key = s:sub(1,14) .. s:sub(20,39)
  if key ~= last then f:write(string.format("%5d : %s\n", frames, s)); last = key end
  if frames == tonumber(os.getenv("NF")) then f:close(); manager.machine:exit() end
end)
