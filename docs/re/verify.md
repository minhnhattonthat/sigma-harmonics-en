# Verify in game (provisional widths)

Checked 2026-10-11 with an end-game save (Death Movement, 1F Great Clock Chamber):
- Field location label 06413: canvas moved from tile row 12 to 8 (dlgfont.PATCH, 0x2048a10): 128 px to the screen
  edge. Lint cap in batches.MEASURED.
- Save/load card chapter 04695/04703 rows 30-38: ~46 px before the fixed hour column, so numerals only (I, Hidden III,
  Death). Play time font 04696/04704 keeps its own digits (latin.KEEP). Location line = 04700 (save) / 04708 (load),
  ~92 px to the card frame (lint cap 113); 黒上の館ホーム is "Kurogami Mansion" there, "Kurogami Mansion Stop" on
  the field label.
- Echo list 04390 and event list 06813 (Notebook): fine.
- Descent screen skill grid: DONE (tools/gridfont.py). The grid reads table 05609 rows 152-223 (not 04985 or 04726)
  and draws with font 05611 (9x9 1bpp, flags 2; the header uses 04725). Descriptor table 0x20c3b58 (0x1c bytes each:
  x, y, w, h, ...): entries 5-25 = 3 columns x 7 rows (x 6/68/130, y 134 + 16k, w 56, h 10), one 2-tile OBJ canvas
  each; a rect that starts mid-tile (y%8 = 6) cannot grow past 10 rows without corrupting the OBJ buffers, so PATCH
  moves y to 128 + 16k (tile-aligned) and h to 16. The engine draws ONE line per canvas, so font 05611 is re-celled to
  16 rows (flags 2 keeps the vertical axis in columns: old columns shift +7) and each name is a run of 9-column chunk
  glyphs (U+F900..) holding 1 or 2 lines of px9. Drawn by 0x2051e70 (open) and the code around 0x2051d08 (card
  switch); slot data fp+0x1eb98 + col*0x38 + row*8 (<0 = empty). Widest line 62 px (cell pitch). QA: all 12 cards of
  the end-game save, both tabs.
- Battle (user states tools/desmume/StateSlots/battle.dst, States/battle.dst): loads 05610 (12x13) and 05611. The
  skill name under each of the 3 cards comes from the SAME table as the Descent grid, 05609 rows 152-223 (found by
  searching a RAM dump), not 04985; the top-bar descriptions (rows 111-124) fit. Only ~11 rows are free from y=245 to
  the screen edge and the engine wraps at 62 px, so a px9 two-line name lost its second line. gridfont now draws every
  name that does not fit one line of PLAIN text (plain text spaces glyphs by advance + 1, wider than the strips) as two
  lines of 3x5 caps in rows 0-4 / 6-10, which fits both screens. Names are drawn ONCE at battle start, and a savestate
  holds the CPK table of the ROM it was made with, so a state goes stale (hang on the loading screen) after ANY rebuild
  that changes file sizes: make the battle state with the current build. IN-GAME BATTLE CHECK STILL OPEN
  (Descent verified; battle only as mockup work/qa/bt1/mock.png). 06365 untouched.
- Sprites (tools/sprite.py, font/sprites.json): field hour badge 06421, Notebook 06822 buttons, battle labels
  05714/05717/05735 done. Left as is: Shiki card art (zodiac kanji), battle icons 曲/技/神 (05720/05729/05738, which
  already carry -Battle Music- / -Card Skill- / -Job Change-).

Not seen yet:
- UI tables guessed to use the main font (meta: own font cannot draw their text): 4985 5609 6365 in battle.
- Term list readings (04388/04741): English term repeated in the reading row; check how the glossary list shows them.
- Glossary term list 04741 (9px font, 110 px JP budget) and skill list 04726 (190 px): provisional 150/210 px.
