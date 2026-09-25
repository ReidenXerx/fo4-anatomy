"""Anatomy Rebuild: your BodySlide builds get the two fixes BodySlide cannot carry (A-36, A-37).

    AnatomyRebuild.exe                      (from Data/Tools/AnatomyRebuild; MO2: run it from MO2)
    AnatomyRebuild.exe --data <Data> [--built <folder>] [--only garments|neck] [--undo]

Run it after BodySlide, every time you build (BodySlide writes its meshes whole, and each build
takes these fixes away again). It changes nothing but these, in meshes you already built:

  - Outfits (A-36): every CBBE outfit a woman wears in your game gets the body's hip handover. The
    Anatomy body's hip fold (A-30) softened CBBE's pelvis -> thigh skinning so her groin no longer
    tears in legs-up poses; an outfit still carries CBBE's old skinning and parts from the skin there,
    up to 3.8 units. Only the pelvis/spine/thigh SPLIT of vertices near the body's fold moves.
  - The neck (A-37): the body's neck ring is turned to face the way the head (and CBBE HeadRear
    Absolute Fix's rear piece) faces, so the join does not show as a line in the light.

How it stays safe:
  - It never runs BodySlide and never changes a vertex's position, a morph (.tri) or a slider: your
    preset, zaps and LooksMenu BodyGen morphs stay exactly as BodySlide built them. It computes the new
    skinning on the outfit's own BodySlide source (the unmorphed shape the body fix was made on), then
    writes it onto your built mesh vertex by vertex, only after proving that the two are the same
    mesh: every shape the same name, vertex count, UVs and non-hip weights. A mesh built with a zap
    slider (vertices removed) or from another source is left as it is, and the log says so.
  - It reads the rest as the game loads it (loose files, then archives), writes only meshes BodySlide
    built, in place (a Vortex hardlink stays a hardlink), and keeps every original in backup/ first.
  - --undo puts back every file it changed that BodySlide has not rebuilt since.
It refuses to run while Fallout 4 is running.
"""
import argparse
import hashlib
import io
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import traceback

FROZEN = getattr(sys, 'frozen', False)
HERE = pathlib.Path(sys.executable).parent if FROZEN else pathlib.Path(__file__).resolve().parent
if not FROZEN:
    sys.path.insert(0, str(HERE))

BODY = 'actors\\character\\characterassets\\femalebody'
TOL_UV = 2e-3                 # halves: the same UV reads back the same
TOL_W = 0.02                  # a non-hip weight share may differ by rounding, not by authorship


class Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()
        return len(s)


def find_data(arg):
    data = pathlib.Path(arg) if arg else HERE.parent.parent            # Data/Tools/AnatomyRebuild
    if not (data / 'Fallout4.esm').exists():
        raise SystemExit(f'{data} is not Fallout 4\'s Data folder. Put this tool in Data/Tools/AnatomyRebuild '
                         f'(the download does), or run it with --data "<your Fallout 4>/Data".')
    return data


def built_root(data, bs, arg):
    """Where BodySlide writes: --built, else its Config.xml OutputDataPath, else Data."""
    if arg:
        return pathlib.Path(arg)
    cfg = bs / 'Config.xml'
    if cfg.exists():
        m = re.search(r'<OutputDataPath>([^<]*)</OutputDataPath>', cfg.read_text(encoding='utf-8-sig', errors='replace'))
        if m and m.group(1).strip():
            p = pathlib.Path(m.group(1).strip())
            if p.exists():
                return p
    return data


def sha(blob):
    return hashlib.sha1(blob).hexdigest()


def running():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Fallout4.exe'], capture_output=True, text=True).stdout
    except OSError:
        return False
    return 'fallout4.exe' in out.lower()


