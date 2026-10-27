-- (copie agent_hyper_etats de agent_ro9/banques_modes/lua/hyper.lua, + WATCHW) (agent_ro9, BANQUES-ET-MODES-ro9.md) scenario Hyper (ro9) sur le fork sfa3hx : entrees INPUTS (format de diag.py),
-- journal des phases et des ids J1/J2, captures SNAPS (images) et SNAPC (images apres le debut du combat),
-- FORCE102 (hexa) : impose l'identifiant etendu $102 de J1 (et FORCE102J2 pour J2) pendant l'ecran de selection.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local out = io.open(os.getenv("OUT"), "w")
local NF = tonumber(os.getenv("NF") or "4000")
local seq = {}
for item in string.gmatch(os.getenv("INPUTS") or "", "[^;]+") do
  local a, b, p, f = string.match(item, "^(%d+)-(%d+):(:[%w]+):(.+)$")
  if a then table.insert(seq, {tonumber(a), tonumber(b), p .. "|" .. f}) end
  local a2, b2, per, dur, p2, f2 = string.match(item, "^(%d+)-(%d+)%%(%d+),(%d+):(:[%w]+):(.+)$")
  if a2 then table.insert(seq, {tonumber(a2), tonumber(b2), p2 .. "|" .. f2, tonumber(per), tonumber(dur)}) end
