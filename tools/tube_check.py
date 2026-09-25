"""What the vagina and anus feel of the partner: his collider balls (as OCBPC collides them) or one tube (the
fork's [Tube], Tube.h), against the flesh of his penis as the fork shapes it (A-31) - measured, before the game.

1. The surface a labia / anus sphere rests on, along the shaft: OCBPC collides sphere against sphere and ADDS
   every overlap, so the balls give max_i sqrt((r_i + rl)^2 - d_i^2) - rl; the tube gives the flesh itself.
   Compared with the mesh's MEAN radius (the fork's [Mouth] skin reads the shaft the same way).
2. fit_check's OCBPC port (ocbpc_sim.run_insert, fit_check.judge) on the deployed body and its own physics,
   per opening and shaft path: the stretch group's smallest push across the axis against its knee, each
   bone's wobble while thrusting, and fit_check's "through" count - with the balls, and with the tube
   (ported here exactly: one push per tube, its deepest, the radius straight between points).

    python tools/tube_check.py             # head x1.25 (SHAPE's headMax), shaft SHAPE['shaft']

Needs fo4-silhouette's tools (mesh.py) and the game's Data folder, as glans_profile.py does.
"""
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'fo4-silhouette' / 'tools' / 'pool'))
sys.path.insert(0, str(HERE.parents[1] / 'fo4-silhouette' / 'tools'))
sys.path.insert(0, str(HERE))
import align_body as ab     # noqa: E402
import fit_check as fc      # noqa: E402
import mesh                 # noqa: E402
import nif                  # noqa: E402
import ocbpc_sim as sim     # noqa: E402
import physics_design as pd  # noqa: E402

DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
NAMES = ('Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05')
SHAFT_R, HEAD_R = pd.COLLIDERS['Penis_01'][0][3], pd.COLLIDERS['Penis_05'][0][3]
SKIN = pd.MOUTH['skin']
STEP = 0.25                                 # the tube's sampling for the port (piecewise linear either way)


def penis(shaft, head):
    """The bones along the axis and the flesh's mean radius there, the fork's shape applied."""
    b = mesh.Body(DATA, 'male')
    er = b.build({'Erection': 1.0})
    moved = [i for i in range(len(b.ref)) if math.dist(er[i], b.ref[i]) > 0.3]
    tip = max(moved, key=lambda i: er[i][1])
    root_pts = sorted(moved, key=lambda i: math.dist(er[i], b.ref[i]))[:20]
    root = [sum(er[i][k] for i in root_pts) / len(root_pts) for k in range(3)]
    ax = [er[tip][k] - root[k] for k in range(3)]
    L = math.sqrt(sum(c * c for c in ax))
    ax = [c / L for c in ax]
    n = nif.Nif(DATA / 'Meshes' / 'Actors' / 'Character' / 'CharacterAssets' / 'MaleBody.nif')
    s = [x for x in n.shapes() if x.count == len(b.ref)][0]
    bones, bxf = n.skin(s)
    O = {nm: nif.bone_origin(bxf[bones.index(nm)]) for nm in NAMES}
    H = {nm: sum((O[nm][j] - root[j]) * ax[j] for j in range(3)) for nm in NAMES}
    bins = {}
    for i in moved:
        p = list(er[i])
        for sl, w in s.skin_weights(i):
            nm = bones[sl]
            if nm in O:
                sc = head if nm == 'Penis_05' else shaft
                p = [p[k] + w * (sc - 1.0) * (er[i][k] - O[nm][k]) for k in range(3)]
        d = [p[k] - root[k] for k in range(3)]
        h = sum(d[k] * ax[k] for k in range(3))
        r = math.sqrt(max(0.0, sum(c * c for c in d) - h * h))
        bins.setdefault(round(h / 0.5), []).append(r)
    return H, {k * 0.5: sum(rs) / len(rs) for k, rs in sorted(bins.items())}


def tube_points(H, head):
    """The fork's tube along the axis: each bone's collider less the skin, the last replaced by the glans
    profile (Glans.h: along x R from the tip bone, radius x R, + skin, then less the skin)."""
    R = HEAD_R * head
    pts = [(H[nm], SHAFT_R * pd.SHAPE['shaft'] - SKIN) for nm in NAMES[:-1]]
    prev = H[NAMES[-2]]
    for along, radius in pd.GLANS_PROFILE:
        at = H[NAMES[-1]] + along * R
        if at > prev:
            pts.append((at, radius * R))
    return pts


def tube_radius(pts, h):
    if h < pts[0][0] or h > pts[-1][0]:
        return None
    for (h0, r0), (h1, r1) in zip(pts, pts[1:]):
        if h0 <= h <= h1:
            return r0 + (r1 - r0) * (h - h0) / max(h1 - h0, 1e-6)
    return pts[-1][1]


def felt_balls(balls, h, rl):
    best = -1e9
    for hi, r in balls:
        d = abs(h - hi)
        if d < r + rl:
            best = max(best, math.sqrt((r + rl) ** 2 - d * d) - rl)
    return best


