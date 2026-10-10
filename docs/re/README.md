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
- A line wider than the box is clipped; a much longer one crashed once (3-line test). Lint keeps 180 px.
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
- Horizontal-for-player prototype (2026-10-10, tools/exp_horizontal.py, works in the opening): font 04387 flags
  3 -> 2; Latin stored upright (latin.orient flags 2) with glyphWidth 16, advance = ink; arm9 patches:
  0x200d3bc/3c4 swap canvas w/h; 0x200d4b8/4c4 nop (x nudge); 0x200d5ac `mov r1,#8`, 0x200d5b0 `mov r2,fp`
  (centre); 0x200d88c `mov r0,#K`; 0x200d8d0-8e8 newline x = x0 - 16*line, y = base - K; 0x200d920-928 y += adv.
  K=52, wrap 56 px: about 10 chars x ~10 lines per bubble.
