-- (e38) BANC DES DÉCORS : charge BD_BASE (pilote : tournee_arcade.lua pour la greffe, tournee_greffe.lua pour Upper),
-- impose le décor BD_DECOR (hexa, mot $FF8100 et $FF8174) en partie (A5+0 = 2, A5+4 ≠ 0) jusqu'au 1er combat (pas au démarrage :
-- le test de RAM plantait, ex. $22), puis pilote la CAMÉRA en imposant le X
-- des joueurs (+$12 des structures $FF8400 / $FF8800, vies $50 maintenues) : butée gauche, centre, butée droite,
-- balayage aller-retour à 2 px/image puis 1 px/image. Relevé (BD_OUT) à chaque image du balayage :
--   « I c k s1x s1y s2x s2y s3x s3y cam »    (registres CPS-A $80410C-$804116, caméra $FF8290/$FF8292)
--   « O slot hex(+$00..+$3F) »                (réservoir des objets de décor $FFC000, 16 × $80, emplacements actifs)
--   « R $FF4174 $FF4176 défilement par ligne (224 lignes) »
--   « S page code attr x y »                  (liste BRUTE d'objets du jeu, BANC_OMBRE, entrées non nulles)
dofile(os.getenv("BD_BASE"))
local mem_b = manager.machine.devices[":maincpu"].spaces["program"]
local A_b = manager.machine.memory.shares[":cps_a_regs"]
local fb = io.open(os.getenv("BD_OUT"), "w")
local GR_b = manager.machine.memory.shares[":gfxram"]
-- (e38) « R » : défilement par ligne de scroll2 (base CPS-A $08), 224 lignes visibles à partir de (s2Y + 16) & $3FF,
-- relatif à s2X (mots signés) + mots $FF4174 / $FF4176 (sorties des effets par décor, A5+$C174/$C176)
local function ligne_rs()
  local base = ((A_b:read_u16(0x08) << 8) & 0x3FFFF) & ~0x7FF
  local y0 = A_b:read_u16(0x12) + 16
  local t = {}
  for l = 0, 223 do t[#t + 1] = string.format("%x", GR_b:read_u16(base + (((y0 + l) & 0x3FF) * 2)) & 0xFFFF) end
  return string.format("R %04x %04x %s", mem_b:read_u16(0xFF4174), mem_b:read_u16(0xFF4176), table.concat(t, ","))
end
local DEC_b = tonumber(os.getenv("BD_DECOR") or "", 16)
local T0_b = tonumber(os.getenv("BD_T0") or "150")
local SP_b = os.getenv("BD_SPRITES") ~= "0"
local k_b, c_b, fini_b = 0, -1, false
local SN_b = {}
for x in string.gmatch(os.getenv("BD_SNAPS") or "", "%d+") do SN_b[tonumber(x)] = true end
-- trajectoire du centre des joueurs (X monde) : butées / centre puis balayages
local G_b, C_b, D_b = 0x130, 0x280, 0x450
local traj = {}
local function tenir(p, n) for _ = 1, n do traj[#traj + 1] = p end end
local function aller(a, b, pas) local s = (b > a) and pas or -pas; for p = a, b, s do traj[#traj + 1] = p end end
tenir(G_b, 150); tenir(C_b, 150); tenir(D_b, 150)
aller(D_b, G_b, 2); aller(G_b, D_b, 2); aller(D_b, C_b, 1); tenir(C_b, 60)
local function combat() return mem_b:read_u16(0xFF8000) == 2 and mem_b:read_u16(0xFF8004) == 4 and mem_b:read_u16(0xFF8008) == 6 end
local function ligne_sprites(page)
  local om = BANC_OMBRE or {}
  for a = page, page + 0x7ff8, 8 do
    local x, y, c, at = om[a] or 0, om[a + 2] or 0, om[a + 4] or 0, om[a + 6] or 0
    if x == 0x8000 and y == 0x8000 then break end
    if x ~= 0 or y ~= 0 or c ~= 0 or at ~= 0 then fb:write(string.format("S %d %04x %04x %04x %04x\n", page == 0x700000 and 0 or 1, c, at, x, y)) end
  end
end
emu.register_frame_done(function()
  k_b = k_b + 1
  if fini_b then return end
  if c_b < 0 then
    if DEC_b and mem_b:read_u16(0xFF8000) == 2 and mem_b:read_u16(0xFF8004) ~= 0 then mem_b:write_u16(0xFF8100, DEC_b); mem_b:write_u16(0xFF8174, DEC_b) end
    if combat() then c_b = 0; fb:write(string.format("COMBAT %d decor %04x drapeau %02x\n", k_b, mem_b:read_u16(0xFF8100), mem_b:read_u8(0xFF7E10))) end
    return
  end
  c_b = c_b + 1
  if not combat() then fb:write(string.format("HORS_COMBAT %d %d\n", k_b, c_b)); fb:flush(); fini_b = true; return end
  mem_b:write_u16(0xFF8450, 0x90); mem_b:write_u16(0xFF8850, 0x90)
  local i = c_b - T0_b
  if i >= 1 then
    local p = traj[i]
    if not p then fb:write(string.format("FIN %d\n", k_b)); fb:flush(); fini_b = true
      if os.getenv("BD_SORTIE") ~= "0" then manager.machine:exit() end
      return end
    mem_b:write_u16(0xFF8412, p - 0x30); mem_b:write_u16(0xFF8812, p + 0x30)
  end
  if SN_b[i] then manager.machine.video:snapshot(); fb:write(string.format("SNAP %d %d\n", i, k_b)) end
  if i < -30 then return end
  fb:write(string.format("I %d %d %04x %04x %04x %04x %04x %04x %04x %04x %02x\n", i, k_b, A_b:read_u16(0x0C), A_b:read_u16(0x0E),
    A_b:read_u16(0x10), A_b:read_u16(0x12), A_b:read_u16(0x14), A_b:read_u16(0x16), mem_b:read_u16(0xFF8290), mem_b:read_u16(0xFF8292),
    mem_b:read_u8(0xFF7E10)))
  if os.getenv("BD_RS") ~= "0" then fb:write(ligne_rs() .. "\n") end
  for s = 0, 15 do
    local a = 0xFFC000 + s * 0x80
    if mem_b:read_u16(a) ~= 0 then
      local t = {}
      for o = 0, 0x3e, 2 do t[#t + 1] = string.format("%04x", mem_b:read_u16(a + o)) end
      fb:write(string.format("O %d %s\n", s, table.concat(t, "")))
    end
  end
  if SP_b then ligne_sprites(0x700000); ligne_sprites(0x708000) end
end)
