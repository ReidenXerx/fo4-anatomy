"""Review sheet for the canine genitals: rows of labelled renders.  python -I canine_sheet.py"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

S = pathlib.Path(r'D:\F4Output\creatures\canine\final8')
OUT = pathlib.Path(r'D:\F4Output\creatures\canine\canine_genitals_review.jpg')
rows = [('Dogmeat / dogs / wolves (same piece, fitted per body)',
         [('dog_qunder', 'rest, from below'), ('dogE_qside', 'erect'), ('dogE_qfront', 'erect: knot in the sheath')]),
        ('Vicious dog (placed on ITS pelvis)',
         [('vic_qside', 'rest'), ('vicE_qside', 'erect: sheath pulled back'), ('uapvicE_qside', 'UAP today (grey): too far back')]),
        ('FEV hound', [('fev_qside', 'rest'), ('fevE_qside', 'erect'), ('uapdogE_qside', 'UAP dog today (grey)')])]
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
    for i, (s, cap) in enumerate(shots):
        im = Image.open(S / f'{s}.png').convert('RGB').resize((T, T))
        x = 12 + i * (T + 12)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + T + 4), cap, fill=(190, 190, 195), font=small)
    y += T + 42
sheet.save(OUT, quality=88)
print(OUT, sheet.size, round(OUT.stat().st_size / 1e6, 2), 'MB')
