"""The mouth (decision A-20): measure it on the game's own heads, and check what the fork will do with it.

FO4 heads have no mouth bones; a face moves through 50 expression morphs (Jaw Open is id 2). The
fo4-ocbpc fork writes the face's merged weights over the animation's while a penis chain crosses the
plane of her lips (CBPSSE/Mouth.cpp). It needs four facts about the head, in the HEAD bone's space:
where the lips meet, which way they face, which way is up, and how far Jaw Open 1.0 parts them.

  1. measure: BaseFemaleHead / BaseMaleHead (.nif + expression .tri) out of Fallout4 - Meshes.ba2.
     Lower lip = front midline vertices Jaw Open moves > 1.5; upper lip = those it moves < 0.3; the
     lip line is where the two meet; into bone space through the head shape's own HEAD skin transform.
     Every number must match physics_design.MOUTH (what physics_config.py writes into ocbp.ini).
  2. the solver, mirrored from Mouth.cpp: shafts at, below and above the lip line, a tip on its way,
     one beside the mouth, one passing far off. Each must give the Jaw Open it was designed to.

    python tools/mouth.py
"""
import math
import pathlib
import struct
import sys
import zlib

import nif
import physics_design as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
BA2 = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data\Fallout4 - Meshes.ba2')
HEADS = {'female': 'BaseFemaleHead', 'male': 'BaseMaleHead'}
OUT = ROOT / 'build/heads'
TOLERANCE = 0.02


def ba2_extract(archive, wanted, out):
    """{name: path} for the GNRL BA2 entries whose lowercase name ends with one of `wanted`."""
    got = {}
    with open(archive, 'rb') as f:
        magic, _version, kind, count, names_at = struct.unpack('<4sI4sIQ', f.read(24))
        if magic != b'BTDX' or kind != b'GNRL':
            raise SystemExit(f'{archive}: not a general BA2')
        records = [struct.unpack('<I4sIIQIII', f.read(36)) for _ in range(count)]
        f.seek(names_at)
        names = []
        for _ in range(count):
            (n,) = struct.unpack('<H', f.read(2))
            names.append(f.read(n).decode('utf-8', 'replace'))
        for name, rec in zip(names, records):
            low = name.lower().replace('\\', '/')
            hit = next((w for w in wanted if low.endswith(w)), None)
            if not hit:
                continue
            _hash, _ext, _dir, _flags, offset, packed, size, _align = rec
            f.seek(offset)
            blob = f.read(packed or size)
            data = zlib.decompress(blob) if packed else blob
            path = out / pathlib.Path(low).name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            got[hit] = path
    missing = [w for w in wanted if w not in got]
    if missing:
        raise SystemExit(f'{archive} has no {missing}')
    return got


def read_tri(path):
    """FaceGen FRTRI003: base vertices and {morph: [delta per vertex]}."""
    d = pathlib.Path(path).read_bytes()
    if d[:8] != b'FRTRI003':
        raise SystemExit(f'{path}: not FRTRI003')
    nv, nt, nq, _u2, _u3, nuv, flags, nm, _nmod, nmodv = struct.unpack('<10i', d[8:48])
    o = 64
    verts = [struct.unpack_from('<3f', d, o + 12 * i) for i in range(nv)]
    o += 12 * nv + 12 * nmodv + 12 * nt + 16 * nq + 8 * nuv
    if flags & 1:
        o += 12 * nt + 16 * nq
    morphs = {}
    for _ in range(nm):
        (n,) = struct.unpack_from('<i', d, o)
        name = d[o + 4:o + 4 + n].rstrip(b'\0').decode('ascii', 'replace')
        o += 4 + n
        (mult,) = struct.unpack_from('<f', d, o)
        o += 4
        morphs[name] = [tuple(c * mult for c in struct.unpack_from('<3h', d, o + 6 * i)) for i in range(nv)]
        o += 6 * nv
    if o != len(d):
        raise SystemExit(f'{path}: parsed {o} of {len(d)} bytes')
    return verts, morphs


def rot(r9, v):
    return [r9[0] * v[0] + r9[1] * v[1] + r9[2] * v[2],
            r9[3] * v[0] + r9[4] * v[1] + r9[5] * v[2],
            r9[6] * v[0] + r9[7] * v[1] + r9[8] * v[2]]


