-- (agent_integration_max) coup_contre.lua + relevé de champs (offsets ARCADE, lus en disposition IMAGE : octet -> XOR 1,
-- mot tel quel, long moitiés échangées) : CHAMPS="J1@FF8400:4.b,5.b,...;J2@FF8800:4.b,..." aux images IMAGES=a-b -> JCH
dofile("<workspace>/work/agent_integration_max/lua/coup_contre.lua")
local m = manager.machine.devices[":maincpu"].spaces["program"]
local i0, i1 = os.getenv("IMAGES"):match("(%d+)-(%d+)"); i0, i1 = tonumber(i0), tonumber(i1)
local G = io.open(os.getenv("JCH"), "w"); local n = 0
local OB = {}
for grp in string.gmatch(os.getenv("CHAMPS"), "[^;]+") do
  local nom, base, lst = grp:match("(%w+)@(%x+):(.+)")
  local F = {}
  for c in string.gmatch(lst, "[^,]+") do local o, t = c:match("(%x+)%.(%a)"); F[#F + 1] = {tonumber(o, 16), t} end
  OB[#OB + 1] = {nom, tonumber(base, 16), F}
end
local function lit(a, t)
  if t == "b" then return string.format("%02x", m:read_u8(a ~ 1)) end
  if t == "w" then return string.format("%04x", m:read_u16(a)) end
  return string.format("%04x%04x", m:read_u16(a + 2), m:read_u16(a))
end
emu.register_frame_done(function()
  n = n + 1
  if n < i0 or n > i1 then return end
  local t = {tostring(n)}
  for _, ob in ipairs(OB) do
    t[#t + 1] = ob[1] .. ":"
    for _, f in ipairs(ob[3]) do t[#t + 1] = string.format("%x=%s", f[1], lit(ob[2] + f[1], f[2])) end
  end
  G:write(table.concat(t, " ") .. "\n"); G:flush()
end)
