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
  OPEN.
- Still Japanese, sprites (not screens): field hour badge "15の刻" (sub OBJ, tiles from 06421/04793), Notebook
  "第死楽章" button and "15の刻" plate. OPEN.

Not seen yet:
- UI tables guessed to use the main font (meta: own font cannot draw their text): 4985 5609 6365 in battle.
- Term list readings (04388/04741): English term repeated in the reading row; check how the glossary list shows them.
- Glossary term list 04741 (9px font, 110 px JP budget) and skill list 04726 (190 px): provisional 150/210 px.
