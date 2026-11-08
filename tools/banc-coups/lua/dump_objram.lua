-- (banc_coups) ajout au banc (LUA_EN_PLUS) : vidage brut des deux memoires d'objets CPS2 (:objram1, :objram2) a
-- l'image STATR de l'essai STATID -> OUT.objram1 / OUT.objram2 (mots gros-boutistes) ; et, si banc_sprites est charge,
-- la liste BRUTE du portage (BANC_OMBRE) -> OUT.ombre (« adresse mot » par ligne).
emu.register_frame_done(function()
  if _G.BANC_ID == os.getenv("STATID") and _G.BANC_R == tonumber(os.getenv("STATR") or "30") then
    for _, n in ipairs({"objram1", "objram2"}) do
      local s = manager.machine.memory.shares[":" .. n]
      local f = io.open(os.getenv("OUT") .. "." .. n, "wb"); local t = {}
      for a = 0, s.size - 2, 2 do t[#t + 1] = string.pack(">I2", s:read_u16(a)) end
      f:write(table.concat(t)); f:close()
    end
    if _G.BANC_OMBRE then
      local f = io.open(os.getenv("OUT") .. ".ombre", "w")
      for a, v in pairs(_G.BANC_OMBRE) do f:write(string.format("%06x %04x\n", a, v)) end
      f:close()
    end
    local f = io.open(os.getenv("OUT") .. ".ram", "wb"); local t = {}
    local sp = manager.machine.devices[":maincpu"].spaces["program"]
    for a = 0xFF0000, 0xFFFFFE, 2 do t[#t + 1] = string.pack(">I2", sp:read_u16(a)) end
    f:write(table.concat(t)); f:close()
  end
end)
