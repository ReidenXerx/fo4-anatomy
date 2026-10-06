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
    Tools/BodySlide/SliderPresets/Anatomy.xml (the "Anatomy Zeroed Sliders" preset),
    Textures/Anatomy/FemaleBody_d/n/s.dds, Materials/Anatomy/AnatomyGenitals.bgsm
and, when BodyTalk 4 is installed, the men's body with the anus opened (A-69):
    Tools/BodySlide/SliderSets/AnatomyMale.osp, Tools/BodySlide/ShapeData/AnatomyMale/*,
    Tools/BodySlide/SliderGroups/AnatomyMale.xml
Then: open BodySlide, choose "Anatomy Body" and your preset, and Build.
"""
import argparse
import contextlib
import errno
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


def own_version():
    """the release's version (release.py writes data/version.txt next to the exe), so every log says which builder
    ran; 'source' when not packed. A plain file, not the exe's version resource read through version.dll: that call
    tipped Windows Defender's ML into flagging 1.2.4's first build (Trojan:Script/Wacatac.C!ml, 2026-10-05)"""
    try:
        return (HERE / 'data' / 'version.txt').read_text(encoding='utf-8').strip() or '?'
    except OSError:
        return 'source' if not FROZEN else '?'
if not FROZEN:
    sys.path.insert(0, str(HERE))
ROOT = HERE.parent
SHIPPED = HERE / 'data' if FROZEN else ROOT / 'build/patch'
PRESETS = HERE / 'data/presets' if FROZEN else ROOT / 'build/config/Anatomy'   # A-57: tools/default_preset.py's files
SET = 'Anatomy Body'
OUTPUTS = {                                         # published path -> produced file (filled in main)
    'Tools/BodySlide/SliderSets/Anatomy.osp': None,
    'Tools/BodySlide/ShapeData/Anatomy/Anatomy.nif': None,
    'Tools/BodySlide/ShapeData/Anatomy/Anatomy.osd': None,
    'Tools/BodySlide/SliderGroups/Anatomy.xml': None,
    'Tools/BodySlide/SliderCategories/Anatomy.xml': None,
    'Tools/BodySlide/SliderPresets/Anatomy.xml': None,
    'Textures/Anatomy/FemaleBody_d.dds': None,
    'Textures/Anatomy/FemaleBody_n.dds': None,
    'Textures/Anatomy/FemaleBody_s.dds': None,
    'Materials/Anatomy/AnatomyGenitals.bgsm': None,
    'F4SE/Plugins/Anatomy/ocbp-body.ini': None,                     # A-57: the physics for the body built (CBBE/3BBB)
    'F4SE/Plugins/Anatomy/OCBPCollisionConfig-body.txt': None,
    'F4SE/Plugins/Anatomy/build.ini': None,                         # what was built, for the engine's health check
}
SKELETON = 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'
FEMALE_SKELETON = 'Meshes/Actors/Character/CharacterAssets/female/skeleton.nif'   # what women load (A-57: 3BBB's bones)
GROUPS = ('<?xml version="1.0" encoding="UTF-8"?>\n<SliderGroups>\n'
          '    <Group name="CBBE">\n        <Member name="Anatomy Body"/>\n    </Group>\n'
          '    <Group name="Anatomy">\n        <Member name="Anatomy Body"/>\n    </Group>\n</SliderGroups>\n')
# CBBE's own "CBBE Zeroed Sliders" under our name: every slider at 0, so a body (and its outfits) built with it is the
# shape Silhouette's run-time morphs start from. In the CBBE group too, so it is there when building CBBE outfits.
PRESET = ('<?xml version="1.0" encoding="UTF-8"?>\n<SliderPresets>\n'
          '    <Preset name="Anatomy Zeroed Sliders" set="Anatomy Body">\n'
          '        <Group name="CBBE"/>\n        <Group name="Anatomy"/>\n'
          '        <SetSlider name="Ankles" size="big" value="0"/>\n'
          '    </Preset>\n</SliderPresets>\n')


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


DEFAULT_PRESET = 'F4SE/Plugins/Anatomy/ocbp-default.ini'


def breasts_driven(game):
    """True when the preset the engine will run simulates LBreast_skin and RBreast_skin: the player's own
    ocbp.ini, else Anatomy's default (A-46, read by the engine only when the player has none). Then CBBE's
    cloth-bone breast weights move onto them. Otherwise they stay."""
    preset = 'F4SE/Plugins/ocbp.ini'
    if game.find(preset) is None:
        if game.find(DEFAULT_PRESET) is None:
            return False, 'no ocbp.ini, and no Anatomy default preset: is Anatomy installed?'
        preset = DEFAULT_PRESET
    attach, section = set(), None
    for line in game.read(preset).decode('utf-8', 'replace').splitlines():
        line = line.split(';')[0].strip()
        if line.startswith('['):
            section = line.strip('[]').strip().lower()
        elif section == 'attach' and '=' in line:
            attach.add(line.split('=', 1)[0].strip())
    driven = {'LBreast_skin', 'RBreast_skin'} <= attach
    whose = 'your ocbp.ini' if preset.endswith('/ocbp.ini') else "Anatomy's default preset (you have no ocbp.ini)"
    return driven, f'{whose}: [Attach] {"names" if driven else "does not name"} LBreast_skin and RBreast_skin'


def fnv1a(blob):
    """The engine's hash (Health.cpp Fnv1a): 32-bit FNV-1a, lowercase hex."""
    h = 2166136261
    for b in blob:
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return f'{h:08x}'


def stamp(body, breasts, preset_bytes):
    """F4SE/Plugins/Anatomy/build.ini: the body built and where its breasts are weighted, and the player's ocbp.ini
    as it was (the engine's health check tells a preset changed since from one that no longer fits)."""
    return ('; written by AnatomyBuilder: what it built, read by Anatomy Engine\'s health check\n'
            '[Build]\n'
            f'date={time.strftime("%Y-%m-%d %H:%M")}\n'
            f'body={body}\n'
            f'breasts={breasts}\n'
            f'presetHash={fnv1a(preset_bytes) if preset_bytes is not None else "none"}\n')


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
    ap.add_argument('--body', choices=('auto', 'cbbe', '3bbb'), default='auto',
                    help='the body to build on (default: 3BBB when it is installed and your physics preset drives its '
                         'breast bones, else CBBE)')
    ap.add_argument('--no-player-preset', action='store_true',
                    help='build as for a player without an ocbp.ini of their own (the prebuilt bodies, A-72)')
    import gamedata
    args = gamedata.parse_args(ap, FROZEN)
    log_path = HERE / 'AnatomyBuilder.log'
    log = open(log_path, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.__stdout__, log)
    sys.stderr = Tee(sys.__stderr__, log)
    work = pathlib.Path(tempfile.mkdtemp(prefix='AnatomyBuilder-'))
    ok = False
    try:
        print(f'Anatomy Builder {own_version()} ({time.strftime("%Y-%m-%d %H:%M")}); log: {log_path}')
        data = find_data(args.data)
        import gamedata
        game = gamedata.Game(data)
        print(f'Data: {data}; {len(game.plugins)} plugins active, {len(game.archives)} archives')
        if getattr(args, 'no_player_preset', False):
            # A-72: a prebuilt body is for players with no preset of their own (another preset is incompatible), so
            # the build must not follow whatever ocbp.ini this Data happens to carry
            find = game.find
            game.find = lambda rel, _f=find: None if rel.replace('\\', '/').lower() == 'f4se/plugins/ocbp.ini' \
                else _f(rel)
            print('   preset: built as for a player without an ocbp.ini of their own')

        # ---- what it reads, and from where (CBBE's file names come from its own slider set)
        import align_body as ab
        osp = data / 'Tools/BodySlide/SliderSets/CBBE.osp'
        if not gamedata.present(osp):
            # say what IS there (a player's MO2 setup, 2026-09-27: 609 plugins seen, no CBBE.osp): no BodySlide folder at
            # all, a SliderSets folder without CBBE's set, or CBBE's set under another name
            sets = data / 'Tools/BodySlide/SliderSets'
            if not gamedata.present_dir(data / 'Tools/BodySlide'):
                seen = 'there is no Tools\\BodySlide folder in this Data at all'
            elif not gamedata.present_dir(sets):
                seen = 'Tools\\BodySlide is there but has no SliderSets folder'
            else:
                names = sorted(e.name for e in os.scandir(sets) if e.name.lower().endswith('.osp'))
                cbbe = [n for n in names if 'cbbe' in n.lower()]
                seen = (f'SliderSets holds {len(names)} slider set file(s); the CBBE-named ones: '
                        f'{", ".join(cbbe[:12]) or "none"}')
            raise SystemExit('CBBE\'s BodySlide files are missing (Tools/BodySlide/SliderSets/CBBE.osp): ' + seen + '. '
                             'Install CBBE (Nexus 15) WITH its BodySlide files (its installer option), make sure it is '
                             'enabled, then run the builder again (under MO2: from MO2, so it sees MO2\'s mods).')
        cset, csliders = ab.read_set(osp, ab.CBBE_SET)
        folder = 'Tools/BodySlide/ShapeData/' + cset.findtext('DataFolder')
        cbbe_files = ['Tools/BodySlide/SliderSets/CBBE.osp', f'{folder}/{cset.findtext("SourceFile")}'] + \
                     sorted({f'{folder}/{f}' for *_, f in csliders})
        missing = [f for f in cbbe_files if not gamedata.present(data / f)]
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
        import tbbb
        theirs = 'F4SE/Plugins/ocbp.ini' if game.find('F4SE/Plugins/ocbp.ini') is not None else None
        on_3bbb, why3 = tbbb.choose(game, args.body, theirs)
        print(f'   body: {why3}')
        # the body in the game is 3BBB (its stamp: a prebuilt body, as the Ivy collection ships, or an earlier build),
        # but 3BBB's BodySlide files are not here, so this run would fall back to CBBE and write a CBBE physics preset
        # over the 3BBB body: nailed, floating breasts (an Ivy player, 2026-10-06). Asked for by name, CBBE still builds.
        stamp_rel = 'F4SE/Plugins/Anatomy/build.ini'
        if args.body == 'auto' and not on_3bbb and game.find(stamp_rel) is not None and \
                game.find(tbbb.SHAPEDATA) is None and \
                'body=3bbb' in game.read(stamp_rel).decode('utf-8', 'replace').replace(' ', '').lower():
            raise SystemExit(
                'your Anatomy body is 3BBB (F4SE/Plugins/Anatomy/build.ini says so: a prebuilt body, as collections '
                'like Ivy ship, or an earlier build), but 3BBB\'s BodySlide files are not installed here, so this run '
                'would make a CBBE body whose physics preset does not fit it. With a prebuilt body you need neither '
                'this builder nor BodySlide: nothing was changed. To build on 3BBB, install "3BBB Physics (CBBE - TWB)" '
                '(Nexus 48978, its CBBE file); to switch to CBBE on purpose, run with --body cbbe.')
        if on_3bbb:
            # A-57: 3BBB's weights, and its bones from the skeleton women load (Skeletal Adjustments' 3BBB skeleton)
            women = work / 'female_skeleton.nif'
            if game.find(FEMALE_SKELETON) is None:
                raise SystemExit(f'a 3BBB body needs a women\'s skeleton with its bones ({FEMALE_SKELETON}): install '
                                 'Skeletal Adjustments for CBBE (Nexus 39006), or build on CBBE (--body cbbe)')
            women.write_bytes(game.read(FEMALE_SKELETON))
            lacking = [b for b in tbbb.BREAST_BONES if b not in zb.skeleton_world(women)]
            if lacking:
                raise SystemExit(f'{FEMALE_SKELETON} has no {lacking}: it is not a 3BBB skeleton. Install Skeletal '
                                 'Adjustments for CBBE (Nexus 39006), or build on CBBE (--body cbbe)')
            verify_zex.WOMEN_SKELETON = women
            print(f'   input {game.describe(tbbb.SHAPEDATA)}  sha1 {sha(game.read(tbbb.SHAPEDATA))}')
            zb.MOVE_BREASTS = False
            breasts = '3bbb'
            print('   breasts: keep 3BBB\'s own breast bones')
        else:
            driven, why = breasts_driven(game)
            zb.MOVE_BREASTS = driven
            breasts = 'moved' if driven else 'cloth'
            print(f'   breasts: {"move onto LBreast_skin/RBreast_skin" if driven else "keep CBBE\'s cloth weights"} ({why})')
        sg.PROJECT = ab.OUT
        gt.OUT = work / 'textures'
        gt.ANATOMY_OUT = gt.OUT / 'Anatomy'
        gt.CROPS = SHIPPED / 'tex'
        gt.FULL_NAHKA = False

        patch = apply_patch.load(SHIPPED / 'nahka_patch.json.gz')
        run_stage('1. CBBE plus Nahka\'s genitals', lambda: apply_patch.build(data, patch, ab.OUT))
        if on_3bbb:
            import json
            mapping = {int(k): v for k, v in json.loads((ab.OUT / 'mapping.json').read_text())['output_to_cbbe'].items()}
            run_stage('1b. the 3BBB body (A-57)', lambda: print(tbbb.apply(
                zb.STAGE1, mapping, patch['near'], len(mapping), game.read(tbbb.SHAPEDATA), game.read(cbbe_files[1]))))
        sys.argv = ['mask.py', '--project', str(ab.OUT)]
        run_stage('2. the genital region', mask.main)
        run_stage('3. bones and weights', zb.main)
        import hip_fold
        run_stage('3b. the hip fold (A-30)', hip_fold.main)
        sys.argv = ['verify_zex.py', '--saved', str(ab.OUT / 'ShapeData/AnatomyBodyZeX')]
        run_stage('4. verification', verify_zex.main)
        run_stage('5. the genitals\' own shape', sg.main)
        run_stage('6. the genitals\' texture and material, from this skin', lambda: gt.main(data))
        import anal_canal
        import osd as osd_module
        run_stage('6b. the anal canal (A-50)', lambda: print(anal_canal.build(
            ab.OUT / 'ShapeData/Anatomy/Anatomy.nif', ab.OUT / 'ShapeData/Anatomy/Anatomy.osd', osd_module)))
        import vaginal_canal
        run_stage('6c. the vaginal canal\'s own UVs (A-54)', lambda: print(vaginal_canal.build(
            ab.OUT / 'ShapeData/Anatomy/Anatomy.nif', ab.OUT / 'ShapeData/Anatomy/Anatomy.osd', osd_module)))
        import atlas
        run_stage('7. the genitals\' own small textures (A-48)', lambda: print(
            atlas.apply(ab.OUT / 'ShapeData/Anatomy/Anatomy.nif', gt.ANATOMY_OUT)))
        run_stage('8. the anal canal mucosa (A-50)', lambda: print(anal_canal.paint_maps(gt.ANATOMY_OUT, atlas.LAST)))
        run_stage('8b. the vaginal canal mucosa (A-54)', lambda: print(vaginal_canal.paint_maps(gt.ANATOMY_OUT, atlas.LAST)))
        # A-69: the men's anus, on the player's own BodyTalk 4 (Nude and Uncut) when it is installed. Optional: a
        # failure here says so and leaves the women's body to be written
        import male_anus
        men = {}

        def men_stage():
            got = male_anus.stage(game, work / 'men')
            if got is None:
                print("   BodyTalk 4 is not installed (its BodyTalk4.osp, Nude and Uncut files): no men's body")
            else:
                men.update(got)
        try:
            run_stage("9. the men's anus, on BodyTalk 4 (A-69)", men_stage)
        except Exception as e:                       # SystemExit included: the women's body still gets written
            men.clear()
            print(f"   the men's body was NOT built: {e}")
            traceback.print_exc()

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
        preset = work / 'AnatomyPreset.xml'
        preset.write_text(PRESET, encoding='utf-8')
        produced['Tools/BodySlide/SliderPresets/Anatomy.xml'] = preset
        # A-57: Anatomy's preset for THIS body; the engine reads it (before the shipped CBBE default) when the player has
        # no ocbp.ini of their own
        kind = '-3bbb' if on_3bbb else ''
        produced['F4SE/Plugins/Anatomy/ocbp-body.ini'] = PRESETS / f'ocbp-default{kind}.ini'
        produced['F4SE/Plugins/Anatomy/OCBPCollisionConfig-body.txt'] = PRESETS / f'OCBPCollisionConfig-default{kind}.txt'
        built = work / 'build.ini'
        built.write_text(stamp('3bbb' if on_3bbb else 'cbbe', breasts, game.read(theirs) if theirs else None),
                         encoding='utf-8')
        produced['F4SE/Plugins/Anatomy/build.ini'] = built
        if set(produced) != set(OUTPUTS):
            raise SystemExit('internal: the output list changed')
        produced.update(men)                            # A-69: the men's files (male_anus.OUTPUTS), when built
        dest =pathlib.Path(args.out) if args.out else data
        print(f'\n=== writing to {dest}')
        for rel, src in produced.items():
            target = dest / rel
            gamedata.make_dirs(target.parent)
            tmp = target.with_name(target.name + '.anatomy-new')
            shutil.copyfile(src, tmp)
            try:
                os.replace(tmp, target)                 # a crash never leaves half a file
            except OSError as e:
                # MO2's virtual Data can put the new file (its Overwrite) and the old one (a mod's folder) on two
                # drives, and a rename cannot cross drives (WinError 17, mb1205 2026-09-30): write it in place
                if getattr(e, 'winerror', None) != 17 and e.errno != errno.EXDEV:
                    raise
                shutil.copyfile(tmp, target)
                os.remove(tmp)
            print(f'   {rel}  sha1 {sha(target.read_bytes())}')
        ok = True
        print('\nDone. Now open BodySlide, choose the set "Anatomy Body", your preset, and Build (or Batch '
              'Build with "Anatomy Body" ticked). Re-run this builder after changing your CBBE, skin or physics preset (ocbp.ini).')
        if men:
            print('Men: build "Anatomy Male Body" (or "Anatomy Male Body Uncut") with your BodyTalk preset, in place of '
                  'BodyTalk4: the same body, with the anus opened.')
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
