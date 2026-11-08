-- (e34) enveloppe : charge OB_BASE (defaut graine_pc.lua), puis a chaque changement de $FF8004 (scene) et aux images OB_IMAGES,
-- ecrit dans OB_OUT les octets OB_ADR="adr:long,..." (68K)
dofile(os.getenv("OB_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mo = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("OB_OUT"), "w"); local IM = {}; local ko, sc = 0, -1
for x in string.gmatch(os.getenv("OB_IMAGES") or "", "%d+") do IM[tonumber(x)] = true end
emu.register_frame_done(function()
  ko = ko + 1
  local s = mo:read_u16(0xFF8004) * 65536 + mo:read_u16(0xFF8008)
  if s == sc and not IM[ko] then return end
  sc = s
  local t = {}
  for a, l in string.gmatch(os.getenv("OB_ADR"), "(%x+):(%x+)") do
    a, l = tonumber(a, 16), tonumber(l, 16); local h = {}
    for i = 0, l - 1 do h[#h + 1] = string.format("%02x", mo:read_u8(a + i)) end
    t[#t + 1] = string.format("%06x=%s", a, table.concat(h))
  end
  fo:write(string.format("%d etat %04x %04x %04x %s\n", ko, mo:read_u16(0xFF8000), mo:read_u16(0xFF8004), mo:read_u16(0xFF8008), table.concat(t, " ")))
  fo:flush()
end)
