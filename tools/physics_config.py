"""The physics configs for the anatomy body, built from the owner's DEPLOYED ones (decision A-7).

Inputs (read only): the staging copies of ocbp.ini (MadKita's Actual Jiggle) and
OCBPCollisionConfig.txt (from Jiggle Physics); the plugin is OCBPC 0.3. Nothing they tune is
dropped; the output (build/config/, never committed: it carries their work, A-2) differs by:

  ocbp.ini
    - [Attach]/[Attach.A] lines naming a bone the ZeX skeleton does not have are commented out,
      with the reason. Measured: 12 of 17 (3BBB bone names); they could never move anything.
    - Our bones: the vagina _CBP_ twins (A-6: animations keep the animated bones) and the anus
      bones (ZeX has no anus twins; OCBPC SETS a simulated bone's transform, so animations no
      longer move them), each with a spring section of its own (values and reasons at SPRING).
  OCBPCollisionConfig.txt
    - Affected: the lower labia twins (Vagina_CBP_L_02 / _R_02) and the four anus bones.
      Colliders: the penis bones from Penis_01 out, plus the hands and fingers already listed.
      Every actor's colliders count, whatever femaleOnly says (scan.cpp:204-218: an actor that is
      not tracked is still entered), and an actor's own colliders act on its own affected bones.
    - Sphere offsets are in the actor's frame; ours are x-only (reasons at AFFECTED).
    - Penis_00 is left out: every skeleton has the penis bones, and a female's own Penis_00
      rests 2 units from her vulva, where it would hold her open. Her Penis_01-05 rest 7+ units
      in front of her pubis (clear of her own spheres), but they are still colliders for OTHER
      actors: in a female/female scene they can push the partner. No key filters colliders by sex.

    python tools/physics_config.py
"""
import pathlib
import re

import zex_bones as zb

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS = zb.ab.DEFAULT_DATA / 'F4SE/Plugins'
OUT = ROOT / 'build/config'

ATTACH = [('Vagina_CBP_00', 'Clitoris'),
          ('Vagina_CBP_L_01', 'LabiaOuter'), ('Vagina_CBP_R_01', 'LabiaOuter'),
          ('Vagina_CBP_L_02', 'Labia'), ('Vagina_CBP_R_02', 'Labia')]
# No anus bones (decision A-11): OCBPC would SET them and discard their animation, and collisions on
# them, 1.0-1.4 units behind Nahka's ring, dragged the pocket into a spike in the owner's look.

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
SECTIONS = {
    'LabiaOuter': SOFT,
    'Labia': dict(SPRING, **QUIET),
    'Clitoris': dict(SPRING, **QUIET),
}
# The spheres (her bones and the partner's penis bones) are the physical design the weights are
# fitted to, so they live in ONE place, physics_design.py, with the reasons: x-only offsets in the
# actor's frame, lip sphere + penis sphere = 3.2 to close the gaps between penis bones, and why the
# anus's side spheres sit a unit outside the ring.
from physics_design import AFFECTED, COLLIDERS  # noqa: E402


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


def ocbp(text, skeleton):
    parts = sections(text)
    dead = []
    new = []
    for name, lines in parts:
        if name in ('Attach', 'Attach.A'):
            kept = []
            for line in lines:
                m = re.match(r'^\s*([A-Za-z0-9_]+)\s*=', line)
                if m and not line.lstrip().startswith(';') and m.group(1) not in skeleton:
                    kept.append(f'; not in the ZeX skeleton, so nothing to move: {line.strip()}')
                    dead.append(m.group(1))
                else:
                    kept.append(line)
            if name == 'Attach':
                kept += ['; --- anatomy (fo4-anatomy A-7, A-11): vagina physics on the _CBP_ twins; the anus has none (A-11)'] + \
                        [f'{b}={s}' for b, s in ATTACH]
            new.append((name, kept))
        else:
            new.append((name, lines))
    body = []
    for name, lines in new:
        body += lines
    for sec, vals in SECTIONS.items():
        body += ['', f'[{sec}]'] + [f'{k}={v}' for k, v in vals.items()]
    header = ['; Generated by fo4-anatomy tools/physics_config.py from the deployed ocbp.ini.',
              f'; {len(dead)} attach line(s) commented out (bones missing from ZeX); anatomy bones appended.']
    return '\n'.join(header + body) + '\n', dead


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
    skeleton = set(zb.skeleton_world(zb.SKELETON))
    OUT.mkdir(parents=True, exist_ok=True)
    ini, dead = ocbp(source('ocbp.ini'), skeleton)
    (OUT / 'ocbp.ini').write_text(ini, encoding='utf-8')
    (OUT / 'OCBPCollisionConfig.txt').write_text(collisions(source('OCBPCollisionConfig.txt')), encoding='utf-8')
    missing = [b for b, _ in ATTACH if b not in skeleton] + [n for n in list(AFFECTED) + list(COLLIDERS) if n not in skeleton]
    print(f'ocbp.ini: {len(dead)} dead attach lines commented out ({sorted(set(dead))}); '
          f'{len(ATTACH)} anatomy bones attached in {len(SECTIONS)} new sections')
    print(f'OCBPCollisionConfig.txt: +{len(AFFECTED)} affected, +{len(COLLIDERS)} colliders '
          f'({sum(len(s) for s in AFFECTED.values()) + sum(len(s) for s in COLLIDERS.values())} spheres)')
    print(f'anatomy bones missing from the skeleton: {missing or "none"}')
    if missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
