-- JOURNAL DES REGISTRES CPS-A ($804100-$80413F) : derniere valeur ecrite par registre, a l'image FRAME
local frames = 0
local target = tonumber(os.getenv("FRAME"))
local space = manager.machine.devices[":maincpu"].spaces["program"]
local last = {}
tap = space:install_write_tap(0x804140, 0x80417f, "cpsa", function(offset, data, mask) last[offset] = data end)
emu.register_frame_done(function()
  frames = frames + 1
  if frames == target then
    local f = io.open(os.getenv("OUT"), "w")
    for a = 0x804140, 0x80417e, 2 do if last[a] then f:write(string.format("%06x %04x\n", a, last[a])) end end
    f:close(); manager.machine:exit()
  end
end)
