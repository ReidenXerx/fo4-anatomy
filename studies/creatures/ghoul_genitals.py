"""Ghoul genitals for women (owner 11-09 via Watcher): Anatomy's genital shape has its own texture
(Textures\\Anatomy\\FemaleBody_d/n/s, material Materials\\Anatomy\\AnatomyGenitals.bgsm), so ghouls show human skin there.
This makes Textures\\Anatomy\\Ghoul\\FemaleBody_* : the human genital texture recoloured by the ghoul/human body tone
ratio at the nearest body point (blurred, so it moves tone, not detail), then the same 3D disgust field as the body,
so the crotch seam matches the new ghoul body.
    python -I ghoul_genitals.py"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ghoul_build as gb  # noqa: E402
import ghoul_common as gc  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
AN = DATA / 'Textures/Anatomy'
HUMAN_BODY = DATA / 'textures/actors/character/custombody/FemaleBody_d.dds'
GHOUL_BODY_OLD = gb.HR / 'custombody/ghoulfemalebody_d.dds'
TONE = 1024                   # body textures are sampled for TONE only, at this size, blurred


def tone_map(path, shapes):
    a = gc.dds_to_array(path, gc.ROOT / 'work' / 'dec_tone' / pathlib.Path(path).parent.name)
    im = Image.fromarray(a[..., :3]).resize((TONE, TONE), Image.BOX).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(im, np.float32) / 255.0


def make_prep(shapes):
    body = shapes['body']
    bpos, btag, _ = gc.rasterize(TONE, [(body['uv'], body['tri'], body['world'], 0)])
    cov = btag >= 0
    tree = cKDTree(bpos[cov])
    cy, cx = np.nonzero(cov)
    human = tone_map(HUMAN_BODY, shapes)[cy, cx]
    ghoul = tone_map(GHOUL_BODY_OLD, shapes)[cy, cx]

    def prep(srcs, full, covered):
        d = srcs['d'].astype(np.float32) / 255.0
        sz = d.shape[0]
        p = full if full.shape[0] == sz else np.stack([gb.resize(full[..., i], sz) for i in range(3)], -1)
        dist, idx = tree.query(p.reshape(-1, 3))
        g = d[..., :3].reshape(-1, 3)
        lw = np.array([0.3, 0.55, 0.15], np.float32)
        # hue swap, not a ratio: the ghoul body's colour at the nearest body point, carrying the genital texture's
        # own light/dark detail (relative to the human skin there). A ratio left the pink mucosa pink (11-09 render)
        detail = np.clip((g @ lw) / np.maximum(human[idx] @ lw, 0.03), 0.3, 1.15)[:, None]
        rgb = ghoul[idx] * detail * 0.88
        # the pinkest, wettest parts (mucosa, canal): necrotic maroon-purple instead of healthy pink
        mucosa = np.clip((g[:, 0] - g[:, 1] - 0.07) / 0.14, 0, 1)[:, None]
        rgb = rgb + (np.array([0.36, 0.13, 0.15], np.float32) * detail ** 0.7 - rgb) * (0.8 * mucosa)
        rgb = np.clip(rgb, 0, 1).reshape(sz, sz, 3)
        print(f'   hue swap: nearest body point median {np.median(dist):.2f} units, max {dist.max():.2f}; '
              f'mucosa texels {float((mucosa > 0.5).mean()) * 100:.1f}%')
        srcs['d'] = np.concatenate([(rgb * 255 + 0.5).astype(np.uint8), srcs['d'][..., 3:]], -1)
    return prep


def main():
    shapes = gb.shapes_in_body_space('F')
    tex = dict(name='F genitals', layers=['genitals'], islands_only=False, prep=make_prep(shapes), maps={
        'd': (AN / 'FemaleBody_d.dds', 'textures/anatomy/ghoul/femalebody_d.dds', 'BC1_UNORM'),
        'n': (AN / 'FemaleBody_n.dds', 'textures/anatomy/ghoul/femalebody_n.dds', 'BC5_UNORM'),
        's': (AN / 'FemaleBody_s.dds', 'textures/anatomy/ghoul/femalebody_s.dds', 'BC5_UNORM')})
    gb.build(tex, shapes, 1109, 1.0, set())


if __name__ == '__main__':
    main()
