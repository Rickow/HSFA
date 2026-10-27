-- (agent greffe_arcade) CARTE DYNAMIQUE DE LA RAM DE TRAVAIL D'HYPER : prises lecture/ecriture sur $FF0000-$FFFFFF,
-- acces du 68K seulement (les acces des scripts Lua, faits pendant les rappels de fin d'image, sont ignores).
-- Par mot : premiere/derniere image de lecture, premiere/derniere image d'ecriture, nombre d'images distinctes.
-- Puis scenario SCENARIO (defaut : tournee_hyper.lua d'agent_hyper_etats). Sortie RAMOUT (+ couverture COUV).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"] or mem
local k, lua_on = 0, false
local R0, R1, W0, W1 = {}, {}, {}, {}
emu.register_frame_done(function() lua_on = true; k = k + 1 end)
RTAP = mem:install_read_tap(0xFF0000, 0xFFFFFF, "ramr", function(o, d, m)
  if lua_on then return end
  local a = o >> 1
  if not R0[a] then R0[a] = k end; R1[a] = k
end)
WTAP = mem:install_write_tap(0xFF0000, 0xFFFFFF, "ramw", function(o, d, m)
  if lua_on then return end
  local a = o >> 1
  if not W0[a] then W0[a] = k end; W1[a] = k
end)
local COUV = os.getenv("COUV"); local S = {}
if COUV then CT = ops:install_read_tap(0x0, 0x3bffff, "couv", function(o, d, m) local a = o >> 1; if not S[a] then S[a] = k end end) end
local function dump()
  local f = io.open(os.getenv("RAMOUT"), "w")
  for a = 0xFF0000 >> 1, 0xFFFFFF >> 1 do
    if R0[a] or W0[a] then
      f:write(string.format("%06x %d %d %d %d\n", a << 1, R0[a] or -1, R1[a] or -1, W0[a] or -1, W1[a] or -1))
    end
  end
  f:close()
  if COUV then
    local g = io.open(COUV, "w"); for a, fr in pairs(S) do g:write(string.format("%x %d\n", a << 1, fr)) end; g:close()
  end
end
STOPSUB = emu.add_machine_stop_notifier(dump)
dofile(os.getenv("SCENARIO") or "<workspace>/work/agent_hyper_etats/lua/tournee_hyper.lua")
emu.register_frame_done(function() lua_on = false end)
