# Sigma Harmonics (Nintendo DS) - English patch v0.9.1 (beta)

Unofficial fan translation of **Sigma Harmonics** (シグマ ハーモニクス, Square Enix / Think Garage, 2008) into English.
This is a patch only. It contains no game data; you need your own dump of the Japanese game.

## What is translated
- All dialogue, menus, notebook, skill and Echo names, location names, tutorials and system text
- Full-screen and sprite graphics that contained text: chapter and time cards, title screen, Super Reasoning menus,
  battle labels, Notebook buttons, the staff credits
- Dialogue bubbles are laid out left-to-right for the way the game is held (sideways, like a notebook), instead of the
  Japanese top-to-bottom column

## How to apply
1. You need the Japanese ROM: `Sigma Harmonics (Japan).nds`
   - size 134,217,728 bytes
   - CRC32 `81c7d250`
   - MD5 `721cf278bf87208f35ab77d51b1459c0`
   - SHA-1 `7b37857acc91704d05f3c90143cbf8e972c54ffd`
2. Apply `Sigma_Harmonics_EN_v0.9.1.xdelta` with an xdelta patcher (xdelta3 command line, [xdelta UI](https://www.romhacking.net/utilities/598/), Delta Patcher):
   `xdelta3 -d -s "Sigma Harmonics (Japan).nds" Sigma_Harmonics_EN_v0.9.1.xdelta "Sigma Harmonics (English).nds"`
3. The patched ROM should be: CRC32 `0322fc69`, MD5 `626cfb3d9e406c70abfa778968401b1a`,
   SHA-1 `8550cfa475e05341d093562fe5c2bcad326d2ee2`.

Start a **new game or load a save** with the patched ROM. Existing save files work (checked with an end-game save);
savestates made with another build do not.

## Changes in v0.9.1
- Battle: the player's skill name now shows in the top-screen action banner (it was blank), in a narrower font so
  every name fits; skill names under the battle cards are centred again.
- Dialogue: the page cursor sits alone on its own line, centred under the text; no more stray gaps or squeezed spaces between letters.
- Ellipsis-only lines ("...", "...?", "...!!") were left in Japanese and showed as vertical dots; now English.

## Tested on
DeSmuME 0.9.14 (x64, JIT on and off). Not tested on real hardware or other emulators.

## Known issues (beta)
- Skill names on the Descent grid and under the battle cards that are too wide for one line are shown on two lines of a
  tiny capital-letter font; it is readable but small. Names that fit stay normal.
- Checked in-game: the opening, field menus, notebook, save/load, the Descent screen and the first battle. Later chapters,
  other battles and the rarely used screens have not all been seen, so a wrong-sized box or a leftover Japanese label is
  possible. Please report them with a screenshot.
- Not verified on screen: the "Hidden Movement III" Notebook button.
- A character with no glyph in a font can hang the game; every character the English text uses was added to the fonts.

## Credits
- Translation, ROM tool-chain and QA: minhnhattonthat, with extensive AI assistance (Claude by Anthropic) for translation drafts, the
  patching tools and testing. The translation was machine-assisted and has not been proofread by a native speaker.
- Romanisation of names follows official / fan sources (the chocomog257 guide), otherwise Hepburn.
- Staff credits in the patch are English transliterations checked against a published credits list.
- Sigma Harmonics is (c) Square Enix / Think Garage. This project is not affiliated with them. Please buy the game.
  Do not distribute patched ROMs.
