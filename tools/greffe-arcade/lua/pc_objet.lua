-- (28/10) enveloppe : charge LUA_BASE ; entre les images PCO_F0 et PCO_F1, compte les debuts de blocs d'instructions
-- (lecture d'opcode non consecutive) executes quand A6 = PCO_A6 -> PCO_OUT (adresse, nombre), par adresse
dofile(os.getenv("LUA_BASE"))
local cp = manager.machine.devices[":maincpu"]; local op = cp.spaces["opcodes"] or cp.spaces["program"]
local f0, f1 = tonumber(os.getenv("PCO_F0")), tonumber(os.getenv("PCO_F1")); local a6 = tonumber(os.getenv("PCO_A6"), 16)
local ip, last, cnt = 0, -10, {}
emu.register_frame_done(function()
  ip = ip + 1
  if ip == f1 then
    local fo = io.open(os.getenv("PCO_OUT"), "w"); local ks = {}
    for a, n in pairs(cnt) do ks[#ks + 1] = a end
    table.sort(ks); for _, a in ipairs(ks) do fo:write(string.format("%06x %d\n", a, cnt[a])) end
    fo:close()
  end
end)
_G.PCOTAP = op:install_read_tap(0x0, 0x3fffff, "pco", function(o, d, m)
  if ip >= f0 and ip < f1 and (o < last or o > last + 10) and (cp.state["A6"].value & 0xffffff) == a6 then cnt[o] = (cnt[o] or 0) + 1 end
  last = o
end)
