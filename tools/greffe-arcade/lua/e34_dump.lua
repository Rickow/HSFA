-- (e34) enveloppe : charge DU_BASE ; a l'image DU_IM, ecrit la plage 68K DU="adr:long" (octets dans l'ordre 68K) dans DU_OUT
dofile(os.getenv("DU_BASE"))
local md = manager.machine.devices[":maincpu"].spaces["program"]; local kd = 0
emu.register_frame_done(function()
  kd = kd + 1; if kd ~= tonumber(os.getenv("DU_IM")) then return end
  local a, l = string.match(os.getenv("DU"), "(%x+):(%x+)"); a = tonumber(a, 16); l = tonumber(l, 16)
  local t = {}; for x = a, a + l - 1 do t[#t + 1] = string.char(md:read_u8(x)) end
  local f = io.open(os.getenv("DU_OUT"), "wb"); f:write(table.concat(t)); f:close()
end)
