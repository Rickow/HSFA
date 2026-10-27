-- TOURNEE ARCADE (HANDOFF §110) : partie Arcade a 1 joueur jusqu'a la fin (combats, rival, boss, fin, generique,
-- entree du nom), sur la ROM arcade (REF=1) ou la traduction. J1 a une vie infinie ; en combat, la vie du CPU est
-- ramenee a 1 et J1 lance des boules de feu (degats meme en garde) -> K.O. rapide (sinon victoire au temps).
-- Journal OUT : changements des modes ($FF8000/2/4, $FF800C), du decor ($FF8100), des persos ; captures toutes les
-- SNAPP images (dossier -snapshot_directory) ; traduction : arret sur exception (comme diag.py). NF = derniere image.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local REF = os.getenv("REF") == "1"
local VS = os.getenv("VS") == "1"   -- (HANDOFF §128) VERSUS : 2e joueur (piece 2, Start J2 a l'entree du mode, bouton J2 sur :IN0)
local out = io.open(os.getenv("OUT"), "w")
local NF = tonumber(os.getenv("NF") or "90000")
local SNAPP = tonumber(os.getenv("SNAPP") or "0")
local SNAP0 = tonumber(os.getenv("SNAP0") or "0")   -- premiere image capturee
local SNAPFIN = os.getenv("SNAPFIN") == "1"   -- captures seulement pendant la sequence de fin ($FF8004 = $000A)
local DUMPC = os.getenv("DUMPC")   -- vidages de la RAM au debut des manches listees (DOUT..n)
local FORCE, FORCEC = os.getenv("FORCE"), tonumber(os.getenv("FORCEC") or "1")
local SAVEAT = tonumber(os.getenv("SAVEAT") or "")   -- etat MAME (nom SAVENAME) a cette image
local J1, J2 = 0xFF8400, 0xFF8800
local XO = REF and 0x10 or 0x12
local k, combats, stable, last, sel = 0, 0, 0, "", 0
local PERSO = tonumber(os.getenv("PERSO") or "", 16)   -- perso de J1 impose a la selection (+$102, hex)
local MODE = tonumber(os.getenv("MODE") or "")   -- traduction : mode du menu Anthology (curseur $C001(A5) = $FF4001)
local CURSEUR = tonumber(os.getenv("CURSEUR") or "")   -- position du curseur de selection de J1 ($FF8411)
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1"); if VS then on(":IN2", "Coin 2") end end
  local jeu = u8(0xFF80A8)
  if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
  local mode = mem:read_u16(0xFF800C)
  -- (HANDOFF §126) adversaires : J2, et les structures joueur des combats a plusieurs (Juli et Juni : $FF8C00/$FF9000,
  -- J2 inactif) ; sinon la manche n'etait jamais detectee (pas de K.O. force, nuls sans fin)
  local adv = {}
  for _, o in ipairs({J2, 0xFF8C00, 0xFF9000}) do if u8(o + 4) == 2 then adv[#adv + 1] = o end end
  local combat = mode == 6 and u8(J1 + 4) == 2 and #adv > 0
  if MODE and not REF and mem:read_u16(0xFF8000) == 4 and jeu & 1 == 0 then mem:write_u8(tonumber(os.getenv("MODE_ADR") or "FF4001", 16), MODE) end   -- curseur : octet $FF4001 (SFA3), $FF4201 (Upper)
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if CURSEUR and ecran_sel and sel < 120 then mem:write_u8(REF and (J1 + 0x11) or ((J1 + 0x11) ~ 1), CURSEUR) end
  if PERSO and ecran_sel and sel < 120 then mem:write_u8(REF and (J1 + 0x102) or ((J1 + 0x102) ~ 1), PERSO) end
  if VS and k >= 1900 and k < 2100 and k % 40 >= 20 and k % 40 < 26 then on(":IN2", "2 Players Start") end   -- pas plus tard : Start J2 sur l'ecran de selection fait tourner le curseur aleatoire
  if VS and combats == 0 and k >= 2000 and k % 24 >= 4 and k % 24 < 8 and not combat then on(":IN0", "P1 Button 1") end
  if VS and combats == 0 and k >= 2000 and k % 24 >= 12 and k % 24 < 16 and not combat then on(":IN0", "P2 Button 1") end
  if combats == 0 and k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not (CURSEUR or PERSO) or not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
  if jeu & 1 == 1 then mem:write_u16(J1 + 0x50, 0x90); mem:write_u16(J1 + 0x52, 0x90) end
  if combat then
    stable = stable + 1
    if stable == 60 then
      combats = combats + 1; out:write(string.format("COMBAT %d %d\n", combats, k))
      if FORCE and combats == FORCEC then   -- FORCE="ff8115=8,..." ecrit (octet, adresse arcade) a la manche FORCEC
        for a, v in string.gmatch(FORCE, "L(%x+)=(%x+)") do   -- long (traduction : moities echangees)
          a, v = tonumber(a, 16), tonumber(v, 16)
          if REF then mem:write_u32(a, v) else mem:write_u16(a, v & 0xffff); mem:write_u16(a + 2, v >> 16) end
        end
        for a, v in string.gmatch(FORCE, "%f[%x](%x+)=(%x+)") do mem:write_u8(REF and tonumber(a, 16) or (tonumber(a, 16) ~ 1), tonumber(v, 16)) end
      end
      if DUMPC and string.find("," .. DUMPC .. ",", "," .. combats .. ",", 1, true) then   -- RAM de travail brute
        local f = io.open(os.getenv("DOUT") .. combats, "wb"); local t = {}
        for a = 0xFF0000, 0xFFFFFE, 2 do t[#t+1] = string.pack(">I2", mem:read_u16(a)) end
        f:write(table.concat(t)); f:close()
      end
    end
    if stable > 60 then
      for _, o in ipairs(adv) do
        local v2 = mem:read_u16(o + 0x50)
        if v2 > 1 and v2 < 0x100 then mem:write_u16(o + 0x50, 1); mem:write_u16(o + 0x52, 1) end
      end
      local av = (mem:read_u16(J1 + XO) < mem:read_u16(adv[1] + XO)) and "Right" or "Left"
      local t = stable % 40     -- boule de feu : bas, bas-avant, avant + poing
      if t < 3 then on(":IN0", "P1 Down") elseif t < 6 then on(":IN0", "P1 Down"); on(":IN0", "P1 " .. av)
      elseif t < 10 then on(":IN0", "P1 " .. av); if t >= 7 then on(":IN0", "P1 Button 1") end end
    end
  else stable = 0 end
  local st = string.format("%04x %04x %04x %04x %04x %02x %02x", mem:read_u16(0xFF8000), mem:read_u16(0xFF8002),
    mem:read_u16(0xFF8004), mode, mem:read_u16(0xFF8100), u8(J1 + 0x102), u8(J2 + 0x102))
  if st ~= last then out:write(string.format("%6d : %s\n", k, st)); last = st end
  if SNAPP > 0 and k % SNAPP == 0 and k >= SNAP0 and (not SNAPFIN or mem:read_u16(0xFF8004) == 0x000A) then manager.machine.video:snapshot() end
  if SAVEAT and k == SAVEAT then manager.machine:save(os.getenv("SAVENAME") or "tournee") end
  if not REF then
    local pc = cpu.state["PC"].value & 0xffffff
    local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
    if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then
      out:write(string.format("EXCEPTION %d pc=%x\n", k, pc)); out:close(); manager.machine:exit(); return
    end
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k >= NF then out:write("FIN\n"); out:close(); manager.machine:exit() end
end)
if not REF then
  dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
  if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end
end
