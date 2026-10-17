# RE notes

- `data/data.cpk` (NitroFS id 0) is a CRI CPK (CPKMC 1.40), ITOC only (files by numeric id, no names), Align 512, content at 0x800.
- Compressed entries are CRILAYLA with the 8-byte magic zeroed. FileSize==ExtractSize means stored raw; the game accepts raw entries for any file.
- ITOC: DataL rows when FileSize and ExtractSize <= 0xFFFF, else DataH. Header EnabledPackedSize = sum ExtractSize, EnabledDataSize = sum FileSize.
- After the cpk: `sound_data.sdat` (id 1), last file in the ROM. ~6.4 MB free before the 128 MB cart limit.
- arm9 is uncompressed, no overlays, holds no text.

## Text
- 362 CPK entries are string tables: u32 LE (offset, length) pairs, then NUL-terminated UTF-8. length includes the NUL. Detected by `strtab.is_strtab`.
- Literal two-char `
` = newline. `$cNN` = colour. Text ids: 3964-6813; many tables follow a small subset NFTR font (e.g. font 04694 + text 04695).
- Some UI text (title menu prompt, chapter titles) is graphics or other data; not yet found.

## Fonts
- 32 NFTR files. 04387 = main 16x16, 3bpp, 1561 glyphs, CGLP flags 3 (glyphs stored rotated 90 deg). Proportional: advance from CWDH is honoured.
- Small 9x9/11x11 subset fonts (1-2 bpp, flags 0/2/6) carry only the glyphs their screen uses.
- A char missing from the font hangs the game (ASCII "AB" froze the first cutscene; "0123 cg", which exist in 04387, render fine).

## Renderer quirks (found in QA, all handled in tools/build.py + tools/latin.py)
- Fonts get every ASCII char plus full-width twins (U+FF01-FF5E) drawn with the same narrow Latin glyphs, and U+2002.
- UI routines (location names, table 6413; bisected with tools/bisect_text.py) hang on ANY 1-byte UTF-8 char:
  UI tables get full-width twins for all ASCII.
- Dialogue renderer clips the glyph after any ASCII 0x50-0x5F (P-Z [ \ ] ^ _): those become full-width twins.
- U+0020 and U+3000 get a full-cell (16 px) advance whatever their glyph says: English spaces are U+2002 (en space).
- Advance = quantised ink width; the renderer adds 1 px. Dialogue Latin = STIX General 13 px, 3bpp, stored rotated 180.
- A line wider than the box is clipped; more than 60 glyphs + breaks in one bubble crashes (see Text engine).
- Opening scene is table 04086 (table ids are not in story order).

## Text engine (NitroSystem g2d, arm9; tools/arm9dis.py, tools/lua/execlog.lua + memwatch.lua)
- 0x2096628 UTF-8 decoder, 0x20965b4 glyph bit reader, 0x2094c10/0x2094cbc measure string/text rect.
- 0x2096260 DrawTextRect -> 0x20960f8 lines -> 0x2096044 one line -> 0x2095a0c char (origin by CGLP flags) ->
  canvas vtable (0x20951dc / 0x2095374 for the dialogue canvas).
- Direction is data: callers (0x200cfac, 0x200d530) switch on the font's CGLP flags: 0,7 -> +x; 1,2 -> +y;
  3,4 -> -x; 5,6 -> -y (raw screen). Each char advances (width + hSpace) along it; each line advances
  (lineHeight + vSpace) along (-dy, dx).
- Dialogue font 04387 has flags 3: raw -x = top-to-bottom for the player (Japanese vertical writing).
  Flags 2 gives raw +y = left-to-right for the player, lines downward. Glyphs are stored pre-rotated; the
  Japanese ones are already upright for the player under either flag, only Latin needs re-rotating.
- Dialogue text reaches sub BG VRAM (0x06204800+) by DMA; glyph data of 04387 in RAM at 0x21dcc3c (CGLP 0x21dcc2c).
- Dialogue bubbles do NOT use the flag direction: 0x200d864 (sole caller 0x2047340) lays out one OBJ sprite per
  char made by 0x200d35c (measure, char canvas, OAM via 0x2095d4c, draw centred via 0x2096260, returns width+1),
  doing x -= advance per char and taking line y from table 0x20cc0bc ([32] / [20,44] / [14,32,50]: max 3 lines).
- Blitter 0x2095374 copies only CWDH glyphWidth raw-x columns of a cell (fine for text along x).
- Bubble record array: 0x24-byte records at +0x18, count at +0x88c, NO bound: max 60 records (one per glyph and
  one per line break); the 61st overwrites the count and the game crashes. The parser stopped at 3 lines.
- Shipped (tools/dlgfont.py, wired into build.py): bubbles read left-to-right for the player. Font 04387 flags 2,
  arm9 PATCH list (layout, 12 lines at 14 px, no extra 1 px), text reflowed to 62 px x 12 lines (fit.py, words
  hyphenated) and packed into <=16 px chunk glyphs drawn into unused kanji slots, one centring spacer per line.
  tools/exp_horizontal.py is the first prototype (kept for reference).
- Chunk spacing (fixed 2026-10, found by the debug-tool event tour): the patched bubble centres each glyph at
  advance / 2 (integer), so an odd-advance chunk landed 1 px early: a gap after it ("wa s") and a squeezed space
  before it ("madeto"). Chunks now draw each char at whole-pixel positions (latin.dlg_adv) and odd-advance chunks
  start their ink 1 px into the cell (latin.dlg_glyph bubble=True); tests/test_dlgfont.py checks it.
- Battle card names: one-line names were plain text in re-celled font 05611, whose glyph widths are +7, so the
  battle screen centred "Big Stop" ~20 px left (off screen). gridfont now draws every name as chunks.

## Game state, save, tasks (debug tool)
- Files, events, save layout, task switching and the warp hooks: tools/debug/README.md.
