"""Rebuild EVERY BodySlide output, women and men, zeroed and with morphs, the garments carrying the hip
fold (A-36), in one run: the owner, 2026-09-26: "automation script for rebuild everything - all woman + man
(with woman overwrite conflicts) bodyslides with built morphs etc + rebuilding garments".

  1. plan     every slider set with an output, sorted by the zero preset that actually zeroes it (a woman's
              set by "CBBE Zeroed Sliders", a man's by "BT - Zero"; resolved the way BodySlide resolves it,
              fo4-silhouette's base_body). One set per output and sex: BuildSelection.xml's choice, else the
              only candidate, else the one whose reference matches the live build; never a guess. The
              Anatomy body (FemaleBody) is left to the Anatomy pipeline, whose Anatomy-dev copy wins in game.
  2. build    a private BodySlide: the program and presets copied, SliderSets copied, ShapeData HARDLINKED
              (no 3.6 GB copy; a patched garment is written as a NEW file after unlinking, never through a
              link), the garments patched there (tools/garments.py).
  3. regen    headless group builds, --trimorphs, each sex into its own folder, then one merged tree in
              which the WOMAN build wins every output both sexes write (hardlinks, no copy).
  4. verify   every planned output built with its .tri; the patched garments against the live builds (the
              same vertices and morphs, only core weights moved); every other output compared byte for byte
              with the live build, and the differences listed.
  5. install  the merged tree over the BodySlide output mod, in place (it is hardlinked into Data), only
              files that differ, the replaced ones backed up; refused while Fallout 4 runs.

    python tools/rebuild_all.py plan
    python tools/rebuild_all.py all [--out D:/F4Output/Rebuild]           # plan, build, regen, verify
    python tools/rebuild_all.py install [--out ...] [--into <mod folder>] # after verify, game closed
"""
import argparse
import collections
import json
import os
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import garments as g
import nif

SILHOUETTE_TOOLS = pathlib.Path(r'C:\Users\DuduPhudu\Documents\Projects\fo4-silhouette\tools')
OUT = pathlib.Path(r'D:\F4Output\Rebuild')
INTO = pathlib.Path(r'D:\Vortex\fallout4\mods\bodyslides_f4_sd')
ZEROS = {'woman': 'CBBE Zeroed Sliders', 'man': 'BT - Zero'}
ANATOMY_OWNS = {'actors\\character\\characterassets\\femalebody'}


def load_silhouette():
    sys.path.insert(0, str(SILHOUETTE_TOOLS))
    import base_body
    import silhouette_gen as sg
    return base_body, sg


def plan(bs, data, into):
    base_body, sg = load_silhouette()
    presets = {p['name']: p for p in sg.read_presets(bs / 'SliderPresets')}
    for z in ZEROS.values():
        if z not in presets:
            raise SystemExit(f'the zero preset "{z}" is not in SliderPresets')
    assets = data / 'Meshes/Actors/Character/CharacterAssets'
    body = set()
    for b in ('FemaleBody', 'MaleBody'):
        if (assets / f'{b}.tri').exists():
            body |= set().union(*base_body.read_tri(assets / f'{b}.tri').values())

    def zeroes(z, ss):
        return not any(v for k, v in base_body.resolve(presets[z], ss).items() if k in body)

    choice = g.build_choices(bs)
    cands = collections.defaultdict(list)             # (sex, output) -> sets
    left = collections.defaultdict(list)
    for ss in base_body.read_slider_sets(bs):
        out = g.norm(ss['output'].replace('meshes\\', '', 1)) if ss['output'] else ''
        if not out:
            continue
        if out in ANATOMY_OWNS or ss['name'] == 'Anatomy Body':
            left['the Anatomy body (built and staged by the Anatomy pipeline)'].append(ss['name'])
            continue
        if not (bs / 'ShapeData' / ss['data_folder'] / ss['source_file']).exists():
            left['its ShapeData is missing'].append(ss['name'])
            continue
        sex = next((s for s, z in ZEROS.items() if zeroes(z, ss)), None)
        if sex is None:
            left['no zero preset zeroes it'].append(ss['name'])
            continue
        cands[(sex, out)].append(ss)
    runs = collections.defaultdict(list)             # sex -> [(set name, output)]
    for (sex, out), ss in sorted(cands.items()):
        # the set the LIVE build is made of wins: BuildSelection.xml can be stale. It named Fusion Girl
        # variants of four outfits whose live builds are the CBBE sets, from a later targeted build, and
        # the first full run rebuilt them on the wrong body (verify listed them, 2026-09-26)
        pick = []
        live = into / 'meshes' / (out + '.nif')
        if len(ss) > 1 and live.exists():
            try:
                built = base_body.read_shapes(live)
                fits = []
                for s in ss:
                    ref = base_body.read_shapes(bs / 'ShapeData' / s['data_folder'] / s['source_file'])
                    if built and set(ref) == set(built) and all(len(ref[n]) == len(built[n]) for n in built):
                        fits.append(s)
                pick = fits if len(fits) == 1 else []
            except Exception:
                pick = []
        if not pick:
            pick = [s for s in ss if s['name'] == choice.get(out)]
        if not pick and len(ss) == 1:
            pick = ss
        if not pick:
            left['several sets write it, BuildSelection names none, the live build fits none uniquely'].append(
                f'{out}: {[s["name"] for s in ss]}')
            continue
        runs[sex].append((pick[0]['name'], out))
    return runs, left


