-- sonde verticale : Y des joueurs (+$14) imposes selon DY (liste), journal des scroll Y
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local out = io.open(os.getenv("OUT"), "w")
local J1, J2 = 0xFF8400, 0xFF8800
local k, y0 = 0, nil
local DYS = {}
for v in string.gmatch(os.getenv("DYS") or "0,32,64,128,256,-32,-64", "[-%d]+") do DYS[#DYS+1] = tonumber(v) end
local MODEY = os.getenv("MODEY") or "both"
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load(os.getenv("ST")); return end
  if k < 4 then return end
  local t = k - 4
  if not y0 then y0 = mem:read_u16(J1 + 0x14); out:write(string.format("Y0 %04x x1 %04x\n", y0, mem:read_u16(J1+0x10))) end
  local seg = t // 90 + 1
  local dy = DYS[seg]
  if not dy then out:close(); manager.machine:exit(); return end
  local y = (y0 + dy) & 0xffff
  mem:write_u16(J1 + 0x14, y); if MODEY == "both" then mem:write_u16(J2 + 0x14, y) end
  mem:write_u16(J1 + 0x10, 0x250); mem:write_u16(J2 + 0x10, 0x2b0)
  for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end
  if t % 90 == 89 or t % 90 == 30 then
    local s = {}
    for a = 0xFF8280, 0xFF82BE, 2 do s[#s+1] = string.format("%04x", mem:read_u16(a)) end
    out:write(string.format("dy=%d t=%d s1y=%04x s2y=%04x s3y=%04x s3x=%04x y1=%04x | %s\n", dy, t, A:read_u16(0x0e), A:read_u16(0x12), A:read_u16(0x16), A:read_u16(0x14), mem:read_u16(J1+0x14), table.concat(s, " ")))
  end
end)
