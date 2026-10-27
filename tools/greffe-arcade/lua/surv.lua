-- (etape 3) enveloppe : charge LUA_BASE, puis journal des ecritures (PC, adresse, donnee, A0-A6) sur SURV2="adr:long:image"
-- (n premieres : SURV2_N) -> SURV2_OUT
dofile(os.getenv("LUA_BASE"))
local cw = manager.machine.devices[":maincpu"]; local mw = cw.spaces["program"]
local a, l, f0 = string.match(os.getenv("SURV2"), "(%x+):(%x+):(%d+)"); a = tonumber(a, 16); l = tonumber(l, 16); f0 = tonumber(f0)
local fw = io.open(os.getenv("SURV2_OUT"), "w"); local nw, im = 0, 0; local nmax = tonumber(os.getenv("SURV2_N") or "20")
emu.register_frame_done(function() im = im + 1 end)
_G.SURV2 = mw:install_write_tap(a, a + l - 1, "surv2", function(o, d, m)
  if im < f0 or nw >= nmax then return end
  nw = nw + 1
  local t = {}
  for _, r in ipairs({"D0","D1","A0","A1","A2","A3","A4","A6"}) do t[#t + 1] = r .. "=" .. string.format("%08x", cw.state[r].value) end
  local sp = cw.state["SP"].value & 0xffffff; local p = {}
  for i = 0, 11 do p[#p + 1] = string.format("%04x", mw:read_u16(sp + 2 * i)) end
  fw:write(string.format("img %d pc=%06x %06x %04x %s pile %s\n", im, cw.state["PC"].value & 0xffffff, o, d, table.concat(t, " "), table.concat(p, " "))); fw:flush()
end)
