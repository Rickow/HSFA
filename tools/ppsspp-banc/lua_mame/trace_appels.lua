-- (agent_ppsspp_banc) Trace d'appels côté Upper MAX : coup.lua de la session d'intégration (lecture seule) + points d'arrêt de journal
-- sur les entrées de fonctions psp_xxxxxx. Variables : BPS = "adr,adr,..." (hexa 68K), JBP = journal (console du débogueur),
-- JFR = « F <image> <c> » par image (c = compteur d'images de combat de coup.lua), DUMPCODE = fichier où écrire $3A0000-$3B7000 (facultatif).
-- Lancer avec EXTRA="-debug -debugger none".
dofile("<workspace>/work/agent_integration_max/lua/coup.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local FR = io.open(os.getenv("JFR"), "w")
local n, c = 0, 0
local JBP = io.open(os.getenv("JBP"), "w")
local lastc = 0
-- vidage de la console du débogueur dans le fichier à chaque image (la console est un tampon circulaire) ; chaque ligne porte un compteur #N
local function vide()
  local log = manager.machine.debugger.consolelog
  local nl, neuf = #log, {}
  for i = nl, 1, -1 do
    local l = log[i]
    local k = tonumber(l:match("^B (%d+) "))
    if k then
      if k <= lastc then break end
      neuf[#neuf + 1] = l
    end
  end
  for i = #neuf, 1, -1 do JBP:write(neuf[i], "\n") end
  if #neuf > 0 then lastc = tonumber(neuf[1]:match("^B (%d+) ")) end
end
local scr = manager.machine.screens[":screen"]
emu.register_frame_done(function()
  n = n + 1
  if mem:read_u16(0xFF800C) == 6 then c = c + 1 else c = 0 end
  FR:write(string.format("F %d %d\n", scr:frame_number(), c))
  if n > 5 then vide() end
  if n == 5 then
    local d = manager.machine.debugger
    if os.getenv("DUMPCODE") then
      local G = io.open(os.getenv("DUMPCODE"), "wb")
      for a = 0x3A0000, 0x3B7000 - 1, 2 do local w = mem:read_u16(a); G:write(string.char(w >> 8, w & 255)) end
      G:close()
    end
    for a in string.gmatch(os.getenv("BPS") or "", "[^,]+") do
      -- l'adresse du point d'arrêt est écrite en clair (le « pc » du débogueur 68000 est en avance de 2) ; la pile : sp (a7 n'est pas un symbole)
      d:command("bpset " .. a .. ",1,{printf \"B %d " .. a .. " f=%d d0=%x d1=%x a6=%x r=%x\\n\",totalcycles,frame,d0,d1,a6,d@sp; g}")
    end
  end
end)
emu.register_stop(function()
  local lg = manager.machine.debugger.consolelog; local DD = io.open(os.getenv("JBP") .. ".dbg", "w"); for i = math.max(1, #lg - 10), #lg do DD:write(lg[i], "\n") end DD:close()
  vide(); FR:close(); JBP:close()
end)
