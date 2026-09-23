"""What a build's genitals do in contact, before the game (decision A-9): the deployed build vs the new one.

For each opening and several shaft paths around the one Nahka drew for (centre and canal axis in
physics_design.OPENINGS; shifted front/back and sideways, steeper, flatter):
  1. every affected bone is run through the OCBPC port (tools/ocbpc_sim.py) against the partner's
     collider spheres sliding in along the path, with the build's OWN configs (spheres parsed from
     its OCBPCollisionConfig.txt, springs from its ocbp.ini); the held offset is the bone's push;
  2. the build's own weights move every vertex by the sum of weight x push (linear blend skinning
     of translations: these bones do not rotate, rotational* = 0);
  3. around the entrance (from the canal mouth out along the shaft's path, radius < shaft + 0.3),
     count the vertices still inside a shaft of physics_design.SHAFT_RADIUS: those are what shows as
     the shaft passing THROUGH her. The deep canal (further in than 0.6) is hidden inside the shaft
     and is not counted;
  4. stretch: the 99th-percentile and worst growth of edges at least 0.05 long among triangles
     touching that region (a spike or tear shows as a large ratio; the slit's boundary loops hold
     edges of a few thousandths whose ratio means nothing, so they are left out);
  5. walking: each affected bone's worst offset at a walk and a run, times the heaviest weight it
     carries, is how far the genitals can visibly flap.

    python tools/fit_check.py                      # deployed Anatomy-dev vs build/ (project + config)
"""
import argparse
import math
import pathlib
import re
import sys

import align_body as ab
import nif
import ocbpc_sim as sim
import physics_design as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEPLOYED = pathlib.Path(r'D:\Vortex\fallout4\mods\Anatomy-dev')
BODY = 'Meshes/Actors/Character/CharacterAssets/FemaleBody.nif'
PENIS = ['Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05']
REGION_ALONG = (-2.5, 0.6)
CLIP = 0.15                     # inside the shaft by more than this counts as showing through


def parse_spheres(text):
    out, cur = {}, None
    for line in text.splitlines():
        line = line.split('#')[0].strip()
        m = re.match(r'^\[([^\]]+)\]', line)
        if m:
            cur = m.group(1).strip()
            continue
        if cur and re.match(r'^-?[\d.]+\s*,', line):
            vals = [float(v) for v in line.split(',')[:4]]
            out.setdefault(cur, []).append(tuple(vals))
    return out


def parse_ini(text):
    out, cur = {}, None
    for line in text.splitlines():
        line = line.split(';')[0].strip()
        m = re.match(r'^\[([^\]]+)\]', line)
        if m:
            cur = out.setdefault(m.group(1).strip(), {})
            continue
        if cur is not None and '=' in line:
            k, v = line.split('=', 1)
            try:
                cur[k.strip()] = float(v)
            except ValueError:
                cur[k.strip()] = v.strip()
    return out


class Build:
    def __init__(self, label, nif_path, ini_paths, col_paths):
        """ini_paths / col_paths: read in order, as the fork reads them (A-21): the player's files,
        then ours. A bone's section comes from the file whose [Attach] names it (a later file wins);
        a collision node gains every file's spheres."""
        self.label = label
        n = nif.Nif(nif_path)
        s = n.shape(ab.SHAPE)
        bones, _ = n.skin(s)
        self.pos = s.positions()
        self.tris = s.triangles()
        # the genitals' own shape (A-22) holds copies of body records: fold its triangles back onto the
        # body's vertices, matched by position and UV, so the whole surface is judged as one
        if any(g.name == 'AnatomyGenitals' for g in n.shapes()):
            g = n.shape('AnatomyGenitals')
            at = {}
            for j in range(s.count):
                at.setdefault((s.position(j), s.uv(j)), j)
            back = [at.get((g.position(k), g.uv(k))) for k in range(g.count)]
            if any(b is None for b in back):
                raise SystemExit(f'{nif_path}: {sum(b is None for b in back)} genital vertices have no body twin')
            self.tris = self.tris + [tuple(back[k] for k in t) for t in g.triangles()]
        self.weights = {}
        # a body weighted to the openings' stretch children (A-17) moves with their bones below the
        # stretch knee, which every path here stays under
        fold = {child: bone for bone, child in pd.STRETCH_BONES.items()}
        for j in range(s.count):
            w = {fold.get(bones[sl], bones[sl]): x for sl, x in s.skin_weights(j)
                 if fold.get(bones[sl], bones[sl]) in pd.REST}
            if w:
                self.weights[j] = w
        self.section = {}
        for ini_path in ini_paths:
            if not ini_path.exists():
                continue
            ini = parse_ini(ini_path.read_text(encoding='utf-8', errors='replace'))
            attach = ini.get('Attach', {})
            self.section.update({b: ini[attach[b]] for b in pd.REST if b in attach and attach[b] in ini})
        spheres = {}
        for col_path in col_paths:
            if col_path.exists():
                for node, rows in parse_spheres(col_path.read_text(encoding='utf-8', errors='replace')).items():
                    spheres.setdefault(node, []).extend(rows)
        self.affected = {b: spheres[b][0] for b in pd.REST if b in spheres}
        self.colliders = [max(r for *_, r in spheres[p]) for p in PENIS if p in spheres]


