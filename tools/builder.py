"""Anatomy Builder: the Anatomy body, made from the player's own CBBE and skin (decisions A-21, A-23).

    AnatomyBuilder.exe                   (anywhere; it finds the game. MO2: run it from MO2)
    AnatomyBuilder.exe --data <Data> [--out <folder>] [--keep-work]

It reads, as the game would load them (loose files first, then archives in load order):
  - CBBE's BodySlide files (the "CBBE Body Physics" set);
  - the skeleton the body is bound to (skeleton.nif);
  - the body's skin material and the textures it names;
  - the player's ocbp.ini, to decide whether the breasts' weights move onto LBreast_skin/RBreast_skin
    (only when that file drives those bones; otherwise CBBE's own cloth physics keeps them);
and Nahka's genitals as shipped with us (data/: her patch against CBBE, and her texture island).

Every stage proves itself or stops (align, weights, verification, the split, the textures). What it
writes are paths no other mod ships, so nothing needs resolving in a mod manager:
    Tools/BodySlide/SliderSets/Anatomy.osp, Tools/BodySlide/ShapeData/Anatomy/*,
    Tools/BodySlide/SliderGroups/Anatomy.xml, Tools/BodySlide/SliderCategories/Anatomy.xml,
    Textures/Anatomy/FemaleBody_d/n/s.dds, Materials/Anatomy/AnatomyGenitals.bgsm
Then: open BodySlide, choose "Anatomy Body" and your preset, and Build.
"""
import argparse
import contextlib
import hashlib
import io
import os
import pathlib
import shutil
import sys
import tempfile
import time
import traceback

# packed: PyInstaller sets sys.frozen; Nuitka (the release's compiler since 2026-09-26) marks its compiled
# modules with __compiled__ instead, and its sys.executable is the exe itself
FROZEN = bool(getattr(sys, 'frozen', False)) or '__compiled__' in globals()
HERE = pathlib.Path(sys.executable).parent if FROZEN else pathlib.Path(__file__).resolve().parent
if not FROZEN:
    sys.path.insert(0, str(HERE))
ROOT = HERE.parent
SHIPPED = HERE / 'data' if FROZEN else ROOT / 'build/patch'
SET = 'Anatomy Body'
OUTPUTS = {                                         # published path -> produced file (filled in main)
    'Tools/BodySlide/SliderSets/Anatomy.osp': None,
    'Tools/BodySlide/ShapeData/Anatomy/Anatomy.nif': None,
    'Tools/BodySlide/ShapeData/Anatomy/Anatomy.osd': None,
    'Tools/BodySlide/SliderGroups/Anatomy.xml': None,
    'Tools/BodySlide/SliderCategories/Anatomy.xml': None,
    'Textures/Anatomy/FemaleBody_d.dds': None,
    'Textures/Anatomy/FemaleBody_n.dds': None,
    'Textures/Anatomy/FemaleBody_s.dds': None,
    'Materials/Anatomy/AnatomyGenitals.bgsm': None,
}
SKELETON = 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'
GROUPS = ('<?xml version="1.0" encoding="UTF-8"?>\n<SliderGroups>\n'
          '    <Group name="CBBE">\n        <Member name="Anatomy Body"/>\n    </Group>\n'
          '    <Group name="Anatomy">\n        <Member name="Anatomy Body"/>\n    </Group>\n</SliderGroups>\n')


class Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()
        return len(s)


def find_data(arg):
    import gamedata
    return gamedata.find_data(arg, HERE, 'AnatomyBuilder.exe')


def sha(blob):
    return hashlib.sha1(blob).hexdigest()[:12]


