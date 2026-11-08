-- (e30) enveloppe : charge LUA_BASE (tournee_arcade.lua) ; aux images V_IM="n,n" : capture, liste BRUTE des objets
-- (BANC_OMBRE, 2 pages) et vidage de la RAM de travail $FF0000-$FFFFFF -> V_DIR/im_<n>.obj, im_<n>.ram
dofile(os.getenv("LUA_BASE"))
local mv = manager.machine.devices[":maincpu"].spaces["program"]
local IMS = {}; for x in string.gmatch(os.getenv("V_IM") or "", "%d+") do IMS[tonumber(x)] = true end
local D = os.getenv("V_DIR"); local kv = 0
emu.register_frame_done(function()
  kv = kv + 1; if not IMS[kv] then return end
  manager.machine.video:snapshot()
  local f = io.open(string.format("%s/im_%d.obj", D, kv), "w")
  f:write(string.format("etat %04x %04x %04x %04x\n", mv:read_u16(0xFF8000), mv:read_u16(0xFF8004), mv:read_u16(0xFF8008), mv:read_u16(0xFF800C)))
  f:write(string.format("bases %04x %04x %04x couches %04x cpsa %04x %04x %04x %04x\n", mv:read_u16(0x804200), mv:read_u16(0x804202), mv:read_u16(0x804204),
    mv:read_u16(0x804166), mv:read_u16(0x804102), mv:read_u16(0x804104), mv:read_u16(0x804106), mv:read_u16(0x804108)))
  local om = BANC_OMBRE or {}
  for _, page in ipairs({0x700000, 0x708000}) do
    for a = page, page + 0x7ff8, 8 do
      local x, y, c, at = om[a] or 0, om[a + 2] or 0, om[a + 4] or 0, om[a + 6] or 0
      if (y & 0xff00) == 0xff00 and x == 0 then end
      if x == 0x8000 and y == 0x8000 then f:write(string.format("FIN %x\n", a)); break end
      if x ~= 0 or y ~= 0 or c ~= 0 or at ~= 0 then
        f:write(string.format("%x e%d %04x %04x %04x %04x\n", a, (y >> 13) & 7, c, at, x, y)) end
    end
  end
  f:close()
  local r = io.open(string.format("%s/im_%d.ram", D, kv), "wb")
  local t = {}
  for a = 0xFF0000, 0xFFFFFF, 2 do local w = mv:read_u16(a); t[#t + 1] = string.char(w >> 8, w & 0xff) end
  r:write(table.concat(t)); r:close()
end)
