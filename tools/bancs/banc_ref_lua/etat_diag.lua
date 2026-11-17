-- (banc_unique, 16/11) etat_diag.lua : DIAGNOSTIC SEULEMENT (jamais une preuve). Enveloppe : charge DIAG_BASE (le Lua
-- d'amorce normal de la partie), puis :
--   DIAG_SAUVE=n  : a l'image n, manager.machine:save(DIAG_NOM) (etat range sous -state_directory, nom = empreinte de la
--                   construction + partie + cle + image ; banc_ref.py ecrit l'empreinte a cote et refuse un etat etranger) ;
--   DIAG_CHARGE=1 : a la 2e image, manager.machine:load(DIAG_NOM) (comme HANDOFF §110 : jamais -state en ligne de commande).
-- Journal DIAG_OUT : une ligne par action. Le compteur d'images du Lua de base repart de 0 apres un chargement : ses
-- reperes d'images (NF, captures) sont relatifs au chargement.
dofile(os.getenv("DIAG_BASE"))
local fdg = io.open(os.getenv("DIAG_OUT"), "w")
local nom = os.getenv("DIAG_NOM")
local sauve = tonumber(os.getenv("DIAG_SAUVE") or "")
local charge = os.getenv("DIAG_CHARGE") == "1"
local ig = 0
emu.register_frame_done(function()
  ig = ig + 1
  if sauve and ig == sauve then manager.machine:save(nom); fdg:write(string.format("SAUVE %d %s\n", ig, nom)); fdg:flush() end
  if charge and ig == 2 then manager.machine:load(nom); fdg:write(string.format("CHARGE %d %s\n", ig, nom)); fdg:flush() end
end)
