"""Lint every translated line in script/*.json: ASCII/font chars, colour codes, box fit, glossary, ordinals,
no leftover Japanese. Prints errors and a count; exit 1 on any error."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402
import text  # noqa: E402

KANA = re.compile('[぀-ヿ一-鿿]')


def main():
    script = text.load_script()
    m = batches.load_meta()
    terms = batches.glossary()
    errs, done, total = [], 0, 0
    for fid, rows in script.items():
        for r in rows:
            if not r['en'] and '…' in r['jp']:  # punctuation-only lines are not "text", but untranslated they draw vertical
                errs.append(f"{r['id']}: '…' line has no English (use ...)")
            if not batches.is_text(r['jp']):
                continue
            total += 1
            if not r['en']:
                continue
            done += 1
            exempt = r['id'].startswith(batches.TERM_EXEMPT)
            for e in batches.errors(r, r['en'], m[fid]) + ([] if exempt else batches.term_errors(r['jp'], r['en'], terms)):
                errs.append(f"{r['id']}: {e}")
            if KANA.search(r['en']):
                errs.append(f"{r['id']}: Japanese left in English")
    for e in errs[:200]:
        print(e)
    print(f'lint: {done}/{total} translated, {len(errs)} errors')
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
