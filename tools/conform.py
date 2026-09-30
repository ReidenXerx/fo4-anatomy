"""A BodySlide project from a clothing mesh ALONE (A-59; the owner, 2026-09-30: "without them at all if we have only
just a clothing mod we should be able make proper bodyslide to any body").

A built outfit mesh is what BodySlide wrote for ONE preset: reference + sum(slider data x value). With no project we
recover the rest from the body it was made on:
  1. which preset: the one whose body the outfit's skin-side vertices hug best (among the body's preset files);
  2. the reference shape: each outfit vertex minus that preset's slider offsets, conformed from the body under it;
  3. the sliders: every body slider's data carried onto every outfit vertex from the six nearest body vertices
     (inverse distance), what Outfit Studio's "Conform Sliders" does by hand, so the outfit follows any preset and
     BodyGen (BodySlide writes the .tri with --trimorphs);
  4. the weights: refit.transfer (our body's, 3BBB here), as for any refit;
  5. a normal project: ShapeData <set>/<set>.nif + .osd, SliderSets <set>.osp, output where the game loads the mesh.
The body is our Anatomy BodySlide source (its CBBE shape and the genitals: panties conform to the vulva too).
Shapes with their own transform (rigid attachments) keep their shape and get no sliders.
"""
import collections
import math
import pathlib
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

import align_body as ab
import garments as g
import nif
import osd
import refit

K = 6                                   # body vertices a slider offset is blended from
SHAPES = ('CBBE', 'AnatomyGenitals')    # the body shapes an outfit conforms to
PRESET_FILES = ('CBBE.xml', 'wtaw body.xml')


