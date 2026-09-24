"""The hip fold (A-30): soften CBBE's pelvis -> thigh handover, so the groin fold does not tear when her
legs go up or she sits.

The owner's look (2026-09-25, Photo177-178, "inner hip"): a fold and a fin on the inside of her hip in a
legs-up scene. Nothing was missing and nothing was pushed (every weighted bone is in the skeleton women
load; the thigh jiggle bones carry no vertex; ButtFat's swing stays under 1.6x). It is the skinning:
CBBE hands those vertices from Pelvis_skin to the thigh over a thin band, and with the leg up that band
stretches up to 11x (the original CBBE: 8x in the inner thigh alone; ours 5x). Averaging the CORE bones'
split with the neighbours across the band spreads the bend (measured, scratchpad crease_proto):

    pose                        worst edge    edges > 3x    p99
    legs up 100                 11.1 -> 4.2   128 -> 36     3.34 -> 2.66
    legs up and spread          10.6 -> 3.9    96 -> 19     3.10 -> 2.37
    sitting 90                  10.3 -> 3.9   107 -> 23     3.17 -> 2.52
    spread 45                    4.2 -> 1.8     3 -> 0      1.55 -> 1.31
    walking (35 forward)         3.5 -> 2.0     1 -> 0      1.59 -> 1.42

The owner's poll (2026-09-25): "I agree with recommendation", knowing the cost: a garment worn OVER the
naked body (panties, stockings, leg pieces) keeps CBBE's weights, so in deep bends the skin can move up to
3.8 off it at the hip (1.5 walking). Full outfits replace the body and are not affected.

Only the core bones' split moves (Pelvis_skin, Pelvis_Rear_skin, Spine1_skin, the thighs), and their
total on a vertex is kept: every other bone's weight (the genital layers, butt fat) stays as it was.
Positions are not touched, so compare_builds (the mesh and the morphs) is unaffected. It runs before the
genitals are split off, so the seam's copies carry the same weights on both shapes.

    python tools/hip_fold.py [--project <folder>]      # rewrites <project>/ShapeData/<ZeX folder> in place
"""
import argparse
import collections

import align_body as ab
import nif

CORE = ('Pelvis_skin', 'Pelvis_Rear_skin', 'Spine1_skin', 'LLeg_Thigh_skin', 'RLeg_Thigh_skin')
THIGHS = ('LLeg_Thigh_skin', 'RLeg_Thigh_skin')
ROUNDS, RING, BOTH = 20, 4, 0.05       # the band: thigh AND pelvis/spine both >= BOTH, grown RING rings
MAX_BONES = 4                          # a vertex in a built FO4 body carries four


def fit(share, slots):
    """A core split {bone: share} into at most `slots` bones. The torso bones (pelvis front and rear,
    spine) barely move against each other when a leg bends, so when slots run short their shares merge
    into the largest of them. The thigh keeps its share: dropping it is exactly the tear this pass
    exists to remove (measured: a perineum vertex that lost its thigh tore 7.2x). {} if nothing fits."""
    if slots <= 0:
        return {}
    if len(share) <= slots:
        return dict(share)
    thighs = sorted(((b, x) for b, x in share.items() if b in THIGHS), key=lambda t: (-t[1], t[0]))
    torso = sorted(((b, x) for b, x in share.items() if b not in THIGHS), key=lambda t: (-t[1], t[0]))
    body = sum(x for _, x in torso)
    if slots == 1:                           # one slot: the bigger of the two groups takes it all
        return {torso[0][0]: 1.0} if torso and body >= (thighs[0][1] if thighs else 0.0) else {thighs[0][0]: 1.0}
    out = dict(thighs[:slots - 1] if torso else thighs[:slots])
    if torso:
        out[torso[0][0]] = body
    s = sum(out.values())
    return {b: x / s for b, x in out.items()}


