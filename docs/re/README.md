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
