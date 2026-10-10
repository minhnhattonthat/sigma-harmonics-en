-- emu.py --script: dump NDS main RAM (4 MB at 0x02000000) at frame DUMP_AT into DUMP_DIR/ram.bin (absolute path)
local DUMP_AT = tonumber(os.getenv("DUMP_AT") or "1700")
local OUT_DIR = os.getenv("DUMP_DIR") or OUT
L.on_frame(function(n)
  if n ~= DUMP_AT then return end
  local f = io.open(OUT_DIR .. "/ram.bin", "wb")
  local buf = {}
  for a = 0x02000000, 0x023FFFFF, 4 do
    local v = memory.readdword(a)
    buf[#buf + 1] = string.char(v % 256, math.floor(v / 256) % 256, math.floor(v / 65536) % 256, math.floor(v / 16777216) % 256)
    if #buf == 4096 then f:write(table.concat(buf)); buf = {} end
  end
  f:write(table.concat(buf)); f:close()
  L.log("dumped ram at " .. n)
end)
