# SPDX-License-Identifier: GPL-3.0-only
"""Anatomy's own default physics preset (decision A-46): the ocbp.ini (and collision file) the engine reads when
the player has none. Written from targets, not from anyone's preset: the presets players use may not ship in a
mod that earns Donation Points (MadKita's Actual Jiggle, 3BBB Physics, Jiggle Physics; read on their pages
2026-09-26), and a file at Data\\F4SE\\Plugins\\ocbp.ini would overwrite every player's own preset.

The owner asked for it to be "different but not less advanced": every flesh bone plain CBBE weights (measured on
the Anatomy body: breasts 552 each once moved off the cloth bones, thigh 559, thigh low 308, belly 182, butt 122,
thigh fat 72, upper belly 29), a spring that firms up toward its limit (stiffness2), a tilt that follows the swing
(rotational), a calmer profile under clothes ([Attach.A], detectArmor), and hands that press breasts and butt
(collision spheres measured from the mesh in each bone's space).

For each part, a target in plain words: how far it moves in a jog, how many visible swings follow a landing, how
soon it settles, the most it may ever move, and how far it tilts at the jog's peak. Every candidate spring runs
through tools/ocbpc_sim.py (the engine's own update, ported) on two scenes and the closest is kept:
  run      the pelvis bobbing 2.0 units at 2.6 Hz (a jog), 60 fps: the largest offset after the first second
  landing  the pelvis dropping 5 units in one frame and stopping: peak, swings, settle time

    python tools/default_preset.py      # search, print the measurements, write build/config/Anatomy/ocbp-default.ini
                                        # and build/config/Anatomy/OCBPCollisionConfig-default.txt
"""
import itertools
import math
import pathlib

import ocbpc_sim as sim

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/config/Anatomy/ocbp-default.ini'
COLLISION_OUT = ROOT / 'build/config/Anatomy/OCBPCollisionConfig-default.txt'
OUT_3BBB = ROOT / 'build/config/Anatomy/ocbp-default-3bbb.ini'                  # A-57
COLLISION_OUT_3BBB = ROOT / 'build/config/Anatomy/OCBPCollisionConfig-default-3bbb.txt'
FPS = 60
TICK, STEP = 4.0, 0.016                      # the engine's defaults (Thing.cpp: timeStep absent -> 0.016)

# run/cap in game units at the bone (after linear); settle in seconds to within 10% of the peak; swings = overshoots
# past rest bigger than 15% of the first peak; tilt = degrees at the jog's peak (0: none). The sideways and forward
# motion follow the vertical at the xyz ratios. `clothed` scales the run for the [Attach.A] profile.
PARTS = {
    'Breasts':    dict(bones=('LBreast_skin', 'RBreast_skin'), run=1.2, swings=2, settle=0.9, cap=3.0,
                       xyz=(0.6, 0.8, 1.0), tilt=6.0, clothed=0.5),
    'Butt':       dict(bones=('LButtFat_skin', 'RButtFat_skin'), run=0.6, swings=1, settle=0.5, cap=1.5,
                       xyz=(0.5, 0.7, 1.0), tilt=3.0, clothed=0.6),
    'Belly':      dict(bones=('Belly_skin',), run=0.3, swings=1, settle=0.4, cap=0.8, xyz=(0.3, 1.0, 0.8), tilt=0.0,
                       clothed=0.6),
    'UpperBelly': dict(bones=('UpperBelly_skin',), run=0.15, swings=1, settle=0.35, cap=0.5, xyz=(0.3, 1.0, 0.8),
                       tilt=0.0, clothed=0.6),
    'Thigh':      dict(bones=('LLeg_Thigh_skin', 'RLeg_Thigh_skin'), run=0.2, swings=1, settle=0.3, cap=0.5,
                       xyz=(0.6, 0.6, 1.0), tilt=0.0, clothed=0.7),
    'ThighLow':   dict(bones=('LLeg_Thigh_Low_skin', 'RLeg_Thigh_Low_skin'), run=0.12, swings=1, settle=0.3,
                       cap=0.4, xyz=(0.6, 0.6, 1.0), tilt=0.0, clothed=0.7),
    'ThighFat':   dict(bones=('LLeg_Thigh_Fat_skin', 'RLeg_Thigh_Fat_skin'), run=0.35, swings=1, settle=0.45,
                       cap=0.9, xyz=(0.8, 0.6, 1.0), tilt=0.0, clothed=0.7),
}

