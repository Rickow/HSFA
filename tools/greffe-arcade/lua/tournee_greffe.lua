-- TOURNEE + COUVERTURE (agent greffe_arcade, d'apres work/mame/tournee.lua, HANDOFF §110/§128).
-- Ajouts : PERDRE=1 (J1 ne joue pas, vie a 1 : partie perdue -> continue / fin de partie) ;
--          journal des mots $FF8000-$FF800E a chaque changement ;
--          COUV=<fichier> : couverture par prise sur l'espace OPCODES (mot lu -> premiere image, par etat de scene) ;
--          SNAPETAT=1 : capture 40 images apres la 1re apparition de chaque etat (A5+0,+4,+8,+C), et toutes les
--          SNAPSC images dans les scenes 6/8/A/C.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"] or mem
local ports = manager.machine.ioport.ports
local VS = os.getenv("VS") == "1"
local PERDRE = os.getenv("PERDRE") == "1"
local VSBOUCLE = os.getenv("VSBOUCLE") == "1"   -- VERSUS en boucle : boutons J1/J2 hors combat (ecran RESULT -> nouvelle selection)
local out = io.open(os.getenv("OUT"), "w")
out:write("ESPACE " .. (cpu.spaces["opcodes"] and "opcodes" or "program") .. "\n")
local NF = tonumber(os.getenv("NF") or "90000")
local SNAPETAT = os.getenv("SNAPETAT") == "1"
local SNAPSC = tonumber(os.getenv("SNAPSC") or "0")
local SNL = {}                                   -- (etape 3) SNAPS="n,n,..." : captures aux images donnees
for x in string.gmatch(os.getenv("SNAPS") or "", "%d+") do SNL[tonumber(x)] = true end
local SAVEAT = tonumber(os.getenv("SAVEAT") or "")
local J1, J2 = 0xFF8400, 0xFF8800
local XO = 0x12
local k, combats, stable, last, sel = 0, 0, 0, "", 0
local PERSO = tonumber(os.getenv("PERSO") or "", 16)
local MODE = tonumber(os.getenv("MODE") or "")
local function u8(a) return mem:read_u8(a ~ 1) end
-- couverture
local COUV = os.getenv("COUV")
local S, stid, etats, netat = {}, 0, {}, 0
local snapq = {}
if COUV then
  CT = ops:install_read_tap(0x0, 0x3bffff, "couv", function(o, d, m)
    local key = (o >> 1) * 512 + stid
    if not S[key] then S[key] = k end
  end)
end
local function ecrit_couv()
  if not COUV then return end
  local f = io.open(COUV, "w")
  for nom, id in pairs(etats) do f:write(string.format("E %d %s\n", id, nom)) end
  for key, fr in pairs(S) do f:write(string.format("%x %d %d\n", (key // 512) * 2, key % 512, fr)) end
  f:close()
end
local function fin(msg) out:write(msg); out:close(); ecrit_couv(); manager.machine:exit() end
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1"); if VS then on(":IN2", "Coin 2") end end
  local jeu = u8(0xFF80A8)
  if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
  -- CONTINUE=1 : Start sur l'ecran CONTINUE (scene A5+4 = 6, A5+8 = 6), une fois le compte entame
  if os.getenv("CONTINUE") == "1" and mem:read_u16(0xFF8004) == 6 and mem:read_u16(0xFF8008) == 6 and k % 120 < 6 then on(":IN2", "1 Player Start") end
  -- (etape 2) GRAINE=hhhh : graine du hasard $FF80AE imposee pendant la fin de selection (A5+4 = 2, A5+8 = 6), comme
  -- tournee_arcade.lua sur ro9a : liste des adversaires comparable ; LISTE_ADV (defaut $FF40C0) journalisee aux combats
  if os.getenv("GRAINE") and mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2 and mem:read_u16(0xFF8008) == 6 then
    mem:write_u16(0xFF80AE, tonumber(os.getenv("GRAINE"), 16))
  end
  local mode = mem:read_u16(0xFF800C)
  local adv = {}
  for _, o in ipairs({J2, 0xFF8C00, 0xFF9000}) do if u8(o + 4) == 2 then adv[#adv + 1] = o end end
  local combat = mode == 6 and u8(J1 + 4) == 2 and #adv > 0
  if MODE and mem:read_u16(0xFF8000) == 4 and jeu & 1 == 0 then mem:write_u8(tonumber(os.getenv("MODE_ADR") or "FF4201", 16), MODE) end
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if PERSO and ecran_sel and sel < 120 then mem:write_u8((J1 + 0x102) ~ 1, PERSO) end
  if VS and k >= 1900 and k < 2100 and k % 40 >= 20 and k % 40 < 26 then on(":IN2", "2 Players Start") end
  if VSBOUCLE and combats > 0 and not combat and k % 24 >= 4 and k % 24 < 8 then on(":IN0", "P1 Button 1") end
  if VSBOUCLE and combats > 0 and not combat and k % 24 >= 12 and k % 24 < 16 then on(":IN0", "P2 Button 1") end
  if VS and combats == 0 and k >= 2000 and k % 24 >= 4 and k % 24 < 8 and not combat then on(":IN0", "P1 Button 1") end
  if VS and combats == 0 and k >= 2000 and k % 24 >= 12 and k % 24 < 16 and not combat then on(":IN0", "P2 Button 1") end
  if combats == 0 and k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not PERSO or not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
  if jeu & 1 == 1 and not PERDRE then mem:write_u16(J1 + 0x50, 0x90); mem:write_u16(J1 + 0x52, 0x90) end
  if combat then
    stable = stable + 1
    if stable == 60 then
      combats = combats + 1
      local la = tonumber(os.getenv("LISTE_ADV") or "FF40C0", 16); local t = {}
      for i = 0, 15 do t[#t + 1] = string.format("%02x", mem:read_u8(la + (i ~ 1))) end
      out:write(string.format("COMBAT %d %d J2 %02x etape %04x decor %04x liste %s\n", combats, k, u8(J2 + 0x102), mem:read_u16(0xFF8114),
        mem:read_u16(0xFF8100), table.concat(t, "")))
    end
    if stable > 60 and PERDRE then
      local v1 = mem:read_u16(J1 + 0x50)
      if v1 > 1 and v1 < 0x100 then mem:write_u16(J1 + 0x50, 1); mem:write_u16(J1 + 0x52, 1) end
    elseif stable > 60 then
      for _, o in ipairs(adv) do
        local v2 = mem:read_u16(o + 0x50)
        if v2 > 1 and v2 < 0x100 then mem:write_u16(o + 0x50, 1); mem:write_u16(o + 0x52, 1) end
      end
      local av = (mem:read_u16(J1 + XO) < mem:read_u16(adv[1] + XO)) and "Right" or "Left"
      local t = stable % 40
      if t < 3 then on(":IN0", "P1 Down") elseif t < 6 then on(":IN0", "P1 Down"); on(":IN0", "P1 " .. av)
      elseif t < 10 then on(":IN0", "P1 " .. av); if t >= 7 then on(":IN0", "P1 Button 1") end end
    end
  else stable = 0 end
  local w = {}
  for a = 0xFF8000, 0xFF800E, 2 do w[#w + 1] = string.format("%04x", mem:read_u16(a)) end
  local st = table.concat(w, " ") .. string.format(" %04x %02x %02x", mem:read_u16(0xFF8100), u8(J1 + 0x102), u8(J2 + 0x102))
  if st ~= last then out:write(string.format("%6d : %s\n", k, st)); last = st end
  -- etat de scene pour la couverture : A5+0, +4, +8, +C (mots)
  local nom = w[1] .. " " .. w[3] .. " " .. w[5] .. " " .. w[7]
  if not etats[nom] then
    netat = netat + 1; etats[nom] = netat
    if SNAPETAT then snapq[k + 40] = true end
  end
  stid = etats[nom]
  local sc = mem:read_u16(0xFF8004)
  local SNAP4 = tonumber(os.getenv("SNAP4") or "0")   -- captures toutes les SNAP4 images en scene 4 hors combat (A5+8 ~= 6)
  if SNAP4 > 0 and k % SNAP4 == 0 and w[1] == "0002" and sc == 4 and w[5] ~= "0006" then
    manager.machine.video:snapshot(); out:write(string.format("SNAP %d %s\n", k, nom))
  elseif snapq[k] or SNL[k] or (SNAPSC > 0 and k % SNAPSC == 0 and w[1] == "0002" and (sc == 6 or sc == 8 or sc == 10 or sc == 12)) then
    manager.machine.video:snapshot(); out:write(string.format("SNAP %d %s\n", k, nom))
  end
  if SAVEAT and k == SAVEAT then manager.machine:save(os.getenv("SAVENAME") or "tournee") end
  local pc = cpu.state["PC"].value & 0xffffff
  local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then fin(string.format("EXCEPTION %d pc=%x\n", k, pc)); return end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k >= NF then fin("FIN\n") end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end
