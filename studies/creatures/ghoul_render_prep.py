"""Inputs for the offline Blender renders: OBJ per ghoul mesh (body space, Blender units = game units / 64 not needed:
the camera is set from the bounds) and render-ready PNGs for BEFORE (the textures the game shows today) and AFTER
(our DDS, decoded back from BC so the renders show what ships). Normals -> full XYZ, OpenGL green for Blender;
_s -> spec (R) and roughness (1 - G).
    python -I ghoul_render_prep.py"""
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ghoul_build as gb  # noqa: E402
import ghoul_common as gc  # noqa: E402

R = gc.ROOT / 'render'


def write_obj(path, shape):
    with open(path, 'w', encoding='ascii') as f:
        for x, y, z in shape['world']:
            f.write(f'v {x:.5f} {y:.5f} {z:.5f}\n')
        for u, v in shape['uv']:
            f.write(f'vt {u:.6f} {1 - v:.6f}\n')
        for a, b, c in shape['tri'] + 1:
            f.write(f'f {a}/{a} {b}/{b} {c}/{c}\n')


def render_maps(kind, rgba, out):
    a = rgba.astype(np.float32) / 255.0
    if kind == 'd':
        img = a[..., :3]
    elif kind == 'n':
        x, y = a[..., 0] * 2 - 1, a[..., 1] * 2 - 1
        z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
        img = np.stack([x, -y, z], -1) * 0.5 + 0.5           # DirectX -> OpenGL green
    else:
        spec, gloss = a[..., 0], a[..., 1]
        img = np.stack([spec, 1 - gloss, np.zeros_like(spec)], -1)   # R spec, G roughness
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(out)


def main():
    (R / 'obj').mkdir(parents=True, exist_ok=True)
    for sex in ('F', 'M'):
        shapes = gb.shapes_in_body_space(sex)
        for key in ('body', 'hands', 'head', 'rear') + (('genitals',) if sex == 'F' else ()):
            write_obj(R / 'obj' / f'{sex}_{key}.obj', shapes[key])
        for tex in gb.TEXTURES[sex]:
            for kind, (src, rel, _) in tex['maps'].items():
                tag = tex['name'].replace(' ', '_')
                for when, path in (('before', src), ('after', gb.OUT / rel)):
                    (R / when).mkdir(parents=True, exist_ok=True)
                    rgba = gc.dds_to_array(path, gc.ROOT / 'work' / f'dec_{when}_{tag}')
                    render_maps(kind, rgba, R / when / f'{tag}_{kind}.png')
        if sex == 'F':                       # genitals: today the human texture, after = our ghoul copy
            an = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data\Textures\Anatomy')
            for kind in 'dns':
                for when, path in (('before', an / f'FemaleBody_{kind}.dds'),
                                   ('after', gb.OUT / f'textures/anatomy/ghoul/femalebody_{kind}.dds')):
                    rgba = gc.dds_to_array(path, gc.ROOT / 'work' / f'dec_{when}_F_genitals')
                    render_maps(kind, rgba, R / when / f'F_genitals_{kind}.png')
        print(sex, 'ready')


if __name__ == '__main__':
    main()
