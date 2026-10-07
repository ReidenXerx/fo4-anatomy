"""Servitron's canal wrap, simulated (fo4-ocbpc Canal.cpp, step for step, as studies/canal_wrap_sim.py does for ours): a
shaft of SHAFT_RADIUS along SRV_VAGINA_PATH to a tip depth, its wrap rings (SRV_CANAL_BONES) placed round it, the
rigged canal skinned with its weights. Wall points inside the shaft, before and with the wrap.

    python studies/servitron_wrap_sim.py <rigged Abdomen ... Rubber.nif>
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402

n = nif.Nif(sys.argv[1])
s = next(x for x in n.shapes() if x.name.endswith('_VInsides'))
bones, _ = n.skin(s)
pos = s.positions()
C = pd.CANAL
R, S = C['rings'], C['spokes']
c0, ax = pd.SRV_VAGINA_CENTRE, pd.SRV_VAGINA_AXIS


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


path = list(pd.SRV_VAGINA_PATH)
cum = [0.0]
for a, b in zip(path, path[1:]):
    cum.append(cum[-1] + math.dist(a, b))


def shaft_to(L):
    out = [sub(path[0], mul(ax, 2.0))]
    for k in range(len(path) - 1):
        out.append(path[k])
        if cum[k + 1] >= L:
            out.append(add(path[k], mul(sub(path[k + 1], path[k]), (L - cum[k]) / (cum[k + 1] - cum[k]))))
            return out
    return out + [path[-1]]


rest = {b: pd.SRV_CANAL_BONES[b] for b in pd.SRV_CANAL_BONES}
name = lambda k, j: f'{pd.SRV_CANAL_PREFIX}{k + 1}_{j}'
centre = [mul(tuple(sum(rest[name(k, j)][i] for j in range(S)) for i in range(3)), 1 / S) for k in range(R)]


def wrap(shaft):
    tip = shaft[-1]
    moved = {}
    for k in range(R):
        axis = unit(sub(centre[min(R - 1, k + 1)], centre[max(0, k - 1)]))
        o = max(0.0, min(1.0, (dot(sub(tip, centre[k]), axis) + C['lead']) / C['lead']))
        o = o * o * (3 - 2 * o)
        d, at = nearest(shaft, centre[k])
        for j in range(S):
            b = name(k, j)
            if o <= 0 or d > C['reach']:
                moved[b] = (0.0, 0.0, 0.0)
                continue
            dr = unit(sub(rest[b], centre[k]))
            r = max(C['radius'], math.dist(rest[b], centre[k]))
            moved[b] = mul(sub(add(at, mul(dr, r)), rest[b]), o)
    return moved


def skinned(moved):
    out = []
    for i in range(s.count):
        d = (0.0, 0.0, 0.0)
        for sl, w in s.skin_weights(i):
            if bones[sl] in moved:
                d = add(d, mul(moved[bones[sl]], w))
        out.append(add(pos[i], d))
    return out


print(f'{s.name}: {s.count} vertices; shaft radius {pd.SHAFT_RADIUS}; radius {C["radius"]}')
sample = list(range(0, s.count, 5))
for L in (4.0, 7.0, 10.0, 12.5):
    shaft = shaft_to(L)
    tipdepth = dot(sub(shaft[-1], c0), ax)
    for label, at in (('as rigged', pos), ('wrapped  ', skinned(wrap(shaft)))):
        reached = [i for i in sample if 2.0 < dot(sub(pos[i], c0), ax) < tipdepth - 0.5]
        ds = [nearest(shaft, at[i])[0] for i in reached]
        if not ds:
            continue
        inside = [x for x in ds if x < pd.SHAFT_RADIUS - 0.05]
        print(f'  tip {L:4.1f} along: {label} {len(inside):4d} of {len(ds):4d} sampled wall points inside the shaft '
              f'(worst {max(0.0, pd.SHAFT_RADIUS - min(ds)):.2f}), loosest {max(ds) - pd.SHAFT_RADIUS:+.2f}')
