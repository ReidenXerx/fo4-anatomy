"""The men's anus (A-69; the owner 2026-10-01: "players desperately wait it on nexus lets do it rn").

BodyTalk 4 (Nude and Uncut) models a closed anus pucker on its own Anus_01-04 bones, about 0.6 units deep; there is no
opening (NeverNude has none at all). The owner's pick: open BodyTalk's own pucker, not a transplant of Nahka's, so the
look stays BodyTalk's and nothing but the player's own BodyTalk is used.

The canal is the women's (anal_canal.py, A-50) with the men's Spec:
  - the opening: the pucker's vertices within OPEN_R of its axis, at any depth (a shallow pucker has no cup floor to
    find by depth; its Anus_01-04 weights form a ring, not a disk). 0.6 gives one loop of 12, radius 0.53 (the
    women's ring is 0.45);
  - the canal: straight in along the pucker's axis for 1.5 units, then up the pelvis tilted 12 degrees back.
    studies/male_anus_probe.py measured the room: tilted 0-15 degrees the walls keep 2.7-3.9 units of flesh to the skin
    all the way; at 45 degrees and beyond they come out through the buttock cleft.

    python tools/male_anus.py <BodyTalk4-Nude.nif> [<.osd>]     # in place, on a copy
"""
import math
import pathlib
import sys

import anal_canal as ac

CENTRE = (0.0, -2.38, -56.16)
AXIS = (0.0, 0.40, 0.917)                 # the pucker's inward axis, measured (its x is 0 by symmetry)
TILT = math.radians(12.0)
UP = (0.0, -math.sin(TILT), math.cos(TILT))   # -y is the back, as for the women's canal
OPEN_R = 0.6


def _offsets():
    a = ac._unit(AXIS)
    inner = ac._mul(a, 1.5)
    out = [ac._mul(a, 0.75), inner]
    for s in (2.0, 4.0, 6.0, 7.2):
        out.append(ac._add(inner, ac._mul(UP, s)))
    return tuple(out)


def spec(mucosa_uv):
    return ac.Spec('BaseMaleBody:0', CENTRE, AXIS, _offsets(), radius=1.0, floor=None, cup_r=2.0, open_r=OPEN_R,
                   mucosa_uv=mucosa_uv, pelvis='Pelvis_Rear_skin')


def floor_uv(nif_path, half=0.002):
    """a tiny UV square at the pucker floor's texels: the canal shows the pucker's own skin until a mucosa patch exists"""
    import nif
    n = nif.Nif(nif_path)
    s = n.shape('BaseMaleBody:0')
    pos = s.positions()
    near = [i for i, p in enumerate(pos) if math.dist(p, CENTRE) < 0.35]
    u = sum(s.uv(i)[0] for i in near) / len(near)
    v = sum(s.uv(i)[1] for i in near) / len(near)
    return (u - half, v - half, u + half, v + half)


PELVIS = 'Pelvis_skin'
STRETCH = ('AnatAnus_F_Stretch', 'AnatAnus_B_Stretch', 'AnatAnus_L_Stretch', 'AnatAnus_R_Stretch')
REACH = {'F': 0.7, 'B': 1.0, 'L': 1.0, 'R': 1.0}   # the women's ring layout (physics_design.REST): F small and close
SHARE = 0.6                        # the most a vertex gives our bones (the women's fit peaked about here, A-14)
RIM_FADE = 1.0                     # the share fades over this much beyond the ring, across the pucker ...
CANAL_FADE = 1.5                   # ... and over this much depth into the canal


def _m4(r9, t, s):
    m = [[r9[3 * i + j] * s for j in range(3)] + [t[i]] for i in range(3)]
    return m + [[0.0, 0.0, 0.0, 1.0]]


def _apply(m, p):
    return tuple(sum(m[i][j] * p[j] for j in range(3)) + m[i][3] for i in range(3))


def _rotate(m, d):
    v = tuple(sum(m[i][j] * d[j] for j in range(3)) for i in range(3))
    return ac._unit(v)


def ring(nif_path):
    """(the opening's centre, its inward axis, its front direction) in shape space, from the unopened pucker"""
    drop, loop, centre, path = ac.plan(nif_path, spec((0, 0, 0, 0)))
    axis = ac._unit(AXIS)
    up = (0.0, 1.0, 0.0)                                   # +y: the front (the scrotum's side)
    front = ac._unit(ac._sub(up, ac._mul(axis, ac._dot(up, axis))))
    return centre, axis, front, path


