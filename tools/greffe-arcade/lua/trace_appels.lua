-- (etape 2) enveloppe : charge LUA_BASE, puis TRACE DES ENTREES DE ROUTINES (mot d'opcode lu a une adresse listee dans
-- TA_DEBUTS : une adresse 68K hexa par ligne) pendant TA_N images a partir de la 1re entree dans l'etat TA_ETAT
-- ("0002_0004_0002_0000"). Sortie TA_OUT : "image_relative adresse" dans l'ordre d'execution (max TA_MAX lignes).
dofile(os.getenv("LUA_BASE"))
local cpt = manager.machine.devices[":maincpu"]; local mt = cpt.spaces["program"]
local opt = cpt.spaces["opcodes"] or mt
local D = {}
for l in io.lines(os.getenv("TA_DEBUTS")) do D[tonumber(l, 16)] = true end
local N = tonumber(os.getenv("TA_N") or "20"); local MAXL = tonumber(os.getenv("TA_MAX") or "400000")
local cible = string.gsub(os.getenv("TA_ETAT"), "_", " ")
local fo = io.open(os.getenv("TA_OUT"), "w")
local debut, rel, nl = nil, -1, 0
_G.TATAP = opt:install_read_tap(0x0, 0x3bffff, "tappels", function(o, d, m)
  if rel >= 0 and rel < N and D[o] and nl < MAXL then nl = nl + 1; fo:write(string.format("%d %x\n", rel, o)) end
end)
local ni = 0
emu.register_frame_done(function()
  ni = ni + 1
  local e = string.format("%04x %04x %04x %04x", mt:read_u16(0xFF8000), mt:read_u16(0xFF8004), mt:read_u16(0xFF8008), mt:read_u16(0xFF800C))
  -- TA_OCC=n : n-ieme entree dans l'etat (defaut 1)
  if e == cible and e ~= dernier_e then occ = (occ or 0) + 1 end
  dernier_e = e
  if debut == nil and e == cible and occ == tonumber(os.getenv("TA_OCC") or "1") then debut = ni - 1 end
  if debut then rel = ni - debut; if rel >= N then fo:close(); debut = -1e9; rel = -1 end end
end)
