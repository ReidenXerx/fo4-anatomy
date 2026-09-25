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
# The inner lips' spheres 1.2 -> 1.7 (2026-09-26, tools/tube_check.py): A-31's thinner shaft (colliders 2.0 -> 1.7)
# pushed them 1.65 where the owner's approved look (A-15) had 2.17, and fit_check's "through" rose 27% -> 42%. The
# vulva's vertices follow these bones only in part, so the lips must push past the flesh for the flesh to clear
# it. With the tube ([Tube]) 1.7 pushes 2.25 and leaves 26% through, under the fist stretch's knee (2.4) on every
# path; 1.9 would cross it (2.48). The price: the region's p99 edge stretch 3.7 -> 4.7.
AFFECTED = {'AnatLip_L': [(0.0, 0.0, 0.0, 1.7)], 'AnatLip_R': [(0.0, 0.0, 0.0, 1.7)],
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
           'Anus': dict(group=2, knee=0.65, gain=2.0, max=1.5, axis=ANUS_AXIS)}
# (Anus knee 1.8 -> 0.65, the owner's look 2026-09-24: "a little more hole opening". A penis pushes the ring
# across by ~1.1, under 1.8, so the stretch never opened for one. fit_check, stretch now simulated: as drawn
# 71% -> 47% of the entrance still inside the shaft, worst edge stretch 12.95 under Nahka's own slider's 14.77.)
STRETCH_BONES = {b: b + '_Stretch' for b in ('AnatLip_L', 'AnatLip_R', 'AnatAnus_F', 'AnatAnus_B',
                                              'AnatAnus_L', 'AnatAnus_R')}

# Props (A-17, the fork's [Props]): whatever an animation hangs on a hand's AnimObject nodes (DR pack's
# dildos and bat) collides along its rendered length. The hands' WEAPON nodes are left out on purpose:
# a rifle held against her chest would squash her breasts.
# targets (fork 2026-09-23): a prop pushes ONLY our genital and anus bones. The first zero-touch log
# showed everyday idle props on AnimObjectR1 (mugs, clipboards, up to 37 units long); an actor's own
# colliders act on its own bones, so without this a woman drinking would push her own breasts.
PROPS = dict(nodes='AnimObjectR1,AnimObjectR2,AnimObjectR3,AnimObjectL1,AnimObjectL2,AnimObjectL3',
             radius=1.6, spacing=1.5, maxLength=40.0, minBound=1.0, targets=','.join(AFFECTED))

# The mouth (A-20, the fo4-ocbpc fork's [Mouth]). FO4 heads have no mouth bones; the fork writes the
# face's merged expression weights (Jaw Open, both lip funnels, Upper Lip Up) over the animation's
# while a penis chain crosses the plane of her lips inside the mouth. Where the lips meet, which way
# they face and how far Jaw Open parts them are measured on the game's own base heads
# (tools/mouth.py re-measures them from Fallout4 - Meshes.ba2 and refuses a mismatch):
#   female: lips meet at (-1.80, 8.12, 0) in the HEAD bone's space; Jaw Open 1.0 puts them 2.97 apart
#   male:   (-1.84, 7.78, 0); 2.30 apart
#   the mouth faces the bone's +y, the face's up is the bone's +x (Bethesda bones run along x)
# The lower lip must drop below the shaft's bottom (the upper lip does not move with Jaw Open), so a
# visible shaft (collider radius - skin) centred on the lip line needs Jaw Open r / gap + margin
# (female: 1.55 / 2.97 + 0.08 = 0.60), and one riding a unit lower 0.94. Props at the mouth stay off:
# vanilla eating and drinking idles hang bottles and food on the same hand nodes.
MOUTH_CHAINS = (SHAFT, tuple(f'Penis{k}' for k in (1, 2, 3, 4)))

# The rest of the face while the mouth is busy (the owner, 2026-09-24: "expressions on the face
# instead of stony but mouth ... cheeks, brows, nose"). Rapport's six oral styles (Rapport_Oral_1..6,
# its generated mfgSetData.xml) each write only a few of these, and some leave the inner brows and
# cheeks at rest; with max() below, a style's value is the floor and ours shows where higher. Each
# term: its value at contact, + at full depth (FACE_DEPTH units past the lips), + at full stroke speed
# (FACE_STROKE units/s in and out). The fork only ever RAISES a morph (max with what the face has),
# so Rapport's sets and the animation's own face stay. Ids: the engine's 50-morph expression table,
# alphabetical by full name (fo4-rapport/tools/make_mfg.py quotes it; the mouth's own ids 2/21/22/
# 44/46 prove the numbering in game). 3 and 26 are the outer brows (the table calls 26 "Right Outer
# Brow Up"; it sits where "Right Brow Outer Up" sorts, the mirror of 3).
FACE_MORPHS = {'Brow Squeeze': 0, 'Left Brow Outer Up': 3, 'Left Cheek Up': 4, 'Left Middle Brow Up': 14,
               'Left Nose Up': 15, 'Right Outer Brow Up': 26, 'Right Cheek Up': 27,
               'Right Middle Brow Up': 37, 'Right Nose Up': 38}