# collision: spheres measured on the Anatomy body (the weight-weighted centre of what the bone carries, the median
# radius of the vertices it carries at least a quarter of); hands press them. The offset is from the bone's origin in
# the ACTOR's frame: the engine places a sphere at bone + skeleton rotation * offset (Thing.cpp), never turning it by
# the bone's own rotation. A-46 measured them in bone space, which put the breast sphere 19 units up at the collarbone
# and the butt's 3.2 off (A-57); these are the same spheres in the engine's frame.
COLLIDE = {
    'LBreast_skin': (-3.38, 7.08, -8.17, 2.5), 'RBreast_skin': (3.38, 7.08, -8.17, 2.5),
    'LButtFat_skin': (-0.9, -7.1, -0.41, 4.2), 'RButtFat_skin': (0.87, -7.09, -0.42, 4.2),
}

# A-57: the preset for a 3BBB body (builder --body 3bbb writes it as ocbp-body.ini). 3BBB's breasts are a chain,
# LBreast_01 -> 02 -> 03 (each the next one's parent), so the tip rides on all three: the base moves least and the tip
# swings longest. Butt_01 (under the pelvis) replaces ButtFat, which carries nothing on 3BBB; LBreast_skin carries
# nothing either. Thigh_01_F/R are 3BBB's front and back thigh flesh. The rest is CBBE's.
PARTS_3BBB = {
    'Breast1': dict(bones=('LBreast_01_skin', 'RBreast_01_skin'), run=0.6, swings=2, settle=0.9, cap=1.8,
                    xyz=(0.6, 0.8, 1.0), tilt=4.0, clothed=0.5),
    'Breast2': dict(bones=('LBreast_02_skin', 'RBreast_02_skin'), run=0.48, swings=2, settle=1.0, cap=1.4,
                    xyz=(0.6, 0.8, 1.0), tilt=0.0, clothed=0.5),
    'Breast3': dict(bones=('LBreast_03_skin', 'RBreast_03_skin'), run=0.42, swings=3, settle=1.1, cap=1.2,
                    xyz=(0.6, 0.8, 1.0), tilt=0.0, clothed=0.5),
    'Butt3B': dict(bones=('LButt_01_skin', 'RButt_01_skin'), run=0.6, swings=1, settle=0.5, cap=1.5,
                   xyz=(0.5, 0.7, 1.0), tilt=0.0, clothed=0.6),
    'ThighF': dict(bones=('LLeg_Thigh_01_F_skin', 'RLeg_Thigh_01_F_skin'), run=0.2, swings=1, settle=0.35, cap=0.5,
                   xyz=(0.6, 0.6, 1.0), tilt=0.0, clothed=0.7),
    'ThighB': dict(bones=('LLeg_Thigh_01_R_skin', 'RLeg_Thigh_01_R_skin'), run=0.25, swings=1, settle=0.4, cap=0.6,
                   xyz=(0.6, 0.6, 1.0), tilt=0.0, clothed=0.7),
}
PARTS_3BBB.update({k: v for k, v in PARTS.items() if k not in ('Breasts', 'Butt')})
COLLIDE_3BBB = {                              # measured on the 3BBB build the same way, in the engine's frame
    'LBreast_02_skin': (-1.11, 3.07, 1.56, 3.65), 'RBreast_02_skin': (1.12, 3.07, 1.55, 3.65),
    'LBreast_03_skin': (-2.13, 2.52, 2.25, 1.46), 'RBreast_03_skin': (2.13, 2.52, 2.25, 1.46),
    'LButt_01_skin': (-0.75, -5.62, -0.66, 3.7), 'RButt_01_skin': (0.76, -5.62, -0.65, 3.7),
}
CHAIN = ('Breast1', 'Breast2', 'Breast3')
HANDS = {'LArm_Hand': 2.5, 'RArm_Hand': 2.5}

ZERO_KEYS = ('gravityBias', 'gravityCorrection', 'cogOffsetX', 'cogOffsetY', 'cogOffsetZ',
             'rotationalX', 'rotationalY', 'rotateLinearX', 'rotateLinearY', 'rotateLinearZ',
             'rotateRotationX', 'rotateRotationY', 'rotateRotationZ', 'absRotX')


