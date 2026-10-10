# Translator brief - Sigma Harmonics (Nintendo DS, 2008, Square Enix / Think Garage)

You translate part of the Japanese script of Sigma Harmonics into English for a fan patch. It is a mystery RPG:
Sigma Kurogami, a cool, bookish boy-genius detective ("boku"), and his childhood friend Neon Tsukiyumi, a cheerful
Card Wielder, travel through the Rift of Time to the Kurogami Mansion, where a chain of murders has rewritten history.
Sigma gathers Echoes (clues) and solves each case with Super Reasoning ("Q.E.D."), then they fight the Ouma.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - character voices and approved example lines. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (`glossary.md` has the full table and rulings).

## Input: `work/tl/<batch>.tsv`
`id<TAB>box<TAB>form<TAB>limit<TAB>Japanese`
- box: `R` = right-hand box (almost always Sigma), `L` = left-hand box (Neon or any other character),
  `R-thought` = Sigma's inner voice, `sys` = narration / tutorial / system, `-` = unknown (use context).
- form: `dlg` = dialogue box, auto-wrapped by the build; `ui` = menu/label/description text in a small font.
- limit: `3x180px` = 3 lines of 180 px (~25 chars each, ~70 chars total) for dialogue; for ui, lines x pixels.
- ` / ` separates the lines of one Japanese box: translate the box as one utterance.
Lines are in game-file order: neighbours are context. A sentence often runs across 2-4 consecutive boxes
(e.g. "Neon, the light at" / "the end of the hall..."): make the pieces read in sequence.
Some scenes repeat the same line in several voices (one per Neon costume, see style reference): translate each
in its own voice; never merge them.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order.
- Plain ASCII: straight quotes, `...`, `--`. No Japanese, no full-width characters, no curly quotes, no tabs.
- Dialogue (`dlg`): no `\n`; the build wraps it. Keep it within the box: check with the fitter (below).
- UI (`ui`): one line unless the Japanese has several; then you may use `\n` (backslash + n) between lines,
  at most as many lines as the Japanese. Keep it within the pixel limit.
- `$c01`..`$c04` start a colour, `$c00` ends it. Copy every code, in the same order, around the matching English
  words: `$c02murder$c00`. No other `$`.

## Validate
- Fit one line: `.venv/Scripts/python -X utf8 tools/fit.py "English text"` (dialogue) or `... --ui` (prints px).
- Whole batch: `.venv/Scripts/python -X utf8 tools/batches.py check <batch>`. Fix every reported id until it prints OK.

## Style
- Faithful: keep the information and the order of ideas; adapt idiom, not meaning. Don't add facts the Japanese
  doesn't state; don't summarise or skip. Wordplay and jokes must still land in English (no translator notes).
- Names and terms exactly as the glossary (`[Echo]`, `Super Reasoning`, `Tsukaibito`, `Ouma`...). Never abbreviate
  to fit; rephrase instead. If a box can't fit without losing meaning, keep the meaning, make it fit as best you can,
  and report it as `LONG: id`.
- Honorifics stay, hyphenated: Neon-san, Sigma-kun, Obaba-sama, Yuriko-san. Given name first.
- Punctuation: 「」 -> "...", 【X】 -> [X] (keep brackets around key terms/Echo names), 《X》 -> <X>, …… -> ...,
  ！？ -> ?!, ～ -> ~. Full-width digits -> ASCII. "Ｑ．Ｅ．Ｄ．" -> "Q.E.D."
- Echo-get lines: `【X】 / の刻音を手に入れた！` -> `Obtained the [X] Echo!`. Glossary-add lines:
  `$c01【用語集】に / 項目が追加された$c00` -> `$c01A new entry was added to the [Glossary].$c00`.
- No ordinal suffix glued to a number ("1th"): write "No. 1", "the first", etc.
- Sound effects / stammers: "Wh-what?", "Ngh!", "Kyaaa!".

## Consistency
Never edit `glossary.md` or any file except your own output. For a recurring name or term not in the glossary,
pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
