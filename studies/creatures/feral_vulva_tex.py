"""Female feral vulva inner (run 6: the dark wound strip read as skin): Textures\\Anatomy\\Creatures\\
FeralVulvaInner_d/n/s.dds - wet pink-red mucosa, a darker opening down the middle (UV u = 0.5, v 0.15..0.85) - and
Materials\\Anatomy\\Creatures\\FeralVulvaInner.bgsm = our FeralStumpWound.bgsm with the texture names swapped (same
length, byte copy).  python -I feral_vulva_tex.py <wound bgsm> <out Data dir>"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ghoul_common as gc  # noqa: E402

SRC, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
N = 256
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
u, v = (xx + 0.5) / N, (yy + 0.5) / N
p = np.stack([u.ravel() * 6, v.ravel() * 6, np.zeros(N * N)], -1).astype(np.float32)
mott = gc.fbm(p, 4, 71).reshape(N, N)
fine = gc.fbm(p * 4, 3, 72).reshape(N, N)
open_ = np.exp(-((u - 0.5) / 0.035) ** 2) * gc.smoothstep(0.15, 0.25, v) * gc.smoothstep(0.85, 0.75, v)
pink = np.array([0.70, 0.33, 0.35], np.float32)
deep = np.array([0.36, 0.08, 0.11], np.float32)
col = pink * (0.85 + 0.25 * mott)[..., None] * (0.96 + 0.06 * fine)[..., None]
col = col + (deep - col) * open_[..., None] * 0.85
d = np.concatenate([(np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), np.full((N, N, 1), 255, np.uint8)], -1)
h = 0.25 * mott + 0.08 * fine - 0.6 * open_
gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 2.0
gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 2.0
n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)
nn = np.zeros((N, N, 4), np.uint8)
nn[..., 0] = (n[..., 0] * 127.5 + 127.5).astype(np.uint8)
nn[..., 1] = (n[..., 1] * 127.5 + 127.5).astype(np.uint8)
nn[..., 2] = (n[..., 2] * 127.5 + 127.5).astype(np.uint8)
nn[..., 3] = 255
ss = np.zeros((N, N, 4), np.uint8)
ss[..., 0] = ((0.50 + 0.1 * fine) * 255).astype(np.uint8)          # wet
ss[..., 1] = ((0.85 - 0.1 * mott) * 255).clip(0, 255).astype(np.uint8)
ss[..., 3] = 255
work = pathlib.Path(r'D:\F4Output\creatures\feral\work_vulva\tex')
for arr, kind, fmt in ((d, 'd', 'BC7_UNORM'), (nn, 'n', 'BC5_UNORM'), (ss, 's', 'BC5_UNORM')):
    gc.array_to_dds(arr, fmt, OUT / 'textures/anatomy/creatures' / f'FeralVulvaInner_{kind}.dds', work)
b = SRC.read_bytes()
nb = b.replace(b'FeralStumpWound', b'FeralVulvaInner')
if nb.count(b'FeralVulvaInner') != 3:
    raise SystemExit(f'expected 3 texture names, found {nb.count(b"FeralVulvaInner")}')
dst = OUT / 'materials/anatomy/creatures/FeralVulvaInner.bgsm'
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(nb)
print('vulva inner textures + bgsm', dst)
