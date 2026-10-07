"""Servitron's own openings (the rubber abdomen, Nexus 32801) and a path for the penis aim inside her: up its own canal,
then on toward our VAGINA_PATH's deep end. For each path point: its clearance from every Servitron body piece that
could be worn around it (abdomens, torsos, legs), so a shaft of SHAFT_RADIUS never shows through her shell.

    python studies/servitron_path.py
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402

D = pathlib.Path(r'D:/F4Output/servitron/x/bs/Data/tools/BodySlide/ShapeData/Servitron')
OPENINGS = {'vagina': ('Abdomen_GITS_Rubber_VRing2', 'Abdomen_GITS_Rubber_VInsides'),
            'anus': ('Abdomen_GITS_Rubber_ARing2', 'Abdomen_GITS_Rubber_AInsides')}
rubber = nif.Nif(D / 'Abdomen GITS Rubber.nif')


def centre(ps):
    return tuple(sum(p[k] for p in ps) / len(ps) for k in range(3))


def unit(v):
    m = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / m for x in v)


out = {}
for name, (ring, ins) in OPENINGS.items():
    rp, ip = rubber.shape(ring).positions(), rubber.shape(ins).positions()
    c = centre(rp)
    far = max(ip, key=lambda p: math.dist(p, c))
    end = centre([p for p in ip if math.dist(p, far) < 0.6])
    out[name] = (c, unit(tuple(end[k] - c[k] for k in range(3))), end)
    print(f'{name}: entrance {tuple(round(x, 3) for x in c)}, axis {tuple(round(x, 3) for x in out[name][1])}, '
          f'canal end {tuple(round(x, 3) for x in end)} ({math.dist(c, end):.2f} deep)')

# body shells around the path: every piece but the openings' own canals and rings
shells = []
for f in sorted(D.glob('*.nif')):
    if not any(k in f.name for k in ('Abdomen', 'Torso', 'Legs')):
        continue
    n = nif.Nif(f)
    for s in n.shapes():
        if any(k in s.name for k in ('Insides', 'Ring', 'Privates', 'Cap')):
            continue
        shells.append((f.name, s.name, s.positions()))

c, ax, end = out['vagina']
path = [c, end] + [p for p in pd.VAGINA_PATH if p[2] > end[2] + 2.0]
print('vagina path:', [tuple(round(x, 2) for x in p) for p in path])
for p in path + [tuple((a + b) / 2 for a, b in zip(path[i], path[i + 1])) for i in range(len(path) - 1)]:
    worst = min(((min(math.dist(p, q) for q in ps), f, s) for f, s, ps in shells), default=(math.inf, '', ''))
    print(f'  {tuple(round(x, 2) for x in p)}: nearest shell {worst[0]:.2f} ({worst[1]} / {worst[2]})')
c, ax, end = out['anus']
print('anus: entrance', tuple(round(x, 3) for x in c), 'axis', tuple(round(x, 3) for x in ax))
