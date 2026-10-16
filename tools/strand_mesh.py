"""The strand mesh the engine stretches between two contact points (fluid strands, adapted from OStrands' design:
https://gitlab.com/LilRicefield/ostrands, GPL-3, tools/make_strand.py there writes the Skyrim one).

A tube of RINGS rings around +X, ring k at x = k * SPACING and skinned only to bone Strand<k> (a child of the root at
that spot). The engine (fo4-ocbpc Strands.cpp) writes each bone every frame, so the tube bends through the points it
simulates; the bone's scale is the ring's radius (RADIUS 1 here), so the engine also thins it.

The shader and texture set are COPIED from a Fallout 4 skinned body (the women's skin material) with their refs and
strings remapped, so the block layout is one the game was built against; the shader type goes from SkinTint (5) to
Default (0), which drops SkinTint's 16-byte tail. Only the nodes, the shape and the skin blocks are written here.
Winding follows the body's: cross(v1 - v0, v2 - v0) points along the vertex normal.

--fluid points the shader at our wet material and adds a NiAlphaProperty (blend: the BGSM's alpha does nothing
without one), and writes that material beside the mesh's Meshes folder: Materials/Anatomy/Strand.bgsm, a copy of the
game's EyeWet.BGSM (lit, alpha-blended, glossy, the eye cubemap) with a cream diffuse of ours, depth-tested, not a
decal, full specular; and Textures/Anatomy/Strand/Strand_d.dds (16x16 uncompressed, the cream).

    python tools/strand_mesh.py <body.nif> <Data root>/Meshes/Anatomy/Strand/Strand.nif [--fluid] [--data <FO4 Data>]

The render facts this layout rests on (2026-10-16, tests 1-20, fo4-ocbpc Strands.cpp): the engine attaches the root
under an actor's 3D and attaches each shape again by itself, or nothing draws.
"""
import argparse
import math
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bgsm  # noqa: E402
import gamedata  # noqa: E402
import nif  # noqa: E402

RINGS = 10
SIDES = 8
SPACING = 1.0
RADIUS = 1.0                                       # the bone scale sets the radius in game
BSX_FLAGS = 0xC2                                   # TrafficCone01.nif's BSXFlags value
NODE_FLAGS = 0xE                                   # the body's NiNode and BSTriShape flags
# vertex desc as the body's: 32-byte records; UV at 8, normal at 12, tangent at 16, skin at 20; half positions;
# VERTEX | UV | NORMAL | TANGENT | SKINNED
DESC = 8 | 2 << 8 | 3 << 16 | 4 << 20 | 5 << 28 | (0x1 | 0x2 | 0x8 | 0x10 | 0x40) << 44
SLSF1_SKINNED = 0x2                                # BSLightingShaderProperty shader flags 1 (at byte 16)
SLSF2_VERTEX_COLORS = 0x20                         # shader flags 2 (at byte 20): the shader would read a colour per vertex
SHADER_DEFAULT = 0                                 # shader type (byte 0); the body's is 5, SkinTint

FLUID_MATERIAL = 'Materials\\Anatomy\\Strand.bgsm'
FLUID_DIFFUSE = 'Anatomy/Strand/Strand_d.dds'      # relative to Textures, as BGSM paths are
FLUID_BASE = 'Materials\\actors\\character\\HumanCommon\\EyeWet.BGSM'
FLUID_COLOUR = (236, 232, 220)                     # a pearly cream
FLUID_ALPHA = 0.85
# NiAlphaProperty flags: blend on (bit 0), source SRC_ALPHA (6 << 1), destination INV_SRC_ALPHA (7 << 5), as the
# BGSM's own blend 6/7
ALPHA_FLAGS = 1 | 6 << 1 | 7 << 5


def ubyte(x):
    return max(0, min(255, round((x + 1.0) * 0.5 * 255)))


def sized(s):
    b = s.encode('latin1')
    return struct.pack('<I', len(b)) + b


def short(s):
    b = s.encode('latin1') + b'\0'
    return struct.pack('<B', len(b)) + b


