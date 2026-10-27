-- (agent_integration_max) espion de lectures : tournee_max.lua + taps de lecture sur des plages (ESPION=a0-a1,b0-b1 hex)
-- journal ESPION_OUT : plage, décalage, pc, nombre, 1re et dernière image
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local W = os.getenv("BANC_DIR")
local vu = {}
local img = 0
local I0, I1 = string.match(os.getenv("ESPION_IMAGES") or "0-99999999", "(%d+)-(%d+)"); I0, I1 = tonumber(I0), tonumber(I1)
ESPION_TAPS = {}
emu.register_frame_done(function() img = img + 1 end)
local function fichier(base)
  local f = io.open(W .. string.format("ext_%06x.bin", base), "rb"); if not f then return nil end
  local s = f:read("a"); f:close(); return s
end
for a0s, a1s, bs in string.gmatch(os.getenv("ESPION") or "", "(%x+)-(%x+)@?(%x*)") do
  local a0, a1 = tonumber(a0s, 16), tonumber(a1s, 16)
  local base = (bs ~= "") and tonumber(bs, 16) or nil
  local s = base and fichier(base)
  table.insert(ESPION_TAPS, sp:install_read_tap(a0, a1, "espion" .. a0s, function(offset, data, mask)
    if img >= I0 and img <= I1 then
    local pc = cpu.state["PC"].value
    local k = string.format("%06x %06x", offset, pc)
    local e = vu[k]
    if e then e[1] = e[1] + 1; e[3] = img else vu[k] = {1, img, img} end
    end
    if s then local i = (offset & ~1) - base + 1; return (s:byte(i) << 8) | s:byte(i + 1) end
    return data
  end))
end
emu.register_stop(function()
  local o = io.open(os.getenv("ESPION_OUT"), "w")
  local t = {}
  for k, e in pairs(vu) do t[#t + 1] = k .. string.format(" %d %d %d", e[1], e[2], e[3]) end
  table.sort(t); for _, l in ipairs(t) do o:write(l .. "\n") end; o:close()
end)
