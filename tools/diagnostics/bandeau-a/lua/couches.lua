-- masque des plans : COUCHES_OFF (hexa, bits CPS-B 0x02 scroll1, 0x04 scroll2, 0x08 scroll3) ; ROWOFF=1 : defilement par ligne coupe
-- ORDRE=xxxx force le registre de controle des plans
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local off = tonumber(os.getenv("COUCHES_OFF") or "0", 16)
CTAP = mem:install_write_tap(0x804166, 0x804167, "lc", function(o, d, m)
  if os.getenv("ORDRE") then d = (d & 0x3f) | (tonumber(os.getenv("ORDRE"), 16) & ~0x3f) end
  return d & ~off end)
if os.getenv("ROWOFF") then RTAP = mem:install_write_tap(0x804122, 0x804123, "vc", function(o, d, m) return d & ~1 end) end
dofile("<workspace>/work/agent_bandeau_A/lua/trace_a.lua")