def bone_points(centre, axis, front):
    left = (-1.0, 0.0, 0.0)                                # the women's AnatAnus_L sits at -x
    return {'F': ac._add(centre, ac._mul(front, REACH['F'])), 'B': ac._add(centre, ac._mul(front, -REACH['B'])),
            'L': ac._add(centre, ac._mul(left, REACH['L'])), 'R': ac._add(centre, ac._mul(left, -REACH['R']))}


def rig(nif_path, centre, axis, front, first_new):
    """Add the four anus stretch bones to the body's skin (nif.with_bones) and weigh the pucker and the canal's first
    rings to them: up to SHARE, shared between the two bones nearest the vertex's angle around the axis, fading over
    RIM_FADE beyond the ring and CANAL_FADE into the canal. Returns {bone: its offset in Pelvis_skin's frame}."""
    import nif
    n = nif.Nif(nif_path)
    s = n.shape('BaseMaleBody:0')
    bones, xf = n.skin(s)
    if PELVIS not in bones:
        raise ValueError(f'the body\'s skin has no {PELVIS}')
    k = bones.index(PELVIS)
    pr, pt, ps = xf[k]
    S = _m4(pr, pt, ps)                                    # shape -> Pelvis_skin's frame
    node = next(v for v in n.nodes.values() if v['name'] == PELVIS)
    pts = bone_points(centre, axis, front)
    local = {f'AnatAnus_{key}': _apply(S, p) for key, p in pts.items()}
    defs = []
    for key in 'FBLR':
        L = local[f'AnatAnus_{key}']
        nr, nt = node['r'], node['t']
        ns = node.get('s', 1.0)
        world_t = tuple(nt[i] + sum(nr[3 * i + j] * ns * L[j] for j in range(3)) for i in range(3))
        defs.append(dict(name=f'AnatAnus_{key}_Stretch', node_rot=nr, node_t=world_t, sphere=(0.0, 0.0, 0.0, 1.0),
                         skin_rot=pr, skin_t=tuple(pt[i] - L[i] for i in range(3)), scale=ps))
    have = [b for b in STRETCH if b in bones]
    if have:
        raise ValueError(f'the body already has {have}: rig runs once, on the opened body')
    raw = n.with_bones(s, defs)
    pathlib.Path(nif_path).write_bytes(raw)
    n = nif.Nif(nif_path)
    s = n.shape('BaseMaleBody:0')
    bones, _ = n.skin(s)
    slot = {b: i for i, b in enumerate(bones)}
    import math as _m
    import struct
    side = ac._unit(ac._cross(axis, front))                # completes (front, side) in the ring's plane
    angles = {'F': 0.0, 'B': _m.pi, 'R': _m.atan2(ac._dot((1.0, 0.0, 0.0), side), ac._dot((1.0, 0.0, 0.0), front)),
              'L': _m.atan2(ac._dot((-1.0, 0.0, 0.0), side), ac._dot((-1.0, 0.0, 0.0), front))}
    order = sorted('FBLR', key=lambda b: angles[b])
    b = bytearray(n.b)
    pos = s.positions()
    touched = 0
    for i, q in enumerate(pos):
        rel = ac._sub(q, centre)
        d = ac._dot(rel, axis)
        radial = ac._sub(rel, ac._mul(axis, d))
        r = _m.sqrt(ac._dot(radial, radial))
        ring_r = 0.53
        if i < first_new:                                  # BodyTalk's own skin: the pucker around the opening
            f = max(0.0, min(1.0, 1.0 - (r - ring_r) / RIM_FADE)) if -0.8 < d <= 0.3 else 0.0
        else:                                              # the canal's own vertices (an axis-only test reached the
            f = max(0.0, min(1.0, 1.0 - (d - 0.3) / CANAL_FADE))   # penis tip and the balls: same depth, far off it)
        f *= SHARE
        if f <= 0.005 or r < 1e-4:
            continue
        a = _m.atan2(ac._dot(radial, side), ac._dot(radial, front))
        # the two bones around this angle, shared linearly
        seq = order + [order[0]]
        share = {}
        for x, y in zip(seq, seq[1:]):
            a0, a1 = angles[x], angles[y] if y != order[0] else angles[y] + 2 * _m.pi
            aa = a if a >= a0 else a + 2 * _m.pi
            if a0 <= aa <= a1:
                t = (aa - a0) / ((a1 - a0) or 1.0)
                share = {x: 1 - t, y: t}
                break
        own = {bones[sl]: w for sl, w in s.skin_weights(i) if w > 0}
        tot = sum(own.values()) or 1.0
        mixed = {bn: w / tot * (1 - f) for bn, w in own.items()}
        for key, sh in share.items():
            nm = f'AnatAnus_{key}_Stretch'
            mixed[nm] = mixed.get(nm, 0.0) + f * sh
        top = sorted(mixed.items(), key=lambda t: -t[1])[:4]
        tt = sum(w for _, w in top) or 1.0
        top = [(slot[bn], w / tt) for bn, w in top] + [(0, 0.0)] * (4 - len(top))
        at = s.data_at + i * s.stride + s.skin_at
        struct.pack_into('<4e', b, at, *(w for _, w in top))
        struct.pack_into('<4B', b, at + 8, *(sl for sl, _ in top))
        touched += 1
    pathlib.Path(nif_path).write_bytes(bytes(b))
    return local, touched


