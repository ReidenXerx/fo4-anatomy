"""Generic review sheet: rows of labelled renders, 3 per row.
    python -I make_sheet.py <out.jpg> "Row title" <png>::<caption> <png>::<caption> ... [--row "Next title" ...]"""
import sys

from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
rows, cur = [], None
args = sys.argv[2:]
i = 0
while i < len(args):
    a = args[i]
    if a == '--row':
        cur = None
        i += 1
        continue
    if '::' not in a:
        cur = (a, [])
        rows.append(cur)
    else:
        p, cap = a.split('::', 1)
        cur[1].append((p, cap))
    i += 1
T = 420
try:
    font = ImageFont.truetype('arial.ttf', 24)
    small = ImageFont.truetype('arial.ttf', 18)
except OSError:
    font = small = ImageFont.load_default()
W = 3 * T + 4 * 12
H = len(rows) * (T + 76) + 12
sheet = Image.new('RGB', (W, H), (24, 24, 27))
d = ImageDraw.Draw(sheet)
y = 12
for title, shots in rows:
    d.text((14, y), title, fill=(235, 235, 235), font=font)
    y += 34
    for k, (p, cap) in enumerate(shots[:3]):
        im = Image.open(p).convert('RGB').resize((T, T))
        x = 12 + k * (T + 12)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + T + 4), cap, fill=(190, 190, 195), font=small)
    y += T + 42
sheet.save(out, quality=88)
print(out, sheet.size)