def link_tree(src, dst):
    """dst mirrors src with hardlinks (the same volume); a file that cannot link is copied."""
    n = 0
    for root, _dirs, files in os.walk(src):
        rel = pathlib.Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for f in files:
            s, d = pathlib.Path(root) / f, dst / rel / f
            if d.exists():
                continue
            try:
                os.link(s, d)
            except OSError:
                shutil.copy2(s, d)
            n += 1
    return n


def build(bs, data, out, into):
    runs, left = plan(bs, data, into)
    home = g.workspace(bs, out, out / 'woman')
    shutil.rmtree(home / 'SliderSets')
    shutil.copytree(bs / 'SliderSets', home / 'SliderSets')
    print(f'ShapeData: {link_tree(bs / "ShapeData", home / "ShapeData")} files linked')
    # the garments (A-36): the same selection and transfer as tools/garments.py, written into the links' place
    targets, _ = g.plan(bs, data)
    woman_sets = {name for name, _o in runs['woman']}
    body = g.Body(bs)
    patched = []
    for t in targets:
        if t['name'] not in woman_sets:
            continue
        src = bs / 'ShapeData' / t['folder'] / t['src']
        report = g.patch_nif(body, src, home / 'ShapeData' / t['folder'] / t['src'])
        moved = {k: v for k, v in report.items() if isinstance(v, int)}
        if moved:
            patched.append(dict(t, moved=moved))
        else:                                           # nothing moved: put the original back (a link)
            dst = home / 'ShapeData' / t['folder'] / t['src']
            dst.unlink()
            os.link(src, dst)
    print(f'garments: {len(patched)} sets carry the hip fold')
    for sex, pairs in runs.items():
        root = ET.Element('SliderGroups')
        grp = ET.SubElement(root, 'Group', name=f'Rebuild {sex}')
        for name in sorted({n for n, _o in pairs}):
            ET.SubElement(grp, 'Member', name=name)
        ET.indent(root)
        ET.ElementTree(root).write(home / 'SliderGroups' / f'Rebuild {sex}.xml', encoding='UTF-8',
                                   xml_declaration=True)
    (out / 'rebuild_plan.json').write_text(json.dumps(dict(runs=runs, left=left, patched=patched), indent=1),
                                           encoding='utf-8')
    for sex, pairs in runs.items():
        print(f'{sex}: {len(pairs)} outputs from {len({n for n, _o in pairs})} slider sets, "{ZEROS[sex]}"')
    for reason, names in sorted(left.items(), key=lambda kv: -len(kv[1])):
        print(f'  left {len(names):4}: {reason}')
    return home


