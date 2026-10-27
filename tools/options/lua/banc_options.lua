-- (agent_options, OPTIONS.md) Reglages de l'ecran OPTION de l'Anthology pour le banc MAME (equivalent des DIP
-- « Option: ... » du coeur FBNeo HSFA, cps_hsfa.cpp HsfaOptions). L'ecran d'options du portage est du C natif PS2
-- (non traduit) ; il recopiait ses reglages dans la RAM du jeu a la place des octets de configuration de l'EEPROM
-- arcade. Ici : les octets choisis sont ecrits a chaque fin d'image passee au menu des modes ($FF8000 = 4).
-- A charger par dofile() depuis le script de scenario (comme banc_mem.lua). Sans variable HSFA_OPT_* : rien n'est
-- ecrit (ancien comportement) ; HSFA_OPTIONS=0 : rien n'est ecrit non plus.
--
-- Variables d'environnement (valeur absente ou 0 = « defaut du jeu », rien n'est ecrit pour ce reglage) :
--   HSFA_OPT_DIFFICULTE 1-8   (etoiles ; PS2 : 5)        -> $FF80A1 = n-1   (arcade $A0)
--   HSFA_OPT_DEGATS     1-4   (PS2 : 2)                  -> $FF80A0 = n-1   (arcade $A1)
--   HSFA_OPT_CHRONO     1-4, 5 = infini (PS2 : 2)        -> $FF80A3 = n-1   (arcade $A2)
--   HSFA_OPT_VITESSE    1 NORMAL, 2 TURBO1, 3 TURBO2 (PS2), 4 FREE1, 5 FREE2   -> $FF80A2 = n-1   (arcade $A3)
--   HSFA_OPT_MANCHES    1 = 1 manche, 2 = 3 (PS2), 3 = 5 : MAX ROUND (1P)     -> $FF80DF = n-1   (arcade $DE)
--   HSFA_OPT_MANCHES_VS idem, MAX ROUND (VS)                                   -> $FF80DE = n-1   (arcade $DF)
--   HSFA_OPT_VS1P / HSFA_OPT_VS2P  1 HUMAN, 2 COM : VS MODE                    -> SFA3 $FF4111/$FF4110, Upper/Hyper $FF4311/$FF4310
--   HSFA_OPT_JOIN       1 OFF, 2 ON (PS2)                                      -> $FF80A5 = n-1   (arcade $A4)
--   HSFA_OPT_EXTRA      "p1,p2,p3" : octets hexa des options secretes EXTRA OPTION 1-3 (bit = 2e valeur de l'ecran)
--   HSFA_OPT_DIP        "B,C,D,E,F,G,H" : octets hexa des DIP B-H du coeur FBNeo (memes codages), prioritaires
--   HSFA_OPT_JEU        sfa3 | upper | hyper (defaut : d'apres BANC_COMMUN, 545 = hyper, 351 = upper, sinon sfa3)
if os.getenv("HSFA_OPTIONS") == "0" then return end
local function n(v) return tonumber(os.getenv(v) or "0") or 0 end
local d = {0, 0, 0, 0, 0, 0, 0}
d[1] = (n("HSFA_OPT_DIFFICULTE") & 0x0F) | ((n("HSFA_OPT_DEGATS") & 7) << 4)
d[2] = (n("HSFA_OPT_CHRONO") & 7) | ((n("HSFA_OPT_VITESSE") & 7) << 3)
d[3] = (n("HSFA_OPT_MANCHES") & 3) | ((n("HSFA_OPT_MANCHES_VS") & 3) << 2) | ((n("HSFA_OPT_VS1P") & 3) << 4) | ((n("HSFA_OPT_VS2P") & 3) << 6)
d[4] = n("HSFA_OPT_JOIN") & 3
local k = 5
for v in string.gmatch(os.getenv("HSFA_OPT_EXTRA") or "", "%x+") do if k <= 7 then d[k] = tonumber(v, 16) & 0xFF; k = k + 1 end end
if os.getenv("HSFA_OPT_DIP") then
  local i = 1
  for v in string.gmatch(os.getenv("HSFA_OPT_DIP"), "%x+") do if i <= 7 then d[i] = tonumber(v, 16) & 0xFF; i = i + 1 end end
end
local actif = false
for i = 1, 7 do if d[i] ~= 0 then actif = true end end
if not actif then return end
local jeu = os.getenv("HSFA_OPT_JEU") or ({["545"] = "hyper", ["351"] = "upper"})[os.getenv("BANC_COMMUN") or ""] or "sfa3"
local vs = (jeu == "sfa3") and 0xFF4110 or 0xFF4310
local X = ({sfa3 = {0xFF41A4, 0xFF41A7, 0xFF41A6}, upper = {0xFF43A6, 0xFF43A9, 0xFF43A8}, hyper = {0xFF43BB, 0xFF43BA, 0xFF43BD}})[jeu]
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local function w(a, v) sp:write_u8(a, v) end
print(string.format("banc_options : %s, DIP B-H = %02X %02X %02X %02X %02X %02X %02X", jeu, d[1], d[2], d[3], d[4], d[5], d[6], d[7]))
emu.register_frame_done(function()
  if sp:read_u16(0xFF8000) ~= 4 then return end            -- menu des modes
  local v
  v = d[1] & 0x0F; if v > 0 then w(0xFF80A1, v - 1) end      -- DIFFICULTY
  v = (d[1] >> 4) & 7; if v > 0 then w(0xFF80A0, v - 1) end  -- DAMAGE LEVEL
  v = d[2] & 7; if v > 0 then w(0xFF80A3, v - 1) end         -- TIMER SPEED (4 = INFINITY)
  v = (d[2] >> 3) & 7; if v > 0 then w(0xFF80A2, v - 1) end  -- SPEED SELECT
  v = d[3] & 3; if v > 0 then w(0xFF80DF, v - 1) end         -- MAX ROUND (1P)
  v = (d[3] >> 2) & 3; if v > 0 then w(0xFF80DE, v - 1) end  -- MAX ROUND (VS)
  v = (d[3] >> 4) & 3; if v > 0 then w(vs + 1, v - 1) end    -- VS MODE (1P)
  v = (d[3] >> 6) & 3; if v > 0 then w(vs, v - 1) end        -- VS MODE (2P)
  v = d[4] & 3; if v > 0 then w(0xFF80A5, v - 1) end         -- JOIN IN
  for p = 1, 3 do if d[4 + p] ~= 0 then w(X[p], d[4 + p]) end end   -- EXTRA OPTION 1-3
end)
