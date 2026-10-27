-- (agent_integration_max) coup_contre.lua + points d'arrêt du débogueur avec « printf » (BPS="adr|format|valeurs;..."),
-- console recopiée dans JBP à l'arrêt ; lancer avec EXTRA="-debug -debugger none"
dofile("<workspace>/work/agent_integration_max/lua/coup_contre.lua")
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if n == 5 then
    local d = manager.machine.debugger
    for spec in string.gmatch(os.getenv("BPS"), "[^;]+") do
      local a, f, v = spec:match("([^|]+)|([^|]+)|(.+)")
      d:command("bpset " .. a .. "," .. (os.getenv("BPCOND") or "1") .. ",{printf \"" .. f .. "\"," .. v .. "; g}")
    end
  end
end)
emu.register_stop(function()
  local G = io.open(os.getenv("JBP"), "w")
  for _, l in ipairs(manager.machine.debugger.consolelog) do G:write(l .. "\n") end
  G:close()
end)
