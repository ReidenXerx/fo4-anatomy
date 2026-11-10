"""Review renders of the female creature meshes (vulva from behind, belly with teats) + one sheet per run.
    python -I fem_renders.py <out dir> [name ...]"""
import pathlib
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
C = pathlib.Path(r'D:\F4Output\creatures')
M = C / 'fem/out/Data/meshes/Actors'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
JOBS = {  # name: (nif, png dir with that body's textures)
    'Raider dog': (M / 'Dogmeat/CharacterAssets/RaiderDog_F.nif', C / 'canine/renderpng'),
    'Vicious dog': (M / 'ViciousDog/ViciousDog_F.nif', C / 'canine/renderpng'),
    'Wolf': (M / 'DLC03/MutatedWolf/WolfFuzzy_F.nif', None),
    'FEV hound': (M / 'FEVHound/CharacterAssets/FEVHound_F.nif', C / 'canine/renderpng'),
    'Yao guai': (M / 'YaoGuai/CharacterAssets/YaoGuai_F.nif', None),
    'Radstag doe': (M / 'RadStag/CharacterAssets/RadStagDoe_F.nif', None),
    'Mole rat': (M / 'Molerat/CharacterAssets/Molerat_F.nif', None),
    'Broodmother': (M / 'Molerat/CharacterAssets/Broodmother_F.nif', None),
}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        raise SystemExit((r.stdout + r.stderr)[-1500:])
    return r.stdout


out = pathlib.Path(sys.argv[1])
names = sys.argv[2:] or list(JOBS)
work = out / '_work'
work.mkdir(parents=True, exist_ok=True)
nifs = [str(JOBS[n][0]) for n in names]
run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'list', work / 'tex.json', *nifs])
png = work / 'png'
run([sys.executable, '-I', HERE / 'feral_tex_prep.py', work / 'tex.json', png, C / 'canine/out9/Data'])
for d in (C / 'canine/renderpng', C / 'yg/renderpng', C / 'rs/renderpng', C / 'mr/renderpng'):
    for p in d.glob('*.png'):
        if not (png / p.name).exists():
            shutil.copyfile(p, png / p.name)
shots = work / 'shots'
if shots.exists():
    shutil.rmtree(shots)
import json  # noqa: E402
import numpy as np  # noqa: E402
KEY = {'Raider dog': 'raiderdog', 'Vicious dog': 'viciousdog', 'Wolf': 'wolffuzzy', 'FEV hound': 'fevhound',
       'Yao guai': 'yaoguai', 'Radstag doe': 'radstagdoe', 'Mole rat': 'molerat', 'Broodmother': 'broodmother'}
items = []
for i, n in enumerate(names):
    items.append(f'v{i}|{JOBS[n][0]}|qback|FOCUS=vulva;RAW=1')
    T = np.array(json.load(open(C / 'fem' / f'geom_{KEY[n]}.json'))['FemTeats']['verts'])
    ys = sorted({round(y, 0) for y in T[:, 1]})
    rear = T[T[:, 1] < T[:, 1].min() + (T[:, 1].max() - T[:, 1].min()) * 0.25]      # the rear pair(s)
    c = rear.mean(0)
    sc = max(rear[:, 0].max() - rear[:, 0].min(), 4) * 2.6
    items.append(f't{i}|{JOBS[n][0]}|qside,pt={c[0]:.2f}/{c[1]:.2f}/{c[2]:.2f}/60/-45/{sc:.2f}/close|FOCUS=teat;RAW=1')
run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'render', png, shots, *items])
tiles = []
for i, n in enumerate(names):
    row = [Image.open(shots / f'{p}.png').convert('RGB').resize((420, 420))
           for p in (f'v{i}_qback', f't{i}_qside', f't{i}_close')]
    tiles.append((n, row))
sheet = Image.new('RGB', (3 * 424, len(tiles) * 446), (30, 30, 32))
d = ImageDraw.Draw(sheet)
for r, (n, row) in enumerate(tiles):
    for c, im in enumerate(row):
        sheet.paste(im, (c * 424, r * 446 + 24))
    d.text((6, r * 446 + 4), f'{n} (female): vulva from behind | belly from the side | rear teats close', fill=(235, 235, 235))
sheet.save(out / 'female_creatures_review.jpg', quality=88)
print('sheet', out / 'female_creatures_review.jpg')
