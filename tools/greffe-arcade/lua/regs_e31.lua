-- (e31) enveloppe : LUA_BASE (graine_pc.lua) + par image de REG_F0 a REG_F1 : mots 68K de REG_ADR (liste hexa) -> REG_OUT
dofile(os.getenv("LUA_BASE"))
local ms = manager.machine.devices[":maincpu"].spaces["program"]
local f0, f1 = tonumber(os.getenv("REG_F0")), tonumber(os.getenv("REG_F1")); local im = 0
local A = {}; for x in string.gmatch(os.getenv("REG_ADR"), "%x+") do A[#A + 1] = tonumber(x, 16) end
local fo = io.open(os.getenv("REG_OUT"), "w")
emu.register_frame_done(function()
  im = im + 1
  if im < f0 or im > f1 then return end
  local t = {}; for _, a in ipairs(A) do t[#t + 1] = string.format("%04x", ms:read_u16(a)) end
  fo:write(im .. " " .. table.concat(t, " ") .. "\n"); fo:flush()
end)
