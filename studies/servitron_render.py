"""Offline renders of a Servitron as the spawn helper builds it (the owner, 2026-10-08: "show me it via offline render bc
its too hard back and forth running game"): Servitron's own skeleton in its bind pose, the parts Anatomy:DebugSpawn
fits, each with its textures as the game resolves them (loose files first, then the archives: our dev files win), lit
by fo4-refit's preview renderer. A Silhouette template can be applied through the meshes' own .tri morphs, to see what
an NPC's body shape does to the chest.

    python studies/servitron_render.py <out.png> [--template Silhouette_Rough_F06] [--abdomen "Abdomen GITS Rubber"]
"""
import argparse
import pathlib
import re
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'fo4-refit' / 'tools'))
sys.path.insert(0, str(ROOT / 'tools'))
import preview as pv  # noqa: E402
import gamedata  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
PARTS = ['Head', 'Head Eyes 1', 'Head Ears', 'Torso 2 GITS Boobs', 'Arm Left', 'Arm Right', 'Hand Left', 'Hand Right',
         'Legs']
TEMPLATES = DATA / 'F4SE/Plugins/F4EE/BodyGen/Loose/Silhouette_templates.ini'
VIEWS = {'front': ((0.0, 62.0, 92.0), (0.0, 0.0, 90.0)), 'three-quarter': ((-40.0, 50.0, 96.0), (0.0, 0.0, 90.0)),
         'body': ((0.0, 150.0, 80.0), (0.0, 0.0, 75.0))}


def template(name):
    for line in TEMPLATES.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith(name + '='):
            vals = {}
            for part in line.split('=', 1)[1].split(','):
                if '@' in part:
                    k, v = part.strip().split('@', 1)
                    try:
                        vals[k] = float(v.split(':')[-1])
                    except ValueError:
                        pass
            return vals
    raise SystemExit(f'no template {name}')


def tri_morphs(raw):
    o, out = 6, {}
    for _ in range(struct.unpack_from('<H', raw, 4)[0]):
        shape = raw[o + 1:o + 1 + raw[o]].decode('latin1')
        o += 1 + raw[o]
        (count,) = struct.unpack_from('<H', raw, o)
        o += 2
        for _ in range(count):
            name = raw[o + 1:o + 1 + raw[o]].decode('latin1').rstrip('\0')
            o += 1 + raw[o]
            mult, nv = struct.unpack_from('<fH', raw, o)
            o += 6
            d = {}
            for k in range(nv):
                i, x, y, z = struct.unpack_from('<H3h', raw, o + 8 * k)
                d[i] = (x * mult, y * mult, z * mult)
            o += 8 * nv
            out.setdefault(shape, {})[name] = d
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('out')
    ap.add_argument('--template')
    ap.add_argument('--abdomen', default='Abdomen GITS Rubber')
    ap.add_argument('--size', type=int, default=640)
    a = ap.parse_args()
    pv.W, pv.H = a.size, int(a.size * 1.15)
    game = gamedata.Game(DATA)
    work = pathlib.Path(r'D:\F4Output\servitron\render')
    work.mkdir(parents=True, exist_ok=True)
    sk_path = work / 'skeleton.nif'
    sk_path.write_bytes(game.read('Meshes/Servitron/skeleton.nif'))
    sk = pv.Skeleton(sk_path)
    bind = sk.pose({}, np.zeros(3))
    vals = template(a.template) if a.template else {}
    r = pv.Renderer()
    drawn = []
    default_place = None
    for name in PARTS + [a.abdomen]:
        rel = f'Meshes/Servitron/{name}.nif'
        p = work / f'{name}.nif'
        p.write_bytes(game.read(rel))
        morphs = {}
        if vals and game.find(rel[:-4] + '.tri') is not None:
            morphs = tri_morphs(game.read(rel[:-4] + '.tri'))
        for part in pv.load_parts(p, game):
            for m, v in vals.items():
                for i, d in morphs.get(part.name, {}).get(m, {}).items():
                    if i < len(part.pos):
                        part.pos[i] += v * np.array(d, np.float32)
            place = part.placement(bind)
            default_place = default_place if default_place is not None else place
            vao, tex = r.upload(part)
            drawn.append((part, vao, tex, None, (0.45, 0.45, 0.5), (1, 1, 1)))
    frames = []
    for label, (eye, target) in VIEWS.items():
        eye = np.array(eye)
        vp = pv.perspective(34 if label != 'body' else 30, pv.W / pv.H, 5, 1000) @ pv.look_at(eye, target)
        d2 = [(p, vao, tex, p.matrices(bind, bind, 'Pelvis_skin', default_place), base, tint)
              for p, vao, tex, _, base, tint in drawn]
        img = r.frame(d2, vp, eye)
        ImageDraw.Draw(img).text((8, 8), f'{label}{"  template " + a.template if a.template else "  (no body template)"}',
                                 fill=(230, 230, 230))
        frames.append(img)
    out = Image.new('RGB', (sum(f.width for f in frames) + 10 * (len(frames) - 1), frames[0].height), (20, 20, 24))
    x = 0
    for f in frames:
        out.paste(f, (x, 0))
        x += f.width + 10
    out.save(a.out)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
