-- BANC DES SPRITES (HANDOFF §82) : emule dans MAME les BANQUES de sprites du portage, comme le fera le fork.
-- Objet du portage : X (priorite CPS2 en bits 13-15, inchangee), Y (bits 13-15 = EMPLACEMENT de banque, au lieu
-- des bits hauts du code), code LOCAL a la banque, attributs CPS2 (tailles de bloc, retournements, palette).
-- Les banques sont des sous-ensembles REORGANISES de la ROM : un objet multi-blocs (code + x + 16y en local)
-- n'est pas contigu dans la ROM -> la liste est ECLATEE en tuiles 16x16 quand le jeu ecrit le marqueur de fin
-- (X = Y = $8000), chaque tuile convertie par la table banques/f<N>.bin (local -> code CPS2).
-- Emplacements : 0 = e254 (communs), 1 = memoire de tuiles du decor (e256, table plan2), 2/3 = banque du perso de J1/J2 (table $59C0B0 : banques/carte.txt),
-- 4 = fichier graphique de la paire dont l'animation est pointee par $BE48(A5). Autres : objets retires.
local W = os.getenv("BANC_BANQUES") or "<workspace>/work/mame/banques/"   -- (HANDOFF §115) Upper : work/mame_ro5/banques/
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local perso, anim, tables = {}, {}, {}
for l in io.lines(W .. "carte.txt") do
  local k, a, b = string.match(l, "^(%a+) (%d+) (%d+)$")
  if k == "perso" then perso[tonumber(a)] = tonumber(b) elseif k == "anim" then anim[tonumber(a)] = tonumber(b) end
end
local function banque(f)
  if not f then return nil end
  if tables[f] == nil then
    local h = io.open(W .. (type(f) == "string" and (f .. ".bin") or string.format("f%d.bin", f)), "rb")
    tables[f] = h and h:read("a") or false
    if h then h:close() end
  end
  return tables[f] or nil
end
local function global(t, l)
  if not t or l < 0 or 4 * l + 4 > #t then return nil end
  local c = string.unpack("<I4", t, 4 * l + 1)
  if c == 0xFFFFFFFF then return nil end
  return c
