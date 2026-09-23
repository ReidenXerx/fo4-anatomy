"""The physical design of the openings, shared by the config, the weights and the checks (A-9).

One place for what a collision will do: the spheres on her bones and on the partner's penis bones
(written into OCBPCollisionConfig.txt by physics_config.py), the shaft each opening expects, and so
the push each bone will get (used by zex_bones.py to fit weights, and by fit_check.py to judge them).

Where the numbers come from:
  - Bone rest positions: the ZeX skeleton in skin space (zex_bones.py step 1 reproduces them; the
    same values are pinned in verify_zex.py).
  - The openings: Nahka's own sliders. VaginaPenetrate spreads the vulva around (0, 1.55, -55.58)
    by up to 0.92 per side; AnusPenetrate spreads a 0.45-radius ring around (0, -1.58, -54.07) by up
    to 1.04 (the >60% movers of each; tools/penetrate_morphs in the scratch notes). Nahka drew them
    for a shaft of about 1.1 (vulva) and 1.35 (anus) radius: the inner lips end ~1.1 from the
    midline, the ring ~1.35 from its centre.
  - The partner: BodyTalk's male body (the owner's MaleBody.nif) is 1.5-1.66 units in radius over
    Penis_01-05 (measured on the mesh), and its penis bones are 2.7-3.1 units apart.
  - The axes: both canals run up and forward, about (0, 0.48, 0.88) (slices of the new geometry).

Tried and dropped: the upper-lip twins (CBP_L_01 / R_01) as collision bones too. The fit then
reproduced 78% of the vulva's opening instead of 51% and cleared more of the entrance, but those
bones sit 0.9 AHEAD of the shaft on the midline, so it drives them forward (2.1 units), and canal-mouth
vertices fitted to them were pulled forward and out of the shaft while their neighbours were not:
edges stretched 35x at the mouth (tools/fit_check.py). Two lateral bones stretch no more than
Nahka's own slider does.

Measured, and it shapes the anus: ZeX puts the four anus bones 1.0-1.4 units BEHIND Nahka's ring.
A shaft entering her ring pushes all four backwards, so the ring's back and sides can open and its
front, 1.2 units from the vulva, has no bone behind it to open it. The weight fit states that
residual rather than hiding it.
"""
import math

REST = {'Vagina_CBP_L_02': (-0.64, 1.09, -55.71), 'Vagina_CBP_R_02': (0.53, 1.07, -55.71),
        'Anus_01': (0.0, -2.98, -54.26), 'Anus_02': (0.0, -2.53, -54.49),
        'Anus_03': (0.10, -2.76, -54.44), 'Anus_04': (-0.10, -2.76, -54.44)}

# "x,y,z,r" per sphere; offsets are in the ACTOR's frame (heading only; CollisionHub.cpp:124 and
# Thing.cpp:326), so only x (left/right) offsets are used: they survive the pelvis pitching.
AFFECTED = {'Vagina_CBP_L_02': [(-0.6, 0.0, 0.0, 1.2)], 'Vagina_CBP_R_02': [(0.6, 0.0, 0.0, 1.2)],
            }
# The anus carries NO physics (decision A-11): in the owner's own look (2026-09-23, Photo118-120) its
# bones, pushed off to OCBPC's cap by a shaft passing beside them, dragged the anal pocket out into a
# ~5-unit spike toward the partner. The simulator had predicted the pinning (hold 4.24 = the cap).
COLLIDERS = {'Penis_01': [(0.0, 0.0, 0.0, 2.0)], 'Penis_02': [(0.0, 0.0, 0.0, 2.0)],
             'Penis_03': [(0.0, 0.0, 0.0, 2.0)], 'Penis_04': [(0.0, 0.0, 0.0, 2.0)],
             'Penis_05': [(0.0, 0.0, 0.0, 1.8)]}
SHAFT_RADIUS = 1.55          # what the partner's visible shaft needs cleared
PENIS_SPACING = 3.0


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


OPENINGS = {
    'vagina': dict(morph='VaginaPenetrate', centre=(0.0, 1.55, -55.58), axis=unit((0.0, 0.48, 0.88)),
                   drawn_for=1.1, bones=('Vagina_CBP_L_02', 'Vagina_CBP_R_02'), physics=True),
    'anus': dict(morph='AnusPenetrate', centre=(0.0, -1.58, -54.07), axis=unit((0.0, 0.45, 0.89)),
                 drawn_for=1.35, bones=('Anus_01', 'Anus_02', 'Anus_03', 'Anus_04'), physics=False),
}


def sphere_centre(bone):
    ox, oy, oz, _ = AFFECTED[bone][0]
    r = REST[bone]
    return (r[0] + ox, r[1] + oy, r[2] + oz)


def expected_push(bone, opening, centre=None, axis=None):
    """(unit direction, distance) a bone is pushed when a shaft of collider spheres runs along the
    opening's axis through its centre: straight out from the axis until its sphere clears a
    collider sphere sitting level with it (the worst case between spheres is the simulator's job)."""
    o = OPENINGS[opening]
    c, a = centre or o['centre'], axis or o['axis']
    s = sphere_centre(bone)
    d = [s[i] - c[i] for i in range(3)]
    along = sum(d[i] * a[i] for i in range(3))
    radial = [d[i] - along * a[i] for i in range(3)]
    h = math.sqrt(sum(x * x for x in radial))
    reach = max(r for spheres in COLLIDERS.values() for *_, r in spheres) + AFFECTED[bone][0][3]
    return tuple(x / h for x in radial), max(0.0, reach - h)
