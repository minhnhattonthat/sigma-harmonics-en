# Contributing

Thanks for helping. Most contributions are one of these four; only the last two need the game ROM.

## 1. Report a problem

Open an issue with:
- a screenshot (DeSmuME: File > Save Screenshot As), the patch version, and what you expected;
- for bugs that are hard to reach, a savestate or save file (`.dsv`) helps a lot. Savestates only work with the exact
  build they were made with, so say which release or commit you used.

## 2. Fix a translation (no ROM needed)

1. Find the line: search `script/*.json` for the English (or Japanese) text. Each entry looks like
   `{"id": "04985:0164", "jp": "神自己回復", "en": "Divine Self-Heal"}`.
2. Edit only the `en` value. An empty `en` means the game shows the Japanese.
3. Follow `glossary.md`: names, terms and style rules there are binding. If a term is wrong or missing, change the
   glossary in the same pull request and say why.
4. Run the check and open a pull request:
   ```sh
   pip install -r requirements.txt
   python -X utf8 tools/check.py
   ```
   GitHub runs the same check on every pull request.

Rules the lint enforces:
- Plain ASCII only (no curly quotes or em dashes; use `--`).
- Keep every `$cNN` colour code, in order, around the matching words.
- Dialogue is wrapped automatically; don't add `\n` to dialogue. Menus and labels keep their `\n` line count.
- Width limits: the lint reports `line too wide` / `too long for the box`. Rephrase rather than abbreviate; if
  something truly can't fit, open an issue, since the engine can often be changed (wider box, two-line text).
- A character with no glyph in its font hangs the game; the lint's ASCII rule protects against that.

## 3. Build and test in an emulator (needs the ROM)

See "Build your own patched ROM" in the README. For scripted QA there is a headless DeSmuME driver:

- Put DeSmuME (0.9.13+, Windows x64) and the 64-bit `lua51.dll` in `tools/desmume/` (gitignored).
- `python -X utf8 .claude/skills/translate-retro-game/scripts/emu.py build/sigma_en.nds --out work/qa/smoke --route tools/routes/newgame.txt --shot-every 150 --smoke --sheet`
  boots a new game and writes screenshots plus a contact sheet. `--route-str "900 -;6 t128,96"` sends inputs
  (frames, then buttons or a touch at raw screen coordinates), `--state-in`/`--state-out` load and save states.
- The game is held sideways: screenshots are raw; rotate 90 degrees counter-clockwise to see what the player sees.

Optionally install the pre-commit hook so every commit runs the check: `cp tools/pre-commit .git/hooks/`
(with the venv active, or edit its `CHECK=` line to point at your Python).

## 4. Graphics and engine work

- Full-screen graphics: `font/screens*.json`, previewed with
  `python -X utf8 tools/scredit.py preview ID out.png` (see the docstring and `docs/graphics-brief.md`).
- Sprites: `font/sprites.json`, `python -X utf8 tools/sprite.py show|preview ID out.png [CELL...]`.
- Engine notes, addresses and what has been verified on screen: `docs/re/README.md`, `docs/re/verify.md`.
- Code style: match the surrounding code; new logic comes with a small test in `tests/`.

## Working with an AI coding agent

`CLAUDE.md` (and the `translate-retro-game` skill under `.claude/skills/`) give an agent the commands, rulings and
tools for this repo. Review its changes like any other pull request.
