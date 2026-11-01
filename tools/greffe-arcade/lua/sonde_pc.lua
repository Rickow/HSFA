-- (e27) enveloppe : graine_pc.lua (donc LUA_BASE) + sonde de PC : a chaque passage sur une adresse de SONDE_PCS (hexa,
-- virgules) a partir de l'image SONDE_F0, si A6 = SONDE_A6 (optionnel) : registres A0/D0/A6 et 16 octets en A0
-- (journal SONDE_OUT, SONDE_N lignes au plus).
dofile("<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]; local os_ = cs.spaces["opcodes"] or ms
local f0 = tonumber(os.getenv("SONDE_F0") or "0"); local a6 = tonumber(os.getenv("SONDE_A6") or "", 16)
local fo = io.open(os.getenv("SONDE_OUT"), "w"); local ks = 0; local nmax = tonumber(os.getenv("SONDE_N") or "200"); local n = 0
emu.register_frame_done(function() ks = ks + 1 end)
_G.SONDES = {}
for x in string.gmatch(os.getenv("SONDE_PCS") or "", "%x+") do
  local pc = tonumber(x, 16)
  _G.SONDES[#_G.SONDES + 1] = os_:install_read_tap(pc, pc + 1, "sonde" .. x, function(o, d, m)
    if ks < f0 or n >= nmax or (cs.state["PC"].value & 0xffffff) ~= pc then return end
    if a6 and (cs.state["A6"].value & 0xffffff) ~= a6 then return end
    n = n + 1
    local A0 = cs.state["A0"].value & 0xffffff; local t = {}
    for i = 0, 7 do t[#t + 1] = string.format("%04x", ms:read_u16((A0 + 2 * i) & 0xfffffe)) end
    fo:write(string.format("%d pc=%06x A0=%08x D0=%08x D1=%08x A6=%08x [A0] %s\n", ks, pc, cs.state["A0"].value, cs.state["D0"].value,
      cs.state["D1"].value, cs.state["A6"].value, table.concat(t, " "))); fo:flush()
  end)
end
-- SONDE_LECT="adresse:longueur" : prise de LECTURE (donnees) a partir de SONDE_F0 : image, PC, adresse, donnee, A0, A6
if os.getenv("SONDE_LECT") then
  local a, l = string.match(os.getenv("SONDE_LECT"), "(%x+):(%x+)"); a = tonumber(a, 16); l = tonumber(l, 16)
  _G.SONDE_L = ms:install_read_tap(a, a + l - 1, "sondel", function(o, d, m)
    if ks < f0 or n >= nmax then return end
    n = n + 1
    fo:write(string.format("%d LIT pc=%06x %06x %04x %04x A0=%08x A6=%08x\n", ks, cs.state["PC"].value & 0xffffff, o, d, m,
      cs.state["A0"].value, cs.state["A6"].value)); fo:flush()
  end)
end
