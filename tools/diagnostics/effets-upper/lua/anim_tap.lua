-- QUI POSE L'ANIMATION D'UN ACTEUR (agent_effets_upper) : charge tournee.lua (copie locale) puis prise d'ecriture sur le
-- champ $1C/$1E (pointeur du pas d'animation, long a moities echangees : mot bas en $1C, mot haut en $1E) des acteurs
-- de $FFA000-$FFDFFF. A l'ecriture du mot haut : pas = (haut << 16) | bas, contexte CPU (PC, A0, D0, retour en (SP),
-- A6), classe / sous-type (octets +2 / +3 PS2 = XOR 1). Table supposee = A0 - D0.w (entree $1A01E : A0 = T + T[2n]).
-- Sortie ANIM_OUT : combinaisons uniques avec compte et premiere image. Filtre PAS (hex "a-b,...") facultatif.
dofile("<workspace>/work/agent_effets_upper/lua/tournee.lua")
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local plages = {}
for a, b in string.gmatch(os.getenv("PAS") or "0-FFFFFFFF", "(%x+)-(%x+)") do plages[#plages + 1] = {tonumber(a, 16), tonumber(b, 16)} end
local function dans(c) for _, p in ipairs(plages) do if c >= p[1] and c <= p[2] then return true end end return false end
local function u8(a) return mem:read_u8(a ~ 1) end
local vus, ordre = {}, {}
local img = 0
emu.register_frame_done(function() img = img + 1 end)
ANIM_TAP = mem:install_write_tap(0xFFA000, 0xFFDFFF, "anim", function(offset, data, mask)
  if offset & 0x7F ~= 0x1E then return end
  local base = offset - 0x1E
  local pas = ((data & 0xffff) << 16) | mem:read_u16(base + 0x1C)
  if not dans(pas) then return end
  local s = cpu.state
  local pc, a0, d0, sp, a6 = s["PC"].value, s["A0"].value & 0xffffff, s["D0"].value, s["SP"].value, s["A6"].value & 0xffffff
  local ret = (mem:read_u16(sp) << 16) | mem:read_u16(sp + 2)
  local d0w = d0 & 0xffff; if d0w >= 0x8000 then d0w = d0w - 0x10000 end
  local cle = string.format("cl=%02X st=%02X pc=%06X ret=%06X D0=%04X table?=%06X pas=%06X", u8(base + 2), u8(base + 3), pc, ret & 0xffffff, d0 & 0xffff, (a0 - d0w) & 0xffffff, pas)
  if not vus[cle] then vus[cle] = {1, img, base, mem:read_u16(0xFF800C)}; ordre[#ordre + 1] = cle else vus[cle][1] = vus[cle][1] + 1 end
end)
emu.register_frame_done(function()
  if img % 1000 == 0 then
    local f = io.open(os.getenv("ANIM_OUT"), "w")
    for _, k in ipairs(ordre) do local v = vus[k]; f:write(string.format("%6d img=%6d acteur=%06X mode=%04X %s\n", v[1], v[2], v[3], v[4], k)) end
    f:close()
  end
end)
