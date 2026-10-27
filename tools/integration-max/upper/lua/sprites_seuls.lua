-- (agent_integration_max) tournee_max.lua + mesure des sprites seuls : aux images SEULS (liste « a,b,… »), capture
-- normale, puis l'image suivante avec les couches de défilement coupées (registre de couches CPS-B $804140 + $26 :
-- bits $02/$04/$08 effacés, écritures du jeu détournées) et capture.
dofile("<workspace>/work/agent_integration_max/lua/tournee_max.lua")
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local S = {}
for x in string.gmatch(os.getenv("SEULS") or "", "[^,]+") do S[tonumber(x)] = true end
local n, coupe = 0, false
TAP_COUCHES = mem:install_write_tap(0x804166, 0x804167, "couches", function(o, d, m)
  if coupe then return d & ~0x3E end
end)
emu.register_frame_done(function()
  n = n + 1
  if coupe then
    manager.machine.video:snapshot(); coupe = false
    if os.getenv("OBJDIR") then                     -- listes d'objets converties (2 banques) de l'image coupée
      for k, nm in ipairs({":objram1", ":objram2"}) do
        local sh = manager.machine.memory.shares[nm]; local t = {}
        for a = 0, sh.size - 2, 2 do t[#t + 1] = string.pack(">I2", sh:read_u16(a)) end
        local f = io.open(string.format("%s/o%d_%d.bin", os.getenv("OBJDIR"), k, n), "wb"); f:write(table.concat(t)); f:close()
      end
    end
    return
  end
  if S[n] then
    manager.machine.video:snapshot(); coupe = true
    mem:write_u16(0x804166, mem:read_u16(0x804166) & ~0x3E)
  end
end)
