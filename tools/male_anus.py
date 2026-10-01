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


def build(nif_path, osd_path=None):
    import osd as osd_module
    sp = spec(floor_uv(nif_path))
    return ac.build(nif_path, osd_path, osd_module if osd_path else None, spec=sp)


if __name__ == '__main__':
    print(build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None))
