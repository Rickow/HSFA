local frames = 0
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local log = io.open("<workspace>/work/mame/trace.txt", "w")
emu.register_frame_done(function()
  frames = frames + 1
  local s = cpu.state
  local pc = s["PC"].value
  local exc = pc >= 0xA00 and pc < 0xA80
  if frames % 60 == 0 or frames < 4 or exc then
    local sp = s["SP"].value
    local extra = ""
    if exc then
      extra = string.format(" EXCEPTION %d ; pile : %04x %04x %04x %04x %04x", (pc-0xA00)//2,
        mem:read_u16(sp), mem:read_u16(sp+2), mem:read_u16(sp+4), mem:read_u16(sp+6), mem:read_u16(sp+8))
    end
    log:write(string.format("image %5d PC=%06x SR=%04x SP=%06x A5=%06x%s\n", frames, pc, s["SR"].value, sp, s["A5"].value, extra))
    log:flush()
    if exc then manager.machine.video:snapshot(); log:close(); manager.machine:exit() end
  end
  if frames == 300 or frames == 900 then manager.machine.video:snapshot() end
  if frames == 1800 then manager.machine.video:snapshot(); log:close(); manager.machine:exit() end
end)
