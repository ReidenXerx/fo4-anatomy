"""The men's anus (roadmap, the owner 2026-10-01: "players desperately wait it"), step 1: measure BodyTalk 4's own anus
pucker and the room a canal has behind it.

BodyTalk4-Nude/-Uncut model a closed pucker (145 vertices on Anus_01-04, its floor ~0.8 deeper than its rim); there is
no opening. This reads, on the reference ShapeData:
  - the pucker: centre, the rim's outward normal (the canal's axis is its opposite), depth profile by radius;
  - for candidate canal centrelines (up the pelvis, tilted back by a range of angles): the clearance from the canal's
    centre to the body's skin along rays around it, every 0.5 units of the path, so the walls (RADIUS) stay inside
    the body with a margin (the buttock cleft behind, the scrotum and penis root in front).

    python studies/male_anus_probe.py [BodyTalk4-Nude.nif]
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import nif

REF = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Tools\BodySlide\ShapeData\BodyTalk4\BodyTalk4-Nude.nif')
RADIUS = 1.0


def body(path):
    n = nif.Nif(path)
    s = [x for x in n.shapes() if n.skin(x)[0]][0]
    bones, _ = n.skin(s)
    pos = np.array(s.positions(), dtype=np.float64)
    tri = np.array(s.triangles(), dtype=np.int64)
    anus = [i for i, b in enumerate(bones) if b.lower().startswith('anus_')]
    w = np.zeros(len(pos))
    for v in range(s.count):
        for sl, x in s.skin_weights(v):
            if sl in anus:
                w[v] += x
    return pos, tri, w


def normals(p, tri):
    a, b, c = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
    fn = np.cross(b - a, c - a)
    n = np.zeros_like(p)
    for k in range(3):
        np.add.at(n, tri[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def ray_hits(origin, d, p, tri):
    """distance along unit d from origin to the nearest triangle (Moller-Trumbore, vectorised), or inf"""
    a, b, c = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(d, e2)
    det = (e1 * h).sum(1)
    ok = np.abs(det) > 1e-9
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = origin - a
    u = (s * h).sum(1) * inv
    q = np.cross(s, e1)
    v = (q * d).sum(1) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
    return t[hit].min() if hit.any() else math.inf


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REF
    pos, tri, w = body(path)
    nrm = normals(pos, tri)
    hit = np.where(w > 0.05)[0]
    c = pos[hit].mean(0)
    r = np.hypot(pos[hit, 0] - c[0], pos[hit, 2] - c[2])
    rim = hit[r > np.percentile(r, 70)]
    out = nrm[rim].mean(0)
    out /= np.linalg.norm(out)
    axis = -out
    floor = pos[hit[r < 0.3]].mean(0)
    print(f'pucker: {len(hit)} vertices, centre {c.round(2)}, floor {floor.round(2)}; the rim faces {out.round(2)}, '
          f'so inward = {axis.round(2)}')
    for lo, hi in ((0, 0.3), (0.3, 0.7), (0.7, 1.2), (1.2, 2.0), (2.0, 3.0)):
        m = (r >= lo) & (r < hi)
        if m.any():
            print(f'  radius {lo}-{hi}: {m.sum():>3} verts, depth along inward {((pos[hit[m]] - c) @ axis).mean():+.2f}')
    side = np.array([1.0, 0.0, 0.0])
    print('candidate canals from the floor: straight inward for 1.5, then up the pelvis tilted back by the angle;')
    print('clearance = min over the path of (nearest skin around the centre) - RADIUS; front/back = along -/+ back dir')
    for tilt in (0, 15, 30, 45, 60):
        t = math.radians(tilt)
        up = np.array([0.0, -math.sin(t), math.cos(t)])          # -y is the back (the women's canal: "back toward the tailbone")
        pts = [floor + axis * s for s in np.arange(0.0, 1.51, 0.5)]
        start = pts[-1]
        pts += [start + up * s for s in np.arange(0.5, 8.01, 0.5)]
        worst, where = math.inf, None
        mins = []
        for k, p0 in enumerate(pts):
            dirn = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)])
            dirn /= np.linalg.norm(dirn) or 1.0
            e1 = np.cross(dirn, side)
            e1 = e1 / (np.linalg.norm(e1) or 1.0)
            e2 = np.cross(dirn, e1)
            best = math.inf
            for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
                d = math.cos(a) * e1 + math.sin(a) * e2
                best = min(best, ray_hits(p0, d, pos, tri))
            mins.append(best)
            if k > 3 and best < worst:       # past the opening: the walls must stay inside
                worst, where = best, k
        print(f'  tilt {tilt:>2} deg: path end {pts[-1].round(2)}; inner clearance min {worst - RADIUS:+.2f} at step {where} '
              f'({pts[where].round(2)}); clearance profile {[round(x - RADIUS, 1) for x in mins[4::3]]}')


if __name__ == '__main__':
    main()
