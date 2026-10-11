# Sigma Harmonics English translation

Unofficial English fan translation of **Sigma Harmonics** (Nintendo DS, Square Enix, 2008): the source text, tools and
graphics recipes that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

## What's here

| Path | What it is |
|---|---|
| `script/NNNNN.json` | Every text table of the game: `id`, original `jp`, translated `en`. This is where translation fixes go. |
| `glossary.md` | Binding names, terms and style rules. |
| `font/screens*.json`, `font/sprites.json`, `font/textures.json` | Recipes that redraw Japanese text in graphics with English. |
| `tools/` | Python build chain: CPK archive, string tables, fonts, graphics, the arm9 patches, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes (text engine, layout, what's been verified in game). |
| `docs/` | Briefs and style reference used for translating and reviewing. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/sigma-harmonics-en
cd sigma-harmonics-en
python -m venv .venv && .venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# copy your dump to: rom/Sigma Harmonics (Japan).nds
#   (134,217,728 bytes, SHA-1 7b37857acc91704d05f3c90143cbf8e972c54ffd)
python -X utf8 tools/build.py                          # -> build/sigma_en.nds (about 2 minutes)
python -X utf8 tools/check.py                          # tests + text lint
```

To package an xdelta patch like the released one (needs `xdelta3` on PATH):

```sh
python -X utf8 tools/release.py 1.0                    # -> release/Sigma_Harmonics_EN_v1.0.zip
```

The build is deterministic: the same sources and ROM give the same patch.

## Contributing

Translation fixes, bug reports with screenshots and engine work are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## How the patch works (short version)

- The game's text lives in UTF-8 string tables inside `data.cpk`; the build rewrites them and repacks the CPK.
- Japanese fonts get Latin glyphs added; UI text uses full-width code points because some UI routines only step
  3-byte UTF-8.
- The game is held sideways, and its dialogue bubbles drew text top-to-bottom. A small arm9 patch
  (`tools/dlgfont.py`) makes them run left-to-right, with English packed into multi-letter glyphs to stay under the
  bubble's 60-glyph limit.
- Skill names too long for their 62 px slot are drawn as two lines of a tiny pixel font (`tools/gridfont.py`).
- Graphics with Japanese text are redrawn from the recipes in `font/` (`tools/scredit.py`, `tools/sprite.py`).

Details: [docs/re/README.md](docs/re/README.md).

## Licence

Tools and English translation: MIT, see [LICENSE](LICENSE). The bundled fonts keep their own licences
(`font/LICENSE-DejaVu.txt`, `font/LICENSE-STIX.txt`). The original Japanese text in `script/` (the `jp` fields) is
Square Enix's and is included only so the translation can be checked against it.
Sigma Harmonics is (c) Square Enix / Think Garage; this project is not affiliated with them. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic) and has not yet been proofread by a native
speaker of both languages. Corrections are very welcome.
