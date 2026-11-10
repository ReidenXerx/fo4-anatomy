"""Auto landmarks for a creature body: the pelvis bone, the rump's rear face (rays from just inside the pelvis going
backwards; the face = the contiguous run of hits below the tail), the vulva height (30 % up that face), and the belly
line (rays from inside down) between the hind and front legs.
    python -I fem_auto.py <body nif>..."""
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402


def body_of(p):
    m = nif.Nif(p)
    b = max(m.shapes(), key=lambda s: s.count)
    names, xf = m.skin(b)
    bones = {n.lower(): np.array(nif.bone_origin(x)) for n, x in zip(names, xf)}
    B = np.array(b.positions())
    T = np.array(b.triangles())
    return B, T, bones


def make_ray(B, T):
    V0, V1, V2 = B[T[:, 0]], B[T[:, 1]], B[T[:, 2]]
    E1, E2 = V1 - V0, V2 - V0

    def ray(o, d):
        pp = np.cross(d, E2)
        det = (E1 * pp).sum(1)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = o - V0
        u = (s * pp).sum(1) * inv
        q = np.cross(s, E1)
        v = (q * d).sum(1) * inv
        t = (E2 * q).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        return None if not hit.any() else o + t[hit].min() * d
    return ray


def landmarks(p):
    B, T, bones = body_of(p)
    ray = make_ray(B, T)
    pel = next(v for k, v in bones.items() if k.endswith('pelvis'))
    lo, hi = B[:, 2].min(), B[:, 2].max()
    iy = pel[1] + 0.05 * (B[:, 1].max() - B[:, 1].min())          # a little in front of the pelvis: inside
    zs = np.linspace(pel[2] * 0.4, pel[2] * 1.35, 60)
    hits = [(z, ray(np.array([0, iy, z]), np.array([0, -1.0, 0]))) for z in zs]
    ys = [(z, h[1]) for z, h in hits if h is not None]
    # the rear face: the longest run of hits whose y changes smoothly (a tail is a jump backwards)
    runs, cur = [], [ys[0]] if ys else []
    for a, b in zip(ys, ys[1:]):
        if abs(b[1] - a[1]) < 0.06 * (B[:, 1].max() - B[:, 1].min()) and b[0] - a[0] < 2 * (zs[1] - zs[0]):
            cur.append(b)
        else:
            runs.append(cur)
            cur = [b]
    runs.append(cur)
    face = max(runs, key=len)
    z0, z1 = face[0][0], face[-1][0]
    vz = z0 + 0.3 * (z1 - z0)
    return dict(pelvis=pel.round(2).tolist(), inside_y=round(float(iy), 2), face=(round(z0, 1), round(z1, 1)),
                vulva_z=round(float(vz), 2), size=round(float(hi - lo), 1), ray=ray, B=B)


def belly(L, y0, y1, x, iz, n=9):
    out = []
    for y in np.linspace(y0, y1, n):
        h = L['ray'](np.array([x, y, iz]), np.array([0, 0, -1.0]))
        out.append((round(float(y), 1), None if h is None else round(float(h[2]), 1)))
    return out


if __name__ == '__main__':
    for p in sys.argv[1:]:
        L = landmarks(p)
        print(p.split('\\')[-1], {k: v for k, v in L.items() if k not in ('ray', 'B')})
