-- (28/10) enveloppe : charge LUA_BASE ; aux images VIDAGE_F="18100,20000" vide VIDAGE_MEM="ff8800:80,ff8a00:40" (mots) -> VIDAGE_OUT
dofile(os.getenv("LUA_BASE"))
local cv = manager.machine.devices[":maincpu"]; local mv = cv.spaces["program"]
local fv = io.open(os.getenv("VIDAGE_OUT"), "w"); local iv = 0; local quand = {}
for f in string.gmatch(os.getenv("VIDAGE_F") or "", "%d+") do quand[tonumber(f)] = true end
emu.register_frame_done(function()
  iv = iv + 1
  if not quand[iv] then return end
  for a, l in string.gmatch(os.getenv("VIDAGE_MEM") or "", "(%x+):(%x+)") do
    local a0 = tonumber(a, 16); local w = {}
    for i = 0, tonumber(l, 16) - 1, 2 do w[#w + 1] = string.format("%04x", mv:read_u16(a0 + i)) end
    fv:write(string.format("img %d %06x : %s\n", iv, a0, table.concat(w, " ")))
  end
  fv:flush()
end)
