-- (etape 2) enveloppe : charge LUA_BASE puis, a l'image LIRE_IMAGE, ecrit dans LIRE_OUT les octets 68K LIRE_ADR (liste a,b,c)
dofile(os.getenv("LUA_BASE"))
local m3 = manager.machine.devices[":maincpu"].spaces["program"]
local n3 = 0
emu.register_frame_done(function()
  n3 = n3 + 1
  if n3 == tonumber(os.getenv("LIRE_IMAGE")) then
    local f = io.open(os.getenv("LIRE_OUT"), "w")
    for a in string.gmatch(os.getenv("LIRE_ADR"), "%x+") do
      local x = tonumber(a, 16); f:write(string.format("%06x %02x\n", x, m3:read_u8(x)))
    end
    f:close()
  end
end)
