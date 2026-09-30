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

import numpy as np
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
        self.tris = []
        for shape in SHAPES:
            s = n.shape(shape)
            base = len(self.pos)
            self.pos += s.positions()
            self.tris += [(a + base, b + base, c + base) for a, b, c in s.triangles()]
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

    def _arrays(self):
        if not hasattr(self, 'P'):
            self.P = np.array(self.pos, dtype=np.float64)
            self.snames = [nm for nm, _ in self.sliders if self.diff.get(nm)]
            self.D = np.zeros((len(self.snames), len(self.pos), 3), dtype=np.float32)
            for k, nm in enumerate(self.snames):
                items = self.diff[nm]
                idx = np.fromiter(items.keys(), dtype=np.int64, count=len(items))
                self.D[k, idx] = np.array(list(items.values()), dtype=np.float32)
            self.T = np.array(self.tris, dtype=np.int64)

    def shaped(self, preset):
        """(positions N x 3, normals N x 3) of the body built with a preset (numpy)."""
        self._arrays()
        if preset not in self._shaped:
            v = np.array([self.presets[preset].get(nm, 0.0) for nm in self.snames], dtype=np.float64)
            pos = self.P + np.einsum('s,snk->nk', v, self.D.astype(np.float64))
            a, b, c = pos[self.T[:, 0]], pos[self.T[:, 1]], pos[self.T[:, 2]]
            fn = np.cross(b - a, c - a)                    # area-weighted vertex normals, for inside/outside
            nrm = np.zeros_like(pos)
            for j in range(3):
                np.add.at(nrm, self.T[:, j], fn)
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
            self._shaped[preset] = (pos, nrm)
        return self._shaped[preset]

    def knn(self, preset, q, k=K):
        """(distances M x k, body vertices M x k) of the k nearest body vertices, however far (chunked brute force)."""
        pos, _ = self.shaped(preset)
        q = np.asarray(q, dtype=np.float64).reshape(-1, 3)
        b = pos.astype(np.float32)
        bb = (b * b).sum(1)
        dist, idx = np.empty((len(q), k)), np.empty((len(q), k), dtype=np.int64)
        for s0 in range(0, len(q), 512):
            qq = q[s0:s0 + 512].astype(np.float32)
            d2 = (qq * qq).sum(1)[:, None] + bb[None, :] - 2.0 * (qq @ b.T)
            part = np.argpartition(d2, k, axis=1)[:, :k]
            dd = np.take_along_axis(d2, part, 1)
            order = np.argsort(dd, axis=1)
            idx[s0:s0 + 512] = np.take_along_axis(part, order, 1)
            dist[s0:s0 + 512] = np.sqrt(np.maximum(np.take_along_axis(dd, order, 1), 0.0))
        return dist, idx

    def signed(self, preset, points, reach=2.0):
        """[distance outside (+) or inside (-) the body built with a preset] for the points within reach of it."""
        pos, nrm = self.shaped(preset)
        q = np.asarray(points, dtype=np.float64).reshape(-1, 3)
        dist, idx = self.knn(preset, q, 1)
        keep = dist[:, 0] <= reach
        j = idx[keep, 0]
        return list(((q[keep] - pos[j]) * nrm[j]).sum(1))

    def offsets_all(self, preset, q):
        """Every slider's offset at every point: array M x S x 3 (self.snames order), inverse-distance blended from
        the K nearest body vertices of the body built with the preset."""
        dist, idx = self.knn(preset, q, K)
        w = 1.0 / np.maximum(dist, 1e-3)
        w /= w.sum(1, keepdims=True)
        out = np.zeros((len(idx), len(self.snames), 3), dtype=np.float32)
        for k in range(K):
            out += w[:, k, None, None].astype(np.float32) * self.D[:, idx[:, k], :].transpose(1, 0, 2)
        return out

    def detect(self, points):
        """(preset, share inside) the mesh was built with: the one whose body pokes through it least (an author
        fixes clipping at the preset they build with), then the tightest fit (the tenth-percentile gap). Measured
        (A-59, 24 BA2 outfits, clipping re-targeted to three presets): this pick 3.4% against the best possible 3.3%;
        the mean gap (the first version) 9.7%, always Zeroed 6.5%."""
        best = None
        for preset in self.presets:
            sd = self.signed(preset, points)
            if len(sd) < max(10, len(points) // 4):
                continue
            inside = sum(1 for d in sd if d < -0.2) / len(sd)
            gaps = sorted(abs(d) for d in sd)
            key = (round(inside, 2), gaps[len(gaps) // 10])
            if best is None or key < best[1]:
                best = (preset, key)
        return None if best is None else (best[0], best[1][0])


def make_project(body, change, src, model, home, set_name):
    """One outfit mesh (src .nif path) -> a project under home (ShapeData, SliderSets). A report dict."""
    n = nif.Nif(src)
    shapes = [s for s in n.shapes() if n.skin(s)[0] and g.identity(n, s)]
    probe = [q for s in shapes for q in s.positions()[::7]]
    found = body.detect(probe)
    if found is None:
        return dict(model=model, skipped='does not sit on the body')
    preset, score = found
    vals = np.array([body.presets[preset].get(nm, 0.0) for nm in body.snames], dtype=np.float32)
    folder = home / 'ShapeData' / set_name
    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / f'{set_name}.nif'
    names = {x.name for x in shapes}
    data = {}
    for s in n.shapes():                                  # the reference shape: the preset's offsets taken out
        if s.name not in names:
            continue
        pos = np.array(s.positions(), dtype=np.float64)
        offs = body.offsets_all(preset, pos)              # M x S x 3
        ref_pos = pos - np.einsum('s,msk->mk', vals, offs)
        for i, q in enumerate(ref_pos):
            s.set_position(i, tuple(float(x) for x in q))
        live = np.abs(offs).max(axis=2) > 1e-5            # M x S
        for k, nm in enumerate(body.snames):
            rows = np.nonzero(live[:, k])[0]
            if len(rows):
                data[s.name + nm] = {int(i): tuple(float(x) for x in offs[i, k]) for i in rows}
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
    return dict(model=model, set=set_name, preset=preset, inside=round(score, 3), shapes=len(shapes),
                sliders=len({k for k in data}))
