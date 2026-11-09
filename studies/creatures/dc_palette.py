"""Deathclaw body texture: extract deathclaw_d/_n, and print colour stats around the vent's body UVs (our lips take
those UVs) + a crop for the eye.  python -I dc_palette.py"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_common as gc  # noqa: E402

D = pathlib.Path(r'D:\F4Output\creatures\dc\tex')
D.mkdir(parents=True, exist_ok=True)
b = gamedata.Ba2(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Fallout4 - Textures1.ba2'))
for k in ('d', 'n'):
    (D / f'deathclaw_{k}.dds').write_bytes(b.read(f'textures\\actors\\deathclaw\\deathclaw_{k}.dds'))
img = gc.dds_to_array(D / 'deathclaw_d.dds', D / 'work')[..., :3].astype(np.float32) / 255
H, W = img.shape[:2]
print('deathclaw_d', W, H)
G = json.load(open(r'D:\F4Output\creatures\dc\geom_male.json'))
uv = np.array(G['Base']['uv'])
print('lips uv range', uv.min(0).round(3), uv.max(0).round(3))
px = np.clip((uv * [W, H]).astype(int), 0, [W - 1, H - 1])
c = img[px[:, 1], px[:, 0]]
print('lips texels mean', c.mean(0).round(3), 'p10', np.percentile(c, 10, 0).round(3), 'p90', np.percentile(c, 90, 0).round(3))
u0, v0 = (uv.min(0) * [W, H]).astype(int) - 40
u1, v1 = (uv.max(0) * [W, H]).astype(int) + 40
Image.fromarray((img[max(v0, 0):v1, max(u0, 0):u1] * 255).astype(np.uint8)).resize((400, 400)).save(D / 'vent_crop.png')
Image.fromarray((img * 255).astype(np.uint8)).resize((512, 512)).save(D / 'deathclaw_d_small.png')
