"""The physics configs for the anatomy body, built from the owner's DEPLOYED ones (decision A-7).

Inputs (read only): the staging copies of ocbp.ini (MadKita's Actual Jiggle) and
OCBPCollisionConfig.txt (from Jiggle Physics); the plugin is OCBPC 0.3. Nothing they tune is
changed or dropped; the output (build/config/, never committed: it carries their work, A-2) only
ADDS our bones:

  ocbp.ini
    - [Attach]: our genital bones (physics_design.REST, A-14), each with a spring section of its own
      (values and reasons at SPRING). Every line MadKita ships stays as it is. (Before A-14 this
      commented out 18 lines whose 3BBB bones ZeX's skeleton lacks; but women load a 3BBB-style
      skeleton that HAS them, so that took their breast, butt and thigh physics away.)
  OCBPCollisionConfig.txt
    - Affected: the inner and outer lips and the four anus bones. Colliders: the penis bones from
      Penis_01 out, plus the hands, fingers and forearms already listed. Every actor's colliders
      count, whatever femaleOnly says (scan.cpp:204-218: an actor that is not tracked is still
      entered), and an actor's own colliders act on its own affected bones.
    - Each of our bones is its sphere's centre (offsets 0; physics_design.py says why).
    - Penis_00 is left out: a female's own Penis_00 would sit near her vulva if her skeleton had
      one (the women's skeleton has none; ZeX's, which men load, does). Penis_01-05 are colliders
      for OTHER actors too: in a female/female scene a partner's could push. No key filters
      colliders by sex.

    python tools/physics_config.py
"""
import pathlib
import re

import physics_design as pd
import zex_bones as zb

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS = zb.ab.DEFAULT_DATA / 'F4SE/Plugins'
OUT = ROOT / 'build/config'

ATTACH = [('AnatVulva', 'Vulva'),
          ('AnatLipOuter_L', 'LabiaOuter'), ('AnatLipOuter_R', 'LabiaOuter'),
          ('AnatLip_L', 'Labia'), ('AnatLip_R', 'Labia'),
          ('AnatAnus_F', 'Anus'), ('AnatAnus_B', 'Anus'), ('AnatAnus_L', 'Anus'), ('AnatAnus_R', 'Anus')]

# Tuned with tools/ocbpc_sim.py, a port of OCBPC's own update (decision A-9). What the source says,
# and what follows from it:
#  - a collision push is divided by linear before it is applied and multiplied back after, so a LOW
#    linear quiets walking without weakening a push; but maxoffset caps the internal offset, so the
#    push a bone can reach is maxoffset * linear: maxoffset = 3 / linear keeps 3 units of room.
#    Measured (walk 1.5u @ 2 Hz, run 3u @ 3 Hz): linear 0.9 moved the bones 0.95 / 2.25 units, which
#    heavy weights would turn into flapping; linear 0.2 at stiffness 150 moves them ~0.1 / ~0.35.
#  - stiffness2 multiplies the SQUARED offset; with the large internal offsets a low linear implies,
#    it would dominate the spring, so it is 0 here.
SPRING = dict(stiffness=150.0, stiffness2=0.0, damping=6.0, timetick=4.0, timeStep=0.020,
              gravityBias=0.0, gravityCorrection=0.0, cogOffsetX=0.0, cogOffsetY=0.0, cogOffsetZ=0.0,
              rotationalX=0.0, rotationalY=0.0, rotationalZ=0.0, rotateLinearX=0.0, rotateLinearY=0.0,
              rotateLinearZ=0.0, rotateRotationX=0.0, rotateRotationY=0.0, rotateRotationZ=0.0, absRotX=0)
# maxoffset 12.5 x linear 0.2 = 2.5 real units per axis: above the ~1.9 a shaft needs (fit_check), below
# the 3 that pinned bones reached in the owner's look (A-11).
QUIET = dict(linearX=0.2, linearY=0.2, linearZ=0.2, maxoffsetX=12.5, maxoffsetY=12.5, maxoffsetZ=12.5)
# The outer lips wobble (A-13): softer, freer, capped lower. Measured (tools/ocbpc_sim.py): bone 0.57 at
# a walk, 0.42 per thrust, the 1.2 cap when running; x the 0.45 layer = 0.26 / 0.19 / 0.54 at the crest.
SOFT = dict(SPRING, stiffness=60.0, damping=3.0, linearX=0.5, linearY=0.5, linearZ=0.5,
            maxoffsetX=2.4, maxoffsetY=2.4, maxoffsetZ=2.4)
