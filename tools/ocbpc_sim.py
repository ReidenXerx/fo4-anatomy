# SPDX-License-Identifier: GPL-3.0-only
# A Python port of OCBPC's per-bone update (Thing::UpdateThing) and sphere collision
# (Collision::IsItColliding), from github.com/ericncream/OpenCBP_FO4 branch cbpc @ 46cfb20
# (GPL-3.0). This file is a derivative of that code and carries its license; it is a local
# analysis tool and never ships with the body (decision A-2 covers the body and configs).
"""Offline OCBPC: what a [section] of ocbp.ini does to one bone, measured before the game.

Faithful to the source, including the parts that look like bugs, because the game runs them:
  - a bone's local transform is SET each frame: first-seen local + physics offset (an animation
    of the same bone is discarded; Thing.cpp:640-662);
  - the push of an overlapping collider sphere is (L - d) along collider -> bone, summed over
    every overlapping pair, from positions at the START of the frame (the loop that should move
    the spheres by the running push edits a copy: Thing.cpp:352-358);
  - a push is divided by linear and scaled by timeTick/deltaT, then relaxed into the internal
    offset; the bone's actual offset is internal * linear, so linear does not weaken a push but
    maxoffset caps the INTERNAL offset (actual cap = maxoffset * linear);
  - the second ("maybe") check predicts the post-spring position with the internal step, not the
    scaled one (Thing.cpp:486), and one collider sharing k grid cells with the bone pushes k times.

Everything is in the actor's frame (x left-/right+, y front, z up), which is what the offsets and
linear axes are in (the skeleton root's rotation).

    python tools/ocbpc_sim.py            # the scenario table for the current physics_config values
"""
import math

import physics_config as pc
import physics_design as pd


