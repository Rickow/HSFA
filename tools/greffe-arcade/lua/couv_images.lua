-- (etape 2) enveloppe : charge LUA_BASE puis enregistre, pour les CF_N images qui suivent la 1re entree dans l'etat
-- CF_ETAT ("A5+0 A5+4 A5+8 A5+C" en hexa, ex. "0002 0004 0002 0000"), les adresses d'opcodes lues (par image).
-- Sortie CF_OUT : lignes "image_relative adresse".
dofile(os.getenv("LUA_BASE"))
local cpuc = manager.machine.devices[":maincpu"]; local memc = cpuc.spaces["program"]
local opc = cpuc.spaces["opcodes"] or memc
local CF_N = tonumber(os.getenv("CF_N") or "60")
local cible = string.gsub(os.getenv("CF_ETAT"), "_", " ")
local debut, rel, vus = nil, -1, {}
local fo = io.open(os.getenv("CF_OUT"), "w")
_G.CFTAP = opc:install_read_tap(0x0, 0x3bffff, "cfimg", function(o, d, m)
  if rel >= 0 and rel < CF_N and not vus[o] then vus[o] = true; fo:write(string.format("%d %x\n", rel, o)) end
end)
local nimg = 0
emu.register_frame_done(function()
  nimg = nimg + 1
  local e = string.format("%04x %04x %04x %04x", memc:read_u16(0xFF8000), memc:read_u16(0xFF8004), memc:read_u16(0xFF8008), memc:read_u16(0xFF800C))
  if debut == nil and e == cible then debut = nimg end
  if debut then
    rel = nimg - debut; vus = {}
    if rel >= CF_N then fo:close(); debut = -1e9; rel = -1 end
  end
end)
