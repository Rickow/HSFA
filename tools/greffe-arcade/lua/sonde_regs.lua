-- (etape 7) enveloppe : charge LUA_BASE ; a chaque lecture de l'opcode SONDE_PC apres SONDE_F0 (N fois) :
-- D0-D7, A0-A7, et SONDE_MEM="A6:0:40,A3:0:20,ff8000:0:10" (registre ou adresse hexa : decalage : longueur, mots)
dofile(os.getenv("LUA_BASE"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local pcs = tonumber(os.getenv("SONDE_PC"), 16); local nmax = tonumber(os.getenv("SONDE_N") or "5")
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local fs = io.open(os.getenv("SONDE_OUT"), "w"); local ns, img = 0, 0
emu.register_frame_done(function() img = img + 1 end)
_G.SONDER = os_:install_read_tap(pcs, pcs + 1, "sonder", function(o, d, m)
  if img < f0 or ns >= nmax then return end
  ns = ns + 1
  local t = {}
  for _, r in ipairs({"D0","D1","D2","D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6","SP"}) do
    t[#t + 1] = r .. "=" .. string.format("%08x", cs.state[r].value) end
  fs:write(string.format("img %d %s\n", img, table.concat(t, " ")))
  for b, dc, ln in string.gmatch(os.getenv("SONDE_MEM") or "", "(%w+):(%x+):(%x+)") do
    local base = cs.state[b] and cs.state[b].value or tonumber(b, 16)
    local a = (base + tonumber(dc, 16)) & 0xffffff; local w = {}
    for i = 0, tonumber(ln, 16) - 1, 2 do w[#w + 1] = string.format("%04x", ms:read_u16(a + i)) end
    fs:write(string.format("  %s+%s (%06x) : %s\n", b, dc, a, table.concat(w, " ")))
  end
  fs:flush()
end)
