"""Does a Servitron ring stay a ring when it opens? (the owner, 2026-10-09: opened, the black rubber rings "look ugly
like stretched texture"). Each opening's four stretch bones are pushed straight out by OPEN units (the collision's
max for SrvVagina, physics_design), every vertex following its weights; then, per ring:
  - folded triangles: a ring triangle whose normal turns past 90 degrees (the band turned inside out);
  - the band: the lip's and the outer edge's mean radius before and after, and the band's width ratio;
  - the seam: how far a ring outer-edge vertex and the nearest shell vertex move apart (a gap the suit shows through).

    python studies/servitron_ring_open.py <rigged abdomen .nif> [--open 1.5]
"""
import argparse
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import servitron as sv  # noqa: E402


def moved(n, s, o, amount):
    side, up = (np.array(v) for v in sv.frame(o['axis']))
    dirs = {}
    for tag, at in sv.RING_ANGLES.items():
        r = math.radians(at)
        dirs[pd.SRV_STRETCH_BONES[f"{o['bones']}_{tag}"]] = math.cos(r) * side + math.sin(r) * up
    bones = n.skin(s)[0]
    P = np.array(s.positions(), float)
    out = P.copy()
    for i in range(s.count):
        for slot, w in s.skin_weights(i):
            d = dirs.get(bones[slot])
            if d is not None:
                out[i] += w * amount * d
    return P, out


def radius(P, o):
    c, ax = np.array(o['centre']), np.array(o['axis'])
    d = P - c
    along = d @ ax
    return np.sqrt(np.maximum(0.0, (d * d).sum(1) - along ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nif')
    ap.add_argument('--open', type=float, default=1.5)
    a = ap.parse_args()
    n = nif.Nif(a.nif)
    names = {s.name: s for s in n.shapes()}
    shell = next(x for x in sv.SHELLS if x in names)
    for nm, o in sv.OPENINGS.items():
        ring = names[shell + o['ring']]
        P0, P1 = moved(n, ring, o, a.open)
        T = np.array(ring.triangles())
        n0 = np.cross(P0[T[:, 1]] - P0[T[:, 0]], P0[T[:, 2]] - P0[T[:, 0]])
        n1 = np.cross(P1[T[:, 1]] - P1[T[:, 0]], P1[T[:, 2]] - P1[T[:, 0]])
        ok = (np.linalg.norm(n0, axis=1) > 1e-9)
        folded = int(((n0 * n1).sum(1)[ok] < 0).sum())
        r0, r1 = radius(P0, o), radius(P1, o)
        lip = r0 < np.percentile(r0, 15)
        edge = r0 > np.percentile(r0, 85)
        w0 = r0[edge].mean() - r0[lip].mean()
        w1 = r1[edge].mean() - r1[lip].mean()
        S0, S1 = moved(n, names[shell], o, a.open)
        near = np.argmin(((S0[None, :, :] - P0[edge][:, None, :]) ** 2).sum(2), axis=1) if edge.sum() * len(S0) < 4e7 else None
        seam = np.linalg.norm((P1[edge] - P0[edge]) - (S1[near] - S0[near]), axis=1) if near is not None else np.array([0.0])
        print(f'{nm:6} ring {ring.count} verts: folded triangles {folded} of {ok.sum()}; lip r {r0[lip].mean():.2f} -> '
              f'{r1[lip].mean():.2f}, edge r {r0[edge].mean():.2f} -> {r1[edge].mean():.2f}; band width {w0:.2f} -> '
              f'{w1:.2f} (x{w1 / w0:.2f}); seam ring edge vs shell apart: mean {seam.mean():.2f}, worst {seam.max():.2f}')


if __name__ == '__main__':
    main()