FACE_WHILE_BUSY = [               # (morph, at contact, + at full depth, + at full stroke speed)
    ('Left Middle Brow Up', 0.30, 0.30, 0.0), ('Right Middle Brow Up', 0.30, 0.30, 0.0),  # pleading
    ('Left Brow Outer Up', 0.10, 0.10, 0.0), ('Right Outer Brow Up', 0.10, 0.10, 0.0),
    ('Brow Squeeze', 0.0, 0.15, 0.20),                                                     # effort
    ('Left Cheek Up', 0.30, 0.15, 0.0), ('Right Cheek Up', 0.30, 0.15, 0.0),               # cheeks
    ('Left Nose Up', 0.0, 0.10, 0.15), ('Right Nose Up', 0.0, 0.10, 0.15),                 # nose
]
FACE_DEPTH, FACE_STROKE = 6.0, 20.0

# skin: collider radius minus this = the shaft's visible radius at her lips. It was 0.45; measured on BodyTalk4's
# erect shaft (scratchpad, 2026-09-25) the colliders (2.0 shaft, 1.8 head) already sit ON its surface (half-width
# 1.91-1.98, half-height 1.65-1.87 unscaled), so with A-31's shape the mouth took a 1.62-1.69 wide shaft for 1.25:
# the lips wrapped a thinner one (the clipping) and the corners (A-32), which open only past +-1.6, never did.
# 0.05 then made them ring the shaft too wide (the owner: "like the same big width as head"): the colliders sit on
# its widest points, the ridge, and its mean radius (x0.85) is ~1.51; 0.2 gives 1.50 for the shaft, 2.14 for the
# head (x1.3). And the lips now ease at lipOpenRate / lipCloseRate, not the jaw's slow close (6), so they close
# back onto the shaft between strokes instead of staying as wide as the head that just passed.
# The glans as the mouth sees it (the fork's Glans.h; tools/glans_profile.py measures it). The mouth reads a penis
# as its collider spheres, the radius straight from one bone's to the next, and that put the mushroom's widest
# point ON the tip bone. On the mesh the crown is 0.6 R behind it (R = the tip sphere's radius, 1.8 x the head):
# at head x1.4 the spheres gave 1.75 where the crown is 2.52, so the lips opened for a head 0.76 thinner and its
# rim showed past both corners (the owner's Photo212, 2026-09-25). Steps: (along, radius) in R, from the tip bone
# back (along < 0); the same in R at head 1.2, 1.3 and 1.4 (to +-0.03). The last is the bone itself.
GLANS_PROFILE = ((-0.85, 0.90), (-0.60, 1.00), (-0.35, 0.93), (-0.12, 0.81), (0.0, 0.73))
MOUTH = dict(enabled=1, chains='/'.join('|'.join(c) for c in MOUTH_CHAINS), props=0,
             glans=SHAFT[-1], glansProfile=','.join(f'{a}:{r}' for a, r in GLANS_PROFILE),
             femaleX=-1.80, femaleY=8.12, femaleZ=0.0, maleX=-1.84, maleY=7.78, maleZ=0.0,
             facingX=0.065, facingY=0.998, facingZ=0.0, upX=0.998, upY=-0.065, upZ=0.0,
             femaleGap=2.97, maleGap=2.30, halfWidth=2.9, below=3.0, above=1.5, skin=0.2, lipOpenRate=60.0, lipCloseRate=50.0,
             ahead=3.0, anticipate=0.3, margin=0.08, funnel=0.3, liftMove=0.53,
             openRate=20.0, closeRate=6.0, blendRate=12.0, holdSeconds=0.35,
             face=','.join(f'{FACE_MORPHS[m]}:{c}:{d}:{s}' for m, c, d, s in FACE_WHILE_BUSY),
             faceDepth=FACE_DEPTH, faceStroke=FACE_STROKE, faceRate=6.0, strokeRate=4.0)