# The openings get a higher cap (fisting, the owner's poll 2026-09-23): a fist pushes the inner lips
# and the anus bones 2.8-2.85 (tools/ocbpc_sim.py), which the 2.5 cap clipped; 20 x 0.2 = 4.0 per
# axis. A penis pushes 2.2 and is unaffected (simulated: every penis path identical).
WIDE = dict(QUIET, maxoffsetX=20.0, maxoffsetY=20.0, maxoffsetZ=20.0)
SECTIONS = {
    'LabiaOuter': SOFT,
    'Labia': dict(SPRING, **WIDE),
    'Vulva': dict(SPRING, **QUIET),
    'Anus': dict(SPRING, **WIDE),
}
# The spheres (her bones and the partner's penis bones) are the physical design the weights are
# fitted to, so they live in ONE place, physics_design.py, with the reasons.
from physics_design import (AFFECTED, AIM, AIM_CHAIN, COLLIDERS, CREATURE_COLLIDERS, FACE, MOUTH,  # noqa: E402
                            MOUTH_CHAINS, PARENT, PROPS, SHAPE, STRETCH)


def sections(text):
    """[(header or None, [lines])] in file order."""
    out, cur = [], (None, [])
    for line in text.splitlines():
        m = re.match(r'^\s*\[([^\]]+)\]', line)
        if m:
            out.append(cur)
            cur = (m.group(1), [line])
        else:
            cur[1].append(line)
    out.append(cur)
    return out


def ocbp(text, skeletons):
    """MadKita's ini with our bones attached. Nothing of theirs is changed; the lines naming a bone
    that no skeleton in the game has are only counted (OCBPC skips a bone it cannot find)."""
    parts = sections(text)
    dead = []
    new = []
    for name, lines in parts:
        if name in ('Attach', 'Attach.A'):
            for line in lines:
                m = re.match(r'^\s*([A-Za-z0-9_]+)\s*=', line)
                if m and not line.lstrip().startswith(';') and not any(m.group(1) in sk for sk in skeletons):
                    dead.append(m.group(1))
            if name == 'Attach':
                lines = lines + ["; --- anatomy (fo4-anatomy A-7, A-14): our own genital bones, in the women's skeleton"] + \
                                [f'{b}={s}' for b, s in ATTACH]
        new.append((name, lines))
    body = []
    for name, lines in new:
        body += lines
    for sec, vals in SECTIONS.items():
        body += ['', f'[{sec}]'] + [f'{k}={v}' for k, v in vals.items()]
    # the fo4-ocbpc fork's props (A-17); OCBPC 0.3 itself ignores an unknown section
    body += ['', '; fo4-anatomy A-17: what an animation hangs on a hand collides along its length (fo4-ocbpc fork)',
             '[Props]'] + [f'{k}={v}' for k, v in PROPS.items()]
    # the fork's mouth (A-20): a penis chain crossing her lips opens her jaw over the animation's
    body += ['', '; fo4-anatomy A-20: the mouth opens to what is in it (fo4-ocbpc fork)',
             '[Mouth]'] + [f'{k}={v}' for k, v in MOUTH.items()]
    body += ['', '; fo4-anatomy A-27: Rapport\'s faces are written after the merge (fo4-ocbpc fork)',
             '[Face]'] + [f'{k}={v}' for k, v in FACE.items()]
    header = ['; Generated by fo4-anatomy tools/physics_config.py from the deployed ocbp.ini: every line of it kept,',
              f'; {len(ATTACH)} anatomy bones appended in {len(SECTIONS)} sections.']
    return '\n'.join(header + body) + '\n', dead


def stretch_keys(pelvis_world):
    """The fork's stretch-group keys per section (A-17). The opening's axis goes in the frame the fork
    measures pushes in: the bones' parent's (Pelvis_skin), so local = R^T x skin-space axis."""
    r = zb.transpose(pelvis_world[0])
    out = {}
    for sec, s in STRETCH.items():
        ax = zb.apply(r, list(s['axis']))
        out[sec] = dict(stretchGroup=float(s['group']), stretchKnee=s['knee'], stretchGain=s['gain'],
                        stretchMax=s['max'], stretchAxisX=round(ax[0], 5), stretchAxisY=round(ax[1], 5),
                        stretchAxisZ=round(ax[2], 5))
    return out


