-- (banc_coups) ajout au banc (LUA_EN_PLUS) : journal des LECTURES du 68K dans une plage (TRACE_A-TRACE_B, hexa),
-- « L id r decalage pc donnee » (decalage depuis TRACE_A), pendant les essais seulement.
-- Les prises sont reposees a chaque image : un rechargement d'etat (machine:load) peut les retirer.
local sp = manager.machine.devices[":maincpu"].spaces["program"]
local cpu = manager.machine.devices[":maincpu"]
local A, Bn = tonumber(os.getenv("TRACE_A"), 16) & ~1, tonumber(os.getenv("TRACE_B"), 16) | 1
local function pose()
  TRACE_TAP = sp:install_read_tap(A, Bn, "trace_lect", function(off, data, mask)
    TRACE_N = (TRACE_N or 0) + 1
    if BANC_R and BANC_OUT then
      BANC_OUT:write(string.format("L %s %d %x %x %04x\n", BANC_ID, BANC_R, off - A, cpu.state["PC"].value & 0xffffff, data))
    end
  end)
end
pose()
local dernier = nil
emu.register_frame_done(function()
  if BANC_R ~= dernier and BANC_R == 1 then if TRACE_TAP then TRACE_TAP:reinstall() end end
  dernier = BANC_R
end)
