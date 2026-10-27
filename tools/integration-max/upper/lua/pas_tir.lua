-- (agent_integration_max) coup_etat.lua + pas d'animation des tirs (objets $FF9400-$FF9FFF dont le type $2 = TYPE, hexa)
dofile("<workspace>/work/agent_integration_max/lua/coup_etat.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local TY = tonumber(os.getenv("TYPE"), 16)
local G = io.open(os.getenv("JTIR"), "w"); local vu = {}
emu.register_frame_done(function()
  for b = 0xFF9400, 0xFF9F00, 0x100 do
    if m:read_u8(b + 1) ~= 0 and (m:read_u8(b + 3) == TY or (TY == 0xFF and not vu["t" .. m:read_u8(b + 3)])) then
      if TY == 0xFF then vu["t" .. m:read_u8(b + 3)] = true; G:write(string.format("type %02x obj %06x\n", m:read_u8(b + 3), b)) end
      local p = (m:read_u16(b + 0x1E) << 16) | m:read_u16(b + 0x1C)
      if not vu[p] then vu[p] = true
        local t = {}; for k = 0, 11 do t[#t + 1] = string.format("%02x", m:read_u8(p + k)) end
        G:write(string.format("obj %06x pas %08x : %s\n", b, p, table.concat(t, " "))); G:flush()
      end
    end
  end
end)
