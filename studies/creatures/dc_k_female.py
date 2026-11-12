"""Female deathclaw genitals from kassarawi's model (Dudu 11-12: "deathclaw genitalia for both sexes that our madam
provided"; credit kassarawi, free use). Her 'Female Death Claw.blend' crotch (vulva + anus, her topology, rest + 'Vag
Open') is exported by dc_blend_export.py (Blender, auto-run OFF) to an npz; this script lays it on the VANILLA
deathclaw belly:
  her local frame: x across, y along the midline (her front = -y), h = height over a smooth base fitted to the ring
  around the patch (canals go negative)  ->  dc frame of dc_geom.py: x_dc = -x k, s = s0 - (y - y_open) k,
  point = surface(x_dc, s) + (h k + LIFT) n   (a 180 degree turn: triangle winding is kept)
  VulvaLips  = skin triangles (body UVs from the island under each triangle, vanilla deathclaw material)
  VulvaInner = canal triangles (flesh: our penis texture's lining rows)
  morph 'Erection' = her 'Vag Open' (AAF's tag for the female shapes stays the same)
The canals go below the body surface, so the female wears a BODY COPY whose vertices under the footprint sink inward
(body.json: vertex index -> new position; written into the vanilla nif's vertex bytes, nothing else changes).
    python -I dc_k_female.py <crotch.npz> <geom_female.json> <body_push.json> [k]"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
src = (HERE / 'dc_geom.py').read_text(encoding='utf-8')
cut = src.index('# ---------------------------------------------------------------- the penis tube')
_argv = sys.argv
sys.argv = [str(HERE / 'dc_geom.py')]
exec(compile(src[:cut], str(HERE / 'dc_geom.py'), 'exec'))      # body, ray, surface, FRAME, islands, LINING_V
sys.argv = _argv
# dc_geom ray-tests only the vent's neighbourhood; the anus lands further back between the thighs
c = BV[BT].mean(1)
keep = (np.abs(c[:, 0]) < 22) & (c[:, 1] > -70) & (c[:, 1] < 20) & (c[:, 2] > 60) & (c[:, 2] < 150)
T = BT[keep]
V0, V1, V2 = BV[T[:, 0]], BV[T[:, 1]], BV[T[:, 2]]
E1, E2 = V1 - V0, V2 - V0
T_ISL = ISL[T[:, 0]]
T_CEN = (V0 + V1 + V2) / 3
print('body tris for the female patch', len(T))

npz, out_geom, out_push = sys.argv[1], sys.argv[2], sys.argv[3]
K = float(sys.argv[4]) if len(sys.argv) > 4 else 78.0 * 1.15     # v2 (kassarawi 11-12): 1.15x
PUFF = 1.6         # v2: her labia (the heights over the base) stand out this much more
DARK = 0.20        # v2: skin toward the genitals one tone darker (vertex colours), the rim matches the body
d = np.load(npz)
HV0, HV1, HF, HN = d['V_rest'], d['V_open'], d['F'], d['N_rest']

# ---------------------------------------------------------------- her patch
Y_OPEN = 0.21                     # her vaginal entrance on the midline (section.png)
YC, EX, EY = 0.27, 0.11, 0.25     # patch ellipse (projected from below): vulva front .. anus + margin; EX keeps
                                  # the patch off the thighs (the deathclaw crotch valley is ~ +-10 wide)
LIFT = 0.05                       # dc units over the body surface (the body under the footprint sinks anyway)
S0 = -0.8                         # dc_geom's female vent centre (s from the entry)

# ---------------------------------------------------------------- a frame that FOLLOWS the midline profile
# dc_geom's FRAME is a plane on the forward-facing lower belly; behind the vent the underside turns back between the
# thighs (dc_section.png), where her anus lands. Profile = rays in the x=0 plane from a point inside the pelvis.
CIN = np.array([0.0, -22.0, 112.0])
prof = []
for th in np.radians(np.arange(-60.0, 215.0, 0.5)):          # 0 = straight forward (+y), 90 = straight down
    dvec = np.array([0.0, np.cos(th), -np.sin(th)])
    try:
        prof.append(ray(CIN, dvec)[0])
    except SystemExit:
        pass
prof = np.array(prof)[::-1]                                  # back -> front: arc grows FORWARD
prof[:, 1] = np.convolve(np.pad(prof[:, 1], 4, mode='edge'), np.ones(9) / 9, mode='valid')
prof[:, 2] = np.convolve(np.pad(prof[:, 2], 4, mode='edge'), np.ones(9) / 9, mode='valid')
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))])
k_e = int(np.argmin(np.linalg.norm(prof - FRAME['P0'], axis=1)))
arc = arc - arc[k_e]                                         # s = 0 at the entry, s grows forward (up the belly)
print('profile', len(prof), 'pts, s range', arc.min().round(1), arc.max().round(1))


def prof_at(s):
    p = np.array([np.interp(s, arc, prof[:, k]) for k in range(3)])
    e = 0.6
    tvec = np.array([np.interp(s + e, arc, prof[:, k]) - np.interp(s - e, arc, prof[:, k]) for k in range(3)])
    tvec /= np.linalg.norm(tvec)
    nvec = np.cross(tvec, np.array([1.0, 0.0, 0.0]))         # in the sagittal plane, away from the body
    if (p - CIN) @ nvec < 0:
        nvec = -nvec
    return p, tvec, nvec


def surface(x, s):
    """body point at (x across, s along the profile) + smoothed outward normal: rays along the local profile
    normal from just outside (a short start keeps them off the thighs)"""
    def hit(xx, ss):
        p, _, nv = prof_at(ss)
        o = p + np.array([xx, 0.0, 0.0]) + 4.0 * nv
        return ray(o, -nv)[0]
    q = hit(x, s)
    e = 0.6
    nn = np.cross(hit(x + e, s) - hit(x - e, s), hit(x, s + e) - hit(x, s - e))
    nn /= np.linalg.norm(nn)
    if nn @ prof_at(s)[2] < 0:
        nn = -nn
    return q, nn


def to_local(p):
    """body point -> (x, s): s of the nearest profile point in the sagittal plane"""
    k = int(np.argmin(np.linalg.norm(prof[:, 1:] - p[1:], axis=1)))
    return float(p[0]), float(arc[k])


HUVT = d['UVT']                    # her 'Head and bits' UV per triangle corner (Blender, v up)
TEX = sys.argv[5] if len(sys.argv) > 5 else r'D:\F4Output\creatures\dc_kassarawi\tex\Deathclaw_brown_body_color.1001.png'
PINK = 45                          # red - green of her paint: the flesh she painted pink (skin reads ~20-25)
CROP = (0.33, 0.19, 0.90, 0.78)    # u0 v0 u1 v1 of her genital island on tile 1001 (+ margin)

# the patch = HER genital island: tile-1001 triangles at the crotch (the head shares the tile, location splits them)
cen3 = HV0[HF].mean(1)
on_tile = np.all((HUVT >= 0) & (HUVT < 1), axis=(1, 2))
near = (np.abs(cen3[:, 0]) < 0.2) & (cen3[:, 1] > -0.1) & (cen3[:, 1] < 0.7) & (cen3[:, 2] > 1.3) & (cen3[:, 2] < 1.8)
tk = on_tile & near
F, UVT = HF[tk], HUVT[tk]
used = np.unique(F)
remap = -np.ones(len(HV0), int)
remap[used] = np.arange(len(used))
F = remap[F]
P0h, P1h = HV0[used], HV1[used]
print('patch (her island)', len(used), 'verts', len(F), 'tris')

# base surface: her underside just outside the island
edges = {}
for t in F:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        k_ = (min(a, b), max(a, b))
        edges[k_] = edges.get(k_, 0) + 1
rim = np.array(sorted({v for k_, c_ in edges.items() if c_ == 1 for v in k_}))
RIM = P0h[rim]
dist_out = np.min(np.linalg.norm(HV0[:, None, :] - RIM[None, :, :], axis=2), axis=1)
ring = (remap < 0) & (dist_out < 0.10) & (HN[:, 2] < -0.3) & (np.abs(HV0[:, 2] - 1.535) < 0.09)
x, y, z = HV0[ring].T
A = np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], 1)
coef = np.linalg.lstsq(A, z, rcond=None)[0]
print('base fit rms', float(np.sqrt(((A @ coef - z) ** 2).mean())).__round__(4), 'ring', int(ring.sum()), 'rim', len(rim))


def zbase(x, y):
    return coef[0] + coef[1] * x + coef[2] * y + coef[3] * x * x + coef[4] * x * y + coef[5] * y * y


D_RIM = np.min(np.linalg.norm(P0h[:, None, :] - RIM[None, :, :], axis=2), axis=1)   # per patch vertex


MOUND = 2.0        # dc units: the island stands this far off the body (the vanilla body stays untouched: sinking its
CANAL = 1.6        # few big crotch triangles dragged creases out past the patch), canals squashed to ~this depth:
                   # under MOUND, so the canal floor stays over the body skin (deeper = the body shows when open)
VULVA_C, VULVA_R = (0.0, 0.16), 0.075    # her labia: PUFF acts here only (the island's outer edge has stray heights)
Y_ANUS = 0.38      # her anal entrance on the midline (section.png)
FUNNEL = 3.0       # dc units of (her) canal depth at which a wall point sits halfway to its entrance's centre
Z_CANAL = 1.575    # her z above which a point is inside a canal (section.png); only those funnel


def local(P):
    """her points -> (x_dc, s, h_dc): the island rides a mound that fades to the body surface over its outer 0.03;
    her heights on top, canals (negative) squashed smoothly so their floors stay above the body skin"""
    h = (zbase(P[:, 0], P[:, 1]) - P[:, 2]) * K              # outward (down) positive
    # funnel: a canal squashed flat shows its walls as rings once open; deeper wall points move toward their
    # entrance's centre instead, so the squashed canal reads as a tunnel narrowing inward
    yc = np.where(np.abs(P[:, 1] - Y_OPEN) < np.abs(P[:, 1] - Y_ANUS), Y_OPEN, Y_ANUS)
    # only real canal depth funnels: her skin island sits up to ~2 units under the fitted base (fit residue), and
    # funnelling that squeezed the whole vulva into a strip (v1 sheet, found in v2's clay check)
    # canal = above her underside skin (z 1.50-1.56 in her section; both canals rise past ~1.575)
    f = 1.0 / (1.0 + np.maximum(P[:, 2] - Z_CANAL, 0) * K / FUNNEL)
    x = P[:, 0] * f
    y = yc + (P[:, 1] - yc) * f
    rv = np.hypot(P[:, 0] - VULVA_C[0], P[:, 1] - VULVA_C[1]) / VULVA_R
    puff = 1 + (PUFF - 1) * np.exp(-rv ** 2 * 1.5)
    h = np.where(h < 0, -CANAL * (1 - np.exp(h / CANAL)), h * puff)
    t = np.clip(D_RIM / 0.055, 0, 1)
    fade = t * t * (3 - 2 * t)
    return -x * K, S0 - (y - Y_OPEN) * K, (h + MOUND) * fade


def place(P):
    xs, ss, hs = local(P)
    V, base, nrm = [], [], []
    for x_, s_, h_ in zip(xs, ss, hs):
        p, n = surface(float(x_), float(s_))
        V.append(p + (h_ + LIFT) * n)
        base.append(p)
        nrm.append(n)
    return np.array(V), np.array(base), hs, np.array(nrm)


V_rest, B_rest, H_rest, N_rest = place(P0h)
V_open, _, _, _ = place(P1h)
# her frame -> ours may be a reflection (her up = our inward): wind the triangles so they face out of the body
_tn = np.cross(V_rest[F[:, 1]] - V_rest[F[:, 0]], V_rest[F[:, 2]] - V_rest[F[:, 0]])
_out = float(((_tn * N_rest[F].mean(1)).sum(1) > 0).mean())
if _out < 0.5:
    F = F[:, ::-1].copy()
    UVT = UVT[:, ::-1].copy()
print('outward-facing triangles', round(_out, 2), '-> flipped' if _out < 0.5 else '-> kept')
print('dc extent', V_rest.min(0).round(1), V_rest.max(0).round(1), 'depth min', H_rest.min().round(2))

# ---------------------------------------------------------------- flesh / skin split by HER paint
from PIL import Image  # noqa: E402
img = np.asarray(Image.open(TEX).convert('RGB')).astype(int)
IH, IW = img.shape[:2]
cuv = UVT.mean(1)
px = img[np.clip(((1 - cuv[:, 1]) * IH).astype(int), 0, IH - 1), np.clip((cuv[:, 0] * IW).astype(int), 0, IW - 1)]
pinkness = px[:, 0] - px[:, 1]
inner = pinkness > PINK
print('pinkness percentiles', np.percentile(pinkness, [5, 25, 50, 75, 95]).round(1).tolist(),
      'skin tris', int((~inner).sum()), 'flesh tris', int(inner.sum()))


def split(tris, uvfun):
    """own vertex set per shape; uvfun(tri row, corner) -> (key, uv); vertices split per (vertex, key)"""
    newid, order, nt = {}, [], []
    for r, t in tris:
        row = []
        for c_, vi in enumerate(t):
            key, uv = uvfun(r, c_)
            kk = (vi, key)
            if kk not in newid:
                newid[kk] = len(order)
                order.append((vi, uv))
            row.append(newid[kk])
        nt.append(tuple(row))
    return order, nt


rows_sk = [(r, F[r]) for r in np.where(~inner)[0]]
rows_in = [(r, F[r]) for r in np.where(inner)[0]]
# skin: the body island under each triangle (UV seams cross the crotch), body UVs
tri_isl = {}
for r, t in rows_sk:
    cen, nc = B_rest[list(t)].mean(0), N_rest[list(t)].mean(0)
    tri_isl[r] = int(T_ISL[ray(cen + 2.0 * nc, -nc)[1]])
sk_order, sk_tris = split(rows_sk, lambda r, c_: (tri_isl[r], island_uv(B_rest[F[r][c_]], tri_isl[r])))
# flesh: her UVs into the cropped texture (nif v runs down)


def crop_uv(r, c_):
    u, v = UVT[r][c_]
    cu = (u - CROP[0]) / (CROP[2] - CROP[0])
    cv = (v - CROP[1]) / (CROP[3] - CROP[1])
    return (round(float(u), 5), round(float(v), 5)), [float(cu), float(1 - cv)]


in_order, in_tris = split(rows_in, crop_uv)
dmin = H_rest.min()


def weights(idx):
    return [_sample(*ray(B_rest[vi] + 2.0 * N_rest[vi], -N_rest[vi])[1:])[1] for vi in idx]


def shape(order, tris):
    idx = [vi for vi, _ in order]
    uv = [list(map(float, u)) for _, u in order]
    g = json_shape(V_rest[idx], tris, uv, weights(idx), {'Erection': OPEN * (V_open[idx] - V_rest[idx])})
    # shade like the skin around it: the body's OWN nif normals under each vertex (the game's normals, not the
    # geometric ones), plus our relief (our normal minus the geometric surface normal); at the rim the body's alone
    bn = []
    for vi in idx:
        _, k, bc = ray(B_rest[vi] + 2.0 * N_rest[vi], -N_rest[vi])
        bn.append((BNRM[T[k]] * bc[:, None]).sum(0))
    bn = np.array(bn)
    t = np.clip(D_RIM[idx] / 0.06, 0, 1)[:, None]
    nn = bn + t * (np.array(g['normals']) - N_rest[idx])
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    g['normals'] = nn.round(5).tolist()
    # vertex colours: the body's own (the engine multiplies them in: ~0.8 at the crotch), darkened toward the
    # genitals; her flesh texture takes a flat 0.9
    if order is sk_order:
        bc_ = []
        for vi in idx:
            _, k, bc = ray(B_rest[vi] + 2.0 * N_rest[vi], -N_rest[vi])
            bc_.append(float((BCOL[T[k]] * bc).sum()))
        f = np.clip(D_RIM[idx] / 0.06, 0, 1)
        g['colors'] = (np.array(bc_) * (1 - DARK * f * f * (3 - 2 * f))).round(4).tolist()
    else:
        g['colors'] = [0.9] * len(idx)
    return g


def _nif_normals(shape):
    import struct
    off = ((shape.desc >> 16) & 0xF) * 4
    out = np.array([struct.unpack_from('<3B', shape.nif.b, shape.data_at + i * shape.stride + off)
                    for i in range(shape.count)], float) / 127.5 - 1.0
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


BNRM = _nif_normals(bs)


def _nif_grey(shape):
    import struct
    off = ((shape.desc >> 24) & 0xF) * 4
    return np.array([struct.unpack_from('<B', shape.nif.b, shape.data_at + i * shape.stride + off)[0]
                     for i in range(shape.count)], float) / 255.0


BCOL = _nif_grey(bs)


OPEN = 0.7         # her 'Vag Open' at full strength gapes wider than the deathclaw crotch reads well


def welded_normals(V, tris):
    key = {}
    wid = np.array([key.setdefault(tuple(np.round(p, 4)), len(key)) for p in V])
    N = np.zeros((len(key), 3))
    for a, b, cc in tris:
        n = np.cross(V[b] - V[a], V[cc] - V[a])
        for i in (a, b, cc):
            N[wid[i]] += n
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]
    return N[wid]


def json_shape(V, tris, uv, weights, morphs):
    bones = sorted({b for w in weights for b in w})
    return {'verts': V.round(5).tolist(), 'tris': [list(map(int, t)) for t in tris], 'uv': uv,
            'normals': welded_normals(V, tris).round(5).tolist(),
            'weights': {b: [round(w.get(b, 0.0), 5) for w in weights] for b in bones},
            'morphs': {k: np.asarray(dd).round(5).tolist() for k, dd in morphs.items()}}


female = {'VulvaLips': shape(sk_order, sk_tris), 'VulvaInner': shape(in_order, in_tris)}
json.dump(female, open(out_geom, 'w'))
print('female: lips', len(female['VulvaLips']['verts']), 'inner', len(female['VulvaInner']['verts']))

# ---------------------------------------------------------------- the body copy: sink what the patch covers
push = {}                                    # the body stays vanilla (MOUND)
json.dump({'shape': bs.name, 'push': push}, open(out_push, 'w'))
print('body vertices sunk', len(push))
