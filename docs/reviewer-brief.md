# Translation reviewer brief - Sigma Harmonics

You review one batch of a JP->EN fan translation of Sigma Harmonics (NDS mystery RPG). Read-only: no edits, no git,
no subagents. Mechanical validity (ids, colour codes, ASCII, box width) is already enforced by the check tool -
judge translation quality.

## Inputs (paths in your dispatch)
- Pairs file `work/tl/<batch>.pairs.txt`: every translated entry as `>> id | JP` then `EN: ...`, with the 2 previous
  lines as context (`   id | JP / EN`). ` \n` in JP is a line break inside one box. Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md` (voices: Sigma, default Neon, Neon's costume
  voices, butler, Ouma, system text).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (one-letter slips are what players notice); honorifics kept and
  hyphenated; each Neon costume voice stays distinct and consistent.
- Continuity: sentences split across consecutive boxes must read in sequence.
- Things players caught that reviewers missed: jokes/wordplay losing their punch; ordinal suffix after a number
  ("1th"); abbreviated names or terms; stock phrases that read awkwardly in English ("... GET!").
- Naturalness: would a fan-translation reader stumble?

## Report (write it to `work/tl/<batch>.review.md` with your file-write tool, then reply with the same text)
### Issues
#### Critical (meaning reversed, wrong speaker, broken sense)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, voice break)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
