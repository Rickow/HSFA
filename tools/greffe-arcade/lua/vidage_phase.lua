-- (31/10) enveloppe : charge VP_SUITE ; a chaque ENTREE dans la phase de combat A5+8 = 6, A5+C = VP_C (hexa), vide
-- VP_MEM ("ff8000:400,...") -> VP_OUT (au plus VP_N fois)
dofile(os.getenv("VP_SUITE"))
local m = manager.machine.devices[":maincpu"].spaces["program"]; local n, k, prev = 0, 0, -1
local c = tonumber(os.getenv("VP_C") or "a", 16); local nmax = tonumber(os.getenv("VP_N") or "2")
local f = io.open(os.getenv("VP_OUT"), "w")
emu.register_frame_done(function()
  n = n + 1
  local pc = m:read_u16(0xFF800C)
  if m:read_u16(0xFF8008) == 6 and pc == c and prev ~= c and k < nmax then
    k = k + 1
    for a, l in string.gmatch(os.getenv("VP_MEM"), "(%x+):(%x+)") do
      local a0 = tonumber(a, 16); local w = {}
      for i = 0, tonumber(l, 16) - 1, 2 do w[#w + 1] = string.format("%04x", m:read_u16(a0 + i)) end
      f:write(string.format("img %d %06x : %s\n", n, a0, table.concat(w, " ")))
    end
    f:flush()
  end
  prev = pc
end)
