-- DISPOSITION.LUA (ETAPE A) : acces a la RAM de travail par ADRESSE ARCADE, quelle que soit la disposition.
--   local D = dofile("<workspace>/work/agent_reorg_A/outils/disposition.lua")
--   D.lire(0xFF80AE, 2)            -- mot de la graine (meme adresse partout)
--   D.ecrire(0xFF8115, 1, 8)       -- octet : traduction a l'adresse XOR 1
--   D.ecrire(0xFF8458, 4, 0x12345) -- long : traduction moities echangees (forme s32 par defaut)
--   D.lire_champ(0xFF8400, 0x102, 1)  -- champ d'une structure (deplacement ARCADE), exceptions A6 appliquees
--   D.force("ff8115=8,Lff8458=12345,Wff8050=90")   -- syntaxe de tournee.lua FORCE (+ W pour un mot)
--   D.adresse(a, n) -> adresse traduction, forme (nil = recette ; "u8x2" mot a octets echanges ; "u8x4" / "s16x2" longs)
-- Arcade (REF=1, ou D.ref = true) : identite. Traduction : recette cps2 (HANDOFF §29) + relocation de la zone basse
-- (agent_symboles reloc_a5) + exceptions par variable (votes des instructions alignees), table disposition_carte.lua
-- generee par gen_disposition.py. Quand la disposition changera (etapes B-E), seule la table change.
local D = {}
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local ici = debug.getinfo(1, "S").source:match("^@(.*/)") or "./"
D.carte = dofile(ici .. "disposition_carte.lua")
D.ref = os.getenv("REF") == "1"
local C = D.carte
local function trad(a, n)
  if D.ref then return a, nil end
  local e = C.exceptions[a * 8 + n]
  local f = C.formes[a * 8 + n]
  if e then return e, f end
  do
    for _, iv in ipairs(C.intervalles) do
      local lo, hi, d = iv[1], iv[2], iv[3]
      if lo < 0x1000000 and ((a >= lo and a < hi) or (n == 1 and (a ~ 1) >= lo and (a ~ 1) < hi)) then
        return ((n == 1) and (a ~ 1) or a) + d, f
      end
    end
  end
  return (n == 1) and (a ~ 1) or a, f
end
-- exceptions de champs : la table range 0x1000000 + deplacement trad ; reconversion vers une adresse absolue
local function trad_champ(base, d, n)
  if D.ref then return base + d, nil end
  local e = C.exceptions[(0x1000000 + d) * 8 + n]
  local f = C.formes[(0x1000000 + d) * 8 + n]
  if e then return base + (e & 0xFFFF), f end
  return base + ((n == 1) and (d ~ 1) or d), f
end
function D.adresse(a, n) return trad(a, n) end
local function lit(t, n, f)
  if n == 1 then return mem:read_u8(t) end
  if n == 2 then local w = mem:read_u16(t); if f == "u8x2" and not D.ref then w = ((w & 0xFF) << 8) | (w >> 8) end; return w end
  if D.ref or f == "s16x2" then return mem:read_u32(t) end
  if f == "u8x4" then return (mem:read_u8(t ~ 1) << 24) | (mem:read_u8((t + 1) ~ 1) << 16) | (mem:read_u8((t + 2) ~ 1) << 8) | mem:read_u8((t + 3) ~ 1) end
  return (mem:read_u16(t + 2) << 16) | mem:read_u16(t)              -- s32 : moities echangees
end
local function ecrit(t, n, v, f)
  if n == 1 then mem:write_u8(t, v & 0xFF) return end
  if n == 2 then
    if f == "u8x2" and not D.ref then v = ((v & 0xFF) << 8) | ((v >> 8) & 0xFF) end
    mem:write_u16(t, v & 0xFFFF) return
  end
  if D.ref or f == "s16x2" then mem:write_u32(t, v & 0xFFFFFFFF) return end
  if f == "u8x4" then for k = 0, 3 do mem:write_u8((t + k) ~ 1, (v >> (24 - 8 * k)) & 0xFF) end return end
  mem:write_u16(t, v & 0xFFFF); mem:write_u16(t + 2, (v >> 16) & 0xFFFF)
end
-- lecture d'un long en zone NON exceptionnelle : t vient de trad(a, 4) (meme adresse que le mot)
function D.lire(a, n) local t, f = trad(a, n); return lit(t, n, f) end
function D.ecrire(a, n, v) local t, f = trad(a, n); ecrit(t, n, v, f) end
function D.lire_champ(base, d, n) local t, f = trad_champ(base, d, n); return lit(t, n, f) end
function D.ecrire_champ(base, d, n, v) local t, f = trad_champ(base, d, n); ecrit(t, n, v, f) end
-- octets d'une plage arcade -> table {adresse traduction = octet} (pour les prises d'ecriture)
function D.octets(a, octets)
  local r = {}
  for i = 1, #octets do r[trad(a + i - 1, 1)] = octets[i] end
  return r
end
function D.force(spec)
  for kind, a, v in string.gmatch(spec, "([LW]?)(%x+)=(%x+)") do
    local n = (kind == "L") and 4 or ((kind == "W") and 2 or 1)
    D.ecrire(tonumber(a, 16), n, tonumber(v, 16))
  end
end
return D
