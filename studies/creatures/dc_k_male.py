"""Male deathclaw genitals after kassarawi's design (Dudu 11-12; her Unity video: an equine penis - a thick sheath
collar at the base, a second (prepuce) ring along the shaft, veined shaft, flared head, blunt tip; no scrotum).
dc_geom.py's male machinery is kept as is - UAP's centrelines for every AAF morph (Erection, Erection Up/Down,
Length, Penis Adjust, Scale), the same shape names (Base, Penis), skin UVs and weights from the body - only the
look changes:
  Base   the vent lips -> a round, puffy SHEATH collar around the root (skin, body UVs)
  Penis  radius_profile -> equine (ring at 45 %, neck, flared head, blunt tip); tube detail -> a few veins and a
         ventral ridge instead of ribs and nub rows
    python -I dc_k_male.py <geom_male.json>"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / 'dc_geom.py').read_text(encoding='utf-8')
a = src.index('# ================================================================ MALE')
b = src.index('# ================================================================ FEMALE')
out = sys.argv[1]
sys.argv = [str(HERE / 'dc_geom.py'), out]
exec(compile(src[:a], str(HERE / 'dc_geom.py'), 'exec'))


def radius_profile(t):            # noqa: F811  (dc_geom's reptilian profile replaced)
    """equine, UAP-erect units: base inside the body, prepuce ring, even shaft, neck, flared head, blunt tip"""
    xs = [0.0, 0.10, 0.20, 0.40, 0.43, 0.46, 0.49, 0.52, 0.70, 0.84, 0.865, 0.90, 0.94, 0.97, 0.99, 1.0]
    ys = [3.4, 3.5, 3.45, 3.4, 3.75, 4.35, 3.75, 3.4, 3.3, 3.2, 3.0, 4.4, 4.2, 3.4, 2.0, 0.0]
    return np.interp(t, xs, ys)


def tube(state, rest_shrink=1.0, inset=None):    # noqa: F811
    C, L, rk = curve_for(state)
    if state == 'E+Scale':
        rk = 1.33
    T_, U, X = frame_along(C)
    total = L[-1]
    nr = int(round(CL_LEN / RING_STEP))
    ts = np.linspace(0.0, 1.0, nr + 1)
    V = []
    for t in ts:
        li = t * total
        k = min(np.searchsorted(L, li), len(C) - 1)
        p, uu, xx = C[k], U[k], X[k]
        if inset is not None:
            p = p + inset
        base = radius_profile(t) * rk * rest_shrink
        ln = t * CL_LEN                                         # detail phase in E units (same in every state)
        for j in range(NSEG + 1):
            th = 2 * np.pi * j / NSEG                           # 0 = dorsal, pi = ventral
            r = base
            if 0.12 < t < 0.85:
                g = np.exp(-(((th - np.pi) / 0.32) ** 2))
                r *= 1 + 0.05 * g                               # ventral (urethral) ridge
                for c0, amp, ph in ((0.0, 0.17, 0.0), (1.15, 0.12, 1.7), (-1.15, 0.12, 3.1)):
                    cth = c0 + 0.32 * np.sin(2 * np.pi * ln / 9.0 + ph)        # veins wander along the shaft
                    dth = (th - cth + np.pi) % (2 * np.pi) - np.pi
                    r += amp * (base / 3.5) * np.exp(-(dth / 0.13) ** 2)
            sx, sz = np.sin(th), np.cos(th)
            V.append(p + r * (sz * uu + sx * xx))
    return np.array(V), ts


male_src = src[a:b]
for old, new in (
        ('MALE = dict(a0=5.6, b0=0.35, L=8.6, W=4.6, H=1.35, s_c=S_E - 0.4)',
         'MALE = dict(a0=R_SHEATH, b0=0.9, L=R_SHEATH + 5.5, W=5.4, H=3.2, s_c=S_E)'),
        ('R_ROOT = float(radius_profile(0.12)) + 0.35',
         'R_ROOT = float(radius_profile(0.12)) + 0.35\nR_SHEATH = R_ROOT + 0.4'),
        ('    return max(0.0, R_ROOT * np.sqrt(max(0.0, 1 - ((s - S_E) / 6.0) ** 2)))',
         '    return max(0.0, (R_ROOT - 0.4) * np.sqrt(max(0.0, 1 - ((s - S_E) / R_SHEATH) ** 2)))'),
):
    assert male_src.count(old) == 1, old
    male_src = male_src.replace(old, new)
# R_SHEATH is used by MALE, which comes first in the section: define it up front
male_src = 'R_SHEATH = float(radius_profile(0.12)) + 0.75\n' + male_src
exec(compile(male_src, str(HERE / 'dc_geom.py') + ' (male, equine)', 'exec'))

# v2 (kassarawi 11-12): the skin around the genitals one tone darker. The sheath skin takes the body's own vertex
# colours (the engine multiplies them in) darkened toward the opening; the rim matches the body
import json  # noqa: E402
import struct  # noqa: E402
DARK = 0.20
_off = ((bs.desc >> 24) & 0xF) * 4
GREY = np.array([struct.unpack_from('<B', bs.nif.b, bs.data_at + i * bs.stride + _off)[0]
                 for i in range(bs.count)], float) / 255.0
G = json.load(open(out))
Vb = np.array(G['Base']['verts'])
cols = []
for p in Vb:
    _, k, bc = ray(p + 6.0 * FRAME['n0'], -FRAME['n0'])
    cols.append(float((GREY[T[k]] * bc).sum()))
rim_d = float(np.max(np.linalg.norm(Vb - FRAME['P0'], axis=1)))
t = np.clip((rim_d - np.linalg.norm(Vb - FRAME['P0'], axis=1)) / (0.6 * rim_d), 0, 1)
G['Base']['colors'] = (np.array(cols) * (1 - DARK * t * t * (3 - 2 * t))).round(4).tolist()
G['Penis']['colors'] = [1.0] * len(G['Penis']['verts'])
json.dump(G, open(out, 'w'))
print('equine male written ->', out, '| sheath colours', round(min(G['Base']['colors']), 3), '..',
      round(max(G['Base']['colors']), 3))
