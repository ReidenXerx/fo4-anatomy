"""Plain script (no pytest) exercising mucosa.paint() against real DXT1/BC5 skin maps and a synthetic
uncompressed 32-bit BGRA DDS. Prints PASS/FAIL per check; exits non-zero on any FAIL.

    python test_mucosa.py
"""
import io
import math
import sys

from PIL import Image, ImageChops, ImageStat

import genital_texture as gt
import mucosa

RECT = (0.55, 0.10, 0.95, 0.50)
REAL_DIR = (r'C:\Users\DuduPhudu\AppData\Local\Temp\claude\C--Users-DuduPhudu-Documents-Projects-vortex-mod-monitor'
            r'\a5e34b3d-529b-41d4-a1a1-743a8e4de9a9\scratchpad\realAtlas\Textures\Anatomy')
REAL_FILES = [
    (f'{REAL_DIR}\\FemaleBody_d.dds', 'colour', (150, 70, 70)),
    (f'{REAL_DIR}\\FemaleBody_n.dds', 'normal', (0, 0, 0)),
    (f'{REAL_DIR}\\FemaleBody_s.dds', 'specular', (180, 200)),
]

FAILS = 0


def check(name, cond):
    global FAILS
    if not cond:
        FAILS += 1
    print(f'{"PASS" if cond else "FAIL"} - {name}')
    return cond


def raw_bounds(w, h, rect):
    u0, v0, u1, v1 = rect
    x0 = max(0, min(w, math.floor(u0 * w)))
    x1 = max(0, min(w, math.ceil(u1 * w)))
    y0 = max(0, min(h, math.floor(v0 * h)))
    y1 = max(0, min(h, math.ceil(v1 * h)))
    return x0, y0, x1, y1


def expanded_bounds(w, h, rect, bw):
    x0, y0, x1, y1 = raw_bounds(w, h, rect)
    if bw == 1:
        return x0, y0, x1, y1
    px0, py0 = (x0 // 4) * 4, (y0 // 4) * 4
    px1, py1 = min(w, ((x1 + 3) // 4) * 4), min(h, ((y1 + 3) // 4) * 4)
    return px0, py0, px1, py1


def verify(label, dds_bytes, kind, base):
    """Runs paint() and every check for one DDS; returns the output bytes."""
    d = gt.Dds(label, dds_bytes)
    out = mucosa.paint(dds_bytes, RECT, kind, base)
    check(f'{label}: output length == input length', len(out) == len(dds_bytes))
    try:
        before = Image.open(io.BytesIO(dds_bytes)).convert('RGBA')
        after = Image.open(io.BytesIO(out)).convert('RGBA')
    except Exception as e:
        check(f'{label}: Image.open succeeds on the output', False)
        print(f'    ({e})')
        return out
    check(f'{label}: Image.open succeeds on the output', True)
    px0, py0, px1, py1 = expanded_bounds(d.w, d.h, RECT, d.bw)
    diff = ImageChops.difference(before, after)
    diff.paste((0, 0, 0, 0), (px0, py0, px1, py1))
    bbox = diff.getbbox()
    check(f'{label}: unchanged outside the rect\'s block-expanded bounds {(px0, py0, px1, py1)} '
          f'(residual bbox {bbox})', bbox is None)
    if kind == 'colour':
        x0, y0, x1, y1 = raw_bounds(d.w, d.h, RECT)
        region = after.crop((x0, y0, x1, y1)).convert('RGB')
        mean = ImageStat.Stat(region).mean
        expect = [b * 0.72 for b in base]
        ok = all(abs(mean[c] - expect[c]) <= 25 for c in range(3))
        check(f'{label}: colour mean {[round(m, 1) for m in mean]} within 25 of expected {expect}', ok)
    return out


def synth_level(size):
    im = Image.new('RGB', (size, size))
    px = im.load()
    for y in range(size):
        for x in range(size):
            px[x, y] = ((x * 7) % 256, (y * 13) % 256, (x + y) % 256)
    return im


def main():
    for path, kind, base in REAL_FILES:
        data = open(path, 'rb').read()
        verify(path, data, kind, base)

    levels = [synth_level(64), synth_level(32), synth_level(16)]
    synth_bytes = gt.uncompressed(levels)
    verify('synthetic uncompressed 32-bit BGRA', synth_bytes, 'colour', (150, 70, 70))

    print()
    if FAILS:
        print(f'FAIL - {FAILS} check(s) failed')
        sys.exit(1)
    print('PASS - all checks passed')


if __name__ == '__main__':
    main()
