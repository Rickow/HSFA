-- (31/10, e22) variante : OM_FS="n,n,..." (plusieurs images, ajoutees au meme fichier, ligne "img n")
-- (28/10) sonde : a l'image OM_F, liste BRUTE du jeu (BANC_OMBRE de banc_sprites) des pages $700000 et $708000 :
-- emplacement (Y bits 13-15), code local, attributs, jusqu'au marqueur de fin -> OM_OUT. Script normal : SL_SUITE.
dofile(os.getenv("SL_SUITE"))
local FS, n = {}, 0
for x in string.gmatch(os.getenv("OM_FS") or "", "%d+") do FS[tonumber(x)] = true end
local f = io.open(os.getenv("OM_OUT"), "w")
emu.register_frame_done(function()
  n = n + 1
  if not FS[n] then return end
  f:write(string.format("img %d\n", n)); local o = BANC_OMBRE or {}
  for _, page in ipairs({0x700000, 0x708000}) do
    local h = {}
    for a = page, page + 0x1ff8, 8 do
      local x, y, c, at = o[a] or 0, o[a + 2] or 0, o[a + 4] or 0, o[a + 6] or 0
      if x == 0x8000 and y == 0x8000 and os.getenv("OM_TOUT") ~= "1" then break end
      local e = (y >> 13) & 7; h[e] = (h[e] or 0) + 1
      f:write(string.format("%06x e%d x=%03x y=%03x c=%04x at=%04x\n", a, e, x & 0x3ff, y & 0x3ff, c, at))
    end
    local s = {}; for e = 0, 7 do if h[e] then s[#s + 1] = string.format("e%d:%d", e, h[e]) end end
    f:write(string.format("page %06x %s\n", page, table.concat(s, " ")))
  end
  f:flush()
end)
