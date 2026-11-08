-- (e30) enveloppe : charge LUA_BASE ; entre les images QE_F0 et QE_F1, toute écriture de la valeur QE_VAL (mot) dans
-- QE_A0-QE_A1 -> QE_OUT : image, adresse, PC, A0-A6, et les mots suivants de la pile
dofile(os.getenv("LUA_BASE"))
local cq = manager.machine.devices[":maincpu"]; local mq = cq.spaces["program"]
local f0, f1 = tonumber(os.getenv("QE_F0")), tonumber(os.getenv("QE_F1"))
local val = 0
local a0, a1 = tonumber(os.getenv("QE_A0"), 16), tonumber(os.getenv("QE_A1"), 16)
local fq = io.open(os.getenv("QE_OUT"), "w"); local iq = 0; local nq = 0
emu.register_frame_done(function() iq = iq + 1 end)
_G.QETAP = mq:install_write_tap(a0, a1, "qe", function(o, d, m)
  if iq < f0 or iq > f1 or nq > 4000 then return end
  local v = d
  if m == 0xffff0000 or (m & 0xffff0000) ~= 0 and (m & 0xffff) == 0 then v = d >> 16 end
  local ok = false; for w in string.gmatch(os.getenv("QE_VAL"), "%x+") do local t = tonumber(w, 16); if (v & 0xffff) == t or (d & 0xffff) == t then ok = true end end
  if not ok then return end
  nq = nq + 1
  local s = {}
  for _, r in ipairs({"A0","A1","A2","A3","A4","A5","A6","D0","D1","D2","D3"}) do s[#s+1] = r .. "=" .. string.format("%x", cq.state[r].value) end
  local sp = cq.state["A7"].value; local p = {}
  for i = 0, 15 do p[#p+1] = string.format("%04x", mq:read_u16(sp + 2*i)) end
  fq:write(string.format("%d %06x d=%x m=%x PC=%06x %s pile %s\n", iq, o, d, m, cq.state["PC"].value, table.concat(s, " "), table.concat(p, " ")))
  fq:flush()
end)
