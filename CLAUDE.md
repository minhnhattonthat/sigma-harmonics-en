# Sigma Harmonics (NDS) English translation

Skill: translate-retro-game (`.claude/skills/translate-retro-game/SKILL.md`). Read it before ROM, text or QA work.
Human contributors: README.md, CONTRIBUTING.md.

## Commands (run from repo root; venv with `pip install -r requirements.txt`; Windows: `.venv/Scripts/python`)
- Build:    `python -X utf8 tools/build.py` -> build/sigma_en.nds (`--marker` id build, `--identity` check)
- Check:    `python -X utf8 tools/check.py` (pytest + lint; pre-commit and GitHub CI run it; ROM tests skip without ROM)
- Extract:  `python -X utf8 tools/text.py extract` (writes missing script/*.json only)
- Smoke:    `python -X utf8 .claude/skills/translate-retro-game/scripts/emu.py build/sigma_en.nds --out work/qa/smoke --route tools/routes/newgame.txt --shot-every 150 --smoke --sheet`
- Release:  `python -X utf8 tools/release.py X.Y` (xdelta3 on PATH; re-applies and compares) -> release/*.zip with
  docs/release-readme.md. Never publish, push or upload without the maintainer's say-so.

## Paths
- Original ROM: `rom/Sigma Harmonics (Japan).nds` (gitignored, SHA-1 7b37857acc91704d05f3c90143cbf8e972c54ffd). Emulator: `tools/desmume/` (gitignored, lua51.dll beside exe).
- Text: `script/NNNNN.json` (one per CPK string table; `id`, `jp`, `en`). Glossary + rulings: `glossary.md`. RE notes: `docs/re/README.md`.
- Table metadata (form, font per table): `tools/tables.json` (committed; regenerate with `tools/batches.py meta`, needs ROM).
- Code: `tools/` cpk.py (CPK/@UTF/CRILAYLA), rom.py (NitroFS cpk swap), strtab.py, text.py, build.py, nftr.py (fonts),
  scredit.py (screens, font/screens*.json), sprite.py (sprite cells, font/sprites.json), dlgfont.py (dialogue + arm9
  PATCH), gridfont.py (two-line skill names).
- Load an end-game save: title t128,96 x2, Continue t93,110, slot t195,78, Yes t155,88, tap. Savestates go stale after
  any rebuild that changes file sizes (they hang on the loading screen).

## Rulings
- Honorifics kept, given name first. Romanisation: official/fan (chocomog257 guide) else Hepburn. Credits English. No abbreviations.
- Game is played sideways; dialogue bubbles read left-to-right for the player via tools/dlgfont.py (font flags 2,
  arm9 patch, chunk glyphs). Bubble = 62 px x 12 lines, max 60 glyph records (else crash). RE: docs/re/README.md.
- A character with no glyph in the active font HANGS the game. Every char used must exist in every font that draws it.
- Renderer quirks + fixes: docs/re/README.md (UI tables full-width; dialogue 0x50-0x5F full-width; spaces U+2002).
- Batches: `tools/batches.py split|check|merge|pairs`; briefs docs/translator-brief.md, docs/reviewer-brief.md;
  style docs/style-reference.md. Echo names: `tools/echoes.py` -> build/echoes.tsv. Bisect a hang: tools/bisect_text.py.

## Status
- v0.9 beta released (GitHub minhnhattonthat/sigma-harmonics-en). Verified in game: opening, field menus, notebook,
  save/load, Descent grid, first battle (docs/re/verify.md).
- Open: later chapters and other battles unseen; "Hidden Movement III" Notebook button unseen.
  Marker build (--marker) does not apply dlgfont or gridfont.
