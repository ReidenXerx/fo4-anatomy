"""A front view of a Servitron torso mesh, every shape in its own colour, triangles painted far to near (+y is toward the
viewer), so whichever piece covers the breasts shows. Writes a PNG.

    python studies/servitron_torso_view.py <torso .nif> <out.png>
"""
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402

COLOURS = {'Boobs': (40, 40, 48), 'Robo-Boobs': (40, 40, 48), 'Torso2_UpperBodyCaps': (190, 120, 60),
           'Torso3_Assaultron': (190, 120, 60)}
OTHER = (90, 140, 200)
n = nif.Nif(sys.argv[1])
X0, X1, Z0, Z1, K = -14.0, 14.0, -40.0, -8.0, 22
img = Image.new('RGB', (int((X1 - X0) * K), int((Z1 - Z0) * K)), (245, 245, 245))
d = ImageDraw.Draw(img)
tris = []
for s in n.shapes():
    pos = s.positions()
    col = COLOURS.get(s.name, OTHER)
    for t in s.triangles():
        a, b, c = (pos[i] for i in t)
        y = (a[1] + b[1] + c[1]) / 3
        # a little shading by facing (normal's y), so shapes read
        nx = (b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1])
        ny = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])
        nz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        lit = 0.55 + 0.45 * abs(ny / ln)
        tris.append((y, [((p[0] - X0) * K, (Z1 - p[2]) * K) for p in (a, b, c)], tuple(int(v * lit) for v in col)))
tris.sort(key=lambda t: t[0])
for _, pts, col in tris:
    d.polygon(pts, fill=col)
d.text((6, 6), f'{pathlib.Path(sys.argv[1]).name}: breasts dark, metal caps orange, suit blue', fill=(0, 0, 0))
img.save(sys.argv[2])
print('wrote', sys.argv[2])
