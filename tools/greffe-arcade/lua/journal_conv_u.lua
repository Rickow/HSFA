-- (greffe_arcade, etape 3) COPIE de work/agent_reorg_A/outils/journal_conv.lua : + prise sur le bloc externe $C80000 d Upper (donnees du module au-dela de U_SPLIT).
-- JOURNAL DES CONVERSIONS DE POINTEURS (ETAPE A, ARCHI-Reorganisation-Donnees.md) : instrumentation PURE (lecture
-- seule, aucune ecriture en memoire). A charger AVANT le script pilote (tournee.lua, commandes.lua, attraction) :
--   dofile(".../journal_conv.lua")
-- Talons observes (fetch d'opcode du premier mot, espace "opcodes") :
--   donnees  : CONV_A0..A6  = $400 $41E $440 $462 $484 $4A6 $4C8  (kernel68k.build_conv, plages PS2 [$583C40,$A97630))
--   code     : CCONV_A0..A6 = $3FF000 $3FF01E $3FF040 ... $3FF0C8 (build_code_conv, plage PS2 [$212B00,$583C40))
-- Piege : le 68000 PRELIT le mot qui suit le RTS d'un talon (= entree du talon suivant) ; un appel authentique se
-- reconnait a PC hors de la zone des talons (PC = adresse de retour dans l'appelant, le JSR n'a pas encore empile).
-- Provenance : anneau des 64 dernieres lectures de mots (RAM $FF0000-$FFFFFF, donnees ROM $090000-$3BFFFF,
-- RAM du portage $F00000-$FEFFFF) ; on cherche le long (a, a+2) dont la valeur, moities echangees ('s') ou native
-- ('n'), egale An. Pour une case RAM : dernier ecrivain (CURPC) de chacun des deux mots.
-- Sortie (JCONV_OUT) : lignes "E pc talon valeur origine forme ecrivain_a ecrivain_a2 nombre" (hex sauf nombre/talon).
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local ops = cpu.spaces["opcodes"] or mem
local st = cpu.state
local OUTF = os.getenv("JCONV_OUT") or "journal_conv.txt"
local F0 = tonumber(os.getenv("JCONV_F0") or "0")       -- premiere image journalisee
local ECRIV = os.getenv("JCONV_ECRIV") ~= "0"          -- suivi des ecrivains RAM
JC = JC or {}
local RA, RV = {}, {}
for i = 0, 63 do RA[i] = -1; RV[i] = 0 end
local ri = 0
local W = {}                                            -- dernier ecrivain par mot de RAM
local AGG = {}
local fr = 0
local nev, nspur = 0, 0
local function lec(o, d, m) ri = (ri + 1) & 63; RA[ri] = o; RV[ri] = d end
table.insert(JC, mem:install_read_tap(0xFF0000, 0xFFFFFF, "jc_ram", lec))
table.insert(JC, mem:install_read_tap(0x090000, 0x3BFFFF, "jc_rom", lec))
table.insert(JC, mem:install_read_tap(0xF00000, 0xFEFFFF, "jc_port", lec))
if ECRIV then
  local function ecr(o, d, m) W[o & ~1] = st["CURPC"].value end
  table.insert(JC, mem:install_write_tap(0xFF0000, 0xFFFFFF, "jc_wram", ecr))
  table.insert(JC, mem:install_write_tap(0xF00000, 0xFEFFFF, "jc_wport", ecr))
end
local function origine(v)
  -- plus recente paire (a, a+2) dont la valeur correspond
  local j = ri
  for _ = 1, 63 do
    local i0 = (j - 1) & 63
    if RA[i0] >= 0 and RA[j] == RA[i0] + 2 then
      local hi, lo = RV[i0], RV[j]
      if ((lo << 16) | hi) == v then return RA[i0], "s" end
      if ((hi << 16) | lo) == v then return RA[i0], "n" end
    end
    j = i0
  end
  return 0, "-"
end
local function evt(talon, reg, zlo, zhi)
  local pc = st["PC"].value & 0xffffff
  if pc >= zlo and pc < zhi then nspur = nspur + 1; return end   -- prelecture apres le RTS du talon precedent
  if fr < F0 then return end
  nev = nev + 1
  local v = st[reg].value & 0xffffffff
  local a, f = origine(v)
  local w1, w2 = 0, 0
  if a >= 0xF00000 then w1 = W[a] or 0; w2 = W[a + 2] or 0 end
  local key = string.format("%x %d %x %x %s %x %x", pc, talon, v, a, f, w1, w2)
  AGG[key] = (AGG[key] or 0) + 1
end
local DST = {0x400, 0x41E, 0x440, 0x462, 0x484, 0x4A6, 0x4C8}
local CST = {0x3FF000, 0x3FF01E, 0x3FF040, 0x3FF062, 0x3FF084, 0x3FF0A6, 0x3FF0C8}
for r = 0, 6 do
  local reg = "A" .. r
  table.insert(JC, ops:install_read_tap(DST[r + 1], DST[r + 1] + 1, "jc_d" .. r, function(o, d, m) evt(r, reg, 0x400, 0x600) end))
  table.insert(JC, ops:install_read_tap(CST[r + 1], CST[r + 1] + 1, "jc_c" .. r, function(o, d, m) evt(10 + r, reg, 0x3FF000, 0x3FF200) end))
end
emu.register_frame_done(function()
  fr = fr + 1
  -- blocs externes du banc ($A00000-$BFFFFF, banc_mem.lua) : tap pose APRES ceux du banc (valeurs servies)
  if fr == 1 then table.insert(JC, mem:install_read_tap(0xA00000, 0xBFFFFF, "jc_ext", lec)); table.insert(JC, mem:install_read_tap(0xC80000, 0xD0FFFF, "jc_ext2", lec)) end
end)
local function vider()
  local f = io.open(OUTF, "w")
  f:write(string.format("# images %d evenements %d prelectures_ecartees %d\n", fr, nev, nspur))
  for k, n in pairs(AGG) do f:write("E ", k, " ", n, "\n") end
  f:close()
end
JC_STOP = emu.add_machine_stop_notifier(vider)
