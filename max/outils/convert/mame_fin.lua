-- Fin arcade (sfa3ud, REF=1) : pendant la séquence de fin ($FF8004 = $000A), une capture toutes les PAS images (défaut 30)
-- avec les ombres de défilement $FF8022-$FF802C (scroll1/2/3 X,Y) dans journal.txt. Charge ensuite tournee.lua (HSFA).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local PAS = tonumber(os.getenv("PAS") or "30")
local f = io.open(os.getenv("FIN_OUT") .. "/journal.txt", "w"); local n = 0; local k = 0
emu.register_frame_done(function()
  if mem:read_u16(0xFF8004) ~= 0x000A then return end
  k = k + 1
  if k % PAS ~= 0 then return end
  local s = ""
  for a = 0xFF8022, 0xFF802C, 2 do s = s .. string.format("%04x ", mem:read_u16(a)) end
  n = n + 1
  f:write(string.format("%04d f%d %s\n", n - 1, manager.machine.screens[":screen"]:frame_number(), s)); f:flush()
  manager.machine.video:snapshot()
  if os.getenv("VIDAGE") == "1" then   -- plans scroll2/3/1 ($914000/$918000/$910000, 16 Ko) + palettes (8 Ko)
    local base = mem:read_u16(0xFF8020) * 256          -- palettes : copie lue par le registre $80410A (ombre $20(A5))
    for _, z in ipairs({{"s2", 0x914000}, {"s3", 0x918000}, {"s1", 0x910000}, {"pal", base}}) do
      local t = {}
      for a = z[2], z[2] + (z[1] == "pal" and 0x1FFE or 0x3FFE), 2 do t[#t + 1] = string.pack(">I2", mem:read_u16(a)) end
      local d = io.open(string.format("%s/%s_%04d.bin", os.getenv("FIN_OUT"), z[1], n - 1), "wb"); d:write(table.concat(t)); d:close()
    end
  end
end)
dofile(os.getenv("TOURNEE"))
