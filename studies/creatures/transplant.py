"""Byte-level transplant: the VANILLA nif stays byte for byte (glow effect shaders, controllers, sequences, palette,
dismember segments, node tree - everything PyNifly drops or rewrites), and only OUR geometry comes from the PyNifly
export (seg_fix'ed):
  new shapes      appended: shape + its BSSkin::Instance + BSSkin::BoneData (from the export, references remapped,
                  bones by NAME onto the vanilla nodes; missing bone nodes appended under the root), and a COPY of a
                  vanilla shape's BSLightingShaderProperty + BSShaderTextureSet (optionally renamed to our BGSM and
                  retextured); added to the root's children
  replaced shapes (sculpted bodies) the vanilla block keeps its index; its shape, skin instance and bone data bytes
                  come from the export, its shader/alpha/controllers stay VANILLA (glow shells keep their effects)
  bodytri         a NiStringExtraData 'BODYTRI' on the root (morph .tri path), if asked
FO4 layouts used (BSVER 130): NiObjectNET = name, extra count, extras, controller; NiAVObject += flags, 13f, collision;
BSTriShape += 4f sphere, skin, shader, alpha, ...; BSSkin::Instance = root, data, bone count, bones, ...;
BSLightingShaderProperty = type, name, extra count (0), controller, ..., texture set at +40; BSShaderTextureSet =
count, sized strings."""
import struct
import sys

import numpy as np

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402


def _net(m, o):
    """(name idx, extra refs, controller, offset after NiObjectNET)"""
    name, n = struct.unpack_from('<iI', m.b, o)
    extras = list(struct.unpack_from(f'<{n}i', m.b, o + 8))
    ctrl = struct.unpack_from('<i', m.b, o + 8 + 4 * n)[0]
    return name, extras, ctrl, o + 12 + 4 * n


def _shape_refs_at(m, idx):
    """offset of the (skin, shader, alpha) triple of a shape block"""
    o, _ = m.offsets[idx]
    _, _, _, p = _net(m, o)
    return p + 4 + 52 + 4 + 16                  # flags, transform, collision, bounding sphere


def _node_world(m, idx, parent_of):
    """world 4x4 of a node in m (accumulated local transforms)"""
    M = np.eye(4)
    chain = []
    k = idx
    while k is not None:
        chain.append(k)
        k = parent_of.get(k)
    for k in reversed(chain):
        n = m.nodes[k]
        L = np.eye(4)
        L[:3, :3] = np.array(n['r']).reshape(3, 3).T * n['s']   # rows = axes (NiMatrix3 rows note)
        L[:3, 3] = n['t']
        M = M @ L
    return M


