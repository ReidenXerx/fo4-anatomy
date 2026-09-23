"""An Outfit Studio mask that protects everything but the genital region (for CopyBoneWeights).

JaneBod Extended's weights are the reference (A-3), but JaneBod is shaped differently from CBBE.
Copied by proximity over the whole body, its hip and thigh weights would leak into CBBE's skin,
which A-4 promises stays CBBE's exactly. The mask confines the copy to Nahka's new geometry plus a
soft band around it:

    new vertex                         m = 0   (free)
    shared vertex within INNER units   m = 0
    between INNER and OUTER            m rises linearly 0 -> 1 (a blend, not a seam)
    everything further                 m = 1   (protected)

Mask file format, from the v5.8.2 tag's MaskFile.cpp (read by the LoadMask automation step):
    <MaskFile version="1"><MaskData name=".."><Shape name=".." vertexCount="N"><V i=".." m=".."/>...
An unlisted vertex is 0 (unmasked); Outfit Studio's tools leave m = 1 alone.

    python tools/mask.py [--inner 1.5] [--outer 3.0]
"""
import argparse
import json
import math
import pathlib

import align_body as ab
import nif

MASK_NAME = 'AnatomyGenitalRegion'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--project', type=pathlib.Path, default=ab.OUT)
    ap.add_argument('--inner', type=float, default=1.5)
    ap.add_argument('--outer', type=float, default=3.0)
    args = ap.parse_args()
    mapping = {int(j) for j in json.loads((args.project / 'mapping.json').read_text())['output_to_cbbe']}
    shape = nif.Nif(args.project / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif').shape(ab.SHAPE)
    pos = shape.positions()
    new = [j for j in range(shape.count) if j not in mapping]
    grid = ab.Grid(pos, new)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<MaskFile version="1">',
             f'    <MaskData name="{MASK_NAME}">',
             f'        <Shape name="{ab.SHAPE}" vertexCount="{shape.count}">']
    free = soft = 0
    for j in range(shape.count):
        if j not in mapping:
            free += 1
            continue
        hit = grid.nearest(pos[j], 1, limit=args.outer)   # empty: no new vertex within the band
        d = math.dist(pos[j], pos[hit[0]]) if hit else math.inf
        if d <= args.inner:
            free += 1
            continue
        m = 1.0 if d >= args.outer else (d - args.inner) / (args.outer - args.inner)
        soft += m < 1.0
        lines.append(f'            <V i="{j}" m="{m:.6f}"/>')
    lines += ['        </Shape>', '    </MaskData>', '</MaskFile>', '']
    out = args.project / 'Masks' / f'{MASK_NAME}.xml'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{out}: {free} vertices free (the {len(new)} new ones + shared within {args.inner} units), '
          f'{soft} blended up to {args.outer}, {shape.count - free - soft} protected')


if __name__ == '__main__':
    main()
