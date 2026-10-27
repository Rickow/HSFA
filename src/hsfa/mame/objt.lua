-- etat d'un objet (OBJ) : octets 0..7, a chaque changement, images F0..F1
local frames=0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local f = io.open(os.getenv("OUT"), "w")
local a0 = tonumber(os.getenv("F0")); local a1 = tonumber(os.getenv("F1")); local B = tonumber(os.getenv("OBJ"))
local last=""
emu.register_frame_done(function()
  frames=frames+1
  if frames>=a0 and frames<=a1 then
    local s=""
    for o=0,15 do s = s .. string.format("%02x", mem:read_u8(B+o)) end
    if s~=last then f:write(string.format("%5d : %s\n", frames, s)); last=s end
  end
  if frames>a1 then f:close(); manager.machine:exit() end
end)
