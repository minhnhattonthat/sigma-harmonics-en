-- emu.py --script: write the live game struct (save card + state, RAM 0x215ef10, 0x3574 bytes) to <out>/game.bin
-- at frame CAPTURE_AT. Turn it into a save with tools/debug/mksave.py new OUT.dsv --state <out>/game.bin.
L.on_frame(function(n)
  if n ~= CAPTURE_AT then return end
  local f = assert(io.open(OUT .. "game.bin", "wb"))
  local buf = {}
  for a = 0x0215ef10, 0x0215ef10 + 0x3574 - 1 do buf[#buf + 1] = string.char(memory.readbyte(a)) end
  f:write(table.concat(buf)); f:close()
  L.log("captured game struct at " .. n)
end)
