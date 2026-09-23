"""The physical design of the genitals, shared by the skeleton, the config, the weights and the checks.

One place for our bones (where they sit, what they do), the collision spheres on them and on the
partner's penis bones (written into OCBPCollisionConfig.txt by physics_config.py), the shaft each
opening expects, and so the push each bone will get (used by zex_bones.py to fit weights, and by
fit_check.py to judge them).

OUR OWN BONES (decision A-14). Women in the owner's game load Discrete Female Skeleton's
female/skeleton.nif (from Skeletal Adjustments for CBBE) and female/skeleton.hkx (from More Flexible
Ragdoll), and NEITHER has a single genital bone: every ZeX bone the body was weighted to was missing,
so those vertices hung at their standing-pose place while her pelvis moved (the fin, the rod and the
anus spike, 2026-09-23), and OCBPC had nothing to simulate. So the body now uses bones of its own,
added to a copy of that skeleton (tools/skeleton.py) under Pelvis_skin, a node no animation keys: the
ragdoll .hkx does not contain it, and it cannot contain names it has never seen. They follow the
pelvis rigidly; only OCBPC moves them.

Where the numbers come from:
  - Positions are skin space (the body's own coordinates); skeleton space = skin - SKIN_OFFSET
    (zex_bones.py step 2 measures the offset from the body's bind data and must agree).
  - The openings: Nahka's own sliders. VaginaPenetrate spreads the vulva around (0, 1.55, -55.58)
    by up to 0.92 per side; AnusPenetrate spreads a 0.45-radius ring around (0, -1.58, -54.07) by up
    to 1.04 (the >60% movers of each). Nahka drew them for a shaft of about 1.1 (vulva) and 1.35
    (anus) radius: the inner lips end ~1.1 from the midline, the ring ~1.35 from its centre.
  - The partner: BodyTalk's male body (the owner's MaleBody.nif) is 1.5-1.66 units in radius over
    Penis_01-05 (measured on the mesh), and its penis bones are 2.7-3.1 units apart. Men load ZeX's
    skeleton, which has those bones.
  - The axes: both canals run up and forward, about (0, 0.48, 0.88) (slices of the new geometry).

Each bone sits AT its sphere's centre (offset 0). Sphere offsets are in the actor's heading frame
(OCBPC CollisionHub.cpp:124, Thing.cpp:326), so any offset other than x drifts off the bone as the
pelvis pitches; with our own bones there is no need for one.

Tried and dropped (with ZeX's bones, still true of the geometry): the upper-lip bones as collision
bones for the opening. Those sat 0.9 AHEAD of the shaft on the midline, so the shaft drove them
forward, and canal-mouth vertices fitted to them stretched 35x (tools/fit_check.py).
"""
import math

SKIN_OFFSET = (0.0, 0.882, -120.844)    # skin = skeleton + this (zex_bones.py step 2 re-measures it)
PARENT = 'Pelvis_skin'                  # in the women's skeleton; no .hkx keys it (tools/skeleton.py)


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def _along(p, d, s):
    return tuple(p[i] + s * d[i] for i in range(3))


VAGINA_CENTRE, VAGINA_AXIS = (0.0, 1.55, -55.58), unit((0.0, 0.48, 0.88))
ANUS_CENTRE, ANUS_AXIS = (0.0, -1.58, -54.07), unit((0.0, 0.45, 0.89))
ANUS_FRONT = (0.0, ANUS_AXIS[2], -ANUS_AXIS[1])    # in the ring's plane, toward the vulva (3.5 away)

REST = {
    # the whole vulva's small sway (our pad, zex_bones.vulva_weights, A-19); where ZeX kept Vagina_CBP_00
    'AnatVulva': (0.0, 4.0, -55.5),
    # outer lips (labia majora, A-13): on each crest; they wobble and a hand or the shaft squishes them
    'AnatLipOuter_L': (-1.4, 2.45, -55.71), 'AnatLipOuter_R': (1.4, 2.45, -55.71),
    # inner lips (labia minora, A-9): beside the entrance; the shaft pushes them apart
    'AnatLip_L': (-1.2, 1.08, -55.71), 'AnatLip_R': (1.2, 1.08, -55.71),
    # the anus: four bones around Nahka's ring, in its plane. The front one is small and close so the
    # vaginal shaft clears it (2.77 from that axis > 2.0 + 0.3); the others a unit out.
    'AnatAnus_F': _along(ANUS_CENTRE, ANUS_FRONT, 0.7), 'AnatAnus_B': _along(ANUS_CENTRE, ANUS_FRONT, -1.0),
    'AnatAnus_L': _along(ANUS_CENTRE, (1.0, 0.0, 0.0), -1.0), 'AnatAnus_R': _along(ANUS_CENTRE, (1.0, 0.0, 0.0), 1.0),
}

# "x,y,z,r" per sphere (offsets 0: each bone is its sphere's centre). AnatVulva has none: it only sways.
AFFECTED = {'AnatLip_L': [(0.0, 0.0, 0.0, 1.2)], 'AnatLip_R': [(0.0, 0.0, 0.0, 1.2)],
            'AnatLipOuter_L': [(0.0, 0.0, 0.0, 0.8)], 'AnatLipOuter_R': [(0.0, 0.0, 0.0, 0.8)],
            'AnatAnus_F': [(0.0, 0.0, 0.0, 0.3)], 'AnatAnus_B': [(0.0, 0.0, 0.0, 0.6)],
            'AnatAnus_L': [(0.0, 0.0, 0.0, 0.6)], 'AnatAnus_R': [(0.0, 0.0, 0.0, 0.6)]}
