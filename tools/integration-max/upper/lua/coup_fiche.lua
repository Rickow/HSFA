-- (agent_integration_max) coup_etat.lua + écritures dans les fiches de manipulation de J1 (FICHES="358,368" offsets hexa, 8 o)
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local G = io.open(os.getenv("JFICHE"), "w")
local f = 0
emu.register_frame_done(function() f = f + 1 end)
TAPS = {}
for o in string.gmatch(os.getenv("FICHES"), "[^,]+") do
  local a = 0xFF8400 + tonumber(o, 16)
  TAPS[#TAPS + 1] = m:install_write_tap(a, a + 7, "fiche" .. o, function(off, data, mask)
    G:write(string.format("%d %s +%x %04x/%04x pc=%06x\n", f, o, off - a, data, mask, cpu.state["PC"].value))
  end)
end
