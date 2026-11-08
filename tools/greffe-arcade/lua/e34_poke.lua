-- (e34) enveloppe : charge PK_BASE, puis a chaque image de [PK_DEB, PK_FIN] ecrit les octets PK="adr=val,..." (68K)
dofile(os.getenv("PK_BASE"))
local mp = manager.machine.devices[":maincpu"].spaces["program"]; local kp = 0
local d, f = tonumber(os.getenv("PK_DEB") or "0"), tonumber(os.getenv("PK_FIN") or "0")
emu.register_frame_done(function()
  kp = kp + 1; if kp < d or kp > f then return end
  for a, v in string.gmatch(os.getenv("PK"), "(%x+)=(%x+)") do mp:write_u8(tonumber(a, 16), tonumber(v, 16)) end
end)
