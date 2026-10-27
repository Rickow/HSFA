-- (agent_hyper_etats) traces du debogueur d'une image : TRACES="image:nom,..." -> essais/traces/<nom>.tr ; puis SCRIPT2
local fr = 0
local T = {}
for f, n in string.gmatch(os.getenv("TRACES") or "", "(%d+):([%w_]+)") do T[tonumber(f)] = n end
local D = "<workspace>/work/agent_hyper_etats/essais/traces/"
local actif = false
emu.register_frame_done(function()
  fr = fr + 1
  if actif then manager.machine.debugger:command("trace off"); actif = false end
  if T[fr] then manager.machine.debugger:command("trace " .. D .. T[fr] .. ".tr,maincpu,noloop"); actif = true end
end)
dofile(os.getenv("SCRIPT2"))
