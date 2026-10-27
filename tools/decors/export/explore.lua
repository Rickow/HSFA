-- exploration API : partie arcade, P1 = Ryu, decor force, infos API a la 1re image de combat
local cpu = manager.machine.devices[":maincpu"]; local mem = cpu.spaces["program"]
local ports = manager.machine.ioport.ports
local STG = tonumber(os.getenv("STG") or "0", 16)
local out = io.open(os.getenv("OUT"), "w")
local J1, J2 = 0xFF8400, 0xFF8800
local k, sel, stable = 0, 0, 0
FST = mem:install_write_tap(0xFF8100, 0xFF8101, "fst", function(o, d, m)
  if k >= 1400 and d ~= 0 then
    if m == 0xffff then return STG elseif m == 0x00ff then return STG & 0xff elseif m == 0xff00 then return 0 end
  end
end)
local function info()
  out:write("== shares\n"); for t, s in pairs(manager.machine.memory.shares) do out:write(t .. " " .. s.size .. "\n") end
  out:write("== regions\n"); for t, s in pairs(manager.machine.memory.regions) do out:write(t .. " " .. s.size .. "\n") end
  out:write("== devices\n"); for t, d in pairs(manager.machine.devices) do out:write(t .. " " .. d.name .. "\n") end
  local ok, p = pcall(function() return manager.machine.palettes end)
  out:write("palettes " .. tostring(ok) .. " " .. tostring(p) .. "\n")
  if ok and p then for t, pp in pairs(p) do out:write("PAL " .. t .. " " .. tostring(pp) .. "\n") end end
  local sc = manager.machine.screens[":screen"]
  out:write(string.format("screen %d x %d\n", sc.width, sc.height))
  local ok2, vis = pcall(function() return sc.visible_area end)
  if ok2 and vis then out:write(string.format("vis %d %d %d %d\n", vis.min_x, vis.max_x, vis.min_y, vis.max_y)) end
end
emu.register_frame_done(function()
  k = k + 1
  local v = {}
  local function on(p, f) v[p .. "|" .. f] = 1 end
  if k >= 1500 and k < 1860 and k % 60 < 8 then on(":IN2", "Coin 1") end
  local jeu = mem:read_u8(0xFF80A8)
  if k >= 1900 and k % 40 < 6 and jeu & 1 == 0 then on(":IN2", "1 Player Start") end
  local mode = mem:read_u16(0xFF800C)
  local ecran_sel = mem:read_u16(0xFF8000) == 2 and mem:read_u16(0xFF8004) == 2
  if ecran_sel then sel = sel + 1 else sel = 0 end
  if ecran_sel and sel < 120 then mem:write_u8(J1 + 0x102, 0) end
  local combat = mode == 6 and mem:read_u8(J1 + 4) == 2 and mem:read_u8(J2 + 4) == 2
  if k >= 2000 and k % 24 < 4 and jeu & 1 == 1 and not combat and (not ecran_sel or sel >= 120) then on(":IN0", "P1 Button 1") end
  if jeu & 1 == 1 then mem:write_u16(J1 + 0x50, 0x90); mem:write_u16(J1 + 0x52, 0x90); mem:write_u16(J2 + 0x50, 0x90); mem:write_u16(J2 + 0x52, 0x90) end
  if combat then stable = stable + 1 else stable = 0 end
  if k % 100 == 0 then out:write(string.format("%d %04x %04x %04x mode=%04x stg=%04x c=%d x1=%04x x2=%04x\n", k, mem:read_u16(0xFF8000), mem:read_u16(0xFF8002), mem:read_u16(0xFF8004), mode, mem:read_u16(0xFF8100), stable, mem:read_u16(J1+0x10), mem:read_u16(J2+0x10))) end
  if stable == 120 then
    info()
    manager.machine.video:snapshot()
    manager.machine:save("combat_" .. os.getenv("STG"))
    out:write("SAVED " .. k .. "\n"); out:close(); manager.machine:exit(); return
  end
  for _, p in ipairs({":IN0", ":IN1", ":IN2"}) do
    for fn, f in pairs(ports[p].fields) do
      if string.match(fn, "^P%d ") or fn == "Coin 1" or fn == "1 Player Start" then f:set_value(v[p .. "|" .. fn] or 0) end
    end
  end
  if k > 9000 then out:write("TIMEOUT\n"); out:close(); manager.machine:exit() end
end)
