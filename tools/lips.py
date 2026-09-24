"""The lips around what is in her mouth (A-32): how each mouth expression morph moves the upper and the lower
lip's inner edge, across the mouth, measured on the female head's .tri. The fork fits these to the cross-section
of a shaft (or a hand) at her lips every frame, so the lips rest on it instead of the jaw opening a hole.

The inner edge is the rim of the head's mouth hole (edges of one triangle only), split by what moves it:
the upper lip's rim rises with Upper Lip Up, the lower lip's drops with Jaw Open. At rest the two meet (a
closed mouth measures a gap of 0.00-0.03). Heights are sampled at signed x across the mouth, in the head's
own units, and are relative to the resting edge.

    python tools/lips.py [--data <Data>]     prints the table; physics_config writes it into [Mouth]
"""
import argparse
import collections
import math
import pathlib
import struct

DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
HEAD_TRI = 'Meshes/Actors/Character/CharacterAssets/BaseFemaleHead.tri'
XS = (-1.2, -0.8, -0.4, 0.0, 0.4, 0.8, 1.2)
# (id in the engine's 54, name in the head's .tri): what can move a lip's inner edge (Rapport's make_mfg order)
MORPHS = ((2, 'JawOpen'), (22, 'LwrLipFunnel'), (46, 'UprLipFunnel'), (21, 'LUprLipUp'), (44, 'RUprLipUp'),
          (11, 'LLwrLipDn'), (34, 'RLwrLipDn'), (20, 'LUprLipDn'), (43, 'RUprLipDn'), (12, 'LLwrLipUp'),
          (35, 'RLwrLipUp'))


def read_tri(data):
    """(vertices, triangles, {morph: [delta]}) of a FRTRI003 file."""
    d = data
    if d[:8] != b'FRTRI003':
        raise SystemExit('not a FRTRI003 head tri')
    nv, nt, nq, _u2, _u3, nuv, flags, nm, _nmod, nmodv = struct.unpack('<14i', d[8:64])[:10]
    o = 64
    verts = [struct.unpack_from('<3f', d, o + 12 * i) for i in range(nv)]
    o += 12 * nv + 12 * nmodv
    tris = [struct.unpack_from('<3i', d, o + 12 * i) for i in range(nt)]
    o += 12 * nt + 16 * nq + 8 * nuv
    if flags & 1:
        o += 12 * nt + 16 * nq
    morphs = {}
    for _ in range(nm):
        (ln,) = struct.unpack_from('<i', d, o)
        o += 4
        name = d[o:o + ln].rstrip(b'\0').decode('ascii', 'replace')
        o += ln
        (mult,) = struct.unpack_from('<f', d, o)
        o += 4
        morphs[name] = [tuple(c * mult for c in struct.unpack_from('<3h', d, o + 6 * i)) for i in range(nv)]
        o += 6 * nv
    return verts, tris, morphs


def measure(tri):
    verts, tris, morphs = read_tri(tri)
    front = {i for i in range(len(verts)) if verts[i][1] > 5.5 and abs(verts[i][0]) < 3.4 and -5.0 < verts[i][2] < 0.5}
    ec = collections.Counter()
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ec[(min(a, b), max(a, b))] += 1
    rim = {v for e, c in ec.items() if c == 1 and e[0] in front and e[1] in front for v in e}
    up = lambda i: morphs['LUprLipUp'][i][2] + morphs['RUprLipUp'][i][2]
    upper = [i for i in rim if up(i) > 0.1 and verts[i][2] > -2.6]
    lower = [i for i in rim if morphs['JawOpen'][i][2] < -1.0 and up(i) < 0.1 and verts[i][2] > -2.6]

    def edge(group, delta):
        """the edge's height at each x (interpolated along the rim), with every vertex moved by delta."""
        pts = sorted((verts[i][0] + delta[i][0], verts[i][2] + delta[i][2]) for i in group)
        out = []
        for x in XS:
            z = float('nan')
            for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
                if x0 <= x <= x1 and x1 > x0:
                    z = z0 + (z1 - z0) * (x - x0) / (x1 - x0)
                    break
            out.append(z)
        return out

    zero = [(0.0, 0.0, 0.0)] * len(verts)
    u0, l0 = edge(upper, zero), edge(lower, zero)
    rest_gap = max(abs(a - b) for a, b in zip(u0, l0))
    table = {}
    for mid, name in MORPHS:
        u, l = edge(upper, morphs[name]), edge(lower, morphs[name])
        table[mid] = ([a - b for a, b in zip(u, u0)], [a - b for a, b in zip(l, l0)])
    return table, rest_gap, len(upper), len(lower), (min(verts[i][0] for i in rim), max(verts[i][0] for i in rim))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=DATA)
    args = ap.parse_args()
    import gamedata
    table, gap, nu, nl, span = measure(gamedata.Game(args.data).read(HEAD_TRI))
    print(f'rim: upper {nu}, lower {nl} vertices, x {span[0]:.2f} .. {span[1]:.2f}; closed mouth gap {gap:.3f}')
    print(f'{"":14}' + ''.join(f'{x:+7.1f}' for x in XS))
    for mid, name in MORPHS:
        u, l = table[mid]
        print(f'{name:12} U' + ''.join(f'{v:+7.2f}' for v in u))
        print(f'{"":12} L' + ''.join(f'{v:+7.2f}' for v in l))
    bad = [MORPHS[k][1] for k, (mid, _) in enumerate(MORPHS) if any(math.isnan(v) for v in table[mid][0] + table[mid][1])]
    if bad or gap > 0.1:
        raise SystemExit(f'the rim is not what was measured (gap {gap:.3f}, unreadable: {bad})')


if __name__ == '__main__':
    main()
