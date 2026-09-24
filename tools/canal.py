"""The paths inside her the aim bends a shaft along (A-28): from each opening, the middle of her body along the
midline, height by height, measured on the installed female body (skin space).

    python tools/canal.py [--data <Fallout 4 Data>]

At each height above the crotch it takes the torso's vertices within a unit of the midline, and the point
halfway between her back and her front there. From an entrance the path leads a little along the opening's
own axis, then joins that midline, resampled every PATH_STEP. It prints each point and the flesh around it
(the distance to the nearest vertex): a shaft (radius 1.55) that follows the path is hidden wherever the
flesh passes that. physics_design.VAGINA_PATH / ANUS_PATH hold the result; rerun this after the body changes.

Reads the body through fo4-silhouette's tools/pool/mesh.py (a sibling repo, read-only).
"""
import argparse
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'fo4-silhouette/tools/pool'))
sys.path.insert(0, str(HERE.parent.parent / 'fo4-silhouette/tools'))
import physics_design as pd  # noqa: E402
from mesh import Body  # noqa: E402

DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
PATH_STEP, PATH_POINTS, LEAD = 3.0, 6, 1.5


def midline(body, top=26):
    torso = [p for p, r in zip(body.ref, body.region) if r == 'torso']
    line = []
    for k in range(top):
        z = -55.0 + k
        ys = [p[1] for p in torso if abs(p[0]) < 1.0 and abs(p[2] - z) < 0.7]
        if len(ys) >= 4:
            line.append((0.0, (min(ys) + max(ys)) / 2, z))
    return line


def path(line, entrance, axis):
    first = tuple(entrance[i] + axis[i] * LEAD for i in range(3))
    seg = [entrance, first] + [p for p in line if p[2] > first[2] + 1.0]
    out, acc = [], 0.0
    for a, b in zip(seg, seg[1:]):
        d = math.dist(a, b)
        while acc + d >= PATH_STEP * (len(out) + 1) and len(out) < PATH_POINTS:
            t = (PATH_STEP * (len(out) + 1) - acc) / d
            out.append(tuple(round(a[i] + (b[i] - a[i]) * t, 2) for i in range(3)))
        acc += d
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=DATA)
    args = ap.parse_args()
    body = Body(args.data, 'female')
    line = midline(body)
    for name, centre, axis in (('VAGINA_PATH', pd.VAGINA_CENTRE, pd.VAGINA_AXIS), ('ANUS_PATH', pd.ANUS_CENTRE, pd.ANUS_AXIS)):
        pts = path(line, centre, axis)
        print(f'{name} = {tuple(pts)}')
        for q in pts:
            print(f'    {q}  flesh {min(math.dist(q, v) for v in body.ref):.2f}')


if __name__ == '__main__':
    main()
