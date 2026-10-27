-- (HANDOFF §93) TEST DU CABLAGE DES COMMANDES : partie a 2 joueurs (J2 passif), puis une sequence d'actions
-- relative au debut du combat (mode $FF800C = 6), d'abord J1 puis J2 ; journal par image de l'etat des deux
-- joueurs, NORMALISE dans la numerotation de la ROM (REF=1 : ROM arcade ; sinon traduction : octets d'etat
-- $4-$7 echanges par mot, X/Y en $12/$16 au lieu de $10/$14). Sortie : OUT (« F rel j b4 b5 b6 b7 x y »).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local REF = os.getenv("REF") == "1"
local out = io.open(os.getenv("OUT"), "w")
local k, t0 = 0, nil
TOURS = 0
TT = mem:install_write_tap(0xFF851C, 0xFF851D, "tours", function(o, d, m) TOURS = TOURS + 1 end)
local function J(p, s) return {":IN0", "P" .. p .. " " .. s} end
local function B(p, n)
  if n <= 3 then return {":IN0", "P" .. p .. " Button " .. n} end
  if p == 2 and n == 6 then return {":IN2", "P2 Button 6"} end
  return {":IN1", "P" .. p .. " Button " .. n}
end
-- actions : {nom, {{debut, fin, champs...}, ...}} relatives au depart de l'action ; une action toutes les 90 images
local function acts(p, av, ar)
  local a = {}
  for n = 1, 6 do a[#a+1] = {"B" .. n, {{0, 3, B(p, n)}}} end
  for n = 1, 6 do a[#a+1] = {"bas+B" .. n, {{0, 12, J(p, "Down")}, {4, 7, B(p, n)}}} end
  a[#a+1] = {"saut", {{0, 4, J(p, "Up")}}}
  a[#a+1] = {"saut avant", {{0, 4, J(p, "Up"), J(p, av)}}}
  a[#a+1] = {"saut arriere", {{0, 4, J(p, "Up"), J(p, ar)}}}
  a[#a+1] = {"saut+B6", {{0, 4, J(p, "Up")}, {14, 17, B(p, 6)}}}
  a[#a+1] = {"marche avant", {{0, 30, J(p, av)}}}
  a[#a+1] = {"marche arriere", {{0, 30, J(p, ar)}}}
  a[#a+1] = {"quart avant+P", {{0, 3, J(p, "Down")}, {3, 6, J(p, "Down"), J(p, av)}, {6, 9, J(p, av), B(p, 1)}}}
  a[#a+1] = {"dragon+P", {{0, 3, J(p, av)}, {3, 6, J(p, "Down")}, {6, 9, J(p, "Down"), J(p, av), B(p, 3)}}}
  a[#a+1] = {"quart arriere+K", {{0, 3, J(p, "Down")}, {3, 6, J(p, "Down"), J(p, ar)}, {6, 9, J(p, ar), B(p, 4)}}}
  return a
end
local seq = {}
local function ajoute(p, av, ar, base)
  for i, a in ipairs(acts(p, av, ar)) do
    local d = base + (i - 1) * 90
    out:write(string.format("A %d J%d %s\n", d, p, a[1]))
    for _, e in ipairs(a[2]) do
      for x = 3, #e do seq[#seq+1] = {d + e[1], d + e[2], e[x]} end
    end
  end
  return base + #acts(p, av, ar) * 90
end
local fin1 = ajoute(1, "Right", "Left", 120)
local fin2 = ajoute(2, "Left", "Right", fin1 + 60)
local FIN = fin2 + 60
local function etat(b)
  local r = {}
  for i = 4, 7 do r[#r+1] = mem:read_u8(b + (REF and i or (i ~ 1))) end
  local x = mem:read_u16(b + (REF and 0x10 or 0x12)); local y = mem:read_u16(b + (REF and 0x14 or 0x16))
  return string.format("%02x %02x %02x %02x %04x %04x %04x %04x %04x", r[1], r[2], r[3], r[4], x, y,
    mem:read_u16(b + 0x11a), mem:read_u16(b + 0x118), mem:read_u16(0xFF8058 + ((b == 0xFF8400) and 0 or 4)))
end
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(f) v[f[1] .. "|" .. f[2]] = 1 end
  if t0 == nil and os.getenv("SNAPABS") and string.find("," .. os.getenv("SNAPABS") .. ",", "," .. k .. ",", 1, true) then manager.machine.video:snapshot() end
  if t0 == nil then
    if k >= 1500 and k < 1860 and k % 60 < 8 then on({":IN2", "Coin 1"}) end      -- 6 pieces (ROM : 2 pieces/credit)
    local jeu = mem:read_u8(REF and 0xFF80A8 or 0xFF80A9)   -- joueurs en jeu (bit 0 J1, bit 1 J2)
    if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on({":IN2", "1 Player Start"}) end
    if k >= 2000 and k % 40 >= 20 and k % 40 < 26 and jeu & 1 == 1 and jeu & 2 == 0 then on({":IN2", "2 Players Start"}) end
    local e1, e2 = etat(0xFF8400), etat(0xFF8800)
    local combat = mem:read_u16(0xFF800C) == 6 and string.sub(e1, 1, 2) == "02" and string.sub(e2, 1, 2) == "02"
    -- (palettes MAX) SEL_J1 / SEL_J2 = bouton de selection (perso + ism ; defaut 1) : choisit la couleur ($129)
    if k >= 2100 and k % 24 < 4 and jeu == 3 and not combat then on(B(1, tonumber(os.getenv("SEL_J1") or "1"))); on(B(2, tonumber(os.getenv("SEL_J2") or "1"))) end
    if k > 2100 and mem:read_u16(0xFF800C) == 6 and string.sub(e1, 1, 2) == "02" and string.sub(e2, 1, 2) == "02"
       and string.sub(e1, 10, 11) == "02" and string.sub(e2, 10, 11) == "02" then
      stable = (stable or 0) + 1
      if stable == 30 then t0 = k; out:write(string.format("T0 %d\n", k)) end
    else stable = 0 end
  else
    local r = k - t0
    if os.getenv("SNAPREL") and string.find("," .. os.getenv("SNAPREL") .. ",", "," .. r .. ",", 1, true) then manager.machine.video:snapshot() end
    for _, s in ipairs(seq) do if r >= s[1] and r <= s[2] then on(s[3]) end end
    if os.getenv("DUMPREL") and r >= tonumber(os.getenv("DUMPREL")) and r < tonumber(os.getenv("DUMPREL")) + 8 then
      local t = {}
      local db = tonumber(os.getenv("DUMPBASE") or "FF8400", 16); for a = db, db + 0x3FE, 2 do t[#t+1] = string.format("%04x", mem:read_u16(a)) end
      out:write(string.format("D %d %s\n", r, table.concat(t, " ")))
    end
    out:write(string.format("F %d 1 %s\n", r, etat(0xFF8400)))
    out:write(string.format("F %d 2 %s\n", r, etat(0xFF8800)))
    out:write(string.format("C %d %d\n", r, TOURS))   -- tours de jeu (copie $51A -> $51C, une par tour)
    if r >= FIN then out:close(); manager.machine:exit() end
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k > 30000 then out:write("PAS DE COMBAT\n"); out:close(); manager.machine:exit() end
end)
if not REF then
  dofile("<workspace>/work/agent_effets_upper/lua/banc_mem.lua"); dofile("<workspace>/work/agent_effets_upper/lua/banc_plans.lua")
  if os.getenv("SPRITES") == "1" then dofile("<workspace>/work/agent_effets_upper/lua/banc_sprites.lua") end
  if os.getenv("PAL_J1") then dofile("<workspace>/work/agent_effets_upper/lua/banc_palettes.lua") end
end