end
local fichier4                                          -- derniere animation connue pointee par $BE48
local function suivre4()
  -- (HANDOFF §108) $BE48(A5) : deplacement SIGNE -> $FF8000 - $41B8 = $FF3E48 (et non $FFBE48, lu a tort jusqu'ici) ;
  -- Upper : $C0BC(A5) -> $FF40BC (BANC_PTR_ANIM)
  local p = mem:read_u32(tonumber(os.getenv("BANC_PTR_ANIM") or "FF3E48", 16))
  local f = anim[p]
  -- (HANDOFF §106) pointeur nul (avant tout chargement natif) : couple de l'intro (graphismes 456, animation 310)
  if p == 0 then f = tonumber(os.getenv("BANC_GFX_INTRO") or "456") end
  if f then fichier4 = f end
end
emu.register_frame_done(suivre4)
local function emplacements()
  suivre4()
  local e = {}
  e[0] = banque(tonumber(os.getenv("BANC_COMMUN") or "254"))   -- (HANDOFF §121) banque commune : SFA3 e254, Upper e351
  e[1] = banque(os.getenv("SLOT1") or "plan2")          -- (§83) ctx+$34 : memoire de tuiles du decor e256 (HUD...)
  -- (HANDOFF §99) BANQUE_J1 / BANQUE_J2 = banque imposee (ex. pl26 : Eagle, table banques/pl26.bin) ; sinon par l'ID
  e[2] = banque(os.getenv("BANQUE_J1") or perso[mem:read_u8(0xFF8503)])   -- octet perso ($102 ROM, octet XOR 1)
  e[3] = banque(os.getenv("BANQUE_J2") or perso[mem:read_u8(0xFF8903)])
  e[4] = banque(fichier4)
  -- (HANDOFF §102) emplacements 6/7 = joueurs 3/4 (DRAMATIC BATTLE : 2 contre 1), structures $FF8C00 / $FF9000
  -- seulement si la structure est ACTIVE (octet d'etat $FF8C01 / $FF9001) : en combat a deux, des objets d'emplacement 6/7
  -- existent aussi (copie bleue de Dan derriere lui, capture de l'utilisateur) ; ils etaient ecartes avant §102
  if mem:read_u8(0xFF8C01) ~= 0 then e[6] = banque(perso[mem:read_u8(0xFF8D03)]) end
  if mem:read_u8(0xFF9001) ~= 0 then e[7] = banque(perso[mem:read_u8(0xFF9103)]) end
  return e
end
local busy = false
OBJ1, OBJ2 = manager.machine.memory.shares[":objram1"], manager.machine.memory.shares[":objram2"]
UNE_BANQUE = os.getenv("BANC_UNE_BANQUE") == "1"      -- (diagnostic) ancien comportement : banque courante seule
if os.getenv("SANS_PAL") then SANS_PAL = {} for v in string.gmatch(os.getenv("SANS_PAL"), "%x+") do SANS_PAL[tonumber(v, 16)] = true end end
local ombre = {}        -- mots ecrits PAR LE JEU (la plage $700000 est en ECRITURE seule ; la liste est construite en
                        -- plusieurs fois, chaque marqueur de fin relance l'eclatement depuis la liste BRUTE)
local function lit(a) return ombre[a] or 0 end
BANC_OMBRE = ombre      -- (diagnostic, lecture seule) liste BRUTE du jeu
-- (§83) la memoire d'objets ne garde QUE des listes converties : une ecriture brute du jeu est detournee vers 'ombre'
-- et la prise rend a la place le mot converti deja en place. Sinon, quand le jeu construit sa liste en deux images,
-- MAME affiche la page en cours d'ecriture : codes LOCAUX bruts = HUD et banniere « ROUND » en tuiles parasites.
local conv = {}
-- (§83) la liste est construite par morceaux et certaines entrees ne sont pas reecrites : des RESTES d'ecrans anciens
-- (trame de fondu de l'ecran VS en plein combat). Une entree n'est retenue que si son X a ete ecrit recemment.
local age = {}
IMAGE = 0
emu.register_frame_done(function() IMAGE = IMAGE + 1 end)
local SANS_AGE = os.getenv("BANC_SANS_AGE") == "1"     -- (diagnostic) desactive le filtre des entrees anciennes
local function recent(a) return SANS_AGE or (age[a] or -99) >= IMAGE - 3 end
STATS = {listes = 0, objets = 0, tuiles = 0, retires = 0, tronques = 0}
local function eclater(page, fin, adr_courante)
  local e = emplacements()
  local out = {}
  for a = page, fin - 8, 8 do   -- objets avant le marqueur de fin
    local x, y, code, at = lit(a), lit(a + 2), lit(a + 4), lit(a + 6)
    if not recent(a) then goto suivant end
    if SANS_PAL and SANS_PAL[at & 0x1f] then goto suivant end   -- (diagnostic) objets d'une palette masques
    local t = e[(y >> 13) & 7]
    if PALSTAT then local c = ((y >> 13) & 7) * 256 + (at & 0x1f); PALSTAT[c] = (PALSTAT[c] or 0) + 1 end
    local nx, ny = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
    local fx, fy = (at & 0x20) ~= 0, (at & 0x40) ~= 0
    STATS.objets = STATS.objets + 1
    for nys = 0, ny - 1 do
      for nxs = 0, nx - 1 do
        local cx = fx and (nx - 1 - nxs) or nxs
        local cy = fy and (ny - 1 - nys) or nys
        local g = global(t, code + cx + 16 * cy)
        if g then
          -- (HANDOFF §116) code de tuile sur 20 bits : bits 16-17 -> Y 13-14 ; bits 18-19 -> X 10-11 (fork sfa3hx,
          -- ROM graphique etendue ; le bit 15 de Y reste le marqueur de fin)
          out[#out + 1] = {((x & 0x3ff) + 16 * nxs) & 0x3ff | (x & 0xe000) | (((g >> 18) & 3) << 10),
                           ((y & 0x3ff) + 16 * nys) & 0x3ff | (((g >> 16) & 3) << 13),
                           g & 0xffff, at & 0x00ff}
        else STATS.retires = STATS.retires + 1
          if RETSTAT then local c = string.format("e%d c=%04x at=%04x x=%03x y=%03x", (y >> 13) & 7, code, at, x & 0x3ff, y & 0x3ff); RETSTAT[c] = (RETSTAT[c] or 0) + 1 end
        end
      end
    end
    ::suivant::
  end
  if #out > 1023 then STATS.tronques = STATS.tronques + #out - 1023; for k = #out, 1024, -1 do out[k] = nil end end
  out[#out + 1] = {0x8000, 0x8000, 0, 0}
  STATS.listes = STATS.listes + 1; STATS.tuiles = STATS.tuiles + #out - 1
  local ret
  busy = true
  -- (HANDOFF §103) la CPS2 echange ses deux banques d'objets a chaque retour de trame. Trop lente en turbo, la
  -- traduction commence une liste avant le retour de trame et la finit apres (une moitie dans chaque banque), et
  -- certaines images n'ont pas de liste (banque gardant une pose ancienne) : fantomes. La liste COMPLETE convertie
  -- est donc ecrite dans les DEUX banques physiques (le fork verrouillera de meme la liste a son marqueur de fin).
  for k, o in ipairs(out) do
    local a = page + 8 * (k - 1)
    for w = 0, 3 do
      conv[a + 2 * w] = o[w + 1]
      if a + 2 * w == adr_courante then ret = o[w + 1] else mem:write_u16(a + 2 * w, o[w + 1]) end
      if not UNE_BANQUE then OBJ1:write_u16(a - page + 2 * w, o[w + 1]); OBJ2:write_u16(a - page + 2 * w, o[w + 1]) end
    end
  end
  busy = false
  return ret or 0x8000
end
TAP_SPRITES = mem:install_write_tap(0x700000, 0x70ffff, "sprites", function(offset, data, mask)
  -- marqueur de fin du portage : X = Y = $8000 (code et attributs quelconques) -> declenche sur Y
  if busy then return end
  ombre[offset] = data & 0xffff
  age[offset] = IMAGE
  if data ~= 0x8000 or (offset & 7) ~= 2 or lit(offset - 2) ~= 0x8000 then return conv[offset] end
  local a = offset - 2
  local page = (offset < 0x708000) and 0x700000 or 0x708000
  local ok, r = pcall(eclater, page, a, offset)
  if not ok then busy = false; if not ERREUR_SPRITES then ERREUR_SPRITES = r; print("banc_sprites : " .. tostring(r)) end return end
  return r
end)
