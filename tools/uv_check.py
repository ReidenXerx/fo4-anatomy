"""Where Nahka's genital geometry samples the body texture, drawn over the owner's texture and hers.

The new vertices' UVs do not continue the crotch skin's UV island: measured, a new vertex's UV lies
~0.92 from its nearest skin vertex's UV, in a corner of the atlas (u 0.2-0.45, v 0.85-1.0) CBBE does
not use for the crotch. Whatever the skin texture has there is what the vulva and canals show.
This renders that region from each texture with the new triangles' UV edges on top.

    python tools/uv_check.py   -> build/uv/<texture>.png
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw

import align_body as ab
import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uv'
TEXTURES = {
    'owner': ab.DEFAULT_DATA / 'Textures/Actors/Character/BaseHumanFemale/FemaleBody_d.dds',
    'nahka': ROOT / 'build/nahka_tex/Data/Body Textures/Textures/Actors/Character/BaseHumanFemale/femalebody_d.dds',
}
REGION = (0.15, 0.80, 0.55, 1.0)       # u0, v0, u1, v1


def main():
    body = nif.Nif(ab.OUT / 'ShapeData/AnatomyBodyZeX/AnatomyBodyZeX.nif')
    s = body.shape(ab.SHAPE)
    mapping = {int(j) for j in json.loads((ab.OUT / 'mapping.json').read_text())['output_to_cbbe']}
    new = {j for j in range(s.count) if j not in mapping}
    tris = [t for t in s.triangles() if any(v in new for v in t)]
    uvs = {v: s.uv(v) for t in tris for v in t}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in TEXTURES.items():
        if not path.exists():
            print(f'{name}: missing {path}')
            continue
        img = Image.open(path).convert('RGB')
        w, h = img.size
        u0, v0, u1, v1 = REGION
        box = (int(u0 * w), int(v0 * h), int(u1 * w), int(v1 * h))
        crop = img.crop(box).resize(((box[2] - box[0]) * 1024 // (box[2] - box[0]),
                                     (box[3] - box[1]) * 1024 // (box[2] - box[0])))
        sx, sy = crop.size[0] / (box[2] - box[0]), crop.size[1] / (box[3] - box[1])
        d = ImageDraw.Draw(crop)
        for t in tris:
            pts = [((uvs[v][0] * w - box[0]) * sx, (uvs[v][1] * h - box[1]) * sy) for v in t]
            d.line(pts + [pts[0]], fill=(255, 0, 0), width=1)
        crop.save(OUT / f'{name}.png')
        whole = img.resize((1024, 1024))
        dw = ImageDraw.Draw(whole)
        for t in tris:
            pts = [(uvs[v][0] * 1024, uvs[v][1] * 1024) for v in t]
            dw.line(pts + [pts[0]], fill=(255, 0, 0), width=1)
        whole.save(OUT / f'{name}_whole.png')
        print(f'{name}: {w}x{h} -> {OUT / (name + ".png")} and _whole.png')


if __name__ == '__main__':
    sys.exit(main())
