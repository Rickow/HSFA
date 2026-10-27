-- (agent_hyper_etats, ETATS-HYPER.md §4) TOURNEE HYPER : enchainement selection -> VS -> combats (K.O. forces) dans
-- Hyper SFA (ro9) sur le fork sfa3hx, en VERSUS a 2 joueurs (MODEJEU=1) ou TRAINING (MODEJEU=4).
-- Equivalent de work/mame/tournee.lua, qui ne reconnait pas les phases d'Hyper (A5+0 reste a 2 ; combat = A5+4 = 4,
-- A5+8 = 6). Toutes les entrees passent par les ports (aucune ecriture de $102/$116/$117) :
--  * titre/menu : pieces, Start J1, curseur $FF4201 deplace par Bas (VERSUS 1 -> TRAINING 4), bouton 1 ;
--  * selection (etat $5 du joueur, 68K) : 0 perso (curseur X/Y $12/$16, grille 0x5C5650, chemin calcule comme le jeu),
--    2 version ($5C), 4 MANUAL/AUTO, 6 mode ZERO 3 ($5C 0..7, 4..7 = sous-etats caches : Start maintenu + Droite),
--    8 ism ($133), A choix commun, C fini ; « EX » = Start maintenu a la validation (grille 0x5C5420) ;
--  * combat : vie de J1 maintenue, vie de l'adversaire ramenee a 1 apres 60 images, J1 avance et frappe.
-- Variables :
--  OUT (journal), NF (derniere image), MODEJEU (1|4), MODEFORCE (n : ecrit le curseur $FF4201 = n, entrees 0/2/3),
--  LISTE = "J1/J2,J1/J2,..." une paire par selection ; joueur = perso(hexa, id de base).famille[.options]
--     famille Z | Z2 | A | Z3 ; options : S (Start maintenu = EX), m0..m7 (mode ZERO 3), iX|iA|iV (ism)
--     ex. "00.A.S/01.Z" ; en TRAINING, la 2e moitie est le mannequin (choisi avec la manette J1).
--  SNAPM=1 : captures ecran VS + 60 et combat + 150 de chaque selection ; NOROUL (defaut 1) : voir hyper.lua.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local out = io.open(os.getenv("OUT"), "w")
local NF = tonumber(os.getenv("NF") or "40000")
local MODEJEU = tonumber(os.getenv("MODEJEU") or "1")
local MODEFORCE = tonumber(os.getenv("MODEFORCE") or "")
local SNAPM = os.getenv("SNAPM") == "1"
local SN = {}                                                -- SNAPS="n,n,..." : captures a ces images
for x in string.gmatch(os.getenv("SNAPS") or "", "%d+") do SN[tonumber(x)] = true end
local J = {0xFF8400, 0xFF8800}
local GRILLE = {0xff,0xff,0xa6,0x0a,0x67,0xff,0xff,0xff,0xff,0x20,0x03,0x04,0x0b,0x21,0xff,0xff,0x22,0x0c,0x07,0x1a,0x08,0x02,0x17,0x3f,0x00,0x18,0x1b,0x1d,0x1c,0x19,0x01,0x3f,0x1e,0x0f,0x06,0x16,0x05,0x10,0x1f,0x3f,0xff,0x23,0x0e,0x0d,0x11,0x15,0xff,0xff,0xff,0xff,0x69,0x09,0xa8,0xff,0xff,0xff,0xff,0xff,0x3f,0x3f,0x3f,0xff,0xff,0xff}
local VERS = {0x30,0x40,0x60,0x00,0x31,0x41,0x61,0x01,0x32,0x42,0x62,0x02,0x33,0x43,0x63,0x03,0x34,0x44,0x64,0x04,0x35,0x45,0x65,0x05,0x36,0x46,0x66,0x06,0x37,0x47,0x67,0x07,0x38,0x48,0x68,0x08,0x39,0x49,0x69,0x09,0x3a,0x4a,0x6a,0x0a,0x3b,0x4b,0x6b,0x0b,0x3c,0x4c,0x6c,0x0c,0x4d,0x6d,0x0d,0xff,0x4e,0x6e,0x0e,0xff,0x4f,0x6f,0x0f,0xff,0x50,0x70,0x10,0xff,0x51,0x71,0x11,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x15,0xff,0xff,0xff,0x7e,0x16,0xff,0xff,0x57,0x77,0x17,0xff,0x18,0xff,0xff,0xff,0x19,0xff,0xff,0xff,0x1a,0xff,0xff,0xff,0x1b,0xff,0xff,0xff,0x1c,0xff,0xff,0xff,0x1d,0xff,0xff,0xff,0x1e,0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x20,0xff,0xff,0xff,0x21,0xff,0xff,0xff,0x22,0xff,0xff,0xff,0x23,0xff,0xff,0xff,0x32,0x42,0x62,0x02,0x15,0xff,0xff,0xff}
local function u8(a) return mem:read_u8(a) end              -- adresses 68K (octet PS2 X = octet 68K X^1)
local function u16(a) return mem:read_u16(a) end
-- liste des selections
local LISTE = {}
for paire in string.gmatch(os.getenv("LISTE") or "00.A/01.Z", "[^,]+") do
  local t = {}
  for spec in string.gmatch(paire, "[^/]+") do
    local f = {}
    for x in string.gmatch(spec, "[^.]+") do f[#f + 1] = x end
    local s = {base = tonumber(f[1], 16), fam = f[2] or "Z3", ex = false, mode = 0, ism = 0, txt = spec}
    for i = 3, #f do
      if f[i] == "S" then s.ex = true
      elseif string.match(f[i], "^m%d$") then s.mode = tonumber(string.sub(f[i], 2))
      elseif f[i] == "iX" then s.ism = -1 elseif f[i] == "iA" then s.ism = 0 elseif f[i] == "iV" then s.ism = 1 end
    end
    t[#t + 1] = s
  end
  LISTE[#LISTE + 1] = t
end
local function famille(id)
  if id < 0x30 then return "Z3" elseif id < 0x40 then return "Z" elseif id < 0x60 then return "Z2" else return "A" end
end
local function colonne(s)                                    -- colonne de la grille des versions pour la famille voulue
  for c = 0, 3 do
    local id = VERS[s.base * 4 + c + 1]
    if id ~= 0xff and famille(id) == s.fam then return c end
  end
  return nil
end
-- deplacement du curseur perso, regles du jeu (mips 0x3198CC) : pas modulo 8, $3F traverse, bit 6+joueur = mur
local DIRS = {{"Right", 1, 0}, {"Left", -1, 0}, {"Down", 0, 1}, {"Up", 0, -1}}
local function pas(x, y, dx, dy, j)
  for _ = 1, 8 do
    x = (x + dx) & 7; y = (y + dy) & 7
    local c = GRILLE[y * 8 + x + 1]
    if c ~= 0x3f then
      if (c >> (6 + j)) & 1 == 1 then return nil end
      return x, y
    end
  end
  return nil
end
local function chemin(x0, y0, base, j)                       -- premiere direction d'un plus court chemin (BFS)
  local vu, file = {[y0 * 8 + x0] = "ici"}, {{x0, y0}}
  local i = 1
  while i <= #file do
    local x, y = file[i][1], file[i][2]; i = i + 1
    if GRILLE[y * 8 + x + 1] & 0x3f == base then
      local k = y * 8 + x
      while vu[k] ~= "ici" and vu[k][2] ~= y0 * 8 + x0 do k = vu[k][2] end
      return vu[k] == "ici" and nil or vu[k][1]
    end
    for _, d in ipairs(DIRS) do
      local nx, ny = pas(x, y, d[2], d[3], j)
      if nx and not vu[ny * 8 + nx] then vu[ny * 8 + nx] = {d[1], y * 8 + x}; file[#file + 1] = {nx, ny} end
    end
  end
  return nil
end
-- INPUTS (format de hyper.lua / diag.py) : entrees supplementaires a des images fixes (essais)
local seq = {}
for item in string.gmatch(os.getenv("INPUTS") or "", "[^;]+") do
  local a, b2, p, f = string.match(item, "^(%d+)-(%d+):(:[%w]+):(.+)$")
  if a then seq[#seq + 1] = {tonumber(a), tonumber(b2), p .. "|" .. f} end
end
-- etat du script
local k, last, nsel, combats, stable, debut_vs, vs_vu, scene_e = 0, "", 0, 0, 0, nil, false, 0
local en_sel = {false, false}
local bloque = {0, 0}
local v = {}
local function on(p, f) v[p .. "|" .. f] = 1 end
local function manette(j) if MODEJEU == 4 then return "P1" else return j == 1 and "P1" or "P2" end end
local function appui(j, quoi) if k % 8 < 3 then on(":IN0", manette(j) .. " " .. quoi) end end
local function start(j) on(":IN2", (MODEJEU == 4 or j == 1) and "1 Player Start" or "2 Players Start") end
local function selectionne(j, s)                             -- un pas de pilotage de la selection du joueur j
  local P = J[j]; local et = u8(P + 5)
  if et == 0 then
    local x, y = u16(P + 0x12) & 7, u16(P + 0x16) & 7
    local d = chemin(x, y, s.base, j - 1)
    if d then appui(j, d) else
      if s.ex then start(j) end
      if k % 16 >= 8 and k % 16 < 11 then on(":IN0", manette(j) .. " Button 1") end
    end
  elseif et == 2 then
    local c = colonne(s) or 0
    if u8(P + 0x5C) ~= c then appui(j, "Down") else
      if s.ex then start(j) end
      if k % 16 >= 8 and k % 16 < 11 then on(":IN0", manette(j) .. " Button 1") end
    end
  elseif et == 6 then
    local base = ({[0] = 0, 1, 2, 3, 3, 1, 0, 2})[s.mode]
    local m = u8(P + 0x5C)
    if m == s.mode then appui(j, "Button 1")
    elseif m <= 3 and m ~= base then appui(j, "Down")
    else start(j); if k % 16 >= 8 and k % 16 < 11 then on(":IN0", manette(j) .. " Right") end end
  elseif et == 8 then
    local i = u8(P + 0x133); if i >= 0x80 then i = i - 0x100 end
    if i ~= s.ism then appui(j, "Down") else appui(j, "Button 1") end
  elseif et == 4 or et == 0xA then appui(j, "Button 1")
  end
end
emu.register_frame_done(function()
  k = k + 1
  v = {}
  local p0, p4, p8, pc_, p10 = u16(0xFF8000), u16(0xFF8004), u16(0xFF8008), u16(0xFF800C), u16(0xFF8010)
  -- titre et menu (A5+0 = 6 titre, 4 menu ; A5+0 = 2 jeu)
  if p0 == 6 or p0 == 4 or (p0 == 2 and p4 == 0) then
    if k > 200 and k % 60 < 6 and k < 900 then on(":IN2", "Coin 1"); if MODEJEU == 1 then on(":IN2", "Coin 2") end end
    if p0 == 6 and k > 300 and k % 40 < 6 then on(":IN2", "1 Player Start") end
    if p0 == 4 then
      if MODEFORCE then mem:write_u8(0xFF4201, MODEFORCE) end
      local cur = u8(0xFF4201)
      if not MODEFORCE and cur ~= MODEJEU then if k % 20 < 4 then on(":IN0", "P1 Down") end
      elseif k % 20 >= 10 and k % 20 < 14 then on(":IN0", "P1 Button 1") end
    end
  end
  -- selection (A5+4 = 2) : chaque joueur dont l'etat ($5) est < $C est pilote selon sa specification
  if SN[k] then manager.machine.video:snapshot() end
  if p0 == 2 and p4 == 2 and p8 == 4 then
    if MODEJEU == 1 and (u8(0xFF80A9) & 2) == 0 and k % 30 < 4 then on(":IN2", "2 Players Start") end
    for j = 1, 2 do
      local P = J[j]; local et = u8(P + 5)
      local actif = (MODEJEU == 1) or j == 1 or u8(J[1] + 5) == 0xC
      if u8(P + 1) ~= 0 and et < 0xC and actif then
        if not en_sel[j] then
          en_sel[j] = true; bloque[j] = 0
          if j == 1 then nsel = nsel + 1; vs_vu = false; debut_vs = nil
            out:write(string.format("SELECTION %d image %d\n", nsel, k)) end
        end
        local paire = LISTE[((nsel - 1) % #LISTE) + 1]
        local s = paire[j] or paire[1]
        selectionne(j, s)
        bloque[j] = bloque[j] + 1
        if bloque[j] == 3000 then out:write(string.format("BLOQUE J%d image %d etat %02x/%02x\n", j, k, et, u8(P + 4))) end
      end
    end
  end
  -- fin de selection d'un joueur (etat $C), journal du choix (aussi quand la scene passe a A5+8 = 8 la meme image)
  for j = 1, 2 do
    local P = J[j]
    if en_sel[j] and u8(P + 5) == 0xC then
      en_sel[j] = false
      out:write(string.format("CHOIX J%d image %d : $102=%02x base=%02x drapeaux=%02x mode=%02x $123=%02x $15F=%02x ism=%02x (%s)\n",
        j, k, u8(P + 0x103), u8(P + 0x117), u8(P + 0x116), u8(P + 0x5C), u8(P + 0x123), u8(P + 0x15F), u8(P + 0x133),
        ((LISTE[((nsel - 1) % #LISTE) + 1])[j] or {txt = "?"}).txt))
    end
  end
  -- autres ecrans de la scene de selection (A5+8 = $A HANDICAP en VERSUS, etc.) : bouton 1 des deux joueurs
  if p0 == 2 and p4 == 2 and p8 ~= 4 and k % 24 >= 12 and k % 24 < 15 then
    on(":IN0", "P1 Button 1"); if MODEJEU == 1 then on(":IN0", "P2 Button 1") end
  end
  -- scene de fin de match VERSUS (A5+4 = $E, dispatcher mips 0x2D550 absent de la traduction : A5+8 croit sans fin).
  -- CONTOURNE_E=1 : apres 120 images, retour force a la selection (A5+4 = 2, A5+8/C/10 = 0, champs de selection des
  -- joueurs remis a 0 comme l'init. 0x95C84), signale au journal.
  if p0 == 2 and p4 == 0xE then
    scene_e = scene_e + 1
    if scene_e == 1 then out:write(string.format("SCENE_E image %d (fin de match VERSUS)\n", k)) end
    if scene_e == 120 and os.getenv("CONTOURNE_E") == "1" then
      out:write(string.format("CONTOURNEMENT scene E image %d : A5+4 <- 2, A5+8/C/10 <- 0\n", k))
      mem:write_u16(0xFF8004, 2); mem:write_u16(0xFF8008, 0); mem:write_u16(0xFF800C, 0); mem:write_u16(0xFF8010, 0)
      -- champs remis a 0 par l'init. des joueurs au lancement du mode (mips 0x95C84) + $3D (etapes de selection)
      for _, P in ipairs(J) do
        for _, o in ipairs({0x3D, 0x118, 0x120, 0x123, 0x129, 0x130, 0x131, 0x133, 0x148, 0x14A, 0x15A, 0x15B, 0x15C, 0x15D,
                            0x15E, 0x15F, 0x162, 0x163}) do mem:write_u8(P + o, 0) end
      end
    end
  else scene_e = 0 end
  -- ecran VS (A5+4 = 4, A5+8 = 4)
  if p4 == 4 and p8 == 4 and not vs_vu then vs_vu = true; debut_vs = k end
  if SNAPM and debut_vs and k == debut_vs + 60 then manager.machine.video:snapshot() end
  -- combat
  local adv = {}
  for _, o in ipairs({J[2], 0xFF8C00, 0xFF9000}) do if u8(o + 5) == 2 then adv[#adv + 1] = o end end
  local combat = p0 == 2 and p4 == 4 and p8 == 6 and u8(J[1] + 5) == 2 and #adv > 0
  if combat then
    stable = stable + 1
    if stable == 1 then combats = combats + 1
      out:write(string.format("MANCHE %d image %d J1 %02x/%02x J2 %02x/%02x\n", combats, k, u8(J[1] + 0x103), u8(J[1] + 0xD2),
        u8(J[2] + 0x103), u8(J[2] + 0xD2))) end
    if SNAPM and stable == 150 then manager.machine.video:snapshot() end
    mem:write_u16(J[1] + 0x50, 0x90); mem:write_u16(J[1] + 0x52, 0x90)
    if stable > 60 then
      for _, o in ipairs(adv) do
        local vie = u16(o + 0x50)
        if vie > 1 and vie < 0x100 then mem:write_u16(o + 0x50, 1); mem:write_u16(o + 0x52, 1) end
      end
      local av = (u16(J[1] + 0x12) < u16(adv[1] + 0x12)) and "Right" or "Left"
      local t = stable % 40                                   -- boule de feu (bas, bas-avant, avant + poing) ou coup
      if t < 3 then on(":IN0", "P1 Down") elseif t < 6 then on(":IN0", "P1 Down"); on(":IN0", "P1 " .. av)
      elseif t < 10 then on(":IN0", "P1 " .. av); if t >= 7 then on(":IN0", "P1 Button 1") end
      elseif t < 30 then on(":IN0", "P1 " .. av); if t % 6 < 2 then on(":IN0", "P1 Button 4") end end
    end
  else stable = 0 end
  for _, e in ipairs(seq) do if k >= e[1] and k <= e[2] then v[e[3]] = 1 end end
  -- journal des transitions
  local st = string.format("%04x %04x %04x %04x %04x | J1 %02x %02x %02x %02x | J2 %02x %02x %02x %02x",
    p0, p4, p8, pc_, p10, u8(J[1] + 1), u8(J[1] + 5), u8(J[1] + 0x103), u8(J[1] + 0xD2),
    u8(J[2] + 1), u8(J[2] + 5), u8(J[2] + 0x103), u8(J[2] + 0xD2))
  if st ~= last then out:write(string.format("%6d : %s\n", k, st)); last = st end
  -- exceptions (comme hyper.lua)
  local pc = cpu.state["PC"].value & 0xffffff
  local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then
    out:write(string.format("EXCEPTION %d pc=%x\n", k, pc)); manager.machine.video:snapshot(); out:close(); manager.machine:exit(); return
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k >= NF then out:write(string.format("FIN %d selections %d manches %d\n", k, nsel, combats)); out:close(); manager.machine:exit() end
end)
-- NOROUL : drapeau « Start » de selection neutralise (roulette aleatoire ; cf. hyper.lua et ETATS-HYPER.md §1.4)
if os.getenv("NOROUL") ~= "0" then
  _G.TAPR = {}
  for _, a in ipairs({0xFF84D2, 0xFF88D2}) do
    _G.TAPR[#_G.TAPR + 1] = mem:install_write_tap(a, a + 1, "noroul" .. a, function(off, data, mask)
      if mask & 0x00ff ~= 0 then return data & 0xff00 end
    end)
  end
end
-- couches du banc (work/mame) : HSFA_BANC_LUA les situe (scripts/validation/valide_tout.sh la pose)
local BANC = os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame"
dofile(BANC .. "/banc_mem.lua"); dofile(BANC .. "/banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile(BANC .. "/banc_sprites.lua") end