# ---- the ledger: what we wrote, so --undo never undoes a newer BodySlide build ----
class Ledger:
    def __init__(self, home):
        self.home = home
        self.path = home / 'backup' / 'ledger.json'
        self.rows = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}

    def write(self, dest, new):
        """Put `new` into dest in place, the original kept first. Returns False if dest already holds it."""
        old = dest.read_bytes()
        if old == new:
            return False
        key = str(dest)
        keep = self.home / 'backup' / 'files' / sha(key.lower().encode())[:16]
        row = self.rows.get(key)
        if not row or row.get('wrote') != sha(old):     # a fresh BodySlide build: it is the original now
            keep.parent.mkdir(parents=True, exist_ok=True)
            keep.write_bytes(old)
            row = {'backup': str(keep), 'original': sha(old)}
        with open(dest, 'r+b') as f:                     # the same file: a hardlink stays one
            f.write(new)
            f.truncate()
        row['wrote'] = sha(new)
        self.rows[key] = row
        self.save()
        return True

    def undo(self):
        done, newer = 0, 0
        for key, row in list(self.rows.items()):
            dest = pathlib.Path(key)
            if not dest.exists():
                continue
            if sha(dest.read_bytes()) != row.get('wrote'):
                newer += 1                               # BodySlide built it again since: not ours to undo
                continue
            with open(dest, 'r+b') as f:
                f.write(pathlib.Path(row['backup']).read_bytes())
                f.truncate()
            del self.rows[key]
            done += 1
        self.save()
        return done, newer

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.rows, indent=1), encoding='utf-8')


# ---- outfits ----
def weights_by_name(n, s):
    bones, _ = n.skin(s)
    return bones, [{bones[sl]: w for sl, w in s.skin_weights(i)} for i in range(s.count)]


def shares(w, core):
    tot = sum(w.values()) or 1.0
    return {b: x / tot for b, x in w.items() if b not in core}


def same_mesh(src, built, core):
    """({shape: [source vertex of each built vertex]}, None) if every skinned shape of the source is the
    built one; else (None, why not). A zap slider (BodySlide's "hide this under the outfit", on by default
    in many outfits' body copies: 3 of 24 sampled) REMOVES vertices and keeps the rest in order, so each
    built vertex is matched to the next source vertex with its UV and its non-hip weights; every built
    vertex must find one, in order, or the build is not this source's."""
    bshapes = {s.name: s for s in built.shapes()}
    maps = {}
    for s in src.shapes():
        bones, _ = src.skin(s)
        if not bones:
            continue
        b = bshapes.get(s.name)
        if b is None:
            return None, f'no shape {s.name} in the build'
        if b.count > s.count:
            return None, f'{s.name}: {s.count} vertices in the source, {b.count} built'
        _, ws = weights_by_name(src, s)
        _, wb = weights_by_name(built, b)
        m, j = [], 0
        for i in range(s.count):
            if j == b.count:
                break
            if max(abs(x - y) for x, y in zip(s.uv(i), b.uv(j))) > TOL_UV:
                continue
            a, c = shares(ws[i], core), shares(wb[j], core)
            if any(abs(a.get(k, 0.0) - c.get(k, 0.0)) > TOL_W for k in set(a) | set(c)):
                continue
            m.append(i)
            j += 1
        if j != b.count:
            return None, f'{s.name}: built vertex {j} of {b.count} has no source vertex (another source)'
        if b.count == s.count and m != list(range(s.count)):
            return None, f'{s.name}: the same count, another order (another source)'
        maps[s.name] = m
    return maps, None


