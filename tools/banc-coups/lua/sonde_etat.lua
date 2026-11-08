-- (banc_coups) SONDE : combat VERSUS (comme agent_coups/coups.lua), sauvegarde d'etat PRISE PAR LUA au combat stable,
-- puis pour chaque essai : rechargement, manip, vidage brut de J1/J2 ($400 o) a chaque image. REF=1 : arcade.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local REF = os.getenv("REF") == "1"
local out = io.open(os.getenv("OUT"), "w")
local J1, J2 = 0xFF8400, 0xFF8800
local function u8(a) return mem:read_u8(REF and a or (a ~ 1)) end
local function w8(a, v) mem:write_u8(REF and a or (a ~ 1), v) end
local champs = {}
for _, p in pairs(ports) do for fn, f in pairs(p.fields) do champs[fn] = f end end
local ESS = {
  {"qcfLP", {{3, "D"}, {3, "DF"}, {3, "F", 1}}},
  {"dpLP", {{3, "F"}, {3, "D"}, {3, "DF", 1}}},
  {"qcbLK", {{3, "D"}, {3, "DB"}, {3, "B", 4}}},
  {"qcfLP", {{3, "D"}, {3, "DF"}, {3, "F", 1}}},
}
local k, t0, sel, stable, phase, ie, r = 0, nil, 0, 0, "menu", 0, 0
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local jeu = u8(0xFF80A8)
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if phase == "menu" then
    if k >= 1500 and k < 1860 and k % 60 < 8 then v["Coin 1"] = 1 end
    if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then v["1 Player Start"] = 1 end
    if k >= 2000 and k % 40 >= 20 and k % 40 < 26 and jeu & 1 == 1 and jeu & 2 == 0 then v["2 Players Start"] = 1 end
    local combat = mem:read_u16(0xFF800C) == 6 and u8(J1 + 4) == 2 and u8(J2 + 4) == 2
    if k >= 2100 and k % 24 < 4 and jeu == 3 and not combat then v["P1 Button 1"] = 1; v["P2 Button 1"] = 1 end
    if k > 2100 and combat and u8(J1 + 7) == 2 and u8(J2 + 7) == 2 then
      stable = stable + 1
      if stable == 150 then
        out:write(string.format("SAVE %d\n", k)); manager.machine:save("banc0"); phase = "attente"; r = 0
      end
    else stable = 0 end
  elseif phase == "attente" then
    r = r + 1
    if r == 3 then
      ie = ie + 1
      if ie > #ESS then out:close(); manager.machine:exit(); return end
      out:write(string.format("ESSAI %d %s k=%d\n", ie, ESS[ie][1], k))
      mem:write_u16(J2 + 0x50, 0x33)   -- marqueur : doit disparaitre au rechargement
      manager.machine:load("banc0"); phase = "essai"; r = 0
    end
  elseif phase == "essai" then
    r = r + 1
    local d = 10
    for _, s in ipairs(ESS[ie][2]) do
      if r >= d and r < d + s[1] then
        if string.find(s[2], "D") then v["P1 Down"] = 1 end
        if string.find(s[2], "F") then v["P1 Right"] = 1 end
        if string.find(s[2], "B") then v["P1 Left"] = 1 end
        if s[3] and r >= d + s[1] - 2 then v["P1 Button " .. s[3]] = 1 end
      end
      d = d + s[1]
    end
    local t = {}
    for a = J1, J1 + 0x3FE, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
    out:write(string.format("D %d %d %s\n", ie, r, table.concat(t, "")))
    t = {}
    for a = J2, J2 + 0x3FE, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
    out:write(string.format("E %d %d %s\n", ie, r, table.concat(t, "")))
    if r >= 120 then phase = "attente"; r = 0 end
  end
  for fn, f in pairs(champs) do
    if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" or fn == "2 Players Start" then f:set_value(v[fn] or 0) end
  end
  if k > 40000 then out:write("TROP LONG\n"); out:close(); manager.machine:exit() end
end)
if not REF then dofile((os.getenv("HSFA_BANC_LUA") or "<workspace>/work/mame") .. "/banc_mem.lua") end
