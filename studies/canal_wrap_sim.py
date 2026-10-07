"""The canal's wrap, simulated (fo4-ocbpc Canal.cpp, step for step): a shaft of SHAFT_RADIUS laid along VAGINA_PATH to
a tip depth, the ring bones placed around it as [Canal] does, the canal wall skinned with the built weights (bones
translate only, so a vertex moves by the weighted sum of its bones' moves). For each tip depth: how much of the
wall the shaft is through (wall points closer to the shaft's axis than its radius), before the wrap and with it.

    python studies/canal_wrap_sim.py <Anatomy.nif (built, stage 6b3 or later)>
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import canal_depth as cd  # noqa: E402

n = nif.Nif(sys.argv[1])
s = n.shape(cd.SHAPE)
bones, _ = n.skin(s)
pos, tris = s.positions(), s.triangles()
tube = sorted(cd._tube(pos, tris))
C = pd.CANAL
R, S = C['rings'], C['spokes']


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def unit(a):
    m = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / m)


def nearest(line, p):
    best = None
    for a, b in zip(line, line[1:]):
        ab = sub(b, a)
        t = max(0.0, min(1.0, dot(sub(p, a), ab) / max(1e-9, dot(ab, ab))))
        q = add(a, mul(ab, t))
        d = math.dist(p, q)
        if best is None or d < best[0]:
            best = (d, q)
    return best


def shaft_to(depth):
    """VAGINA_PATH from the entrance (lead in 2 units outside) cut where it is `depth` along VAGINA_AXIS"""
    path = [add(pd.VAGINA_PATH[0], mul(pd.VAGINA_AXIS, -2.0))] + list(pd.VAGINA_PATH)
    out = [path[0]]
    for a, b in zip(path, path[1:]):
        da, db = cd.depth_of(a), cd.depth_of(b)
        if db >= depth:
            out.append(add(a, mul(sub(b, a), (depth - da) / (db - da))))
            return out
        out.append(b)
    return out


rest = {name: pd.CANAL_BONES[name] for name in pd.CANAL_BONES}
centre = [mul(tuple(sum(rest[pd.canal_bone(k, j)][i] for j in range(S)) for i in range(3)), 1 / S) for k in range(R)]


def wrap(shaft):
    tip = shaft[-1]
    moved = {}
    for k in range(R):
        axis = unit(sub(centre[min(R - 1, k + 1)], centre[max(0, k - 1)]))
        o = max(0.0, min(1.0, (dot(sub(tip, centre[k]), axis) + C['lead']) / C['lead']))
        o = o * o * (3 - 2 * o)
        d, at = nearest(shaft, centre[k])
        for j in range(S):
            b = pd.canal_bone(k, j)
            if o <= 0 or d > C['reach']:
                moved[b] = (0.0, 0.0, 0.0)
                continue
            dr = unit(sub(rest[b], centre[k]))
            r = max(C['radius'], math.dist(rest[b], centre[k]))
            moved[b] = mul(sub(add(at, mul(dr, r)), rest[b]), o)
    return moved


def skinned(moved):
    out = {}
    for i in tube:
        d = (0.0, 0.0, 0.0)
        for sl, w in s.skin_weights(i):
            if bones[sl] in moved:
                d = add(d, mul(moved[bones[sl]], w))
        out[i] = add(pos[i], d)
    return out


print(f'{len(tube)} canal vertices; shaft radius {pd.SHAFT_RADIUS}; [Canal] {C}')
for depth in (3.0, 5.0, 7.0, 9.0, 11.0, 12.5):
    shaft = shaft_to(depth)
    for label, at in (('as built', {i: pos[i] for i in tube}), ('wrapped ', skinned(wrap(shaft)))):
        reached = [i for i in tube if 1.0 < cd.depth_of(pos[i]) < depth - 0.5]
        ds = [nearest(shaft, at[i])[0] for i in reached]
        through = [x for x in ds if x < pd.SHAFT_RADIUS - 0.05]
        deepest = max((pd.SHAFT_RADIUS - x for x in ds), default=0.0)
        gap = sorted(ds)[len(ds) // 2] if ds else 0.0
        print(f'  tip {depth:4.1f} deep, {label}: {len(through):3d} of {len(reached):3d} wall points inside the shaft '
              f'(worst {max(0.0, deepest):.2f} in), median wall-to-axis {gap:.2f}')
