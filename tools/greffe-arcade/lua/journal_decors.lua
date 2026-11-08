-- (e28) enveloppe : charge REC_BASE (defaut tournee_hyper_guy.lua), puis JOURNAL DES DECORS dans JDEC : a chaque entree en
-- combat (A5+4 = 4, A5+8 = 6) : image, id etendu ($103) de J1 et de J2, decor $FF8100, $174, drapeaux $FF7E10 / $FF7E11 /
-- $FF7E00, mode $FF4201, bases de plans du fork ; JDEC_SNAP=n : capture a la n-ieme image de chaque combat.
dofile(os.getenv("REC_BASE") or "<workspace>/work/greffe_arcade/lua/tournee_hyper_guy.lua")
local m_j = manager.machine.devices[":maincpu"].spaces["program"]
local f_j = io.open(os.getenv("JDEC"), "w"); local SN_j = tonumber(os.getenv("JDEC_SNAP") or "0")
local k_j, dans_j, n_j, nc_j = 0, false, 0, 0
emu.register_frame_done(function()
  k_j = k_j + 1
  local c = m_j:read_u16(0xFF8004) == 4 and m_j:read_u16(0xFF8008) == 6
  if c and not dans_j then
    nc_j = nc_j + 1; n_j = 0
    f_j:write(string.format("COMBAT %d image %d J1 %02x J2 %02x decor %04x 174 %04x fe10 %02x fe11 %02x fe00 %02x mode %02x bases %04x %04x %04x\n",
      nc_j, k_j, m_j:read_u8(0xFF8503), m_j:read_u8(0xFF8903), m_j:read_u16(0xFF8100), m_j:read_u16(0xFF8174), m_j:read_u8(0xFF7E10),
      m_j:read_u8(0xFF7E11), m_j:read_u8(0xFF7E00), m_j:read_u8(0xFF4201), m_j:read_u16(0x804200), m_j:read_u16(0x804202), m_j:read_u16(0x804204)))
    f_j:flush()
  end
  if c then n_j = n_j + 1; if SN_j > 0 and n_j == SN_j then manager.machine.video:snapshot(); f_j:write(string.format("SNAP %d image %d decor %04x\n", nc_j, k_j, m_j:read_u16(0xFF8100))); f_j:flush() end end
  dans_j = c
end)