end
local SN, SC = {}, {}
for x in string.gmatch(os.getenv("SNAPS") or "", "%d+") do SN[tonumber(x)] = true end
for x in string.gmatch(os.getenv("SNAPC") or "", "%d+") do SC[tonumber(x)] = true end
local F1 = tonumber(os.getenv("FORCE102") or "", 16)
local F2 = tonumber(os.getenv("FORCE102J2") or "", 16)
local F117 = tonumber(os.getenv("FORCE117") or "", 16)    -- (diagnostic) drapeaux de version $117 de J1 imposes
local FW0 = tonumber(os.getenv("FORCE_DE") or "0")       -- fenetre d'ecriture de $102 (images)
local FW1 = tonumber(os.getenv("FORCE_A") or "0")
local FMODE = tonumber(os.getenv("MODE") or "")           -- curseur du menu des modes (MODE_ADR)
local FMADR = tonumber(os.getenv("MODE_ADR") or "FF4201", 16)
local k, last, debut, vs = 0, "", nil, nil
local WATCH = nil                                          -- WATCH="FF4201,..." : octets 68K ajoutes au journal
if os.getenv("WATCH") then WATCH = {} for x in string.gmatch(os.getenv("WATCH"), "%x+") do WATCH[#WATCH + 1] = tonumber(x, 16) end end
local WATCHW = nil                                         -- WATCHW="FF851A,..." : mots 68K ajoutes au journal
if os.getenv("WATCHW") then WATCHW = {} for x in string.gmatch(os.getenv("WATCHW"), "%x+") do WATCHW[#WATCHW + 1] = tonumber(x, 16) end end
local SNAPVS, FINC = tonumber(os.getenv("SNAPVS") or ""), tonumber(os.getenv("FINC") or "")
-- tables du decodage des versions (fonction 0x321BA0) : $116 = 0x5C5300[$102], $117 = 0x5C2490[$102] (fichier ro9)
T116, T117 = {}, {}
do
  local f = io.open("<workspace>/anthology_extract/decompressed/ro9_usa_prog68k.bin", "rb"); local b = f:read("a"); f:close()
  for i = 0, 127 do T116[i] = b:byte(0x5C5300 - 0x1F0000 + i + 1); T117[i] = b:byte(0x5C2490 - 0x1F0000 + i + 1) end
end
local J1, J2 = 0xFF8400, 0xFF8800
local function u8(a) return mem:read_u8(a ~ 1) end       -- numerotation PS2 -> 68K (octet XOR 1)
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  for _, s in ipairs(seq) do
    local on = k >= s[1] and k <= s[2] and (not s[4] or (k - s[1]) % s[4] < s[5])
    v[s[3]] = (v[s[3]] or 0) | (on and 1 or 0)
  end
  if FMODE and mem:read_u16(0xFF8000) == 4 then mem:write_u8(FMADR, FMODE) end
  if k >= FW0 and k <= FW1 then
    if F1 then mem:write_u8((J1 + 0x102) ~ 1, F1); mem:write_u8((J1 + 0x116) ~ 1, T116[F1]); mem:write_u8((J1 + 0x117) ~ 1, F117 or T117[F1]) end
    if F2 then mem:write_u8((J2 + 0x102) ~ 1, F2); mem:write_u8((J2 + 0x116) ~ 1, T116[F2]); mem:write_u8((J2 + 0x117) ~ 1, T117[F2]) end
  end
  local st = string.format("%04x %04x %04x %04x %04x | J1 %02x %02x %02x %02x %02x %02x | J2 %02x %02x %02x %02x %02x %02x",
    mem:read_u16(0xFF8000), mem:read_u16(0xFF8002), mem:read_u16(0xFF8004), mem:read_u16(0xFF8008), mem:read_u16(0xFF800C),
    u8(J1 + 0), u8(J1 + 4), u8(J1 + 0x102), u8(J1 + 0x116), u8(J1 + 0x117), u8(J1 + 0xD3),
    u8(J2 + 0), u8(J2 + 4), u8(J2 + 0x102), u8(J2 + 0x116), u8(J2 + 0x117), u8(J2 + 0xD3))
  if WATCH then for _, a in ipairs(WATCH) do st = st .. string.format(" %06x=%02x", a, mem:read_u8(a)) end end
  if WATCHW then for _, a in ipairs(WATCHW) do st = st .. string.format(" %06x=%04x", a, mem:read_u16(a)) end end
  if st ~= last then out:write(string.format("%6d : %s\n", k, st)); last = st end
  -- combat : J1 et J2 en etat 2 ($4), phases A5+4 = 4 et A5+8 = 6 (Hyper : A5+0 reste a 2)
  if not debut and mem:read_u16(0xFF8004) == 4 and mem:read_u16(0xFF8008) == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2 then debut = k; out:write(string.format("COMBAT %d\n", k))
    _G.RETSTAT = {}; _G.PALSTAT = {}                         -- statistiques du combat seulement
    if STATS then for c, n in pairs(STATS) do STATS[c] = 0 end end
  end
  -- SNAPVS=n : capture n images apres l'entree sur l'ecran VS (A5+4 = A5+8 = 4) ; FINC=n : fin n images apres le combat
  if SNAPVS and not vs and mem:read_u16(0xFF8004) == 4 and mem:read_u16(0xFF8008) == 4 then vs = k end
  if SN[k] or (debut and SC[k - debut]) or (vs and k == vs + SNAPVS) then manager.machine.video:snapshot() end
  if FINC and debut and k >= debut + FINC then NF = k end
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
  if k >= NF then
    if STATS then out:write(string.format("STATS listes %d objets %d tuiles %d retires %d tronques %d\n", STATS.listes, STATS.objets, STATS.tuiles, STATS.retires, STATS.tronques)) end
    if _G.PALSTAT then
      local par = {}
      for c, n in pairs(_G.PALSTAT) do local e = c // 256; par[e] = (par[e] or 0) + n end
      for e = 0, 7 do if par[e] then out:write(string.format("OBJETS emplacement %d : %d\n", e, par[e])) end end
    end
    if _G.RETSTAT then
      local par = {}
      for c, n in pairs(_G.RETSTAT) do local e = string.match(c, "^e(%d)"); par[e] = (par[e] or 0) + n end
      for e, n in pairs(par) do out:write(string.format("RETIRES emplacement %s : %d\n", e, n)) end
      if os.getenv("RETDET") then                                -- detail : codes locaux retires les plus frequents
        local l = {}
        for c, n in pairs(_G.RETSTAT) do l[#l + 1] = {c, n} end
        table.sort(l, function(x, y) return x[2] > y[2] end)
        for i = 1, math.min(#l, tonumber(os.getenv("RETDET"))) do out:write(string.format("RET %6d %s\n", l[i][2], l[i][1])) end
      end
    end
    out:write("FIN\n"); out:close(); manager.machine:exit()
  end
end)
_G.RETSTAT = {}; _G.PALSTAT = {}     -- (environnement du script autoboot distinct de celui des dofile)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end
-- (agent_hyper_etats) WTAP="FF8502,..." : journal des ecritures (mot 68K) avec le PC (fenetre WTAP_DE..WTAP_A images)
if os.getenv("WTAP") then
  local T0, T1 = tonumber(os.getenv("WTAP_DE") or "0"), tonumber(os.getenv("WTAP_A") or "999999")
  _G.TAPS = {}
  for x in string.gmatch(os.getenv("WTAP"), "%x+") do
    local a = tonumber(x, 16)
    _G.TAPS[#_G.TAPS + 1] = mem:install_write_tap(a, a + 1, "wtap" .. x, function(off, data, mask)
      if k >= T0 and k <= T1 then
        out:write(string.format("TAP %d %06x=%04x/%04x PC=%06x\n", k, off, data, mask, cpu.state["PC"].value & 0xffffff))
      end
    end)
  end
end
-- (agent_hyper_etats) NOROUL=1 : neutralise le drapeau « Start » de la selection ($D3 68K du joueur, pose par mips 0x31611C)
-- qui lance la roulette aleatoire. Sur PS2, ce drapeau vient du bit $0100 du moteur (natif 0x23D20), distinct du START
-- arcade ($62) qui donne le bit 15 de $11A ; dans le banc les deux viennent du meme bouton Start.
if os.getenv("NOROUL") == "1" then
  _G.TAPR = {}
  for _, a in ipairs({0xFF84D2, 0xFF88D2}) do
    _G.TAPR[#_G.TAPR + 1] = mem:install_write_tap(a, a + 1, "noroul" .. a, function(off, data, mask)
      if mask & 0x00ff ~= 0 then return data & 0xff00 end
    end)
  end
end