def transplant(van_path, src_path, out_path, new, replace=(), bodytri=None, replace_mat=None):
    """new: {shape name: (vanilla shape to copy the material from, bgsm or None, [d, n, s] or None)}
    replace_mat: {replaced shape name: (shape to copy the material from, bgsm or None, tex or None)} - the replaced
    shape's OWN shader + texture set blocks are overwritten in place (e.g. UAP's penis taking the body material)"""
    replace_mat = replace_mat or {}
    V, P = nif.Nif(van_path), nif.Nif(src_path)
    vshape = {s.name: s for s in V.shapes()}
    pshape = {s.name: s for s in P.shapes()}
    vnode = {n['name']: i for i, n in V.nodes.items()}
    p_parent = {k: i for i, n in P.nodes.items() for k in n['kids']}
    strings = list(V.strings)
    add_strings = []

    def sidx(text):
        if text in strings:
            return strings.index(text)
        strings.append(text)
        add_strings.append(text)
        return len(strings) - 1

    nblocks = len(V.offsets)
    append = []                                                   # (type name, bytes)

    def new_index():
        return nblocks + len(append)

    replace_blocks = {}
    root = 0
    root_kids, root_extras = [], []

    def bone_ref(pref):
        name = P.nodes[pref]['name']
        if name in vnode:
            return vnode[name]
        # a bone the vanilla file lacks (e.g. Penis_00..05): a flat NiNode under the root at its world transform
        W = _node_world(P, pref, p_parent)
        sc = float(np.linalg.norm(W[:3, 0]))
        R = (W[:3, :3] / sc).T                                     # back to rows
        blk = struct.pack('<iIi', sidx(name), 0, -1) + struct.pack('<I', 14) + \
            struct.pack('<3f', *W[:3, 3]) + struct.pack('<9f', *R.ravel()) + struct.pack('<f', sc) + \
            struct.pack('<i', -1) + struct.pack('<I', 0)
        i = new_index()
        append.append(('NiNode', blk))
        vnode[name] = i
        root_kids.append(i)
        return i

    def skin_blocks(pskin_idx, data_idx_target):
        """remapped BSSkin::Instance bytes from P (bones by name), bone data index given"""
        o, sz = P.offsets[pskin_idx]
        b = bytearray(P.b[o:o + sz])
        _root, _data, nb = struct.unpack_from('<iiI', b, 0)
        bones = struct.unpack_from(f'<{nb}i', b, 12)
        struct.pack_into('<ii', b, 0, root, data_idx_target)
        for k, pb in enumerate(bones):
            struct.pack_into('<i', b, 12 + 4 * k, bone_ref(pb))
        return bytes(b)

    def raw(m, idx):
        o, sz = m.offsets[idx]
        return bytes(m.b[o:o + sz])

    # ---- replaced (sculpted) shapes: keep vanilla indices, shader, alpha
    for name in replace:
        vs, ps = vshape[name], pshape[name]
        v_skin, v_shader, v_alpha = struct.unpack_from('<3i', V.b, _shape_refs_at(V, vs.index))
        p_skin = struct.unpack_from('<i', P.b, _shape_refs_at(P, ps.index))[0]
        v_data = struct.unpack_from('<i', V.b, V.offsets[v_skin][0] + 4)[0]
        p_data = struct.unpack_from('<i', P.b, P.offsets[p_skin][0] + 4)[0]
        blk = bytearray(raw(P, ps.index))
        base = P.offsets[ps.index][0]
        _, pextras, _, _ = _net(P, base)
        if pextras:
            raise SystemExit(f'{name}: export shape carries extra data, not handled')
        # NiObjectNET header: take VANILLA's (name, extras, controller) so its effects/controllers stay attached
        vo = V.offsets[vs.index][0]
        _, vextras, vctrl, vafter = _net(V, vo)
        _, _, _, pafter = _net(P, base)
        head = bytes(V.b[vo:vafter])
        blk = bytearray(head + bytes(blk[pafter - base:]))
        ro = _shape_refs_at(V, vs.index) - vo                      # same offset in the new block (same header)
        struct.pack_into('<3i', blk, ro, v_skin, v_shader, v_alpha)
        replace_blocks[vs.index] = bytes(blk)
        replace_blocks[v_skin] = skin_blocks(p_skin, v_data)
        replace_blocks[v_data] = raw(P, p_data)
        if V.types[vs.index] != P.types[ps.index]:
            raise SystemExit(f'{name}: block type differs ({V.types[vs.index]} vs {P.types[ps.index]})')
        if name in replace_mat:
            mat_from, bgsm, tex = replace_mat[name]
            ms = vshape[mat_from]
            _, m_shader, _ = struct.unpack_from('<3i', V.b, _shape_refs_at(V, ms.index))
            if V.types[v_shader] != 'BSLightingShaderProperty' or V.types[m_shader] != 'BSLightingShaderProperty':
                raise SystemExit(f'{name}: replace_mat needs lighting shaders')
            v_tex = struct.unpack_from('<i', V.b, V.offsets[v_shader][0] + 40)[0]
            m_tex = struct.unpack_from('<i', V.b, V.offsets[m_shader][0] + 40)[0]
            sh = bytearray(raw(V, m_shader))
            if struct.unpack_from('<I', sh, 8)[0] != 0 or struct.unpack_from('<i', sh, 12)[0] != -1:
                raise SystemExit(f'{mat_from}: shader has extra data / controller, not handled')
            struct.pack_into('<i', sh, 40, v_tex)
            if bgsm:
                struct.pack_into('<i', sh, 4, sidx(bgsm))
            replace_blocks[v_shader] = bytes(sh)
            tb = bytearray(raw(V, m_tex))
            if tex:
                n = struct.unpack_from('<I', tb, 0)[0]
                paths, o = [], 4
                for _ in range(n):
                    ln = struct.unpack_from('<I', tb, o)[0]
                    paths.append(bytes(tb[o + 4:o + 4 + ln]))
                    o += 4 + ln
                for k, t in enumerate(tex):
                    paths[k] = t.encode('latin1')
                tb = bytearray(struct.pack('<I', n) + b''.join(struct.pack('<I', len(p)) + p for p in paths))
            replace_blocks[v_tex] = bytes(tb)
            struct.pack_into('<i', blk, ro + 8, -1)                # no alpha on skin
            replace_blocks[vs.index] = bytes(blk)

    # ---- new shapes
    for name, (mat_from, bgsm, tex) in new.items():
        ps = pshape[name]
        base = P.offsets[ps.index][0]
        _, pextras, _, pafter = _net(P, base)
        if pextras:
            raise SystemExit(f'{name}: export shape carries extra data, not handled')
        p_skin = struct.unpack_from('<i', P.b, _shape_refs_at(P, ps.index))[0]
        p_data = struct.unpack_from('<i', P.b, P.offsets[p_skin][0] + 4)[0]
        ms = vshape[mat_from]
        _, m_shader, _ = struct.unpack_from('<3i', V.b, _shape_refs_at(V, ms.index))
        if V.types[m_shader] != 'BSLightingShaderProperty':
            raise SystemExit(f'{mat_from}: material source is {V.types[m_shader]}')
        m_tex = struct.unpack_from('<i', V.b, V.offsets[m_shader][0] + 40)[0]
        i_shape = new_index()
        append.append((P.types[ps.index], b''))                    # placeholder, filled below
        i_skin = new_index()
        append.append(('BSSkin::Instance', b''))
        i_data = new_index()
        append.append(('BSSkin::BoneData', raw(P, p_data)))
        i_shader = new_index()
        sh = bytearray(raw(V, m_shader))
        if struct.unpack_from('<I', sh, 8)[0] != 0 or struct.unpack_from('<i', sh, 12)[0] != -1:
            raise SystemExit(f'{mat_from}: shader has extra data / controller, not handled')
        i_tex = i_shader + 1
        struct.pack_into('<i', sh, 40, i_tex)
        if bgsm:
            struct.pack_into('<i', sh, 4, sidx(bgsm))
        append.append(('BSLightingShaderProperty', bytes(sh)))
        tb = bytearray(raw(V, m_tex))
        if tex:
            n = struct.unpack_from('<I', tb, 0)[0]
            paths, o = [], 4
            for _ in range(n):
                ln = struct.unpack_from('<I', tb, o)[0]
                paths.append(bytes(tb[o + 4:o + 4 + ln]))
                o += 4 + ln
            for k, t in enumerate(tex):
                paths[k] = t.encode('latin1')
            tb = bytearray(struct.pack('<I', n) + b''.join(struct.pack('<I', len(p)) + p for p in paths))
        append.append(('BSShaderTextureSet', bytes(tb)))
        # the shape: VANILLA-style header (our name, no extras, no controller), refs remapped, alpha none
        body = bytes(P.b[pafter:P.offsets[ps.index][0] + P.offsets[ps.index][1]])
        blk = bytearray(struct.pack('<iIi', sidx(name), 0, -1) + body)
        ro = 12 + 4 + 52 + 4 + 16
        struct.pack_into('<3i', blk, ro, i_skin, i_shader, -1)
        append[i_shape - nblocks] = (P.types[ps.index], bytes(blk))
        append[i_skin - nblocks] = ('BSSkin::Instance', skin_blocks(p_skin, i_data))
        root_kids.append(i_shape)

    if bodytri:
        i = new_index()
        append.append(('NiStringExtraData', struct.pack('<ii', sidx('BODYTRI'), sidx(bodytri))))
        root_extras.append(i)

    # ---- root: append children + extra data
    o, sz = V.offsets[root]
    name, extras, ctrl, after = _net(V, o)
    rest = bytes(V.b[after:o + sz])
    av = rest[:4 + 52 + 4]
    nk = struct.unpack_from('<I', rest, 60)[0]
    kids = list(struct.unpack_from(f'<{nk}i', rest, 64))
    tail = rest[64 + 4 * nk:]
    extras = extras + root_extras
    kids = kids + root_kids
    replace_blocks[root] = (struct.pack('<iI', name, len(extras)) + struct.pack(f'<{len(extras)}i', *extras)
                            + struct.pack('<i', ctrl) + av + struct.pack('<I', len(kids))
                            + struct.pack(f'<{len(kids)}i', *kids) + tail)
    data = V.with_edits(replace=replace_blocks, append=append, add_strings=add_strings)
    open(out_path, 'wb').write(data)
    chk = nif.Nif(out_path)
    return dict(blocks=len(chk.types), shapes=[s.name for s in chk.shapes()], appended=len(append),
                new_strings=add_strings)
