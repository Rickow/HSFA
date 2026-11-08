-- (e34) enveloppe : charge ISO_BASE (defaut graine_pc.lua) ; a partir de l'image ISO_DEB, plans actives = ISO_EN (masque
-- CPS-B $804166 : 2 = scroll1, 4 = scroll2, 8 = scroll3 ; ISO_OBJ=0 : objets retires) ; captures aux images ISO_IM
dofile(os.getenv("ISO_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mi = manager.machine.devices[":maincpu"].spaces["program"]
local deb = tonumber(os.getenv("ISO_DEB") or "0"); local en = tonumber(os.getenv("ISO_EN") or "14")
local IMS = {}; for x in string.gmatch(os.getenv("ISO_IM") or "", "%d+") do IMS[tonumber(x)] = true end
local ki = 0
_G.ISO_LT = mi:install_write_tap(0x804166, 0x804167, "e34iso", function(o, d, m) if ki >= deb then return (d & ~0x3e) | en end end)
if os.getenv("ISO_OBJ") == "0" then
  _G.ISO_OT = mi:install_write_tap(0x700000, 0x70ffff, "e34isoo", function(o, d, m) if ki >= deb then return 0xff00 end end)
end
emu.register_frame_done(function() ki = ki + 1; if IMS[ki] then manager.machine.video:snapshot() end end)
