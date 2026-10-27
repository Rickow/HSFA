-- (etape 2) enveloppe : charge LUA_BASE, puis impose la graine du hasard $FF80AE = GRAINE a CHAQUE entree dans la routine
-- dont l'adresse 68K est GRAINE_PC (prise sur l'espace opcodes) : la liste des adversaires (0x24F9D0) est alors construite
-- avec la meme graine dans Upper et dans ro9a (oracle). Journal : GRAINE_OUT (image de chaque declenchement).
dofile(os.getenv("LUA_BASE_G") or os.getenv("LUA_BASE"))
local cg = manager.machine.devices[":maincpu"]; local mg = cg.spaces["program"]
local og = cg.spaces["opcodes"] or mg
local pcg = tonumber(os.getenv("GRAINE_PC"), 16); local gr = os.getenv("GRAINE") and tonumber(os.getenv("GRAINE"), 16)
local fg = io.open(os.getenv("GRAINE_OUT"), "w")
local ng = 0
_G.GTAP = og:install_read_tap(pcg, pcg + 1, "graine", function(o, d, m)
  if ng == 0 and os.getenv("DUMP_ADR") then
    local t = {}
    for a in string.gmatch(os.getenv("DUMP_ADR"), "%x+") do
      local x = tonumber(a, 16); t[#t + 1] = string.format("%06x=%02x", x, mg:read_u8(x))
    end
    fg:write("etat " .. table.concat(t, " ") .. "\n")
  end
  if gr then mg:write_u16(0xFF80AE, gr) end
  if ng == 0 and os.getenv("FORCE_ADR") then                  -- FORCE_ADR="ff8120=32,ff8123=82" (octets 68K)
    for a, v in string.gmatch(os.getenv("FORCE_ADR"), "(%x+)=(%x+)") do mg:write_u8(tonumber(a, 16), tonumber(v, 16)) end
  end
  ng = ng + 1; fg:write(string.format("graine %d\n", ng)); fg:flush()
end)
