-- (01/11, decors etape 1) NOUVEAU CHALLENGER pendant une partie Arcade : enveloppe (charge LUA_BASE_D), puis a partir de
-- l'image DEFI_IMG (en combat) : Coin 2 puis « 2 Players Start » ; J2 valide ce qui est sous son curseur (P2 Button 1).
-- DEFI_ID=hh : l'id etendu lu par le challenger (MOVE.B $0103(A6),D0 entre DEFI_PC et DEFI_PC+8) est remplace par hh
-- (preuve de la table D4 pour toutes les familles sans piloter la selection de J2). Journal DEFI_OUT : ecritures de
-- $FF8100 (decor) avec image et PC, lectures substituees.
dofile(os.getenv("LUA_BASE_D"))
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local IMG = tonumber(os.getenv("DEFI_IMG") or "1500")
local ID = tonumber(os.getenv("DEFI_ID") or "", 16)
local PC0 = tonumber(os.getenv("DEFI_PC") or "0", 16)
local fd = io.open(os.getenv("DEFI_OUT"), "w")
local im, debut = 0, nil
-- (e25) le port donne est ignore : le champ est cherche dans TOUS les ports (P2 Button 1 / P2 Right sont dans :IN0)
local function pose(p, n, v) for _, pt in pairs(ports) do for fn, fl in pairs(pt.fields) do if fn == n then fl:set_value(v) end end end end
emu.register_frame_done(function()
  im = im + 1
  local combat = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 4 and mem:read_u16(0xFF8008) == 6
  if not debut and im >= IMG and combat then debut = im; fd:write(string.format("DEFI %d\n", im)); fd:flush() end
  if debut and im < debut + 4000 then
    local t = (im - debut) % 30
    if im < debut + 120 then pose(":IN2", "Coin 2", t < 4 and 1 or 0)
    elseif im < debut + 400 then pose(":IN2", "2 Players Start", t < 4 and 1 or 0) end
    if im >= debut + 120 then pose(":IN1", "P2 Button 1", (im % 24) < 3 and 1 or 0) end
  end
  -- (e25) DEFI_SANS_START=n : a partir de DEFI + n images, J1 n'appuie plus sur Start (le vaincu du defi ne revient pas
  -- en challenger : comme l'oracle Upper, dont la tournee n'appuie pas sur Start en partie)
  local ss = tonumber(os.getenv("DEFI_SANS_START") or "")
  if debut and ss and im >= debut + ss then pose(":IN2", "1 Player Start", 0) end
  -- (e25) DEFI_J2_ATTAQUE=1 : en combat apres le defi, J2 marche vers J1 et frappe (avec PERDRE_ETAPE=0 PERDRE_J2=id du
  -- challenger, J1 a 1 point de vie : le challenger gagne vite au lieu d'attendre la fin du temps)
  if debut and os.getenv("DEFI_J2_ATTAQUE") == "1" and combat and im > debut + 400 then
    local x1, x2 = mem:read_u16(0xFF8412), mem:read_u16(0xFF8812)
    pose(":IN1", "P2 Right", x2 < x1 and 1 or 0); pose(":IN1", "P2 Left", x2 >= x1 and 1 or 0)
    pose(":IN1", "P2 Button 1", (im % 12) < 3 and 1 or 0)
  end
end)
_G.DEFI_W = mem:install_write_tap(0xFF8100, 0xFF8101, "defi_w", function(o, d, m)
  fd:write(string.format("img %d pc=%06x $100 <- %04x (J2 $103=%02x $117=%02x)\n", im, cpu.state["PC"].value & 0xffffff, d,
    mem:read_u8(0xFF8903), mem:read_u8(0xFF8917))); fd:flush()
end)
if ID then
  _G.DEFI_R = mem:install_read_tap(0xFF8902, 0xFF8903, "defi_r", function(o, d, m)
    local pc = cpu.state["PC"].value & 0xffffff
    if pc >= PC0 and pc <= PC0 + 8 and (m & 0x00ff) ~= 0 then
      fd:write(string.format("img %d pc=%06x lecture $103 = %02x -> %02x\n", im, pc, d & 0xff, ID)); fd:flush()
      return (d & 0xff00) | ID
    end
  end)
end
