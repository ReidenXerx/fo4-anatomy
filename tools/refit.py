"""Outfit refits (roadmap 2, A-58), first target: every CBBE garment of the collection onto our 3BBB body.

The owner (2026-09-30): Ivy's collection moves to 3BBB, so all its clothes need refitting; build the refit pipeline
on that and polish it there. CBBE -> 3BBB is the simplest refit: 3BBB IS CBBE's mesh re-weighted (A-57: the same
vertices, triangles, UVs and slider data; only the feet moved), so an outfit keeps its shape and sliders and only its
weights change (the roadmap's reshape and slider steps are empty here).

The weights, per garment vertex (garments.py's A-36 machinery, generalised): what the body's weights did under it.
  - the change: our body's weights (Anatomy.nif, now 3BBB + the hip fold) minus CBBE's at the same skin vertex, over
    ALL bones; our run-time genital bones (Anat...) count as the pelvis they ride, so a garment never gets a lip or
    anus bone;
  - blended from the six nearest body vertices (inverse distance), fully within NEAR of the skin, fading out by FAR,
    so a loose hem or a coat keeps its author's weights;
  - added to the author's own weights, never across the midline (an L bone never on the right), the author's sum
    kept, four bones at most: a top that hugs the breast takes LBreast_01..03 as the skin under it did, a pocket
    stays where its author put it.
Everything else is garments.py's: the sets worn as a woman's model, a private BodySlide workspace, the headless
zero-preset --trimorphs build, verify (same vertices, same morphs), install in place with backups.

    python tools/refit.py plan  [--data <Data>]
    python tools/refit.py trial --only "<name part>" ...   # patch a few sets, measure them, no BodySlide
    python tools/refit.py build|regen|verify|install|all   # as garments.py
"""
import argparse
import collections
import math
import pathlib
import sys

import garments as g
import nif

NEAR, FAR = g.NEAR, g.FAR
CHANGED = 0.02               # a body vertex whose weights moved more than this (L1) is part of the change
AE_DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
WORK = pathlib.Path(r'D:\F4Output\AnatomyRefit3BBB')
GROUP = 'Anatomy Refit 3BBB'
THREE_BBB = {f'{s}{b}' for s in 'LR' for b in ('Breast_01_skin', 'Breast_02_skin', 'Breast_03_skin', 'Butt_01_skin',
                                               'Leg_Thigh_01_F_skin', 'Leg_Thigh_01_R_skin')}


def rides(bone):
    """The bone a garment may take for one of ours: our run-time genital nodes ride the pelvis."""
    return 'Pelvis_skin' if bone.startswith('Anat') else bone


def side_ok(bone, x):
    """Never hand a vertex the other side's bone (the hip fold's rule: L is x < 0)."""
    if x > 0.5 and bone[:1] == 'L' and bone[1:2].isupper():
        return False
    if x < -0.5 and bone[:1] == 'R' and bone[1:2].isupper():
        return False
    return True


class Change:
    """Our body against CBBE's: per skin vertex, how its weights changed (garments.Body's interface: band, bind,
    target(q))."""

    def __init__(self, bs):
        n = nif.Nif(bs / 'ShapeData/Anatomy/Anatomy.nif')
        s = n.shape('CBBE')
        bones, _ = n.skin(s)
        self.pos = s.positions()
        ours = []
        for i in range(s.count):
            w = collections.defaultdict(float)
            for sl, x in s.skin_weights(i):
                w[rides(bones[sl])] += x
            ours.append(dict(w))
        cb = nif.Nif(bs / 'ShapeData/CBBE/CBBEBodyPhysics.nif')
        cs = cb.shape('CBBE')
        cbones, _ = cb.skin(cs)
        cgrid = g.Grid(cs.positions())
        self.delta, self.band = [], set()
        for i, p in enumerate(self.pos):
            hit = cgrid.within(p, 0.2)                 # 3BBB moved only the feet, 0.16 at most
            if not hit:
                self.delta.append({})
                continue
            c = {cbones[sl]: x for sl, x in cs.skin_weights(hit[0][1])}
            d = {b: ours[i].get(b, 0.0) - c.get(b, 0.0) for b in set(ours[i]) | set(c)}
            d = {b: x for b, x in d.items() if abs(x) > 1e-4}
            self.delta.append(d)
            if sum(abs(x) for x in d.values()) > CHANGED:
                self.band.add(i)
        self.grid = g.Grid(self.pos)
        self.bind = _bind(n, s)

    def target(self, q):
        """(blend 0..1, {bone: change}) for a garment vertex at q, or None when the skin under it did not change."""
        hits = self.grid.within(q, FAR)
        if not hits or not any(i in self.band for _, i in hits[:6]):
            return None
        d0 = hits[0][0]
        f = 1.0 if d0 <= NEAR else (FAR - d0) / (FAR - NEAR)
        acc, tot = collections.defaultdict(float), 0.0
        for d, i in hits[:6]:
            k = 1.0 / max(d, 1e-3)
            tot += k
            for b, x in self.delta[i].items():
                acc[b] += k * x
        return f, {b: x / tot for b, x in acc.items()}