def collisions(text):
    parts = sections(text)
    out = []
    for name, lines in parts:
        if name == 'AffectedNodes':
            lines = _append_list(lines, AFFECTED)
        elif name == 'ColliderNodes':
            lines = _append_list(lines, COLLIDERS)
        out += lines
    out += ['', '#' * 78, '# Anatomy spheres (fo4-anatomy A-7, A-9): offsets in the actor frame, x only -- see physics_config.py',
            '#' * 78]
    for node, spheres in list(AFFECTED.items()) + list(COLLIDERS.items()):
        out += ['', f'[{node}]'] + [','.join(f'{v:g}' for v in s) for s in spheres]
    return '\n'.join(out) + '\n'


def _append_list(lines, names):
    """Node names go right after the last listed name, before the section's trailing blank lines."""
    last = max((i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith('#')
                and not l.strip().startswith('[')), default=0)
    return lines[:last + 1] + list(names) + lines[last + 1:]


# Once Anatomy-dev is deployed, Data's copies ARE our output, and building from them again would
# append our sections a second time. So the inputs are the owning mods' staging copies, by name,
# and an input that already carries our marker is refused.
MODS = pathlib.Path(r'D:\Vortex\fallout4\mods')
SOURCES = {'ocbp.ini': "MadKita's Actual Jiggle-90677-1-1-1737600200",
           'OCBPCollisionConfig.txt': 'Jiggle Physics-82699-1-1715599262'}
MARKER = 'fo4-anatomy'


def source(name):
    p = MODS / SOURCES[name] / 'F4SE/Plugins' / name
    if not p.exists():
        raise SystemExit(f'{p} is gone: the owner changed physics mods; point SOURCES at the new one')
    text = p.read_text(encoding='utf-8', errors='replace')
    if MARKER in text:
        raise SystemExit(f'{p} already carries our additions: refusing to stack them twice')
    return text


ANATOMY = OUT / 'Anatomy'       # -> Data/F4SE/Plugins/Anatomy/: the zero-touch release files (A-21)


def bone_table(pelvis_world):
    """[Bones] for the fork's run-time injection (A-21): each of our nodes, its parent and its local
    offset, identity rotation. Under Pelvis_skin the offset is where the body was bound to put the bone
    (REST, skin space) in the frame of the body's own bind Pelvis_skin, so it holds for any skeleton
    whose Pelvis_skin matches the body's (every CBBE body assumes that). A stretch child sits on its bone."""
    pr, pt, ps = pelvis_world
    rows = []
    for name, skin in pd.REST.items():
        w = [skin[i] - pd.SKIN_OFFSET[i] for i in range(3)]
        local = [v / ps for v in zb.apply(zb.transpose(pr), [w[i] - pt[i] for i in range(3)])]
        rows.append((name, PARENT, local))
    for bone, child in pd.STRETCH_BONES.items():
        rows.append((child, bone, [0.0, 0.0, 0.0]))
    return rows


def throat(head_world, mouth_local, offsets=pd.THROAT, frame_world=None):
    """Throat offsets in a skeleton's bone frame (HEAD's, or frame_world's: Neck's for THROAT_NECK): the
    mouth [Mouth] places in HEAD's frame, plus each offset (world axes), back into the frame (bone_table's
    formula)."""
    hr, ht, hs = head_world
    mouth = [ht[i] + v * hs for i, v in enumerate(zb.apply(hr, list(mouth_local)))]
    fr, ft, fs = frame_world or head_world
    out = []
    for off in offsets:
        w = [mouth[i] + off[i] - ft[i] for i in range(3)]
        out.append([v / fs for v in zb.apply(zb.transpose(fr), w)])
    return out


def aim_keys(pelvis_world, head_f=None, head_m=None, neck_f=None, neck_m=None):
    """[Aim] (A-28) as the fork reads it: each opening's centre a point in Pelvis_skin's frame (bone_table's
    formula), its axis into her a direction in that frame (stretch_keys's: R^T x the skin-space axis)."""
    pr, pt, ps = pelvis_world

    def point(skin):
        w = [skin[i] - pd.SKIN_OFFSET[i] - pt[i] for i in range(3)]
        return [v / ps for v in zb.apply(zb.transpose(pr), w)]

    def axis(a):
        return zb.apply(zb.transpose(pr), list(a))

    def fmt(v, digits=5):
        return ','.join(f'{x:.{digits}f}' for x in v)

    def path(points, local=point):
        return ';'.join(fmt(local(q), 3) for q in points)

    keys = dict(AIM, chain='|'.join(AIM_CHAIN), vagina=fmt(point(pd.VAGINA_CENTRE)), vaginaIn=fmt(axis(pd.VAGINA_AXIS)),
                vaginaPath=path(pd.VAGINA_PATH), anus=fmt(point(pd.ANUS_CENTRE)), anusIn=fmt(axis(pd.ANUS_AXIS)),
                anusPath=path(pd.ANUS_PATH))
    for sex, head, neck, key in (('female', head_f, neck_f, 'F'), ('male', head_m, neck_m, 'M')):
        if head is not None:
            mouth = (MOUTH[f'{sex}X'], MOUTH[f'{sex}Y'], MOUTH[f'{sex}Z'])
            keys[f'throat{key}'] = ';'.join(fmt(q, 3) for q in throat(head, mouth))
            if neck is not None:
                keys[f'throatNeck{key}'] = ';'.join(fmt(q, 3) for q in throat(head, mouth, pd.THROAT_NECK, neck))
    return keys


