"""The vaginal canal's lining, before (folds='across', A-54) and after (folds='rugae', 2026-10-07), as flat patches:
colour, the normal map, and colour lit from above by that normal (so the folds' relief shows). Base tone: a typical
introitus colour; size: the patch at a 4K body texture (205 around x 410 deep, here x2 for viewing).

    python studies/rugae_preview.py  -> D:/F4Output/rugae_preview.png
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mucosa  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

BASE = (176, 104, 98)         # an introitus-like tone
SPEC = (51, 23)
W, H = 205, 410


def patch(folds):
    col, nrm, lit = (Image.new('RGB', (W, H)) for _ in range(3))
    light = (0.0, -0.55, 0.835)                          # from "up the canal", a little above
    for y in range(H):
        t = (y + 0.5) / H
        for x in range(W):
            s = (x + 0.5) / W
            px = mucosa._pattern_pixel(s, t, 'colour', BASE, 0, 0, 1, 1, folds, mucosa_wet())
            pn = mucosa._pattern_pixel(s, t, 'normal', BASE, 0, 0, 1, 1, folds, mucosa_wet())
            col.putpixel((x, y), px[:3])
            nrm.putpixel((x, y), pn[:3])
            n = [(c / 127.5 - 1.0) for c in pn[:3]]
            k = max(0.15, n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
            lit.putpixel((x, y), tuple(min(255, int(c * k * 1.15)) for c in px[:3]))
    return col, nrm, lit


def mucosa_wet():
    return (72, 140)


if __name__ == '__main__':
    rows = [patch('across'), patch('rugae')]
    gap = 10
    sheet = Image.new('RGB', (3 * W * 2 + 4 * gap, 2 * H * 2 + 3 * gap + 40), (30, 30, 34))
    d = ImageDraw.Draw(sheet)
    for r, (label, imgs) in enumerate(zip(('BEFORE (A-54)', 'AFTER (rugae)'), rows)):
        y = gap + 30 + r * (H * 2 + gap)
        d.text((gap, y - 22), label + ':  colour | normal map | lit', fill=(230, 230, 230))
        for c, im in enumerate(imgs):
            sheet.paste(im.resize((W * 2, H * 2), Image.NEAREST), (gap + c * (W * 2 + gap), y))
    out = pathlib.Path(r'D:\F4Output\rugae_preview.png')
    sheet.save(out)
    print(out)
