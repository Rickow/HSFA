-- BALAYAGE CAMERA + RELEVE PAR IMAGE (decors_ws)
-- Charge l'etat de combat ST, impose les X des 2 joueurs (J1 = c - GAP, J2 = c + GAP) selon un trajet,
-- et ecrit pour CHAQUE image : registres CPS-A (64 o) et CPS-B (64 o), palette MAME (pens 0..0xBFF, ARGB),
-- RAM video $900000-$90FFFF (64 Ko : tilemaps, table rowscroll, source palette).
-- Ecran (BGRA 384x224) toutes les SNAPP images dans SCR.
-- ISO=n (1,2,3) : rend SEUL le plan scroll n (CPS-B layer control force) ; ISO=0 : tous les plans ;
--   avec ISO defini, les sprites sont supprimes (ecritures objram remplacees par $FF00 = fin de liste).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local A = manager.machine.memory.shares[":cps_a_regs"]
local B = manager.machine.memory.shares[":cps_b_regs"]
local G = manager.machine.memory.shares[":gfxram"]
local P = manager.machine.palettes[":palette"]
local SC = manager.machine.screens[":screen"]
local REC = os.getenv("REC"); local SCR = os.getenv("SCR")
local SNAPP = tonumber(os.getenv("SNAPP") or "8")
local ISO = tonumber(os.getenv("ISO") or "")
local GAP = tonumber(os.getenv("GAP") or "96")
local fr = REC and io.open(REC, "wb"); local fs = SCR and io.open(SCR, "wb")
local J1, J2 = 0xFF8400, 0xFF8800
local JUMP = os.getenv("JUMP") == "1"
local ports = manager.machine.ioport.ports
-- trajet : liste {cible, maintien} ; 2 px / image
local PATH = {}
for a, b in string.gmatch(os.getenv("PATH_C") or "100:40,400:40,280:20", "(%x+):(%d+)") do PATH[#PATH+1] = {tonumber(a, 16), tonumber(b)} end
if ISO then
  local en = ({[0] = 0x0e, [1] = 0x02, [2] = 0x04, [3] = 0x08})[ISO]
  LT = mem:install_write_tap(0x804166, 0x804167, "lay", function(o, d, m) return (d & ~0x3e) | en end)
  OT1 = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m) return 0xff00 end)
end
local k, t, c, seg, hold = 0, 0, nil, 1, 0
emu.register_frame_done(function()
  k = k + 1
  if k == 2 then manager.machine:load(os.getenv("ST")); return end
  if k < 4 then return end
  if not c then c = mem:read_u16(J1 + 0x10) + GAP end
  -- avance du trajet
  local tg = PATH[seg]
  if tg then
    if c < tg[1] then c = math.min(tg[1], c + 2) elseif c > tg[1] then c = math.max(tg[1], c - 2)
    else hold = hold + 1; if hold >= tg[2] then seg = seg + 1; hold = 0 end end
  end
  -- JUMP=1 : J1 saute pendant les maintiens (camera verticale)
  local up = JUMP and hold > 0 and hold % 45 < 12
  for fn, f in pairs(ports[":IN0"].fields) do if fn == "P1 Up" then f:set_value(up and 1 or 0) end end
  mem:write_u16(J1 + 0x10, c - GAP); mem:write_u16(J2 + 0x10, c + GAP)
  for _, j in ipairs({J1, J2}) do mem:write_u16(j + 0x50, 0x90); mem:write_u16(j + 0x52, 0x90) end
  if fr then
    local s = {string.pack(">c4I4I4", "FRM0", t, c)}
    for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A:read_u16(o)) end
    for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", B:read_u16(o)) end
    for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P:pen_color(i)) end
    for o = 0, 0xfffe, 2 do s[#s+1] = string.pack(">I2", G:read_u16(o)) end
    fr:write(table.concat(s))
  end
  if fs and t % SNAPP == 0 then
    local px, w, h = SC:pixels()
    fs:write(string.pack(">c4I4I4I4", "SCR0", t, w, h)); fs:write(px)
  end
  t = t + 1
  if not PATH[seg] then
    if fr then fr:close() end; if fs then fs:close() end
    print("FIN " .. t); manager.machine:exit()
  end
end)
