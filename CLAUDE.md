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
- Game is played sideways; dialogue bubbles read left-to-right for the player via tools/dlgfont.py (font flags 2,
  arm9 patch, chunk glyphs). Bubble = 62 px x 12 lines, max 60 glyph records (else crash). RE: docs/re/README.md.
- A character with no glyph in the active font HANGS the game. Every char used must exist in every font that draws it.

- Renderer quirks + fixes: docs/re/README.md (UI tables full-width; dialogue 0x50-0x5F full-width; spaces U+2002).
- Batches: `tools/batches.py split|check|merge|pairs`; briefs docs/translator-brief.md, docs/reviewer-brief.md;
  style docs/style-reference.md. Echo names: `tools/echoes.py` -> build/echoes.tsv. Bisect a hang: tools/bisect_text.py.

## Status
- Done: engine, 53 batches translated + reviewed, all graphics groups (font/screens*.json), credits verified,
  horizontal dialogue bubbles (opening QA'd).
- Next: QA other screens that draw with font 04387 (its direction flipped), in-game UI widths (docs/re/verify.md),
  release (xdelta). Marker build (--marker) does not apply dlgfont.
