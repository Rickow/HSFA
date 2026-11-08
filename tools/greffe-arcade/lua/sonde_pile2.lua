-- (28/10) enveloppe : charge LUA_BASE ; a l'opcode SONDE_PC apres SONDE_F0 : registres + 40 mots de pile (N fois)
dofile(os.getenv("LUA_BASE"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local nmax = tonumber(os.getenv("SONDE_N") or "3")
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local fs = io.open(os.getenv("SONDE_OUT"), "w"); local img = 0
emu.register_frame_done(function() img = img + 1 end)
_G.SONDEP2 = {}
for a in string.gmatch(os.getenv("SONDE_PC"), "%x+") do
  local pcs, ns = tonumber(a, 16), 0
  _G.SONDEP2[#_G.SONDEP2 + 1] = os_:install_read_tap(pcs, pcs + 1, "sondep2" .. a, function(o, d, m)
    if img < f0 or ns >= nmax or (cs.state["PC"].value & 0xffffff) ~= pcs then return end
    ns = ns + 1
    local sp = cs.state["SP"].value & 0xffffff; local p, r = {}, {}
    for i = 0, 39 do p[#p + 1] = string.format("%04x", ms:read_u16(sp + 2 * i)) end
    for _, n in ipairs({"D0","D1","D2","A0","A1","A2","A3","A4","A5","A6"}) do r[#r + 1] = string.format("%s=%08x", n, cs.state[n].value) end
    fs:write(string.format("img %d pc=%06x %s SP=%06x\n  pile %s\n", img, pcs, table.concat(r, " "), sp, table.concat(p, " "))); fs:flush()
  end)
end
