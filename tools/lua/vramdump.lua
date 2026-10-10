-- emu.py --script: dump NDS VRAM regions at frame DUMP_AT into <out>/vram_<name>.bin
local DUMP_AT = tonumber(os.getenv("DUMP_AT") or "1700")
local OUT = os.getenv("DUMP_DIR") or "."
local regions = {
  {"bga", 0x06000000, 0x80000}, {"bgb", 0x06200000, 0x20000},
  {"obja", 0x06400000, 0x40000}, {"objb", 0x06600000, 0x20000},
  {"pal", 0x05000000, 0x800},
}
L.on_frame(function(n)
  if n ~= DUMP_AT then return end
  for _, r in ipairs(regions) do
    local f = io.open(OUT .. "/vram_" .. r[1] .. ".bin", "wb")
    for a = r[2], r[2] + r[3] - 1, 4 do
      local v = memory.readdword(a)
      f:write(string.char(v % 256, math.floor(v / 256) % 256, math.floor(v / 65536) % 256, math.floor(v / 16777216) % 256))
    end
    f:close()
  end
  L.log("dumped vram at " .. n)
  L.shot("dump")
end)
