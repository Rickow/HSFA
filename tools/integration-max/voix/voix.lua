-- Injection de commandes son au Z80 (programme 68K muet : build ro5 sans boite aux lettres, comme inj2.lua de l'agent
-- ro5) ; par commande : toutes les ecritures de registres QSound (temps emule en s, registre, valeur) et WAV de la
-- session a partir de DEBUT (start_recording). Env : CODES (liste hex), DEBUT (image), PAS (images par commande),
-- OUT (journal), WAV (fichier, facultatif), P7 (octet $61800F, defaut 0).
dofile("<workspace>/work/mame/banc_mem.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local zm = manager.machine.devices[":audiocpu"].spaces["program"]
local log = io.open(os.getenv("OUT"), "w")
-- CODES : « code » ou « code:images » (duree propre a la commande, sinon PAS)
local codes, durees = {}, {}
for c, d in string.gmatch(os.getenv("CODES") or "0a61", "(%x+):?(%d*)") do
  codes[#codes + 1] = tonumber(c, 16); durees[#durees + 1] = tonumber(d)
end
local DEBUT, PAS = tonumber(os.getenv("DEBUT") or "1100"), tonumber(os.getenv("PAS") or "240")
local P7 = tonumber(os.getenv("P7") or "0", 16)
local frames, t0, k, ph0 = 0, nil, nil, 0
local qhi, qlo = 0, 0
local function t() return manager.machine.time:as_double() end
QT = zm:install_write_tap(0xd000, 0xd002, "qs", function(offset, data, mask)
  if offset == 0xd000 then qhi = data & 0xff elseif offset == 0xd001 then qlo = data & 0xff
  elseif t0 then log:write(string.format("Q %.6f %02x %04x\n", t() - t0, data & 0xff, (qhi << 8) | qlo)) end
end)
local function envoie(hi, lo)
  local v = {[0x618001]=hi, [0x618003]=lo, [0x618005]=0, [0x618007]=0, [0x618009]=0, [0x61800d]=0, [0x61800f]=P7,
             [0x618011]=0, [0x618013]=0, [0x618015]=0, [0x618017]=0, [0x618019]=0}
  for a, x in pairs(v) do mem:write_u8(a, x) end
  mem:write_u8(0x61801f, 0)
end
emu.register_frame_done(function()
  frames = frames + 1
  if frames == DEBUT then
    if os.getenv("WAV") then manager.machine.sound:start_recording(os.getenv("WAV")) end
    t0 = t()
  end
  if frames < DEBUT then return end
  if not k then k, ph0 = 1, frames end
  local ph = frames - ph0
  if ph == (durees[k] or PAS) then k = k + 1; ph0 = frames; ph = 0 end
  if ph == 0 then
    if k > #codes then
      if os.getenv("WAV") then manager.machine.sound:stop_recording() end
      log:write("FIN\n"); log:close(); manager.machine:exit(); return
    end
    envoie(0xff, 0x00)
  elseif ph == 4 then
    log:write(string.format("C %.6f %04x\n", t() - t0, codes[k])); log:flush()
    envoie(codes[k] >> 8, codes[k] & 0xff)
  end
end)