def _bind(n, s):
    """bone -> with_bones' definition, from the body's own skin (garments.Body's reader)."""
    out = {}
    o, _ = n.offsets[s.skin]
    c = nif.Cursor(n.b, o)
    c.take('i')
    data = c.take('i')
    refs = [c.take('i') for _ in range(c.take('I'))]
    o, _ = n.offsets[data]
    c = nif.Cursor(n.b, o)
    for k in range(c.take('I')):
        sphere = c.take('4f')
        rot9, t3, sc = c.take('9f'), c.take('3f'), c.take('f')
        node = n.nodes.get(refs[k])
        if node:
            out[node['name']] = dict(name=node['name'], node_rot=node['r'], node_t=node['t'], sphere=sphere,
                                     skin_rot=rot9, skin_t=t3, scale=sc)
    return out


def transfer(body, positions, weights):
    """{vertex: new weights} (shares summing to 1; patch_nif writes them at the author's sum). A shape its author
    already weighted to 3BBB's bones is left alone (adding the change again would double it)."""
    if any(b in THREE_BBB for w in weights for b in w):
        return {}
    wid = nif.weld(positions)
    first, out = {}, {}
    for i, (q, w) in enumerate(zip(positions, weights)):
        gi = wid[i]
        if gi in first:                                # welded copies take the same weights: no seam crack
            if first[gi] in out:
                out[i] = out[first[gi]]
            continue
        first[gi] = i
        own = sum(w.values())
        if own <= 0:
            continue
        t = body.target(q)
        if t is None:
            continue
        f, delta = t
        mixed = {b: x / own for b, x in w.items()}
        for b, x in delta.items():
            if side_ok(b, q[0]):
                mixed[b] = mixed.get(b, 0.0) + f * x
        mixed = {b: x for b, x in mixed.items() if x > 0.005}
        top = sorted(mixed.items(), key=lambda bx: -bx[1])[:g.MAX_BONES]
        s = sum(x for _, x in top)
        if s <= 0:
            continue
        new = {b: x / s for b, x in top}
        if g.l1(new, {b: x / own for b, x in w.items()}) < 0.01:
            continue
        out[i] = new
    return out


def check(positions, before, after):
    """The proof per shape, or stop: four or fewer weights summing to 1, no bone across the midline, welded copies
    equal (a seam never cracks)."""
    wid = nif.weld(positions)
    for i, w in after.items():
        if abs(sum(w.values()) - 1.0) > 1e-4 or len(w) > g.MAX_BONES:
            raise SystemExit(f'refit: vertex {i} weights {w} are not four or fewer summing to 1')
        bad = [b for b in w if not side_ok(b, positions[i][0]) and b not in before[i]]
        if bad:
            raise SystemExit(f'refit: vertex {i} at x {positions[i][0]:.2f} was given the other side\'s {bad}')
    seen = {}
    for i in after:
        if wid[i] in seen and after[i] != after[seen[wid[i]]]:
            raise SystemExit(f'refit: welded copies {seen[wid[i]]} and {i} differ: the seam would crack')
        seen.setdefault(wid[i], i)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('what', choices=('plan', 'trial', 'build', 'regen', 'verify', 'install', 'all'))
    ap.add_argument('--data', type=pathlib.Path, default=AE_DATA)
    ap.add_argument('--work', type=pathlib.Path, default=WORK)
    ap.add_argument('--target', type=pathlib.Path, default=WORK / 'built')
    ap.add_argument('--into', type=pathlib.Path, default=pathlib.Path(r'D:\Vortex\fallout4\mods\bodyslides_f4_sd'))
    ap.add_argument('--preset', default=g.PRESET)
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    bs = args.data / 'Tools/BodySlide'
    g.GROUP, g.WORK = GROUP, args.work
    if args.what == 'plan':
        targets, left = g.plan(bs, args.data)
        print(f'{len(targets)} CBBE garments worn as a woman\'s model')
        for reason, names in sorted(left.items(), key=lambda kv: -len(kv[1])):
            print(f'  left {len(names):4}: {reason}')
        return
    body = Change(bs)
    print(f'our body vs CBBE: {len(body.band)} skin vertices changed (3BBB + the hip fold)')
    home = args.work / 'BodySlide'
    if args.what in ('trial', 'build', 'all'):
        home, built = g.build(bs, args.data, args.work, args.target, args.only, body=body, xfer=transfer, chk=check)
        if args.what == 'trial':
            return
    if args.what in ('regen', 'all'):
        code, ok, errors = g.regen(home, args.target, args.preset)
        print(f"BodySlide exit {code}; {'all sets built' if ok else 'NOT all sets built'}; {len(errors)} error lines")
        for e in errors[:30]:
            print('   ', e)
        if not ok:
            sys.exit(1)
    if args.what in ('verify', 'all', 'install'):
        bad, checked, missing = g.verify(args.target, args.into, core_only=False)
        print(f'verify: {checked} rebuilt meshes against {args.into}: {len(bad)} bad, {len(missing)} not there')
        for b in bad[:40]:
            print('   BAD', b)
        if bad:
            sys.exit(1)
    if args.what == 'install':
        print(f'install: {g.install(args.target, args.into, args.work)} files written in place into {args.into}')


if __name__ == '__main__':
    main()