def soften(positions, triangles, weights, rounds=ROUNDS, ring=RING):
    """weights: [{bone: w}] per vertex -> the new list (the same object where nothing changed)."""
    wid = nif.weld(positions)
    groups = collections.defaultdict(list)
    for j, g in enumerate(wid):
        groups[g].append(j)
    nbr = collections.defaultdict(set)
    for t in triangles:
        for a in t:
            for b in t:
                if wid[a] != wid[b]:
                    nbr[wid[a]].add(wid[b])
    thighs, rest = set(THIGHS), set(CORE) - set(THIGHS)
    band = {wid[i] for i, w in enumerate(weights)
            if sum(w.get(b, 0.0) for b in thighs) >= BOTH and sum(w.get(b, 0.0) for b in rest) >= BOTH}
    for _ in range(ring):
        band |= {n for g in band for n in nbr[g]}
    total, share = {}, {}
    for g, js in groups.items():
        w = weights[js[0]]
        t = sum(w.get(b, 0.0) for b in CORE)
        total[g] = t
        share[g] = {b: w[b] / t for b in CORE if w.get(b, 0.0) > 0} if t > 0 else {}
    for _ in range(rounds):
        nxt = dict(share)
        for g in band:
            ns = [n for n in nbr[g] if total[n] > 0]
            if total[g] <= 0 or not ns:
                continue
            acc = collections.defaultdict(float)
            for n in ns:
                for b, x in share[n].items():
                    acc[b] += x / len(ns)
            mixed = {b: 0.5 * share[g].get(b, 0.0) + 0.5 * acc.get(b, 0.0) for b in set(share[g]) | set(acc)}
            s = sum(mixed.values())
            nxt[g] = {b: x / s for b, x in mixed.items() if x / s > 1e-3}
        share = nxt
    out = []
    for i, w in enumerate(weights):
        g = wid[i]
        if g not in band or total[g] <= 0:
            out.append(w)
            continue
        # the other bones keep their slots and weights exactly; the core bones share the slots left
        new = {b: x for b, x in w.items() if b not in CORE and x >= 0.005}   # a ~0 weight frees its slot
        core = fit(share[g], MAX_BONES - len(new))
        if not core:
            out.append(w)
            continue
        for b, x in core.items():
            new[b] = x * total[g]
        s = sum(new.values())
        out.append({b: x / s for b, x in new.items()})
    return out


def check(positions, before, after):
    """The stage's proof: or stop."""
    wid = nif.weld(positions)
    changed = sum(1 for a, b in zip(before, after) if a is not b)
    for i, w in enumerate(after):
        if w is before[i]:
            continue                                  # untouched: CBBE's own (half floats, 0.9996 sums)
        if abs(sum(w.values()) - 1.0) > 1e-4 or len(w) > MAX_BONES:
            raise SystemExit(f'hip fold: vertex {i} weights {w} are not four or fewer summing to 1')
        side = positions[i][0]
        if (side > 0.5 and w.get('LLeg_Thigh_skin', 0) > 0.01 and before[i].get('LLeg_Thigh_skin', 0) <= 0.01) or \
           (side < -0.5 and w.get('RLeg_Thigh_skin', 0) > 0.01 and before[i].get('RLeg_Thigh_skin', 0) <= 0.01):
            raise SystemExit(f'hip fold: vertex {i} at x {side:.2f} was given the other side\'s thigh')
        for b, x in before[i].items():
            if b not in CORE and x > 0.01 and abs(after[i].get(b, 0.0) - x) > 0.02 + 0.3 * x:
                raise SystemExit(f'hip fold: vertex {i} lost its {b} weight ({x:.3f} -> {after[i].get(b, 0.0):.3f})')
    first = {}
    touched = {wid[i] for i in range(len(after)) if after[i] is not before[i]}
    for i, g in enumerate(wid):              # only copies we wrote: CBBE has one toe pair 1e-4 apart
        if g in touched and g in first and after[i] != after[first[g]]:
            raise SystemExit(f'hip fold: welded copies {first[g]} and {i} differ: the seam would crack')
        first.setdefault(g, i)
    return changed


def apply(nif_path, shape_name=ab.SHAPE):
    body = nif.Nif(nif_path)
    shape = body.shape(shape_name)
    bones, _ = body.skin(shape)
    slot = {b: k for k, b in enumerate(bones)}
    missing = [b for b in CORE if b not in slot]
    if missing:
        raise SystemExit(f'hip fold: the body is not weighted to {missing}')
    pos = shape.positions()
    before = [{bones[sl]: w for sl, w in shape.skin_weights(i) if w > 0} for i in range(shape.count)]
    after = soften(pos, shape.triangles(), before)
    changed = check(pos, before, after)
    for i, (a, b) in enumerate(zip(before, after)):
        if a is not b:
            shape.set_skin_weights(i, [(slot[n], w) for n, w in b.items()])
    body.save(nif_path)
    print(f'3b. hip fold: the pelvis -> thigh split softened on {changed} vertices ({ROUNDS} rounds, {RING} rings)')
    return changed


def main():
    import zex_bones as zb
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--project', default=str(ab.OUT))
    args = ap.parse_args([] if __name__ != '__main__' else None)
    import pathlib
    apply(pathlib.Path(args.project) / 'ShapeData' / zb.OUT_FOLDER / f'{zb.OUT_FOLDER}.nif')


if __name__ == '__main__':
    main()
