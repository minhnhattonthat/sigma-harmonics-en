-- emu.py --script: log callers of the functions in EXEC_AT (comma-separated hex) between frames WATCH_FROM..WATCH_TO.
-- Writes <out>/exec.txt: one line per distinct (fn, lr) with a count and the first r0-r3 and 4 stack words.
local FROM = tonumber(os.getenv("WATCH_FROM") or "4300")
local TO = tonumber(os.getenv("WATCH_TO") or "4400")
local seen, order, on = {}, {}, false
local function reg(n) return memory.getregister("arm9." .. n) end
for s in (os.getenv("EXEC_AT") or ""):gmatch("[^,]+") do
  local fn = tonumber(s)
  L.on_exec(fn, function()
    if not on then return end
    local k = string.format("fn=%08x lr=%08x", fn, reg("r14"))
    if not seen[k] then
      local sp = reg("r13")
      seen[k] = { c = 0, s = string.format("r0=%08x r1=%08x r2=%08x r3=%08x sp:%08x %08x %08x %08x", reg("r0"), reg("r1"),
        reg("r2"), reg("r3"), memory.readdword(sp), memory.readdword(sp + 4), memory.readdword(sp + 8), memory.readdword(sp + 12)) }
      order[#order + 1] = k
    end
    seen[k].c = seen[k].c + 1
  end)
end
L.on_frame(function(n)
  if n == FROM then on = true end
  if n == TO then
    on = false
    local f = io.open(OUT .. "exec.txt", "w")
    for _, k in ipairs(order) do f:write(k, " n=", seen[k].c, " ", seen[k].s, "\n") end
    f:close()
  end
end)
