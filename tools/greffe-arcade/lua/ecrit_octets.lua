-- (31/10) enveloppe : charge ECR_SUITE ; de l'image ECR_F0 a ECR_F1, ecrit chaque image les octets ECR="ff8519=00,..."
dofile(os.getenv("ECR_SUITE"))
local m = manager.machine.devices[":maincpu"].spaces["program"]; local n = 0
local f0, f1 = tonumber(os.getenv("ECR_F0") or "0"), tonumber(os.getenv("ECR_F1") or "99999999")
emu.register_frame_done(function()
  n = n + 1
  if n < f0 or n > f1 then return end
  for a, v in string.gmatch(os.getenv("ECR"), "(%x+)=(%x+)") do m:write_u8(tonumber(a, 16), tonumber(v, 16)) end
end)
