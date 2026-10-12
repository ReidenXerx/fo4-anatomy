# SPDX-License-Identifier: GPL-3.0-only
"""How far the breasts lag behind while the actor RUNS (sdp_phoenix via Watcher, 2026-10-12: 3BBB breasts sink
into the chest while running, round again when she stops).

OCBPC's spring runs in world space and its damping acts on the bone's ABSOLUTE velocity, so an actor moving at a
steady speed V needs a steady spring stretch to keep the bone moving: diff ~ V * damping / stiffness, pointing back.
default_preset.py tuned every part on a pelvis bobbing IN PLACE, so this lag was never measured. Here the pelvis
also travels forward (+y) at walk / run / sprint speeds; printed: the chain tip's steady offset along y (negative =
pulled back into the chest) after 2 s, and the bob's swing on top.

    python studies/breast_run_lag.py [preset.ini]
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'tools'))
import ocbpc_sim as sim  # noqa: E402

FPS = 60
PRESET = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path(__file__).resolve().parent.parent / 'build/config/Anatomy/ocbp-default-3bbb.ini'
CHAINS = {'breasts (3BBB 01-02-03)': ['Breast1', 'Breast2', 'Breast3'], 'butt (3BBB)': ['Butt3B']}
SPEEDS = {'walk': 120.0, 'run': 330.0, 'sprint': 500.0}      # game units per second


def section(name):
    s = sim.preset_section(name, PRESET)
    s.setdefault('timetick', s.get('timeTick', 4.0))
    s.setdefault('gravityBias', 0.0)
    s.setdefault('gravityCorrection', 0.0)
    return s


def run(names, speed, seconds=4.0, bob=2.0, hz=2.6):
    bs = [sim.Bone(section(n), [0.0, 0.0, 0.0], 0.6) for n in names]
    ys = []
    for f in range(int(seconds * FPS)):
        t = f / FPS
        carry = [0.0, speed * t, bob * math.sin(2 * math.pi * hz * t)]
        c = list(carry)
        for b in bs:
            b.update(c, [], 1000 / FPS)
            c = [c[i] + b.offset(c)[i] for i in range(3)]
        if t > 2.0:
            ys.append(c[1] - carry[1])
    return sum(ys) / len(ys), max(ys) - min(ys)


if __name__ == '__main__':
    print(f'preset: {PRESET}')
    for tau in (0.0, sim.RELATIVE_TAU):
        sim.RELATIVE_TAU = tau
        print(f'followTravel {tau}' + (' (before 1.2.20)' if tau == 0 else ' (1.2.20)'))
        for label, names in CHAINS.items():
            for sp, v in SPEEDS.items():
                mean, swing = run(names, v)
                print(f'  {label:24s} {sp:6s} {v:5.0f} u/s: tip y {mean:+6.2f} units (swing {swing:.2f})')
