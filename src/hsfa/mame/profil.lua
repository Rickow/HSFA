-- profil : nombre de mots d'instruction lus par bloc de 256 octets pendant les images K0..K0+N (espace opcodes)
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]; local ops = cpu.spaces["opcodes"] or mem
local k, K0, N = 0, tonumber(os.getenv("K0")), tonumber(os.getenv("KN") or "300")
local cnt = {}
local function cb(o, d, m) local b = o >> 8; cnt[b] = (cnt[b] or 0) + 1 end
emu.register_frame_done(function()
  k = k + 1
  if k == K0 then PT = ops:install_read_tap(0x0, 0x3fffff, "prof", cb) end
  if k == K0 + N then
    PT:remove()
    local f = io.open(os.getenv("POUT"), "w")
    for b, n in pairs(cnt) do f:write(string.format("%06x %d\n", b << 8, n)) end
    f:close()
  end
end)
dofile("<workspace>/work/mame/commandes.lua")