def geometry():
    """Vertex records and triangles: rings of SIDES + 1 vertices (the seam column doubled for the UV)."""
    recs, pos = [], []
    for k in range(RINGS):
        for j in range(SIDES + 1):
            a = 2 * math.pi * j / SIDES
            c, s = math.cos(a), math.sin(a)
            p = (k * SPACING, RADIUS * c, RADIUS * s)
            nrm, tan = (0.0, c, s), (1.0, 0.0, 0.0)
            bit = (nrm[1] * tan[2] - nrm[2] * tan[1], nrm[2] * tan[0] - nrm[0] * tan[2],
                   nrm[0] * tan[1] - nrm[1] * tan[0])
            r = struct.pack('<4e', p[0], p[1], p[2], bit[0])
            r += struct.pack('<2e', j / SIDES, k / (RINGS - 1))
            r += bytes((ubyte(nrm[0]), ubyte(nrm[1]), ubyte(nrm[2]), ubyte(bit[1])))
            r += bytes((ubyte(tan[0]), ubyte(tan[1]), ubyte(tan[2]), ubyte(bit[2])))
            r += struct.pack('<4e', 1.0, 0.0, 0.0, 0.0) + bytes((k, 0, 0, 0))
            assert len(r) == (DESC & 0xF) * 4
            recs.append(r)
            pos.append((p, nrm))
    tris = []

    def outward(t):
        (p0, n0), (p1, _), (p2, _) = (pos[i] for i in t)
        e1 = [p1[i] - p0[i] for i in range(3)]
        e2 = [p2[i] - p0[i] for i in range(3)]
        cr = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        return t if sum(cr[i] * n0[i] for i in range(3)) > 0 else (t[0], t[2], t[1])
    for k in range(RINGS - 1):
        for j in range(SIDES):
            a, b = k * (SIDES + 1) + j, (k + 1) * (SIDES + 1) + j
            tris += [outward((a, b, a + 1)), outward((a + 1, b, b + 1))]
    return recs, tris


def av(name, t=(0.0, 0.0, 0.0), extras=()):
    """NiObjectNET + NiAVObject: name, extra data refs, no controller, flags, transform, no collision."""
    return (struct.pack('<iI', name, len(extras)) + struct.pack(f'<{len(extras)}i', *extras) +
            struct.pack('<iI', -1, NODE_FLAGS) + struct.pack('<3f', *t) +
            struct.pack('<9f', 1, 0, 0, 0, 1, 0, 0, 0, 1) + struct.pack('<fi', 1.0, -1))


def dds_rgba(width, height, rgba):
    """An uncompressed 32-bit DDS (B8G8R8A8), one colour, no mips."""
    pf = struct.pack('<II4sIIIII', 32, 0x41, b'\0\0\0\0', 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    head = struct.pack('<4sIIIIIII', b'DDS ', 124, 0x1 | 0x2 | 0x4 | 0x8 | 0x1000, height, width, width * 4, 0, 0)
    head += b'\0' * 44 + pf + struct.pack('<IIIII', 0x1000, 0, 0, 0, 0)
    r, g, b, a = rgba
    return head + bytes((b, g, r, a)) * (width * height)


def fluid_material(data_root, game_data):
    """Materials/Anatomy/Strand.bgsm and its diffuse under data_root, from the game's EyeWet.BGSM."""
    base = gamedata.Game(game_data).read(FLUID_BASE)
    if base is None:
        raise SystemExit(f'{FLUID_BASE} was not found in {game_data}')
    m = bytearray(bgsm.with_textures(base, {'diffuse': FLUID_DIFFUSE}))
    struct.pack_into('<f', m, 28, FLUID_ALPHA)
    m[44] = 1                                     # z-test: the bodies hide it (EyeWet's eyes skip it)
    m[47] = 0                                     # not a decal
    _, end = bgsm.textures(bytes(m))
    assert m[end + 15] == 1, 'EyeWet tail: specular expected on at +15'
    struct.pack_into('<f', m, end + 28, 1.0)      # specular multiplier (EyeWet's 0.2), smoothness 1 follows
    out = pathlib.Path(data_root) / FLUID_MATERIAL.replace('\\', '/')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(m))
    tex = pathlib.Path(data_root) / 'Textures' / FLUID_DIFFUSE
    tex.parent.mkdir(parents=True, exist_ok=True)
    tex.write_bytes(dds_rgba(16, 16, FLUID_COLOUR + (255,)))
    return out, tex