def regen(home, out):
    results = {}
    for sex in ('man', 'woman'):
        target = out / sex
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        log = home / 'Log_BS.txt'
        if log.exists():
            log.unlink()
        cmd = [str(home / 'BodySlide.exe'), '--groupbuild', f'Rebuild {sex}', '--targetdir', str(target),
               '--preset', ZEROS[sex], '--trimorphs']
        run = subprocess.run(cmd, cwd=home, capture_output=True, text=True, timeout=14400)
        text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
        shutil.copy2(log, out / f'Log_BS_{sex}.txt') if log.exists() else None
        ok = 'All group build sets processed successfully!' in text
        errors = [line for line in text.splitlines() if '[1]' in line or 'rror' in line or 'ailed' in line]
        results[sex] = (run.returncode, ok, errors)
        print(f"{sex}: BodySlide exit {run.returncode}; {'all sets built' if ok else 'NOT all built'}; "
              f'{len(errors)} error lines')
        for e in errors[:20]:
            print('   ', e)
    merged = out / 'merged'
    if merged.exists():
        shutil.rmtree(merged)
    for sex in ('man', 'woman'):                      # the woman's build wins what both write
        for f in (out / sex).rglob('*'):
            if f.is_file():
                d = merged / f.relative_to(out / sex)
                d.parent.mkdir(parents=True, exist_ok=True)
                if d.exists():
                    d.unlink()
                os.link(f, d)
    return all(ok for _c, ok, _e in results.values())


def verify(out, into):
    p = json.loads((out / 'rebuild_plan.json').read_text(encoding='utf-8'))
    merged = out / 'merged'
    missing = []
    for sex, pairs in p['runs'].items():
        for _name, o in pairs:
            nif_path = out / sex / 'meshes' / (o + '.nif')
            if not nif_path.exists() and not any((out / sex).rglob(pathlib.Path(o).name + '.nif')):
                missing.append(f'{sex}: {o}')
    # the garments: the same vertices and morphs as the live build, only core weights moved
    patched_outputs = {t['output'] for t in p['patched']}
    tmp = out / '_garments'
    if tmp.exists():
        shutil.rmtree(tmp)
    for f in merged.rglob('*.nif'):
        rel = f.relative_to(merged)
        if g.norm(str(rel)) in patched_outputs:
            d = tmp / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            os.link(f, d)
            if f.with_suffix('.tri').exists():
                os.link(f.with_suffix('.tri'), d.with_suffix('.tri'))
    bad, checked, _m = g.verify(tmp, into)
    same, differ, new = 0, [], []
    for f in merged.rglob('*'):
        if not f.is_file():
            continue
        rel = f.relative_to(merged)
        live = into / rel
        if not live.exists():
            new.append(str(rel))
        elif live.read_bytes() == f.read_bytes():
            same += 1
        elif g.norm(str(rel.with_suffix('.nif'))) not in patched_outputs:
            differ.append(str(rel))
    print(f'verify: {len(missing)} planned outputs not built; garments {checked} checked, {len(bad)} bad; '
          f'other files: {same} identical to the live build, {len(differ)} differ, {len(new)} new')
    for m in missing[:20]:
        print('   NOT BUILT', m)
    for b in bad[:20]:
        print('   BAD', b)
    for d in differ[:40]:
        print('   differs', d)
    (out / 'verify.json').write_text(json.dumps(dict(missing=missing, bad=bad, differ=differ, new=new), indent=1),
                                     encoding='utf-8')
    return not missing and not bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('what', choices=('plan', 'all', 'regen', 'verify', 'install'))
    ap.add_argument('--data', type=pathlib.Path, default=g.DATA)
    ap.add_argument('--out', type=pathlib.Path, default=OUT)
    ap.add_argument('--into', type=pathlib.Path, default=INTO)
    args = ap.parse_args()
    bs = args.data / 'Tools/BodySlide'
    if args.what == 'plan':
        runs, left = plan(bs, args.data, args.into)
        for sex, pairs in runs.items():
            print(f'{sex}: {len(pairs)} outputs, "{ZEROS[sex]}"')
        for reason, names in sorted(left.items(), key=lambda kv: -len(kv[1])):
            print(f'  left {len(names):4}: {reason}')
        return
    if args.what in ('all', 'regen'):
        home = build(bs, args.data, args.out, args.into) if args.what == 'all' else args.out / 'BodySlide'
        if not regen(home, args.out):
            sys.exit(1)
    ok = verify(args.out, args.into)
    if args.what == 'install':
        if not ok:
            raise SystemExit('verify failed: nothing installed')
        print(f'install: {g.install(args.out / "merged", args.into, args.out)} files written in place into '
              f'{args.into}')
    elif not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
