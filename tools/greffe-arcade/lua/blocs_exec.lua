-- (31/10) enveloppe : charge LUA_BASE ; entre les images BX_F0 et BX_F1, ensemble des debuts de blocs executes
-- (lecture d'opcode non consecutive) dans [BX_LO, BX_HI) -> BX_OUT (adresse 68K et nombre)
dofile(os.getenv("LUA_BASE"))
local cp = manager.machine.devices[":maincpu"]; local op = cp.spaces["opcodes"] or cp.spaces["program"]
local f0, f1 = tonumber(os.getenv("BX_F0")), tonumber(os.getenv("BX_F1"))
local lo, hi = tonumber(os.getenv("BX_LO") or "1000", 16), tonumber(os.getenv("BX_HI") or "c0000", 16)
local n, last, cnt, tap = 0, -10, {}, nil
emu.register_frame_done(function()
  n = n + 1
  if n == f0 then
    tap = op:install_read_tap(lo, hi - 1, "blocs_exec", function(o, d, m)
      if o ~= last + 2 and o ~= last then cnt[o] = (cnt[o] or 0) + 1 end
      last = o
    end)
  elseif n == f1 and tap then
    tap:remove(); tap = nil
    local f = io.open(os.getenv("BX_OUT"), "w"); local k = {}
    for a in pairs(cnt) do k[#k + 1] = a end; table.sort(k)
    for _, a in ipairs(k) do f:write(string.format("%06x %d\n", a, cnt[a])) end
    f:close()
  end
end)
