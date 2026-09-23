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
from physics_design import AFFECTED, COLLIDERS, PARENT, PROPS, STRETCH  # noqa: E402


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
    missing = [b for b, _ in ATTACH if b not in women] + [n for n in AFFECTED if n not in women] +               [n for n in COLLIDERS if n not in men]
    print(f'ocbp.ini: every source line kept ({len(dead)} name a bone no skeleton has: {sorted(set(dead)) or "none"}); '
          f'{len(ATTACH)} anatomy bones attached in {len(SECTIONS)} new sections')
    print(f'OCBPCollisionConfig.txt: +{len(AFFECTED)} affected, +{len(COLLIDERS)} colliders '
          f'({sum(len(s) for s in AFFECTED.values()) + sum(len(s) for s in COLLIDERS.values())} spheres)')
    print(f'anatomy bones missing from the skeleton that carries them: {missing or "none"}')
    if missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
