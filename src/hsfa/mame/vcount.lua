local frames = 0
local target = tonumber(os.getenv("FRAME"))
local space = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local n = {}; local pcs = {}
tapv = space:install_write_tap(0x900000, 0x92ffff, "cnt", function(offset, data, mask)
  if frames == target then
    local r = (offset - 0x900000) // 0x4000
    n[r] = (n[r] or 0) + 1
    local p = cpu.state["PC"].value; pcs[p] = (pcs[p] or 0) + 1
  end
end)
emu.register_frame_done(function()
  frames = frames + 1
  if frames > target then
    local f = io.open(os.getenv("OUT"), "w")
    for r, c in pairs(n) do f:write(string.format("zone %06x : %d ecritures\n", 0x900000 + r * 0x4000, c)) end
    for p, c in pairs(pcs) do if c > 20 then f:write(string.format("  pc %06x : %d\n", p, c)) end end
    f:close(); manager.machine:exit()
  end
end)
