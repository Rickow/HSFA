-- (e31) comme trace_e28.lua + action facultative TRACE_ACT (ex. 'tracelog "A6=%x D4=%x ",a6,d4') ; -debug -debugger none
dofile("<workspace>/work/greffe_arcade/lua/graine_pc.lua")
local f0, f1 = tonumber(os.getenv("TRACE_F0")), tonumber(os.getenv("TRACE_F1")); local kt = 0
local act = os.getenv("TRACE_ACT")
emu.register_frame_done(function()
  kt = kt + 1
  local d = manager.machine.debugger
  if not d then return end
  if kt == f0 then d:command("trace " .. os.getenv("TRACE_OUT") .. ",maincpu,noloop" .. (act and (",{" .. act .. "}") or "")) end
  if kt == f1 then d:command("trace off,maincpu") end
end)
