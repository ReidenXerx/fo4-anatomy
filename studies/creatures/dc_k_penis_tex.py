"""Texture for the equine deathclaw penis (kassarawi's design: pink-mauve, darker veins, lighter flared head).
Laid out for dc_geom's tube UVs: u = around the shaft (0 = dorsal), v = LINING_V rows (slit floor flesh) and
SHAFT_V rows (inside end -> tip). Veins follow dk_male's wandering vein paths so paint and geometry agree.
    python -I dc_k_penis_tex.py <out_d.png> <out_n.png> [size]"""
import sys

import numpy as np
from PIL import Image, ImageFilter

out_d, out_n = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
LINING_V, SHAFT_V = (0.01, 0.09), (0.12, 0.995)
CL_LEN = 37.9                     # erect centreline length (dk_male run): the vein phase uses it
rng = np.random.default_rng(11)
u = (np.arange(N) + 0.5) / N
v = (np.arange(N) + 0.5) / N
U, Vv = np.meshgrid(u, v)                       # image row = v (nif v runs down the image)
t = np.clip((Vv - SHAFT_V[0]) / (SHAFT_V[1] - SHAFT_V[0]), 0, 1)
col = np.zeros((N, N, 3))
mauve, pink, glans, flesh = (np.array(c, float) for c in ((112, 58, 74), (168, 92, 104), (196, 112, 116),
                                                             (190, 78, 88)))
shade = np.clip((t - 0.05) / 0.35, 0, 1)[..., None]                    # darker toward the inside end
col[:] = mauve * (1 - shade) + pink * shade
head = np.clip((t - 0.84) / 0.04, 0, 1)[..., None]
col = col * (1 - head) + glans * head
ring = np.exp(-((t - 0.45) / 0.012) ** 2)[..., None]                   # the prepuce ring: a slightly darker band
col = col * (1 - 0.28 * ring)
# veins: three wandering lines on the shaft (same paths as the geometry)
th = U * 2 * np.pi
ln = t * CL_LEN
vein = np.zeros((N, N))
for c0, amp, ph in ((0.0, 1.0, 0.0), (1.15, 0.75, 1.7), (-1.15, 0.75, 3.1)):
    cth = c0 + 0.32 * np.sin(2 * np.pi * ln / 9.0 + ph)
    dth = (th - cth + np.pi) % (2 * np.pi) - np.pi
    vein = np.maximum(vein, amp * np.exp(-(dth / 0.07) ** 2))
vein *= ((t > 0.12) & (t < 0.85))
col = col * (1 - 0.55 * vein[..., None]) + np.array([86, 40, 74.0]) * 0.55 * vein[..., None]
# mottling
noise = Image.fromarray((rng.random((N // 8, N // 8)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)
noise = np.asarray(noise.filter(ImageFilter.GaussianBlur(N / 160)), float) / 255 - 0.5
col *= (1 + 0.10 * noise)[..., None]
# lining rows: wet flesh
lin = (Vv >= LINING_V[0] - 0.01) & (Vv <= LINING_V[1] + 0.01)
col[lin] = flesh * (1 + 0.08 * noise[lin])[:, None]
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(out_d)
# normal map from the vein + ring height (tangent space, gentle)
h = 0.9 * vein + 0.6 * ring[..., 0] + 0.15 * noise
gy, gx = np.gradient(h)
s = 6.0
nrm = np.dstack([-gx * s, -gy * s, np.ones_like(h)])
nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(out_n)
print('equine penis texture', out_d, out_n, N)
