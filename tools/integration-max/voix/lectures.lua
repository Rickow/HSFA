-- Taps de lecture sur la ROM QSound (espace « rom » du peripherique :qsound) : signale toute lecture dans les zones
-- ecrites par gen_voix_max.py (fichier ZONES : « debut fin nom » en decimal), puis enchaine voix.lua.
local rom = manager.machine.devices[":qsound"].spaces["rom"]
local lg = io.open(os.getenv("LECT"), "w")
local vus = {}
LTAPS = {}
for l in io.lines(os.getenv("ZONES")) do
  local a, b, nom = l:match("(%d+) (%d+) (%S+)")
  a, b = tonumber(a), tonumber(b)
  LTAPS[#LTAPS + 1] = rom:install_read_tap(a, b, "z" .. a, function(offset, data, mask)
    local k = nom .. string.format("%06x", offset & 0xfffff0)
    if not vus[k] then
      vus[k] = true
      lg:write(string.format("%.6f %06x %s\n", manager.machine.time:as_double(), offset, nom)); lg:flush()
    end
  end)
end
dofile("<workspace>/work/agent_voix_max/voix.lua")
