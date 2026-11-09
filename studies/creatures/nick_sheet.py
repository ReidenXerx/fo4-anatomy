"""Review sheet for the synth penis (Nick + every gen2 synth): ours at rest and erect, next to UAP's current one.
    python -I nick_sheet.py"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

S = pathlib.Path(r'D:\F4Output\creatures\nick\shots')
OUT = pathlib.Path(r'D:\F4Output\creatures\nick\nick_synth_review.jpg')
rows = [('OURS - flaccid', ['rest_gfront', 'rest_gside2']),
        ('OURS - erect (UAP/AAF "Erection" morph)', ['erect_gfront', 'erect_gside2']),
        ('UAP today (replaced)', ['uap_gfront', 'uap_gside2'])]
T = 520
try:
    font = ImageFont.truetype('arial.ttf', 26)
except OSError:
    font = ImageFont.load_default()
W = 2 * T + 3 * 12
H = sum(T + 50 for _ in rows) + 12
sheet = Image.new('RGB', (W, H), (24, 24, 27))
d = ImageDraw.Draw(sheet)
y = 12
for title, shots in rows:
    d.text((14, y), title, fill=(235, 235, 235), font=font)
    y += 38
    for i, s in enumerate(shots):
        im = Image.open(S / f'{s}.png').convert('RGB').resize((T, T))
        sheet.paste(im, (12 + i * (T + 12), y))
    y += T + 12
sheet.save(OUT, quality=90)
print(OUT, sheet.size, round(OUT.stat().st_size / 1e6, 2), 'MB')
