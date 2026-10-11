# Verify in game (provisional widths)

Checked 2026-10-11 with an end-game save (Death Movement, 1F Great Clock Chamber):
- Field location label 06413: canvas moved from tile row 12 to 8 (dlgfont.PATCH, 0x2048a10): 128 px to the screen
  edge. Lint cap in batches.MEASURED.
- Save/load card chapter 04695/04703 rows 30-38: ~46 px before the fixed hour column, so numerals only (I, Hidden III,
  Death). Play time font 04696/04704 keeps its own digits (latin.KEEP). Location line = 04700 (save) / 04708 (load),
  ~92 px to the card frame (lint cap 113); 黒上の館ホーム is "Kurogami Mansion" there, "Kurogami Mansion Stop" on
  the field label.
- Echo list 04390 and event list 06813 (Notebook): fine.
- Descent screen skill grid (04985/05609/06365 names): 3 columns of 64 px, centred; most English names overflow.
  OPEN. Layout: descriptor table 0x20c3b58 (26 x 0x1c: x, y, w, h, ... player view); entries 5-25 = 3 category
  columns x 7 slots (x 6/68/130, y 134 + 16k, w 56), canvases tile-aligned (2 tiles high). Drawn by 0x2051e70
  (open) and the routine around 0x2051d08 (card switch); slot data fp+0x1eb98 + col*0x38 + row*8 (<0 = empty).
  End-game cards show 13-15 skills.
- Sprites (tools/sprite.py, font/sprites.json): field hour badge 06421, Notebook 06822 buttons, battle labels
  05714/05717/05735 done. Left as is: Shiki card art (zodiac kanji), battle icons 曲/技/神 (05720/05729/05738, which
  already carry -Battle Music- / -Card Skill- / -Job Change-).

Not seen yet:
- UI tables guessed to use the main font (meta: own font cannot draw their text): 4985 5609 6365 in battle.
- Term list readings (04388/04741): English term repeated in the reading row; check how the glossary list shows them.
- Glossary term list 04741 (9px font, 110 px JP budget) and skill list 04726 (190 px): provisional 150/210 px.
