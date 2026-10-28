-- (28/10) enveloppe : charge LUA_BASE, puis journal des ecritures sur plusieurs plages SURVS="ff814a:4,ff8162:2"
-- (image >= SURV_F0, au plus SURV_N par plage, ecritures de valeur identique comprises) -> SURV_OUT
dofile(os.getenv("LUA_BASE"))
local cw = manager.machine.devices[":maincpu"]; local mw = cw.spaces["program"]
local f0 = tonumber(os.getenv("SURV_F0") or "0"); local nmax = tonumber(os.getenv("SURV_N") or "200")
local fw = io.open(os.getenv("SURV_OUT"), "w"); local im = 0
emu.register_frame_done(function() im = im + 1 end)
_G.SURVS = {}
for a, l in string.gmatch(os.getenv("SURVS"), "(%x+):(%x+)") do
  local a0, n = tonumber(a, 16), 0
  _G.SURVS[#_G.SURVS + 1] = mw:install_write_tap(a0, a0 + tonumber(l, 16) - 1, "survs" .. a, function(o, d, m)
    if im < f0 or n >= nmax then return end
    if os.getenv("SURV_NZ") == "1" and (d & m) == 0 then return end
    n = n + 1
    local t = {}
    for _, r in ipairs({"D0","D1","A0","A1","A6"}) do t[#t + 1] = r .. "=" .. string.format("%08x", cw.state[r].value) end
    local sp = cw.state["SP"].value & 0xffffff; local p = {}
    for i = 0, 5 do p[#p + 1] = string.format("%04x", mw:read_u16(sp + 2 * i)) end
    fw:write(string.format("img %d pc=%06x %06x %04x m=%04x %s pile %s\n", im, cw.state["PC"].value & 0xffffff, o, d, m,
      table.concat(t, " "), table.concat(p, " "))); fw:flush()
  end)
end
