-- EFFETS D'UPPER SANS FRAME LISIBLE (agent_effets_upper) : charge tournee.lua (copie locale, partie Arcade scriptee),
-- puis releve dans la liste d'objets BRUTE du jeu ($700000-$70FFFF) les objets de l'emplacement 0 (banque commune e351,
-- bits 13-15 de Y = 0) dont le code LOCAL tombe dans les plages PLAGES (hex, "a-b,c-d"). Pour chacun : contexte du CPU
-- au moment ou le jeu ecrit le mot de code (PC, A0-A6, D0-D7) et champs de l'acteur A6 (classe, sous-type, $1C...).
-- Sorties : EFF_OUT (une ligne par objet retenu, au plus EFF_MAX lignes), EFF_RESUME (agregats a la fin),
-- EFF_ACTEURS (vidage $100 octets des acteurs vus, un par (classe, sous-type, routine)). Lecture seule de la RAM.
dofile("<workspace>/work/agent_effets_upper/lua/tournee.lua")
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local plages = {}
for a, b in string.gmatch(os.getenv("PLAGES") or "3C24-4062,5224-5662", "(%x+)-(%x+)") do plages[#plages + 1] = {tonumber(a, 16), tonumber(b, 16)} end
local function dans(c) for _, p in ipairs(plages) do if c >= p[1] and c <= p[2] then return true end end return false end
local out = io.open(os.getenv("EFF_OUT"), "w")
local MAX = tonumber(os.getenv("EFF_MAX") or "60000")
local nl = 0
local function u8(a) return mem:read_u8(a ~ 1) end
local function l32(a) return (mem:read_u16(a + 2) << 16) | mem:read_u16(a) end   -- long a moities echangees (§29)
local R = {"PC", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "SP", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"}
local ctx, age, img = {}, {}, 0
local pcs = {}          -- PC -> nombre d'ecritures de code (tous emplacements)
local function regs()
  local t = {}
  for i, r in ipairs(R) do t[i] = cpu.state[r].value end
  return t
end
EFF_TAP = mem:install_write_tap(0x700000, 0x70ffff, "effets", function(offset, data, mask)
  if BANC_BUSY then return end
  if offset & 7 == 4 then
    age[offset] = img
    -- la prise de banc_sprites.lua peut passer avant (elle rend le mot CONVERTI) : on prend la valeur brute de l'ombre
    local c = data & 0xffff
    if BANC_OMBRE and BANC_OMBRE[offset] and not dans(c) then c = BANC_OMBRE[offset] end
    if dans(c) then
      DBG[5] = DBG[5] + 1
      local ok, e = pcall(function()
        local r = regs(); local a6 = r[8] & 0xffffff
        ctx[offset] = {c, r, u8(a6 + 2), u8(a6 + 3), u8(a6), l32(a6 + 0x1C), mem:read_u16(a6 + 0x32), mem:read_u16(a6 + 0x34), img}
      end)
      if not ok and not ERRMSG then ERRMSG = tostring(e) end
    end
  end
end)
local resume, acteurs = {}, {}
DBG = {0, 0, 0, 0, 0}
local fa = io.open(os.getenv("EFF_ACTEURS"), "w")
local histo = {}        -- (emplacement, code >> 6) -> nombre d'objets (images de combat)
local function ecrit_resume()
  local f = io.open(os.getenv("EFF_RESUME"), "w")
  local t = {}
  for k, v in pairs(resume) do t[#t + 1] = {k, v} end
  table.sort(t, function(a, b) return a[2] > b[2] end)
  for _, e in ipairs(t) do f:write(string.format("%8d %s\n", e[2], e[1])) end
  f:write("ERR " .. tostring(ERRMSG) .. "\n"); f:write(string.format("DBG %d %d %d %d %d\n", DBG[1], DBG[2], DBG[3], DBG[4], DBG[5]))
  f:close()
  if os.getenv("EFF_HISTO") then
    local h = io.open(os.getenv("EFF_HISTO"), "w")
    local u = {}
    for k, v in pairs(histo) do u[#u + 1] = {k, v} end
    table.sort(u, function(a, b) return a[1] < b[1] end)
    for _, e in ipairs(u) do h:write(string.format("e%d %04X-%04X %d\n", e[1] >> 16, (e[1] & 0xffff) << 6, ((e[1] & 0xffff) << 6) + 63, e[2])) end
    h:close()
  end
  out:flush()
end
emu.register_frame_done(function()
  img = img + 1
  if img % 600 == 0 then ecrit_resume() end
  if not BANC_OMBRE then return end
  local combat = mem:read_u16(0xFF800C) == 6
  if combat and os.getenv("EFF_HISTO") then
    for page = 0x700000, 0x708000, 0x8000 do
      for a = page, page + 0x2000 - 8, 8 do
        local x, y = BANC_OMBRE[a] or 0, BANC_OMBRE[a + 2] or 0
        if x == 0x8000 and y == 0x8000 then break end
        if (age[a + 4] or -9) >= img - 1 then
          local k = (((y >> 13) & 7) << 16) | ((BANC_OMBRE[a + 4] or 0) >> 6)
          histo[k] = (histo[k] or 0) + 1
        end
      end
    end
  end
  for page = 0x700000, 0x708000, 0x8000 do
    for a = page, page + 0x2000 - 8, 8 do
      local x, y = BANC_OMBRE[a] or 0, BANC_OMBRE[a + 2] or 0
      if x == 0x8000 and y == 0x8000 then break end
      local c = BANC_OMBRE[a + 4] or 0
      local k = ctx[a + 4]
      if (y >> 13) & 7 == 0 and dans(c) then DBG[1] = DBG[1] + 1; if k then DBG[2] = DBG[2] + 1; if k[1] == c then DBG[3] = DBG[3] + 1 end end; if (age[a + 4] or -9) >= img - 1 then DBG[4] = DBG[4] + 1 end end
      if (y >> 13) & 7 == 0 and dans(c) and (age[a + 4] or -9) >= img - 1 and k and k[1] == c and k[9] >= img - 1 then
        local r = k[2]
        local a6 = r[8] & 0xffffff
        local cle = string.format("pc=%06X a6cl=%02X st=%02X a0=%06X", r[1], k[3], k[4], r[2] & 0xffffff)
        resume[cle] = (resume[cle] or 0) + 1
        local ka = string.format("%02X/%02X pc=%06X", k[3], k[4], r[1])
        if not acteurs[ka] and fa then
          acteurs[ka] = true
          local t = {}
          for o = 0, 0xFE, 2 do t[#t + 1] = string.format("%04X", mem:read_u16(a6 + o)) end
          fa:write(string.format("image %d acteur %06X %s 1C=%08X 32=%04X%04X regs=", img, a6, ka, k[6], k[7], k[8]))
          for i, v in ipairs(r) do fa:write(string.format("%s=%X ", R[i], v)) end
          fa:write("\n  " .. table.concat(t, " ") .. "\n"); fa:flush()
        end
        if nl < MAX then
          nl = nl + 1
          out:write(string.format("%6d %s obj=%06X x=%04X y=%04X c=%04X at=%04X pc=%06X A6=%06X cl=%02X st=%02X e0=%02X 1C=%08X 32=%04X%04X A0=%06X A1=%06X A2=%06X A3=%06X A4=%06X D0=%X D1=%X D2=%X D3=%X D7=%X\n",
            img, combat and "C" or "-", a, x, y, c, BANC_OMBRE[a + 6] or 0, r[1], a6, k[3], k[4], k[5], k[6], k[7], k[8],
            r[2] & 0xffffff, r[3] & 0xffffff, r[4] & 0xffffff, r[5] & 0xffffff, r[6] & 0xffffff, r[10], r[11], r[12], r[13], r[17]))
        end
      end
    end
  end
end)
