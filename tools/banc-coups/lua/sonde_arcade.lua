-- (banc_coups) SONDE des arcades SFA1 / SFA2 / Alpha 2 Gold (mode A) : pieces, Start J1 puis J2, bouton 1 des deux
-- joueurs en boucle ; journal toutes les 30 images : mots A5+$0..$10, A5+$A8, octets $0-$7 et quelques champs des
-- structures $FF8400 / $FF8800, et vidage brut de la RAM aux images listees (DUMPS="k1,k2", fichiers OUT.k.ram).
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local ports = manager.machine.ioport.ports
local out = io.open(os.getenv("OUT"), "w")
local champs = {}
for _, p in pairs(ports) do for fn, f in pairs(p.fields) do champs[fn] = f end end
local NF = tonumber(os.getenv("NF") or "6000")
local D = {}
for x in string.gmatch(os.getenv("DUMPS") or "", "%d+") do D[tonumber(x)] = true end
local k = 0
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  if k >= 600 and k < 900 and k % 60 < 8 then v["Coin 1"] = 1; v["Coin 2"] = 1 end
  if k >= 1000 and k < 1400 and k % 40 < 6 then v["1 Player Start"] = 1 end
  if k >= 1020 and k < 1400 and k % 40 >= 20 and k % 40 < 26 then v["2 Players Start"] = 1 end
  if k >= 1400 and k % 24 < 4 then v["P1 Button 1"] = 1; v["P2 Button 1"] = 1 end
  if k % 30 == 0 then
    local t = {}
    for a = 0xFF8000, 0xFF8010, 2 do t[#t + 1] = string.format("%04x", mem:read_u16(a)) end
    local j = {}
    for _, b in ipairs({0xFF8400, 0xFF8800}) do
      local s = {}
      for a = b, b + 7 do s[#s + 1] = string.format("%02x", mem:read_u8(a)) end
      j[#j + 1] = table.concat(s) .. string.format(" x=%04x y=%04x v=%04x 102=%02x%02x", mem:read_u16(b + 0x10),
        mem:read_u16(b + 0x14), mem:read_u16(b + 0x50), mem:read_u8(b + 0x102), mem:read_u8(b + 0x103))
    end
    out:write(string.format("%6d %s a8=%04x | %s | %s\n", k, table.concat(t, " "), mem:read_u16(0xFF80A8), j[1], j[2]))
  end
  if D[k] then
    local f = io.open(os.getenv("OUT") .. "." .. k .. ".ram", "wb"); local t = {}
    for a = 0xFF0000, 0xFFFFFE, 2 do t[#t + 1] = string.pack(">I2", mem:read_u16(a)) end
    f:write(table.concat(t)); f:close()
  end
  for fn, f in pairs(champs) do
    if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "Coin 2" or fn == "1 Player Start" or fn == "2 Players Start" then
      f:set_value(v[fn] or 0)
    end
  end
  if k >= NF then out:close(); manager.machine:exit() end
end)
