-- (etape 3) enveloppe : charge LUA_BASE puis, aux images VRAM_IMAGES (liste), vide VRAM CPS ($900000-$92FFFF) et la
-- RAM des sprites ($700000-$701FFF) dans VRAM_OUT.<image>
dofile(os.getenv("LUA_BASE"))
local mv = manager.machine.devices[":maincpu"].spaces["program"]; local iv = 0; local L = {}
for x in string.gmatch(os.getenv("VRAM_IMAGES"), "%d+") do L[tonumber(x)] = true end
emu.register_frame_done(function()
  iv = iv + 1
  if L[iv] then
    local f = io.open(os.getenv("VRAM_OUT") .. "." .. iv, "wb"); local t = {}
    for a = 0x900000, 0x92FFFE, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
    for a = 0x700000, 0x701FFE, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
    f:write(table.concat(t)); f:close()
  end
end)
