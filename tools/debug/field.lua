-- emu.py --script: field cheats applied at frame AT (default 3000), once the field is up.
-- Quick field from a cold boot: route tools/debug/newgame.txt + warp.lua --var "SWAP='5915=8391'" (field ~frame 2400).
--   UNLOCK=1   enable every field-menu button (System, Super Reasoning, Shiki Cards, Descent, Sound Search, ...):
--              the menu (0x20492c8) greys out button i unless its byte at state +0x1b0.. is non-zero.
--   BATTLE=N   start battle N: CTaskField's update (0x2067374, r0 = task) switches task on the exit code at
--              task +0x2b80 (2 = 2DEvent, 3 = Battle, 4 = Field); CTaskBattle reads its id (s16) at state +0x110.
-- State = RAM 0x215ef44 (the save slot); see mksave.py.
local STATE, at, field = 0x0215ef44, AT or 3000, nil
L.on_exec(0x2067374, function() field = memory.getregister("arm9.r0") end)
L.on_frame(function(n)
  if n ~= at then return end
  if UNLOCK then
    for i = 0, 7 do memory.writebyte(STATE + 0x1b0 + i, 1) end
    L.log("menu unlocked at " .. n)
  end
  if BATTLE then
    if not field then return L.fail("field.lua: no field task by frame " .. n) end
    memory.writeword(STATE + 0x110, BATTLE)
    memory.writedword(field + 0x2b80, 3)
    L.log(string.format("battle %d from field task %08x at %d", BATTLE, field, n))
  end
end)
