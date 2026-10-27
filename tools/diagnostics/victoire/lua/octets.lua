-- journal par image (changements) d'une liste d'octets (adresses brutes, sans XOR) : OCT="ff814a,ff814b,..." fenetre W0-W1
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local fo = io.open(os.getenv("SOUT"), "w")
local W0, W1 = tonumber(os.getenv("W0")), tonumber(os.getenv("W1"))
local L = {}
for a in string.gmatch(os.getenv("OCT"), "%x+") do L[#L + 1] = tonumber(a, 16) end
local kk, prev = 0, ""
local hdr = {}; for _, a in ipairs(L) do hdr[#hdr + 1] = string.format("%06x", a) end
fo:write("# " .. table.concat(hdr, " ") .. "\n")
emu.register_frame_done(function()
  kk = kk + 1
  if kk < W0 or kk > W1 then return end
  local t = {}
  for _, a in ipairs(L) do t[#t + 1] = string.format("%02x", mem:read_u8(a)) end
  local s = table.concat(t, " ")
  if s ~= prev then fo:write(kk .. " " .. s .. "\n"); fo:flush(); prev = s end
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
