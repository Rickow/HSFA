-- (agent_integration_max) tournee_max.lua + écritures dans la file des commandes son ($5E80(A5) = $FFDE80..) :
-- image, valeur, PC et 6 longs de la pile (appelants) ; FILTRE = masque:valeur (hexa) sur le mot écrit
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("SONS_OUT"), "w")
local fm, fv = (os.getenv("FILTRE") or "0:0"):match("(%x+):(%x+)"); fm, fv = tonumber(fm, 16), tonumber(fv, 16)
local n = 0
local function cb(o, d, m)
  if (d & fm) == fv then
    local sp = cpu.state["SP"].value; local t = {}
    for k = 0, 5 do t[#t + 1] = string.format("%08x", mem:read_u32(sp + 4 * k)) end
    f:write(string.format("%d %06x %04x pc=%06x pile %s\n", n, o, d, cpu.state["PC"].value, table.concat(t, " ")))
  end
end
-- les écoutes RAM disparaissent quand la carte mémoire est refaite : réinstallée toutes les 30 images
emu.register_frame_done(function()
  n = n + 1
  if n % 30 == 1 then if SONS_TAP then SONS_TAP:remove() end; SONS_TAP = mem:install_write_tap(0xFFDE80, 0xFFEFFF, "file", cb) end
end)
emu.register_stop(function() f:close() end)
