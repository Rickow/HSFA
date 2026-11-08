-- (e28) enveloppe : charge REC_BASE (defaut lua/graine_pc.lua, qui charge LUA_BASE), puis, pour chaque decor ($FF8100),
-- a la REC_TOUS-ieme image de combat (A5+0 = 2, A5+4 = 4, A5+8 = 6) : capture d'ecran + liste BRUTE des objets de l'image
-- (BANC_OMBRE de banc_sprites.lua, avant conversion) dans REC_OBJ : image, decor, drapeau $FF7E10, puis une ligne par objet
-- « e<emplacement> code attr x y » (emplacement = bits 13-15 de Y). REC_OBJ_N=n : n releves par decor, toutes les REC_PAS images.
dofile(os.getenv("REC_BASE") or "<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local mem_o = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("REC_OBJ"), "w")
local TOUS_o = tonumber(os.getenv("REC_TOUS") or "240")
local N_o = tonumber(os.getenv("REC_OBJ_N") or "1"); local PAS_o = tonumber(os.getenv("REC_PAS") or "60")
local vu_o = {}; local k_o = 0
local function liste(page)
  local t = {}
  local om = BANC_OMBRE or {}
  for a = page, page + 0x7ff8, 8 do
    local x, y, c, at = om[a] or 0, om[a + 2] or 0, om[a + 4] or 0, om[a + 6] or 0
    if x == 0x8000 and y == 0x8000 then t[#t + 1] = string.format("FIN %x", a); break end
    if x ~= 0 or y ~= 0 or c ~= 0 or at ~= 0 then
      t[#t + 1] = string.format("e%d %04x %04x %04x %04x %x", (y >> 13) & 7, c, at, x, y, a) end
  end
  return t
end
emu.register_frame_done(function()
  k_o = k_o + 1
  if mem_o:read_u16(0xFF8000) == 2 and mem_o:read_u16(0xFF8004) == 4 and mem_o:read_u16(0xFF8008) == 6 then
    local d = mem_o:read_u16(0xFF8100); vu_o[d] = (vu_o[d] or 0) + 1
    local n = vu_o[d] - TOUS_o
    if n >= 0 and n % PAS_o == 0 and n / PAS_o < N_o then
      manager.machine.video:snapshot()
      local t0, t1 = liste(0x700000), liste(0x708000)
      fo:write(string.format("IMAGE %d decor %04x drapeau %02x bases %04x %04x %04x pages %d %d\n", k_o, d, mem_o:read_u8(0xFF7E10),
        mem_o:read_u16(0x804200), mem_o:read_u16(0x804202), mem_o:read_u16(0x804204), #t0, #t1))
      for _, l in ipairs(t0) do fo:write(l .. "\n") end
      for _, l in ipairs(t1) do fo:write(l .. "\n") end
      fo:flush()
    end
  end
end)
-- REC_CUMUL=n : toutes les n images de combat, chaque tuile d'objet de l'emplacement REC_EMPL (defaut 1) jamais vue sur ce
-- decor est ecrite dans REC_OBJ.cumul : « decor code_tuile attr code_objet image » (tuiles des objets multi-tuiles developpees)
local CUM_o = tonumber(os.getenv("REC_CUMUL") or "0"); local EMP_o = tonumber(os.getenv("REC_EMPL") or "1")
if CUM_o > 0 then
  local fc = io.open(os.getenv("REC_OBJ") .. ".cumul", "w"); local vus = {}; local kc = 0
  emu.register_frame_done(function()
    if os.getenv("REC_CUMUL_TOUT") ~= "1" and not (mem_o:read_u16(0xFF8000) == 2 and mem_o:read_u16(0xFF8004) == 4 and mem_o:read_u16(0xFF8008) == 6) then return end
    kc = kc + 1; if kc % CUM_o ~= 0 then return end
    local d = mem_o:read_u16(0xFF8100); local om = BANC_OMBRE or {}
    vus[d] = vus[d] or {}
    for _, page in ipairs({0x700000, 0x708000}) do
      for a = page, page + 0x7ff8, 8 do
        local x, y, c, at = om[a] or 0, om[a + 2] or 0, om[a + 4] or 0, om[a + 6] or 0
        if x == 0x8000 and y == 0x8000 then break end
        if (y >> 13) & 7 == EMP_o and (x ~= 0 or y ~= 0 or c ~= 0) then
          local nx, ny = ((at >> 8) & 15) + 1, ((at >> 12) & 15) + 1
          for j = 0, ny - 1 do for i = 0, nx - 1 do
            local t = (c + i + 16 * j) & 0xffff
            if not vus[d][t] then vus[d][t] = true; fc:write(string.format("%04x %04x %04x %04x %d\n", d, t, at, c, k_o)) end
          end end
        end
      end
    end
    fc:flush()
  end)
end
-- REC_ETAT="a0,a4" (+ REC_ETAT_IM="n,n,...") : capture + liste brute complete aux n-iemes images de l'etat A5+0 = a0, A5+4 = a4
-- (ex. "2,6" : citation du vaincu / CONTINUE), dans REC_OBJ.etat
if os.getenv("REC_ETAT") then
  local a0, a4 = string.match(os.getenv("REC_ETAT"), "(%x+),(%x+)"); a0, a4 = tonumber(a0, 16), tonumber(a4, 16)
  local IMs = {}; for x in string.gmatch(os.getenv("REC_ETAT_IM") or "100", "%d+") do IMs[tonumber(x)] = true end
  local fe = io.open(os.getenv("REC_OBJ") .. ".etat", "w"); local ne = 0
  emu.register_frame_done(function()
    if mem_o:read_u16(0xFF8000) == a0 and mem_o:read_u16(0xFF8004) == a4 then
      ne = ne + 1
      if IMs[ne] then
        manager.machine.video:snapshot()
        local t0, t1 = liste(0x700000), liste(0x708000)
        fe:write(string.format("IMAGE %d etat %d decor %04x bases %04x %04x %04x A5+8 %04x pages %d %d\n", k_o, ne, mem_o:read_u16(0xFF8100),
          mem_o:read_u16(0x804200), mem_o:read_u16(0x804202), mem_o:read_u16(0x804204), mem_o:read_u16(0xFF8008), #t0, #t1))
        for _, l in ipairs(t0) do fe:write("p0 " .. l .. "\n") end
        for _, l in ipairs(t1) do fe:write("p1 " .. l .. "\n") end
        fe:flush()
      end
    end
  end)
end
