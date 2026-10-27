-- (agent_integration_max) tournee_max.lua + écritures dans WP=a-b (hexa) : image, adresse, valeur, PC, 4 longs de pile
-- (écoute réinstallée toutes les 30 images) ; IMAGES=a-b
dofile(os.getenv("WPBASE") or "<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local a, b = os.getenv("WP"):match("(%x+)-(%x+)"); a, b = tonumber(a, 16), tonumber(b, 16)
local i0, i1 = (os.getenv("IMAGES") or "0-99999999"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local f = io.open(os.getenv("WPOUT") or os.getenv("TRACE"), "w"); local n = 0
local function cb(o, d, m)
  if n >= i0 and n <= i1 then
    local sp = cpu.state["SP"].value; local t = {}
    for k = 0, 3 do t[#t + 1] = string.format("%08x", mem:read_u32(sp + 4 * k)) end
    f:write(string.format("%d %06x %04x pc=%06x A0=%06x A1=%06x pile %s\n", n, o, d, cpu.state["PC"].value,
      cpu.state["A0"].value, cpu.state["A1"].value, table.concat(t, " ")))
  end
end
emu.register_frame_done(function()
  n = n + 1
  if n % 30 == 1 then if WPZ then WPZ:remove() end; WPZ = mem:install_write_tap(a, b, "wpz", cb) end
end)