def lip_keys():
    """[Mouth] lip table (A-32, tools/lips.py): how each mouth morph moves the lips' inner edges across the
    mouth, per sex, measured on the heads the game loads. lipXs = where; lip<F|M><id> = upper edge's
    moves;lower edge's moves at those x, in the head's own units."""
    import gamedata
    import lips
    game = gamedata.Game(lips.DATA)
    out = ['; the lips around what is in her mouth (A-32): each morph\'s move of the upper;lower lip edge at lipXs;'
           ' and of the rim\'s left,right end (lipRim: the ends at rest)',
           'lipXs=' + ','.join(f'{x:g}' for x in lips.XS)]
    for sex, head in (('F', 'BaseFemaleHead'), ('M', 'BaseMaleHead')):
        table, gap, _, _, _ = lips.measure(game.read(f'Meshes/Actors/Character/CharacterAssets/{head}.tri'))
        if gap > 0.1:
            raise SystemExit(f'{head}: the lips do not meet at rest ({gap:.3f}): not the head lips.py measured')
        rest = lips.measure(game.read(f'Meshes/Actors/Character/CharacterAssets/{head}.tri'))[4]
        if not rest[0] < 0 < rest[1]:
            raise SystemExit(f'{head}: the rim does not straddle the middle ({rest})')
        out.append(f'lipRim{sex}={rest[0]:.3f},{rest[1]:.3f}')
        for mid, _ in lips.MORPHS:
            u, lo, (dl, dr) = table[mid]
            out.append(f'lip{sex}{mid}=' + ','.join(f'{v:.3f}' for v in u) + ';' + ','.join(f'{v:.3f}' for v in lo)
                       + f';{dl:.3f},{dr:.3f}')
    return out


def anatomy_ini(pelvis_world, head_f=None, head_m=None, neck_f=None, neck_m=None):
    """Our own ocbp.ini, read by the fork AFTER the player's (A-21): only our lines, nothing of theirs."""
    lines = ['; fo4-anatomy: read by the fo4-ocbpc fork after Data/F4SE/Plugins/ocbp.ini (decision A-21).',
             '; Generated by tools/physics_config.py - edit physics_design.py / physics_config.py, not this.',
             '', '[Attach]'] + [f'{b}={s}' for b, s in ATTACH]
    for sec, vals in SECTIONS.items():
        lines += ['', f'[{sec}]'] + [f'{k}={v}' for k, v in vals.items()]
    lines += ['', '[Props]'] + [f'{k}={v}' for k, v in PROPS.items()]
    lines += ['', '[Mouth]'] + [f'{k}={v}' for k, v in MOUTH.items()] + lip_keys()
    lines += ['', '[Face]'] + [f'{k}={v}' for k, v in FACE.items()]
    lines += ['', '; the penis finds its opening (A-28): openings in Pelvis_skin\'s frame, angles in degrees',
              '[Aim]'] + [f'{k}={v}' for k, v in aim_keys(pelvis_world, head_f, head_m, neck_f, neck_m).items()]
    lines += ['', '; every man\'s penis: the shaft this thin, the head this big (one size per man) (A-31)',
              '[Shape]'] + [f'{k}={v}' for k, v in SHAPE.items()]
    lines += ['', '; our nodes, created at run time under the skeleton the actor loaded: name=parent,x,y,z',
              '[Bones]'] + [f'{n}={p},{l[0]:.6f},{l[1]:.6f},{l[2]:.6f}' for n, p, l in bone_table(pelvis_world)]
    return '\n'.join(lines) + '\n'


def anatomy_collisions():
    """Our own OCBPCollisionConfig.txt, appended by the fork to the player's: a node they already list
    keeps its spheres and gains ours."""
    lines = ['# fo4-anatomy: appended by the fo4-ocbpc fork to Data/F4SE/Plugins/OCBPCollisionConfig.txt (A-21)',
             '', '[AffectedNodes]'] + list(AFFECTED) + ['', '[ColliderNodes]'] + list(COLLIDERS)
    for node, spheres in list(AFFECTED.items()) + list(COLLIDERS.items()):
        lines += ['', f'[{node}]'] + [','.join(f'{v:g}' for v in s) for s in spheres]
    return '\n'.join(lines) + '\n'


