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


MIN_BA2 = 100               # a BA2 mesh the refit changes on fewer vertices is rigid gear grazing the chest (a helmet's hem)
NOT_OUTFIT = ('actors\\', 'supermutant', 'feralghoul', 'mannequin')


def ba2(bs, data, out):
    """Outfits whose game mesh loads from a BA2 and that no BodySlide set rebuilds (the owner, 2026-09-30): the built
    mesh itself is refitted (same transfer) and written loose under `out` (a loose file wins over any archive), its
    .tri copied unchanged (the vertices do not move). Skipped: meshes the refit barely touches (MIN_BA2), bodies and
    creatures, and outfits made for the vanilla body (a quarter of their skin-side vertices 0.3 inside CBBE's skin:
    the vanilla -> CBBE refit's job). Returns [(model, archive, changed vertices)]."""
    import gamedata
    import tempfile
    game = gamedata.Game(data)
    body = Change(bs)
    bpos = body.pos
    bn = nif.Nif(bs / 'ShapeData/Anatomy/Anatomy.nif').shape('CBBE')
    acc = [[0.0, 0.0, 0.0] for _ in bpos]
    for a, b, c in bn.triangles():
        u = [bpos[b][k] - bpos[a][k] for k in range(3)]
        v = [bpos[c][k] - bpos[a][k] for k in range(3)]
        nrm = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        for x in (a, b, c):
            for k in range(3):
                acc[x][k] += nrm[k]
    normal = [[x / (math.sqrt(sum(y * y for y in v)) or 1.0) for x in v] for v in acc]
    by_sets = {g.output_of(s) for _, s in g.slider_sets(bs)}
    tmp = pathlib.Path(tempfile.mkdtemp())
    done = []
    for model in sorted(g.worn_female(data)):
        rel = 'Meshes/' + model.replace('\\', '/') + '.nif'
        where = game.find(rel)
        if where is None or where[0] != 'archive' or model in by_sets:
            continue
        if any(k in model for k in NOT_OUTFIT) or model.split('\\')[-1].endswith('body'):
            continue
        src = tmp / 'in.nif'
        try:
            src.write_bytes(game.read(rel))
            n = nif.Nif(src)
        except Exception:
            continue
        changed = near = inside = 0
        for s in n.shapes():
            bones, _ = n.skin(s)
            if not bones or not g.identity(n, s):
                continue
            pos = s.positions()
            w = [{bones[sl]: x for sl, x in s.skin_weights(i)} for i in range(s.count)]
            changed += len(transfer(body, pos, w))
            for q in pos:
                h = body.grid.within(q, 1.5)
                if h and h[0][1] in body.band:
                    near += 1
                    j = h[0][1]
                    if sum((q[k] - bpos[j][k]) * normal[j][k] for k in range(3)) < -0.3:
                        inside += 1
        if changed < MIN_BA2 or (near and inside / near > 0.25):
            continue
        dst = out / rel
        report = g.patch_nif(body, src, dst, transfer, check)
        tri = rel[:-4] + '.tri'
        if game.find(tri) is not None:
            (out / tri).write_bytes(game.read(tri))
        a, b = nif.Nif(src), nif.Nif(dst)                  # the proof: the same vertices, only weights changed
        for sa, sb in zip(a.shapes(), b.shapes()):
            if sa.positions() != sb.positions():
                raise SystemExit(f'refit ba2: {rel}/{sa.name} moved its vertices')
        done.append((model, pathlib.Path(where[1]).name, sum(v for v in report.values() if isinstance(v, int))))
    return done


_W = {}


def _init_worker(bs):
    import os
    for v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[v] = '1'                           # one BLAS thread per worker: the pool already fills the cores
    import conform
    import tempfile
    g.WORK = pathlib.Path(tempfile.mkdtemp(prefix='refit-'))     # garments.reparse's scratch file, one per process
    _W['body'], _W['change'] = conform.Body(bs), Change(bs)


def _project(job):
    import conform
    model, src, home = job
    name = 'Anatomy3BBB ' + model.replace('\\', ' ').replace('/', ' ')[-60:]
    try:
        return conform.make_project(_W['body'], _W['change'], pathlib.Path(src), model, pathlib.Path(home), name)
    except SystemExit as e:
        return dict(model=model, skipped=str(e))


def projects(bs, work, jobs, workers=11):
    """A BodySlide project per outfit mesh (conform.py, A-59), in parallel (one process per core but one; each loads
    the body once). jobs: [(model, source .nif)]. Returns (home, reports)."""
    import multiprocessing as mp
    home = g.workspace(bs, work, work / 'built')
    with mp.Pool(workers, initializer=_init_worker, initargs=(bs,)) as pool:
        reports = list(pool.imap_unordered(_project, [(m, str(s), str(home)) for m, s in jobs]))
    import xml.etree.ElementTree as ET
    root = ET.Element('SliderGroups')
    grp = ET.SubElement(root, 'Group', name=GROUP)
    for r in sorted(reports, key=lambda r: r.get('set', '')):
        if 'set' in r:
            ET.SubElement(grp, 'Member', name=r['set'])
    ET.indent(root)
    ET.ElementTree(root).write(home / 'SliderGroups' / f'{GROUP}.xml', encoding='UTF-8', xml_declaration=True)
    return home, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('what', choices=('plan', 'trial', 'build', 'regen', 'verify', 'install', 'all', 'ba2', 'projects'))
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
    if args.what == 'projects':
        # the BA2-only outfits `ba2` selected (their refitted meshes carry the original positions): each becomes a
        # BodySlide project, then BodySlide builds the group at --preset
        import gamedata
        game = gamedata.Game(args.data)
        work = args.work / 'projects'
        src_dir = work / 'src'
        src_dir.mkdir(parents=True, exist_ok=True)
        jobs = []
        for p in sorted((args.work / 'ba2').rglob('*.nif')):
            rel = p.relative_to(args.work / 'ba2').as_posix()
            model = rel[len('Meshes/'):-4].replace('/', '\\').lower()
            src = src_dir / (model.replace('\\', '_') + '.nif')
            src.write_bytes(game.read(rel))                 # the ORIGINAL mesh, straight from its archive
            jobs.append((model, src))
        home, reports = projects(bs, work, jobs)
        made = [r for r in reports if 'set' in r]
        print(f'{len(made)} projects, {len(reports) - len(made)} skipped:',
              [(r['model'], r.get('skipped')) for r in reports if 'set' not in r][:10])
        print('presets detected:', collections.Counter(r['preset'] for r in made).most_common())
        code, ok, errors = g.regen(home, work / 'built', args.preset)
        print(f"BodySlide exit {code}; {'all sets built' if ok else 'NOT all sets built'}; {len(errors)} error lines")
        for e in errors[:20]:
            print('   ', e)
        return
    if args.what == 'ba2':
        out = args.work / 'ba2'
        done = ba2(bs, args.data, out)
        print(f'{len(done)} BA2-only outfits refitted into {out}')
        for model, arch, n in done:
            print(f'  {n:6}  {arch:40}  {model}')
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
