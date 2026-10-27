-- (etape 3) enveloppe : charge LUA_BASE, puis a l'image VRAM_IMAGE ecrit les mots de $900000-$92FFFF (VRAM CPS) et
-- $804100-$80413F dans VRAM_OUT (binaire gros-boutiste, 0x30000 + 0x40 octets)
dofile(os.getenv("LUA_BASE"))
local mv = manager.machine.devices[":maincpu"].spaces["program"]; local iv = 0
emu.register_frame_done(function()
  iv = iv + 1
  if iv == tonumber(os.getenv("VRAM_IMAGE")) then
    local f = io.open(os.getenv("VRAM_OUT"), "wb"); local t = {}
    for a = 0x900000, 0x92FFFE, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
    for a = 0x804100, 0x80413E, 2 do t[#t + 1] = string.pack(">I2", mv:read_u16(a)) end
    f:write(table.concat(t)); f:close()
  end
end)
