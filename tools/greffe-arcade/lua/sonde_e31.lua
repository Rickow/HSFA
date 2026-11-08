-- (e31) enveloppe : LUA_BASE (graine_pc.lua) + a chaque lecture de l'opcode SONDE_PC (apres SONDE_F0, N fois) :
-- D0 D1 A0 A1 A6 et 64 octets de l'objet en A6 -> SONDE_OUT
dofile(os.getenv("LUA_BASE"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local pcs = tonumber(os.getenv("SONDE_PC"), 16); local nmax = tonumber(os.getenv("SONDE_N") or "200")
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local fs = io.open(os.getenv("SONDE_OUT"), "w"); local ns, img = 0, 0
emu.register_frame_done(function() img = img + 1 end)
_G.SONDE31 = os_:install_read_tap(pcs, pcs + 1, "sonde31", function(o, d, m)
  if img < f0 or ns >= nmax then return end
  ns = ns + 1
  local a6 = cs.state["A6"].value & 0xffffff; local t = {}
  if a6 >= 0xff0000 then for i = 0, 63 do t[#t + 1] = string.format("%02x", ms:read_u8(a6 + i)) end end
  fs:write(string.format("img %d D0=%08x D1=%08x A0=%08x A1=%08x A6=%08x $100=%04x obj %s\n", img, cs.state["D0"].value,
    cs.state["D1"].value, cs.state["A0"].value, cs.state["A1"].value, a6, ms:read_u16(0xFF8100), table.concat(t))); fs:flush()
end)
