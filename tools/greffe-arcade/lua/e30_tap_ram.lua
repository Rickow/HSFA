-- (e30) enveloppe : charge LUA_BASE ; journalise TOUTES les écritures dans TR_A0-TR_A1 entre les images TR_F0 et TR_F1
-- (image, adresse, donnée, masque, PC, A6) -> TR_OUT ; au plus TR_N lignes
dofile(os.getenv("LUA_BASE"))
local ct = manager.machine.devices[":maincpu"]; local mt = ct.spaces["program"]
local f0, f1 = tonumber(os.getenv("TR_F0")), tonumber(os.getenv("TR_F1")); local nmax = tonumber(os.getenv("TR_N") or "20000")
local ft = io.open(os.getenv("TR_OUT"), "w"); local it, nt = 0, 0
emu.register_frame_done(function() it = it + 1 end)
_G.TRTAP = mt:install_write_tap(tonumber(os.getenv("TR_A0"), 16), tonumber(os.getenv("TR_A1"), 16), "tr", function(o, d, m)
  if it < f0 or it > f1 or nt >= nmax then return end
  nt = nt + 1
  local sp = (ct.state["SP"] or ct.state["A7"] or ct.state["ISP"]).value; local p = {}
  for i = 0, 7 do p[#p + 1] = string.format("%08x", mt:read_u32(sp + 4 * i)) end
  ft:write(string.format("%d %06x %x %x PC=%x A6=%x D0=%x pile %s\n", it, o, d, m, ct.state["PC"].value, ct.state["A6"].value, ct.state["D0"].value, table.concat(p, " "))); ft:flush()
end)
