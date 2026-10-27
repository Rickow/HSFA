-- (HANDOFF §138) PROFIL DES ADAPTATEURS : nombre de lectures de mots d'opcodes par ADRESSE, sur les seules images de
-- combat ($FF800C = 6), a partir de l'image K0 (defaut 2500). Sortie POUT : « adresse compte » (hex, decimal),
-- reecrite toutes les 500 images. Se charge APRES tournee.lua (dofile) : PROF_TOUR=1 l'enchaine.
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]; local ops = cpu.spaces["opcodes"] or mem
local k, K0 = 0, tonumber(os.getenv("K0") or "2500")
local cnt, cur, nimg = {}, {}, 0
local PT
local function cb(o, d, m) cur[o] = (cur[o] or 0) + 1 end
local function dump()
  local f = io.open(os.getenv("POUT"), "w")
  f:write(string.format("# images_combat %d\n", nimg))
  for a, n in pairs(cnt) do f:write(string.format("%06x %d\n", a, n)) end
  f:close()
end
emu.register_frame_done(function()
  k = k + 1
  if k == K0 then PT = ops:install_read_tap(0x0, 0x3fffff, "profad", cb) end
  if k > K0 then
    if mem:read_u16(0xFF800C) == 6 then nimg = nimg + 1; for a, n in pairs(cur) do cnt[a] = (cnt[a] or 0) + n end end
    cur = {}
    if k % 500 == 0 then dump() end
  end
end)
