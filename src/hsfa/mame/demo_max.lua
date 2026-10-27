dofile("<workspace>/work/mame/tournee.lua")
-- (HANDOFF §129) DEMO D'UN PERSO MAX (MAX_DEMO) : en combat, J1 marche avant / arriere, s'accroupit, coup leger (frames redirigees) ;
-- captures toutes les 15 images pendant 360 images (-snapshot_directory). Charge tournee.lua (memes variables).
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local ports = manager.machine.ioport.ports
local k, st = 0, 0
local function u8(a) return mem:read_u8(a ~ 1) end
emu.register_frame_done(function()
  k = k + 1
  local combat = mem:read_u16(0xFF800C) == 6 and u8(0xFF8404) == 2
  if combat then st = st + 1 else st = 0 end
  if st < 60 then return end
  local ph = (st // 90) % 4; local t = st % 90
  local v = {}
  local av = (mem:read_u16(0xFF8412) < mem:read_u16(0xFF8812)) and "Right" or "Left"
  local ar = av == "Right" and "Left" or "Right"
  if ph == 0 then v["P1 " .. av] = 1 elseif ph == 1 then v["P1 " .. ar] = 1
  elseif ph == 2 then v["P1 Down"] = 1 elseif ph == 3 and t % 20 < 3 then v["P1 Button 1"] = 1 end
  for fn, f in pairs(ports[":IN0"].fields) do if string.match(fn, "^P1 ") then f:set_value(v[fn] or 0) end end
  if st >= 60 and st < 60 + 360 and st % 15 == 0 then manager.machine.video:snapshot() end
end)
