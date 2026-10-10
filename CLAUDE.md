# Sigma Harmonics (NDS) English translation

Skill: translate-retro-game (H:/translation/sigma-hamonics/.claude/skills/translate-retro-game/SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root; `.venv` has ndspy, Pillow, pytest)
- Build:    `.venv/Scripts/python -X utf8 tools/build.py` -> build/sigma_en.nds (`--marker` id build, `--identity` check)
- Check:    `.venv/Scripts/python -X utf8 tools/check.py` (pytest + lint; pre-commit runs it, ~40 s)
- Extract:  `.venv/Scripts/python -X utf8 tools/text.py extract` (writes missing script/*.json only)
- Smoke:    `python -X utf8 .claude/skills/translate-retro-game/scripts/emu.py build/sigma_en.nds --out work/qa/smoke --route tools/routes/newgame.txt --shot-every 150 --smoke --sheet`
- Release:  not built yet (xdelta3 on PATH via scoop); never publish without the user.

## Paths
- Original ROM: `rom/Sigma Harmonics (Japan).nds` (gitignored, SHA-1 7b37857acc91704d05f3c90143cbf8e972c54ffd). Emulator: `tools/desmume/` (gitignored, lua51.dll beside exe).
- Text: `script/NNNNN.json` (one per CPK string table; `id`, `jp`, `en`). Glossary + rulings: `glossary.md`. RE notes: `docs/re/README.md`.
- Code: `tools/` cpk.py (CPK/@UTF/CRILAYLA), rom.py (NitroFS cpk swap), strtab.py, text.py, build.py, nftr.py (fonts).

## Rulings
- Honorifics kept, given name first. Romanisation: official/fan (chocomog257 guide) else Hepburn. Credits English. No abbreviations.
- Game is played sideways; dialogue font 04387 stores glyphs pre-rotated (CGLP flags 3).
- A character with no glyph in the active font HANGS the game. Every char used must exist in every font that draws it.

## Status
- Done: CPK/ROM identity rebuild, extract (362 tables, 12,685 strings), marker build boots.
- Next: engine spike = add Latin glyphs to fonts; marker tour; then translation batches.
