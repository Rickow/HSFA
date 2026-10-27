-- sonde : coups.lua + journal des ecritures (PC) sur SONDE_ADR (plages hex "a-b,c-d") pour r dans [SONDE_R0, SONDE_R1]
dofile("<workspace>/work/agent_coups/coups.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("OUT") .. ".sonde", "w")
local R0, R1 = tonumber(os.getenv("SONDE_R0")), tonumber(os.getenv("SONDE_R1"))
SONDE_TAPS = {}
local n = 0
for a, b in string.gmatch(os.getenv("SONDE_ADR"), "(%x+)-(%x+)") do
  n = n + 1
  SONDE_TAPS[n] = mem:install_write_tap(tonumber(a, 16), tonumber(b, 16), "sonde" .. n, function(o, d, m)
    local fr = COUPS_R or -1
    if fr >= R0 and fr <= R1 then f:write(string.format("%d %06x pc=%06x d=%04x m=%04x\n", fr, o, cpu.state["PC"].value & 0xffffff, d, m)); f:flush() end
  end)
end
