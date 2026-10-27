-- (agent_integration_max) cherche les mots de RAM ($FF0000-$FFFFFF) qui augmentent de 1 à chaque image (images 3000-3060)
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local n, prev, ok = 0, nil, nil
emu.register_frame_done(function()
  n = n + 1
  if n < 3000 or n > 3060 then return end
  local cur = {}
  for a = 0xFF0000, 0xFFFFFE, 2 do cur[a] = m:read_u16(a) end
  if prev then
    if not ok then ok = {} for a in pairs(cur) do ok[a] = true end end
    for a in pairs(ok) do if (prev[a] + 1) & 0xffff ~= cur[a] then ok[a] = nil end end
  end
  prev = cur
  if n == 3060 then
    local f = io.open(os.getenv("CPT"), "w")
    for a in pairs(ok) do f:write(string.format("%06x %04x\n", a, cur[a])) end
    f:close()
  end
end)
