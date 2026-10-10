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