def patch_built(g, body, src_path, built_path):
    """(new bytes or None, vertices moved or why not, whether this source IS the build's)."""
    import nif
    src = nif.Nif(src_path)
    built = nif.Nif(built_path)
    maps, why = same_mesh(src, built, g.CORE)
    if why:
        return None, why, False
    before_pos = {s.name: s.positions() for s in built.shapes()}
    plans = {}
    for s in src.shapes():
        bones, _ = src.skin(s)
        if not bones or not g.identity(src, s):
            continue
        pos = s.positions()
        _, before = weights_by_name(src, s)
        after = g.transfer(body, pos, before)
        if not after:
            continue
        g.check(pos, before, after)                     # the stage's own proof, as in the owner's build
        plans[s.name] = after
    if not plans:
        return None, 'off the hip band (nothing to move)', True
    for name, after in plans.items():                   # bones the build lacks, with the body's bind data
        b = built.shape(name)
        have, _ = built.skin(b)
        need = sorted({k for w in after.values() for k in w} - set(have))
        missing = [k for k in need if k not in body.bind]
        if missing:
            return None, f'the body has no bind data for {missing}', True
        if need:
            built = g.reparse(built.with_bones(b, [body.bind[k] for k in need]))
    moved = 0
    for name, after in plans.items():
        b = built.shape(name)
        have, _ = built.skin(b)
        slot = {k: j for j, k in enumerate(have)}
        _, own = weights_by_name(built, b)
        for j, i in enumerate(maps[name]):
            w = after.get(i)
            if w is None:
                continue
            tot = sum(own[j].values()) or 1.0
            if all(abs(own[j].get(k, 0.0) / tot - w.get(k, 0.0)) < 5e-4 for k in set(w) | set(own[j])):
                continue                                # a second run: it has this already (halves re-round)
            b.set_skin_weights(j, [(slot[k], x) for k, x in w.items()], total=tot)
            moved += 1
    for s in built.shapes():                            # proof on the result: nothing but weights moved
        if s.positions() != before_pos[s.name]:
            raise SystemExit(f'{built_path}: {s.name} positions changed (internal error)')
    if not moved:
        return bytes(nif.Nif(built_path).b), 0, True     # already has it: the file as it is
    return bytes(built.b), moved, True


def outfits(data, bs, root, ledger, report):
    import garments as g
    g.WORK = pathlib.Path(tempfile.mkdtemp(prefix='AnatomyRebuild-'))
    if not (bs / 'ShapeData/Anatomy/Anatomy.nif').exists():
        raise SystemExit('Tools/BodySlide/ShapeData/Anatomy/Anatomy.nif is missing: run the Anatomy Builder first')
    if not (bs / 'ShapeData/CBBE/CBBEBodyPhysics.nif').exists():
        raise SystemExit("CBBE's BodySlide files are missing (ShapeData/CBBE/CBBEBodyPhysics.nif): install CBBE with them")
    # every candidate set per built mesh: the build itself says which one it came from (same_mesh)
    member, worn = g.groups(bs), g.worn_female(data)
    cands = {}
    skipped = {}
    for osp, s in g.slider_sets(bs):
        name = s.get('name')
        out = g.output_of(s)
        gs = member.get(name, set())
        if any(g.OTHER_BODY.search(x) for x in gs | {name}) or 'CBBE Bodies' in gs or out in g.BODY_OUTPUTS \
                or name == 'Anatomy Body' or out not in worn:
            continue
        src = bs / 'ShapeData' / (s.findtext('DataFolder') or '').strip() / (s.findtext('SourceFile') or '').strip()
        if src.is_file():
            cands.setdefault(out, []).append((name, src))
    print(f'{len(cands)} CBBE outfit meshes a woman wears in your game; looking for your builds in {root}')
    body = g.Body(bs)
    print(f"the body: {len(body.band)} vertices where the hip fold changed CBBE's split")
    done = same = 0
    t0 = time.time()
    for k, (out, sets) in enumerate(sorted(cands.items())):
        built = root / 'meshes' / (out + '.nif')
        if not built.is_file():
            skipped.setdefault('not built yet (build it in BodySlide first)', []).append(out)
            continue
        why, matched = None, False
        for name, src in sets:
            new, why, matched = patch_built(g, body, src, built)
            if matched:
                break
        if new is not None:
            if ledger.write(built, new):
                done += 1
                print(f'   {name[:60]:60} {why:5} vertices')
            else:
                same += 1
        else:
            skipped.setdefault(why if matched else 'left as built: ' + why, []).append(out)
        if k and k % 100 == 0:
            print(f'   ... {k} of {len(cands)} ({time.time() - t0:.0f} s)')
    report['outfits'] = dict(changed=done, already=same, left={k: len(v) for k, v in skipped.items()})
    print(f'outfits: {done} changed, {same} already had it')
    for reason, names in sorted(skipped.items(), key=lambda kv: -len(kv[1])):
        short = reason if len(reason) < 100 else reason[:97] + '...'
        print(f'   left {len(names):4}: {short}' + (f'  ({names[0]})' if len(names) == 1 else ''))


