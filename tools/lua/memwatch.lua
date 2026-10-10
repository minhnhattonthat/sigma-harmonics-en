-- emu.py --script: log who writes (WATCH_MODE=write) or reads (=read) memory [WATCH_AT, +WATCH_LEN) between frames
-- WATCH_FROM..WATCH_TO. CPU accesses only (DMA does not fire). Writes <out>/writes.txt: one line per distinct
-- (pc, lr) with a count and the first r0-r3.
local REG = os.getenv("WATCH_MODE") == "read" and memory.registerread or memory.registerwrite
local A = tonumber(os.getenv("WATCH_AT") or "0x06204800")
local N = tonumber(os.getenv("WATCH_LEN") or "0x2000")
local FROM = tonumber(os.getenv("WATCH_FROM") or "4300")
local TO = tonumber(os.getenv("WATCH_TO") or "4400")
local seen, order = {}, {}
local function reg(n) return memory.getregister("arm9." .. n) end
local armed = false
L.on_frame(function(n)
  if n == FROM and not armed then
    armed = true
    REG(A, N, function(addr, size)
      local k = string.format("pc=%08x lr=%08x", reg("r15"), reg("r14"))
      if not seen[k] then
        seen[k] = { c = 0, s = string.format("addr=%08x r0=%08x r1=%08x r2=%08x r3=%08x", addr or 0, reg("r0"), reg("r1"), reg("r2"), reg("r3")) }
        order[#order + 1] = k
      end
      seen[k].c = seen[k].c + 1
    end)
  end
  if n == TO then
    REG(A, N, nil)
    local f = io.open(OUT .. "writes.txt", "w")
    for _, k in ipairs(order) do f:write(k, " n=", seen[k].c, " ", seen[k].s, "\n") end
    f:close()
    L.log("writes logged: " .. #order)
  end
end)
