-- emu.py --script: play any story event from a cold boot (route tools/debug/newgame.txt).
-- An event is a script file N plus its text table N+1 in data.cpk (e.g. opening = script 04085 + text 04086).
-- When the game looks up the HOST event's files (0x2089970 = ITOC find by id, id in r2), we hand it EVENT's instead.
-- Globals (--var): TABLE = text table id of the event to play (script = TABLE-1); HOST = host text table (default
-- 4086, the opening, which New Game loads ~frame 2300; field events crash there, use 4512 = the first field event,
-- ~frame 4600 with --mash 40). SWAP = "from=to,..." swaps any other file ids
-- (e.g. "5915=5916": New Game's room script; "5915=8391" skips the opening, field ~frame 2400).
local map = {}
if TABLE then
  local host = HOST or 4086
  map[host - 1], map[host] = TABLE - 1, TABLE
end
for f, t in (SWAP or ""):gmatch("(%d+)=(%d+)") do map[tonumber(f)] = tonumber(t) end
-- 0x2069ed4(mgr, dst, slot, index) fetches text row `index` of the table loaded in `slot`: log each row once so
-- the tour can count which lines were shown ("msg <slot> <row>").
local shown, active = {}, not TABLE -- with TABLE, count only rows fetched after the event's script loads
L.on_exec(0x2069ed4, function()
  if not active then return end
  local k = string.format("msg %d %d", memory.getregister("arm9.r2"), memory.getregister("arm9.r3"))
  if not shown[k] then shown[k] = true; L.log(k) end
end)
local hits = 0
L.on_exec(0x2089970, function()
  local id = memory.getregister("arm9.r2")
  if LOADS then L.log(string.format("load %d %05d", L.frame, id)) end -- --var LOADS=1: every file looked up
  if map[id] then
    memory.setregister("arm9.r2", map[id])
    -- CHAPTER=c: scripts branch on the save card's chapter byte; set it as the event loads (earlier changes New Game)
    if CHAPTER and TABLE and map[id] == TABLE then memory.writebyte(0x0215ef18, CHAPTER) end
    if TABLE and map[id] == TABLE - 1 then active = true end
    hits = hits + 1
    if hits <= 8 then L.log(string.format("warp %d -> %d at frame %d", id, map[id], L.frame or -1)) end
  end
end)
