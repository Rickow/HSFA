-- (e25) enveloppe : charge LUA_BASE_S ; journal des ECRITURES QUI CHANGENT la memoire dans SURVC="adr:long:image0"
-- (image, PC, adresse, ancienne -> nouvelle valeur, A6) -> SURVC_OUT ; SURVC_N (defaut 400) lignes au plus
dofile(os.getenv("LUA_BASE_S"))
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]
local a, l, f0 = string.match(os.getenv("SURVC"), "(%x+):(%x+):(%d+)")
a = tonumber(a, 16); l = tonumber(l, 16); f0 = tonumber(f0)
local fs = io.open(os.getenv("SURVC_OUT"), "w"); local ns, nmax, im = 0, tonumber(os.getenv("SURVC_N") or "400"), 0
emu.register_frame_done(function() im = im + 1 end)
_G.SURVC_TAP = ms:install_write_tap(a, a + l - 1, "survc", function(o, d, m)
  if im < f0 or ns >= nmax then return end
  local old = ms:read_u16(o & ~1)
  if (old & m) ~= (d & m) then
    ns = ns + 1
    local pl = ""
    if os.getenv("SURVC_PILE") == "1" then
      local sp = cs.state["SP"].value & 0xffffff; local t = {}
      for i = 0, 11 do t[#t + 1] = string.format("%08x", ms:read_u32(sp + 4 * i)) end
      pl = " pile " .. table.concat(t, " ") .. string.format(" D0=%08x D1=%08x", cs.state["D0"].value, cs.state["D1"].value)
    end
    fs:write(string.format("img %d pc=%06x %06x %04x -> %04x m=%04x A6=%06x%s\n", im, cs.state["PC"].value & 0xffffff, o, old, d, m,
      cs.state["A6"].value & 0xffffff, pl)); fs:flush()
  end
end)
