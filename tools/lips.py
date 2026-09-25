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
          (35, 'RLwrLipUp'), (8, 'LLipCornerOut'), (31, 'RLipCornerOut'), (7, 'LLipCornerIn'), (30, 'RLipCornerIn'))
# ACROSS: every morph also moves the rim's two ends (the mouth's inner corners), the head's horizontal
# room (the owner, 2026-09-25: "fit head of penis IN HORIZONTAL AXIS"). Jaw Open widens it 0.27 / 0.22,
# each funnel narrows it 0.08 a side, Corner Out takes its own end out 0.40 / 0.34 and the other 0.11.
# THE CORNERS THEMSELVES (2026-09-26, the owner: "the corner of mouth still kinda static"): the rim's ends
# are its extremes, and they are not the corners. The vertex where the lips meet (the rest extreme) is:
# Jaw Open takes it IN 0.26 / 0.18 while the opening's widest point (lower, on the dropped lip) goes out;
# Lip Corner In (7 / 30) takes its own corner in 0.32 / 0.38, which the extremes do not show (a neighbour
# bulges 0.11 out, with every corner morph: the 'other end 0.11' above is that vertex, not a corner). So
# each morph also carries its move of the two corner vertices, for the fork's hug of the shaft's sides.


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

    def filled(vals):
        """a sample the rim does not reach (a corner morph moves the corner past it): its nearest one's"""
        out = list(vals)
        for k, v in enumerate(out):
            if math.isnan(v):
                near = sorted((abs(j - k), vals[j]) for j in range(len(vals)) if not math.isnan(vals[j]))
                out[k] = near[0][1] if near else 0.0
        return out

    zero = [(0.0, 0.0, 0.0)] * len(verts)
    u0, l0 = edge(upper, zero), edge(lower, zero)
    cl = min(rim, key=lambda i: verts[i][0])     # the corners: where the lips meet, the rest extremes
    cr = max(rim, key=lambda i: verts[i][0])
    rest_gap = max(abs(a - b) for a, b in zip(u0, l0))
    ends = lambda d: (min(verts[i][0] + d[i][0] for i in rim), max(verts[i][0] + d[i][0] for i in rim))
    rest_ends = ends(zero)
    table = {}
    for mid, name in MORPHS:
        u, l = edge(upper, morphs[name]), edge(lower, morphs[name])
        lo, hi = ends(morphs[name])
        d = morphs[name]
        ends_move = (lo - rest_ends[0], hi - rest_ends[1])
        if name in ('LLipCornerIn', 'RLipCornerIn'):
            # its extremes move only by the neighbour's 0.11 bulge: to the fork's clearance that is a free
            # widening, which it took (Corner In at 0.6 with a head passing). It is the hug's knob, nothing else.
            ends_move = (0.0, 0.0)
        table[mid] = (filled([a - b for a, b in zip(u, u0)]), filled([a - b for a, b in zip(l, l0)]),
                      ends_move, (d[cl][0], d[cr][0]))
    return table, rest_gap, len(upper), len(lower), rest_ends, (verts[cl][0], verts[cr][0])


def corners(tri):
    """(rim's -x end, rim's +x end, how far Left Lip Corner Out takes the -x end, Right the +x end): the
    corners' room (the owner's look, 2026-09-25: the corner still clipped a shaft filling her mouth). Corner
    Out barely moves the lips' heights (+-0.07), so it is not in the table: it moves the corner OUT."""
    verts, tris, morphs = read_tri(tri)
    front = {i for i in range(len(verts)) if verts[i][1] > 5.5 and abs(verts[i][0]) < 3.4 and -5.0 < verts[i][2] < 0.5}
    ec = collections.Counter()
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ec[(min(a, b), max(a, b))] += 1
    rim = {v for e, c in ec.items() if c == 1 and e[0] in front and e[1] in front for v in e}
    lo = min(verts[i][0] for i in rim)
    hi = max(verts[i][0] for i in rim)
    left, right = morphs['LLipCornerOut'], morphs['RLipCornerOut']
    lo_out = min(verts[i][0] + left[i][0] for i in rim)
    hi_out = max(verts[i][0] + right[i][0] for i in rim)
    return lo, hi, lo - lo_out, hi_out - hi


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', type=pathlib.Path, default=DATA)
    args = ap.parse_args()
    import gamedata
    table, gap, nu, nl, span, corner = measure(gamedata.Game(args.data).read(HEAD_TRI))
    print(f'rim: upper {nu}, lower {nl} vertices, x {span[0]:.2f} .. {span[1]:.2f}; closed mouth gap {gap:.3f}')
    print(f'{"":14}' + ''.join(f'{x:+7.1f}' for x in XS))
    print(f'the corners (where the lips meet) at x {corner[0]:.2f} / {corner[1]:.2f}')
    for mid, name in MORPHS:
        u, l, (dl, dr), (cl, cr) = table[mid]
        print(f'{name:12} U' + ''.join(f'{v:+7.2f}' for v in u) + f'   ends {dl:+.2f} / {dr:+.2f}   corners {cl:+.2f} / {cr:+.2f}')
        print(f'{"":12} L' + ''.join(f'{v:+7.2f}' for v in l))
    lo, hi, ml, mr = corners(gamedata.Game(args.data).read(HEAD_TRI))
    print(f'corners: rim {lo:.2f} .. {hi:.2f}; Left Lip Corner Out takes the left end {ml:.2f} out, Right {mr:.2f}')
    bad = [MORPHS[k][1] for k, (mid, _) in enumerate(MORPHS) if any(math.isnan(v) for v in table[mid][0] + table[mid][1])]
    if bad or gap > 0.1:
        raise SystemExit(f'the rim is not what was measured (gap {gap:.3f}, unreadable: {bad})')


if __name__ == '__main__':
    main()
