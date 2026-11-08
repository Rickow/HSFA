-- (31/10) enveloppe : charge SNP_SUITE ; capture d'ecran aux images SNP="n,n,..."
dofile(os.getenv("SNP_SUITE"))
local n, Q = 0, {}
for x in string.gmatch(os.getenv("SNP") or "", "%d+") do Q[tonumber(x)] = true end
emu.register_frame_done(function() n = n + 1; if Q[n] then manager.machine.video:snapshot() end end)