# ---- the neck ----
def neck(data, root, ledger, report):
    import gamedata
    import neck_seam as ns
    built = root / 'meshes' / (BODY + '.nif')
    if not built.is_file():
        print(f'neck: no built body at {built}: build "Anatomy Body" in BodySlide first')
        report['neck'] = 'no body built'
        return
    game = gamedata.Game(data)
    work = pathlib.Path(tempfile.mkdtemp(prefix='AnatomyRebuild-neck-'))
    pieces = []
    for name, rel in (('_head.nif', ns.HEAD_MESH), ('_headrear.nif', ns.REAR_MESH)):
        try:
            raw = game.read(rel)
        except FileNotFoundError:
            continue                                    # no rear piece without CBBE HeadRear Absolute Fix
        (work / name).write_bytes(raw)
        pieces.append(work / name)
    copy = work / 'femalebody.nif'
    copy.write_bytes(built.read_bytes())
    changed = ns.apply(copy, pieces)
    if not changed:
        report['neck'] = 'already'
        return
    wrote = ledger.write(built, copy.read_bytes())
    report['neck'] = 'changed' if wrote else 'already'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', help='Fallout 4 Data folder (default: two folders above this tool)')
    ap.add_argument('--built', help="BodySlide's output folder (default: its Config.xml's, else Data)")
    ap.add_argument('--only', choices=('garments', 'neck'), help='one of the two fixes only')
    ap.add_argument('--undo', action='store_true', help='put back every file it changed that BodySlide has '
                                                        'not rebuilt since')
    ap.add_argument('--home', help=argparse.SUPPRESS)   # where backup/ and the log live (tests)
    args = ap.parse_args()
    home = pathlib.Path(args.home) if args.home else HERE
    home.mkdir(parents=True, exist_ok=True)
    log_path = home / 'AnatomyRebuild.log'
    log = open(log_path, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.__stdout__, log)
    sys.stderr = Tee(sys.__stderr__, log)
    ok = False
    try:
        print(f'Anatomy Rebuild ({time.strftime("%Y-%m-%d %H:%M")}); log: {log_path}')
        if running():
            raise SystemExit('Fallout 4 is running: close it first (a running game holds its meshes)')
        ledger = Ledger(home)
        if args.undo:
            done, newer = ledger.undo()
            print(f'undo: {done} file(s) put back; {newer} rebuilt by BodySlide since, left as they are')
            ok = True
            return 0
        data = find_data(args.data)
        bs = data / 'Tools/BodySlide'
        root = built_root(data, bs, args.built)
        print(f'Data: {data}\nBodySlide builds: {root}')
        report = {}
        if args.only in (None, 'garments'):
            print('\n=== outfits: the hip handover (A-36)')
            outfits(data, bs, root, ledger, report)
        if args.only in (None, 'neck'):
            print('\n=== the neck seam (A-37)')
            neck(data, root, ledger, report)
        ok = True
        print(f'\nDone: {json.dumps(report)}\nRun this again after every BodySlide build. --undo puts the '
              f'originals back (kept in {home / "backup"}).')
    except SystemExit as e:
        print(f'\nSTOPPED: {e.code}')
    except Exception:
        print('\nFAILED with an error; the log has the details:')
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        log.close()
        if FROZEN and sys.stdin is not None and sys.stdin.isatty():
            try:
                input('\nPress Enter to close.')
            except EOFError:
                pass
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
