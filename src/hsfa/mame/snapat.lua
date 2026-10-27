local frames = 0
local want = {}; local last = 0
for n in string.gmatch(os.getenv("SNAPS"), "%d+") do want[tonumber(n)] = true; if tonumber(n) > last then last = tonumber(n) end end
emu.register_frame_done(function()
  frames = frames + 1
  if want[frames] then manager.machine.video:snapshot() end
  if frames >= last then manager.machine:exit() end
end)
