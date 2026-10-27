-- prises d'ecriture : WR="a0-a1,a2-a3" (hexa) ; journal des PC distincts par image entre F0 et F1 ; puis BASE_LUA
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local F0, F1 = tonumber(os.getenv("F0")), tonumber(os.getenv("F1"))
local wo = io.open(os.getenv("WOUT"), "w")
local kw, vus = 0, {}
local PCMIN, PCMAX = tonumber(os.getenv("PCMIN") or "", 16), tonumber(os.getenv("PCMAX") or "", 16)
WPT = {}
for a0, a1 in string.gmatch(os.getenv("WR"), "(%x+)-(%x+)") do
  a0, a1 = tonumber(a0, 16), tonumber(a1, 16)
  WPT[#WPT + 1] = mem:install_write_tap(a0, a1, "w" .. a0, function(o, d, m)
    if kw >= F0 and kw <= F1 then
      local pc = cpu.state["PC"].value
      if PCMIN and (pc < PCMIN or pc > PCMAX) then return end
      local key = string.format("%06x>%06x", pc, o & ~0xf)
      if os.getenv("WDETAIL") then wo:write(string.format("%d pc=%06x a=%06x d=%04x m=%04x\n", kw, pc, o, d, m))
      elseif not vus[key] then vus[key] = kw; wo:write(string.format("%d pc=%06x a=%06x d=%04x\n", kw, pc, o, d)) end
    end
  end)
end
emu.register_frame_done(function() kw = kw + 1; if kw == F1 + 1 then wo:flush() end end)
dofile(os.getenv("BASE_LUA2") or "<workspace>/work/agent_bandeau_A/lua/trace_a.lua")