def measure(head_nif, head_tri):
    verts, morphs = read_tri(head_tri)
    jaw = morphs['JawOpen']
    moved = [math.sqrt(sum(c * c for c in d)) for d in jaw]
    front = max(v[1] for v in verts)
    near = [i for i, v in enumerate(verts) if abs(v[0]) < 0.6 and v[1] > front - 2.2]
    lower = [i for i in near if moved[i] > 1.5]
    upper = [i for i in near if moved[i] < 0.3]
    top = max(lower, key=lambda i: verts[i][2])
    bottom = min((i for i in upper if verts[i][2] > verts[top][2] - 0.3), key=lambda i: verts[i][2])
    a, b = verts[bottom], verts[top]
    lip_line = (0.0, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)        # symmetric: on the midline
    opened = [b[k] + jaw[top][k] for k in range(3)]
    gap = math.dist(a, opened)
    h = nif.Nif(head_nif)
    shape = h.shapes()[0]
    bones, skin_xf = h.skin(shape)
    r, t, s = skin_xf[bones.index('HEAD')]
    mouth = [s * c + t[k] for k, c in enumerate(rot(r, lip_line))]
    return dict(mouth=mouth, facing=rot(r, [0.0, 1.0, 0.0]), up=rot(r, [0.0, 0.0, 1.0]), gap=gap,
                vertices=len(verts), morphs=len(morphs))


# ---- the solver, as Mouth.cpp runs it (one frame, no smoothing) ----------------------------------

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


def norm(a):
    n = math.sqrt(dot(a, a))
    return mul(a, 1.0 / n) if n > 1e-6 else (0.0, 0.0, 0.0)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def section_half_u(a, f, u, r):
    c = max(0.25, abs(dot(a, f)))
    m = sub(a, mul(f, dot(a, f)))
    ml = math.sqrt(dot(m, m))
    if ml < 1e-4:
        return r
    m = mul(m, 1.0 / ml)
    n = cross(f, m)
    return math.hypot(dot(m, u) * r / c, dot(n, u) * r)


def solve(chain, mouth, f, u, gap, cfg=pd.MOUTH):
    """chain: [(point, collider radius)], base to tip. Returns (inside, jaw target, lift target, approach)."""
    s = cross(f, u)
    vis = lambda r: max(0.2, r - cfg['skin'])                        # noqa: E731
    need, over, approach, inside = 0.0, -1e9, 0.0, False

    def consider(x, r, direction):
        nonlocal need, over, inside
        q = sub(x, mouth)
        qs, qu = dot(q, s), dot(q, u)
        if abs(qs) > cfg['halfWidth'] or qu < -cfg['below'] or qu > cfg['above']:
            return
        hu = section_half_u(direction, f, u, r)
        inside = True
        need, over = max(need, hu - qu), max(over, qu + hu)

    for (p0, r0), (p1, r1) in zip(chain, chain[1:]):
        d0, d1 = dot(sub(p0, mouth), f), dot(sub(p1, mouth), f)
        if (d0 > 0) == (d1 > 0):
            continue
        t = d0 / (d0 - d1)
        consider(add(p0, mul(sub(p1, p0), t)), vis(r0 + (r1 - r0) * t), norm(sub(p1, p0)))
    base, rb = chain[0]
    db = dot(sub(base, mouth), f)
    if db <= 0 and db > -(vis(rb) + 2.0) and len(chain) > 1:
        consider(sub(base, mul(f, db)), vis(rb), norm(sub(chain[1][0], base)))
    tip, rt = chain[-1]
    dt, vt = dot(sub(tip, mouth), f), vis(rt)
    if abs(dt) < vt:
        direction = norm(sub(tip, chain[-2][0])) if len(chain) > 1 else mul(f, -1)
        consider(sub(tip, mul(f, dt)), math.sqrt(vt * vt - dt * dt), direction)
    elif 0 < dt and dt - vt < cfg['ahead']:
        q = sub(sub(tip, mouth), mul(f, dt))
        if abs(dot(q, s)) <= cfg['halfWidth'] and -cfg['below'] <= dot(q, u) <= cfg['above']:
            approach = max(approach, 1.0 - (dt - vt) / cfg['ahead'])
    jaw = min(1.0, max(0.0, need / gap + cfg['margin'])) if inside else 0.0
    lift = min(1.0, max(0.0, over / cfg['liftMove'])) if inside and over > 0 else 0.0
    return inside, jaw, lift, approach


