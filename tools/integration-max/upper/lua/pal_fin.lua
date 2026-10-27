-- (agent_integration_max) tournee_max.lua + vidage des PALETTES à chaque image multiple de SNAPP de la séquence de fin
-- ($FF8004 = $000A ; PALTEST=1 : sans condition). Base AFFICHÉE = long $C154(A5) d'Upper ($FF4154, homologue de $20(A5)
-- arcade ; ex. $0090C000) ; tampons de fin $91C000 / $920000 (échangés à chaque scène, $26080) vidés aussi. PALDIR/<image>.bin =
-- [mot de base (2 o)] + palettes affichées ($1800 o) + $91C000 ($1800 o) + $920000 ($1800 o), mots gros-boutistes.
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local SNAPP = tonumber(os.getenv("SNAPP") or "45")
local D = os.getenv("PALDIR")
local k = 0
-- base de palette : DERNIÈRE valeur écrite par le jeu dans le registre CPS-A $80410A (élargi par le portage ; Upper la
-- calcule depuis le long $C154(A5)) ; adresse = valeur << 8
REG_PAL = 0
TAP_PAL = mem:install_write_tap(0x80410A, 0x80410B, "regpal", function(o, d, m) REG_PAL = d end)
local function zone(t, a) for x = a, a + 0x17FE, 2 do t[#t + 1] = string.pack(">I2", mem:read_u16(x)) end end
emu.register_frame_done(function()
  k = k + 1
  if k % SNAPP ~= 0 or (mem:read_u16(0xFF8004) ~= 0x000A and os.getenv("PALTEST") ~= "1") then return end
  -- Upper : base de palette = long $C154(A5) = $FF4154 (image $3432 : LSR.L #8 -> $80410A) ; arcade : $20(A5)
  local b = REG_PAL
  local t = {string.pack(">I2", b)}
  zone(t, b * 0x100); zone(t, 0x91C000); zone(t, 0x920000)
  local f = assert(io.open(string.format("%s/%06d.bin", D, k), "wb")); f:write(table.concat(t)); f:close()
end)
