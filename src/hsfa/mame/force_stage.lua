-- (HANDOFF §92) force le decor : toute ecriture de $FF8100 ($100(A5), decor*2) entre les images FS0 et FS1
-- devient STG (hex, ex. 22 = Gen) ; SUIVI=1 imprime chaque changement de decor (« S image valeur »)
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local k, last = 0, -1
local FS0, FS1, STG = tonumber(os.getenv("FS0")), tonumber(os.getenv("FS1")), tonumber(os.getenv("STG"), 16)
FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if k >= FS0 and k <= FS1 and d ~= 0 then
    if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
  end
end)
emu.register_frame_done(function()
  k = k + 1
  if os.getenv("SUIVI") then
    local s = mem:read_u16(0xFF8100)
    if s ~= last then print(string.format("S %d %04x", k, s)); last = s end
  end
end)
dofile("<workspace>/work/mame/jeu.lua")
