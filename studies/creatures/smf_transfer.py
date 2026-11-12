"""Female super mutant from ilhamitaa24's 3D sculpt (Dudu 11-12: "yes download"; v2's parametric shape was rejected).
Her model and the game body stand in different poses (she: upright T-pose; the game mutant: arms hanging, other
proportions), so the shape moves over PER SEGMENT along each segment's own bone axis, not by projecting one surface
onto the other:
  segment     axis (game skin space)              her axis (her rig)          scale (game units per her unit)
  torso       Pelvis -50.5 -> Neck -4.3            Hips 1.131 -> Neck 1.609     segment-length ratio
  thigh L/R   Thigh -54.2 -> Calf -92.7            UpLeg 1.072 -> Leg 0.606     segment-length ratio
For each segment: a cylindrical radius map r(t, theta) of her outer surface (scaled) and of the game body's skin
(first hit of a ray out of the axis), the ratio smoothed (median, then box) and clamped; every game vertex moves
radially by the ratio of each segment it is skinned to, blended by its skin weights (pelvis/spine/chest = torso,
thigh = that thigh). Calves/feet (her boots), arms (pose) and head stay vanilla; the map fades out at the segment
ends. Her gear (belt, straps, loincloth) is thin or hangs off the body: the median + clamp ride over it.
Character frame for both: u = toward the character's LEFT, v = forward; theta = atan2(u, v) (0 front, +90 left).
    python -I smf_transfer.py <her sample.npz> <out positions json> [diagnostic png]"""
import json
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

VAN = r'D:\F4Output\creatures\sm\vanilla\supermutantbody.nif'
d = np.load(sys.argv[1])
HP, HB = d['P'], {str(n): p for n, p in zip(d['bone_names'], d['bone_pos'])}
n = nif.Nif(VAN)
body = n.shape('SupermutantBodyNew:0')
V = np.array(body.positions())
T = np.array(body.triangles())
names, xf = n.skin(body)
BONE = {}
for nm, (r, t, sc) in zip(names, xf):
    BONE[nm] = -np.linalg.solve(np.array(r).reshape(3, 3), np.array(t)) / sc

NT, NA = 24, 36                                    # t bins, theta bins
CLAMP = (0.78, 1.5)


def game_uv(P):
    return -P[:, 0], P[:, 1]                       # left = -x, front = +y


def her_uv(P):
    return P[:, 0], -P[:, 1]                       # left = +x, front = -y


SEGS = {
    'torso': dict(g0=BONE['Pelvis'], g1=BONE['Neck_skin'], h0=HB['Hips'], h1=HB['Neck'], t_rng=(0.0, 0.80),
                  bones=('Pelvis', 'SPINE1', 'SPINE2', 'Chest', 'Pelvis_skin', 'Spine1_skin', 'Spine2_skin',
                         'Chest_skin')),
    'thighL': dict(g0=BONE['LLeg_Thigh'], g1=BONE['LLeg_Calf_skin'], h0=HB['LeftUpLeg'], h1=HB['LeftLeg'],
                   t_rng=(0.0, 0.90), bones=('LLeg_Thigh', 'LLeg_Thigh_skin')),
    'thighR': dict(g0=BONE['RLeg_Thigh'], g1=BONE['RLeg_Calf_skin'], h0=HB['RightUpLeg'], h1=HB['RightLeg'],
                   t_rng=(0.0, 0.90), bones=('RLeg_Thigh', 'RLeg_Thigh_skin')),
}


def frame(p0, p1, uvfun):
    """axis frame: origin p0, unit axis a (p0 -> p1), length; lateral/forward basis from the character frame"""
    a = p1 - p0
    L = np.linalg.norm(a)
    a = a / L
    return p0, a, L


def cyl(P, p0, a, L, uvfun):
    """(t, theta, r) of points about the axis; theta from the character frame projected off the axis"""
    rel = P - p0
    t = rel @ a / L
    radial = rel - np.outer(rel @ a, a)
    u, v = uvfun(radial)
    return t, np.arctan2(u, v), np.hypot(u, v) if False else np.linalg.norm(radial, axis=1)


