# Graphics brief - Sigma Harmonics full-screen text images

You relabel a group of full-screen tile graphics in English. Work only on the ids in your dispatch. No subagents.
Don't edit tools/, script/, or any recipe file but your own. Don't build the ROM or commit; the controller does.

## Read first
- `work/qa/rg_text_survey.md`: what each id shows (thumbnail reading; check the full-size image yourself).
- `glossary.md` rulings and terms (names given-name first, honorifics kept, no abbreviations, 楽章 -> Movement,
  Nの刻 -> "N:00", 第死楽章 -> Death Movement, 裏Ⅲ楽章 -> Hidden Movement III). `grep` script/*.json for any
  term that already has an English form and reuse it exactly.
- Docstring of `tools/scredit.py`.

## Tool
- `.venv/Scripts/python -X utf8 tools/scredit.py show ID OUT.png` - original, player view, 2x.
- `.venv/Scripts/python -X utf8 tools/scredit.py preview ID OUT.png` - your recipe applied and re-rendered from the
  written tiles, 2x. Open OUT.png with the Read tool and look at it every time. Write PNGs under
  `work/qa/gfx/` (create it).
- Recipe file: `font/screens_<group>.json` (your group name is in the dispatch). Format in the scredit docstring:
  `wipe` boxes, then `text` items. Coordinates are player view (the 2x PNG halved). A 32x24 screen is 192x256 in
  player view; other screen sizes rotate the same way (raw W x H -> player H x W).
- Fonts in `font/`: DejaVuSerif.ttf (titles, banners, cards - default), DejaVuSans.ttf / DejaVuSans-Bold.ttf (UI,
  small labels). Pick sizes so text fits; multi-line with `\n`. `outline: [r,g,b]` adds a 1px outline.
- 4bpp screens: each 8x8 cell has only its palette's 16 colours. Draw text in the colour the Japanese used (sample
  it from the `show` PNG). A hue shift in `preview` means the colour isn't available there.
- The wipe fills each row with that row's most common dark colour. On busy art, use several small wipe boxes
  hugging the text instead of one big box. If wiping can't give a clean result, say so in your report.
- An `AssertionError ... tiles > N` means too many new unique tiles: shrink the wiped area or the text.

## Style
- Match the original's placement, colour and hierarchy (big title, small subtitle). Horizontal English, centred
  where the Japanese was centred. Drop furigana (it was a reading aid).
- Already-English parts (e.g. "-Yes-" under はい, role titles in credits) stay; replace only the Japanese, and
  remove a now-redundant English subtitle only if the main label becomes the same word.

## Report (reply with only this)
`<group>: N ids done`, then `SKIPPED: id - why` and `CHECK: id - what the controller should look at`.