def section(k, d, lin, maxo, k2=0.0, tilt_z=0.0):
    s = {key: 0.0 for key in ZERO_KEYS}
    s.update(stiffness=k, stiffness2=k2, damping=d, timetick=TICK, timeStep=STEP, rotationalZ=tilt_z,
             linearX=lin[0], linearY=lin[1], linearZ=lin[2], maxoffsetX=maxo[0], maxoffsetY=maxo[1], maxoffsetZ=maxo[2])
    return s


def landing(s):
    """The pelvis drops 5 units at frame 10 and stays: the bone's vertical offset, frame by frame."""
    b = sim.Bone(s, [0.0, 0.0, 0.0], 0.6)
    out = []
    for f in range(FPS * 3):
        carry = [0.0, 0.0, -5.0 if f >= 10 else 0.0]
        b.update(carry, [], 1000 / FPS)
        if f >= 10:
            out.append(b.offset(carry)[2])
    return out


def measure(s):
    run = sim.run_gait(s, 2.0, 2.6, FPS)
    z = landing(s)
    first = max(range(len(z)), key=lambda i: abs(z[i]))
    peak = abs(z[first]) or 1e-9
    swings, sign = 0, math.copysign(1, z[first])
    for v in z[first:]:
        if -sign * v > 0.15 * peak:          # past rest, the other way
            swings += 1
            sign = -sign
    last = max((i for i, v in enumerate(z) if abs(v) > 0.10 * peak), default=0)
    return dict(run=run, peak=peak, swings=swings, settle=(last + 1) / FPS)


def fit(t, k, d, run_scale):
    """For one spring: linear for the target run, maxoffset for the cap (the engine caps the INTERNAL offset:
    actual = maxoffset * linear), stiffness2 so the restoring force doubles at the cap (soft near rest, firm at the
    limit), re-fitted together; the tilt from the NAKED target (radians per unit of offset, so a calmer clothed
    swing tilts proportionally less)."""
    target, cap = t['run'] * run_scale, t['cap'] * run_scale
    base = measure(section(k, d, (1.0, 1.0, 1.0), (50.0, 50.0, 50.0)))['run'] or 1e-6
    lin = tuple(target / base * r for r in t['xyz'])
    for _ in range(3):
        maxo = tuple(cap / max(l, 1e-3) for l in lin)
        run = measure(section(k, d, lin, maxo, k / maxo[2]))['run'] or 1e-6
        lin = tuple(l * target / run for l in lin)
    lin = tuple(round(l, 3) for l in lin)
    maxo = tuple(round(cap / max(l, 1e-3), 2) for l in lin)
    tilt = -round(math.radians(t['tilt']) / t['run'], 4) if t['tilt'] else 0.0
    s = section(k, d, lin, maxo, round(k / maxo[2], 3), tilt)
    return s, measure(s)


def design(t, run_scale=1.0):
    """The spring (stiffness, damping) whose landing, WITH its fitted linear, cap and stiffness2, has the target
    swings and settle time and the target run."""
    best = None
    for k, d in itertools.product([10, 15, 20, 30, 40, 60, 80, 120, 160, 220, 300],
                                  [0.5, 1, 1.5, 2, 3, 4, 6, 8, 12]):
        s, m = fit(t, k, d, run_scale)
        score = (abs(m['swings'] - t['swings']) * 2 + abs(m['settle'] - t['settle']) / t['settle']
                 + abs(m['run'] - t['run'] * run_scale) / (t['run'] * run_scale))
        if best is None or score < best[0]:
            best = (score, s, m)
    return best[1], best[2]


def ini_section(name, t, s, m, run_scale):
    return ['', f'; {name}: target run {t["run"] * run_scale:g}, {t["swings"]} swing(s), settle {t["settle"]} s, '
                f'cap {t["cap"]}, tilt {t["tilt"]:g} deg; measured run {m["run"]:.2f}, {m["swings"]} swing(s), '
                f'settle {m["settle"]:.2f} s', f'[{name}]'] + [f'{key}={s[key]:g}' for key in sorted(s)]


