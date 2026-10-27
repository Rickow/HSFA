-- (etape 3) enveloppe : charge LUA_BASE, puis a chaque lecture de l'opcode SONDE_PC (adresse 68K) apres l'image
-- SONDE_F0 : registres et 32 octets a l'adresse du registre SONDE_REG (defaut A1), SONDE_N premieres fois -> SONDE_OUT
dofile(os.getenv("LUA_BASE"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local pcs = tonumber(os.getenv("SONDE_PC"), 16); local nmax = tonumber(os.getenv("SONDE_N") or "5")
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local rg = os.getenv("SONDE_REG") or "A1"
local fs = io.open(os.getenv("SONDE_OUT"), "w"); local ns, img = 0, 0
emu.register_frame_done(function() img = img + 1 end)
_G.SONDE = os_:install_read_tap(pcs, pcs + 1, "sonde", function(o, d, m)
  if img < f0 or ns >= nmax then return end
  ns = ns + 1
  local t = {}
  for _, r in ipairs({"D0","D1","D2","D3","A0","A1","A2","A3","A4","A6"}) do t[#t + 1] = r .. "=" .. string.format("%08x", cs.state[r].value) end
  local a = cs.state[rg].value & 0xffffff; local b = {}
  for i = 0, 31 do b[#b + 1] = string.format("%02x", ms:read_u8(a + i)) end
  fs:write(string.format("img %d %s | %s@%06x %s\n", img, table.concat(t, " "), rg, a, table.concat(b, " "))); fs:flush()
end)
