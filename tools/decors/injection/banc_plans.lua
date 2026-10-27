-- (HANDOFF §120) fork sfa3hx : HSFA_PLANS="b1,b2,b3" (hexa, unites de 64 Ko) = bases des plans scroll1/2/3 ; les
-- memoires de decor sont rangees telles quelles dans la ROM etendue (hsfa_plans.py) : aucune conversion, aucune prise.
if os.getenv("HSFA_PLANS") then
  local sp = manager.machine.devices[":maincpu"].spaces["program"]
  local b = {}
  for v in string.gmatch(os.getenv("HSFA_PLANS"), "%x+") do b[#b + 1] = tonumber(v, 16) end
  local fait = false
  emu.register_frame_done(function()
    if not fait then for k = 1, 3 do sp:write_u16(0x804200 + 2 * (k - 1), b[k] or 0) end; fait = true end
  end)
  return
end
-- RENUMEROTATION DES TUILES DE PLAN de l Anthology (HANDOFF §65), commune a banc.lua et jeu.lua
local space = manager.machine.devices[":maincpu"].spaces["program"]
local base = {[2]=0x900000, [3]=0x904000, [4]=0x908000}
local OFF = {[3]=0x5600, [4]=0x0b00}      -- index 3 = scroll2 ($804104), 4 = scroll3 ($804106)
-- (HANDOFF §83) scroll3 : la tilemap du portage contient des indices LOCAUX de la banque 32x32 e312 (emplacement 5),
-- banque REORGANISEE (blocs a decalages differents) -> table banques/f312.bin (indice ROM 32x32 ; code MAME = -$4000)
local function charge(n)
  local h = io.open((os.getenv("BANC_BANQUES") or "<workspace>/work/mame/banques/") .. n, "rb"); if not h then return nil end
  local d = h:read("a"); h:close(); return d
end
-- (HANDOFF §83) tables locale -> indice ROM par plan ; code MAME = indice - debut du quart 1 dans l'unite du plan
local TAB = {[2] = {charge("plan1.bin"), 0x20000, 0}, [3] = {charge("plan2.bin"), 0x10000, 0x5600},
             [4] = {charge("f312.bin"), 0x4000, 0x0b00}}
local function convertit(k, c)
  local t = TAB[k]
  if t[1] and 4 * c + 4 <= #t[1] then
    local g = string.unpack("<I4", t[1], 4 * c + 1)
    if g ~= 0xFFFFFFFF and g >= t[2] and g - t[2] <= 0xffff then return g - t[2] end
  end
  if MANQUES then MANQUES[k * 0x10000 + c] = (MANQUES[k * 0x10000 + c] or 0) + 1 end   -- (diagnostic)
  return (c + t[3]) & 0xffff
end
-- (HANDOFF §103) le jeu ecrit souvent une tilemap AVANT de pointer le registre de base dessus (debut de l'intro :
-- tuiles en $914000 alors que scroll2 vaut encore $904000) : on garde la valeur BRUTE du portage de chaque mot de
-- code, et un changement de base reconvertit toute la zone du plan.
local RAW, occupe = {}, false
local function reconvertit(k)
  local b = base[k]
  occupe = true
  for o = b, b + 0x3ffc, 4 do space:write_u16(o, convertit(k, RAW[o] or space:read_u16(o))) end
  occupe = false
end
tap1 = space:install_write_tap(0x804102, 0x804107, "bases", function(offset, data, mask)
  local k = (offset - 0x804100) // 2 + 1
  local nb = (data & 0xffc0) << 8
  if nb ~= base[k] then base[k] = nb; reconvertit(k) end
end)
tap2 = space:install_write_tap(0x900000, 0x92ffff, "tuiles", function(offset, data, mask)
  if occupe then return end
  if mask ~= 0xffff then data = (((RAW[offset] or space:read_u16(offset)) & ~mask) | (data & mask)) & 0xffff end
  RAW[offset] = data
  for k = 2, 4 do
    local b = base[k]
    if offset >= b and offset < b + 0x4000 and ((offset - b) & 2) == 0 then
      return convertit(k, data)
    end
  end
end)
