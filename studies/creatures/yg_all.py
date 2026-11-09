"""Yao guai genitals (bear: furred sheath, no knot, furred scrotum), both meshes: canine_geom (noknot sack) ->
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
Y = pathlib.Path(r'D:\F4Output\creatures\yg')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\meshes')
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
PEN = ('Materials\\Anatomy\\Creatures\\CaninePenis.bgsm',
       ['textures\\Anatomy\\Creatures\\CaninePenis_d.dds', 'textures\\Anatomy\\Creatures\\CaninePenis_n.dds',
        'textures\\Anatomy\\Creatures\\CaninePenis_s.dds'])
JOBS = [('YaoGuai', 'yaoguai.nif', 'yaoguai:0'), ('YaoGuaiShaggy', 'yaoguaishaggy.nif', 'YaoGuaiShaggy:0')]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


for name, van, body in JOBS:
    uap = DATA / 'actors/yaoguai/characterassets' / f'{name}.nif'
    geom = Y / f'geom_{name}.json'
    o = run([sys.executable, '-I', str(HERE / 'canine_geom.py'), str(uap), 'YaoGuai_penis2', 'YaoGuai_balls2',
             str(uap.with_suffix('.tri')), str(Y / 'vanilla' / van), str(geom), 'noknot', 'sack'])
    print(name, [l for l in o.splitlines() if l.startswith(('penis', 'sheath', 'sack'))])
    exp = Y / 'build' / 'meshes/actors/yaoguai/characterassets' / f'{name}.nif'
    o = run([BL, '-b', '-P', str(HERE / 'canine_build.py'), '--', str(geom), str(Y / 'vanilla' / van), str(exp),
             'YaoGuai_penis2', 'YaoGuai_sheath', 'Pelvis', 'YaoGuai_balls2'])
    print([l for l in o.splitlines() if l.startswith(('BUILT', 'sheath fur', 'sack uv'))])
    print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(Y / 'vanilla' / van), str(exp), 'single'])[:200])
    run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(exp.with_suffix('.tri'))])
    dst = out / 'meshes/actors/yaoguai/characterassets' / f'{name}.nif'
    dst.parent.mkdir(parents=True, exist_ok=True)
    near = body
    info = transplant(Y / 'vanilla' / van, exp, dst,
                      {'YaoGuai_penis2': (body, PEN[0], PEN[1]), 'YaoGuai_sheath': (near, None, None),
                       'YaoGuai_balls2': (near, None, None)},
                      bodytri=f'Actors\\YaoGuai\\CharacterAssets\\{name}.tri')
    shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
    print(name, info['blocks'], info['shapes'][-3:])
src_tex = pathlib.Path(r'D:\F4Output\creatures\canine\out9\Data')
for top in ('textures', 'materials'):
    shutil.copytree(src_tex / top, out / top, dirs_exist_ok=True)
