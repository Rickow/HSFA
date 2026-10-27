-- (agent_integration_max) tournee_max.lua (sans ALEA) + manipulation de J1 répétée toutes les PER images de combat :
-- COUP="D:0-3,D+L:3-6,L:6-9,B5:7-10" (directions U/D/L/R et boutons B1-B6, plages d'images dans la période)
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local ports = manager.machine.ioport.ports
local function champ(nm) for _, p in pairs(ports) do for fn, fl in pairs(p.fields) do if fn == nm then return fl end end end end
local N = {U = "P1 Up", D = "P1 Down", L = "P1 Left", R = "P1 Right"}
for k = 1, 6 do N["B" .. k] = "P1 Button " .. k end
-- AR / AV : arrière / avant selon l'orientation de J1 (octet $FF840A, ORIENT=0 si 0 = tourné vers la droite)
N["AR"] = "AR"; N["AV"] = "AV"
local OR0 = tonumber(os.getenv("ORIENT") or "0")
local PER = tonumber(os.getenv("PER") or "80")
local S = {}
for part in string.gmatch(os.getenv("COUP") or "", "[^,]+") do
  local keys, a, b = part:match("([^:]+):(%d+)-(%d+)")
  for k in string.gmatch(keys, "[^+]+") do S[#S + 1] = {N[k] ~= "AR" and N[k] ~= "AV" and champ(N[k]) or false, tonumber(a), tonumber(b), N[k]} end
end
local c = 0
local TR = os.getenv("TRACE") and io.open(os.getenv("TRACE"), "w")
emu.register_frame_done(function()
  if TR and c > 120 then TR:write(string.format("%d %04x%04x %02x\n", c, mem:read_u16(0xFF841E), mem:read_u16(0xFF841C), mem:read_u8(0xFF8405))) end
  if mem:read_u16(0xFF800C) == 6 then c = c + 1 else c = 0 end
  if c > 120 then
    local t = c % PER
    local on = {}
    -- clé = nom du champ (les objets champ() renvoyés par sol2 sont distincts à chaque appel)
    local droite = (mem:read_u8(0xFF840A) == OR0)
    local AR, AV = droite and N.L or N.R, droite and N.R or N.L
    for _, s in ipairs(S) do if t >= s[2] and t < s[3] then
      local nm = s[4] == "AR" and AR or (s[4] == "AV" and AV or s[4]); on[nm] = true end end
    for _, nm in ipairs({N.L, N.R}) do if not CH then CH = {} end; CH[nm] = CH[nm] or champ(nm) end
    for _, s in ipairs(S) do if s[1] then s[1]:set_value(on[s[4]] and 1 or 0) end end
    for _, nm in ipairs({N.L, N.R}) do local used = false
      for _, s in ipairs(S) do if s[4] == nm then used = true end end
      if not used then CH[nm]:set_value(on[nm] and 1 or 0) end end
  end
end)

-- (agent_integration_max) J2 : COUP2 (même syntaxe, directions AR/AV selon $FF880A, ORIENT2), période PER2
if os.getenv("COUP2") then
  local N2 = {U = "P2 Up", D = "P2 Down", L = "P2 Left", R = "P2 Right", AR = "AR", AV = "AV"}
  for k = 1, 6 do N2["B" .. k] = "P2 Button " .. k end
  local PER2 = tonumber(os.getenv("PER2") or os.getenv("PER") or "80")
  local OR2 = tonumber(os.getenv("ORIENT2") or "1")
  local S2 = {}
  for part in string.gmatch(os.getenv("COUP2"), "[^,]+") do
    local keys, a, b = part:match("([^:]+):(%d+)-(%d+)")
    for k in string.gmatch(keys, "[^+]+") do S2[#S2 + 1] = {N2[k], tonumber(a), tonumber(b)} end
  end
  local CH2 = {}
  for _, nm in ipairs({"P2 Up", "P2 Down", "P2 Left", "P2 Right", "P2 Button 1", "P2 Button 2", "P2 Button 3", "P2 Button 4", "P2 Button 5", "P2 Button 6"}) do CH2[nm] = champ(nm) end
  local c2 = 0
  emu.register_frame_done(function()
    if mem:read_u16(0xFF800C) == 6 then c2 = c2 + 1 else c2 = 0 end
    if c2 > 120 then
      local t = c2 % PER2
      local droite = (mem:read_u8(0xFF880A) == OR2)
      local on = {}
      for _, s in ipairs(S2) do if t >= s[2] and t < s[3] then
        local nm = s[1] == "AR" and (droite and "P2 Left" or "P2 Right") or (s[1] == "AV" and (droite and "P2 Right" or "P2 Left") or s[1])
        on[nm] = true end end
      for nm, f in pairs(CH2) do if f then f:set_value(on[nm] and 1 or 0) end end
    end
  end)
end
