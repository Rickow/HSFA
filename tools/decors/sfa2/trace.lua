-- Trace d'execution (debogueur MAME, -debug -debugger none) entre les images T0 et T1 -> TRACE, puis SCRIPT.
local T0, T1 = tonumber(os.getenv("T0")), tonumber(os.getenv("T1"))
local F = os.getenv("TRACE") or "trace.txt"
local n = 0
ABONNEMENT_TRACE = emu.add_machine_frame_notifier(function()
  n = n + 1
  local dbg = manager.machine.debugger
  if n == 1 then dbg.execution_state = "run" end
  if n == T0 then dbg:command('trace ' .. F .. ',maincpu,noloop') ; dbg.execution_state = "run" end
  if n == T1 then dbg:command('trace off'); dbg.execution_state = "run" end
end)
dofile(os.getenv("SCRIPT"))