# The fork's [Face] (A-27): Rapport's faces are written after the engine's merge. Only the switch ships:
# probe= (log what a line's lip sync moves) and test= (the self-test) are for a tester's own ini, and
# release.py refuses an ini that sets them.
FACE = dict(authority=1, react=1)   # react: the busy mouth's reaction rises above Rapport's held face
# The fork's [Eyes] (glances, RFAG; the owner, 2026-09-25: "glances on 1-2 seconds"): Rapport says who looks at
# whom and for how long, the fork turns the eye the engine's way (it slides the eye texture's UV; fork Glance.h)
# and opens the lids. glances=1 tells Rapport it works (hello bit 4): only once the owner has seen it in game.
# signUp/signSide: the engine's own axes, the owner's look and the probe (2026-09-25): the eye texture's u is
# VERTICAL (-0.25 x up) and v SIDEWAYS (-0.25 x side); the first build had them swapped and the eyes went a
# quarter-turn off ("his head on perfect 12 h then her gaze is somewhere 8-10 h"). The eyes sit eyeRise up the face from the
# mouth's point and eyeBack into it (a human face's proportions in game units; an error of a unit is ~1 degree
# at a partner's distance). probe= and test= are a tester's (release.py refuses them).
EYES = dict(enabled=1, glances=0, signUp=-1, signSide=-1, eyeRise=4.8, eyeBack=0.8)
# The fork's [Tube] (2026-09-26, fork Tube.h, tools/tube_check.py): every penis chain collides as ONE tube instead
# of its bones' balls. OCBPC collides sphere against sphere and ADDS every overlap; five balls ~3 apart made a lip
# ride 0.8 in and out along the shaft, stand 0.6 .. 1.4 ahead of the glans, and a ball in two grid cells push twice.
# The tube is the mouth's reading of a chain (A-32): the radius straight between bones less the skin (the flesh's
# mean), and the glans's own profile. Measured in fit_check's port: the anus 72% -> 27% through, its thrust wobble
# 0.69 -> 0.21, its opening held on a steep entry (0.52 -> 1.25); the vagina's wobble halved.
TUBE = dict(enabled=1, chains=MOUTH['chains'], skin=MOUTH['skin'], glans=MOUTH['glans'],
            glansProfile=MOUTH['glansProfile'])

# The fork's [Aim] (A-28): each frame a penis chain turns about its root onto the opening it is closest to
# entering. The chain is ZeX's: Penis_00 hangs off the pelvis and carries the shaft the body skins to
# (MaleBody names Penis_00-05). Her openings are the fit's own lines -- VAGINA/ANUS_CENTRE along their
# _AXIS, into her, the paths every shaft was simulated along (fit_check, ocbpc_sim) -- which
# physics_config.aim_keys writes into Pelvis_skin's frame as [Bones] are. Mouths are [Mouth]'s own point.
# Angles in degrees. A new lock turns the shaft at most captureAngle and is kept up to keepAngle; the
# shaft runs within entryAngle of the opening's axis, and the opening lies within reach x the chain's
# length (16.1). It aims depth inside, and stretches up to maxStretch so minInside passes the entrance.
# Only people in an AAF scene (Anatomy:Arousal tells the fork through AnatomyAim.SetBusy).
AIM_CHAIN = ('Penis_00',) + SHAFT
# The second look (the owner, 2026-09-24, Photo164-166): it works, but (1) hand-job stages of a vaginal scene
# were aimed into her too, and (2) a deep shaft ran straight on along the entrance's axis, which tilts
# forward, and came out through her mons. So: a lock needs the animation's own shaft line to pass within
# captureMiss of the entrance (a near miss the animation meant, kept to keepMiss), a knuckle within
# handRadius of the shaft's outer part means a hand holds it (not aimed, and not for handHold after), and
# past the entrance the shaft bends joint by joint along the path inside her (PPA's "snake").
AIM = dict(enabled=1, requireScene=1, captureAngle=35, keepAngle=45, captureMiss=5.0, keepMiss=8.0, entryAngle=75,
           reach=1.3, minReach=2.0, depth=2.0, minInside=3.0, maxStretch=1.10, rate=8.0, mouths=1,
           anatomyBone='AnatVulva', hands='LArm_Finger31|RArm_Finger31', handRadius=4.0, handHold=1.0,
           grips='LArm|RArm',   # a gripping hand is the target: the middle of <side>_Finger21..53
           mouthDrop=1.3,       # a mouth is entered this far below her lip line: centred on it the shaft rode
                                # over her upper lip into cheek and nose (the owner's look, 2026-09-24)
           mouthLead=1.5)       # and turned onto her mouth's axis this far in front of her lips: straight from his
                                # hips, it crossed them at a slant, an oval wider than her mouth opens, and the
                                # corner clipped (the owner's look, 2026-09-25, A-32)
