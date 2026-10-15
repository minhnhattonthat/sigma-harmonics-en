-- emu.py --script: log every data.cpk file the game looks up (0x2089970 = ITOC find by id, id in r2) to log.txt
-- as "load <frame> <id> lr=<caller>". Shows which script / text table / font a scene uses.
-- --var STACK=1 adds the code addresses found on the stack (a rough call chain).
local frame = 0
L.on_frame(function(n) frame = n end)
L.on_exec(0x2089970, function()
  local s = string.format("load %d %05d lr=%08x", frame, memory.getregister("arm9.r2"), memory.getregister("arm9.r14"))
  if STACK then
    local sp = memory.getregister("arm9.r13")
    for a = sp, sp + 0x200, 4 do
      local v = memory.readdword(a)
      if v >= 0x02000000 and v < 0x020e5000 then s = s .. string.format(" %08x", v) end
    end
  end
  L.log(s)
end)
