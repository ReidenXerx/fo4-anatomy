"""Find texture windows for Nick's synth penis UVs: a plain window in the synth skin (clean AND dirty diffuse plus the
normal map, so no plate seams cross it) and a dark, even window in the endoskeleton texture (rubber joints).
Also checks the window holds no body UVs that pass through it in a misleading way (it may; reuse is fine).
    python -I nick_uvregion.py"""
import pathlib
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
PNG = pathlib.Path(r'D:\F4Output\creatures\nick\png')


def load(name):
    return np.asarray(Image.open(PNG / name).convert('RGB'), float) / 255.0


def window_scores(img, w, h, step=8):
    """(score map, positions): std of luminance + gradient energy over each w x h window (pixels)."""
    lum = img.mean(2)
    gy, gx = np.gradient(lum)
    g = np.hypot(gx, gy)
    out = []
    H, W = lum.shape
    for y in range(0, H - h, step):
        for x in range(0, W - w, step):
            win = lum[y:y + h, x:x + w]
            out.append((win.std() + 3 * g[y:y + h, x:x + w].mean(), win.mean(), x, y))
    return out


skin = load('gen2skin_d.png')
dirty = load('gen2skindirty_d.png')
nrm = load('gen2skin_n.png') if (PNG / 'gen2skin_n.png').exists() else None
S = skin.shape[0]
w, h = int(0.07 * S), int(0.13 * S)
a = {(x, y): s for s, m, x, y in window_scores(skin, w, h)}
b = {(x, y): s for s, m, x, y in window_scores(dirty, w, h)}
c = {(x, y): s for s, m, x, y in window_scores(nrm, w, h)} if nrm is not None else {}
best = sorted(((a[k] + b[k] + c.get(k, 0), k) for k in a))[:5]
for s, (x, y) in best:
    print(f'skin window u {x / S:.3f}..{(x + w) / S:.3f}  v {y / S:.3f}..{(y + h) / S:.3f}  score {s:.4f}')
syn = load('gen2synth_d.png')
w2, h2 = int(0.035 * S), int(0.10 * S)
cands = [(s + 2.0 * m, m, x, y) for s, m, x, y in window_scores(syn, w2, h2) if m < 0.16]
for s, m, x, y in sorted(cands)[:5]:
    print(f'rubber window u {x / S:.3f}..{(x + w2) / S:.3f}  v {y / S:.3f}..{(y + h2) / S:.3f}  mean {m:.3f} score {s:.4f}')
