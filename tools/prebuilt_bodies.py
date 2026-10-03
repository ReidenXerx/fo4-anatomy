"""Prebuilt bodies for the Anatomy page (A-72, the owner 2026-10-03): CBBE and 3BBB women and BodyTalk 4 men, built at
ZEROED sliders with their .tri morphs, so LooksMenu BodyGen / Silhouette shape them in game.

    python tools/prebuilt_bodies.py [--data <Fallout 4 Data>] [--out D:/F4Output/Prebuilt]
        -> <out>/stage/<part>/...      one Data-relative tree per installer part (women-cbbe, women-3bbb, men, men-uncut)

Per women's body: the AnatomyBuilder on the given Data (--body cbbe / 3bbb), BodySlide in the LAB at "CBBE Zeroed
Sliders" with --trimorphs, the neck seam (A-37) on the built mesh, and the builder's physics preset for that body
(ocbp-body.ini, its collision, build.ini). The genitals' texture is baked from CBBE's OWN skin (its loose
FemaleBody_d/n/s.dds under the vanilla material), not from whatever skin this Data has installed: the default most
players have. Men: the builder's "Anatomy Male Body" and "... Uncut" sets at "BT - Zero" with --trimorphs (BodyTalk
4's own textures, nothing of ours to bake).
The LAB's own set files are put back afterwards. BodySlide's window steals focus: run it only when the game's holder
said "free". Nothing third-party enters the repo (A-2): this tool is committed, its outputs are not.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import garments      # noqa: E402
import gamedata      # noqa: E402
import neck_seam     # noqa: E402
import nif           # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAB = pathlib.Path(r'D:\F4Output\AnatomyLab\BodySlide')
CBBE_MOD = pathlib.Path(r"D:\Vortex\fallout4\mods\Caliente's Beautiful Bodies Enhancer - v2.7.2-15-2-7-2-1766404952")
SKIN_MATERIAL = 'Materials/actors/Character/BaseHumanFemale/basehumanFemaleskin.bgsm'
ASSETS = 'Meshes/Actors/Character/CharacterAssets'
WOMEN_FILES = ('Materials/Anatomy/AnatomyGenitals.bgsm', 'F4SE/Plugins/Anatomy/ocbp-body.ini',
               'F4SE/Plugins/Anatomy/OCBPCollisionConfig-body.txt', 'F4SE/Plugins/Anatomy/build.ini')
SWAP = ('SliderSets/Anatomy.osp', 'SliderSets/AnatomyMale.osp', 'ShapeData/Anatomy', 'ShapeData/AnatomyMale',
        'SliderCategories/Anatomy.xml')


def run_builder(data, out, body):
    # CBBE: as for a player with no preset of their own (another preset is incompatible), so its breasts go onto
    # LBreast_skin/RBreast_skin as Anatomy's CBBE preset drives them; 3BBB: 3BBB's own preset and Anatomy's 3BBB one
    # both drive 3BBB's breast bones, so this Data's preset is fine
    extra = ['--no-player-preset'] if body == 'cbbe' else []
    r = subprocess.run([sys.executable, str(ROOT / 'tools/builder.py'), '--data', str(data), '--out', str(out),
                        '--body', body] + extra, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    log = r.stdout + r.stderr
    (out.parent / f'builder-{body}.log').write_text(log, encoding='utf-8')
    if 'Done.' not in log:
        raise SystemExit(f'the builder ({body}) did not finish; log {out.parent / f"builder-{body}.log"}')
    print(f'builder {body}:', '; '.join(l.strip() for l in log.splitlines() if l.strip().startswith(('body:', 'breasts:'))))


def cbbe_skin_textures(work, game):
    """the genitals' maps and material baked from CBBE's own skin: a small Data with the vanilla material and CBBE's
    loose body maps, through the texture stage alone"""
    import genital_texture as gt
    data = work / 'cbbe_skin_data'
    shutil.rmtree(data, ignore_errors=True)
    base = next(gamedata.Ba2(a) for a in game.archives if pathlib.Path(a).name.lower() == 'fallout4 - materials.ba2')
    (data / SKIN_MATERIAL).parent.mkdir(parents=True, exist_ok=True)
    (data / SKIN_MATERIAL).write_bytes(base.read(SKIN_MATERIAL))
    src = CBBE_MOD / 'textures/actors/character/basehumanfemale'
    dst = data / 'Textures/Actors/Character/BaseHumanFemale'
    dst.mkdir(parents=True, exist_ok=True)
    for m in ('FemaleBody_d.dds', 'FemaleBody_n.dds', 'FemaleBody_s.dds'):
        f = next(p for p in src.iterdir() if p.name.lower() == m.lower())
        shutil.copy2(f, dst / m)
    gt.ANATOMY_OUT = work / 'cbbe_skin_out'
    gt.main(data)
    return gt.ANATOMY_OUT


def bodyslide(builder_out, sets, preset, target):
    """build `sets` (set names) from the builder's project in the LAB at `preset` with morphs into target"""
    bs = builder_out / 'Tools/BodySlide'
    backup = target.parent / f'lab_backup_{target.name}'
    shutil.rmtree(backup, ignore_errors=True)
    for rel in SWAP:
        src = LAB / rel
        if src.exists():
            (backup / rel).parent.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, backup / rel)
    group = 'PrebuiltBodies'
    try:
        for rel in SWAP:
            if (bs / rel).exists():
                if (LAB / rel).is_dir():
                    shutil.rmtree(LAB / rel)
                (shutil.copytree if (bs / rel).is_dir() else shutil.copy2)(bs / rel, LAB / rel)
        (LAB / f'SliderGroups/{group}.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<SliderGroups>\n    <Group name="PrebuiltBodies">\n'
            + ''.join(f'        <Member name="{s}"/>\n' for s in sets) + '    </Group>\n</SliderGroups>\n', encoding='utf-8')
        shutil.rmtree(target, ignore_errors=True)
        rr, answered = garments.run_bodyslide([str(LAB / 'BodySlide.exe'), '--groupbuild', group, '--targetdir',
                                               str(target), '--preset', preset, '--trimorphs'], LAB, 1800)
        print(f'BodySlide {sets} at "{preset}": exit {rr.returncode}', answered or '')
    finally:
        (LAB / f'SliderGroups/{group}.xml').unlink(missing_ok=True)
        for rel in SWAP:
            if (LAB / rel).exists() and not (backup / rel).exists():
                (shutil.rmtree if (LAB / rel).is_dir() else pathlib.Path.unlink)(LAB / rel)
            if (backup / rel).exists():
                if (LAB / rel).is_dir():
                    shutil.rmtree(LAB / rel)
                (shutil.copytree if (backup / rel).is_dir() else shutil.copy2)(backup / rel, LAB / rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=r'D:\SteamFreeGames\Fallout 4 AE\Data')
    ap.add_argument('--out', default=r'D:\F4Output\Prebuilt')
    ap.add_argument('--parts', default='women-cbbe,women-3bbb,men', help='which to (re)build')
    a = ap.parse_args()
    parts = set(a.parts.split(','))
    data, out = pathlib.Path(a.data), pathlib.Path(a.out)
    if b'Fallout4.exe' in subprocess.run(['tasklist'], capture_output=True).stdout:
        raise SystemExit('the game is running: BodySlide would steal its focus; ask its holder for "free" first')
    game = gamedata.Game(data)
    work = out / 'work'
    work.mkdir(parents=True, exist_ok=True)
    stage = out / 'stage'
    for p in parts | ({'men-uncut'} if 'men' in parts else set()):
        shutil.rmtree(stage / p, ignore_errors=True)
    skin = cbbe_skin_textures(work, game)
    pieces = []
    for name, rel in (('_head.nif', neck_seam.HEAD_MESH), ('_headrear.nif', neck_seam.REAR_MESH)):
        try:
            p = work / name
            p.write_bytes(game.read(rel))
            pieces.append(p)
        except FileNotFoundError:
            pass
    for body in ('cbbe', '3bbb'):
        if f'women-{body}' not in parts and not (body == 'cbbe' and 'men' in parts):
            continue
        b = work / f'builder_{body}'
        shutil.rmtree(b, ignore_errors=True)
        run_builder(data, b, body)
        built = work / f'built_{body}'
        bodyslide(b, ['Anatomy Body'], 'CBBE Zeroed Sliders', built)
        nifp, tri = next(built.rglob('FemaleBody.nif')), next(built.rglob('FemaleBody.tri'))
        neck_seam.apply(nifp, pieces)
        part = stage / f'women-{body}'
        (part / ASSETS).mkdir(parents=True)
        shutil.copy2(nifp, part / ASSETS / 'FemaleBody.nif')
        shutil.copy2(tri, part / ASSETS / 'FemaleBody.tri')
        for rel in WOMEN_FILES[1:]:
            (part / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(b / rel, part / rel)
        for m in ('FemaleBody_d.dds', 'FemaleBody_n.dds', 'FemaleBody_s.dds'):
            (part / 'Textures/Anatomy').mkdir(parents=True, exist_ok=True)
            shutil.copy2(skin / m, part / 'Textures/Anatomy' / m)
        (part / 'Materials/Anatomy').mkdir(parents=True, exist_ok=True)
        shutil.copy2(skin / 'AnatomyGenitals.bgsm', part / 'Materials/Anatomy/AnatomyGenitals.bgsm')
        n = nif.Nif(part / ASSETS / 'FemaleBody.nif')
        print(f'women-{body}:', [(s.name, s.count) for s in n.shapes()])
        if body == 'cbbe' and 'men' in parts:
            for sets, name in ((['Anatomy Male Body'], 'men'), (['Anatomy Male Body Uncut'], 'men-uncut')):
                mb = work / f'built_{name}'
                bodyslide(b, sets, 'BT - Zero', mb)
                part = stage / name
                (part / ASSETS).mkdir(parents=True)
                shutil.copy2(next(mb.rglob('MaleBody.nif')), part / ASSETS / 'MaleBody.nif')
                shutil.copy2(next(mb.rglob('MaleBody.tri')), part / ASSETS / 'MaleBody.tri')
                n = nif.Nif(part / ASSETS / 'MaleBody.nif')
                print(f'{name}:', [(s.name, s.count) for s in n.shapes()])
    print('staged:', ', '.join(sorted(p.name for p in stage.iterdir())))


if __name__ == '__main__':
    main()
