-- Partie Arcade complete (tournee.lua du banc, lecture seule) + releve de toutes les valeurs ecrites dans $FF8100
-- ($100(A5) = numero de decor x 2, indice des tables de listes et de palettes relogees) : une valeur >= $40 lirait
-- au-dela des 32 entrees (comportement different apres relogement). Journal : OUT .. ".decors"
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local vus, k = {}, 0
local jd = io.open(os.getenv("OUT") .. ".decors", "w")
GT = mem:install_write_tap(0xFF8100, 0xFF8101, "garde", function(o, d, m)
  if not vus[d] then vus[d] = true; jd:write(string.format("image %d : $FF8100 <- %04X (masque %04X)\n", k, d, m)); jd:flush() end
end)
emu.register_frame_done(function() k = k + 1 end)
dofile("<workspace>/work/mame/tournee.lua")