def engine_keys(nif_path, centre, axis, path, local):
    """[BonesMale] and the men's [Aim] keys: the same bones and opening as the women's, in Pelvis_skin's frame"""
    import nif
    n = nif.Nif(nif_path)
    s = n.shape('BaseMaleBody:0')
    bones, xf = n.skin(s)
    pr, pt, ps = xf[bones.index(PELVIS)]
    S = _m4(pr, pt, ps)

    def fmt(v, d=5):
        return ','.join(f'{x:.{d}f}' for x in v)
    rows = [f'AnatAnus_{k}=Pelvis_skin,{fmt(local[f"AnatAnus_{k}"], 6)}' for k in 'FBLR']
    aim = {'anusM': fmt(_apply(S, centre)), 'anusInM': fmt(_rotate(S, axis)),
           'anusPathM': ';'.join(fmt(_apply(S, p), 3) for p in path)}
    return rows, aim


def build(nif_path, osd_path=None):
    """open the pucker, stitch the canal, add and weigh our anus bones; returns (report, [BonesMale] rows, [Aim] keys)"""
    import osd as osd_module
    centre, axis, front, path = ring(nif_path)
    import nif
    first_new = nif.Nif(nif_path).shape('BaseMaleBody:0').count
    line = ac.build(nif_path, osd_path, osd_module if osd_path else None, spec=spec(floor_uv(nif_path)))
    local, touched = rig(nif_path, centre, axis, front, first_new)
    rows, aim = engine_keys(nif_path, centre, axis, path, local)
    return f'{line}; our 4 anus bones added, {touched} vertices weighted to them', rows, aim


# ---- the Builder's men's stage: the player's own BodyTalk 4, opened, as a slider set of ours
BT_OSP = 'Tools/BodySlide/SliderSets/BodyTalk4.osp'
BT_FOLDER = 'Tools/BodySlide/ShapeData/BodyTalk4'
FOLDER = 'AnatomyMale'
VARIANTS = {'BodyTalk4': ('Nude', 'Anatomy Male Body'), 'BodyTalk4-Uncut': ('Uncut', 'Anatomy Male Body Uncut')}
OUTPUTS = [f'Tools/BodySlide/SliderSets/{FOLDER}.osp', f'Tools/BodySlide/SliderGroups/{FOLDER}.xml'] + \
          [f'Tools/BodySlide/ShapeData/{FOLDER}/{FOLDER}-{v}.{x}' for v, _ in VARIANTS.values() for x in ('nif', 'osd')]
# in BodyTalk's own group, so the player's BodyTalk presets show for it, and BodySlide's group filter finds it
GROUPS = ('<?xml version="1.0" encoding="UTF-8"?>\n<SliderGroups>\n    <Group name="BodyTalk - Bodies">\n' +
          ''.join(f'        <Member name="{ours}"/>\n' for _, ours in VARIANTS.values()) + '    </Group>\n'
          '    <Group name="Anatomy">\n' + ''.join(f'        <Member name="{ours}"/>\n' for _, ours in VARIANTS.values()) +
          '    </Group>\n</SliderGroups>\n')


