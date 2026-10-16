"""How far the skin sits from each of the climax fluid's body capsules (fo4-ocbpc Fluid.cpp kParts), measured on the
game's own deployed bodies: the women's (Ivy's built Anatomy 3BBB, CBBE shape) and the men's (BodyTalk), at rest.

Each capsule runs between two skeleton bones (skeleton.nif, composed to world; the matrix convention is the one that
puts SPINE1/SPINE2/Chest where the body's skin data says they are). Its vertices: those whose strongest weight is on a
bone of that body part, and that project inside the segment (10-90%: the caps belong to the next part). The radius
printed is the median distance from the segment (and the 25th/75th): a capsule at the median has half the skin outside
it, so fluid on it sits on the skin, not under it.

    python studies/fluid_body_capsules.py
"""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
import nif  # noqa: E402

ASSETS = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Meshes\Actors\Character\CharacterAssets')
# (a, b, the skin bones that belong to it): Fluid.cpp's kParts
PARTS = [
    ('SPINE1', 'Chest', ('Spine1', 'SPINE1', 'Spine2', 'SPINE2', 'Chest', 'UpperBelly', 'RibHelper')),
    ('Pelvis', 'SPINE1', ('Pelvis', 'Belly')),
    ('LLeg_Thigh', 'LLeg_Calf', ('LLeg_Thigh',)), ('RLeg_Thigh', 'RLeg_Calf', ('RLeg_Thigh',)),
    ('LLeg_Calf', 'LLeg_Foot', ('LLeg_Calf',)), ('RLeg_Calf', 'RLeg_Foot', ('RLeg_Calf',)),
    ('LArm_UpperArm', 'LArm_ForeArm1', ('LArm_UpperArm', 'LArm_UpperFat', 'LArm_UpperTwist')),
    ('RArm_UpperArm', 'RArm_ForeArm1', ('RArm_UpperArm', 'RArm_UpperFat', 'RArm_UpperTwist')),
    ('LArm_ForeArm1', 'LArm_Hand', ('LArm_ForeArm',)), ('RArm_ForeArm1', 'RArm_Hand', ('RArm_ForeArm',)),
]


def mat_vec(r, v, transpose):
    m = (r[0:3], r[3:6], r[6:9])
    if transpose:
        return tuple(m[0][i] * v[0] + m[1][i] * v[1] + m[2][i] * v[2] for i in range(3))
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))


def mat_mul(a, b, transpose):
    # world rotation of a child: parent applied after child (same convention as mat_vec)
    A = (a[0:3], a[3:6], a[6:9])
    B = (b[0:3], b[3:6], b[6:9])
    if transpose:   # rows hold axes: child rows expressed through the parent's rows
        return tuple(sum(B[i][k] * A[k][j] for k in range(3)) for i in range(3) for j in range(3))
    return tuple(sum(A[i][k] * B[k][j] for k in range(3)) for i in range(3) for j in range(3))


def skeleton_world(transpose):
    sk = nif.Nif(ASSETS / 'skeleton.nif')
    nodes = sk._nodes()
    parent = {k: i for i, n in nodes.items() for k in n['kids']}
    out = {}

    def world(i):
        n = nodes[i]
        if i not in parent or parent[i] not in nodes:
            return n['t'], n['r'], n['s']
        pt, pr, ps = world(parent[i])
        off = mat_vec(pr, tuple(c * ps for c in n['t']), transpose)
        return tuple(pt[k] + off[k] for k in range(3)), mat_mul(pr, n['r'], transpose), ps * n['s']
    for i, n in nodes.items():
        out[n['name']] = world(i)[0]
    return out


def seg_dist(p, a, b):
    ab = [b[i] - a[i] for i in range(3)]
    l2 = sum(c * c for c in ab)
    t = sum((p[i] - a[i]) * ab[i] for i in range(3)) / l2 if l2 else 0.0
    q = [a[i] + ab[i] * max(0.0, min(1.0, t)) for i in range(3)]
    return math.dist(p, q), t


def measure(body_file):
    n = nif.Nif(ASSETS / body_file)
    shape = max(n.shapes(), key=lambda s: s.count)
    names, xf = n.skin(shape)
    origins = {nm: nif.bone_origin(x) for nm, x in zip(names, xf) if nm}
    # the joints from the skin data itself: a skeleton bone where the body has it, else its _skin helper (which
    # sits on it). Composing skeleton.nif's tree came out ~95 units off per bone (10-17), so it is not used
    w = {}
    for a_, b_, _ in PARTS:
        for j in (a_, b_):
            for cand in (j, j + '_skin', j.replace('ForeArm1', 'ForeArm1_skin')):
                if cand in origins:
                    w[j] = origins[cand]
                    break
    print(f'{body_file} ({shape.name}, {shape.count} vertices)')
    pos = shape.positions()
    owner = []
    for i in range(shape.count):
        sw = shape.skin_weights(i)
        owner.append(names[max(sw, key=lambda p: p[1])[0]] if sw else None)
    for a, b, keys in PARTS:
        if a not in w or b not in w:
            print(f'  {a:14} {b:14} missing in the skeleton')
            continue
        ds = []
        for i, nm in enumerate(owner):
            if nm and any(nm.startswith(k) or k in nm for k in keys):
                d, t = seg_dist(pos[i], w[a], w[b])
                if 0.1 <= t <= 0.9:
                    ds.append(d)
        if len(ds) < 20:
            print(f'  {a:14} {b:14} only {len(ds)} vertices')
            continue
        q = statistics.quantiles(ds, n=4)
        print(f'  {a:14} {b:14} median {statistics.median(ds):5.2f}  (25% {q[0]:5.2f}, 75% {q[2]:5.2f})  {len(ds)} vertices')


if __name__ == '__main__':
    for f in ('FemaleBody.nif', 'MaleBody.nif'):
        measure(f)
