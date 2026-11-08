-- obj.lua (sfa = SFA1 arcade, oracle local ; agent decors_restes, 07/11) : POSITIONS des sprites de decor au pixel.
-- Decor force (STG = $FFAE00 hexa), partie 1 joueur, puis selon MODE :
--   MODE=balai  (defaut) : vies maintenues, centre des joueurs c balaye $1C0 -> $040 -> $540 -> $1C0 (4 px/image) :
--                la camera parcourt toute sa course (deux bouts + milieu) ;
--   MODE=combat : VRAI combat (rien n'est force sauf : vie de J1 maintenue ; a l'image KKO (defaut 2800) les joueurs
--                sont rapproches et la vie de J2 mise a 1 ; J1 frappe (bouton 1 toutes les 8 images) -> K.O. ->
--                fin de manche ($2E07) -> creation des objets $1F de Charlie (liste $41CC0).
-- Journal OUT_pos.txt, images K0..K1-1 :
--   f k cam2x cam2y cam3x cam3y cam1x cam1y e07 e1c  plans ($FF8200/$FF8280/$FF8300 : +$10/+$14) et drapeaux $2E07/$2E1C
--   a k slot classe sous etat cadre($20) X($10) Y($14) b9 bb bc bd bf d0   objets actifs du pool 1 ($FF9400)
--        d0 vx($30) vy($34) attente($2C) $A anim($26) duree($24)
--        (d0 = correction de $1225A pour le plan 8 quand $F(A6) != 0, calculee comme le jeu)
--   s k banque i x y code attr   entrees OBJ de palette >= 24 de la banque ecrite pendant l'image
--   d k fente classe sous cadre X Y b9 bb bc bd bf d0 cam1x cam1y cam2x cam2y cam3x cam3y banque x,y,code,attr;… : CHAQUE
--        dessin d'un objet de decor ($11FE6 / $1208C) : etat de l'objet et des plans a la 1re entree, D4 du jeu (ancre
--        Y0 << 16 | X0 calculee par $1225A), puis les entrees OBJ reellement ecrites (derniere valeur ecrite a chaque
--        adresse dans l'image ; prefixe X si un dessin posterieur de l'image a recouvert ces adresses) ; ATTENTION : les lignes
--        d et w portent le n de la derniere image FINIE : leur OBJ est celui des lignes s de l'image k + 1
--   w k pc a6 classe code attr   ecrivain (PC, A6 et classe de l'objet A6) des mots d'attribut de palette 24-31 ecrits
--                                 dans l'OBJ : une ligne par (pc, code, palette), la 1re fois qu'il est vu
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local O = {[0] = manager.machine.memory.shares[":objram1"], [1] = manager.machine.memory.shares[":objram2"]}
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "00", 16)
local OUT = os.getenv("OUT")
local MODE = os.getenv("MODE") or "balai"
local K0, K1 = tonumber(os.getenv("K0") or "2600"), tonumber(os.getenv("K1") or "4000")
local KKO = tonumber(os.getenv("KKO") or "2800")
local k = 0
TAP_STG = mem:install_write_tap(0xFFAE00, 0xFFAE01, "stg", function(o, d, m)
  if k < 700 then return end
  if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
end)
local ecrit = {[0] = 0, [1] = 0}; local vus = {}; local dessins = {}; local cur = {}; local ombre = {}; local proprio = {}
local f = io.open(OUT .. "_pos.txt", "w")
TAP_OBJ = mem:install_write_tap(0x700000, 0x70ffff, "obj", function(o, d, m)
  if k < K0 or k >= K1 then return end
  local b = (o >= 0x708000) and 1 or 0
  ecrit[b] = ecrit[b] + 1
  ombre[o] = d
  if (o & 7) == 6 and (d & 0x1f) >= 24 then
    local pc = cpu.state["PC"].value; local a6 = cpu.state["A6"].value & 0xffffff
    if (pc == 0x11fe6 or pc == 0x1208c) and a6 >= 0xff9400 and a6 < 0xffa400 then
      -- dessin d'un objet de decor ($11F5E type 0 / $11FEE type 2) : etat de l'objet et des plans A CET INSTANT
      local d0 = 0
      if mem:read_u8(a6 + 9) == 8 and mem:read_u8(a6 + 0xf) ~= 0 then
        local d1 = mem:read_u8(a6 + 0xf); if d1 >= 0x80 then d1 = d1 - 0x100 end
        local base = mem:read_u32(0xFF8380); local i = (mem:read_u16(0xFF8398) - 2 * d1) & 0xffff
        local v = mem:read_u16(base + ((i >= 0x8000) and (i - 0x10000) or i)); if v >= 0x8000 then v = v - 0x10000 end
        d0 = v - 0xC0
      end
      local c = cur[a6]
      if c and c.o + 8 == o and c.pc == pc then c.o = o; c.e[#c.e + 1] = o
      else
        c = {o = o, pc = pc, e = {o}, n = #dessins + 1}; cur[a6] = c; dessins[#dessins + 1] = c
        c.t = string.format("d %d %d %02x %02x %08x %04x %04x %02x %02x %02x %02x %02x %d %04x %04x %04x %04x %04x %04x %d",
        k, (a6 - 0xFF9400) // 0x80, mem:read_u8(a6 + 2), mem:read_u8(a6 + 3), mem:read_u32(a6 + 0x20), mem:read_u16(a6 + 0x10),
        mem:read_u16(a6 + 0x14), mem:read_u8(a6 + 9), mem:read_u8(a6 + 0xb), mem:read_u8(a6 + 0xc), mem:read_u8(a6 + 0xd),
        mem:read_u8(a6 + 0xf), d0, mem:read_u16(0xFF8210), mem:read_u16(0xFF8214), mem:read_u16(0xFF8290), mem:read_u16(0xFF8294),
        mem:read_u16(0xFF8310), mem:read_u16(0xFF8314), b) .. string.format(" %08x", cpu.state["D4"].value & 0xffffffff)
      end
      proprio[o] = c.n
    end
    local code = O[b]:read_u16((o & 0x1fff) - 2)
    local cle = string.format("%x %x %x", pc, code, d & 0x1f)
    if not vus[cle] then
      vus[cle] = true
      local cl = (a6 >= 0xff0000) and mem:read_u8(a6 + 2) or 0
      f:write(string.format("w %d %06x %06x %02x %04x %04x\n", k, pc, a6, cl, code, d))
    end
  end
end)
local function set(p, fl, v) local x = ports[p].fields[fl]; if x then x:set_value(v) end end
local PATH = {{0x1C0, 20}, {0x040, 40}, {0x540, 40}, {0x1C0, 40}}
local seg, c, hold = 1, 0x1C0, 0
local function s16(v) if v >= 0x8000 then return v - 0x10000 end return v end
emu.register_frame_done(function()
  k = k + 1
  set(":IN2", "Coin 1", ((k >= 600 and k < 606) or (k >= 640 and k < 646)) and 1 or 0)
  set(":IN2", "1 Player Start", (k >= 760 and k < 766) and 1 or 0)
  local b1 = (k >= 900 and k < 2300 and k % 30 < 3)
  if MODE == "combat" and k >= KKO then b1 = (k % 8 < 2) end
  set(":IN0", "P1 Button 1", b1 and 1 or 0)
  if MODE == "balai" and k >= 2600 then
    for _, j in ipairs({0xFF8400, 0xFF8800}) do mem:write_u16(j + 0x40, 0x90); mem:write_u16(j + 0x42, 0x90) end
    if k >= K0 then
      local cible, duree = PATH[seg][1], PATH[seg][2]
      if c < cible then c = math.min(cible, c + 4) elseif c > cible then c = math.max(cible, c - 4) end
      if c == cible then hold = hold + 1 end
      if hold >= duree and seg < #PATH then seg = seg + 1; hold = 0 end
    end
    mem:write_u16(0xFF8410, c - 96); mem:write_u16(0xFF8810, c + 96)
  elseif MODE == "combat" and k >= 2600 then
    mem:write_u16(0xFF8440, 0x90); mem:write_u16(0xFF8442, 0x90)
    if k == KKO then
      local x2 = mem:read_u16(0xFF8810); mem:write_u16(0xFF8410, x2 - 48)
      mem:write_u16(0xFF8840, 1); mem:write_u16(0xFF8842, 1)
    end
  end
  if k >= K0 and k < K1 then
    f:write(string.format("f %d %04x %04x %04x %04x %04x %04x %02x %02x\n", k, mem:read_u16(0xFF8290), mem:read_u16(0xFF8294),
      mem:read_u16(0xFF8310), mem:read_u16(0xFF8314), mem:read_u16(0xFF8210), mem:read_u16(0xFF8214),
      mem:read_u8(0xFFAE07), mem:read_u8(0xFFAE1C)))
    for s = 0, 31 do
      local a = 0xFF9400 + 0x80 * s
      if mem:read_u8(a) ~= 0 then
        local d0 = 0
        if mem:read_u8(a + 9) == 8 and mem:read_u8(a + 0xf) ~= 0 then
          local d1 = mem:read_u8(a + 0xf); if d1 >= 0x80 then d1 = d1 - 0x100 end
          local base = mem:read_u32(0xFF8380); local i = (mem:read_u16(0xFF8398) - 2 * d1) & 0xffff
          d0 = s16(mem:read_u16(base + s16(i))) - 0xC0
        end
        f:write(string.format("a %d %d %02x %02x %02x %08x %04x %04x %02x %02x %02x %02x %02x %d %08x %08x %04x %02x %04x %04x\n", k, s,
          mem:read_u8(a + 2), mem:read_u8(a + 3), mem:read_u8(a + 4), mem:read_u32(a + 0x20), mem:read_u16(a + 0x10),
          mem:read_u16(a + 0x14), mem:read_u8(a + 9), mem:read_u8(a + 0xb), mem:read_u8(a + 0xc), mem:read_u8(a + 0xd),
          mem:read_u8(a + 0xf), d0, mem:read_u32(a + 0x30), mem:read_u32(a + 0x34), mem:read_u16(a + 0x2c), mem:read_u8(a + 0xa),
          mem:read_u16(a + 0x26), mem:read_u16(a + 0x24)))
      end
    end
    -- entrees : DERNIERE valeur ecrite a chaque adresse pendant l'image (ombre des ecritures, independante de l'ordre
    -- des cycles de movem) ; dessin recouvert ensuite par un autre dessin de l'image : marque « X »
    for _, c in ipairs(dessins) do
      local t = {}; local ok = true
      for _, o in ipairs(c.e) do
        if proprio[o] ~= c.n then ok = false end
        t[#t + 1] = string.format("%04x,%04x,%04x,%04x", ombre[o - 6] or 0xffff, ombre[o - 4] or 0xffff, ombre[o - 2] or 0xffff, ombre[o] or 0xffff)
      end
      f:write(c.t .. " " .. (ok and "" or "X") .. table.concat(t, ";") .. "\n")
    end
    for b = 0, 1 do
      if ecrit[b] > 0 then
        for i = 0, 0x1ff8, 8 do
          local x, y, code, at = O[b]:read_u16(i), O[b]:read_u16(i + 2), O[b]:read_u16(i + 4), O[b]:read_u16(i + 6)
          if at == 0xff00 or y >= 0x8000 then break end
          if (at & 0x1f) >= 24 then f:write(string.format("s %d %d %d %04x %04x %04x %04x\n", k, b, i // 8, x, y, code, at)) end
        end
      end
    end
  end
  ecrit[0], ecrit[1] = 0, 0; dessins = {}; cur = {}; ombre = {}; proprio = {}
  if k == K1 then f:close(); manager.machine:exit() end
end)
