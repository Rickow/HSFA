-- journal par image (changements) des 7 emplacements d'objets d'ecran $FF5000 + $200*i (mots 0..$1F), fenetre W0-W1
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("SOUT"), "w")
local W0, W1 = tonumber(os.getenv("W0")), tonumber(os.getenv("W1"))
local B, NS, NW = tonumber(os.getenv("SB") or "FF5000", 16), tonumber(os.getenv("NS") or "7"), tonumber(os.getenv("NW") or "16")
local kk, prev = 0, {}
emu.register_frame_done(function()
  kk = kk + 1
  if kk < W0 or kk > W1 then return end
  for i = 0, NS - 1 do
    local t = {}
    for a = 0, NW - 1 do t[#t + 1] = string.format("%04x", mem:read_u16(B + 0x200 * i + 2 * a)) end
    local s = table.concat(t, " ")
    if s ~= prev[i] then fo:write(string.format("%d s%d %s\n", kk, i, s)); prev[i] = s end
  end
  fo:flush()
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
