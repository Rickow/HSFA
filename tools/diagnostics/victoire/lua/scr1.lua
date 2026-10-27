-- journal des ecritures dans la page scroll1 (base CPS-A reg 1) entre les images W0 et W1 : image pc adresse donnee
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local sh = manager.machine.memory.shares
local fo = io.open(os.getenv("SOUT"), "w")
local W0, W1 = tonumber(os.getenv("W0")), tonumber(os.getenv("W1"))
local kk, tap = 0, nil
emu.register_frame_done(function()
  kk = kk + 1
  if kk == W0 then
    local base = (sh[":cps_a_regs"]:read_u16(2) << 8) & 0xffffff
    fo:write(string.format("base scroll1 %06x\n", base))
    tap = mem:install_write_tap(tonumber(os.getenv("TA0") or "900000",16), tonumber(os.getenv("TA1") or "92ffff",16), "s1", function(o, d, m)
      fo:write(string.format("%d %06x %06x %04x %04x\n", kk, cpu.state["PC"].value & 0xffffff, o, d, m)); return d end)
  end
  if kk == W1 and tap then tap:remove(); tap = nil; fo:flush() end
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
