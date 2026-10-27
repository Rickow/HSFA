-- (agent_integration_max) vidage.lua sur une zone DEB-FIN (hexa) aux images VIDAGES
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local V = {}; local A0, A1 = tonumber(os.getenv("DEB"), 16), tonumber(os.getenv("FIN"), 16)
for x in string.gmatch(os.getenv("VIDAGES") or "", "%d+") do V[tonumber(x)] = true end
local n = 0
emu.register_frame_done(function()
  n = n + 1
  if V[n] then
    local t = {}
    for a = A0, A1, 2 do local w = mem:read_u16(a); t[#t + 1] = string.char(w >> 8, w & 0xFF) end
    local f = io.open(os.getenv("VIDAGE_OUT") .. n .. ".bin", "wb"); f:write(table.concat(t)); f:close()
  end
end)
