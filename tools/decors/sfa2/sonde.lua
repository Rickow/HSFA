-- SONDE : toutes les lectures de $FF8100 (decor x 2) pendant une partie (tournee.lua du banc, lecture seule) :
-- PC de l'instruction lectrice, nombre, premiere image, mode $FF8000/$FF8004 et valeur. Journal OUT .. ".lect"
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local vus, kk = {}, 0
LT = mem:install_read_tap(0xFF8100, 0xFF8101, "sonde", function(o, d, m)
  local pc = cpu.state["PC"].value & 0xffffff
  local e = vus[pc]
  if not e then vus[pc] = {1, kk, mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), d} else e[1] = e[1] + 1 end
end)
emu.register_frame_done(function()
  kk = kk + 1
  if kk % 1000 == 0 or kk == tonumber(os.getenv("NF") or "0") - 1 then
    local f = io.open(os.getenv("OUT") .. ".lect", "w")
    local t = {}
    for pc, e in pairs(vus) do t[#t + 1] = pc end
    table.sort(t)
    for _, pc in ipairs(t) do local e = vus[pc]; f:write(string.format("%06x n=%d premiere=%d mode=%04x/%04x val=%04x\n", pc, e[1], e[2], e[3], e[4], e[5])) end
    f:close()
  end
end)
dofile("<workspace>/work/mame/tournee.lua")
