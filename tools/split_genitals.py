"""The genitals become their own shape with their own material (decision A-21, zero-touch).

Nahka's genital triangles sample a corner of the body atlas CBBE never uses (uv_check.py). They
used to share the body's material, so their texture had to be patched INTO the skin mod's files: a
file that must win over the skin mod. Here they move to a shape of their own, "AnatomyGenitals",
whose material (Materials/Anatomy/AnatomyGenitals.bgsm, genital_texture.py) points at our own
copies of the textures. The skin mod's files are never touched.

What moves, exactly:
  - every triangle whose three UVs lie in the island corner (the same corner genital_texture.py
    rasterises), and the vertices they use. No other triangle uses those vertices: a vertex has one
    UV, and the island's UVs are nowhere else;
  - the vertex RECORDS byte for byte (position, UV, normal, tangent, weights), so both shapes
    deform identically where they meet, and the UVs stay atlas UVs: an overlay authored for the
    body samples the same texel there as before;
  - the skin: a new BSSkin::Instance naming the same bones in the same slots, and a copy of the
    body's BSSkin::BoneData, so every weight byte keeps its meaning;
  - the sliders: every "<body><slider>" diff on a moved vertex, re-indexed, as "AnatomyGenitals<slider>".
The body keeps all its vertices (so its slider data stays valid as it is) and loses the moved
triangles; its segment ranges are recounted.

Proven: the two shapes' triangles, as positions, are exactly the body's before; every moved record
is byte-identical; the body's kept triangles keep their order; segment counts add up; both skins
name the same bones; every moved slider diff arrives.

    python tools/split_genitals.py      build/project AnatomyBodyZeX -> Anatomy ("Anatomy Body")
"""
import pathlib
import re
import struct
import sys
import xml.etree.ElementTree as ET

import align_body as ab
import nif
import osd

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT = ab.OUT
SOURCE_FOLDER, SOURCE_SET = 'AnatomyBodyZeX', 'Anatomy Body ZeX'
OUT_FOLDER, OUT_SET = 'Anatomy', 'Anatomy Body'
BODY = ab.SHAPE                                   # 'CBBE'
GENITALS = 'AnatomyGenitals'
MATERIAL = 'Materials\\Anatomy\\AnatomyGenitals.bgsm'
TEXTURES = ['Textures\\Anatomy\\FemaleBody_d.dds', 'Textures\\Anatomy\\FemaleBody_n.dds',
            'Textures\\Anatomy\\FemaleBody_s.dds']
CORNER = (0.15, 0.80, 0.55, 1.0)                  # u0, v0, u1, v1: genital_texture.CORNER


def island(shape):
    """The triangles genital_texture.islands() paints: UV centroid in the corner AND at least one of
    Nahka's vertices (align_body's mapping: a vertex not shared with CBBE). The same rule, so the new
    shape's material covers exactly the texels the texture patch writes. A few of them reach a CBBE
    vertex at the rim; that record is simply copied too (both shapes keep it, byte-identical)."""
    import json
    u0, v0, u1, v1 = CORNER
    shared = {int(j) for j in json.loads((ab.OUT / 'mapping.json').read_text())['output_to_cbbe']}
    uv = [shape.uv(i) for i in range(shape.count)]
    tris = shape.triangles()
    moved = []
    for k, t in enumerate(tris):
        cu = sum(uv[v][0] for v in t) / 3
        cv = sum(uv[v][1] for v in t) / 3
        if u0 <= cu <= u1 and v0 <= cv <= v1 and any(v not in shared for v in t):
            moved.append(k)
    rim = sum(1 for k in moved if any(v in shared for v in tris[k]))
    return tris, moved, rim


def parse_shape(n, shape):
    """The body block cut into its parts: (prefix up to the triangle count, vertex bytes, segment bytes)."""
    o, size = n.offsets[shape.index]
    c = nif.Cursor(n.b, o)
    n._av(c)
    c.take('4f')
    c.take('i'), c.take('i'), c.take('i')
    c.take('Q')
    counts_at = c.o                                   # uint32 ntri, uint16 nv, uint32 size
    vdata = bytes(n.b[shape.data_at:shape.data_at + shape.count * shape.stride])
    seg_at = shape.data_at + shape.count * shape.stride + 6 * shape.triangle_count
    return bytes(n.b[o:counts_at]), vdata, bytes(n.b[seg_at:o + size])