def breasts_driven(game):
    """True when the player's own ocbp.ini simulates LBreast_skin and RBreast_skin (the owner's
    MadKita setup); then CBBE's cloth-bone breast weights move onto them. Otherwise they stay."""
    if game.find('F4SE/Plugins/ocbp.ini') is None:
        return False, 'no ocbp.ini'
    attach, section = set(), None
    for line in game.read('F4SE/Plugins/ocbp.ini').decode('utf-8', 'replace').splitlines():
        line = line.split(';')[0].strip()
        if line.startswith('['):
            section = line.strip('[]').strip().lower()
        elif section == 'attach' and '=' in line:
            attach.add(line.split('=', 1)[0].strip())
    driven = {'LBreast_skin', 'RBreast_skin'} <= attach
    return driven, f'ocbp.ini [Attach] {"names" if driven else "does not name"} LBreast_skin and RBreast_skin'


def run_stage(label, fn):
    print(f'\n=== {label}')
    t = time.time()
    try:
        fn()
    except SystemExit as e:
        if e.code not in (None, 0):
            raise SystemExit(f'{label} stopped: {e.code}')
    print(f'--- {label}: done in {time.time() - t:.0f} s')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--data', nargs='+', help='Fallout 4 Data folder (default: Data/Tools/<here>, else the game the '
                                   'registry names)')
    ap.add_argument('--out', help='write the results here instead of into Data')
    ap.add_argument('--keep-work', action='store_true', help='keep the work folder (for a bug report)')
    import gamedata
    args = gamedata.parse_args(ap, FROZEN)
    log_path = HERE / 'AnatomyBuilder.log'
    log = open(log_path, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.__stdout__, log)
    sys.stderr = Tee(sys.__stderr__, log)
    work = pathlib.Path(tempfile.mkdtemp(prefix='AnatomyBuilder-'))
    ok = False
    try:
        print(f'Anatomy Builder ({time.strftime("%Y-%m-%d %H:%M")}); log: {log_path}')
        data = find_data(args.data)
        import gamedata
        game = gamedata.Game(data)
        print(f'Data: {data}; {len(game.plugins)} plugins active, {len(game.archives)} archives')

        # ---- what it reads, and from where (CBBE's file names come from its own slider set)
        import align_body as ab
        osp = data / 'Tools/BodySlide/SliderSets/CBBE.osp'
        if not osp.exists():
            raise SystemExit('CBBE\'s BodySlide files are missing (Tools/BodySlide/SliderSets/CBBE.osp). Install CBBE '
                             '(Nexus 15) with its BodySlide files, then run the builder again.')
        cset, csliders = ab.read_set(osp, ab.CBBE_SET)
        folder = 'Tools/BodySlide/ShapeData/' + cset.findtext('DataFolder')
        cbbe_files = ['Tools/BodySlide/SliderSets/CBBE.osp', f'{folder}/{cset.findtext("SourceFile")}'] + \
                     sorted({f'{folder}/{f}' for *_, f in csliders})
        missing = [f for f in cbbe_files if not (data / f).exists()]
        if missing:
            raise SystemExit(f'CBBE\'s BodySlide files are incomplete ({missing}): reinstall CBBE (Nexus 15)')
        import genital_texture as gt
        for rel in cbbe_files + [SKELETON, gt.SKIN_MATERIAL]:
            if game.find(rel) is None:
                raise SystemExit(f'{rel}: the game does not have it (loose or in any active archive)')
            print(f'   input {game.describe(rel)}  sha1 {sha(game.read(rel))}')
        for name in ('nahka_patch.json.gz', 'tex/crops.json'):
            if not (SHIPPED / name).exists():
                raise SystemExit(f'{SHIPPED / name} is missing: reinstall Anatomy')

        # ---- the pipeline, pointed at the work folder
        ab.DEFAULT_DATA = data
        ab.OUT = work / 'project'
        skeleton_copy = work / 'skeleton.nif'
        skeleton_copy.write_bytes(game.read(SKELETON))
        import apply_patch
        import mask
        import split_genitals as sg
        import verify_zex
        import zex_bones as zb
        zb.SKELETON = skeleton_copy
        zb.MASK = ab.OUT / 'Masks/AnatomyGenitalRegion.xml'
        zb.STAGE1 = ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif'
        driven, why = breasts_driven(game)
        zb.MOVE_BREASTS = driven
        print(f'   breasts: {"move onto LBreast_skin/RBreast_skin" if driven else "keep CBBE\'s cloth weights"} ({why})')
        sg.PROJECT = ab.OUT
        gt.OUT = work / 'textures'
        gt.ANATOMY_OUT = gt.OUT / 'Anatomy'
        gt.CROPS = SHIPPED / 'tex'
        gt.FULL_NAHKA = False

        run_stage('1. CBBE plus Nahka\'s genitals', lambda: apply_patch.build(
            data, apply_patch.load(SHIPPED / 'nahka_patch.json.gz'), ab.OUT))
        sys.argv = ['mask.py', '--project', str(ab.OUT)]
        run_stage('2. the genital region', mask.main)
        run_stage('3. bones and weights', zb.main)
        import hip_fold
        run_stage('3b. the hip fold (A-30)', hip_fold.main)
        sys.argv = ['verify_zex.py', '--saved', str(ab.OUT / 'ShapeData/AnatomyBodyZeX')]
        run_stage('4. verification', verify_zex.main)
        run_stage('5. the genitals\' own shape', sg.main)
        run_stage('6. the genitals\' texture and material, from this skin', lambda: gt.main(data))

        # ---- publish into Data (or --out): our own paths only
        produced = {
            'Tools/BodySlide/SliderSets/Anatomy.osp': ab.OUT / 'SliderSets/Anatomy.osp',
            'Tools/BodySlide/ShapeData/Anatomy/Anatomy.nif': ab.OUT / 'ShapeData/Anatomy/Anatomy.nif',
            'Tools/BodySlide/ShapeData/Anatomy/Anatomy.osd': ab.OUT / 'ShapeData/Anatomy/Anatomy.osd',
            'Textures/Anatomy/FemaleBody_d.dds': gt.ANATOMY_OUT / 'FemaleBody_d.dds',
            'Textures/Anatomy/FemaleBody_n.dds': gt.ANATOMY_OUT / 'FemaleBody_n.dds',
            'Textures/Anatomy/FemaleBody_s.dds': gt.ANATOMY_OUT / 'FemaleBody_s.dds',
            'Materials/Anatomy/AnatomyGenitals.bgsm': gt.ANATOMY_OUT / 'AnatomyGenitals.bgsm',
            'Tools/BodySlide/SliderCategories/Anatomy.xml': ab.OUT / 'SliderCategories/Anatomy.xml',
        }
        groups = work / 'Anatomy.xml'
        groups.write_text(GROUPS, encoding='utf-8')
        produced['Tools/BodySlide/SliderGroups/Anatomy.xml'] = groups
        if set(produced) != set(OUTPUTS):
            raise SystemExit('internal: the output list changed')
        dest = pathlib.Path(args.out) if args.out else data
        print(f'\n=== writing to {dest}')
        for rel, src in produced.items():
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + '.anatomy-new')
            shutil.copyfile(src, tmp)
            os.replace(tmp, target)                     # a crash never leaves half a file
            print(f'   {rel}  sha1 {sha(target.read_bytes())}')
        ok = True
        print('\nDone. Now open BodySlide, choose the set "Anatomy Body", your preset, and Build (or Batch '
              'Build with "Anatomy Body" ticked). Re-run this builder after changing your CBBE, skin or physics preset (ocbp.ini).')
    except SystemExit as e:
        print(f'\nSTOPPED: {e.code}')
    except Exception:
        print('\nFAILED with an error; the log has the details:')
        traceback.print_exc()
    finally:
        if ok and not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)
        elif not ok:
            print(f'(work folder kept for a bug report: {work})')
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        log.close()
    if FROZEN and sys.stdin is not None and sys.stdin.isatty():
        try:                                            # a double-clicked window would close unread;
            input('\nPress Enter to close.')            # run from a script or launcher, nobody is there
        except EOFError:
            pass
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
