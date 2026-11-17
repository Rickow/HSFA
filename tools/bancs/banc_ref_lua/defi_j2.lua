-- (banc_unique, 16/11) defi_j2.lua : 2e JOUEUR QUI DEFIE en cours d'Arcade (« HERE COMES A NEW CHALLENGER »).
-- COPIE adaptee de couleur_cpu_ha2/lua/defi_carte.lua (= greffe_ro9a38/essais/outils/defi_carte.lua, forme mesuree qui
-- marche : revue_greffe/RESULTATS_ESSAIS.md 08b et flou/01). Enveloppe : charge LUA_BASE_D (ex. graine_pc.lua -> tournee).
-- Coin 2 de DEFI_COIN a DEFI_COIN+120 ; puis, a la 1re image >= DEFI_IMG ou (A5+0, A5+4, A5+8) = DEFI_ETAT (defaut
-- "2 4 2" = carte ; "2 4 4" face-a-face ; "2 4 6" combat), « 2 Players Start » en impulsions SERREES (3 images sur 6, comme
-- flou/01) tant que l'etat dure (600 images au plus) ; P2 Button 1 ensuite (J2 valide ce qui est sous son curseur).
-- Ce rappel est enregistre APRES celui de la tournee (qui remet Coin 2 / 2 Players Start a 0 a chaque image) : il l'emporte.
-- Journal DEFI_OUT : « DEFI image etat », puis une ligne toutes les 10 images (etat, J2 $103) pendant 4000 images.
dofile(os.getenv("LUA_BASE_D"))
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local IMG = tonumber(os.getenv("DEFI_IMG") or "500")
local COIN = tonumber(os.getenv("DEFI_COIN") or "400")
local E = {}; for x in string.gmatch(os.getenv("DEFI_ETAT") or "2 4 2", "%x+") do E[#E + 1] = tonumber(x, 16) end
local fd = io.open(os.getenv("DEFI_OUT"), "w")
local im, debut = 0, nil
local function pose(n, v) for _, pt in pairs(ports) do for fn, fl in pairs(pt.fields) do if fn == n then fl:set_value(v) end end end end
emu.register_frame_done(function()
  im = im + 1
  local a0, a4, a8 = mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), mem:read_u16(0xFF8008)
  if im >= COIN and im < COIN + 120 then pose("Coin 2", ((im - COIN) % 30) < 4 and 1 or 0) end
  local vise = a0 == E[1] and a4 == E[2] and a8 == E[3]
  if not debut and im >= IMG and vise then
    debut = im; fd:write(string.format("DEFI %d etat %04x %04x %04x\n", im, a0, a4, a8)); fd:flush() end
  if debut and vise and im < debut + 600 then pose("2 Players Start", ((im - debut) % 6) < 3 and 1 or 0) end
  if debut and im >= debut + 60 and im < debut + 4000 then pose("P2 Button 1", (im % 24) < 3 and 1 or 0) end
  if debut and im < debut + 4000 and im % 10 == 0 then
    fd:write(string.format("img %d etat %04x %04x %04x J2 $101=%02x $103=%02x\n", im, a0, a4, a8, mem:read_u8(0xFF8801), mem:read_u8(0xFF8903))); fd:flush() end
end)
