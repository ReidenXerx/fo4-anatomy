"""3BBB bodies (roadmap 1, A-57): Anatomy built on the 3BBB body when the player's physics runs 3BBB's bones.

3BBB (Nexus 48978, "CBBE 3BBB Body" 1.20, SQr17) is CBBE 2.7.2's physics body re-weighted (measured 2026-09-30):
the same 22,708 vertices, triangles and UVs; its BodySlide set reads CBBE's own CBBEBody.osd. The weights differ on
7,216 vertices: the breasts leave CBBE's chest/cloth bones for LBreast_01..03 / RBreast_01..03, the butt and thighs
gain LButt_01 / RButt_01 and LLeg_Thigh_01_F/R (and R). Only the feet moved (4,686 vertices below the knee, at most
0.16), so nothing near Nahka's patch differs and the patch applies to CBBE as ever.

So this is stage 1b, right after stage 1 (CBBE + Nahka), before the genital bones and the hip fold:
  - 3BBB's twelve bones join the body's skin (nif.with_bones, their node and skin transforms and bounding spheres
    copied from the 3BBB file);
  - every CBBE vertex stage 1 kept takes 3BBB's record: position, normal, tangents and weights (slots by name), so
    the shared skin is 3BBB exactly (A-4's rule, for a 3BBB player);
  - each of Nahka's vertices keeps its own weights plus the change 3BBB made at the CBBE neighbours it was blended
    from (patch 'near'): where she meets CBBE skin, both sides move the same, so the seam stays shut.
Stages 3 and 3b then run as for CBBE (the genital layers, the hip fold's core split; 3BBB's butt and thigh bones are
not core, so they are kept).

Chosen when the preset the engine runs (the player's ocbp.ini, else Anatomy's default) attaches 3BBB's breast bones
and the 3BBB body's BodySlide files are installed; CBBE stays the default otherwise.
"""
import collections
import struct

import nif

SHAPEDATA = 'Tools/BodySlide/ShapeData/CBBE 3BBB Body/CBBE 3BBB Body.nif'
SHAPE = 'CBBE-3BBB'
BREAST_BONES = ('LBreast_01_skin', 'RBreast_01_skin')      # what a 3BBB preset's [Attach] names


def attached(preset_text):
    """The bone names a preset's [Attach] section drives."""
    out, section = set(), None
    for line in preset_text.splitlines():
        line = line.split(';')[0].strip()
        if line.startswith('['):
            section = line.strip('[]').strip().lower()
        elif section == 'attach' and '=' in line:
            out.add(line.split('=', 1)[0].strip())
    return out


def choose(game, want, preset_rel):
    """(True, why) to build on 3BBB. want: 'auto' | 'cbbe' | '3bbb'; preset_rel: the preset the engine will run."""
    have = game.find(SHAPEDATA) is not None
    if want == 'cbbe':
        return False, 'CBBE (asked for)'
    if want == '3bbb':
        if not have:
            raise SystemExit(f'--body 3bbb: the 3BBB body is not installed ({SHAPEDATA}); install "3BBB Physics '
                             '(CBBE - TWB)" (Nexus 48978), its CBBE file')
        return True, '3BBB (asked for)'
    if not have:
        return False, 'CBBE: no 3BBB body installed'
    drives = preset_rel is not None and set(BREAST_BONES) <= attached(game.read(preset_rel).decode('utf-8', 'replace'))
    if drives:
        return True, f'3BBB: its body is installed and {preset_rel} drives its breast bones'
    return False, f'CBBE: a 3BBB body is installed, but {preset_rel or "no preset"} does not drive its breast bones'


def _bone_data(n, shape):
    """[(sphere (cx, cy, cz, r), rot 9, t 3, scale)] per skin slot, as BSSkin::BoneData stores them."""
    o, _ = n.offsets[shape.skin]
    c = nif.Cursor(n.b, o)
    c.take('i')
    data = c.take('i')
    o, _ = n.offsets[data]
    c = nif.Cursor(n.b, o)
    return [(c.take('4f'), c.take('9f'), c.take('3f'), c.take('f')) for _ in range(c.take('I'))]