COLLIDERS = {'Penis_01': [(0.0, 0.0, 0.0, 2.0)], 'Penis_02': [(0.0, 0.0, 0.0, 2.0)],
             'Penis_03': [(0.0, 0.0, 0.0, 2.0)], 'Penis_04': [(0.0, 0.0, 0.0, 2.0)],
             'Penis_05': [(0.0, 0.0, 0.0, 1.8)],
             # the fist (fisting, the owner's poll 2026-09-23). Jiggle Physics' own hand colliders are
             # the wrist (2.5) and the fingertips (1.5-1.8), so a fist's front had nothing. A hand is 5.42
             # across the four knuckles (MaleHands/FemaleHands): a fist ~6.5 wide. ONE ball on the
             # middle knuckle, not four small ones: a row of spheres wider than the opening puts the
             # outer ones beyond the lips, where they push the lips back IN (A-17, simulated).
             'LArm_Finger31': [(0.0, 0.0, 0.0, 3.0)], 'RArm_Finger31': [(0.0, 0.0, 0.0, 3.0)],
             # UAP's super mutants carry penis bones of their own (Supermutant/skeleton.nif: Penis1-4;
             # measured 2026-09-23, the only creature skeleton here with any). Bigger than a man's.
             **{f'Penis{k}': [(0.0, 0.0, 0.0, 2.5)] for k in (1, 2, 3, 4)}}
# which skeleton carries each collider, for physics_config's check (the rest are human, ZeX's)
CREATURE_COLLIDERS = {f'Penis{k}': 'Supermutant' for k in (1, 2, 3, 4)}
SHAFT = ('Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05')
SHAFT_RADIUS = 1.55          # what the partner's visible shaft needs cleared
PENIS_SPACING = 3.0

# Stretch (A-17, the fo4-ocbpc fork's stretch groups): each opening's bones form a group. When ALL of
# them are pushed across the opening's axis further than the knee, which is something bigger than a
# penis in it, each moves its child "<bone>_Stretch" out by gain x (the group's smallest push - knee),
# up to max. The body is weighted to those children instead of the bones. A child follows its bone,
# so a penis (below the knee: the child stays put) moves the body exactly as before, and only a
# fist-sized object adds the stretch. Simulated (smallest push across the axis): every penis path at
# the partner's bone spacing stays under the knee (vagina <= 2.21, anus <= 1.13), two fingers too
# (2.11 / 1.34); a fist or a wrist filling the entrance is far past it (vagina 3.9-4.5, anus 3.2-4.0).
# max starts at 1.5, not 2.5: at 2.5 a fist opens the entrance to a median 3.0 but stretches its worst
# edges x27; the owner's look tunes it (the keys are in ocbp.ini, no rebuild).
STRETCH = {'Labia': dict(group=1, knee=2.4, gain=3.0, max=1.5, axis=VAGINA_AXIS),
           'Anus': dict(group=2, knee=1.8, gain=2.0, max=1.5, axis=ANUS_AXIS)}
STRETCH_BONES = {b: b + '_Stretch' for b in ('AnatLip_L', 'AnatLip_R', 'AnatAnus_F', 'AnatAnus_B',
                                              'AnatAnus_L', 'AnatAnus_R')}

# Props (A-17, the fork's [Props]): whatever an animation hangs on a hand's AnimObject nodes (DR pack's
# dildos and bat) collides along its rendered length. The hands' WEAPON nodes are left out on purpose:
# a rifle held against her chest would squash her breasts.
PROPS = dict(nodes='AnimObjectR1,AnimObjectR2,AnimObjectR3,AnimObjectL1,AnimObjectL2,AnimObjectL3',
             radius=1.6, spacing=1.5, maxLength=40.0, minBound=1.0)

# gain: the fitted layer's target beyond Nahka's drawing scaled to the shaft. The owner's first look at
# A-14 (2026-09-23 19:10): "it works ... only 1 thing we need to widen vagina slightly more". Simulated
# (tools/fit_check.py's judge, entrance ring): x1.35 puts the entrance's median radius at the shaft's
# 1.55 (from 1.33) with 30% of the entrance still inside it (from 56%), and stretches less than Nahka's
# own slider (p99 5.0 / max 9.3 against 5.2 / 13.0); x1.5 would pass her p99.
# x1.40 (A-19): JaneBod's painting is gone, and its small outer-lip weights near the midline had
# been opening the entrance's front a little (x1.35 without them: 30% -> 32% as drawn, 27% -> 31%
# steeper). x1.40 puts the six paths' total back within 1% of the deployed build (3,233 vs 3,207
# vertices still inside), at p99 5.17 as drawn: Nahka's own, the limit above.
OPENINGS = {
    'vagina': dict(morph='VaginaPenetrate', centre=VAGINA_CENTRE, axis=VAGINA_AXIS, drawn_for=1.1,
                   bones=('AnatLip_L', 'AnatLip_R'), physics=True, gain=1.40),
    'anus': dict(morph='AnusPenetrate', centre=ANUS_CENTRE, axis=ANUS_AXIS, drawn_for=1.35,
                 bones=('AnatAnus_F', 'AnatAnus_B', 'AnatAnus_L', 'AnatAnus_R'), physics=True),
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
    # the SHAFT's spheres: the weights are fitted to a penis, never to the fist's bigger ball (A-17)
    reach = max(r for name in SHAFT for *_, r in COLLIDERS[name]) + AFFECTED[bone][0][3]
    return tuple(x / h for x in radial), max(0.0, reach - h)