def recount_segments(seg, kept_before, ntri):
    """BSSubIndexTriShape segment data with triangle ranges recounted after removing triangles.
    kept_before[k] = how many kept triangles precede old triangle k (length old ntri + 1)."""
    c = nif.Cursor(seg, 0)
    out = bytearray()
    nprim, nseg, total = c.take('I'), c.take('I'), c.take('I')
    out += struct.pack('<III', ntri, nseg, total)

    def rng(start, count):
        lo, hi = start // 3, start // 3 + count
        return kept_before[lo] * 3, kept_before[hi] - kept_before[lo]

    for _ in range(nseg):
        start, count, parent, nsub = c.take('I'), c.take('I'), c.take('I'), c.take('I')
        s, k = rng(start, count)
        out += struct.pack('<IIII', s, k, parent, nsub)
        for _ in range(nsub):
            ss, sc, sp, su = c.take('I'), c.take('I'), c.take('I'), c.take('I')
            s2, k2 = rng(ss, sc)
            out += struct.pack('<IIII', s2, k2, sp, su)
    out += seg[c.o:]                                   # per-segment user data and the SSF name: unchanged
    return bytes(out)


def texture_set(n, index, paths):
    """A copy of a BSShaderTextureSet with its first textures replaced."""
    o, size = n.offsets[index]
    c = nif.Cursor(n.b, o)
    count = c.take('I')
    items = []
    for _ in range(count):
        ln = c.take('I')
        items.append(bytes(n.b[c.o:c.o + ln]))
        c.o += ln
    for k, p in enumerate(paths):
        items[k] = p.encode('latin1')
    return struct.pack('<I', count) + b''.join(struct.pack('<I', len(t)) + t for t in items)


