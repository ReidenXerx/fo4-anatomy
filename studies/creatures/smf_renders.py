"""Review sheet for the female super mutant: the bare body (front, side, three-quarter, crotch) and every armour set
on her (front + three-quarter), armour from smf_refit's body-space previews (RAW=1 throughout).
    python -I smf_renders.py <out dir>"""
import pathlib
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

S = pathlib.Path(r'C:\Users\DuduPhudu\AppData\Local\Temp\claude\91d5ea4d77dbd0b4\f4e4cb45-4d12-44cf-946e-4ccea9c60a1e'
                 r'\scratchpad')
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
F = pathlib.Path(r'D:\F4Output\creatures\smf')
BODY = F / 'out/Data/meshes/Actors/Supermutant/CharacterAssets/SupermutantBody_F.nif'
PV = F / 'out/_preview'
SETS = {'Armour 0': ['SMArmor0_Torso', 'SMArmor0_Arms'], 'Armour 1 (full)': ['SMArmor1'],
        'Armour 1': ['SMArmor1_Torso', 'SMArmor1_Arms', 'SMArmor1_Lower'],
        'Armour 2': ['SMArmor2_Torso', 'SMArmor2_Arms', 'SMArmor2_Lower'], 'Armour 3': ['SMArmor3_Torso'],
        'Rags 1': ['SMRags1_Torso', 'SMRags1_Lower'], 'Rags 2': ['SMRags2_Torso', 'SMRags2_Arms'],
        'Suicide chains': ['SuicideChains']}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        raise SystemExit((r.stdout + r.stderr)[-1500:])


out = pathlib.Path(sys.argv[1])
work = out / '_work'
work.mkdir(parents=True, exist_ok=True)
nifs = [str(BODY)] + [str(PV / f'{n}_F.nif') for v in SETS.values() for n in v]
run([BL, '-b', '-P', S / 'feral_tex_render.py', '--', 'list', work / 'tex.json', *nifs])
png = work / 'png'
run([sys.executable, '-I', S / 'feral_tex_prep.py', work / 'tex.json', png, r'D:\F4Output\creatures\canine\out9\Data'])
for p in pathlib.Path(r'D:\F4Output\creatures\sm\renderpng').glob('*.png'):
    if not (png / p.name).exists():
        shutil.copyfile(p, png / p.name)
shots = work / 'shots'
if shots.exists():
    shutil.rmtree(shots)
items = [f'body|{BODY}|pt=0/0/-60/0/0/170/front,pt=0/0/-35/90/0/80/side,pt=0/0/-35/35/0/75/q,'
         f'pt=0/8/-62/0/-35/26/crotch|RAW=1;EXP=3']
for i, (k, v) in enumerate(SETS.items()):
    path = '+'.join([str(BODY)] + [str(PV / f'{n}_F.nif') for n in v])
    items.append(f's{i}|{path}|pt=0/0/-45/0/0/110/front,pt=0/0/-35/40/0/80/q|RAW=1;EXP=3')
run([BL, '-b', '-P', S / 'feral_tex_render.py', '--', 'render', png, shots, *items])
T = 400
rows = [('Female super mutant', [f'body_{v}' for v in ('front', 'side', 'q', 'crotch')])]
pairs = [(k, [f's{i}_front', f's{i}_q']) for i, k in enumerate(SETS)]
for a in range(0, len(pairs), 2):
    chunk = pairs[a:a + 2]
    rows.append((' | '.join(k for k, _ in chunk), [x for _, v in chunk for x in v]))
sheet = Image.new('RGB', (4 * (T + 4), len(rows) * (T + 26)), (30, 30, 32))
d = ImageDraw.Draw(sheet)
for r, (label, names) in enumerate(rows):
    d.text((6, r * (T + 26) + 5), label, fill=(235, 235, 235))
    for c, n in enumerate(names):
        sheet.paste(Image.open(shots / f'{n}.png').convert('RGB').resize((T, T)), (c * (T + 4), r * (T + 26) + 24))
sheet.save(out / 'female_super_mutant_review.jpg', quality=88)
print('sheet', out / 'female_super_mutant_review.jpg')
