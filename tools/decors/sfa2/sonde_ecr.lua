-- écritures de $FF8100 (PC, valeur, image, modes) pendant une partie (tournee.lua du banc, lecture seule)
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local kk = 0
local f = io.open(os.getenv("OUT") .. ".ecr", "w")
WT = mem:install_write_tap(0xFF8100, 0xFF8101, "ecr", function(o, d, m)
  f:write(string.format("image %d PC %06x val %04x masque %04x mode %04x/%04x/%04x J2 %02x\n", kk, cpu.state["PC"].value & 0xffffff,
    d, m, mem:read_u16(0xFF8000), mem:read_u16(0xFF8004), mem:read_u16(0xFF800C), mem:read_u8((0xFF8800 + 0x102) ~ 1))); f:flush()
end)
emu.register_frame_done(function() kk = kk + 1 end)
dofile("<workspace>/work/mame/tournee.lua")
