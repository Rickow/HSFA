-- a l'image W0 : execute les commandes du debogueur du fichier DCMD (une par ligne) ; a W1 : DCMD2 (facultatif) ; journal console -> DLOG
local kk = 0
local W0, W1 = tonumber(os.getenv("W0")), tonumber(os.getenv("W1") or "-1")
local function run(f) for l in io.lines(f) do if l ~= "" then manager.machine.debugger:command(l) end end end
local function dump()
  local fo = io.open(os.getenv("DLOG"), "w")
  for _, l in ipairs(manager.machine.debugger.consolelog) do fo:write(l, "\n") end
  fo:close()
end
emu.register_frame_done(function()
  kk = kk + 1
  if kk == W0 then run(os.getenv("DCMD")) end
  if kk == W1 then if os.getenv("DCMD2") then run(os.getenv("DCMD2")) end; dump() end
end)
dofile(os.getenv("BASE_LUA") or "<workspace>/work/mame/tournee.lua")
