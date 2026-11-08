-- empreinte.lua — PREUVE INTERNE (optionnelle) : CRC32 de la ROM programme telle que le 68000 la voit (0-0x3FFFFF),
-- calculé DANS MAME au démarrage, comparé à EMPREINTE_CRC (calculé sur les fichiers : empreinte.py crc -- <commande>).
-- Puis exécute le vrai script du banc (EMPREINTE_SUITE). Différent -> ligne « EMPREINTE_LUA ECART » et arrêt de MAME.
-- Variables : EMPREINTE_CRC (8 chiffres hexa), EMPREINTE_SUITE (script Lua du banc), EMPREINTE_LUA_OUT (fichier, facultatif).
-- Usage (lance.sh) : -autoboot_script outils/empreinte.lua avec EMPREINTE_SUITE=<script du banc>.
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local T = {}
for i = 0, 255 do
  local c = i
  for _ = 1, 8 do c = (c & 1 ~= 0) and (0xEDB88320 ~ (c >> 1)) or (c >> 1) end
  T[i] = c
end
local c = 0xFFFFFFFF
for a = 0, 0x3FFFFE, 2 do
  local w = mem:read_u16(a)
  c = T[(c ~ (w >> 8)) & 0xFF] ~ (c >> 8)
  c = T[(c ~ (w & 0xFF)) & 0xFF] ~ (c >> 8)
end
local crc = string.format("%08x", c ~ 0xFFFFFFFF)
local att = (os.getenv("EMPREINTE_CRC") or ""):lower()
local etat = (att == "" and "NON_VERIFIEE") or (att == crc and "OK") or "ECART"
local msg = "EMPREINTE_LUA " .. etat .. " crc=" .. crc .. (att ~= "" and (" attendu=" .. att) or "")
print(msg)
if os.getenv("EMPREINTE_LUA_OUT") then
  local f = io.open(os.getenv("EMPREINTE_LUA_OUT"), "a"); if f then f:write("# " .. msg .. "\n"); f:close() end
end
if etat == "ECART" then
  print("ARRET DU BANC : la ROM programme chargee n'est pas celle attendue")
  manager.machine:exit()
  return
end
if os.getenv("EMPREINTE_SUITE") and os.getenv("EMPREINTE_SUITE") ~= "" then dofile(os.getenv("EMPREINTE_SUITE")) end
