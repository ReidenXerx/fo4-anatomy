"""Mole rat genitals (rodent: prepuce sheath, no knot, scrotum): canine_geom (noknot sack) ->
canine_build (penis + sheath + sack) -> seg_fix single -> tri normalize -> transplant onto VANILLA bodies.
    python -I yg_all.py <out Data>"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from transplant import transplant  # noqa: E402

out = pathlib.Path(sys.argv[1])
Y = pathlib.Path(r'D:\F4Output\creatures\mr')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes')
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
PEN = ('Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
       ['textures\\Anatomy\\Creatures\\CaninePenis_d.dds', 'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
        'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])
JOBS = [('Molerat', 'molerat.nif', 'Molerat:0'), ('Molerat01', 'molerat01.nif', 'Molerat01:0'),   # 01/02: armored
        ('Molerat02', 'molerat02.nif', 'Molerat02:0')]                                            # variants (run 7)
# the reference = darthroman's AAF creature pack in its staging folder (NOT the deployed Data: ours wins there now)
REF = pathlib.Path(r'D:\Vortex\fallout4\mods\AAF_darthroman_creature_pack_v1.0.7\Meshes\Actors\Molerat\CharacterAssets')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


for name, van, body in JOBS:
    uap = REF / f'{name}.nif'
    geom = Y / f'geom_{name}.json'
    o = run([sys.executable, '-I', str(HERE / 'canine_geom.py'), str(uap), 'Molerat_Penis002', 'Molerat_Balls',
             str(uap.with_suffix('.tri')), str(Y / 'vanilla' / van), str(geom), 'noknot', 'sack'])
    print(name, [l for l in o.splitlines() if l.startswith(('penis', 'sheath', 'sack'))])
    exp = Y / 'build' / 'meshes/actors/molerat/characterassets' / f'{name}.nif'
    o = run([BL, '-b', '-P', str(HERE / 'canine_build.py'), '--', str(geom), str(Y / 'vanilla' / van), str(exp),
             'Molerat_Penis002', 'Molerat_Sheath', 'Pelvis', 'Molerat_Balls'])
    print([l for l in o.splitlines() if l.startswith(('BUILT', 'sheath fur', 'sack uv'))])
    print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(Y / 'vanilla' / van), str(exp), 'single'])[:200])
    run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(exp.with_suffix('.tri'))])
    dst = out / 'meshes/actors/molerat/characterassets' / f'{name}.nif'
    dst.parent.mkdir(parents=True, exist_ok=True)
    near = body
    info = transplant(Y / 'vanilla' / van, exp, dst,
                      {'Molerat_Penis002': (body, PEN[0], PEN[1]), 'Molerat_Sheath': (near, None, None),
                       'Molerat_Balls': (near, None, None)},
                      bodytri=f'Actors\\Molerat\\CharacterAssets\\{name}.tri')
    shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
    print(name, info['blocks'], info['shapes'][-3:])
src_tex = pathlib.Path(r'D:\F4Output\creatures\canine\out9\Data')
for top in ('textures', 'materials'):
    shutil.copytree(src_tex / top, out / top, dirs_exist_ok=True)
