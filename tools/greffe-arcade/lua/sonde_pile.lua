-- (etape 4) enveloppe : charge LUA_BASE ; a chaque lecture de l'opcode SONDE_PC apres SONDE_F0 : 12 mots de pile (N fois)
dofile(os.getenv("LUA_BASE"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local pcs = tonumber(os.getenv("SONDE_PC"), 16); local nmax = tonumber(os.getenv("SONDE_N") or "5")
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local fs = io.open(os.getenv("SONDE_OUT"), "w"); local ns, img = 0, 0
emu.register_frame_done(function() img = img + 1 end)
_G.SONDEP = os_:install_read_tap(pcs, pcs + 1, "sondep", function(o, d, m)
  if img < f0 or ns >= nmax then return end
  ns = ns + 1
  local sp = cs.state["SP"].value & 0xffffff; local p = {}
  for i = 0, 15 do p[#p + 1] = string.format("%04x", ms:read_u16(sp + 2 * i)) end
  fs:write(string.format("img %d D0=%08x D1=%08x A6=%08x pile %s\n", img, cs.state["D0"].value, cs.state["D1"].value, cs.state["A6"].value, table.concat(p, " "))); fs:flush()
end)
