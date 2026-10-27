-- PARTIE ARCADE COMPLETE sur la ROM corrigee (tournee.lua du banc, lecture seule) + journal des decors ecrits dans
-- $FF8100 + garde des lecteurs de $FF8100 non traites quand le decor vaut >= $50 + journal des commandes son.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local kk = 0
local f = io.open(os.getenv("OUT") .. ".decors", "w")
local vus = {}
GW = mem:install_write_tap(0xFF8100, 0xFF8101, "ecr", function(o, d, m)
  f:write(string.format("image %d : $FF8100 <- %04X (PC %06x)\n", kk, d, cpu.state["PC"].value & 0xffffff)); f:flush()
end)
local CONNUS = {}
for l in io.lines("<workspace>/work/decors_sfa2/format/sites100_tr.txt") do
  local a = tonumber(string.match(l, "^(%x+):"), 16); for d = 2, 8, 2 do CONNUS[a + d] = true end
end
for a = 0x93200, 0x93800, 2 do CONNUS[a] = true end
for a = 0xC40, 0xC50, 2 do CONNUS[a] = true end
for a = 0xBF0, 0xC08, 2 do CONNUS[a] = true end      -- IRQ (sauvegarde des registres)
local lj = io.open(os.getenv("OUT") .. ".lect", "w")
local dans_lua = false        -- lectures faites par les scripts Lua (fin d'image) : ignorées
GL = mem:install_read_tap(0xFF8100, 0xFF8101, "lect", function(o, d, m)
  if not dans_lua and d >= 0x50 and m == 0xffff then
    local pc = cpu.state["PC"].value & 0xffffff
    if not CONNUS[pc] and not vus[pc] then vus[pc] = true; lj:write(string.format("image %d PC %06x\n", kk, pc)); lj:flush() end
  end
end)
local js = io.open(os.getenv("OUT") .. ".son", "w")
local boite = {}
GS = mem:install_write_tap(0x618000, 0x61801f, "son", function(offset, data, mask)
  local a = (mask & 0xff) ~= 0 and (offset | 1) or (offset & ~1)
  local v = (mask & 0xff) ~= 0 and (data & 0xff) or ((data >> 8) & 0xff)
  boite[a] = v
  if a == 0x61801f and v == 0 then
    local cmd = ((boite[0x618001] or 0) << 8) | (boite[0x618003] or 0)
    if cmd < 0x100 or cmd >= 0xFF00 then js:write(string.format("%6d cmd %04x decor %04x\n", kk, cmd, mem:read_u16(0xFF8100))); js:flush() end
  end
end)
emu.register_frame_done(function() kk = kk + 1; dans_lua = true end)
dofile("<workspace>/work/mame/tournee.lua")
emu.register_frame_done(function() dans_lua = false end)
