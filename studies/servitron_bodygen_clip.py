"""Does Silhouette's BodyGen push Servitron's suit through its breasts? Each of Silhouette's women's templates (it
lists ServitronRace) applied, through the torso's own .tri, to the breasts and the suit; then: suit vertices in front
of the breasts' surface (per 0.5-unit cell of their front view), and how far the worst one is.

    python studies/servitron_bodygen_clip.py <Torso ... Boobs.nif (built)> [templates.ini]
"""
import pathlib
import re
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import nif  # noqa: E402

NIF = pathlib.Path(sys.argv[1])
TEMPLATES = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else
                         r'D:\SteamFreeGames\Fallout 4 AE\Data\F4SE\Plugins\F4EE\BodyGen\Loose\Silhouette_templates.ini')
SUITS = ('Torso2_GITS_Open', 'Torso3_GITS_Half_Open', 'Torso3_GITS_Half_Open_Metal', 'Overalls_Softbody_Open')


def tri(path):
    """{shape: {morph: {vertex: (dx, dy, dz)}}}"""
    b = path.read_bytes()
    o, out = 6, {}
    for _ in range(struct.unpack_from('<H', b, 4)[0]):
        shape = b[o + 1:o + 1 + b[o]].decode('latin1')
        o += 1 + b[o]
        (count,) = struct.unpack_from('<H', b, o)
        o += 2
        morphs = out.setdefault(shape, {})
        for _ in range(count):
            name = b[o + 1:o + 1 + b[o]].decode('latin1').rstrip('\0')
            o += 1 + b[o]
            mult, nv = struct.unpack_from('<fH', b, o)
            o += 6
            d = {}
            for k in range(nv):
                i, x, y, z = struct.unpack_from('<H3h', b, o + 8 * k)
                d[i] = (x * mult, y * mult, z * mult)
            o += 8 * nv
            morphs[name] = d
    return out


def templates(path):
    out = {}
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        m = re.match(r'^(Silhouette_\w+)=(.*)$', line)
        if not m:
            continue
        vals = {}
        for part in m.group(2).split(','):
            if '@' not in part:
                continue
            k, v = part.strip().split('@', 1)
            v = v.split(':')[-1]                       # a range lo:hi -> its high end (the most extreme)
            try:
                vals[k] = float(v)
            except ValueError:
                pass
        out[m.group(1)] = vals
    return out


n = nif.Nif(NIF)
shapes = {s.name: s for s in n.shapes()}
breast = next(k for k in ('Boobs', 'Robo-Boobs') if k in shapes)
suit = next(k for k in SUITS if k in shapes)
morphs = tri(NIF.with_suffix('.tri'))


def shaped(name, vals):
    pos = [list(p) for p in shapes[name].positions()]
    for m, v in vals.items():
        for i, d in morphs.get(name, {}).get(m, {}).items():
            if i < len(pos):
                for k in range(3):
                    pos[i][k] += v * d[k]
    return pos


used = {i for t in shapes[suit].triangles() for i in t}
rows = []
for name, vals in templates(TEMPLATES).items():
    bp, sp = shaped(breast, vals), shaped(suit, vals)
    cell = {}
    for p in bp:
        k = (round(p[0] * 2), round(p[2] * 2))
        cell[k] = max(cell.get(k, -1e9), p[1])
    ahead = [sp[i][1] - cell[(round(sp[i][0] * 2), round(sp[i][2] * 2))] for i in used
             if (round(sp[i][0] * 2), round(sp[i][2] * 2)) in cell]
    front = [a for a in ahead if a > 0.0]
    rows.append((len(front), max(front, default=0.0), name))
rows.sort(reverse=True)
print(f'{NIF.name}: {breast} / {suit}; {len(rows)} templates')
print('at zero sliders (the built shape):', end=' ')
print(rows and '')
for c, worst, name in rows[:8]:
    print(f'  {name:24} suit vertices in front of the breasts {c:4d}, worst {worst:.2f} ahead')
print('templates with none in front:', sum(1 for r in rows if r[0] == 0), 'of', len(rows))
