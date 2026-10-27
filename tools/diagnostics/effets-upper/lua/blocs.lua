-- BLOCS DE DONNEES PAR PERSO D'UPPER (agent_effets_upper) : charge tournee.lua (copie locale), puis, 120 images apres le
-- debut du 1er combat (J1 = PERSO) : journal BLOCS_OUT avec
--  - T_61A100 (image $B0440, 48 longs : 32 pointeurs + la table suivante) et T_749838 (image $1DFB78, 40 longs), lus
--    dans la memoire du 68K (longs a moities echangees -> valeur PS2) et convertis par la regle de CONV_A0 ($4FE) ;
--  - $2B0/$2B4/$2B8/$2BC de J1 et J2 (RAM), et les 12 longs de l'en-tete du bloc du perso de J1 ;
--  - vidages : RAM de travail $FF0000-$FFFFFF (BLOCS_DIR/ram_<perso>.bin) et bloc du perso de J1, de son debut au bloc
--    suivant de T_749838 (BLOCS_DIR/bloc_<perso>_<adr68k>.bin, vue 68K = mots gros-boutistes tels que lus par le jeu).
-- Lecture seule.
dofile("<workspace>/work/agent_effets_upper/lua/tournee.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local out = io.open(os.getenv("BLOCS_OUT"), "w")
local DIR = os.getenv("BLOCS_DIR")
local function u8(a) return mem:read_u8(a ~ 1) end
local function lech(a) return (mem:read_u16(a + 2) << 16) | mem:read_u16(a) end
local function conv(a)   -- CONV_A0 d'Upper (image $400 -> $4FE)
  if a < 0x60ACC0 or a >= 0xC3FC50 then return a end
  if a >= 0xA14000 then
    if a >= 0xA60000 then
      if a >= 0xA80000 then if a >= 0xC00000 then return a - 0x885100 end return a end
      if a >= 0xA62000 then return a + 0x530000 end return a + 0xBB8000
    end
    if a >= 0xA20000 then if a >= 0xA50000 then return a + 0x530000 end return a + 0xEE0000 end
    return a
  end
  if a >= 0xA00000 then
    if a >= 0xA10000 then if a >= 0xA12000 then return a + 0xCF6000 end return a + 0xCF0000 end
    return a + 0x5F0000
  end
  if a >= 0x8E4AE0 then if a >= 0x9A0180 then return a + 0x55FE80 end return a + 0x39B520 end
  return (a - 0x569CC0) & 0xFFFFFFFF
end
local stable, fait = 0, false
emu.register_frame_done(function()
  if fait then return end
  local combat = mem:read_u16(0xFF800C) == 6 and u8(0xFF8404) == 2
  if combat then stable = stable + 1 else stable = 0 end
  if stable ~= 120 then return end
  fait = true
  local p1, p2 = u8(0xFF8502), u8(0xFF8902)
  out:write(string.format("J1 perso %02X  J2 perso %02X  decor $FF8100=%04X\n", p1, p2, mem:read_u16(0xFF8100)))
  out:write("T_61A100 (image $B0440) : index, long lu (PS2), CONV\n")
  for i = 0, 47 do local v = lech(0xB0440 + 4 * i); out:write(string.format("  %02X %08X -> %08X\n", i, v, conv(v))) end
  out:write("T_749838 (image $1DFB78) : index, long lu (PS2), CONV\n")
  local t = {}
  for i = 0, 39 do local v = lech(0x1DFB78 + 4 * i); t[i] = v; out:write(string.format("  %02X %08X -> %08X\n", i, v, conv(v))) end
  for _, j in ipairs({0xFF8400, 0xFF8800}) do
    out:write(string.format("joueur %06X perso %02X :", j, u8(j + 0x102)))
    for _, o in ipairs({0x2B0, 0x2B4, 0x2B8, 0x2BC}) do local v = lech(j + o); out:write(string.format(" $%X=%08X(->%08X)", o, v, conv(v))) end
    out:write(string.format(" isme $132=%02X\n", u8(j + 0x132)))
  end
  -- en-tete et bloc du perso de J1
  local b = t[p1]; local b68 = conv(b)
  local suiv = nil
  for i = 0, 39 do if t[i] > b and (not suiv or t[i] < suiv) then suiv = t[i] end end
  out:write(string.format("bloc J1 : PS2 %08X -> 68K %08X ; bloc suivant PS2 %08X ; taille %X\n", b, b68, suiv or 0, (suiv or b) - b))
  for i = 0, 11 do
    local v = lech(b68 + 4 * i)
    out:write(string.format("  isme %d %s : %08X -> %08X\n", i // 4, ({"$2B0", "$2B8", "$2B4", "$2BC"})[i % 4 + 1], v, conv(v)))
  end
  if suiv then
    local f = io.open(string.format("%s/bloc_%02X_%06X.bin", DIR, p1, b68), "wb"); local s = {}
    for a = b68, b68 + (suiv - b) - 2, 2 do s[#s + 1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(s)); f:close()
  end
  local f = io.open(string.format("%s/ram_%02X.bin", DIR, p1), "wb"); local s = {}
  for a = 0xFF0000, 0xFFFFFE, 2 do s[#s + 1] = string.pack(">I2", mem:read_u16(a)) end
  f:write(table.concat(s)); f:close()
  out:write("FIN\n"); out:close()
  manager.machine:exit()
end)
