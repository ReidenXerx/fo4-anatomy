"""A side view of the vaginal canal on a built body (tools/canal_depth.py, 2026-10-07): the drawn skin near the midline,
the tube Nahka made (kept part), the new deeper part, and the engine's VAGINA_PATH the penis follows.

    python studies/canal_depth_preview.py <Anatomy.nif> <new vertices> [out.png]
"""
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402
import physics_design as pd  # noqa: E402
import canal_depth as cd  # noqa: E402

n = nif.Nif(sys.argv[1])
s = n.shape(cd.SHAPE)
pos, tris = s.positions(), s.triangles()
first = s.count - 26 - int(sys.argv[2])                    # 6c appends the entrance ring's 26 copies after us
out = sys.argv[3] if len(sys.argv) > 3 else r'D:\F4Output\canal_depth_preview.png'
tube = cd._tube(pos, tris)
Y0, Y1, Z0, Z1, K = -8.0, 9.0, -60.0, -36.0, 40       # the view, in game units; K pixels a unit
img = Image.new('RGB', (int((Y1 - Y0) * K), int((Z1 - Z0) * K) + 90), (250, 247, 244))
d = ImageDraw.Draw(img)


def xy(p):
    return (p[1] - Y0) * K, (Z1 - p[2]) * K


def dots(ps, colour, r):
    for p in ps:
        x, y = xy(p)
        d.ellipse((x - r, y - r, x + r, y + r), fill=colour)


skin = []
for sh in n.shapes():
    sp = sh.positions()
    for t in sh.triangles():
        if sh.name == cd.SHAPE and all(i in tube for i in t):
            continue
        skin += [sp[i] for i in t if abs(sp[i][0]) < 0.6]
dots([p for p in set(skin) if Y0 < p[1] < Y1 and Z0 < p[2] < Z1], (201, 184, 173), 1.5)
dots([pos[i] for i in tube if i < first], (59, 111, 182), 3)
dots([pos[i] for i in tube if first <= i < s.count - 26], (192, 57, 43), 3)
d.line([xy(p) for p in pd.VAGINA_PATH], fill=(34, 34, 34), width=2)
dots(pd.VAGINA_PATH, (34, 34, 34), 4)
h = int((Z1 - Z0) * K)
for k, (txt, c) in enumerate((('her skin (midline slice, |x| < 0.6)', (160, 140, 128)), ('canal today (kept part)', (59, 111, 182)),
                              ('canal, deeper (new)', (192, 57, 43)), ('VAGINA_PATH: where the penis aims', (34, 34, 34)))):
    d.text((12, h + 8 + 20 * k), txt, fill=c)
d.text((12, 8), 'side view: belly to the right, up is up; 1 unit = %d px' % K, fill=(90, 90, 90))
img.save(out)
print('wrote', out)