def tube_push(self, at, colliders):
    """Tube.h Push, on ocbpc_sim's colliders read as a polyline of (centre, radius): the deepest overlap."""
    hit, best, out = False, 0.0, [0.0, 0.0, 0.0]
    for (a, ra), (b, rb) in zip(colliders, colliders[1:]):
        ab_ = [b[k] - a[k] for k in range(3)]
        ac = [at[k] - a[k] for k in range(3)]
        l2 = sum(x * x for x in ab_)
        s = max(0.0, min(1.0, sum(ac[k] * ab_[k] for k in range(3)) / l2)) if l2 > 1e-8 else 0.0
        p = [a[k] + ab_[k] * s for k in range(3)]
        r = ra + (rb - ra) * s
        d = [at[k] - p[k] for k in range(3)]
        dist = math.sqrt(sum(x * x for x in d))
        depth = r + self.radius - dist
        if depth > 0 and depth > best:
            best, hit = depth, True
            out = [x * depth / dist * self.dup for x in d] if dist > 1e-5 else [0.0, 0.0, depth]
    return hit, out


def main():
    shaft, head = pd.SHAPE['shaft'], pd.SHAPE['headMax']
    H, flesh = penis(shaft, head)
    balls = [(H[nm], (HEAD_R * head) if nm == 'Penis_05' else SHAFT_R * shaft) for nm in NAMES]
    tube = tube_points(H, head)
    print(f'shaft x{shaft}, head x{head}; balls ' + ', '.join(f'{h:.2f}:{r:.2f}' for h, r in balls))
    print('1. the surface a sphere rests on, less the flesh (mean radius); + off it, - into it')
    for name, rl in (('labia (r 1.2)', 1.2), ('anus sides (r 0.6)', 0.6), ('anus front (r 0.3)', 0.3)):
        for who in ('balls', 'tube'):
            parts = {'shaft body': [], 'crown': [], 'tip': []}
            for h, r in flesh.items():
                if h < 3.0:
                    continue                       # the root, in his body
                f = felt_balls(balls, h, rl) if who == 'balls' else tube_radius(tube, h)
                if f is None or f < -1e8:
                    continue
                part = 'shaft body' if h <= H['Penis_04'] else 'crown' if h <= H['Penis_05'] - 0.8 else 'tip'
                parts[part].append(f - r)
            print(f'   {name:19} {who:5}: ' + ', '.join(f'{k} {min(v):+.2f} .. {max(v):+.2f}' for k, v in parts.items() if v))

    print('2. fit_check\'s OCBPC port on the deployed body (its own physics)')
    plugins = ab.DEFAULT_DATA / 'F4SE/Plugins'
    b = fc.Build('deployed', fc.DEPLOYED / fc.BODY,
                 [plugins / 'ocbp.ini', fc.DEPLOYED / 'F4SE/Plugins/Anatomy/ocbp.ini'],
                 [plugins / 'OCBPCollisionConfig.txt', fc.DEPLOYED / 'F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt'])
    knee = {int(float(s.get('stretchGroup', 0) or 0)): float(s.get('stretchKnee', 0)) for s in b.section.values()}
    first = min(h for h, _ in tube)
    dense = [tube_radius(tube, first + k * STEP) for k in range(int((tube[-1][0] - first) / STEP) + 1)]
    partners = {'balls': ([r for _, r in balls], pd.PENIS_SPACING, sim.Bone._push),
                'tube': (dense, STEP, tube_push)}
    for opening, o in pd.OPENINGS.items():
        for path, (centre, axis) in fc.paths(opening).items():
            if path not in ('as drawn', 'steeper', 'flatter'):
                continue
            for who, (radii, spacing, push_fn) in partners.items():
                saved = sim.Bone._push
                sim.Bone._push = push_fn
                try:
                    pushes, wobble = {}, {}
                    for bone in o['bones']:
                        ox, oy, oz, r = b.affected[bone]
                        rest = pd.REST[bone]
                        res = sim.run_insert(b.section[bone], [rest[0] + ox, rest[1] + oy, rest[2] + oz], list(centre),
                                             list(axis), radii, spacing, r)
                        pushes[bone] = res['hold_vec'] or [0.0, 0.0, 0.0]
                        wobble[bone] = res['thrust_max'] - res['thrust_min']
                finally:
                    sim.Bone._push = saved
                ax_ = pd.unit(pd.STRETCH['Labia' if opening == 'vagina' else 'Anus']['axis'])
                across = [math.sqrt(max(0.0, sum(x * x for x in v) - sum(v[k] * ax_[k] for k in range(3)) ** 2))
                          for v in pushes.values()]
                g = 1 if opening == 'vagina' else 2
                n, inside, worst, _, _ = fc.judge(b, centre, axis, {**{x: [0, 0, 0] for x in b.affected}, **pushes})
                print(f'   {opening:6} {path:9} {who:5}: smallest push across {min(across):.2f} (knee {knee.get(g, 0):.2f}), '
                      f'thrust wobble {max(wobble.values()):.2f}, through {inside}/{n} ({100 * inside / max(n, 1):.0f}%)')


if __name__ == '__main__':
    main()
