-- BANC VISUEL (HANDOFF §65) : emule dans MAME la NUMEROTATION DES TUILES DE PLAN de l'Anthology, que le
-- fork appliquera : code CPS2 = code portage + decalage du plan (scroll1 +0, scroll2 +$5600, scroll3 +$B00).
-- Les bases des plans sont suivies sur les registres CPS-A ($804102/04/06). Captures : SNAPS="250,500,..."
dofile("<workspace>/work/mame/banc_mem.lua")
local space = manager.machine.devices[":maincpu"].spaces["program"]
local base = {[2]=0x900000, [3]=0x904000, [4]=0x908000}
local OFF = {[3]=0x5600, [4]=0x0b00}      -- index 3 = scroll2 ($804104), 4 = scroll3 ($804106)
tap1 = space:install_write_tap(0x804102, 0x804107, "bases", function(offset, data, mask)
  local k = (offset - 0x804100) // 2 + 1
  base[k] = (data & 0xffc0) << 8
end)
tap2 = space:install_write_tap(0x900000, 0x92ffff, "tuiles", function(offset, data, mask)
  for k, off in pairs(OFF) do
    local b = base[k]
    if offset >= b and offset < b + 0x4000 and ((offset - b) & 2) == 0 then
      return (data + off) & 0xffff
    end
  end
end)
local frames = 0
local want = {}; local last = 0
for n in string.gmatch(os.getenv("SNAPS") or "250,500,750,1000,1250,1500,1750,2000", "%d+") do
  want[tonumber(n)] = true; if tonumber(n) > last then last = tonumber(n) end end
emu.register_frame_done(function()
  frames = frames + 1
  if want[frames] then manager.machine.video:snapshot() end
  if frames >= last then manager.machine:exit() end
end)
