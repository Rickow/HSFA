-- (agent_integration_max) recharge ETAT puis journalise (TRACE) les écritures dans WP=debut-fin (hexa) : image, PC, valeur
local n, NTR = 0, tonumber(os.getenv("NTR") or "300")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local a, b = os.getenv("WP"):match("(%x+)-(%x+)"); a, b = tonumber(a, 16), tonumber(b, 16)
local f = io.open(os.getenv("TRACE"), "w")
local tap
emu.register_frame_done(function()
  n = n + 1
  if n == 2 then manager.machine:load(os.getenv("ETAT")) end
  if n == 4 then tap = mem:install_write_tap(a, b, "wp", function(o, d, m) f:write(string.format("%d %06x pc=%06x d=%04x m=%04x\n", n, o, cpu.state["PC"].value, d, m)) end) end
  if n == 4 + NTR then f:close(); manager.machine:exit() end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
