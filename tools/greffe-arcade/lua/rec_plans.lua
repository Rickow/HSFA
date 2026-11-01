-- (e26) enveloppe : charge REC_BASE (defaut lua/graine_pc.lua, qui charge LUA_BASE), puis releve aux images REC_IMAGES
-- ("n,n,...") ou toutes les REC_PAS images entre REC_DE et REC_A : format FRM2 de decors_sfa2/export/lua/rec_sfa2.lua
-- (t, c = image, mode 0, cam Y 0, masque de pages 7 ; CPS-A, CPS-B, palette MAME $000-$BFF, RAM video $900000-$92FFFF)
-- dans REC ; et dans REC.txt : image, registres de bases des plans du fork ($804200-$804205), $FF8100, $FF7E10, $FF8032.
dofile(os.getenv("REC_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mem_r = manager.machine.devices[":maincpu"].spaces["program"]
local A_r = manager.machine.memory.shares[":cps_a_regs"]
local B_r = manager.machine.memory.shares[":cps_b_regs"]
local G_r = manager.machine.memory.shares[":gfxram"]
local P_r = manager.machine.palettes[":palette"]
local fr_r = io.open(os.getenv("REC"), "wb"); local ft_r = io.open(os.getenv("REC") .. ".txt", "w")
local IM_r = {}
for x in string.gmatch(os.getenv("REC_IMAGES") or "", "%d+") do IM_r[tonumber(x)] = true end
local de_r, a_r, pas_r = tonumber(os.getenv("REC_DE") or "0"), tonumber(os.getenv("REC_A") or "0"), tonumber(os.getenv("REC_PAS") or "0")
local k_r = 0
local REC_TOUS_r = tonumber(os.getenv("REC_TOUS") or ""); local vu_r = {}
-- REC_DECOR=hh : releve toutes les REC_PAS images de combat (A5+8 = 6) sur le decor $FF8100 = hh, REC_MAX releves au plus
local dec_r = tonumber(os.getenv("REC_DECOR") or "", 16); local max_r = tonumber(os.getenv("REC_MAX") or "8"); local nc_r, nr_r = 0, 0
emu.register_frame_done(function()
  k_r = k_r + 1
  local ok = IM_r[k_r] or (pas_r > 0 and not dec_r and k_r >= de_r and k_r <= a_r and (k_r - de_r) % pas_r == 0)
  if dec_r and mem_r:read_u16(0xFF8100) == dec_r and mem_r:read_u16(0xFF8008) == 6 and nr_r < max_r then
    nc_r = nc_r + 1
    if nc_r % pas_r == 0 then ok = true; nr_r = nr_r + 1 end
  end
  -- REC_TOUS=n : un releve par decor ($FF8100), a la n-ieme image de combat (A5+0 = 2, A5+4 = 4, A5+8 = 6) sur ce decor
  if REC_TOUS_r then
    if mem_r:read_u16(0xFF8000) == 2 and mem_r:read_u16(0xFF8004) == 4 and mem_r:read_u16(0xFF8008) == 6 then
      local d = mem_r:read_u16(0xFF8100); vu_r[d] = (vu_r[d] or 0) + 1
      if vu_r[d] == REC_TOUS_r then ok = true end
    end
  end
  if not ok then return end
  local s = {string.pack(">c4I4I4I2i2I2", "FRM2", k_r, k_r, 0, 0, 7)}
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", A_r:read_u16(o)) end
  for o = 0, 0x3e, 2 do s[#s+1] = string.pack(">I2", B_r:read_u16(o)) end
  for i = 0, 0xbff do s[#s+1] = string.pack(">I4", P_r:pen_color(i)) end
  for o = 0, 0x2fffe, 2 do s[#s+1] = string.pack(">I2", G_r:read_u16(o)) end
  fr_r:write(table.concat(s)); fr_r:flush()
  ft_r:write(string.format("%d bases %04x %04x %04x decor %04x drapeau %02x couches %04x\n", k_r, mem_r:read_u16(0x804200),
    mem_r:read_u16(0x804202), mem_r:read_u16(0x804204), mem_r:read_u16(0xFF8100), mem_r:read_u8(0xFF7E10), mem_r:read_u16(0xFF8032)))
  ft_r:flush()
end)
