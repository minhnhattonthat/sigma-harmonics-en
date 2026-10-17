# Debug tool: reach any scene without playing

Everything here boots the ROM cold in the DeSmuME QA fork (`tools/desmume/`, from
`<skill>/scripts/fetch_emu.py desmume`, <skill> = the translate-retro-game skill folder: $RETRO_SKILL or the plugin). No user save, no savestate, so it keeps working
after every rebuild.

```
python -X utf8 tools/debug/tour.py 4100 4512            # dialogue events by text table id
python -X utf8 tools/debug/tour.py                      # all 335 dialogue events (~1 h with --jobs 4)
python -X utf8 tools/debug/tour.py --rooms 2 30         # field rooms by room byte (no N = all 95)
python -X utf8 tools/debug/tour.py --scenes descent     # named screens from scenes.json (no NAME = all)
```

Output: `work/qa/<events|rooms|scenes>/<id>/sheet.png` (frames after the warp), `final.png`, `log.txt`, and
`report.tsv`. Events report `ok shown/rows missing [..]`: the rows of `script/<table>.json` the dialogue fetched.
Missing rows are other choice branches, per-object lines (touching things in the room), lines an event shows only
in its real context, or a stall: read the sheet. Scripts branch on the chapter byte: `--chapter C` plays events in
chapter C (0-7), `--sweep` retries every event under half shown in each chapter and keeps the best (event 04040:
0 rows in chapter 0, 13 in chapter 1).

| File | What |
|---|---|
| `tour.py` | Runner: events, rooms, scenes; parallel (`--jobs`), exit 1 if a case fails |
| `warp.lua` | `TABLE=N`: when New Game loads the opening event (script 04085 + text 04086), hand it event N-1 / N instead; `CHAPTER=c` sets the save card's chapter byte as it loads (scripts branch on it). `SWAP="a=b,.."` swaps any file ids; `5915=8391` skips the opening (field at ~frame 2400). `LOADS=1` logs every file looked up. Logs `msg <slot> <row>` for each text row fetched |
| `field.lua` | `UNLOCK=1` enables every field-menu button, `BATTLE=N` starts battle N from the field (`AT=frame`) |
| `capture.lua` | `CAPTURE_AT=frame`: writes the live game struct (save card + state) to `<out>/game.bin` |
| `mksave.py` | Builds a `.dsv` from a captured struct (`new`) or patches one: `--card 0xa=N` room, `--set OFF=VAL`, `--unlock` (menu + all Shiki cards); fixes both checksums |
| `scenes.json` | Named screens: field, battle, menu, system, config, glossary, movements, load, save, reasoning, shiki, descent, sound |
| `newgame.txt` | Route: cold boot to New Game |

## How it works (arm9 addresses, original ROM)

- Files: `0x2089970` finds a data.cpk entry by id (r2). Every load goes through it, so a Lua exec hook can log or
  swap ids. A story event is script file N (odd, `Sigma000` bytecode) plus text table N+1 (`script/NNNNN.json`).
- Text rows: `0x2069ed4(mgr, dst, slot, row)` fetches row `row` of the table in `slot` (2 = event dialogue).
- Save (`.dsv`, 64 KB EEPROM): `SIGMA V000.001` + three 0x34-byte cards at 0x10 + three 0x3540-byte slots at 0xac.
  In RAM card and state sit together at 0x215ef10 (state at 0x215ef44). Card +8 chapter (0xff = empty), +0xa room
  (field loads scenario script 5914+room, `0x2066fec`). Checksums: card +0x10, state +0x3218 (XOR of words).
- State offsets: +0x18 13 Shiki card records of 12 bytes (byte 0 = owned); +0x110 battle id (s16); +0x1b0.. menu
  button enables (`0x20492c8`).
- Tasks (RTTI names in arm9): CTaskTitle, CTaskField, CTaskBattle, CTask2DEvent. CTaskField's update `0x2067374`
  switches task on the exit code at task +0x2b80 (2 = 2DEvent, 3 = Battle, 4 = Field); factories at 0x20da5e4
  (Field), 0x20da620 (Battle), 0x20da644.

## Not covered yet

- Events whose script needs story flags beyond the chapter byte, or player actions (examining objects), show few
  rows (see report.tsv). The event-flag area of the state is not mapped yet.
- Battle ids: 1 and 119 load (119 = the end-game save's last battle); 60 gives a black screen. Valid id list unknown.
- Chapter (story) flags beyond the card byte are not mapped, so rooms load with New Game progress.