def v_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def v_sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def v_mul(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def sgn(v):
    return (v > 0) - (v < 0)


class Bone:
    """One simulated bone. `rest` is its world position at rest; the parent moves it by `carry`."""

    def __init__(self, section, rest, radius, dup=1):
        s = section
        self.k1, self.k2, self.damp = s['stiffness'], s['stiffness2'], s['damping']
        self.lin = [s['linearX'], s['linearY'], s['linearZ']]
        self.maxo = [s['maxoffsetX'], s['maxoffsetY'], s['maxoffsetZ']]
        self.tick = max(1.0, s['timetick'])
        self.step = s.get('timeStep', 0.016)
        self.gbias, self.gcorr = s['gravityBias'], s['gravityCorrection']
        self.rest, self.radius, self.dup = list(rest), radius, dup
        self.old = list(rest)            # oldWorldPos (internal)
        self.vel = [0.0, 0.0, 0.0]
        self.act_off = [0.0, 0.0, 0.0]   # last frame's local offset (internal * linear), kept by the bone
        self.actual = list(rest)         # the bone's world position the game shows

    def _push(self, at, colliders):
        push, hit = [0.0, 0.0, 0.0], False
        for c, r in colliders:
            lim = r + self.radius
            d2 = sum((at[i] - c[i]) ** 2 for i in range(3))
            if d2 < lim * lim:
                hit = True
                d = math.sqrt(d2) or 1e-6
                push = v_add(push, v_mul(v_sub(at, c), (lim - d) / d * self.dup))
        return hit, push

    def update(self, carry, colliders, delta_ms):
        """carry: the parent's displacement this frame (the bone's target = rest + carry)."""
        dt = clamp(int(delta_ms), 8, 64)
        mult = self.tick / dt
        target = v_add(self.rest, carry)
        # the parent has moved since last frame; the bone keeps last frame's local offset
        self.actual = v_add(target, self.act_off)
        hit, cv = self._push(self.actual, colliders)
        if hit:
            cv = [clamp(cv[i] / self.lin[i] * mult, -self.maxo[i], self.maxo[i]) for i in range(3)]
            self.vel = v_mul(cv, self.step)
            new = v_add(self.old, cv)
        else:
            diff = v_sub(target, self.old)
            diff[2] += self.gcorr
            if max(abs(x) for x in diff) > 100:
                self.old, self.vel = list(target), [0.0, 0.0, 0.0]
                self.act_off, self.actual = [0.0, 0.0, 0.0], list(target)
                return
            diff = v_mul(diff, mult)
            force = [diff[i] * self.k1 + diff[i] * diff[i] * sgn(diff[i]) * self.k2 for i in range(3)]
            force[2] -= self.gbias
            pos_delta = [0.0, 0.0, 0.0]
            t = dt
            while True:
                self.vel = [self.vel[i] + force[i] * self.step - self.vel[i] * self.damp * self.step for i in range(3)]
                pos_delta = v_add(pos_delta, v_mul(self.vel, self.step))
                t -= self.tick
                if t < self.tick:
                    break
            maybe = v_add(self.old, pos_delta)
            hit2, cv2 = self._push(v_add(self.actual, pos_delta), colliders)
            if hit2:
                cv2 = [clamp(cv2[i] / self.lin[i] * mult, -self.maxo[i], self.maxo[i]) for i in range(3)]
                self.vel = v_mul(cv2, self.step)
                new = v_add(maybe, cv2)
            else:
                new = maybe
        diff = v_sub(new, target)
        diff = [clamp(diff[0], -self.maxo[0], self.maxo[0]), clamp(diff[1], -self.maxo[1], self.maxo[1]),
                clamp(diff[2] - self.gcorr, -self.maxo[2], self.maxo[2]) + self.gcorr]
        self.old = v_add(target, diff)
        self.act_off = [diff[i] * self.lin[i] for i in range(3)]
        self.actual = v_add(target, self.act_off)

    def offset(self, carry):
        return v_sub(self.actual, v_add(self.rest, carry))


class ContactBone(Bone):
    """The engine's A-55 contact (fo4-ocbpc Thing.cpp, a body bone not named Anat...): the spring always runs, then the
    bone is projected out of every collider where it would be SHOWN (the push turned back into internal units by
    1/linear), only the velocity INTO the collider removed, and tangential velocity decaying at FRICTION per second."""
    FRICTION = 8.0

    def update(self, carry, colliders, delta_ms):
        dt = clamp(int(delta_ms), 8, 64)
        mult = self.tick / dt
        target = v_add(self.rest, carry)
        diff = v_sub(target, self.old)
        diff[2] += self.gcorr
        if max(abs(x) for x in diff) > 100:
            self.old, self.vel = list(target), [0.0, 0.0, 0.0]
            self.act_off, self.actual = [0.0, 0.0, 0.0], list(target)
            return
        diff = v_mul(diff, mult)
        force = [diff[i] * self.k1 + diff[i] * diff[i] * sgn(diff[i]) * self.k2 for i in range(3)]
        force[2] -= self.gbias
        pos_delta = [0.0, 0.0, 0.0]
        t = dt
        while True:
            self.vel = [self.vel[i] + force[i] * self.step - self.vel[i] * self.damp * self.step for i in range(3)]
            pos_delta = v_add(pos_delta, v_mul(self.vel, self.step))
            t -= self.tick
            if t < self.tick:
                break
        new = v_add(self.old, pos_delta)
        shown = [target[i] + (new[i] - target[i]) * self.lin[i] for i in range(3)]
        push = [0.0, 0.0, 0.0]
        for _ in range(4):
            hit, p = self._push(v_add(shown, push), colliders)
            if not hit:
                break
            push = v_add(push, p)
        if any(abs(x) > 1e-9 for x in push):
            internal = [push[i] / self.lin[i] if self.lin[i] > 1e-4 else 0.0 for i in range(3)]
            new = v_add(new, internal)
            ln = math.sqrt(sum(x * x for x in internal))
            if ln > 1e-6:
                n = [x / ln for x in internal]
                vn = sum(self.vel[i] * n[i] for i in range(3))
                if vn < 0:
                    self.vel = [self.vel[i] - vn * n[i] for i in range(3)]
                    vn = 0.0
                keep = math.exp(-self.FRICTION * dt / 1000)
                self.vel = [vn * n[i] + (self.vel[i] - vn * n[i]) * keep for i in range(3)]
        diff = v_sub(new, target)
        diff = [clamp(diff[0], -self.maxo[0], self.maxo[0]), clamp(diff[1], -self.maxo[1], self.maxo[1]),
                clamp(diff[2] - self.gcorr, -self.maxo[2], self.maxo[2]) + self.gcorr]
        self.old = v_add(target, diff)
        self.act_off = [diff[i] * self.lin[i] for i in range(3)]
        self.actual = v_add(target, self.act_off)


# --------------------------------------------------------------------------
# scenarios
# --------------------------------------------------------------------------

def gait(amplitude, hz, seconds, fps):
    """The pelvis bobbing up and down (and swaying forward half as much) at `hz`."""
    frames = int(seconds * fps)
    return [[0.0, 0.5 * amplitude * math.sin(2 * math.pi * hz * f / fps + 1.0),
             amplitude * math.sin(2 * math.pi * hz * f / fps)] for f in range(frames)]


def shaft(entry, axis, depth, radii, spacing):
    """Collider spheres along a shaft whose tip is `depth` units past `entry` along `axis`."""
    return [(v_add(entry, v_mul(axis, depth - i * spacing)), r) for i, r in enumerate(reversed(radii))]


def run_gait(section, amplitude, hz, fps=60, seconds=4.0):
    b = Bone(section, [0.0, 0.0, 0.0], 0.6)
    worst = 0.0
    for f, carry in enumerate(gait(amplitude, hz, seconds, fps)):
        b.update(carry, [], 1000 / fps)
        if f > fps:                      # after the first second
            worst = max(worst, max(abs(x) for x in b.offset(carry)))
    return worst


def run_insert(section, bone_rest, entry, axis, radii, spacing, affected_r, fps=60, dup=1,
               insert_s=1.0, hold_s=1.0, thrust_s=3.0, thrust_amp=2.5, thrust_hz=1.2, depth=5.0):
    """Shaft slides in along `axis` to `depth`, holds, thrusts, withdraws. Returns the bone's lateral
    push during hold, its min/max during thrusts, and the frames it took to reach 90% of the hold."""
    b = Bone(section, bone_rest, affected_r, dup)
    total = insert_s + hold_s + thrust_s + insert_s
    hold, thrust, settle, peak, hold_vec = [], [], None, 0.0, None
    far = -spacing * len(radii) - 4
    for f in range(int(total * fps)):
        t = f / fps
        if t < insert_s:
            d = far + (depth - far) * t / insert_s
        elif t < insert_s + hold_s:
            d = depth
        elif t < insert_s + hold_s + thrust_s:
            d = depth - thrust_amp * (1 - math.cos(2 * math.pi * thrust_hz * (t - insert_s - hold_s))) / 2
        else:
            d = depth - (depth - far) * (t - insert_s - hold_s - thrust_s) / insert_s
        b.update([0.0, 0.0, 0.0], shaft(entry, axis, d, radii, spacing), 1000 / fps)
        off = b.offset([0.0, 0.0, 0.0])
        mag = math.sqrt(sum(x * x for x in off))
        peak = max(peak, mag)
        if insert_s <= t < insert_s + hold_s:
            hold.append(mag)
            hold_vec = off
        elif insert_s + hold_s <= t < insert_s + hold_s + thrust_s:
            thrust.append(mag)
    steady = hold[-1]
    settle = next((i for i, m in enumerate(hold) if m >= 0.9 * steady), None)
    late = hold[len(hold) // 2:]
    # frame-to-frame change while nothing moves: anything above ~0.02 reads as a vibrating lip
    jitter = max(abs(a - b) for a, b in zip(late, late[1:])) if len(late) > 1 else 0.0
    after = b.offset([0.0, 0.0, 0.0])
    return dict(hold=steady, hold_vec=hold_vec, hold_min=min(late), hold_max=max(late), jitter=jitter, settle_frames=settle,
                thrust_min=min(thrust), thrust_max=max(thrust), peak=peak, after=math.sqrt(sum(x * x for x in after)))


def run_squeeze(cls, section, bone_r, kind='steady', fps=60, hand_r=2.5, press=1.0, seconds=5.0):
    """A hand sphere pressed into a body bone's sphere (roadmap 2): 'steady' (in over 1 s, held), 'knead' (+-0.5 at
    1 Hz), 'grab' (in over 0.1 s). Returns (twitch, sink): twitch = the worst frame-to-frame change of the bone's shown
    offset while the hand holds still (steady/grab, after 2 s), sink = how deep the hand ends up inside the flesh."""
    b = cls(section, [0.0, 0.0, 0.0], bone_r)
    lim = bone_r + hand_r
    shown, sink = [], 0.0
    for f in range(int(seconds * fps)):
        t = f / fps
        if kind == 'knead':
            depth = min(1.0, t) * (press + 0.5 * math.sin(2 * math.pi * t))
        elif kind == 'grab':
            depth = press * min(1.0, max(0.0, (t - 1.0) / 0.1))
        else:
            depth = press * min(1.0, t)
        hand = [0.0, lim - depth, 0.0]
        b.update([0.0, 0.0, 0.0], [(hand, hand_r)], 1000 / fps)
        shown.append(list(b.actual))
        if t > 1.5:
            sink = max(sink, lim - math.dist(b.actual, hand))
    hold = shown[int(2.0 * fps):]
    twitch = max(math.dist(a, c) for a, c in zip(hold, hold[1:]))
    return twitch, sink


def preset_section(name, path=None):
    """One [section] of our built physics preset (build/config/Anatomy/ocbp-default.ini) as {key: float}."""
    import pathlib
    import re
    path = path or pathlib.Path(__file__).resolve().parent.parent / 'build/config/Anatomy/ocbp-default.ini'
    text = pathlib.Path(path).read_text(encoding='utf-8')
    m = re.search(r'^\[' + re.escape(name) + r'\]\s*$(.*?)(?=^\[|\Z)', text, re.M | re.S)
    out = {}
    for line in m.group(1).splitlines():
        if '=' in line and not line.lstrip().startswith(';'):
            k, v = line.split('=', 1)
            out[k.strip()] = float(v)
    return out


def contact_distance(bone_rest, entry, axis, radii, spacing, affected_r, depth=5.0):
    """Where the bone must end up geometrically: out of every sphere at full depth."""
    spheres = shaft(entry, axis, depth, radii, spacing)
    # push straight away from the shaft axis until clear of all spheres
    rel = v_sub(bone_rest, entry)
    along = sum(rel[i] * axis[i] for i in range(3))
    radial = v_sub(rel, v_mul(axis, along))
    rn = math.sqrt(sum(x * x for x in radial)) or 1e-6
    out = v_mul(radial, 1 / rn)
    h = rn
    while any(math.dist(v_add(v_add(entry, v_mul(axis, along)), v_mul(out, h)), c) < r + affected_r
              for c, r in spheres):
        h += 0.005
    return h - rn


def main():
    labia, anus = pc.SECTIONS['Labia'], pc.SECTIONS['Anus']
    print('gait (worst bone offset after 1 s, units): walk 1.5u @ 2 Hz, run 3u @ 3 Hz')
    for name, sec in (('Labia', labia), ('Anus', anus)):
        print(f'  [{name}] walk {run_gait(sec, 1.5, 2.0):.2f}  run {run_gait(sec, 3.0, 3.0):.2f}')
    radii = [pc.COLLIDERS[n][0][3] for n in ('Penis_01', 'Penis_02', 'Penis_03', 'Penis_04', 'Penis_05')]
    paths = {'along the canal': ([0.0, 0.5, -55.9], [0.0, 0.48, 0.88]),
             'canal, 1 behind': ([0.0, -0.5, -55.9], [0.0, 0.48, 0.88]),
             'canal, 1 ahead': ([0.0, 1.5, -55.9], [0.0, 0.48, 0.88]),
             'straight up': ([0.0, 0.5, -55.9], [0.0, 0.0, 1.0]),
             'flatter': ([0.0, 0.5, -55.9], [0.0, 0.8, 0.6]),
             '0.4 to her right': ([0.4, 0.5, -55.9], [0.0, 0.48, 0.88])}
    for bone, rest in (('AnatLip_L', pd.REST['AnatLip_L']), ('AnatLip_R', pd.REST['AnatLip_R'])):
        ox, oy, oz, ra = pc.AFFECTED[bone][0]
        sphere = [rest[0] + ox, rest[1] + oy, rest[2] + oz]
        print(f'insert, {bone} (sphere at x {sphere[0]:+.2f}, r {ra}):')
        for name, (entry, axis) in paths.items():
            r = run_insert(labia, sphere, entry, axis, radii, 3.0, ra)
            print(f'  {name:17} hold {r["hold"]:.2f} (90% after {r["settle_frames"]} frames); thrusts '
                  f'{r["thrust_min"]:.2f}..{r["thrust_max"]:.2f}; peak {r["peak"]:.2f}; after withdrawal {r["after"]:.2f}')
    ring = {b: pd.REST[b] for b in ('AnatAnus_F', 'AnatAnus_B', 'AnatAnus_L', 'AnatAnus_R')}
    axis = [0.0, 0.45 / math.hypot(0.45, 0.89), 0.89 / math.hypot(0.45, 0.89)]
    for shift in (0.0, 0.3):
        entry = [0.0, -2.76 - shift, -54.4]
        entry = [entry[i] - axis[i] * 1.5 for i in range(3)]
        print(f'anal insert, shaft {shift:.1f} behind the ring centre:')
        for bone, rest in ring.items():
            ox, oy, oz, ra = pc.AFFECTED[bone][0]
            sphere = [rest[0] + ox, rest[1] + oy, rest[2] + oz]
            r = run_insert(anus, sphere, entry, axis, radii, 3.0, ra)
            print(f'  {bone}: hold {r["hold"]:.2f}; thrusts {r["thrust_min"]:.2f}..{r["thrust_max"]:.2f}; '
                  f'peak {r["peak"]:.2f}; after {r["after"]:.2f}')


    print('squeeze (roadmap 2, A-55): a hand (r 2.5) pressed 1.0 into a body bone; twitch / sink, OCBPC -> contact')
    presets = {'Breasts': (preset_section('Breasts'), 2.5), 'Butt': (preset_section('Butt'), 4.2)}
    for name, (sec, r) in presets.items():
        for kind in ('steady', 'grab', 'knead'):
            for fps in (30, 60, 144):
                a = run_squeeze(Bone, sec, r, kind, fps)
                c = run_squeeze(ContactBone, sec, r, kind, fps)
                print(f'  [{name}] {kind:6} {fps:3} fps  twitch {a[0]:.3f} -> {c[0]:.3f}  sink {a[1]:.2f} -> {c[1]:.2f}')


if __name__ == '__main__':
    main()
