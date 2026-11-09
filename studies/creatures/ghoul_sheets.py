"""Before/after sheets from the Blender shots: one image per sex per view pair, labelled.
    python -I ghoul_sheets.py"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

S = pathlib.Path(r'D:\F4Output\ghoulskin\render\shots')
OUT = pathlib.Path(r'D:\F4Output\ghoulskin\render\sheets')
OUT.mkdir(parents=True, exist_ok=True)
try:
    FONT = ImageFont.truetype('arial.ttf', 28)
except OSError:
    FONT = ImageFont.load_default()


def sheet(sex, views, name, h=900):
    tiles = []
    for v in views:
        for when in ('before', 'after'):
            im = Image.open(S / f'{sex}_{when}_{v}.png').convert('RGB')
            im = im.resize((int(im.width * h / im.height), h))
            d = ImageDraw.Draw(im)
            d.text((14, 10), f'{"TODAY" if when == "before" else "NEW"} - {v}', fill=(255, 255, 255), font=FONT)
            tiles.append(im)
    w = sum(t.width for t in tiles) + 8 * (len(tiles) - 1)
    out = Image.new('RGB', (w, h), (20, 20, 22))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + 8
    out.save(OUT / f'{name}.jpg', quality=88)
    return OUT / f'{name}.jpg'


for sex, tag in (('F', 'women'), ('M', 'men')):
    print(sheet(sex, ['front', 'back'], f'ghoul_{tag}_full'))
    print(sheet(sex, ['face', 'neckback'], f'ghoul_{tag}_head'))
    print(sheet(sex, ['torso', 'crotch'], f'ghoul_{tag}_torso_crotch'))
