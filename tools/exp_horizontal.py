"""Prototype: horizontal dialogue for the player. Font 04387 flags 3 -> 2, Latin upright, arm9 layout patches,
lines wrapped narrow. Out: build/exp3/h2.nds. argv: K (y start offset) WRAP (px)."""
import struct
import sys

import keystone
import ndspy.rom

sys.path.insert(0, 'H:/translation/sigma-hamonics/tools')
import build  # noqa: E402
import fit  # noqa: E402
import latin  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 56
WRAP = int(sys.argv[2]) if len(sys.argv) > 2 else 56

orig_glyphs = latin.glyphs


def glyphs(x):
    p = latin.params(x)
    if p['flags'] != 3:
        return orig_glyphs(x)
    out = {}
    for ch in latin.ASCII:
        rows, adv = latin.raster_ttf(ch, latin.DLG_TTF, latin.DLG_PX, p['w'], p['h'], p['base'], p['bpp'])
        out[ord(ch)] = (latin.pack(latin.orient(rows, 2, p['w'], p['h']), p['bpp'], p['size']), 0, p['w'], adv)  # blitter draws glyphWidth raw-x columns
        out[latin.fullwidth(ch)] = out[ord(ch)]
    return out


latin.glyphs = glyphs
orig_fonts = build.fonts


def fonts(c):
    out = orig_fonts(c)
    x = bytearray(out[4387][0])
    i = bytes(x).find(b'PLGC')
    x[i + 15] = 2
    out[4387] = (bytes(x), len(x))
    return out


build.fonts = fonts
fit.fit_dialogue = lambda s: fit.NL.join(fit.wrap(s.replace(fit.NL, ' '), WRAP))
if '--test' in sys.argv:  # opening lines 0-3 -> 58/62/75/95-char probes for the 60-record limit
    PROBE = 'Abcde fghij klmno pqrst uvwxy zabcd efghi jklmn opqrs tuvwx yzabc defgh ijklm nopqr stuvw'
    orig_load = build.text.load_script

    def load_script():
        s = orig_load()
        for i, n in enumerate((58, 62, 75, 95)):
            s[4086][i]['en'] = f'{n:02d}' + PROBE[2:n]
        return s
    build.text.load_script = load_script

ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)
PATCH = {
    0x200d3bc: 'ldr r0, [sp, #0x18]',      # canvas raw w = text height
    0x200d3c4: 'ldr r1, [sp, #0x14]',      # canvas raw h = text width
    0x200d778: 'cmp r0, #12',              # parser: up to 12 lines (was 3)
    0x200d4b8: 'mov r0, r0',               # no x nudge for narrow glyphs
    0x200d4c4: 'mov r0, r0',
    0x200d5ac: 'mov r1, #8',               # centre x: cell origin x = 8 + 8 - 16 = 0
    0x200d5b0: 'mov r2, fp',               # centre y = char width / 2
    0x200d88c: f'mov r0, #{K}',            # first line: y = base - K
    0x200d8d0: 'add r7, r7, #1',           # newline: x = x0 - 16 * line, y = base - K
    0x200d8d4: 'sub r0, sb, r7, lsl #4',
    0x200d8d8: 'str r0, [sl, #0x10]',
    0x200d8dc: f'mov r0, #{K}',
    0x200d8e0: 'sub r0, r5, r0',
    0x200d8e4: 'str r0, [sl, #0x14]',
    0x200d8e8: 'b 0x200d92c',
    0x200d920: 'ldr r1, [sl, #0x14]',      # per char: y += advance
    0x200d924: 'add r0, r1, r0',
    0x200d928: 'str r0, [sl, #0x14]',
}

build.BUILD = build.text.ROOT / 'build' / 'exp3'
build.main([])
src = build.BUILD / 'sigma_en.nds'
r = ndspy.rom.NintendoDSRom.fromFile(src)
a9 = bytearray(r.arm9)
for addr, asm in PATCH.items():
    enc, _ = ks.asm(asm, addr)
    assert len(enc) == 4, asm
    a9[addr - 0x02000000:addr - 0x02000000 + 4] = bytes(enc)
r.arm9 = bytes(a9)
r.saveToFile(build.BUILD / 'h2.nds')
print('patched', len(PATCH))
