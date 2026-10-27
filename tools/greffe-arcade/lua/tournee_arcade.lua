-- (greffe_arcade, etape 2) PARTIE ARCADE DANS HYPER AUGMENTE (ro9a) sur le fork sfa3hx.
-- D'apres agent_hyper_etats/lua/tournee_hyper.lua : titre -> menu (curseur $FF4201 = 0, ARCADE) -> selection J1 seul
-- -> combats (vie de J1 maintenue, vie de l'adversaire ramenee a 1 apres 60 images, J1 avance et frappe) ; entre les
-- combats (carte, face-a-face, citation) : Start et bouton 1 de J1.
-- Variables : OUT (journal), NF, PERSO (spec J1, format de tournee_hyper : "00.Z3"), SNAPETAT=1 (capture 40 images
--   apres la 1re apparition de chaque etat A5+4/+8/+C), SNAPS="n,n" (captures), GRAINE=hhhh (graine du hasard $FF80AE
--   imposee pendant la fin de selection A5+4=2/A5+8=6 : liste des adversaires reproductible, comparable a Upper),
--   LISTE_ADV=hhhhhh (adresse 68K de la liste des adversaires : $FF43BE dans ro9a, $FF40C0 dans Upper),
--   PERDRE=1 (J1 passif, vie a 1), CONTINUE=1 (Start sur l'ecran CONTINUE), MENU=1 (menu par les entrees : sinon
--   curseur force a 0).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local out = io.open(os.getenv("OUT"), "w")
local NF = tonumber(os.getenv("NF") or "40000")
local SNAPETAT = os.getenv("SNAPETAT") == "1"
local PERDRE = os.getenv("PERDRE") == "1"
local GRAINE = tonumber(os.getenv("GRAINE") or "", 16)
local LISTE_ADV = tonumber(os.getenv("LISTE_ADV") or "FF4B2E", 16)
local SN = {}
for x in string.gmatch(os.getenv("SNAPS") or "", "%d+") do SN[tonumber(x)] = true end
local J = {0xFF8400, 0xFF8800}
local GRILLE = {0xff,0xff,0xa6,0x0a,0x67,0xff,0xff,0xff,0xff,0x20,0x03,0x04,0x0b,0x21,0xff,0xff,0x22,0x0c,0x07,0x1a,0x08,0x02,0x17,0x3f,0x00,0x18,0x1b,0x1d,0x1c,0x19,0x01,0x3f,0x1e,0x0f,0x06,0x16,0x05,0x10,0x1f,0x3f,0xff,0x23,0x0e,0x0d,0x11,0x15,0xff,0xff,0xff,0xff,0x69,0x09,0xa8,0xff,0xff,0xff,0xff,0xff,0x3f,0x3f,0x3f,0xff,0xff,0xff}
local VERS = {0x30,0x40,0x60,0x00,0x31,0x41,0x61,0x01,0x32,0x42,0x62,0x02,0x33,0x43,0x63,0x03,0x34,0x44,0x64,0x04,0x35,0x45,0x65,0x05,0x36,0x46,0x66,0x06,0x37,0x47,0x67,0x07,0x38,0x48,0x68,0x08,0x39,0x49,0x69,0x09,0x3a,0x4a,0x6a,0x0a,0x3b,0x4b,0x6b,0x0b,0x3c,0x4c,0x6c,0x0c,0x4d,0x6d,0x0d,0xff,0x4e,0x6e,0x0e,0xff,0x4f,0x6f,0x0f,0xff,0x50,0x70,0x10,0xff,0x51,0x71,0x11,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x15,0xff,0xff,0xff,0x7e,0x16,0xff,0xff,0x57,0x77,0x17,0xff,0x18,0xff,0xff,0xff,0x19,0xff,0xff,0xff,0x1a,0xff,0xff,0xff,0x1b,0xff,0xff,0xff,0x1c,0xff,0xff,0xff,0x1d,0xff,0xff,0xff,0x1e,0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x20,0xff,0xff,0xff,0x21,0xff,0xff,0xff,0x22,0xff,0xff,0xff,0x23,0xff,0xff,0xff,0x32,0x42,0x62,0x02,0x15,0xff,0xff,0xff}
local function u8(a) return mem:read_u8(a) end
local function u16(a) return mem:read_u16(a) end
local spec = {base = 0, fam = "Z3", ex = false, mode = 0, ism = 0}
do
  local f = {}
  for x in string.gmatch(os.getenv("PERSO") or "00.Z3", "[^.]+") do f[#f + 1] = x end
  spec.base = tonumber(f[1], 16); spec.fam = f[2] or "Z3"
  for i = 3, #f do
    if f[i] == "S" then spec.ex = true elseif string.match(f[i], "^m%d$") then spec.mode = tonumber(string.sub(f[i], 2))
    elseif f[i] == "iX" then spec.ism = -1 elseif f[i] == "iA" then spec.ism = 0 elseif f[i] == "iV" then spec.ism = 1 end
  end
end
local function famille(id)
  if id < 0x30 then return "Z3" elseif id < 0x40 then return "Z" elseif id < 0x60 then return "Z2" else return "A" end
end
local function colonne(s)
  for c = 0, 3 do
    local id = VERS[s.base * 4 + c + 1]
    if id ~= 0xff and famille(id) == s.fam then return c end
  end
  return nil
end
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
local function chemin(x0, y0, base, j)
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
local k, last, combats, stable, etats, nsc = 0, "", 0, 0, {}, 0
-- COUV=<fichier> : couverture par prise sur l'espace OPCODES (mot lu -> premiere image, par etat A5+0/+4/+8/+C)
local ops = cpu.spaces["opcodes"] or mem
local COUV = os.getenv("COUV")
local S, stid, cetats, cn = {}, 0, {}, 0
if COUV then
  CT = ops:install_read_tap(0x0, 0x3bffff, "couv", function(o, d, m)
    local key = (o >> 1) * 512 + stid
    if not S[key] then S[key] = k end
  end)
end
local function ecrit_couv()
  if not COUV then return end
  local f = io.open(COUV, "w")
  for nom, id in pairs(cetats) do f:write(string.format("E %d %s\n", id, nom)) end
  for key, fr in pairs(S) do f:write(string.format("%x %d %d\n", (key // 512) * 2, key % 512, fr)) end
  f:close()
end
-- (etape 3) JVARS="ff8104,ff814b,..." : octets 68K ajoutes a la ligne d'etat du journal
local JVL = {}
for x in string.gmatch(os.getenv("JVARS") or "", "%x+") do JVL[#JVL + 1] = tonumber(x, 16) end
function JV()
  if #JVL == 0 then return "" end
  local t = {}
  for _, a in ipairs(JVL) do t[#t + 1] = string.format("%02x", u8(a)) end
  return " | " .. table.concat(t, " ")
end
local snapq = {}
local v = {}
local function on(p, f) v[p .. "|" .. f] = 1 end
local function appui(quoi) if k % 8 < 3 then on(":IN0", "P1 " .. quoi) end end
local function selectionne(s)
  local P = J[1]; local et = u8(P + 5)
  if et == 0 then
    local x, y = u16(P + 0x12) & 7, u16(P + 0x16) & 7
    local d = chemin(x, y, s.base, 0)
    if d then appui(d) else
      if s.ex then on(":IN2", "1 Player Start") end
      if k % 16 >= 8 and k % 16 < 11 then on(":IN0", "P1 Button 1") end
    end
  elseif et == 2 then
    local c = colonne(s) or 0
    if u8(P + 0x5C) ~= c then appui("Down") else
      if k % 16 >= 8 and k % 16 < 11 then on(":IN0", "P1 Button 1") end
    end
  elseif et == 6 then
    if u8(P + 0x5C) == s.mode then appui("Button 1") else appui("Down") end
  elseif et == 8 then
    local i = u8(P + 0x133); if i >= 0x80 then i = i - 0x100 end
    if i ~= s.ism then appui("Down") else appui("Button 1") end
  elseif et == 4 or et == 0xA then appui("Button 1")
  end
end
local function liste()
  local t = {}
  for i = 0, 15 do t[#t + 1] = string.format("%02x", u8(LISTE_ADV + (i ~ 1))) end
  return table.concat(t, "")
end
emu.register_frame_done(function()
  if FINI then return end
  k = k + 1
  v = {}
  local p0, p4, p8, pc_, p10 = u16(0xFF8000), u16(0xFF8004), u16(0xFF8008), u16(0xFF800C), u16(0xFF8010)
  -- titre et menu
  if p0 == 6 or p0 == 4 or (p0 == 2 and p4 == 0) then
    if k > 200 and k % 60 < 6 and k < 900 then on(":IN2", "Coin 1") end
    if p0 == 6 and k > 300 and k % 40 < 6 then on(":IN2", "1 Player Start") end
    if p0 == 4 then
      if os.getenv("MENU") ~= "1" then mem:write_u8(0xFF4201, 0) end
      local cur = u8(0xFF4201)
      if cur ~= 0 then if k % 20 < 4 then on(":IN0", "P1 Up") end
      elseif k % 20 >= 10 and k % 20 < 14 then on(":IN0", "P1 Button 1") end
    end
  end
  -- selection : J1 seul
  if p0 == 2 and p4 == 2 and p8 == 4 then
    if u8(J[1] + 1) ~= 0 and u8(J[1] + 5) < 0xC then selectionne(spec) end
  end
  if p0 == 2 and p4 == 2 and p8 ~= 4 and k % 24 >= 12 and k % 24 < 15 then on(":IN0", "P1 Button 1") end
  -- graine du hasard imposee pendant la fin de selection (liste des adversaires reproductible)
  if GRAINE and p0 == 2 and p4 == 2 and p8 == 6 then mem:write_u16(0xFF80AE, GRAINE) end
  -- combat
  local adv = {}
  for _, o in ipairs({J[2], 0xFF8C00, 0xFF9000}) do if u8(o + 5) == 2 then adv[#adv + 1] = o end end
  local combat = p0 == 2 and p4 == 4 and p8 == 6 and u8(J[1] + 5) == 2 and #adv > 0
  if combat then
    stable = stable + 1
    if stable == 1 then combats = combats + 1
      out:write(string.format("MANCHE %d image %d J1 %02x/%02x/%02x J2 %02x/%02x/%02x etape %04x decor %04x liste %s\n", combats, k,
        u8(J[1] + 0x103), u8(J[1] + 0x117), u8(J[1] + 0x116), u8(J[2] + 0x103), u8(J[2] + 0x117), u8(J[2] + 0x116),
        u16(0xFF8114), u16(0xFF8100), liste())) end
    if not PERDRE then mem:write_u16(J[1] + 0x50, 0x90); mem:write_u16(J[1] + 0x52, 0x90) end
    if stable > 60 then
      if PERDRE then
        local v1 = u16(J[1] + 0x50)
        if v1 > 1 and v1 < 0x100 then mem:write_u16(J[1] + 0x50, 1); mem:write_u16(J[1] + 0x52, 1) end
      else
        for _, o in ipairs(adv) do
          local vie = u16(o + 0x50)
          if vie > 1 and vie < 0x100 then mem:write_u16(o + 0x50, 1); mem:write_u16(o + 0x52, 1) end
        end
        local av = (u16(J[1] + 0x12) < u16(adv[1] + 0x12)) and "Right" or "Left"
        local t = stable % 40
        if t < 3 then on(":IN0", "P1 Down") elseif t < 6 then on(":IN0", "P1 Down"); on(":IN0", "P1 " .. av)
        elseif t < 10 then on(":IN0", "P1 " .. av); if t >= 7 then on(":IN0", "P1 Button 1") end
        elseif t < 30 then on(":IN0", "P1 " .. av); if t % 6 < 2 then on(":IN0", "P1 Button 4") end end
      end
    end
  else
    stable = 0
    -- hors combat, en partie : Start et bouton 1 (textes, PRESS START, CONTINUE)
    -- (etape 3) NOCONT=1 : rien sur l'ecran CONTINUE (A5+4 = 6) -> GAME OVER
    -- (etape 3) SCENEA_PASSIF=1 : aucune touche pendant la fin (A5+4 = A) : classement et fin comme dans l'oracle
    if p0 == 2 and p4 ~= 2 and p4 ~= 0 and not (os.getenv("NOCONT") == "1" and p4 == 6)
       and not (os.getenv("SCENEA_PASSIF") == "1" and p4 == 0xA)
       and not (PERDRE and combats > 0) then   -- (etape 6) PERDRE : aucune touche apres le 1er combat (sinon Start abrege la defaite, comme un 2e joueur)
      if k % 30 < 3 then on(":IN2", "1 Player Start") end
      if k % 30 >= 15 and k % 30 < 18 then on(":IN0", "P1 Button 1") end
    end
  end
  -- journal
  local st = string.format("%04x %04x %04x %04x %04x | J1 %02x %02x %02x %02x | J2 %02x %02x %02x %02x | $A9 %02x $100 %04x",
    p0, p4, p8, pc_, p10, u8(J[1] + 1), u8(J[1] + 5), u8(J[1] + 0x103), u8(J[1] + 0xD2),
    u8(J[2] + 1), u8(J[2] + 5), u8(J[2] + 0x103), u8(J[2] + 0xD2), u8(0xFF80A9), u16(0xFF8100)) .. JV()
  if st ~= last then out:write(string.format("%6d : %s\n", k, st)); last = st; immobile = 0 else immobile = (immobile or 0) + 1 end
  if immobile and immobile > tonumber(os.getenv("BLOCAGE") or "4000") and not combat then
    FINI = true; manager.machine.video:snapshot()
    out:write(string.format("BLOQUE %d etat %s\n", k, st)); out:close(); ecrit_couv(); manager.machine:exit(); return
  end
  local nom = string.format("%04x %04x %04x %04x", p0, p4, p8, pc_)
  if not cetats[nom] then cn = cn + 1; cetats[nom] = cn end
  stid = cetats[nom]
  if not etats[nom] then
    etats[nom] = k; nsc = nsc + 1
    if SNAPETAT and p0 == 2 then snapq[k + 40] = nom end
  end
  -- (etape 3) SNAPSC=n : une capture toutes les n images dans les scenes 6/8/A/C (continue, game over, fin, sortie)
  local SNAPSC = tonumber(os.getenv("SNAPSC") or "0")
  if SNAPSC > 0 and k % SNAPSC == 0 and p0 == 2 and (p4 == 6 or p4 == 8 or p4 == 0xA or p4 == 0xC) then snapq[k] = snapq[k] or nom end
  if snapq[k] or SN[k] then manager.machine.video:snapshot(); out:write(string.format("SNAP %d %s\n", k, snapq[k] or nom)) end
  -- exceptions
  local pc = cpu.state["PC"].value & 0xffffff
  local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then
    if FINI then return end
    FINI = true
    local sp = cpu.state["SP"].value & 0xffffff
    local pl = {}
    for i = 0, 47 do pl[#pl + 1] = string.format("%04x", u16(sp + 2 * i)) end
    out:write("PILE " .. table.concat(pl, " ") .. "\n")
    if TRACEPC then RING_DUMP() end
    out:write(string.format("EXCEPTION %d pc=%x sp=%x pile=%04x %04x%04x %04x %04x %04x%04x\n", k, pc, sp, u16(sp), u16(sp + 2), u16(sp + 4),
      u16(sp + 6), u16(sp + 8), u16(sp + 10), u16(sp + 12)))
    local function reg(n) local e = cpu.state[n]; return e and e.value or 0 end
    for r = 0, 7 do out:write(string.format("  D%d=%08x A%d=%08x\n", r, reg("D" .. r), r, reg("A" .. r))) end
    local a6 = reg("A6") & 0xffffff
    for _, base in ipairs({a6, reg("A4") & 0xffffff}) do
      local t = {}
      for i = 0, 31 do t[#t + 1] = string.format("%04x", u16(base + 2 * i)) end
      out:write(string.format("MEM %06x %s\n", base, table.concat(t, " ")))
    end
    manager.machine.video:snapshot(); out:close(); ecrit_couv(); manager.machine:exit(); return
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  -- (etape 5) ARRET_FIN=1 : arret des que la partie revient en scene C (ou 0/2) APRES la fin (scene A) : balayage des fins
  if os.getenv("ARRET_FIN") == "1" then
    if p0 == 2 and p4 == 0xA and not _VU_A then _VU_A = k; out:write(string.format("SCENE_A %d\n", k)) end
    if _VU_A and p4 ~= 0xA and not _FIN_A then _FIN_A = k; out:write(string.format("FIN_A %d duree %d scene %x\n", k, k - _VU_A, p4)) end
    if _FIN_A and k >= _FIN_A + 300 then FINI = true; out:write(string.format("FIN %d manches %d\n", k, combats)); out:close(); ecrit_couv(); manager.machine:exit(); return end
  end
  if k >= NF then FINI = true; out:write(string.format("FIN %d manches %d\n", k, combats)); out:close(); ecrit_couv(); manager.machine:exit() end
end)
-- SURV="adresse:longueur:image" : prise d'ecriture, journal (image, PC, adresse, donnee) des 40 premieres ecritures
-- a partir de l'image donnee
if os.getenv("SURV") then
  local a, l, f0 = string.match(os.getenv("SURV"), "(%x+):(%x+):(%d+)")
  a = tonumber(a, 16); l = tonumber(l, 16); f0 = tonumber(f0)
  local nw = 0
  _G.TAPS = mem:install_write_tap(a, a + l - 1, "surv", function(o, d, m)
    if k >= f0 and nw < tonumber(os.getenv("SURV_N") or "40") then
      nw = nw + 1
      local sp = cpu.state["SP"].value & 0xffffff
      local pl = {}
      for i = 0, 15 do pl[#pl + 1] = string.format("%04x", mem:read_u16(sp + 2 * i)) end
      out:write(string.format("ECRIT %d pc=%06x %06x %04x %04x pile %s\n", k, cpu.state["PC"].value & 0xffffff, o, d, m, table.concat(pl, " ")))
    end
  end)
end
-- TRACEPC=image : a partir de cette image, anneau des 400 derniers mots d'opcodes lus (hors boucle d'attente),
-- vide dans le journal a l'exception (lignes TRACE)
TRACEPC = tonumber(os.getenv("TRACEPC") or "")
ring, ri = {}, 0
_G.RING_DUMP = function()
  local t = {}
  for i = 1, 400 do local x = ring[((ri + i - 1) % 400) + 1]; if x then t[#t + 1] = string.format("%x", x) end end
  out:write("TRACE " .. table.concat(t, " ") .. "\n")
end
if TRACEPC then
  local last = -10
  _G.TAPPC = ops:install_read_tap(0x0, 0x3bffff, "tracepc", function(o, d, m)
    if o >= 0xA00 and o < 0xA80 then GELE = true end
    if k >= TRACEPC and not GELE and (o < last or o > last + 6) then ri = ri % 400 + 1; ring[ri] = o end
    last = o
  end)
end
if os.getenv("NOROUL") ~= "0" then
  _G.TAPR = {}
  for _, a in ipairs({0xFF84D2, 0xFF88D2}) do
    _G.TAPR[#_G.TAPR + 1] = mem:install_write_tap(a, a + 1, "noroul" .. a, function(off, data, mask)
      if mask & 0x00ff ~= 0 then return data & 0xff00 end
    end)
  end
end
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end
