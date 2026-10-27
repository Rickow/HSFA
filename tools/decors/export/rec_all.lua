-- BALAYAGE COMPLET D'UN DECOR (export de tous les decors) : X d'une butee a l'autre, puis course Y.
-- Charge l'etat de combat ST (decor deja force), puis enchaine des segments {cible c, maintien, mode Y} :
--   nat  : Y naturel (J1 saute pendant les maintiens)
--   haut : Y des 2 joueurs imposes tres haut (+$100) -> la camera monte jusqu'a sa BUTEE NATURELLE (mesuree)
--   cup  : camera Y imposee (prise d'ecriture sur $FF82A4 = decalage camera Y, + = vers le haut)
--          a (butee naturelle mesuree + CUPX), au-dela de la course reelle (marge d'export)
--   cdn  : camera Y imposee a -CDN (vers le bas)
-- Joueurs : X imposes (J1 = c - GAP, J2 = c + GAP), vies maintenues.
-- Releve par image (REC, format FRM2) : t, c, mode, cam Y ($FF82A4), CPS-A (64 o), CPS-B (64 o), palette MAME
--   (pens 0..$BFF, ARGB), puis les pages de 64 Ko de la RAM video ($900000/$910000/$920000) contenant une base
--   (plans, rowscroll, palette) de l'image courante ou precedente (masque de pages en tete).
-- Ecran (BGRA 384x224) toutes les SNAPP images dans SCR. ISO=n : plan n seul (layer control force), ISO=0 : 3 plans ;
--   ISO defini -> sprites supprimes (ecritures objram remplacees par $FF00).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local B = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local SC = manager.machine.screens[":screen"]
local ports = manager.machine.ioport.ports
local REC = os.getenv("REC"); local SCR = os.getenv("SCR")
if REC == "" then REC = nil end
local SNAPP = tonumber(os.getenv("SNAPP") or "8")
local ISO = tonumber(os.getenv("ISO") or "")
local GAP = tonumber(os.getenv("GAP") or "96")
local SPEED = tonumber(os.getenv("SPEED") or "4")
local CUPX = tonumber(os.getenv("CUPX") or "32")
local CDN = tonumber(os.getenv("CDN") or "16")
local fr = REC and io.open(REC, "wb"); local fs = SCR and io.open(SCR, "wb")
local J1, J2 = 0xFF8400, 0xFF8800
local CAMY = 0xFF82A4
local PATH = {}
for a, b, m in string.gmatch(os.getenv("PATH_C") or
    "80:60:nat,480:60:nat,480:50:haut,80:50:haut,80:40:cup,480:40:cup,480:40:cdn,80:40:cdn,280:10:nat",
    "(%x+):(%d+):(%a+)") do PATH[#PATH+1] = {tonumber(a, 16), tonumber(b), m} end
if ISO then
  local en = ({[0] = 0x0e, [1] = 0x02, [2] = 0x04, [3] = 0x08})[ISO]
  LT = mem:install_write_tap(0x804166, 0x804167, "lay", function(o, d, m) return (d & ~0x3e) | en end)
  OT1 = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) return 0xff00 end)
end
local force_cam = nil
local camtop = 0                 -- butee haute naturelle mesuree (max de $FF82A4 en mode haut, signe)
CT = mem:install_write_tap(CAMY, CAMY + 1, "camy", function(o, d, m) if force_cam then return force_cam & 0xffff end end)
local MODES = {nat = 0, haut = 1, cup = 2, cdn = 3}
local k, t, c, seg, hold, y0 = 0, 0, nil, 1, 0, nil
local prevpages = 0
local function s16(v) if v >= 0x8000 then return v - 0x10000 end return v end
local function pages_of()
  local m = 0
  for _, o in ipairs({0x02, 0x04, 0x06, 0x08, 0x0a}) do
    local b = (A:read_u16(o) * 256) & 0x3ffff
    m = m | (1 << (b >> 16))
    if o == 0x0a then m = m | (1 << ((b + 0x17ff) >> 16)) end
  end
  return m & 7
end
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load(os.getenv("ST")); return end
  if k < 4 then return end
  if not c then c = mem:read_u16(J1 + 0x10) + GAP; y0 = mem:read_u16(J1 + 0x14) end
  local tg = PATH[seg]
  local mode = tg and tg[3] or "nat"
  if tg then
    if c < tg[1] then c = math.min(tg[1], c + SPEED) elseif c > tg[1] then c = math.max(tg[1], c - SPEED)
    else hold = hold + 1; if hold >= tg[2] then seg = seg + 1; hold = 0 end end
  end
  -- mode Y
  local up = (mode == "nat") and hold > 0 and hold % 45 < 12
  for fn, f in pairs(ports[":IN0"].fields) do if fn == "P1 Up" then f:set_value(up and 1 or 0) end end
  if mode == "haut" then
    mem:write_u16(J1 + 0x14, y0 + 0x100); mem:write_u16(J2 + 0x14, y0 + 0x100)
    local cy = s16(mem:read_u16(CAMY)); if cy > camtop then camtop = cy end
  end
  if mode == "cup" then force_cam = camtop + CUPX elseif mode == "cdn" then force_cam = -CDN else force_cam = nil end
  if force_cam then mem:write_u16(CAMY, force_cam & 0xffff) end
  mem:write_u16(J1 + 0x10, c - GAP); mem:write_u16(J2 + 0x10, c + GAP)
  for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end
  if fr then
    local pg = pages_of()
    local pm = pg | prevpages; prevpages = pg
    local s = {string.pack(">c4I4I4I2i2I2", "FRM2", t, c, MODES[mode], s16(mem:read_u16(CAMY)), pm)}
    for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
    for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", B:read_u16(o)) end
    for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
    for p = 0, 2 do
      if pm & (1 << p) ~= 0 then
        local b0 = p * 0x10000
        for o = b0, b0 + 0xfffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
      end
    end
    fr:write(table.concat(s))
  end
  if fs and t % SNAPP == 0 then
    local px, w, h = SC:pixels()
    fs:write(string.pack(">c4I4I4I4", "SCR0", t, w, h)); fs:write(px)
  end
  t = t + 1
  if not PATH[seg] then
    if fr then fr:close() end; if fs then fs:close() end
    print(string.format("FIN %d camtop %d", t, camtop)); manager.machine:exit()
  end
end)
