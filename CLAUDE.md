# Sigma Harmonics (NDS) English translation

Skill: translate-retro-game (plugin, enabled in .claude/settings.json; <skill> = its folder, or $RETRO_SKILL). Read it before ROM, text or QA work.
Human contributors: README.md, CONTRIBUTING.md.

## Commands (run from repo root; venv with `pip install -r requirements.txt`; Windows: `.venv/Scripts/python`)
- Build:    `python -X utf8 tools/build.py` -> build/sigma_en.nds (`--marker` id build, `--identity` check)
- Check:    `python -X utf8 tools/check.py` (pytest + lint; pre-commit and GitHub CI run it; ROM tests skip without ROM)
- Extract:  `python -X utf8 tools/text.py extract` (writes missing script/*.json only)
- Smoke:    `python -X utf8 <skill>/scripts/emu.py build/sigma_en.nds --out work/qa/smoke --route tools/routes/newgame.txt --shot-every 150 --smoke --sheet`
- Debug:    `python -X utf8 tools/debug/tour.py [TABLE..]` plays dialogue events from a cold boot (no save) ->
  work/qa/events/<table>/sheet.png + report.tsv (rows shown/total); `--rooms [N..]` warps to rooms. See tools/debug/.
- Release:  `python -X utf8 tools/release.py X.Y` (xdelta3 on PATH; re-applies and compares) -> release/*.zip with
  docs/release-readme.md. Never publish, push or upload without the maintainer's say-so.

## Paths
- Original ROM: `rom/Sigma Harmonics (Japan).nds` (gitignored, SHA-1 7b37857acc91704d05f3c90143cbf8e972c54ffd). Emulator: DeSmuME QA fork in `tools/desmume/` (gitignored; `scripts/fetch_emu.py desmume` =
  github.com/minhnhattonthat/desmume qa-2: headless, own ini per run, parallel-safe). Stock build kept in work/desmume-stock.
- Text: `script/NNNNN.json` (one per CPK string table; `id`, `jp`, `en`). Glossary + rulings: `glossary.md`. RE notes: `docs/re/README.md`.
- Table metadata (form, font per table): `tools/tables.json` (committed; regenerate with `tools/batches.py meta`, needs ROM).
- Code: `tools/` cpk.py (CPK/@UTF/CRILAYLA), rom.py (NitroFS cpk swap), strtab.py, text.py, build.py, nftr.py (fonts),
  scredit.py (screens, font/screens*.json), sprite.py (sprite cells, font/sprites.json), dlgfont.py (dialogue + arm9
  PATCH), gridfont.py (two-line skill names).
- Load a save: `--sav F.dsv --route tools/routes/continue.txt`. Make one without playing: tools/debug/capture.lua +
  mksave.py (card +0xa = room). Savestates go stale after any rebuild that changes file sizes (hang on loading).

## Rulings
- Honorifics kept, given name first. Romanisation: official/fan (chocomog257 guide) else Hepburn. Credits English. No abbreviations.
- Game is played sideways; dialogue bubbles read left-to-right for the player via tools/dlgfont.py (font flags 2,
  arm9 patch, chunk glyphs). Bubble = 62 px x 12 lines, max 60 glyph records (else crash). RE: docs/re/README.md.
- A character with no glyph in the active font HANGS the game. Every char used must exist in every font that draws it.
- Renderer quirks + fixes: docs/re/README.md (UI tables full-width; dialogue 0x50-0x5F full-width; spaces U+2002).
- Batches: `tools/batches.py split|check|merge|pairs`; briefs docs/translator-brief.md, docs/reviewer-brief.md;
  style docs/style-reference.md. Echo names: `tools/echoes.py` -> build/echoes.tsv. Bisect a hang: tools/bisect_text.py.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update the Status section.

## Status
- v0.9 beta released (GitHub minhnhattonthat/sigma-harmonics-en). Verified in game: opening, field menus, notebook,
  save/load, Descent grid, first battle (docs/re/verify.md).
- Open: later chapters and other battles unseen; "Hidden Movement III" Notebook button unseen.
  Marker build (--marker) does not apply dlgfont or gridfont.
