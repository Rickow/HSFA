-- (e33) enveloppe : charge LUA_BASE, puis journal de chaque entrée à l'adresse 68K AP_PC (espace opcodes) : image, états
-- A5+0/4/8/C, bases du fork $804200-$804204, décor $100, adresse de retour (pile) -> AP_OUT (AP_N entrées au plus)
dofile(os.getenv("LUA_BASE"))
local ca = manager.machine.devices[":maincpu"]; local ma = ca.spaces["program"]; local oa = ca.spaces["opcodes"] or ma
local fa = io.open(os.getenv("AP_OUT"), "w"); local na, ia, nmax = 0, 0, tonumber(os.getenv("AP_N") or "500")
emu.register_frame_done(function() ia = ia + 1 end)
_G.AP_TAPS = {}
for x in string.gmatch(os.getenv("AP_PC"), "%x+") do
  local pc = tonumber(x, 16)
  _G.AP_TAPS[#_G.AP_TAPS + 1] = oa:install_read_tap(pc, pc + 1, "ap" .. x, function(o, d, m)
    if na >= nmax then return end
    na = na + 1
    local sp = ca.state["SP"].value & 0xffffff
    fa:write(string.format("img %d pc=%06x etat %04x %04x %04x %04x bases %04x %04x %04x decor %04x ret %04x%04x %04x%04x\n", ia, pc,
      ma:read_u16(0xFF8000), ma:read_u16(0xFF8004), ma:read_u16(0xFF8008), ma:read_u16(0xFF800C), ma:read_u16(0x804200),
      ma:read_u16(0x804202), ma:read_u16(0x804204), ma:read_u16(0xFF8100), ma:read_u16(sp), ma:read_u16(sp + 2), ma:read_u16(sp + 4), ma:read_u16(sp + 6)))
    fa:flush()
  end)
end