# ---------------------------------------------------------------- game body: first skin hit from the axis
V0, V1, V2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
E1, E2 = V1 - V0, V2 - V0


def ray_first(o, dvec):
    p = np.cross(dvec, E2)
    det = (E1 * p).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - V0
    u = (s * p).sum(1) * inv
    q = np.cross(s, E1)
    v = (q * dvec).sum(1) * inv
    t = (E2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return float(t[hit].min()) if hit.any() else np.nan


def maps(seg):
    g0, g1, h0, h1 = seg['g0'], seg['g1'], seg['h0'], seg['h1']
    _, ga, gL = frame(g0, g1, game_uv)
    _, ha, hL = frame(h0, h1, her_uv)
    s = gL / hL
    tb = np.linspace(seg['t_rng'][0], seg['t_rng'][1], NT)
    th = np.linspace(-np.pi, np.pi, NA, endpoint=False)
    # basis perpendicular to each axis, aligned to the character frame (forward first)
    def basis(a, fwd, left):
        f = fwd - (fwd @ a) * a
        f /= np.linalg.norm(f)
        lft = np.cross(a, f)
        if lft @ left < 0:
            lft = -lft
        return f, lft
    gf, gl = basis(ga, np.array([0, 1.0, 0]), np.array([-1.0, 0, 0]))
    hf, hl = basis(ha, np.array([0, -1.0, 0]), np.array([1.0, 0, 0]))
    # her: outermost sample point per bin (scaled)
    rel = HP - h0
    t = rel @ ha / hL
    rad = rel - np.outer(rel @ ha, ha)
    ang = np.arctan2(rad @ hl, rad @ hf)
    r = np.linalg.norm(rad, axis=1) * s
    Rh = np.full((NT, NA), np.nan)
    ti = np.round((t - tb[0]) / (tb[1] - tb[0])).astype(int)
    ai = np.round((ang + np.pi) / (2 * np.pi) * NA).astype(int) % NA
    keep = (ti >= 0) & (ti < NT) & (r < 60)
    if seg is SEGS['torso']:
        keep &= np.abs(rel[:, 0]) * s < 34          # her T-pose arms stand out sideways: never torso
    else:
        keep &= r < 25                              # the other leg / torso are further than a thigh radius
    for i, j, rr in zip(ti[keep], ai[keep], r[keep]):
        if not rr <= Rh[i, j]:
            Rh[i, j] = rr if np.isnan(Rh[i, j]) or rr > Rh[i, j] else Rh[i, j]
    # game: first hit out of the axis
    Rg = np.full((NT, NA), np.nan)
    for i, tt in enumerate(tb):
        o = g0 + ga * gL * tt
        for j, aa in enumerate(th):
            Rg[i, j] = ray_first(o, np.cos(aa) * gf + np.sin(aa) * gl)
    ratio = Rh / Rg
    return dict(tb=tb, th=th, Rh=Rh, Rg=Rg, ratio=ratio, g0=g0, ga=ga, gL=gL, gf=gf, gl=gl, s=s)


def smooth(M):
    """nan-aware median 3x3 then 3x3 box, theta wraps"""
    def nb(A, f):
        out = np.full_like(A, np.nan)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                w = [A[ii, jj % A.shape[1]] for ii in range(max(0, i - 1), min(A.shape[0], i + 2))
                     for jj in (j - 1, j, j + 1)]
                w = [x for x in w if not np.isnan(x)]
                out[i, j] = f(w) if w else np.nan
        return out
    M = nb(M, np.median)
    M = nb(M, np.mean)
    return np.where(np.isnan(M), 1.0, M)


def sample(M, tb, th, t, a):
    fi = np.clip((t - tb[0]) / (tb[1] - tb[0]), 0, len(tb) - 1.001)
    fj = ((a + np.pi) / (2 * np.pi) * len(th)) % len(th)
    i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
    di, dj = fi - i0, fj - j0
    j1 = (j0 + 1) % len(th)
    i1 = np.minimum(i0 + 1, len(tb) - 1)
    return ((1 - di) * (1 - dj) * M[i0, j0] + (1 - di) * dj * M[i0, j1] + di * (1 - dj) * M[i1, j0]
            + di * dj * M[i1, j1])


W = np.zeros((len(V), len(names)))
for i in range(len(V)):
    for slot, w in body.skin_weights(i):
        W[i, slot] += w
out = V.copy()
disp = np.zeros_like(V)
diag = {}
# her PROPORTIONS at the mutant's size: segment-length scaling makes her ~1.3x the mutant overall, so every ratio is
# divided by the torso's median (thighs too: their thickness relative to the torso is what transfers)
MAPS = {key: maps(seg) for key, seg in SEGS.items()}
NORM = float(np.nanmedian(smooth(MAPS['torso']['ratio'])))
print('size normalisation (torso median ratio)', round(NORM, 3))
for key, seg in SEGS.items():
    m = MAPS[key]
    raw = smooth(m['ratio']) / NORM
    print(f'{key:7s} raw (normalised) min {raw.min():.2f} median {np.median(raw):.2f} max {raw.max():.2f}')
    R = np.clip(raw, *CLAMP)
    diag[key] = (m, R)
    rel = V - m['g0']
    t = rel @ m['ga'] / m['gL']
    rad = rel - np.outer(rel @ m['ga'], m['ga'])
    a = np.arctan2(rad @ m['gl'], rad @ m['gf'])
    k = sample(R, m['tb'], m['th'], t, a)
    lo, hi = seg['t_rng']
    fade = np.clip((t - lo) / 0.08, 0, 1) * np.clip((hi - t) / 0.08, 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    wseg = sum(W[:, names.index(b)] for b in seg['bones'] if b in names)
    disp += (wseg * fade)[:, None] * rad * (k - 1)[:, None]
    print(f'{key:7s} scale {m["s"]:.1f}  ratio min {np.nanmin(R):.2f} max {np.nanmax(R):.2f} '
          f'median {np.nanmedian(R):.2f}  verts moved {(wseg * fade > 0.05).sum()}')
out = V + disp
json.dump({'shape': body.name, 'positions': out.round(4).tolist()}, open(sys.argv[2], 'w'))
print('max move', np.linalg.norm(disp, axis=1).max().round(2))

if len(sys.argv) > 3:
    from PIL import Image, ImageDraw
    Wd, PAD = 700, 20
    z_lo, z_hi = -150, 45
    sc = (Wd * 1.4 - 2 * PAD) / (z_hi - z_lo)
    img = Image.new('RGB', (2 * Wd, int(Wd * 1.4)), (250, 250, 250))
    dr = ImageDraw.Draw(img)
    # her points mapped by the torso scale for reference (pelvis-anchored)
    mt = diag['torso'][0]
    Hm = (HP - HB['Hips']) * np.array([-mt['s'], -mt['s'], mt['s']]) + BONE['Pelvis']

    def pt(uu, z, off):
        return (off + Wd / 2 + uu * sc, PAD + (z_hi - z) * sc)
    for ax, off in ((0, 0), (1, Wd)):
        for p in Hm[::3]:
            dr.point(pt(p[ax], p[2], off), fill=(235, 150, 60))
        for tt in T:
            q = out[tt]
            dr.line([pt(q[0][ax], q[0][2], off), pt(q[1][ax], q[1][2], off), pt(q[2][ax], q[2][2], off),
                     pt(q[0][ax], q[0][2], off)], fill=(60, 60, 80), width=1)
    dr.text((10, 5), 'transferred game body (wire) vs her sculpt at torso scale (orange)', fill=(0, 0, 0))
    img.save(sys.argv[3])
    print('diagnostic', sys.argv[3])
