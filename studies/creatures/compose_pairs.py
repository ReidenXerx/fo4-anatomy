"""Soft | erect pair images per creature and view (same camera both sides), plus a contact sheet for review.
    python -I compose_pairs.py <renders_pairs root>"""
import pathlib
import sys

from PIL import Image

root = pathlib.Path(sys.argv[1])
pairs = []
for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith('_')):
    for soft in sorted(d.glob('*-soft_*.jpg')):
        erect = soft.with_name(soft.name.replace('-soft_', '-erect_'))
        if not erect.exists():
            continue
        a, b = Image.open(soft).convert('RGB'), Image.open(erect).convert('RGB')
        im = Image.new('RGB', (a.width + b.width + 12, max(a.height, b.height)), (40, 40, 42))
        im.paste(a, (0, 0))
        im.paste(b, (a.width + 12, 0))
        dst = d / soft.name.replace('-soft_', '-pair_')
        im.save(dst, quality=90)
        pairs.append(dst)
sheet = [Image.open(p).resize((480, 236)) for p in pairs]
cols = 3
c = Image.new('RGB', (cols * 480, ((len(sheet) + cols - 1) // cols) * 236))
for i, im in enumerate(sheet):
    c.paste(im, ((i % cols) * 480, (i // cols) * 236))
(root / '_work').mkdir(exist_ok=True)
c.save(root / '_work' / 'pairs_contact.jpg', quality=85)
print(len(pairs), 'pairs')
