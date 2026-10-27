local frames = 0
local target = tonumber(os.getenv("FRAME"))
local space = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local scr = nil
for tag, s in pairs(manager.machine.screens) do scr = s end
local lines = {}
tap = space:install_write_tap(0x804100, 0x80417f, "log", function(offset, data, mask)
  if frames == target then
    local ok, v = pcall(function() return scr:vpos() end)
    table.insert(lines, string.format("%06x %04x  ligne %s  pc %06x", offset, data, tostring(v), cpu.state["PC"].value))
  end
end)
emu.register_frame_done(function()
  frames = frames + 1
  if frames > target then
    local f = io.open(os.getenv("OUT"), "w"); f:write(table.concat(lines, "\n") .. "\n"); f:close(); manager.machine:exit()
  end
end)
