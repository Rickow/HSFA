-- (e28) enveloppe : REC_BASE (defaut graine_pc.lua) ; a l'image CH_IM : mots $FF6E88-$FF6EC0 et objets de $FF0000-$FFFFFF
-- (pas de $20) dont le mot +$1A vaut $2000 (emplacement 1) : adresse, mots +0..+$1F -> CH_OUT
dofile(os.getenv("REC_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mc = manager.machine.devices[":maincpu"].spaces["program"]; local kc = 0; local im = tonumber(os.getenv("CH_IM"))
emu.register_frame_done(function()
  kc = kc + 1; if kc ~= im then return end
  local f = io.open(os.getenv("CH_OUT"), "w")
  local t = {}; for a = 0xFF6E80, 0xFF6EC0, 2 do t[#t + 1] = string.format("%04x", mc:read_u16(a)) end
  f:write("A5+6E80 " .. table.concat(t, " ") .. "\n")
  for a = 0xFF0000, 0xFFFFE0, 0x20 do
    if mc:read_u16(a + 0x1A) == 0x2000 and mc:read_u8(a + 1) ~= 0 then
      local s = {}; for i = 0, 0x3e, 2 do s[#s + 1] = string.format("%04x", mc:read_u16(a + i)) end
      f:write(string.format("%06x %s\n", a, table.concat(s, " ")))
    end
  end
  f:close()
end)
