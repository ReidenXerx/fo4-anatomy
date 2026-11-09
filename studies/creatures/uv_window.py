"""Plainest w x h window (fractions) in a diffuse (+ optional normal) PNG.
    python -I uv_window.py <diffuse.png> [normal.png] [w h]"""
import sys

import numpy as np
from PIL import Image

d = np.asarray(Image.open(sys.argv[1]).convert('RGB'), float) / 255
n = np.asarray(Image.open(sys.argv[2]).convert('RGB'), float) / 255 if len(sys.argv) > 2 and sys.argv[2] != '-' else None
fw, fh = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.07, 0.13)
S = d.shape[0]
w, h = int(fw * S), int(fh * S)
lum = d.mean(2)
gy, gx = np.gradient(lum)
g = np.hypot(gx, gy)
skin = (d[..., 0] - d[..., 2]) > 0.05                 # warm skin pixels (UV background is neutral grey)
best = []
for y in range(0, S - h, 8):
    for x in range(0, S - w, 8):
        if skin[y:y + h, x:x + w].mean() < 0.999:
            continue
        s = lum[y:y + h, x:x + w].std() + 3 * g[y:y + h, x:x + w].mean()
        if n is not None:
            s += 2 * n[y:y + h, x:x + w, :2].std()
        best.append((s, x, y, lum[y:y + h, x:x + w].mean()))
best.sort()
for s, x, y, m in best[:6]:
    print(f'u {x / S:.3f}..{(x + w) / S:.3f}  v {y / S:.3f}..{(y + h) / S:.3f}  score {s:.4f}  mean {m:.3f}')
