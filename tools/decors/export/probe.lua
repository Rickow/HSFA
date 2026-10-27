-- sonde : charge l'etat de combat, deplace les persos, journalise registres CPS-A et RAM camera
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local B = manager.machine.memory.shares[":cps_b_regs"]
local out = io.open(os.getenv("OUT"), "w")
local k = 0
local J1, J2 = 0xFF8400, 0xFF8800
local loaded = false
emu.register_frame_done(function()
  k = k + 1
  if k == 2 and not loaded then manager.machine:load(os.getenv("ST")); loaded = true; return end
  if k < 4 then return end
  local t = k - 4
  -- X : centre 0x280 ; va a gauche puis a droite
  local c
  if t < 200 then c = 0x280 - t * 2 elseif t < 600 then c = 0x280 - 400 + (t - 200) * 2 else c = 0x280 + 400 - (t - 600) * 2 end
  mem:write_u16(J1 + 0x10, c - 0x30); mem:write_u16(J2 + 0x10, c + 0x30)
  for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end
  local s = {string.format("%4d c=%04x", t, c)}
  for o = 0, 0x23, 2 do s[#s+1] = string.format("%04x", A:read_u16(o)) end
  s[#s+1] = "|"
  for o = 0x20, 0x3f, 2 do s[#s+1] = string.format("%04x", B:read_u16(o)) end
  s[#s+1] = "|"
  for a = 0xFF8280, 0xFF82FE, 2 do s[#s+1] = string.format("%04x", mem:read_u16(a)) end
  out:write(table.concat(s, " ") .. "\n")
  if t == 10 then
    local p = manager.machine.palettes[":palette"]
    out:write("PALTEST " .. tostring(p.entries) .. " " .. string.format("%x %x", p:pen_color(0x200 + 5), p:pen_color(0x401)) .. "\n")
    local r = mem:read_range(0x900000, 0x900007, 16)
    out:write("RR " .. #r .. " " .. string.format("%02x%02x%02x%02x %04x %04x\n", r:byte(1), r:byte(2), r:byte(3), r:byte(4), mem:read_u16(0x900000), mem:read_u16(0x900002)))
    local px, w, h = manager.machine.screens[":screen"]:pixels()
    out:write("PIX " .. #px .. " " .. tostring(w) .. " " .. tostring(h) .. "\n")
    manager.machine.video:snapshot()
    local f = io.open("cap/probe_pix.bin", "wb"); f:write(px); f:close()
  end
  if t >= 1000 then out:close(); manager.machine:exit() end
end)
