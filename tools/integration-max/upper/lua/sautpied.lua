-- (agent_integration_max) tournee_max.lua (sans ALEA) + saut avant + gros pied de J1 toutes les 70 images de combat ;
-- journal : image, pas courant de J1 ($1C), vie J2, X J1/J2
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("TRACE"), "w"); local n, c = 0, 0
local ports = manager.machine.ioport.ports
local function champ(nm) for _, p in pairs(ports) do for fn, fl in pairs(p.fields) do if fn == nm then return fl end end end end
local UP, RT, HK = champ("P1 Up"), champ("P1 Right"), champ("P1 Button 6")
emu.register_frame_done(function()
  n = n + 1
  local combat = mem:read_u16(0xFF800C) == 6
  if combat then c = c + 1 else c = 0 end
  if c > 120 then
    local t = c % 70
    UP:set_value((t < 4) and 1 or 0); RT:set_value((t < 4) and 1 or 0); HK:set_value((t >= 14 and t < 18) and 1 or 0)
    f:write(string.format("%d %04x%04x vie2=%04x x1=%04x x2=%04x y1=%04x\n", n, mem:read_u16(0xFF841E), mem:read_u16(0xFF841C),
      mem:read_u16(0xFF8850), mem:read_u16(0xFF8412), mem:read_u16(0xFF8812), mem:read_u16(0xFF8416)))
  end
end)
