-- (31/10, e22) enveloppe : charge FB_SUITE ; toute ecriture de l'octet $B (mot $A, masque 00ff) d'un objet de
-- $FFBB80-$FFBFFF entre les images FB_F0 et FB_F1 est remplacee par FB_V (variante du face-a-face = tick & 3)
dofile(os.getenv("FB_SUITE"))
local cb = manager.machine.devices[":maincpu"]; local mb = cb.spaces["program"]
local f0, f1, v = tonumber(os.getenv("FB_F0")), tonumber(os.getenv("FB_F1")), tonumber(os.getenv("FB_V"))
local ib = 0
emu.register_frame_done(function() ib = ib + 1 end)
_G.FBTAP = mb:install_write_tap(0xFFBB80, 0xFFBFFF, "force_b", function(o, d, m)
  if ib < f0 or ib > f1 then return end
  if (o & 0x7f) == 0x0a and (m & 0xff) == 0xff then return (d & 0xff00) | v end
end)