def pushes(build, centre, axis):
    out = {}
    for b, (ox, oy, oz, r) in build.affected.items():
        if b not in build.section:
            continue
        rest = pd.REST[b]
        sphere = [rest[0] + ox, rest[1] + oy, rest[2] + oz]
        res = sim.run_insert(build.section[b], sphere, list(centre), list(axis), build.colliders,
                             pd.PENIS_SPACING, r)
        out[b] = res['hold_vec'] or [0.0, 0.0, 0.0]
    return out


def judge(build, centre, axis, push, moved=None):
    weighted = moved is None
    if moved is None:
        moved = {}
        for j, w in build.weights.items():
            d = [sum(x * push.get(b, (0, 0, 0))[k] for b, x in w.items()) for k in range(3)]
            if any(abs(c) > 1e-6 for c in d):
                moved[j] = d
    region, inside, worst = [], 0, 0.0
    for j, p in enumerate(build.pos):
        rel = [p[k] - centre[k] for k in range(3)]
        along = sum(rel[k] * axis[k] for k in range(3))
        if not REGION_ALONG[0] <= along <= REGION_ALONG[1]:
            continue
        rad = math.sqrt(max(0.0, sum(c * c for c in rel) - along * along))
        if rad > pd.SHAFT_RADIUS + 0.3:
            continue
        region.append(j)
        q = [p[k] + moved.get(j, (0, 0, 0))[k] for k in range(3)]
        rel2 = [q[k] - centre[k] for k in range(3)]
        along2 = sum(rel2[k] * axis[k] for k in range(3))
        rad2 = math.sqrt(max(0.0, sum(c * c for c in rel2) - along2 * along2))
        depth = pd.SHAFT_RADIUS - rad2
        if depth > CLIP:
            inside += 1
            worst = max(worst, depth)
    rs = set(region)
    ratios = []
    for t in build.tris:
        if not rs.intersection(t):
            continue
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            l0 = math.dist(build.pos[a], build.pos[b])
            if l0 < 0.05:
                continue
            pa = [build.pos[a][k] + moved.get(a, (0, 0, 0))[k] for k in range(3)]
            pb = [build.pos[b][k] + moved.get(b, (0, 0, 0))[k] for k in range(3)]
            ratios.append(math.dist(pa, pb) / l0)
    ratios.sort()
    p99 = ratios[int(0.99 * (len(ratios) - 1))] if ratios else 1.0
    # a crack: two copies of one point (a UV seam) moved apart
    wid = nif.weld(build.pos)
    first, crack = {}, 0.0
    for j, g in enumerate(wid):
        d = moved.get(j, (0.0, 0.0, 0.0))
        if g in first:
            crack = max(crack, math.dist(first[g], d))
        else:
            first[g] = d
    if weighted:                        # the slider reference row is Nahka's data, not a build's weights
        build.crack = max(getattr(build, 'crack', 0.0), crack)
    return len(region), inside, worst, (p99, ratios[-1] if ratios else 1.0), clipped(build, centre, axis, moved, region)


def clipped(build, centre, axis, moved, region):
    """Where the vertices left inside the shaft are: by depth along the shaft and by side."""
    side = {'left': 0, 'right': 0, 'front': 0, 'back': 0}
    depth = {}
    front = pd.unit((0.0, axis[2], -axis[1]))
    for j in region:
        p = build.pos[j]
        q = [p[k] + moved.get(j, (0, 0, 0))[k] for k in range(3)]
        rel = [q[k] - centre[k] for k in range(3)]
        along = sum(rel[k] * axis[k] for k in range(3))
        radial = [rel[k] - along * axis[k] for k in range(3)]
        rad = math.sqrt(sum(c * c for c in radial))
        if pd.SHAFT_RADIUS - rad <= CLIP:
            continue
        fx, fy = radial[0], sum(radial[k] * front[k] for k in range(3))
        side['left' if fx < 0 and abs(fx) >= abs(fy) else 'right' if abs(fx) >= abs(fy) else 'front' if fy > 0 else 'back'] += 1
        key = f'{math.floor(along * 2) / 2:+.1f}'
        depth[key] = depth.get(key, 0) + 1
    return side, dict(sorted(depth.items()))


