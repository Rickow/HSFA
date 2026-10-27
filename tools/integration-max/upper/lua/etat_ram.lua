-- (agent_integration_max) recharge ETAT, puis toutes les PAS images écrit (TRACE) quelques champs des joueurs (RAM brute)
local n, NTR, PAS = 0, tonumber(os.getenv("NTR") or "300"), tonumber(os.getenv("PAS") or "20")
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local f = io.open(os.getenv("TRACE"), "w")
emu.register_frame_done(function()
  n = n + 1
  if n == 2 then manager.machine:load(os.getenv("ETAT")) end
  if n > 3 and n % PAS == 0 then
    local t = {}
    for _, j in ipairs({0xFF8400, 0xFF8800}) do
      t[#t + 1] = string.format("[%06x $4=%04x $6=%04x perso=%02x $1C=%04x%04x $32=%02x $3E0=%04x $3E2=%04x]", j, mem:read_u16(j + 4),
        mem:read_u16(j + 6), mem:read_u8(j + 0x103), mem:read_u16(j + 0x1e), mem:read_u16(j + 0x1c), mem:read_u8(j + 0x33),
        mem:read_u16(j + 0x3e0), mem:read_u16(j + 0x3e2))
    end
    f:write(string.format("%d A5+10=%04x 12D=%02x %s\n", n, mem:read_u16(0xFF8010), mem:read_u8(0xFF812C), table.concat(t, " ")))
  end
  if n == 4 + NTR then f:close(); manager.machine:exit() end
end)
dofile("<workspace>/work/mame/banc_mem.lua"); dofile("<workspace>/work/mame/banc_plans.lua")
