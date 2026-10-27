-- toutes les ecritures sur [A0,A1] entre les images F0 et F1 (prise d'ecriture), avec PC
local frames=0
local space = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local a0 = tonumber(os.getenv("A0")); local a1 = tonumber(os.getenv("A1"))
local f0 = tonumber(os.getenv("F0")); local f1 = tonumber(os.getenv("F1"))
local lines = {}
tapx = space:install_write_tap(a0, a1, "w", function(offset, data, mask)
  if frames >= f0 then table.insert(lines, string.format("%5d %06x %04x/%04x pc %06x", frames, offset, data, mask, cpu.state["PC"].value)) end
end)
emu.register_frame_done(function()
  frames=frames+1
  if frames > f1 then local f=io.open(os.getenv("OUT"),"w"); f:write(table.concat(lines,"\n").."\n"); f:close(); manager.machine:exit() end
end)
