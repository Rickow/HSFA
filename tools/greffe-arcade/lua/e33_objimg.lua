-- (e33) enveloppe (OI_PAS=n : aussi toutes les n images de la scene A) : charge OI_BASE (defaut lua/graine_pc.lua), puis aux images OI_IMAGES ("n,n") : capture + liste BRUTE des
-- objets (BANC_OMBRE, avant conversion) des deux pages -> OI_OUT (« e<empl> code attr x y adresse »), bases, $100, etats
dofile(os.getenv("OI_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mo = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("OI_OUT"), "w"); local IM = {}; local ko = 0
for x in string.gmatch(os.getenv("OI_IMAGES") or "", "%d+") do IM[tonumber(x)] = true end
local function liste(page)
  local t = {}; local om = BANC_OMBRE or {}
  for a = page, page + 0x7ff8, 8 do
    local x, y, c, at = om[a] or 0, om[a + 2] or 0, om[a + 4] or 0, om[a + 6] or 0
    if x == 0x8000 and y == 0x8000 then break end
    if x ~= 0 or y ~= 0 or c ~= 0 or at ~= 0 then t[#t + 1] = string.format("e%d %04x %04x %04x %04x %x", (y >> 13) & 7, c, at, x, y, a) end
  end
  return t
end
emu.register_frame_done(function()
  ko = ko + 1
  local pas = tonumber(os.getenv("OI_PAS") or "0")   -- OI_PAS=n : aussi toutes les n images de la scene A (fin)
  if not IM[ko] and not (pas > 0 and ko % pas == 0 and mo:read_u16(0xFF8000) == 2 and mo:read_u16(0xFF8004) == 0xA) then return end
  manager.machine.video:snapshot()
  local t0, t1 = liste(0x700000), liste(0x708000)
  fo:write(string.format("IMAGE %d etat %04x %04x %04x %04x decor %04x bases %04x %04x %04x pages %d %d\n", ko, mo:read_u16(0xFF8000),
    mo:read_u16(0xFF8004), mo:read_u16(0xFF8008), mo:read_u16(0xFF800C), mo:read_u16(0xFF8100), mo:read_u16(0x804200),
    mo:read_u16(0x804202), mo:read_u16(0x804204), #t0, #t1))
  for _, l in ipairs(t0) do fo:write("0 " .. l .. "\n") end
  -- OI_RAM="debut:fin:pas,..." : en-tetes (32 o) des objets actifs (octet +1 non nul) de ces reservoirs
  for a, b, p in string.gmatch(os.getenv("OI_RAM") or "", "(%x+):(%x+):(%x+)") do
    a, b, p = tonumber(a, 16), tonumber(b, 16), tonumber(p, 16)
    for o = a, b - 1, p do
      if mo:read_u8(o + 1) ~= 0 then
        local h = {}
        for i = 0, 31, 2 do h[#h + 1] = string.format("%04x", mo:read_u16(o + i)) end
        fo:write(string.format("R %06x %s\n", o, table.concat(h, " ")))
      end
    end
  end
  for _, l in ipairs(t1) do fo:write("1 " .. l .. "\n") end
  fo:flush()
end)