def main():
    import skeleton
    if not skeleton.OUT.exists():
        raise SystemExit(f'{skeleton.OUT} is missing: run tools/skeleton.py first')
    women_world = zb.skeleton_world(skeleton.OUT)          # ours: the women's, with our bones
    women = set(women_world)
    men = set(zb.skeleton_world(zb.SKELETON))               # ZeX's: the partner's penis bones
    for sec, keys in stretch_keys(women_world[PARENT]).items():
        SECTIONS[sec] = dict(SECTIONS[sec], **keys)
    OUT.mkdir(parents=True, exist_ok=True)
    ini, dead = ocbp(source('ocbp.ini'), (women, men))
    (OUT / 'ocbp.ini').write_text(ini, encoding='utf-8')
    (OUT / 'OCBPCollisionConfig.txt').write_text(collisions(source('OCBPCollisionConfig.txt')), encoding='utf-8')
    creatures = {}
    for race in set(CREATURE_COLLIDERS.values()):
        creatures[race] = set(zb.skeleton_world(zb.ab.DEFAULT_DATA / f'Meshes/Actors/{race}/CharacterAssets/skeleton.nif'))
    missing = [b for b, _ in ATTACH if b not in women] + [n for n in AFFECTED if n not in women] + \
              [n for n in COLLIDERS if n not in (creatures[CREATURE_COLLIDERS[n]] if n in CREATURE_COLLIDERS else men)] + \
              [n for chain in MOUTH_CHAINS for n in chain if n not in COLLIDERS]   # a mouth chain is only colliders
    print(f'ocbp.ini: every source line kept ({len(dead)} name a bone no skeleton has: {sorted(set(dead)) or "none"}); '
          f'{len(ATTACH)} anatomy bones attached in {len(SECTIONS)} new sections')
    print(f'OCBPCollisionConfig.txt: +{len(AFFECTED)} affected, +{len(COLLIDERS)} colliders '
          f'({sum(len(s) for s in AFFECTED.values()) + sum(len(s) for s in COLLIDERS.values())} spheres)')
    print(f'anatomy bones missing from the skeleton that carries them: {missing or "none"}')
    if missing:
        raise SystemExit(1)

    # the zero-touch files (A-21): ours alone, merged by the fork at run time
    bind = zb.skeleton_world(zb.SKELETON)                  # the skeleton the body is bound to
    ANATOMY.mkdir(parents=True, exist_ok=True)
    # the throat in each skeleton's own HEAD and Neck frames: the women's (ours) and the men's (ZeX's)
    ours = {'ocbp.ini': anatomy_ini(bind[PARENT], women_world['HEAD'], bind['HEAD'], women_world['Neck'], bind['Neck']),
            'OCBPCollisionConfig.txt': anatomy_collisions()}
    # the fork's INIReader (inih) reads at most INI_MAX_LINE = 200 bytes a line, newline included, and
    # silently cuts the rest: a long [Mouth] face= list would lose its last term without a word
    for name, text in ours.items():
        long_lines = [(n + 1, len(line)) for n, line in enumerate(text.splitlines()) if len(line) + 2 > 200]
        if long_lines:
            raise SystemExit(f'{name}: line(s) too long for the fork\'s INI reader (200 with the newline): '
                             f'{long_lines}')
        (ANATOMY / name).write_text(text, encoding='utf-8')
    # the run-time bones must land exactly where the patched skeleton put them
    import nif
    built = nif.Nif(skeleton.OUT)
    by_name = {n['name']: n for n in built.nodes.values()}
    worst = 0.0
    for name, parent, local in bone_table(bind[PARENT]):
        node = by_name.get(name)
        if node is None:
            raise SystemExit(f'{name} is not in {skeleton.OUT}')
        worst = max(worst, max(abs(a - b) for a, b in zip(node['t'], local)))
    print(f'Anatomy/ocbp.ini: {len(ATTACH)} bones attached, [Props], [Mouth], [Face], [Bones] ({len(bone_table(bind[PARENT]))} nodes, '
          f'largest difference from the patched skeleton {worst:.1e}); Anatomy/OCBPCollisionConfig.txt: '
          f'{len(AFFECTED)} affected, {len(COLLIDERS)} colliders')
    if worst > 1e-4:
        raise SystemExit('the run-time bone table does not match the patched skeleton')


if __name__ == '__main__':
    main()
