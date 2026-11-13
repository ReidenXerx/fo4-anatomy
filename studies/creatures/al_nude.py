"""Immersive Aliens, option B (Dudu + ilhamitaa24 11-13): a NUDE Zetan from the vanilla suit body.
The Zetan body (Alien_01:0) is its suit: one connected suit part (torso, arms, gloves, legs, boots, collar, backpack -
UV islands of it), the head part, and ~70 small accessory parts (hoses, buttons, belt pouches, antenna, teeth, eyes).
  KEEP   the head + everything on it (eyes, teeth: parts whose centre sits inside the head's box), and the suit
         islands that ARE the body (centre below the collar line and in front of the backpack)
  HIDE   collar, backpack, hoses, belt pouches, antenna, chest buttons: their vertices collapse onto one point inside
         the chest (zero-area triangles draw nothing); positions only, topology/skin/segments untouched
  SKIN   a new atlas: every kept suit texel is repainted with the alien's own head skin (yellow, brown spots) by a
         TRIPLANAR projection of a forehead crop in 3D (seamless across the suit's many UV islands); normal flat,
         specular from the head. The head region of the atlas is untouched.
Outputs: <out>/positions.json (vertex index -> new position for the hidden ones), <out>/AlienNude_d/_n/_s.png.
    python -I al_nude.py <alien_body.nif> <png dir with actors__alien__alien_01_d/_n/_s.png> <out dir>"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

SRC, PNG, OUT = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
n = nif.Nif(SRC)
s = n.shape('Alien_01:0')
P = np.array(s.positions())
T = np.array(s.triangles())
UV = np.array([s.uv(i) for i in range(s.count)])

# ---------------------------------------------------------------- parts (welded) and suit UV islands
key = {}
wid = np.array([key.setdefault(tuple(np.round(p, 3)), len(key)) for p in P])
par = np.arange(len(key))


def find(a, par):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


for a, b, c in wid[T]:
    for x, y in ((a, b), (b, c)):
        ra, rb = find(x, par), find(y, par)
        if ra != rb:
            par[ra] = rb
part = np.array([find(w, par) for w in wid])
ids, cnt = np.unique(part, return_counts=True)
suit = ids[np.argmax(cnt)]
by_size = ids[np.argsort(-cnt)]
head = by_size[1]                                        # second largest: the head (z 40.7..72.8)
ipar = np.arange(len(P))
for a, b, c in T:
    for x, y in ((a, b), (b, c)):
        ra, rb = find(x, ipar), find(y, ipar)
        if ra != rb:
            ipar[ra] = rb
isl = np.array([find(i, ipar) for i in range(len(P))])
hm = part == head
hlo, hhi = P[hm].min(0), P[hm].max(0)
COLLAR_Z = 38.0                                          # the suit's top edge under the collar ring
keep = np.zeros(len(P), bool)
skin = np.zeros(len(P), bool)                            # suit texels to repaint
keep[hm] = True
for pid in ids:
    if pid in (suit, head):
        continue
    m = part == pid
    c = P[m].mean(0)
    if np.all(c > hlo - 0.5) and np.all(c < hhi + 0.5) and c[1] > 0:     # eyes, teeth, tongue: on the face
        keep[m] = True
for iid in np.unique(isl[part == suit]):
    m = (isl == iid) & (part == suit)
    c = P[m].mean(0)
    body = c[2] < COLLAR_Z and c[1] > -15.0             # not the collar, not the backpack
    if body:
        keep[m] = True
        skin[m] = True
hide = ~keep
anchor = np.array([0.0, 0.0, 20.0])                     # inside the chest
push = {int(i): anchor.tolist() for i in np.where(hide)[0]}
# NECK: the suit had the collar ring there - without it the head floats over the torso's open top. The head's lowest
# band stretches DOWN into the torso, and the torso's top opening is pulled IN around it.
NECK_DROP = 6.0
hz = P[hm][:, 2]
hb = hm & (P[:, 2] < hz.min() + 4.0)
neck_c = P[hb].mean(0)
neck_r = float(np.median(np.linalg.norm((P[hb] - neck_c)[:, :2], axis=1)))
for i in np.where(hm & (P[:, 2] < hz.min() + 6.0))[0]:
    f = 1 - (P[i, 2] - hz.min()) / 6.0
    q = P[i].copy()
    q[2] -= NECK_DROP * f
    push[int(i)] = q.round(4).tolist()
kt = [t for t in T if keep[t].all() and skin[t].any()]
ecount = {}
for t in kt:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        k_ = (min(wid[a], wid[b]), max(wid[a], wid[b]))
        ecount[k_] = ecount.get(k_, 0) + 1
open_w = {w for k_, c_ in ecount.items() if c_ == 1 for w in k_}
rim = [i for i in np.where(skin)[0] if wid[i] in open_w and P[i, 2] > 30.0]
for i in np.where(skin & (P[:, 2] > 26.0))[0]:
    d = min(np.linalg.norm(P[i] - P[j]) for j in rim) if rim else 99
    if d > 6.0:
        continue
    f = 1 - d / 6.0
    q = P[i].copy()
    rel = q[:2] - neck_c[:2]
    r = np.linalg.norm(rel)
    target = neck_r * 1.08
    if r > target:
        q[:2] = neck_c[:2] + rel / r * (r - (r - target) * f)
    push[int(i)] = q.round(4).tolist()
print('neck centre', neck_c.round(1), 'radius', round(neck_r, 2), '| torso rim vertices', len(rim))
json.dump({'shape': s.name, 'push': push}, open(OUT / 'positions.json', 'w'))
print('kept', int(keep.sum()), 'hidden', int(hide.sum()), 'suit->skin', int(skin.sum()), 'of', len(P))

# ---------------------------------------------------------------- the skin atlas (triplanar head skin)
D = np.asarray(Image.open(PNG / 'actors__alien__alien_01_d.png').convert('RGB')).astype(float)
H, W = D.shape[:2]
S_ = np.asarray(Image.open(PNG / 'actors__alien__alien_01_s.png').convert('RGB').resize((W, H))).astype(float)
# forehead crop: the top-left of the head region, above the face (no features)
crop = D[int(0.02 * H):int(0.14 * H), int(0.05 * W):int(0.30 * W)]
scrop = S_[int(0.02 * H):int(0.14 * H), int(0.05 * W):int(0.30 * W)]
ch, cw = crop.shape[:2]
TILE = 14.0                                              # game units per crop repeat


def tri_sample(img, a, b):
    ii = ((a / TILE) % 1.0 * (img.shape[0] - 1)).astype(int)
    jj = ((b / TILE) % 1.0 * (img.shape[1] - 1)).astype(int)
    return img[ii, jj]


Dn = D.copy()
Sn = S_.copy()
Nn = np.asarray(Image.open(PNG / 'actors__alien__alien_01_n.png').convert('RGB').resize((W, H))).astype(float).copy()
skin_tris = [t for t in T if skin[t].all()]
# per-vertex normals (geometry)
VN = np.zeros_like(P)
for a, b, c in T:
    VN[[a, b, c]] += np.cross(P[b] - P[a], P[c] - P[a])
VN /= np.maximum(np.linalg.norm(VN, axis=1, keepdims=True), 1e-9)
for t in skin_tris:
    uv = UV[t] * np.array([W, H])
    lo = np.floor(uv.min(0)).astype(int)
    hi = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
    px = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv
    v0, v1, v2 = b - a, c - a, px - a
    den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-9:
        continue
    l1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
    l2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
    l0 = 1 - l1 - l2
    inside = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
    if not inside.any():
        continue
    L = np.stack([l0, l1, l2], 1)[inside]
    X = L @ P[t]
    Nv = L @ VN[t]
    w = np.abs(Nv) ** 4
    w /= w.sum(1, keepdims=True)
    col = (w[:, 0:1] * tri_sample(crop, X[:, 1], X[:, 2]) + w[:, 1:2] * tri_sample(crop, X[:, 0], X[:, 2])
           + w[:, 2:3] * tri_sample(crop, X[:, 0], X[:, 1]))
    spc = (w[:, 0:1] * tri_sample(scrop, X[:, 1], X[:, 2]) + w[:, 1:2] * tri_sample(scrop, X[:, 0], X[:, 2])
           + w[:, 2:3] * tri_sample(scrop, X[:, 0], X[:, 1]))
    qx = np.clip(px[inside, 0].astype(int), 0, W - 1)
    qy = np.clip(px[inside, 1].astype(int), 0, H - 1)
    Dn[qy, qx] = col
    Sn[qy, qx] = spc
    Nn[qy, qx] = (128, 128, 255)
for name, img in (('AlienNude_d.png', Dn), ('AlienNude_s.png', Sn), ('AlienNude_n.png', Nn)):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / name)
print('atlas repainted:', len(skin_tris), 'suit triangles ->', OUT)
