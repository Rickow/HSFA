-- (e27) enveloppe : graine_pc.lua (donc LUA_BASE) + prise d'ecriture sur les champs +$1C/+$1E (pointeur d'animation)
-- des objets de [SURVO_LO, SURVO_HI) (pas de $80), a partir de l'image SURVO_F0 et pendant la scene A5+4 = SURVO_SCENE
-- (defaut A) ; journal SURVO_OUT : image, PC, adresse, donnee, classe (+2), registres A0/D0.
dofile("<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local cs = manager.machine.devices[":maincpu"]; local ms = cs.spaces["program"]
local lo = tonumber(os.getenv("SURVO_LO") or "FFB000", 16); local hi = tonumber(os.getenv("SURVO_HI") or "FFC000", 16)
local f0 = tonumber(os.getenv("SURVO_F0") or "0"); local sc = tonumber(os.getenv("SURVO_SCENE") or "A", 16)
local fo = io.open(os.getenv("SURVO_OUT"), "w"); local ks = 0; local nmax = tonumber(os.getenv("SURVO_N") or "400"); local n = 0
emu.register_frame_done(function() ks = ks + 1 end)
_G.SOTAP = ms:install_write_tap(lo, hi - 1, "survobj", function(o, d, m)
  local r = o & 0x7F
  if (r == 0x1C or r == 0x1E) and ks >= f0 and n < nmax and ms:read_u16(0xFF8004) == sc then
    n = n + 1
    local b = o - r
    fo:write(string.format("%d pc=%06x %06x %04x %04x classe %04x A0=%08x D0=%08x\n", ks, cs.state["PC"].value & 0xffffff, o, d, m,
      ms:read_u16(b + 2), cs.state["A0"].value, cs.state["D0"].value)); fo:flush()
  end
end)
