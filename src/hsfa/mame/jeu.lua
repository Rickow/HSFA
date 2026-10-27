-- PARTIE JOUABLE (HANDOFF §80) : sequence d'entrees + journal des modes + captures.
-- INPUTS="debut-fin:PORT:Champ;..."  (ex. "1500-1505::IN2:Coin 1"), SNAPS="f1,f2", NF=derniere image, OUT=journal
if os.getenv("BANC_MEM") ~= "0" then
  dofile("<workspace>/work/mame/banc_mem.lua")
  dofile("<workspace>/work/mame/banc_plans.lua")      -- traduction seulement (tuiles de plan Anthology)
  if os.getenv("SPRITES") ~= "0" then dofile("<workspace>/work/mame/banc_sprites.lua") end   -- banques (§82)
end
local frames = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local ports = manager.machine.ioport.ports
local seq = {}
for item in string.gmatch(os.getenv("INPUTS") or "", "[^;]+") do
  local a, b, p, f = string.match(item, "^(%d+)-(%d+):(:[%w]+):(.+)$")
  if a then table.insert(seq, {tonumber(a), tonumber(b), p .. "|" .. f}) end   -- cle = NOM (objet champ recree a chaque acces)
  -- (HANDOFF §90) forme periodique : 'debut-fin%periode,duree:PORT:champ' (appui de 'duree' images toutes les 'periode')
  local a2, b2, per, dur, p2, f2 = string.match(item, "^(%d+)-(%d+)%%(%d+),(%d+):(:[%w]+):(.+)$")
  if a2 then table.insert(seq, {tonumber(a2), tonumber(b2), p2 .. "|" .. f2, tonumber(per), tonumber(dur)}) end
end
local want = {}
for n in string.gmatch(os.getenv("SNAPS") or "", "%d+") do want[tonumber(n)] = true end
local NF = tonumber(os.getenv("NF") or "6000")
local log = io.open(os.getenv("OUT") or "/dev/null", "w")
local last = ""
if os.getenv("QSLOG") then   -- journal des commandes son (ecritures $618001/$618003 : code de commande)
  QSTAP = mem:install_write_tap(0x618000, 0x618003, "qs", function(offset, data, mask)
    log:write(string.format("QS %d %x %x\n", frames, offset, data & 0xff))
  end)
end
emu.register_frame_done(function()
  frames = frames + 1
  local v = {}
  for _, s in ipairs(seq) do
    local on = frames >= s[1] and frames <= s[2] and (not s[4] or (frames - s[1]) % s[4] < s[5])
    v[s[3]] = (v[s[3]] or 0) | (on and 1 or 0)
  end
  for k, x in pairs(v) do local p, f = string.match(k, "^(.-)|(.*)$"); ports[p].fields[f]:set_value(x) end
  local st = string.format("%04x %04x %04x", mem:read_u16(0xff8000), mem:read_u16(0xff8002), mem:read_u16(0xff8004))
  if st ~= last then log:write(string.format("%6d : %s\n", frames, st)); last = st end
  if want[frames] then manager.machine.video:snapshot() end
  if os.getenv("PCS") and frames % 300 == 0 then
    local cpu=manager.machine.devices[":maincpu"]
    log:write(string.format("PC %d pc=%x slot=%x flag=%x\n", frames, cpu.state["PC"].value, mem:read_u16(0x663884), mem:read_u16(0x663888)))
  end
  if frames >= NF then log:close(); manager.machine:exit() end
end)
