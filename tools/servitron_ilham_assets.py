"""Ilham's penis textures + material for Anatomy Servitron (2026-11-22, Dudu's approval via Watcher; her own Substance
exports from D:\\F4Output\\ilham-robot). Nothing of hers enters git: this tool is committed, its outputs are not.

    python tools/servitron_ilham_assets.py <MouthCockTextures folder> <Servitron default__abdomenring.bgsm> <out Data>
        -> <out>/Textures/Anatomy/Servitron/Ilham/Penis_d.dds (the Assaultron colour), Penis_<Colour>_d.dds (the others),
           Penis_n.dds, Penis_s.dds; <out>/Materials/Anatomy/Servitron/IlhamPenis.bgsm (Servitron's own ring material,
           our textures)
Maps at 2K. _d BC7; _n BC5 linear (--ignore-srgb: a colour-managed normal map decodes flat, shared memory
normal-maps-srgb-55-not-128); _s = specular (R, from metallic: 0.15 plastic .. 1.0 metal) + gloss (G, 1 - roughness), BC5.
"""
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bgsm  # noqa: E402

TEXCONV = r'D:\F4Tools\texconv\texconv.exe'
SIZE = 2048
REL = 'Anatomy/Servitron/Ilham'


def texconv(src, out_dir, fmt, extra=()):
    r = subprocess.run([TEXCONV, '-nologo', '-y', '-f', fmt, '-w', str(SIZE), '-h', str(SIZE), '-m', '0', *extra,
                        '-o', str(out_dir), str(src)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'texconv {src}: {r.stdout}{r.stderr}')


def main():
    src, template, out = (pathlib.Path(a) for a in sys.argv[1:4])
    tex = out / 'Textures' / REL
    tex.mkdir(parents=True, exist_ok=True)
    work = out.parent / '_work'
    work.mkdir(parents=True, exist_ok=True)
    for colour in ('Assaultron', 'Ada', 'Nuke', 'Vex'):
        name = 'Penis_d' if colour == 'Assaultron' else f'Penis_{colour}_d'
        Image.open(src / f'{colour}Clr_BaseColor.png').convert('RGB').save(work / f'{name}.png')
        texconv(work / f'{name}.png', tex, 'BC7_UNORM')
    n = np.asarray(Image.open(src / 'PenMth_NormalMap.png').convert('RGB'))
    med = np.median(n.reshape(-1, 3), axis=0)
    if abs(med[0] - 128) > 8 or abs(med[1] - 128) > 8:
        raise SystemExit(f'normal map median {med}: not a flat-centred linear normal map')
    Image.fromarray(n).save(work / 'Penis_n.png')
    texconv(work / 'Penis_n.png', tex, 'BC5_UNORM', ['--ignore-srgb'])
    metal = np.asarray(Image.open(src / 'PenMth_Metallic.png')).astype(np.float32)
    metal = metal / (65535.0 if metal.max() > 255 else 255.0)
    if metal.ndim == 3:
        metal = metal[..., 0]
    rough = np.asarray(Image.open(src / 'PenMth_Roughness.png').convert('L')).astype(np.float32) / 255.0
    spec = np.clip(0.15 + 0.85 * metal, 0, 1)
    gloss = np.clip(1.0 - rough, 0, 1)
    s = np.stack([spec, gloss, np.zeros_like(spec)], axis=-1)
    Image.fromarray((s * 255 + 0.5).astype(np.uint8)).save(work / 'Penis_s.png')
    texconv(work / 'Penis_s.png', tex, 'BC5_UNORM', ['--ignore-srgb'])
    mat = bgsm.with_textures(template.read_bytes(), {'diffuse': f'{REL}/Penis_d.dds', 'normal': f'{REL}/Penis_n.dds',
                                                      'smoothspec': f'{REL}/Penis_s.dds'})
    (out / 'Materials/Anatomy/Servitron').mkdir(parents=True, exist_ok=True)
    (out / 'Materials/Anatomy/Servitron/IlhamPenis.bgsm').write_bytes(mat)
    print('textures:', sorted(p.name for p in tex.iterdir()))
    print('material:', bgsm.textures(mat)[0][:3], 'normal median', med)


if __name__ == '__main__':
    main()