def apply(stage1_path, mapping, near, base, tbbb_bytes, cbbe_bytes, shape_name='CBBE'):
    """Stage 1b in place on stage 1's nif. mapping: {output index: CBBE index} for the CBBE vertices stage 1 kept;
    near: Nahka's vertex k (output base + k) -> [(CBBE index, weight)]. Returns a report line."""
    tn = _from_bytes(tbbb_bytes)
    cn = _from_bytes(cbbe_bytes)
    ts, cs = tn.shape(SHAPE), cn.shape('CBBE')
    if (ts.count, ts.triangles(), ts.desc) != (cs.count, cs.triangles(), cs.desc):
        raise SystemExit('the 3BBB body is not CBBE 2.7.2\'s mesh re-weighted (vertices, triangles or layout differ)')
    if any(ts.uv(i) != cs.uv(i) for i in range(cs.count)):
        raise SystemExit('the 3BBB body\'s UVs differ from CBBE 2.7.2\'s')
    tbones, txf = tn.skin(ts)
    cbones, _ = cn.skin(cs)
    tdata = _bone_data(tn, ts)

    body = nif.Nif(stage1_path)
    s = body.shape(shape_name)
    ours, _ = body.skin(s)
    node_of = {v['name']: v for v in tn.nodes.values()}
    defs = []
    for k, name in enumerate(tbones):
        if name in ours:
            continue
        node = node_of[name]
        sphere, rot, tr, sc = tdata[k]
        defs.append(dict(name=name, node_rot=tuple(node['r']), node_t=tuple(node['t']), sphere=tuple(sphere),
                         skin_rot=tuple(rot), skin_t=tuple(tr), scale=sc))
    if defs:
        stage1_path.write_bytes(body.with_bones(s, defs))
        body = nif.Nif(stage1_path)
        s = body.shape(shape_name)
        ours, _ = body.skin(s)
    slot = {b: k for k, b in enumerate(ours)}
    missing = sorted({b for b in tbones if b not in slot})
    if missing:
        raise SystemExit(f'3BBB bones the body could not take: {missing}')

    def weights(shape, bones, i):
        return {bones[sl]: w for sl, w in shape.skin_weights(i)}

    # the shared skin: 3BBB's record, its weights' slots by name
    moved = 0
    for out_i, c_i in mapping.items():
        if s.record(out_i)[:s.skin_at] != cs.record(c_i)[:s.skin_at]:
            raise SystemExit(f'stage 1 changed CBBE vertex {c_i} (output {out_i}): not CBBE\'s record')
        rec = bytearray(ts.record(c_i))
        w = struct.unpack_from('<4e', rec, ts.skin_at)
        sl = struct.unpack_from('<4B', rec, ts.skin_at + 8)
        struct.pack_into('<4B', rec, ts.skin_at + 8, *[slot[tbones[sl[q]]] if w[q] > 0 else 0 for q in range(4)])
        if bytes(rec) != s.record(out_i):
            moved += 1
        s.set_record(out_i, bytes(rec))

    # Nahka's vertices: her weights plus 3BBB's change at the CBBE neighbours she was blended from
    shifted = 0
    for k, nb in enumerate(near):
        i = base + k
        if not nb:
            continue
        delta = collections.defaultdict(float)
        for c_i, wt in nb:
            for b, x in weights(ts, tbones, c_i).items():
                delta[b] += wt * x
            for b, x in weights(cs, cbones, c_i).items():
                delta[b] -= wt * x
        if all(abs(x) < 1e-4 for x in delta.values()):
            continue
        new = weights(s, ours, i)
        for b, x in delta.items():
            new[b] = new.get(b, 0.0) + x
        new = {b: x for b, x in new.items() if x > 1e-4}
        s.set_skin_weights(i, [(slot[b], x) for b, x in new.items()])
        shifted += 1
    body.save(stage1_path)
    return (f'1b. 3BBB: {len(defs)} bones added ({", ".join(d["name"] for d in defs)}); {moved} of {len(mapping)} '
            f'CBBE vertices took 3BBB\'s record; {shifted} of Nahka\'s {len(near)} vertices shifted by 3BBB\'s change')


def _from_bytes(blob):
    import pathlib
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.nif', delete=False) as fh:
        fh.write(blob)
    try:
        return nif.Nif(pathlib.Path(fh.name))
    finally:
        pathlib.Path(fh.name).unlink(missing_ok=True)
