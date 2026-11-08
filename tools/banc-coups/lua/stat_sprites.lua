-- (banc_coups) ajout au banc (LUA_EN_PLUS, avec SPRITES=1) : pour l'essai STATID, a chaque image, objets de la liste
-- du portage RETIRES par banc_sprites.lua (emplacement sans banque ou code hors table), regroupes :
-- « S id r emplacement code attributs x y nombre_de_tuiles ».
_G.RETSTAT = {}
emu.register_frame_done(function()
  if _G.BANC_ID == os.getenv("STATID") and _G.BANC_R and _G.BANC_OUT then
    for c, n in pairs(_G.RETSTAT) do _G.BANC_OUT:write(string.format("S %s %d %s n=%d\n", _G.BANC_ID, _G.BANC_R, c, n)) end
  end
  _G.RETSTAT = {}
end)
