-- (agent_bandeau_A) journal par image des registres CPS-A + table de defilement par ligne, puis tournee.lua
-- REGOUT : fichier ; REG0/REG1 : fenetre d'images journalisees
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local sh = manager.machine.memory.shares
local ro = io.open(os.getenv("REGOUT"), "w")
local R0, R1 = tonumber(os.getenv("REG0") or "0"), tonumber(os.getenv("REG1") or "999999")
local kk = 0
local function ca(i) return sh[":cps_a_regs"]:read_u16(2 * i) end
emu.register_frame_done(function()
  kk = kk + 1
  if kk < R0 or kk > R1 then return end
  local t = {}
  for i = 0, 0x12 do t[#t + 1] = string.format("%04x", ca(i)) end
  local other = (ca(4) & 0xffc0) << 8
  local ro_ = ca(0x10)
  local l = {}
  for y = 0, 255, 4 do l[#l + 1] = string.format("%04x", mem:read_u16(other + 2 * ((ro_ + y) & 0x3ff))) end
  ro:write(string.format("%d %s | LC %04x | %04x %04x %04x | RS %s\n", kk, table.concat(t, " "), sh[":cps_b_regs"]:read_u16(0x26), mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), mem:read_u16(0xFF800C), table.concat(l, " ")))
  ro:flush()
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