class Body:
    """Our BodySlide body: positions at the reference, every CBBE slider's per-vertex data, the presets."""

    def __init__(self, bs):
        n = nif.Nif(bs / 'ShapeData/Anatomy/Anatomy.nif')
        data = osd.read(bs / 'ShapeData/Anatomy/Anatomy.osd')
        self.cset, sliders = ab.read_set(bs / 'SliderSets/CBBE.osp', ab.CBBE_SET)
        self.sliders = [(name, attrs) for name, attrs, _, _ in sliders]
        self.pos, self.diff = [], collections.defaultdict(dict)   # diff[slider][body vertex] = (x, y, z)
        for shape in SHAPES:
            s = n.shape(shape)
            base = len(self.pos)
            self.pos += s.positions()
            for name, _ in self.sliders:
                for i, d in data.get(shape + name, {}).items():
                    self.diff[name][base + i] = d
        self.presets = {}
        for f in PRESET_FILES:
            p = bs / 'SliderPresets' / f
            if not p.exists():
                continue
            for pr in ET.parse(p).getroot().iter('Preset'):
                if pr.get('set') != 'CBBE Body':
                    continue
                vals = {}
                for ss in pr.iter('SetSlider'):
                    if ss.get('size', 'big') == 'big':
                        vals[ss.get('name')] = float(ss.get('value', '0')) / 100
                self.presets[pr.get('name')] = vals
        self._shaped = {}

    def shaped(self, preset):
        """(positions, grid) of the body built with a preset."""
        if preset not in self._shaped:
            vals = self.presets[preset]
            pos = [list(p) for p in self.pos]
            for name, v in vals.items():
                if not v:
                    continue
                for i, d in self.diff.get(name, {}).items():
                    for k in range(3):
                        pos[i][k] += v * d[k]
            self._shaped[preset] = (pos, g.Grid(pos))
        return self._shaped[preset]

    def nearest(self, grid, q):
        """[(distance, body vertex)] of the K nearest, however far."""
        for r in (1.0, 3.0, 8.0, 20.0, 60.0):
            h = grid.within(q, r)
            if len(h) >= K:
                return h[:K]
        return grid.within(q, 200.0)[:K]

    def offsets(self, grid, q, values=None):
        """{slider: (x, y, z)} at q, blended from the nearest body vertices; with values, their sum as one offset."""
        hits = self.nearest(grid, q)
        wsum = sum(1.0 / max(d, 1e-3) for d, _ in hits)
        out = {}
        for name, _ in self.sliders:
            dd = self.diff.get(name)
            if not dd:
                continue
            acc = [0.0, 0.0, 0.0]
            for d, i in hits:
                x = dd.get(i)
                if x:
                    w = 1.0 / max(d, 1e-3) / wsum
                    for k in range(3):
                        acc[k] += w * x[k]
            if any(abs(a) > 1e-5 for a in acc):
                out[name] = tuple(acc)
        if values is None:
            return out
        return tuple(sum(values.get(nm, 0.0) * v[k] for nm, v in out.items()) for k in range(3))

    def detect(self, points):
        """(preset, mean distance) whose body the skin-side points hug best."""
        best = None
        for preset in self.presets:
            _, grid = self.shaped(preset)
            ds = []
            for q in points:
                h = grid.within(q, 2.0)
                if h:
                    ds.append(h[0][0])
            if len(ds) < max(10, len(points) // 4):
                continue
            score = sum(ds) / len(ds)
            if best is None or score < best[1]:
                best = (preset, score)
        return best


def make_project(body, change, src, model, home, set_name):
    """One outfit mesh (src .nif path) -> a project under home (ShapeData, SliderSets). A report dict."""
    n = nif.Nif(src)
    shapes = [s for s in n.shapes() if n.skin(s)[0] and g.identity(n, s)]
    probe = [q for s in shapes for q in s.positions()[::7]]
    found = body.detect(probe)
    if found is None:
        return dict(model=model, skipped='does not sit on the body')
    preset, score = found
    values = body.presets[preset]
    _, grid = body.shaped(preset)
    folder = home / 'ShapeData' / set_name
    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / f'{set_name}.nif'
    names = {x.name for x in shapes}
    data = {}
    for s in n.shapes():                                  # the reference shape: the preset's offsets taken out
        if s.name not in names:
            continue
        for i, q in enumerate(s.positions()):
            offs = body.offsets(grid, q)
            shift = tuple(sum(values.get(nm, 0.0) * v[k] for nm, v in offs.items()) for k in range(3))
            s.set_position(i, tuple(q[k] - shift[k] for k in range(3)))
            for nm, v in offs.items():
                data.setdefault(s.name + nm, {})[i] = v
    ref = folder / '_reference.nif'
    n.save(ref)
    g.patch_nif(change, ref, dst, refit.transfer, refit.check)        # the weights, on the reference shape
    ref.unlink()
    osd.write(folder / f'{set_name}.osd', data)
    parts = model.replace('/', '\\').split('\\')
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<SliderSetInfo version="1">',
         f'    <SliderSet name={quoteattr(set_name)}>',
         f'        <DataFolder>{escape(set_name)}</DataFolder>',
         f'        <SourceFile>{escape(set_name)}.nif</SourceFile>',
         f'        <OutputPath>{escape(chr(92).join(["meshes"] + parts[:-1]))}</OutputPath>',
         f'        <OutputFile GenWeights="false">{escape(parts[-1])}</OutputFile>']
    for s in shapes:
        L.append(f'        <Shape target={quoteattr(s.name)}>{escape(s.name)}</Shape>')
    for name, attrs in body.sliders:
        rows = [s.name for s in shapes if (s.name + name) in data]
        if not rows:
            continue
        a = ' '.join(f'{k}={quoteattr(v)}' for k, v in attrs.items())
        L.append(f'        <Slider {a}>')
        for sh in rows:
            L.append(f'            <Data name={quoteattr(sh + name)} target={quoteattr(sh)} local="true">'
                     f'{escape(set_name)}.osd\\{escape(sh + name)}</Data>')
        L.append('        </Slider>')
    L += ['    </SliderSet>', '</SliderSetInfo>', '']
    (home / 'SliderSets').mkdir(parents=True, exist_ok=True)
    (home / 'SliderSets' / f'{set_name}.osp').write_text('\n'.join(L), encoding='utf-8')
    return dict(model=model, set=set_name, preset=preset, fit=round(score, 3), shapes=len(shapes),
                sliders=len({k for k in data}))
