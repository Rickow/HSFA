-- SUIVI DES ECRIVAINS des cases RAM qui contiennent des pointeurs PS2 (passe 2 du journal des conversions).
-- SUIVI_CASES = "ff8664,ff8a64,..." (adresses des longs, liste issue de analyse_conv.py). Pour chaque ecriture d'un mot
-- de ces longs : CURPC de l'ecrivain, valeur, et adresse de la plus recente LECTURE de meme valeur (anneau de 64 mots :
-- RAM, ROM de donnees $090000-$3BFFFF) = source probable d'une copie. Sortie SUIVI_OUT : "W case mot pc valeur source n".
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]; local st = cpu.state
local RA, RV = {}, {}
for i = 0, 63 do RA[i] = -1; RV[i] = -1 end
local ri = 0
local function lec(o, d, m) ri = (ri + 1) & 63; RA[ri] = o; RV[ri] = d end
SU = {}
table.insert(SU, mem:install_read_tap(0xFF0000, 0xFFFFFF, "su_ram", lec))
table.insert(SU, mem:install_read_tap(0x090000, 0x3BFFFF, "su_rom", lec))
local S = {}
local lo, hi = 0xFFFFFF, 0
for h in (os.getenv("SUIVI_CASES") or ""):gmatch("%x+") do
  local a = tonumber(h, 16); S[a] = a; S[a + 2] = a
  lo = math.min(lo, a); hi = math.max(hi, a + 3)
end
local AGG = {}
if hi > 0 then
  table.insert(SU, mem:install_write_tap(lo, hi, "su_w", function(o, d, m)
    local c = S[o]; if not c then return end
    local src = 0
    local j = ri
    for _ = 1, 64 do if RV[j] == d and RA[j] ~= o then src = RA[j]; break end; j = (j - 1) & 63 end
    local k = string.format("%x %x %x %x %x", c, o - c, st["CURPC"].value, d, src)
    AGG[k] = (AGG[k] or 0) + 1
  end))
end
SU_STOP = emu.add_machine_stop_notifier(function()
  local f = io.open(os.getenv("SUIVI_OUT") or "suivi.txt", "w")
  for k, n in pairs(AGG) do f:write("W ", k, " ", n, "\n") end
  f:close()
end)