def main():
    src = PROJECT / 'ShapeData' / SOURCE_FOLDER
    n = nif.Nif(src / f'{SOURCE_FOLDER}.nif')
    body = n.shape(BODY)
    tris, moved, rim = island(body)
    if not moved:
        raise SystemExit('no genital triangles found: is this the anatomy body?')
    moved_set = set(moved)
    verts = sorted({i for k in moved for i in tris[k]})
    remap = {old: new for new, old in enumerate(verts)}
    kept = [k for k in range(len(tris)) if k not in moved_set]
    kept_before = [0] * (len(tris) + 1)
    for k in range(len(tris)):
        kept_before[k + 1] = kept_before[k] + (0 if k in moved_set else 1)
    print(f'1. island: {len(moved)} of {len(tris)} triangles ({rim} reach a CBBE vertex at the rim), '
          f'{len(verts)} vertices copied to {GENITALS}')

    prefix, vdata, seg = parse_shape(n, body)
    stride = body.stride
    # the body: same vertices, the kept triangles, recounted segments
    ktri = b''.join(struct.pack('<3H', *tris[k]) for k in kept)
    body_counts = struct.pack('<IHI', len(kept), body.count, len(vdata) + len(ktri))
    new_seg = recount_segments(seg, kept_before, len(kept)) if n.types[body.index] == 'BSSubIndexTriShape' else seg
    body_blk = prefix + body_counts + vdata + ktri + new_seg

    # the genitals: a BSTriShape with the moved records, re-indexed triangles, their own bound
    nb = len(n.offsets)
    idx_shape, idx_inst, idx_data, idx_shader, idx_texset = nb, nb + 1, nb + 2, nb + 3, nb + 4
    s_name, s_material = len(n.strings), len(n.strings) + 1
    o, _ = n.offsets[body.index]
    c = nif.Cursor(n.b, o)
    c.take('i')                                       # name
    for _ in range(c.take('I')):
        c.take('i')
    c.take('i')                                       # controller
    flags = c.take('I')
    t, r, s = c.take('3f'), c.take('9f'), c.take('f')
    c.take('i')                                       # collision
    c.take('4f')
    skin_ref, shader_ref, alpha_ref = c.take('i'), c.take('i'), c.take('i')
    desc = c.take('Q')
    gv = b''.join(vdata[i * stride:(i + 1) * stride] for i in verts)
    gtri = b''.join(struct.pack('<3H', *(remap[i] for i in tris[k])) for k in moved)
    pts = [body.position(i) for i in verts]
    ctr = [sum(p[k] for p in pts) / len(pts) for k in range(3)]
    rad = max(sum((p[k] - ctr[k]) ** 2 for k in range(3)) ** 0.5 for p in pts)
    shape_blk = (struct.pack('<iIi', s_name, 0, -1) + struct.pack('<I', flags) + struct.pack('<3f', *t)
                 + struct.pack('<9f', *r) + struct.pack('<f', s) + struct.pack('<i', -1)
                 + struct.pack('<4f', *ctr, rad) + struct.pack('<iii', idx_inst, idx_shader, -1)
                 + struct.pack('<Q', desc) + struct.pack('<IHI', len(moved), len(verts), len(gv) + len(gtri))
                 + gv + gtri)
    # skin: the same bones in the same slots, data -> a copy of the body's bone data
    io, isz = n.offsets[skin_ref]
    inst = bytearray(n.b[io:io + isz])
    body_data = struct.unpack_from('<i', inst, 4)[0]
    struct.pack_into('<i', inst, 4, idx_data)
    do, dsz = n.offsets[body_data]
    data_blk = bytes(n.b[do:do + dsz])
    # shader: the body's, named after our material, pointing at our texture set
    so, ssz = n.offsets[shader_ref]
    shader = bytearray(n.b[so:so + ssz])
    struct.pack_into('<i', shader, 4, s_material)
    texset_ref = struct.unpack_from('<i', shader, 40)[0]
    if not (0 <= texset_ref < nb and n.types[texset_ref] == 'BSShaderTextureSet'):
        raise SystemExit(f'the body shader\'s texture set is not where expected (+40 -> {texset_ref})')
    struct.pack_into('<i', shader, 40, idx_texset)
    texset_blk = texture_set(n, texset_ref, TEXTURES)
    # the root gains the new shape as a child
    root = 0
    ro, rsz = n.offsets[root]
    rc = nif.Cursor(n.b, ro)
    n._av(rc)
    kids_at = rc.o
    kids = rc.take('I')
    root_blk = (bytes(n.b[ro:kids_at]) + struct.pack('<I', kids + 1) + bytes(n.b[kids_at + 4:kids_at + 4 + 4 * kids])
                + struct.pack('<i', idx_shape) + bytes(n.b[kids_at + 4 + 4 * kids:ro + rsz]))
    out = n.with_edits(replace={body.index: body_blk, root: root_blk},
                       append=[('BSTriShape', shape_blk), ('BSSkin::Instance', bytes(inst)),
                               ('BSSkin::BoneData', data_blk), ('BSLightingShaderProperty', bytes(shader)),
                               ('BSShaderTextureSet', texset_blk)],
                       add_strings=[GENITALS, MATERIAL])
    dst = PROJECT / 'ShapeData' / OUT_FOLDER
    dst.mkdir(parents=True, exist_ok=True)
    out_nif = dst / f'{OUT_FOLDER}.nif'
    out_nif.write_bytes(out)

    # ---- proofs, on the file as written
    m = nif.Nif(out_nif)
    b2, g2 = m.shape(BODY), m.shape(GENITALS)
    problems = []
    if b2.count != body.count or [b2.record(i) for i in range(0, b2.count, 997)] != [body.record(i) for i in range(0, body.count, 997)]:
        problems.append('the body\'s vertex records changed')
    if b2.triangles() != [tris[k] for k in kept]:
        problems.append('the body\'s kept triangles are not the old ones in order')
    if any(g2.record(new) != body.record(old) for old, new in remap.items()):
        problems.append('a moved vertex record differs')
    before = sorted(tuple(body.position(i) for i in t) for t in tris)
    after = sorted([tuple(b2.position(i) for i in t) for t in b2.triangles()]
                   + [tuple(g2.position(i) for i in t) for t in g2.triangles()])
    if before != after:
        problems.append('the two shapes\' triangles are not the body\'s before')
    if m.skin(b2)[0] != m.skin(g2)[0] or m.skin(g2)[1] != n.skin(body)[1]:
        problems.append('the skins name different bones or bind them differently')
    if m.types[b2.index] == 'BSSubIndexTriShape':
        seg_o = b2.data_at + b2.count * b2.stride + 6 * b2.triangle_count
        nprim, nseg = struct.unpack_from('<II', m.b, seg_o)
        counts = [struct.unpack_from('<I', m.b, seg_o + 12 + 16 * k + 4)[0] for k in range(nseg)]
        if nprim != b2.triangle_count or sum(counts) != b2.triangle_count:
            problems.append(f'segments count {sum(counts)} / {nprim} for {b2.triangle_count} triangles')
    print(f'2. wrote {out_nif}: {BODY} {b2.count} vertices / {b2.triangle_count} triangles; {GENITALS} '
          f'{g2.count} / {g2.triangle_count}; material {MATERIAL}')

    # ---- sliders: every diff on a moved vertex, re-indexed, under the new shape's name
    data = osd.read(src / f'{SOURCE_FOLDER}.osd')
    added, moved_diffs, sliders = {}, 0, set()
    for name, diffs in data.items():
        if not name.startswith(BODY):
            continue
        slider = name[len(BODY):]
        g = {remap[i]: d for i, d in diffs.items() if i in remap}
        if g:
            added[GENITALS + slider] = g
            moved_diffs += len(g)
            sliders.add(slider)
    expected = sum(1 for name, diffs in data.items() if name.startswith(BODY) for i in diffs if i in remap)
    if moved_diffs != expected:
        problems.append(f'slider diffs moved {moved_diffs} of {expected}')
    osd.write(dst / f'{OUT_FOLDER}.osd', {**data, **added})
    back = osd.read(dst / f'{OUT_FOLDER}.osd')
    if any(back.get(k) != {i: tuple(v) for i, v in sorted(d.items()) if tuple(v) != (0.0, 0.0, 0.0)} for k, d in added.items()):
        problems.append('the written slider data does not read back')

    # ---- the slider set: the new set name and folder, the new shape, a Data line per moved slider
    osp = (PROJECT / 'SliderSets' / f'{SOURCE_FOLDER}.osp').read_text(encoding='utf-8')
    osp = (osp.replace(f'name="{SOURCE_SET}"', f'name="{OUT_SET}"')
              .replace(f'<DataFolder>{SOURCE_FOLDER}</DataFolder>', f'<DataFolder>{OUT_FOLDER}</DataFolder>')
              .replace(f'<SourceFile>{SOURCE_FOLDER}.nif</SourceFile>', f'<SourceFile>{OUT_FOLDER}.nif</SourceFile>')
              .replace(f'{SOURCE_FOLDER}.osd\\', f'{OUT_FOLDER}.osd\\'))
    osp = osp.replace(f'<Shape target="{BODY}">{BODY}</Shape>',
                      f'<Shape target="{BODY}">{BODY}</Shape>\n        <Shape target="{GENITALS}">{GENITALS}</Shape>', 1)
    missing_sliders = []
    for slider in sorted(sliders):
        pat = re.compile(rf'(<Slider name="{re.escape(slider)}"[^>]*>\s*\n)(.*?)(\s*</Slider>)', re.S)
        mo = pat.search(osp)
        if not mo:
            missing_sliders.append(slider)
            continue
        line = (f'\n            <Data name="{GENITALS}{slider}" target="{GENITALS}" local="true">'
                f'{OUT_FOLDER}.osd\\{GENITALS}{slider}</Data>')
        osp = osp[:mo.end(2)] + line + osp[mo.end(2):]
    if missing_sliders:
        problems.append(f'no <Slider> in the set for {missing_sliders}')
    (PROJECT / 'SliderSets' / f'{OUT_FOLDER}.osp').write_text(osp, encoding='utf-8')
    tree = ET.parse(PROJECT / 'SliderSets' / f'{OUT_FOLDER}.osp')           # it must still be XML
    lines = [d for d in tree.iter('Data') if d.get('target') == GENITALS]
    print(f'3. slider data: {moved_diffs} diffs of {len(sliders)} sliders re-indexed onto {GENITALS}; '
          f'SliderSets/{OUT_FOLDER}.osp "{OUT_SET}": {len(lines)} Data lines for {GENITALS}')
    if len(lines) != len(sliders):
        problems.append(f'{len(lines)} Data lines for {len(sliders)} sliders')
    if problems:
        raise SystemExit('FAIL - ' + '; '.join(problems))
    print('PASS - the same triangles in two shapes, every moved record and slider diff intact')


if __name__ == '__main__':
    sys.exit(main())
