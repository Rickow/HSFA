-- (banc_coups) BANC DE TEST DES COUPS : partie VERSUS a 2 joueurs, J1 = perso teste, J2 = adversaire passif ;
-- au combat stable, SAUVEGARDE D'ETAT PRISE PAR LUA (machine:save), puis pour chaque coup du PLAN : rechargement,
-- remise des positions / vies / jauge, appuis image par image, journal de J1, J2 et des objets.
-- Modules (variable MODULE, voir lance.sh) : ref3 (arcade sfa3ud, REF=1), ro3, ro5 (Upper, fork), ro9 (Hyper, fork).
-- Variables :
--   OUT  journal ; PLAN  fichier du plan (lignes « T|id|dist|jauge|seqJ1|seqJ2|obs », voir outils/plan.py)
--   PERSO / PERSO2  id $102 (hexa) de J1 / J2 (SFA3, Upper : ecrit pendant la selection) ; ISM = X|A|V (J1)
--   LISTE (Hyper) : « J1/J2 » au format de tournee_hyper.lua (ex. « 00.Z3.iA/01.Z3 », « 00.Z/01.Z3 »)
--   COTE = g (J1 a gauche, defaut) | d (J1 a droite : directions en miroir, resolues a l'execution)
--   NOBS  images d'observation apres la derniere entree (defaut 150) ; DUMP=1 : vidage brut de J1 a chaque image
-- Sequence : jetons separes par des espaces, « n:TOUCHES » (n TOURS DE JEU, 4 pour 3 images en turbo ; TOUCHES = U,D,F,B (avant / arriere selon le
--   cote reel), 1-6 boutons (LP MP HP LK MK HK), S = Start, N = rien ; reunies par « + »), « G:n » = attendre (au plus
--   n images) que J1 soit en garde (octet $5 = 2 (reaction : blocage), variable GARDE), « Y:n » = attendre que J1 quitte le sol.
-- Journal : « T id nom », « F id r e1 e2 x1 y1 x2 vie2 aa ani fp jauge sens tours vie1 d1 d2 » (d = compteur de duree du pas, $32), « O id r adr mot2 etat x », « X id r pc »,
--   « R id fin ».
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local REF = os.getenv("REF") == "1"
local HYPER = os.getenv("HYPER") == "1"
local out = io.open(os.getenv("OUT"), "w")
_G.BANC_OUT = out   -- (scripts ajoutes par LUA_EN_PLUS : journal commun ; BANC_R = image de l'essai, BANC_ID = essai)
local J1, J2 = 0xFF8400, 0xFF8800
local XO, YO = REF and 0x10 or 0x12, REF and 0x14 or 0x16
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
local function w8(a, v) mem:write_u8(REF and a or (a ~ 1), v) end
local function u16(a) return mem:read_u16(a) end
local function u32(a) if REF then return mem:read_u32(a) else return (mem:read_u16(a + 2) << 16) | mem:read_u16(a) end end
local PERSO = tonumber(os.getenv("PERSO") or "", 16)
local PERSO2 = tonumber(os.getenv("PERSO2") or "", 16)
local ISMV = ({X = 0xFF, A = 0, V = 1})[os.getenv("ISM") or ""]
local COTE = os.getenv("COTE") or "g"
local NOBS = tonumber(os.getenv("NOBS") or "150")
local DUMP = os.getenv("DUMP") == "1"
TOURS = 0   -- tours de jeu (copie $51A -> $51C, une par tour ; commandes.lua)
TT = mem:install_write_tap(0xFF851C, 0xFF851D, "tours", function(o, d, m) TOURS = TOURS + 1 end)
-- OPCODES = fichier d'opcodes DECHIFFRES (mots gros-boutistes depuis $000000) : jeu chiffre d'origine (oracle japonais
-- 980727, sfz3jr1) joue avec le pilote sfa3ud (cle Phoenix = pas de dechiffrement) : la ROM reste BRUTE (lectures de
-- donnees exactes) et la memoire d'opcodes (:decrypted_opcodes) recoit programme XOR table « x » (tables sz3jx.03a/.04a)
if os.getenv("OPCODES") then
  local f = io.open(os.getenv("OPCODES"), "rb"); local d = f:read("a"); f:close()
  local sh
  for n, s in pairs(manager.machine.memory.shares) do if string.find(n, "decrypted") then sh = s; OPC_NOM = n end end
  if sh then
    for a = 0, #d - 2, 2 do sh:write_u16(a, (d:byte(a + 1) << 8) | d:byte(a + 2)) end
    print("OPCODES : " .. OPC_NOM .. " <- " .. #d .. " o")
  else print("OPCODES : memoire d'opcodes introuvable") end
end
local champs = {}
for _, p in pairs(ports) do for fn, f in pairs(p.fields) do champs[fn] = f end end
-- ---------------------------------------------------------------- plan
local TESTS = {}
for l in io.lines(os.getenv("PLAN")) do
  local f = {}
  for x in string.gmatch(l .. "|", "([^|]*)|") do f[#f + 1] = x end
  if f[1] == "T" then
    local t = {id = f[2], dist = tonumber(f[3], 16) or 0x60, jauge = tonumber(f[4], 16), s1 = {}, s2 = {}, obs = tonumber(f[7] or "") or NOBS, nom = f[8] or ""}
    for _, c in ipairs({{f[5], t.s1}, {f[6] or "", t.s2}}) do
      for tok in string.gmatch(c[1], "%S+") do
        local n, k = string.match(tok, "^(%d+):(.*)$")
        if n then
          local s = {n = tonumber(n), att = nil, t = {}}
          if k == "G" or k == "Y" then s.att = k else for x in string.gmatch(k, "[^+]+") do s.t[#s.t + 1] = x end end
          c[2][#c[2] + 1] = s
        else
          local k2, n2 = string.match(tok, "^([GY]):(%d+)$")
          if k2 then c[2][#c[2] + 1] = {n = tonumber(n2), att = k2, t = {}} end
        end
      end
    end
    TESTS[#TESTS + 1] = t
  end
end
-- ---------------------------------------------------------------- selection (SFA3 / Upper : ecriture de $102)
local k, sel, stable, phase, ie, r = 0, 0, 0, "menu", 0, 0
local v = {}
local function on(f) v[f] = 1 end
local function sel_sfa3()
  local jeu = u8(0xFF80A8)
  local ecran_sel = u16(0xFF8000) == 2 and u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if k >= 1500 and k < 1860 and k % 60 < 8 then on("Coin 1") end
  if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on("1 Player Start") end
  if k >= 2000 and k % 40 >= 20 and k % 40 < 26 and jeu & 1 == 1 and jeu & 2 == 0 then on("2 Players Start") end
  if PERSO and ecran_sel and sel < 120 then w8(J1 + 0x102, PERSO) end
  if PERSO2 and ecran_sel and sel < 120 then w8(J2 + 0x102, PERSO2) end
  local combat = u16(0xFF800C) == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2
  -- isme impose jusqu'au combat (l'init. de manche lit $132 : lignes du bloc d'animation, marche, sauts)
  if ISMV and not combat and k > 2000 then w8(J1 + 0x132, ISMV) end
  if k >= 2100 and k % 24 < 4 and jeu == 3 and not combat and (not ecran_sel or sel >= 120) then on("P1 Button 1"); on("P2 Button 1") end
  return combat and u8(J1 + 7) == 2 and u8(J2 + 7) == 2
end
-- ---------------------------------------------------------------- selection Hyper (copie de tournee_hyper.lua)
local GRILLE = {0xff,0xff,0xa6,0x0a,0x67,0xff,0xff,0xff,0xff,0x20,0x03,0x04,0x0b,0x21,0xff,0xff,0x22,0x0c,0x07,0x1a,0x08,0x02,0x17,0x3f,0x00,0x18,0x1b,0x1d,0x1c,0x19,0x01,0x3f,0x1e,0x0f,0x06,0x16,0x05,0x10,0x1f,0x3f,0xff,0x23,0x0e,0x0d,0x11,0x15,0xff,0xff,0xff,0xff,0x69,0x09,0xa8,0xff,0xff,0xff,0xff,0xff,0x3f,0x3f,0x3f,0xff,0xff,0xff}
local VERS = {0x30,0x40,0x60,0x00,0x31,0x41,0x61,0x01,0x32,0x42,0x62,0x02,0x33,0x43,0x63,0x03,0x34,0x44,0x64,0x04,0x35,0x45,0x65,0x05,0x36,0x46,0x66,0x06,0x37,0x47,0x67,0x07,0x38,0x48,0x68,0x08,0x39,0x49,0x69,0x09,0x3a,0x4a,0x6a,0x0a,0x3b,0x4b,0x6b,0x0b,0x3c,0x4c,0x6c,0x0c,0x4d,0x6d,0x0d,0xff,0x4e,0x6e,0x0e,0xff,0x4f,0x6f,0x0f,0xff,0x50,0x70,0x10,0xff,0x51,0x71,0x11,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x15,0xff,0xff,0xff,0x7e,0x16,0xff,0xff,0x57,0x77,0x17,0xff,0x18,0xff,0xff,0xff,0x19,0xff,0xff,0xff,0x1a,0xff,0xff,0xff,0x1b,0xff,0xff,0xff,0x1c,0xff,0xff,0xff,0x1d,0xff,0xff,0xff,0x1e,0xff,0xff,0xff,0x1f,0xff,0xff,0xff,0x20,0xff,0xff,0xff,0x21,0xff,0xff,0xff,0x22,0xff,0xff,0xff,0x23,0xff,0xff,0xff,0x32,0x42,0x62,0x02,0x15,0xff,0xff,0xff}
local HJ = {J1, J2}
local function r8(a) return mem:read_u8(a) end   -- Hyper : adresses 68K brutes (octet arcade X = 68K X^1)
local HSEL = {}
do
  local paire = os.getenv("LISTE") or "00.Z3/01.Z3"
  for spec in string.gmatch(paire, "[^/]+") do
    local f = {}
    for x in string.gmatch(spec, "[^.]+") do f[#f + 1] = x end
    local s = {base = tonumber(f[1], 16), fam = f[2] or "Z3", ex = false, mode = 0, ism = 0}
    for i = 3, #f do
      if f[i] == "S" then s.ex = true
      elseif string.match(f[i], "^m%d$") then s.mode = tonumber(string.sub(f[i], 2))
      elseif f[i] == "iX" then s.ism = -1 elseif f[i] == "iA" then s.ism = 0 elseif f[i] == "iV" then s.ism = 1 end
    end
    HSEL[#HSEL + 1] = s
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
      local kk = y * 8 + x
      while vu[kk] ~= "ici" and vu[kk][2] ~= y0 * 8 + x0 do kk = vu[kk][2] end
      return vu[kk] == "ici" and nil or vu[kk][1]
    end
    for _, d in ipairs(DIRS) do
      local nx, ny = pas(x, y, d[2], d[3], j)
      if nx and not vu[ny * 8 + nx] then vu[ny * 8 + nx] = {d[1], y * 8 + x}; file[#file + 1] = {nx, ny} end
    end
  end
  return nil
end
local hstable = 0
local function appui(j, quoi) if k % 8 < 3 then on((j == 1 and "P1 " or "P2 ") .. quoi) end end
local function hstart(j) on(j == 1 and "1 Player Start" or "2 Players Start") end
local function hselectionne(j, s)
  local P = HJ[j]; local et = r8(P + 5); local m = j == 1 and "P1 " or "P2 "
  if et == 0 then
    local x, y = u16(P + 0x12) & 7, u16(P + 0x16) & 7
    local d = chemin(x, y, s.base, j - 1)
    if d then appui(j, d) else
      if s.ex then hstart(j) end
      if k % 16 >= 8 and k % 16 < 11 then on(m .. "Button 1") end
    end
  elseif et == 2 then
    local c = colonne(s) or 0
    if r8(P + 0x5C) ~= c then appui(j, "Down") else
      if s.ex then hstart(j) end
      if k % 16 >= 8 and k % 16 < 11 then on(m .. "Button 1") end
    end
  elseif et == 6 then
    local base = ({[0] = 0, 1, 2, 3, 3, 1, 0, 2})[s.mode]
    local md = r8(P + 0x5C)
    if md == s.mode then appui(j, "Button 1")
    elseif md <= 3 and md ~= base then appui(j, "Down")
    else hstart(j); if k % 16 >= 8 and k % 16 < 11 then on(m .. "Right") end end
  elseif et == 8 then
    local i = r8(P + 0x133); if i >= 0x80 then i = i - 0x100 end
    if i ~= s.ism then appui(j, "Down") else appui(j, "Button 1") end
  elseif et == 4 or et == 0xA then appui(j, "Button 1")
  end
end
local function sel_hyper()
  local p0, p4, p8 = u16(0xFF8000), u16(0xFF8004), u16(0xFF8008)
  if p0 == 6 or p0 == 4 or (p0 == 2 and p4 == 0) then
    if k > 200 and k % 60 < 6 and k < 900 then on("Coin 1"); on("Coin 2") end
    if p0 == 6 and k > 300 and k % 40 < 6 then on("1 Player Start") end
    if p0 == 4 then
      local cur = r8(0xFF4201)
      if cur ~= 1 then if k % 20 < 4 then on("P1 Down") end
      elseif k % 20 >= 10 and k % 20 < 14 then on("P1 Button 1") end
    end
  end
  if p0 == 2 and p4 == 2 and p8 == 4 then
    if (r8(0xFF80A9) & 2) == 0 and k % 30 < 4 then on("2 Players Start") end
    for j = 1, 2 do
      local P = HJ[j]
      if r8(P + 1) ~= 0 and r8(P + 5) < 0xC then hselectionne(j, HSEL[j] or HSEL[1]) end
    end
  end
  if p0 == 2 and p4 == 2 and p8 ~= 4 and k % 24 >= 12 and k % 24 < 15 then on("P1 Button 1"); on("P2 Button 1") end
  return p0 == 2 and p4 == 4 and p8 == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2 and u8(J1 + 7) == 2 and u8(J2 + 7) == 2
end
-- ---------------------------------------------------------------- essais
local function exception()
  if REF then return nil end
  local pc = cpu.state["PC"].value & 0xffffff
  local em = mem:read_u32(0x6638F0); if em >= 0xA00 and em < 0xA80 then pc = em end
  if pc >= 0x400000 or (pc >= 0xA00 and pc < 0xA80) then return pc end
  return nil
end
local function etat(b) return string.format("%02x%02x%02x%02x", u8(b + 4), u8(b + 5), u8(b + 6), u8(b + 7)) end
local function anim(b)
  local p = u32(b + 0x1C) & 0xffffff
  local fp = {}
  -- pas d'animation de 20 o : octets 0-3 et 8-19 (normalises) ; 4-7 = pointeur de frame (reloge dans la traduction)
  for a = p, p + 19 do if a < p + 4 or a >= p + 8 then fp[#fp + 1] = string.format("%02x", u8(a)) end end
  return string.format("%06x %s", p, table.concat(fp))
end
local cur, pos, ess
local function avant()   -- direction « avant » de J1 (vers J2), « arriere » ; meme chose pour J2
  local d = u16(J1 + XO) < u16(J2 + XO)
  return d and "Right" or "Left", d and "Left" or "Right"
end
local function joue(seq, st, p, rr)
  -- st = {i, debut} : segment courant de la sequence ; renvoie true si la sequence est finie
  local av, ar = avant()
  if p == 2 then av, ar = ar, av end
  local pre = p == 1 and "P1 " or "P2 "
  while st.i <= #seq do
    local s = seq[st.i]
    if s.att then
      local fini = false
      local P = (p == 1) and J1 or J2
      if s.att == "G" then   -- garde : arriere tenu pendant l'attente ; fini a l'entree en blocage ($5 = GARDE, 2)
        fini = u8(P + 5) == (tonumber(os.getenv("GARDE") or "", 16) or 0x02)
        on(pre .. ar)
      elseif s.att == "Y" then fini = u16(P + YO) ~= u16(P + 0x64) end
      if fini or rr - st.d >= s.n then st.i = st.i + 1; st.d = rr else
        for _, x in ipairs(s.held or {}) do on(x) end
        return false
      end
    elseif rr - st.d >= s.n then st.i = st.i + 1; st.d = rr
    else
      local held = {}
      for _, t in ipairs(s.t) do
        local q
        if t == "U" then q = pre .. "Up" elseif t == "D" then q = pre .. "Down" elseif t == "F" then q = pre .. av
        elseif t == "B" then q = pre .. ar elseif t == "S" then q = (p == 1) and "1 Player Start" or "2 Players Start"
        elseif string.match(t, "^%d$") then q = pre .. "Button " .. t end
        if q then on(q); held[#held + 1] = q end
      end
      return false
    end
  end
  return true
end
local function prepare(t)
  local cam = u16(REF and 0xFF8290 or 0xFF8292)
  local a, b = cam + 0x60, cam + 0x60 + t.dist
  if COTE == "d" then a, b = cam + 0x60 + t.dist, cam + 0x60 end
  mem:write_u16(J1 + XO, a); mem:write_u16(J2 + XO, b)
  for _, P in ipairs({J1, J2}) do mem:write_u16(P + 0x50, 0x90); mem:write_u16(P + 0x52, 0x90) end
  if t.jauge then mem:write_u16(J1 + 0x11E, t.jauge) end
end
-- VITESSE : SPEED SELECT force (octet arcade $FF80A3, traduction $FF80A2 ; 0 NORMAL, 1 TURBO1, 2 TURBO2) ; defaut 0 :
-- un tour de jeu par image, chaque etat est vu dans les deux machines (en turbo, l'image de 2 tours n'en montre qu'un)
local VITESSE = tonumber(os.getenv("VITESSE") or "0")
emu.register_frame_done(function()
  k = k + 1
  v = {}
  -- (Hyper reecrit la vitesse au debut du combat : on la force a chaque image, menu et essais)
  if VITESSE >= 0 and k > 1000 then w8(0xFF80A3, VITESSE) end
  if phase == "menu" then
    local ok = HYPER and sel_hyper() or (not HYPER and sel_sfa3())
    if ok then stable = stable + 1 else stable = 0 end
    -- Hyper : 150 images d'etats de combat ne suffisent pas, la main n'est donnee qu'apres « FIGHT » (~ +20 images)
    if stable == (HYPER and 400 or 150) then
      out:write(string.format("SAVE %d J1 %02x/%02x ism=%02x J2 %02x ism=%02x\n", k, u8(J1 + 0x102), u8(J1 + 0x116), u8(J1 + 0x132),
        u8(J2 + 0x102), u8(J2 + 0x132)))
      manager.machine:save("banc0"); phase = "attente"; r = 0
    end
    if k > 40000 then out:write("PAS DE COMBAT\n"); out:close(); manager.machine:exit(); return end
  elseif phase == "attente" then
    r = r + 1
    if r == 2 then
      ie = ie + 1
      if ie > #TESTS then out:write("FIN\n"); out:close(); manager.machine:exit(); return end
      ess = TESTS[ie]
      out:write(string.format("T %s %s\n", ess.id, ess.nom))
      manager.machine:load("banc0"); phase = "essai"; r = 0
      pos = {{i = 1, d = 8}, {i = 1, d = 8}}
    end
  elseif phase == "essai" then
    r = r + 1
    _G.BANC_R, _G.BANC_ID = r, ess.id
    if r <= 6 then prepare(ess) end
    local f1, f2 = true, true
    -- temps de la sequence = TOURS DE JEU depuis l'image 8 (et non images) : la traduction peut sauter un tour
    -- (cadence turbo) ; en tours, les appuis restent alignes sur le temps du jeu dans les deux machines
    if r == 7 then ess.t0 = TOURS end
    if r >= 8 then local tt = 8 + TOURS - ess.t0; f1 = joue(ess.s1, pos[1], 1, tt); f2 = joue(ess.s2, pos[2], 2, tt) end
    if r < 8 then f1, f2 = false, false end
    if f1 and f2 and not ess.fin then ess.fin = r end
    out:write(string.format("F %s %d %s %s %04x %04x %04x %04x %02x %s %04x %02x %d %04x %02x %02x\n", ess.id, r, etat(J1), etat(J2), u16(J1 + XO),
      u16(J1 + YO), u16(J2 + XO), u16(J2 + 0x50), u8(J1 + 0xAA), anim(J1), u16(J1 + 0x11E), u8(J1 + 0xB), TOURS, u16(J1 + 0x50), u8(J1 + 0x32), u8(J2 + 0x32)))
    for _, base in ipairs({0xFF9400, 0xFFA000}) do
      for i = 0, 11 do
        local o = base + i * 0x100
        if u8(o) ~= 0 then out:write(string.format("O %s %d %06x %02x%02x %s %04x\n", ess.id, r, o, u8(o + 2), u8(o + 3), etat(o), u16(o + XO))) end
      end
    end
    -- captures : SNAPID = essai, SNAPR = « debut-fin » (images de l'essai), SNAPP = pas (defaut 1) ; SPRITES=1 conseille
    if os.getenv("SNAPID") == ess.id then
      local a, b = string.match(os.getenv("SNAPR") or "8-120", "(%d+)-(%d+)")
      if r >= tonumber(a) and r <= tonumber(b) and (r - tonumber(a)) % tonumber(os.getenv("SNAPP") or "1") == 0 then
        manager.machine.video:snapshot()
      end
    end
    if os.getenv("RAMDUMP") and r == tonumber(os.getenv("RAMDUMP")) and (os.getenv("RAMID") or ess.id) == ess.id then
      local f = io.open(os.getenv("OUT") .. "." .. ess.id .. ".ram", "wb"); local t = {}
      for a = 0xFF0000, 0xFFFFFE, 2 do t[#t + 1] = string.pack(">I2", u16(a)) end
      f:write(table.concat(t)); f:close()
    end
    if DUMP then
      local t = {}
      for a = J1, J1 + 0x3FE, 2 do t[#t + 1] = string.format("%04x", u16(a)) end
      out:write(string.format("D %s %d %s\n", ess.id, r, table.concat(t)))
    end
    local x = exception()
    if x then out:write(string.format("X %s %d %x\n", ess.id, r, x)); ess.fin = ess.fin or r; r = 100000 end
    if ess.fin and r >= ess.fin + ess.obs then
      out:write(string.format("R %s %d\n", ess.id, ess.fin)); phase = "attente"; r = 0
    end
    if r > 3000 then out:write(string.format("R %s %d trop_long\n", ess.id, r)); phase = "attente"; r = 0 end
  end
  for fn, f in pairs(champs) do
    if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then
      f:set_value(v[fn] or 0)
    end
  end
end)
if HYPER and os.getenv("NOROUL") ~= "0" then
  _G.TAPR = {}
  for _, a in ipairs({0xFF84D2, 0xFF88D2}) do
    _G.TAPR[#_G.TAPR + 1] = mem:install_write_tap(a, a + 1, "noroul" .. a, function(off, data, mask)
      if mask & 0x00ff ~= 0 then return data & 0xff00 end
    end)
  end
end
if not REF then
  dofile((os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame") .. "/banc_mem.lua")
  if os.getenv("HSFA_PLANS") then dofile((os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame") .. "/banc_plans.lua") end
  if os.getenv("SPRITES") == "1" then
    if not os.getenv("HSFA_PLANS") then dofile((os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame") .. "/banc_plans.lua") end
    dofile((os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame") .. "/banc_sprites.lua")
  end
end
if os.getenv("LUA_EN_PLUS") then dofile(os.getenv("LUA_EN_PLUS")) end
