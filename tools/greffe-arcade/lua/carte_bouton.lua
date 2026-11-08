-- (e38) CARTE DU MONDE : charge CB_BASE (pilote), puis pendant la scène 4/2 (A5+0 = 2, A5+4 = 4, A5+8 = 2) :
-- CB_BOUTON = b1 / b2 / b4 / st (ou "port|champ") appuyé CB_DUREE images toutes les CB_PER
-- images (défaut 3 / 30) ; CB_BOUTON = "aucun" : aucune entrée pendant 4/2 (annule le Start du pilote).
-- Journal CB_OUT : image et mots A5+0/+4/+8/+C à chaque changement, jusqu'à CB_N passages en 4/2 (défaut 3) puis sortie.
dofile(os.getenv("CB_BASE"))
local mem_c = manager.machine.devices[":maincpu"].spaces["program"]
local ports_c = manager.machine.ioport.ports
local fc = io.open(os.getenv("CB_OUT"), "w")
local B_c = os.getenv("CB_BOUTON") or "aucun"
local ALIAS_c = {b1 = ":IN0|P1 Button 1", b2 = ":IN0|P1 Button 2", b4 = ":IN1|P1 Button 4", st = ":IN2|1 Player Start"}
B_c = ALIAS_c[B_c] or B_c   -- (pas d'espace dans les VARS des lanceurs : b1, b2, b4, st, aucun)
local PER_c, DUR_c = tonumber(os.getenv("CB_PER") or "30"), tonumber(os.getenv("CB_DUREE") or "3")
local N_c = tonumber(os.getenv("CB_N") or "3")
local k_c, der_c, n_c, deb_c = 0, "", 0, 0
emu.register_frame_done(function()
  k_c = k_c + 1
  local a0, a4, a8, ac = mem_c:read_u16(0xFF8000), mem_c:read_u16(0xFF8004), mem_c:read_u16(0xFF8008), mem_c:read_u16(0xFF800C)
  local st = string.format("%04x %04x %04x %04x", a0, a4, a8, ac)
  if st ~= der_c then
    fc:write(string.format("%d %s\n", k_c, st)); fc:flush()
    if a0 == 2 and a4 == 4 and a8 == 2 and not der_c:match("^0002 0004 0002") then n_c = n_c + 1; deb_c = k_c end
    if der_c:match("^0002 0004 0002") and not (a0 == 2 and a4 == 4 and a8 == 2) then
      fc:write(string.format("CARTE %d duree %d\n", n_c, k_c - deb_c)); fc:flush()
      if n_c >= N_c then fc:close(); manager.machine:exit() end
    end
    der_c = st
  end
  if a0 == 2 and a4 == 4 and a8 == 2 then
    for p, port in pairs(ports_c) do
      for fn, f in pairs(port.fields) do
        if string.match(fn, "^P%d ") or fn == "1 Player Start" or fn == "2 Players Start" then
          local on = (B_c ~= "aucun") and (p .. "|" .. fn == B_c) and ((k_c - deb_c) % PER_c < DUR_c) and (k_c - deb_c) >= 10
          f:set_value(on and 1 or 0)
        end
      end
    end
  end
end)