def shaft(tip_at, direction, radii=(2.0, 2.0, 2.0, 2.0, 1.8), spacing=3.0):
    """A straight penis chain whose tip (Penis_05) is at tip_at, pointing along direction."""
    d = norm(direction)
    n = len(radii)
    return [(add(tip_at, mul(d, -spacing * (n - 1 - i))), r) for i, r in enumerate(radii)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = [f'characterassets/{n.lower()}.{e}' for n in HEADS.values() for e in ('nif', 'tri')]
    files = ba2_extract(BA2, wanted, OUT)
    cfg = pd.MOUTH
    worst = 0.0
    measured = {}
    print('1. the heads (HEAD bone space; physics_design.MOUTH in brackets)')
    for sex, name in HEADS.items():
        m = measure(files[f'characterassets/{name.lower()}.nif'], files[f'characterassets/{name.lower()}.tri'])
        measured[sex] = m
        want_mouth = (cfg[f'{sex}X'], cfg[f'{sex}Y'], cfg[f'{sex}Z'])
        want_f = (cfg['facingX'], cfg['facingY'], cfg['facingZ'])
        want_u = (cfg['upX'], cfg['upY'], cfg['upZ'])
        errs = [max(abs(a - b) for a, b in zip(m['mouth'], want_mouth)), max(abs(a - b) for a, b in zip(m['facing'], want_f)),
                max(abs(a - b) for a, b in zip(m['up'], want_u)), abs(m['gap'] - cfg[f'{sex}Gap'])]
        worst = max(worst, *errs)
        print(f'   {name}: {m["vertices"]} vertices, {m["morphs"]} morphs; lips meet at '
              f'({m["mouth"][0]:.2f}, {m["mouth"][1]:.2f}, {m["mouth"][2]:.2f}) [{want_mouth}], facing '
              f'({m["facing"][0]:.3f}, {m["facing"][1]:.3f}, {m["facing"][2]:.3f}), up ({m["up"][0]:.3f}, '
              f'{m["up"][1]:.3f}, {m["up"][2]:.3f}); Jaw Open 1.0 parts them {m["gap"]:.2f} [{cfg[f"{sex}Gap"]}]')
    if worst > TOLERANCE:
        raise SystemExit(f'physics_design.MOUTH is off the game\'s heads by {worst:.3f} (> {TOLERANCE}): update it')

    # 2. the solver in the bone frame itself (the plugin rotates it into the world; the geometry is the same)
    m = measured['female']
    mouth, f, u = tuple(m['mouth']), norm(tuple(m['facing'])), norm(tuple(m['up']))
    gap = cfg['femaleGap']
    vis = pd.SHAFT_RADIUS
    scenes = [
        # (label, chain, expected inside, expected jaw (None = any), expected lift (None = any))
        ('centred on the lip line, 3 in', shaft(sub(mouth, mul(f, 3.0)), mul(f, -1)), True, vis / gap + cfg['margin'], 1.0),
        ('a unit below the lip line', shaft(add(sub(mouth, mul(f, 3.0)), mul(u, -1.0)), mul(f, -1)), True,
         min(1.0, (vis + 1.0) / gap + cfg['margin']), None),
        ('its top on the lip line', shaft(add(sub(mouth, mul(f, 3.0)), mul(u, -vis)), mul(f, -1)), True,
         min(1.0, 2 * vis / gap + cfg['margin']), 0.0),
        ('tip 2 in front of the lips', shaft(add(mouth, mul(f, 2.0 + 1.35)), mul(f, -1)), False, 0.0, 0.0),
        ('beside the mouth (4 to the side)', shaft(add(sub(mouth, mul(f, 3.0)), mul(cross(f, u), 4.0)), mul(f, -1)),
         False, 0.0, 0.0),
        ('passing 20 below (her chest)', shaft(add(mouth, mul(u, -20.0)), mul(f, -1)), False, 0.0, 0.0),
    ]
    print('2. the solver (female head; visible shaft radius 1.55, tip 1.35)')
    bad = []
    for label, chain, want_inside, want_jaw, want_lift in scenes:
        inside, jaw, lift, approach = solve(chain, mouth, f, u, gap)
        ok = inside == want_inside and (want_jaw is None or abs(jaw - want_jaw) < 0.02) and \
            (want_lift is None or abs(lift - want_lift) < 0.02)
        print(f'   {"ok " if ok else "BAD"} {label:34} inside {str(inside):5} Jaw Open {jaw:.2f} lift {lift:.2f} '
              f'approach {approach:.2f}')
        if not ok:
            bad.append(label)
    tip_inside, _, _, tip_approach = solve(scenes[3][1], mouth, f, u, gap)
    if tip_approach <= 0.0:
        bad.append('the approaching tip did not register')
    if bad:
        raise SystemExit(f'the solver does not do what it was designed to: {bad}')
    print('PASS - the heads match the design and the solver opens the mouth only for what is in it')


if __name__ == '__main__':
    sys.exit(main())
