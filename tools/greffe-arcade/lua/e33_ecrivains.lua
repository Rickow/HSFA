-- (e33) enveloppe : charge LUA_BASE, puis RECENSEMENT des écrivains d'une plage EC="adr:long" (PC → nombre, 1re/dernière
-- image, adresses min/max, 1re donnée) ; relevé réécrit toutes les EC_PAS images (défaut 200) et à la sortie -> EC_OUT.
-- EC_F0 : image de début.
dofile(os.getenv("LUA_BASE"))
local cw = manager.machine.devices[":maincpu"]; local mw = cw.spaces["program"]
local a, l = string.match(os.getenv("EC"), "(%x+):(%x+)"); a = tonumber(a, 16); l = tonumber(l, 16)
local f0 = tonumber(os.getenv("EC_F0") or "0"); local pas = tonumber(os.getenv("EC_PAS") or "200")
local T, im = {}, 0
local function vide()
  local fw = io.open(os.getenv("EC_OUT"), "w"); local k = {}
  for pc, e in pairs(T) do k[#k + 1] = pc end
  table.sort(k)
  fw:write(string.format("image %d\n", im))
  for _, pc in ipairs(k) do local e = T[pc]
    fw:write(string.format("pc=%06x n=%d img=%d-%d adr=%06x-%06x 1er=%06x:%04x A6=%06x $100=%04x\n", pc, e.n, e.i0, e.i1, e.amin, e.amax, e.a0, e.d0, e.a6, e.s)) end
  fw:close()
end
emu.register_frame_done(function() im = im + 1; if im % pas == 0 then vide() end end)
emu.add_machine_stop_notifier(vide)
_G.EC_TAP = mw:install_write_tap(a, a + l - 1, "e33ec", function(o, d, m)
  if im < f0 then return end
  local pc = cw.state["PC"].value & 0xffffff; local e = T[pc]
  if not e then e = {n = 0, i0 = im, amin = o, amax = o, a0 = o, d0 = d, a6 = cw.state["A6"].value & 0xffffff, s = mw:read_u16(0xFF8100)}; T[pc] = e end
  e.n = e.n + 1; e.i1 = im; if o < e.amin then e.amin = o end; if o > e.amax then e.amax = o end
end)
