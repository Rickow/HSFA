-- (frame_data_max) LUA_EN_PLUS du banc des coups : quand EXCMARK ($6638F0) désigne un talon d'exception ($A00-$A7F), écrit une fois par essai
-- « E id r em=talon pc a7 pile[0..31] regs » (cadre 68000 sous a7 : erreur d'adresse = mot fonction, adresse fautive, IR, SR, PC).
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local vu = {}
emu.register_frame_done(function()
  local id = _G.BANC_ID
  if not id or vu[id] then return end
  local em = mem:read_u32(0x6638F0)
  if em < 0xA00 or em >= 0xA80 then return end
  vu[id] = true
  local st = cpu.state
  local a7 = (st["SP"] or st["A7"] or st["SSP"]).value & 0xffffff
  local p = {}
  for i = 0, 31, 2 do p[#p + 1] = string.format("%04x", mem:read_u16(a7 + i)) end
  local r = {}
  for _, n in ipairs({"D0","D1","D2","D3","D4","D5","D6","D7","A0","A1","A2","A3","A4","A5","A6"}) do r[#r + 1] = n .. "=" .. string.format("%x", st[n].value) end
  local q = {}
  for a = 0xA00, 0xA2E, 2 do q[#q + 1] = string.format("%04x", mem:read_u16(a)) end
  local pcf = (mem:read_u16(a7 + 10) << 16) | mem:read_u16(a7 + 12)
  local c = {}
  for a = (pcf & 0xfffffe) - 0x30, (pcf & 0xfffffe) + 0x8, 2 do c[#c + 1] = string.format("%04x", mem:read_u16(a)) end
  _G.BANC_OUT:write(string.format("C %s pcf=%x code[pcf-0x30..]=%s\n", id, pcf, table.concat(c, " ")))
  _G.BANC_OUT:write(string.format("E %s %s em=%x pc=%x a7=%x pile=%s %s talons=%s\n", id, tostring(_G.BANC_R), em, st["PC"].value, a7, table.concat(p, " "), table.concat(r, " "), table.concat(q, "")))
end)