def slider_sets(osp_text):
    """BodyTalk4.osp's Nude and Uncut sets, renamed and pointed at our opened copies: same sliders, same output
    (MaleBody), so building ours replaces BodyTalk's build exactly as building BodyTalk's replaces ours"""
    import re
    blocks = []
    for m in re.finditer(r'<SliderSet name="([^"]+)">.*?</SliderSet>', osp_text, re.S):
        name = m.group(1)
        if name not in VARIANTS:
            continue
        v, ours = VARIANTS[name]
        b = m.group(0).replace(f'<SliderSet name="{name}">', f'<SliderSet name="{ours}">', 1)
        b = re.sub(r'<DataFolder>[^<]*</DataFolder>', f'<DataFolder>{FOLDER}</DataFolder>', b, count=1)
        b = re.sub(r'<SourceFile>[^<]*</SourceFile>', f'<SourceFile>{FOLDER}-{v}.nif</SourceFile>', b, count=1)
        b = b.replace('DataFolder="BodyTalk4"', f'DataFolder="{FOLDER}"')
        refs = re.findall(r'>([^<>\\]+)\.osd\\', b)
        b = b.replace(f'>BodyTalk4-{v}.osd\\', f'>{FOLDER}-{v}.osd\\')
        if any(r != f'BodyTalk4-{v}' for r in refs):
            raise ValueError(f'{name}: slider data from {sorted(set(refs))}, not only BodyTalk4-{v}.osd')
        if 'BodyTalk4' in b.replace('BodyTalk4-', ''):
            raise ValueError(f'{name}: a BodyTalk4 path left in our set')
        blocks.append(b)
    if len(blocks) != len(VARIANTS):
        raise ValueError(f'BodyTalk4.osp has {len(blocks)} of the sets {sorted(VARIANTS)}')
    return '<?xml version="1.0" encoding="UTF-8"?>\n<SliderSetInfo version="1">\n    ' + '\n    '.join(blocks) + \
        '\n</SliderSetInfo>\n'


def stage(game, work):
    """Open the player's BodyTalk 4 (Nude and Uncut) into work/: {published path: produced file}, or None when BodyTalk 4
    is not installed. Says when the opening is not where the shipped engine keys put it (another BodyTalk version)."""
    import physics_design as pd
    sources = [BT_OSP] + [f'{BT_FOLDER}/BodyTalk4-{v}.{x}' for v, _ in VARIANTS.values() for x in ('nif', 'osd')]
    if any(game.find(rel) is None for rel in sources):
        return None
    for rel in sources:
        print(f'   input {game.describe(rel)}')
    produced = {}
    shape_dir = pathlib.Path(work) / 'ShapeData' / FOLDER
    shape_dir.mkdir(parents=True, exist_ok=True)
    for v, ours in VARIANTS.values():
        nif_path, osd_path = shape_dir / f'{FOLDER}-{v}.nif', shape_dir / f'{FOLDER}-{v}.osd'
        nif_path.write_bytes(game.read(f'{BT_FOLDER}/BodyTalk4-{v}.nif'))
        osd_path.write_bytes(game.read(f'{BT_FOLDER}/BodyTalk4-{v}.osd'))
        report, rows, aim = build(nif_path, osd_path)
        print(f'   {ours}: {report}')
        got = {r.split('=')[0]: [float(x) for x in r.split('=')[1].split(',')[1:]] for r in rows}
        off = max(abs(a - b) for k, p in pd.MEN_ANUS_BONES.items() for a, b in zip(got[k], p))
        if off > 0.01:
            print(f'   WARNING: {ours}\'s opening is {off:.3f} from where the engine aims (physics_design.MEN_ANUS_*, '
                  'measured on BodyTalk 4 3.8): the penis may miss it')
        for path in (nif_path, osd_path):
            produced[f'Tools/BodySlide/ShapeData/{FOLDER}/{path.name}'] = path
    osp = pathlib.Path(work) / f'{FOLDER}.osp'
    osp.write_text(slider_sets(game.read(BT_OSP).decode('utf-8-sig')), encoding='utf-8')
    produced[f'Tools/BodySlide/SliderSets/{FOLDER}.osp'] = osp
    groups = pathlib.Path(work) / f'{FOLDER}-groups.xml'
    groups.write_text(GROUPS, encoding='utf-8')
    produced[f'Tools/BodySlide/SliderGroups/{FOLDER}.xml'] = groups
    assert set(produced) == set(OUTPUTS)
    return produced


if __name__ == '__main__':
    report, rows, aim = build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(report)
    print('[BonesMale]')
    print('\n'.join(rows))
    print('[Aim] men:')
    print('\n'.join(f'{k}={v}' for k, v in aim.items()))
