-- (HANDOFF §99) PALETTES IMPOSEES DANS LE BANC : PAL_J1=<fichier> (ex. palettes Eagle, 30 x 16 mots u16 petit-boutistes
-- 0xFRGB) remplace la palette d'objets PALOBJ_J1 (defaut 0, celle des objets de J1) par la palette n PAL_N (defaut 0).
-- Base des palettes : registre CPS-A $80410A (adresse = base << 8, ex. $90C0 -> $90C000 ; objets = 32 premieres).
-- MAME recopie les palettes A L'ECRITURE de ce registre : les couleurs sont posees dans la prise, juste avant.
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("PAL_J1"), "rb"); local s = f:read("a"); f:close()
local n = tonumber(os.getenv("PAL_N") or "0"); local dest = tonumber(os.getenv("PALOBJ_J1") or "0")
local cols = {}
for i = 0, 15 do cols[i] = string.unpack("<I2", s, 32 * n + 2 * i + 1) end
-- prise sur les 32 octets de la palette visee : toute ecriture du jeu y est remplacee par la couleur imposee
-- (base suivie sur le registre ; prise reposee si la base change). Rien n'est ecrit depuis une prise.
local base, zone = nil, nil
PAL_REG = mem:install_write_tap(0x80410A, 0x80410B, "palbase", function(o, d, m) base = d & 0xffff end)
emu.register_frame_done(function()
  if not base then return end
  local a = (base << 8) + 32 * dest
  if zone ~= a then
    if PAL_TAP then PAL_TAP:remove() end
    zone = a
    PAL_TAP = mem:install_write_tap(a, a + 31, "palj1", function(o, d, m) return cols[(o - a) >> 1] end)
    for i = 0, 15 do mem:write_u16(a + 2 * i, cols[i]) end
  end
end)