def paths(opening):
    o = pd.OPENINGS[opening]
    c, a = o['centre'], o['axis']
    shift = (lambda dx, dy: (c[0] + dx, c[1] + dy, c[2]))
    return {'as drawn': (c, a), '0.6 behind': (shift(0, -0.6), a), '0.6 ahead': (shift(0, 0.6), a),
            '0.4 right': (shift(0.4, 0), a), 'steeper': (c, pd.unit((0.0, 0.2, 1.0))),
            'flatter': (c, pd.unit((0.0, 0.8, 0.6)))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--old', type=pathlib.Path, default=DEPLOYED)
    args = ap.parse_args()
    # A-21: the physics the game runs is the player's files plus ours, merged by the fork
    plugins = ab.DEFAULT_DATA / 'F4SE/Plugins'
    builds = [Build('deployed', args.old / BODY,
                    [plugins / 'ocbp.ini', args.old / 'F4SE/Plugins/Anatomy/ocbp.ini'],
                    [plugins / 'OCBPCollisionConfig.txt', args.old / 'F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt']),
              Build('new', ab.OUT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif',
                    [plugins / 'ocbp.ini', ROOT / 'build/config/Anatomy/ocbp.ini'],
                    [plugins / 'OCBPCollisionConfig.txt', ROOT / 'build/config/Anatomy/OCBPCollisionConfig.txt'])]
    for b in builds:
        print(f'{b.label}: {len(b.weights)} vertices on the affected bones; colliders {b.colliders}; '
              f'affected {b.affected}')
    print(f'\nshaft radius {pd.SHAFT_RADIUS}; region: along -2.5..0.6 from the opening, within the shaft + 0.3; '
          f'"through" = inside by > {CLIP}')
    print(f'{"":8} {"path":11} | ' + ' | '.join(f'{b.label:>34}' for b in builds))
    print(f'{"":8} {"":11} | ' + ' | '.join(f'{"through/region  worst  stretch p99/max":>34}' for _ in builds))
    details = []
    import osd
    sliders = osd.read(ab.OUT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.osd')
    for opening, o in pd.OPENINGS.items():
        scale = pd.SHAFT_RADIUS / o['drawn_for']
        morph = {j: [c * scale for c in v] for j, v in sliders.get(ab.TARGET + o['morph'], {}).items()}
        n, inside, worst, (p99, smax), where = judge(builds[1], o['centre'], o['axis'], None, moved=morph)
        print(f'{opening:8} {"Nahka x" + format(scale, ".2f"):11} | {"(her slider, the target)":>34} | '
              f'{inside:4}/{n:<4} {100 * inside / max(n, 1):3.0f}%  {worst:4.2f}  {p99:4.2f}/{smax:5.2f}')
        details.append(f'   {opening}, Nahka slider: still inside by side {where[0]}; by depth {where[1]}')
        for name, (c, a) in paths(opening).items():
            cells = []
            for b in builds:
                push = pushes(b, c, a)
                n, inside, worst, (p99, smax), where = judge(b, c, a, push)
                cells.append(f'{inside:4}/{n:<4} {100 * inside / max(n, 1):3.0f}%  {worst:4.2f}  {p99:4.2f}/{smax:5.2f}')
                if name == 'as drawn':
                    details.append(f'   {opening} as drawn, {b.label}: still inside by side {where[0]}; by depth {where[1]}')
            print(f'{opening:8} {name:11} | ' + ' | '.join(f'{x:>34}' for x in cells))
    print('\n' + '\n'.join(details))
    print('\nwalking: worst bone offset x heaviest weight it carries (walk 1.5u @ 2 Hz / run 3u @ 3 Hz)')
    for b in builds:
        worst_walk = worst_run = 0.0
        for bone, sec in b.section.items():
            wmax = max((w.get(bone, 0.0) for w in b.weights.values()), default=0.0)
            worst_walk = max(worst_walk, wmax * sim.run_gait(sec, 1.5, 2.0))
            worst_run = max(worst_run, wmax * sim.run_gait(sec, 3.0, 3.0))
        print(f'  {b.label:9} walk {worst_walk:.2f}  run {worst_run:.2f}; worst crack across a seam in any case '
              f'{getattr(b, "crack", 0.0):.4f}')


if __name__ == '__main__':
    main()