def build(body_path, out_path, material=None, fluid=False):
    body = nif.Nif(body_path)
    shader = next(i for i, t in enumerate(body.types) if t == 'BSLightingShaderProperty')
    so, ss = body.offsets[shader]
    shader_src = bytes(body.b[so:so + ss])
    assert not struct.unpack_from('<I', shader_src, 20)[0] & SLSF2_VERTEX_COLORS, 'a skin shader without vertex colours'
    tset = struct.unpack_from('<i', shader_src, 40)[0]
    to, ts = body.offsets[tset]
    tset_bytes = bytes(body.b[to:to + ts])
    mat = FLUID_MATERIAL if fluid else material or body.string(struct.unpack_from('<i', shader_src, 4)[0])
    wet = body.string(struct.unpack_from('<i', shader_src, 60)[0])

    strings = ['StrandRoot'] + [f'Strand{k:02}' for k in range(RINGS)] + ['StrandShape', 'BSX', mat] + ([wet] if wet else [])
    S = {s: i for i, s in enumerate(strings)}
    blocks = []                                                       # [type, bytes]

    def add(kind, data=b''):
        blocks.append([kind, data])
        return len(blocks) - 1

    # a NiNode root carrying BSXFlags, as vanilla TrafficCone01.nif: under an actor's 3D the game then gives it the fade
    # bits (TopFadeNode 14, 32, FadedIn 37) and draws it; without BSX it kept 80000E and drew nothing (10-16, tests 20/23)
    root = add('NiNode')
    bsx = add('BSXFlags', struct.pack('<iI', S['BSX'], BSX_FLAGS))
    bones = [add('NiNode', av(S[f'Strand{k:02}'], (k * SPACING, 0.0, 0.0)) + struct.pack('<I', 0)) for k in range(RINGS)]
    shape = add('BSTriShape')
    skin = add('BSSkin::Instance')
    bonedata = add('BSSkin::BoneData')

    # the body's shader + texture set, refs and strings remapped, as Default (type 0)
    sb = bytearray(shader_src)
    struct.pack_into('<i', sb, 4, S[mat])
    struct.pack_into('<i', sb, 60, S[wet] if wet else -1)
    if struct.unpack_from('<I', sb, 0)[0] == 5:
        # SkinTint (5) ends in a tint colour + alpha (16 bytes) that Default (0) does not have; left in, the game read
        # every later block 16 bytes off and asked for a 3 GB allocation (10-16). Vanilla: type 5 = 156 bytes, 0 = 140
        assert len(sb) == 156
        sb = sb[:-16]
    struct.pack_into('<I', sb, 0, SHADER_DEFAULT)
    struct.pack_into('<I', sb, 16, struct.unpack_from('<I', sb, 16)[0] | SLSF1_SKINNED)
    shd = add('BSLightingShaderProperty')
    struct.pack_into('<i', sb, 40, add('BSShaderTextureSet', tset_bytes))
    blocks[shd][1] = bytes(sb)
    alpha = add('NiAlphaProperty', struct.pack('<iIiHB', -1, 0, -1, ALPHA_FLAGS, 128)) if fluid else -1

    recs, tris = geometry()
    data = b''.join(recs) + b''.join(struct.pack('<3H', *tr) for tr in tris)
    length = (RINGS - 1) * SPACING
    blocks[shape][1] = (av(S['StrandShape']) + struct.pack('<4f', length / 2, 0, 0, length / 2 + RADIUS) +
                        struct.pack('<iii', skin, shd, alpha) + struct.pack('<Q', DESC) +
                        struct.pack('<IHI', len(tris), len(recs), len(data)) + data)
    blocks[skin][1] = struct.pack('<iiI', 0, bonedata, RINGS) + struct.pack(f'<{RINGS}i', *bones) + struct.pack('<I', 0)
    bd = struct.pack('<I', RINGS)
    for k in range(RINGS):
        # bound in the bone's space (around its ring), then the skin-to-bone transform: v_bone = v_skin - (kS, 0, 0)
        bd += struct.pack('<4f', 0, 0, 0, RADIUS + SPACING) + struct.pack('<9f', 1, 0, 0, 0, 1, 0, 0, 0, 1)
        bd += struct.pack('<3f', -k * SPACING, 0, 0) + struct.pack('<f', 1.0)
    blocks[bonedata][1] = bd
    kids = bones + [shape]
    blocks[root][1] = av(S['StrandRoot'], extras=(bsx,)) + struct.pack('<I', len(kids)) + struct.pack(f'<{len(kids)}i', *kids)

    types = []
    for t, _ in blocks:
        if t not in types:
            types.append(t)
    head = b'Gamebryo File Format, Version 20.2.0.7\n' + struct.pack('<IBII', 0x14020007, 1, 12, len(blocks))
    head += struct.pack('<I', 130) + short('Anatomy strand_mesh.py') + short('') + short('') + short('')
    head += struct.pack('<H', len(types)) + b''.join(sized(t) for t in types)
    head += b''.join(struct.pack('<H', types.index(t)) for t, _ in blocks)
    head += b''.join(struct.pack('<I', len(b)) for _, b in blocks)
    head += struct.pack('<II', len(strings), max(len(s) for s in strings)) + b''.join(sized(s) for s in strings)
    head += struct.pack('<I', 0)
    footer = struct.pack('<Ii', 1, 0)                                 # one root: block 0
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(head + b''.join(b for _, b in blocks) + footer)
    back = nif.Nif(out)                                               # our own reader must take it back
    sh = back.shape('StrandShape')
    bnames, _ = back.skin(sh)
    assert bnames == [f'Strand{k:02}' for k in range(RINGS)], bnames
    assert sh.count == len(recs) and sh.triangle_count == len(tris)
    print(f'{out}: {len(blocks)} blocks, {len(recs)} vertices, {len(tris)} triangles, {RINGS} bones, material {mat}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('body')
    ap.add_argument('out')
    ap.add_argument('--material')
    ap.add_argument('--fluid', action='store_true')
    ap.add_argument('--data', help='Fallout 4 Data, to read EyeWet.BGSM from (--fluid)')
    a = ap.parse_args()
    build(a.body, a.out, a.material, a.fluid)
    if a.fluid:
        data_root = pathlib.Path(a.out).resolve().parents[3]          # <root>/Meshes/Anatomy/Strand/Strand.nif
        for p in fluid_material(data_root, gamedata.find_data(a.data, tool='strand_mesh.py')):
            print(p)
