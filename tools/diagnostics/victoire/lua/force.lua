-- a partir de l'image F0 : ecrit a chaque image les octets FOCT="adr=val,..." (adresses brutes) ; puis BASE_LUA
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local F0 = tonumber(os.getenv("F0") or "0")
local L = {}
for a, v in string.gmatch(os.getenv("FOCT") or "", "(%x+)=(%x+)") do L[#L + 1] = {tonumber(a, 16), tonumber(v, 16)} end
local kk = 0
emu.register_frame_done(function()
  kk = kk + 1
  if kk >= F0 then for _, e in ipairs(L) do mem:write_u8(e[1], e[2]) end end
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