# The shape (A-31, the owner's poll 2026-09-25): "i want make it mushroom ... more narrow ствол give us more
# fit stability especially with mouth ... i like when head is bigger". Everyone, the player too; the head
# varied per man. The fork scales the chain's bones at run time (BodyTalk's files untouched): Penis_01 x
# shaft (Penis_02..04 inherit it, their joints pushed back out so every joint stays put) and the tip bone
# Penis_05, which alone carries the glans (0.96-1.00 over its last three slabs), to head in the world.
# Measured on BodyTalk4's erect penis (scratchpad penis_shape, max radius root -> tip): the shaft 2.04 -> 1.74
# at 0.85, the head 1.89 today (narrower than the shaft: a bullet) -> 2.14 / 2.33 / 2.52 at 1.2 / 1.3 / 1.4,
# the crown just behind the tip (the tip bone pivots at the tip), the length +0.2..0.4. The colliders on
# those bones scale with them (Collision.cpp), so the thinner shaft also pushes her open less.
# headMax was 1.4. With the crown where the mesh has it (GLANS_PROFILE), the widest mouth the face morphs make
# (A-32: the rim's ends -2.39 .. 2.26 at full stretch) still held a x1.3 crown 0.1 short a side and x1.4 0.3; the
# owner's poll (2026-09-25): "Narrow the range". At x1.25 the right corner is ~0.05-0.1 short (the mouth opens
# less to the right), practically flush; x1.2 is flush.
SHAPE = dict(enabled=1, shaft=0.85, headMin=1.2, headMax=1.25)
# The paths inside her (skin space), from tools/canal.py: the middle of her body along the midline, height
# by height, measured on the installed body. Flesh around them (to the nearest vertex): 0.17 just inside the
# vagina (the lips open there anyway), 1.46 four units in, then 2.5 to 5.9 -- past the shaft's 1.55 from
# there on. It leads a little along the entrance's axis, then curves BACK toward her middle before rising.
VAGINA_PATH = ((0.0, 0.93, -53.59), (0.0, -0.27, -51.33), (0.0, 0.08, -48.36), (0.0, 0.68, -45.44),
               (0.0, 1.39, -42.54), (0.0, 2.08, -39.62))
ANUS_PATH = ((0.0, -0.36, -51.33), (0.0, 0.08, -48.39), (0.0, 0.67, -45.47), (0.0, 1.38, -42.56),
             (0.0, 2.08, -39.65), (0.0, 2.58, -36.69))
# The throat: offsets from the mouth ([Mouth]'s point), in the standing body's frame (y forward, z up), so
# it holds for either skeleton. The first design turned down the neck ~2 inside the lips; the owner's look
# (Photo, 2026-09-24): "mouth needs same treatment". A blowjob keeps 6-8 of the shaft in the mouth, so
# that bent the shaft down under her tongue and out through her jaw. Now: straight back 6 (the mouth's
# depth, to the throat), then down the front half of the neck.
# The owner's x-ray (Photo176, 2026-09-25), her head thrown back: the shaft turned down right behind the
# mouth and came out through the front of her throat under the chin. "penis should go deeper to throat when
# it start beinding and go down to neck ... closer to back side of neck". Two faults, both measured
# (scratchpad neck_measure: the head mesh AND the body, the midline |x| < 1.6, world, standing):
#  - under the jaw the throat's front is at y 1.1-1.5, not the 3.2-4.6 of the lower neck the first design
#    measured, so the old path (y -0.6..-0.9 there) ran 2.0 behind the skin: 0.45 of flesh past the shaft;
#  - the whole path hung from HEAD, so a head thrown back swung its neck part forward, out of the neck.
# Now: straight back 9 (to the pharynx), then down at y -3.0..-3.5, 60% of the upper neck's depth from the
# front (front 1.3, back -6.65 at z 112.3: 4.7 from the front, 3.25 from the back). The mouth part is in
# HEAD's frame (THROAT), the neck part in Neck's (THROAT_NECK), so the path bends where her neck bends.
# Both are offsets from the mouth ([Mouth]'s point) in the standing body's frame (y forward, z up);
# physics_config places them in each skeleton's own bones.
# The owner's lying blowjob (2026-09-26, Photo225, him on his back, her head bent down over his hips): "penis
# start bending not when he closer to back of neck inside throat but on the front wall of neck -> clipping".
# The head turns about its bone's origin, the top of the spine: 8.12 behind the female mouth point and 1.8 above
# it ([Mouth] femaleMouth). The pharynx points (back 9 and 10.1) sit BELOW that pivot, 2.5 and 5.0 down, i.e.
# in the neck, but hung from HEAD: a head bent 60 degrees down swings a point 2.5 below the pivot ~2.2 forward,
# to the neck's front wall. So only the mouth's own points (in front of the pivot) hang from HEAD now; from
# the pharynx down, the path is the neck's, and the bend happens where the neck is, whatever the head does.
THROAT = ((0.0, -3.0, -0.12), (0.0, -6.0, -0.3))
THROAT_NECK = ((0.0, -9.0, -0.7), (0.0, -10.1, -3.2), (0.0, -10.5, -6.2), (0.0, -10.6, -9.2), (0.0, -10.3, -12.2))

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
