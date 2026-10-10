# Fixer brief - Sigma Harmonics

You apply one reviewer report to the merged English. Work only on the batch in your dispatch. No subagents.

## Read
1. `work/tl/<batch>.review.md` - the reviewer's findings (Critical / Important / Minor).
2. `work/tl/<batch>.pairs.txt` - JP and current EN with context (`>> id | JP` then `EN:`).
3. `glossary.md` (rulings + "Decisions from earlier batches") and `docs/style-reference.md`.

## Do
- Fix every Critical and Important item. Fix Minor items too when the suggestion is clearly better and faithful;
  skip style nits you disagree with. Re-read the JP yourself: the reviewer can be wrong; don't apply a "fix"
  that makes the meaning worse.
- Settled forms win: Master Key (capitalised), ではでは -> "Then, then", はてな -> "Question mark?",
  時の変革者 -> Changer of Time, 過去の変革者 -> Changer of the Past, Nの刻 -> "N:00", -fuu tic, "Age of the Gods".
- Do NOT rename an Echo (the [X] in "Obtained the [X] Echo!" and Echo-list names): Echo names are shared across
  many tables. If a review says an Echo name is wrong, leave it and report `ECHO: jp -> suggested en`.
- Keep colour codes ($cNN) in place, plain ASCII, dialogue without `\n`.

## Output
Write `work/tl/<batch>.fix.tsv` with your file-write tool: `id<TAB>new English`, only the lines you change.
Then run `.venv/Scripts/python -X utf8 tools/batches.py apply <batch>.fix` from the repo root. It writes nothing
if any line fails (width, codes, glossary); fix those lines and run it again until it prints `apply ...: N lines written`.
For a dialogue line, `.venv/Scripts/python -X utf8 tools/fit.py "text"` shows the wrap first.

## Report (reply with only this)
`<batch>: N lines changed`; then `ECHO: ...` lines and `SKIPPED: id - why` for review items you didn't apply.