def chain_run(sections, amplitude=2.0, hz=2.6, seconds=4.0):
    """A chain's tip (each bone carried by the pelvis bob plus its parents' offsets): worst tip offset after 1 s."""
    bs = [sim.Bone(s, [0.0, 0.0, 0.0], 0.6) for s in sections]
    worst = 0.0
    for f, carry in enumerate(sim.gait(amplitude, hz, seconds, FPS)):
        c = list(carry)
        for b in bs:
            b.update(c, [], 1000 / FPS)
            c = [c[i] + b.offset(c)[i] for i in range(3)]
        if f > FPS:
            worst = max(worst, max(abs(c[i] - carry[i]) for i in range(3)))
    return worst


def main(body='cbbe'):
    parts, collide = (PARTS_3BBB, COLLIDE_3BBB) if body == '3bbb' else (PARTS, COLLIDE)
    out, collision_out = (OUT_3BBB, COLLISION_OUT_3BBB) if body == '3bbb' else (OUT, COLLISION_OUT)
    naked, clothed = {}, {}
    for name, t in parts.items():
        naked[name] = (t,) + design(t)
        clothed[name] = (t,) + design(t, t['clothed'])
        for label, (_, s, m), scale in (('naked', naked[name], 1.0), ('clothed', clothed[name], t['clothed'])):
            print(f'{name:10} {label:7} k={s["stiffness"]:<4g} k2={s["stiffness2"]:<6g} d={s["damping"]:<4g} '
                  f'lin=({s["linearX"]:g}, {s["linearY"]:g}, {s["linearZ"]:g}) maxo={s["maxoffsetZ"]:<6g} '
                  f'tiltZ={s["rotationalZ"]:<7g}| run {m["run"]:.2f} (target {t["run"] * scale:.2f}), '
                  f'{m["swings"]} swing(s) (target {t["swings"]}), settle {m["settle"]:.2f} s (target {t["settle"]})')
    lines = ["; Anatomy's default physics preset (decision A-46): read by the Anatomy Engine ONLY when",
             '; Data\\F4SE\\Plugins\\ocbp.ini is missing. Install any physics preset and it replaces all of this.',
             '; GENERATED by tools/default_preset.py from targets - edit the targets there, not this.',
             '', '[General]', 'playerOnly=0', 'npcOnly=0', 'useWhitelist=0', 'femaleOnly=1', 'maleOnly=0',
             '; clothed (anything in the body slot): the [Attach.A] profile, calmer', 'detectArmor=1', 'armorIgnore=',
             '', '[Tuning]', 'rate=0', '', '[Attach]']
    lines += [f'{b}={name}' for name, (t, _, _) in naked.items() for b in t['bones']]
    lines += ['', '[Attach.A]']
    lines += [f'{b}={name}Clothed' for name, (t, _, _) in clothed.items() for b in t['bones']]
    for name, (t, s, m) in naked.items():
        lines += ini_section(name, t, s, m, 1.0)
    for name, (t, s, m) in clothed.items():
        lines += ini_section(f'{name}Clothed', t, s, m, t['clothed'])
    if body == '3bbb':
        tip = chain_run([naked[n][1] for n in CHAIN])
        lines.insert(3, f'; 3BBB body (A-57): the breast chain\'s tip runs {tip:.2f} in a jog (CBBE\'s one breast bone: '
                        f'{PARTS["Breasts"]["run"]:g})')
        print(f'breast chain tip in a jog: {tip:.2f} (CBBE breast target {PARTS["Breasts"]["run"]:g})')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\r\n')
    col = ["# Anatomy's default collision (decision A-46): read by the Anatomy Engine ONLY when",
           '# Data\\F4SE\\Plugins\\OCBPCollisionConfig.txt is missing. GENERATED by tools/default_preset.py.',
           '# Spheres measured on the Anatomy body: x,y,z from the bone in the actor\'s frame (A-57), radius.', '',
           '[AffectedNodes]']
    col += list(collide) + ['', '[ColliderNodes]'] + list(HANDS)
    for bone, (x, y, z, r) in collide.items():
        col += ['', f'[{bone}]', f'{x:g},{y:g},{z:g},{r:g}']
    for bone, r in HANDS.items():
        col += ['', f'[{bone}]', f'0,0,0,{r:g}']
    collision_out.write_text('\n'.join(col) + '\n', encoding='utf-8', newline='\r\n')
    print('wrote', out, 'and', collision_out)


if __name__ == '__main__':
    import sys
    main('3bbb' if '--3bbb' in sys.argv[1:] else 'cbbe')
