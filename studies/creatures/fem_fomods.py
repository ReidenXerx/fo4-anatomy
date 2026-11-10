"""Immersive 1.1 FOMODs (Dudu 11-10: female creatures approved, 50 % of spawns): the 1.0 archive's steps + a
"Female ..." step (one checkbox, ON by default): the mod's female meshes, its light plugin and its RobCo Patcher
list. The dogs' wolf part installs only when Far Harbor (DLCCoast.esm) is active.
    python -I fem_fomods.py <out dir> [mod key ...]"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from creature_fomods import MM_LINE, MODS, SEVENZIP, image, option  # noqa: E402

FEM = pathlib.Path(r'D:\F4Output\creatures\fem')
SHOTS = FEM / 'review/_work/shots'
MESH = FEM / 'out/Data/meshes'
ROBCO_LINE = ('RobCo Patcher: check this yourself - it adds the female creatures to the spawn lists. Without it the '
              'female models still apply to creatures that are already female, but no new females spawn.')
# review shot index per creature (fem_renders.JOBS order) -> card tiles
SHOT = {'Raider dog': 0, 'Vicious dog': 1, 'Wolf': 2, 'FEV hound': 3, 'Yao guai': 4, 'Radstag doe': 5,
        'Mole rat': 6, 'Broodmother': 7}
FEMALE = {
    'dogs': dict(step='Female dogs, wolves and FEV hounds', robco=True,
                 parts=[('Dogs', ['Actors/Dogmeat/CharacterAssets/RaiderDog_F.nif',
                                  'Actors/ViciousDog/ViciousDog_F.nif', 'Actors/ViciousDog/ViciousDogPackLeader_F.nif',
                                  'Actors/FEVHound/CharacterAssets/FEVHound_F.nif'], None),
                        ('Wolves', ['Actors/DLC03/MutatedWolf/WolfAlpha_F.nif',
                                    'Actors/DLC03/MutatedWolf/WolfFuzzy_F.nif'], 'DLCCoast.esm')],
                 shots=['Raider dog', 'Vicious dog', 'Wolf', 'FEV hound'],
                 desc='Half of the raider dogs, vicious dogs, pack leaders, FEV hounds and Far Harbor wolves that spawn '
                      'are now female: a vulva under the tail and a row of teats along the belly, in each animal\'s own '
                      'fur. The wolves need Far Harbor.'),
    'yaoguai': dict(step='Female yao guai', robco=True,
                    parts=[('Yao Guai', ['Actors/YaoGuai/CharacterAssets/YaoGuai_F.nif',
                                         'Actors/YaoGuai/CharacterAssets/YaoGuaiShaggy_F.nif'], None)],
                    shots=['Yao guai'],
                    desc='Half of the yao guai that spawn are now female: a vulva under the tail with the fur parted '
                         'around it and three pairs of teats, on both yao guai bodies.'),
    'radstag': dict(step='Female radstags', robco=False,
                    parts=[('Radstags', ['Actors/RadStag/CharacterAssets/RadStagDoe_F.nif'], None)],
                    shots=['Radstag doe'],
                    desc='The radstag does the game already spawns get a vulva and a four-teat udder between the hind '
                         'legs. Fawns are left as they are.'),
    'molerat': dict(step='Female mole rats and the Broodmother', robco=True,
                    parts=[('Mole Rats', ['Actors/Molerat/CharacterAssets/Molerat_F.nif',
                                          'Actors/Molerat/CharacterAssets/Molerat01_F.nif',
                                          'Actors/Molerat/CharacterAssets/Molerat02_F.nif',
                                          'Actors/Molerat/CharacterAssets/Broodmother_F.nif'], None)],
                    shots=['Mole rat', 'Broodmother'],
                    desc='Half of the mole rats that spawn are now female, and the Broodmother is always female: a '
                         'vulva under the tail and teats along the belly, under the same dirt as the rest of the body.'),
}


def card(names, dst):
    tiles = []
    for n in names:
        for v in (f'v{SHOT[n]}_qback', f't{SHOT[n]}_close'):
            tiles.append(Image.open(SHOTS / f'{v}.png').convert('RGB').resize((450, 450)))
    cols = min(len(tiles), 4)
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGB', (cols * 450 + 8 * (cols - 1), rows * 450 + 8 * (rows - 1)), (40, 40, 42))
    for i, t in enumerate(tiles):
        im.paste(t, ((i % cols) * 458, (i // cols) * 458))
    image_tmp = dst.with_suffix('.png')
    im.save(image_tmp)
    image(image_tmp, dst)
    image_tmp.unlink()


def step(name, opts, kind='SelectAll'):
    return (f'    <installStep name="{escape(name)}">\n      <optionalFileGroups order="Explicit">\n'
            f'        <group name="{escape(name)}" type="{kind}">\n          <plugins order="Explicit">\n'
            f'{"".join(opts)}          </plugins>\n        </group>\n      </optionalFileGroups>\n    </installStep>\n')


def build(key, out, version='1.1.0'):
    m, f = MODS[key], FEMALE[key]
    stage = pathlib.Path(tempfile.mkdtemp(prefix=f'fomod-{key}-', dir=r'D:\F4Output'))
    shutil.copytree(m['src'], stage / 'Core')
    imgs = stage / 'fomod/images'
    checks = list(m['checks']) + ([ROBCO_LINE] if f['robco'] else []) + [MM_LINE]
    steps = [step('Checking your setup', [option('Your setup', '\n'.join(checks))])]
    for i, (fname, desc, src) in enumerate(m['features']):
        image(src, imgs / f'feature{i + 1}.jpg')
        steps.append(step(fname, [option(fname, desc, f'fomod/images/feature{i + 1}.jpg')]))
    shutil.copyfile(imgs / 'feature1.jpg', imgs / 'banner.jpg')
    Image.open(imgs / 'feature1.jpg').save(stage / 'fomod/screenshot.png')
    card(f['shots'], imgs / 'female.jpg')
    files, cond = '', ''
    for stem, meshes, master in f['parts']:
        d = stage / 'Female' / stem
        src = FEM / 'plugins' / stem
        for p in src.rglob('*'):
            if p.is_file():
                (d / p.relative_to(src)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, d / p.relative_to(src))
        for rel in meshes:
            (d / 'meshes' / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MESH / rel, d / 'meshes' / rel)
        if master is None:
            files += f'                <folder source="Female\\{stem}" destination="" priority="1"/>\n'
        else:
            cond += ('      <pattern>\n        <dependencies operator="And">\n'
                     '          <flagDependency flag="female" value="On"/>\n'
                     f'          <fileDependency file="{master}" state="Active"/>\n        </dependencies>\n'
                     f'        <files>\n          <folder source="Female\\{stem}" destination="" priority="1"/>\n'
                     '        </files>\n      </pattern>\n')
    opt = option(f['step'], f['desc'], 'fomod/images/female.jpg',
                 files=f'              <files>\n{files}              </files>\n',
                 flags='              <conditionFlags><flag name="female">On</flag></conditionFlags>\n',
                 typ='Recommended')
    steps.append(step(f['step'], [opt], kind='SelectAny'))
    cond = f'  <conditionalFileInstalls>\n    <patterns>\n{cond}    </patterns>\n  </conditionalFileInstalls>\n' \
        if cond else ''
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
           f'  <moduleName>{escape(m["name"])}</moduleName>\n  <moduleImage path="fomod/images/banner.jpg"/>\n'
           '  <requiredInstallFiles>\n    <folder source="Core" destination="" priority="0"/>\n'
           f'  </requiredInstallFiles>\n  <installSteps order="Explicit">\n{"".join(steps)}  </installSteps>\n'
           f'{cond}</config>\n')
    (stage / 'fomod/ModuleConfig.xml').write_bytes(b'\xef\xbb\xbf' + xml.encode('utf-8'))
    out.mkdir(parents=True, exist_ok=True)
    arc = out / f'{m["name"]} {version}.7z'
    if arc.exists():
        raise SystemExit(f'{arc} exists: use a fresh folder')
    r = subprocess.run([SEVENZIP, 'a', '-t7z', '-mx=7', str(arc), '*'], cwd=stage, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-600:] + r.stderr[-600:])
    listing = sorted(p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file())
    shutil.copyfile(imgs / 'female.jpg', out / f'{key}_female_card.jpg')
    shutil.rmtree(stage)
    return arc, listing


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    for k in (sys.argv[2:] or list(FEMALE)):
        arc, listing = build(k, out)
        print(f'{arc.name}: {len(listing)} files, {arc.stat().st_size / 1e6:.1f} MB;',
              [x for x in listing if x.startswith('Female')])
