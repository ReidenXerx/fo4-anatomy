"""Merge vanilla leveled lists and outfits that several plugins edit directly, into one small light patch.

Written for Eli's Armour Compendium 2.1.1 (the owner, 2026-10-02): it still edits 13 vanilla leveled lists and one
outfit directly, and six of them are also edited by other plugins in the owner's load order (LIF.esl,
Mercenary.esp, NCWR_MinutemenOverhaul.esp, Look At Me RE.esp), so only the last one's version would count.

How a record is merged: VANILLA's version (Fallout4.esm) is the base, and every plugin's change is applied as a
difference against it -- the entries (LVLO, with any COED) or outfit items (INAM) it added are added, the ones it
removed are removed, and a scalar field (LVLD chance none, LVLM max count, LVLF flags, LVLG global) it changed is taken,
the latest plugin in load order winning a field two plugins both changed. Nobody's additions are lost and nobody's
removals come back. Every form id is remapped from its plugin's master list to the patch's own. The patch adds no
record, so it is flagged light (ESL) and loads after all of them.

    python tools/plugin_merge.py --out <patch.esp> --record LVLI:LL_Clothes_Wastelander ... [--plugins a.esp b.esp ...]
"""
import argparse
import collections
import os
import pathlib
import struct
import zlib

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
AUTHOR = 'ReidenXerx (fo4-anatomy tools/plugin_merge.py)'
LIGHT = 0x200
SCALARS = ('LVLD', 'LVLM', 'LVLF', 'LVLG')
FID_FIELDS = {'LVLG': (0,)}                    # scalar subrecords holding a form id, at these offsets


def subrecords(data):
    out, pos, big = [], 0, None
    while pos + 6 <= len(data):
        t = data[pos:pos + 4].decode('latin1')
        size = struct.unpack_from('<H', data, pos + 4)[0]
        pos += 6
        if t == 'XXXX':
            big = struct.unpack_from('<I', data, pos)[0]
            pos += size
            continue
        if big is not None:
            size, big = big, None
        out.append((t, data[pos:pos + size]))
        pos += size
    return out


def field(sig, data):
    if len(data) > 0xFFFF:
        return b'XXXX' + struct.pack('<HI', 4, len(data)) + sig.encode('ascii') + struct.pack('<H', 0) + data
    return sig.encode('ascii') + struct.pack('<H', len(data)) + data


class Plugin:
    """a plugin's masters, and its records of the wanted types by form id (raw subrecords)"""

    def __init__(self, path, types):
        self.name = pathlib.Path(path).name
        b = pathlib.Path(path).read_bytes()
        hsize = struct.unpack_from('<I', b, 4)[0]
        self.masters = [d[:-1].decode('latin1') for t, d in subrecords(b[24:24 + hsize]) if t == 'MAST']
        self.records = {}
        pos = 24 + hsize
        while pos + 24 <= len(b):
            t = b[pos:pos + 4].decode('latin1')
            size = struct.unpack_from('<I', b, pos + 4)[0]
            if t == 'GRUP':
                label = b[pos + 8:pos + 12].decode('latin1')
                gtype = struct.unpack_from('<i', b, pos + 12)[0]
                if gtype == 0 and label not in types:
                    pos += size
                    continue
                pos += 24
                continue
            if t in types:
                flags, fid = struct.unpack_from('<II', b, pos + 8)
                data = b[pos + 24:pos + 24 + size]
                if flags & 0x40000:
                    data = zlib.decompress(data[4:])
                self.records[self.glob(fid)] = (t, flags & ~0x40000, subrecords(data))
            pos += 24 + size

    def glob(self, fid):
        """a form id as (owning plugin, local id)"""
        i = fid >> 24
        return (self.masters[i] if i < len(self.masters) else self.name).lower(), fid & 0xFFFFFF


def entries(p, subs):
    """a leveled list's entries as hashable tuples with global refs: (level, ref, count, rest, coed)"""
    out, cur = [], None
    for t, d in subs:
        if t == 'LVLO':
            if cur:
                out.append(cur)
            level = struct.unpack_from('<H', d, 0)[0]
            ref = p.glob(struct.unpack_from('<I', d, 4)[0])
            cur = (level, ref, d[8:], None)
        elif t == 'COED' and cur:
            owner = p.glob(struct.unpack_from('<I', d, 0)[0]) if struct.unpack_from('<I', d, 0)[0] else None
            cur = cur[:3] + ((owner, d[4:]),)
    if cur:
        out.append(cur)
    return out


def items(p, subs):
    for t, d in subs:
        if t == 'INAM':
            return [p.glob(struct.unpack_from('<I', d, i)[0]) for i in range(0, len(d), 4)]
    return []


def merge(fid, base, versions):
    """base: (Plugin, record) of Fallout4.esm; versions: [(Plugin, record)] in load order -> merged subrecords
    with GLOBAL refs in place of form ids: [(sig, payload)] where payload may hold ('ref', glob)"""
    bp, (btype, bflags, bsubs) = base
    if btype == 'LVLI':
        ve = collections.Counter(entries(bp, bsubs))
        result = collections.Counter(ve)
        added, removed = collections.Counter(), collections.Counter()
        for p, (t, f, subs) in versions:
            me = collections.Counter(entries(p, subs))
            for e, n in (me - ve).items():
                added[e] = max(added[e], n)
            for e, n in (ve - me).items():
                removed[e] = max(removed[e], n)
        result = result - removed + added
        scal = {t: d for t, d in bsubs if t in SCALARS}
        scal_owner = {t: bp for t in scal}
        # LVLF merges bit by bit: each plugin's set bits are set and its cleared bits cleared (LIF sets "calculate from
        # all levels" on lists EAC also edits; a whole-field take would drop LIF's bit for EAC's value)
        # (LVLF is one byte in Fallout 4; read whatever width the field has, little-endian)
        width = lambda d: int.from_bytes(d, 'little') if d else 0
        vf = width(dict(bsubs).get('LVLF', b''))
        flags_now = vf
        for p, (t, f, subs) in versions:
            d = dict(subs).get('LVLF')
            if d is not None:
                mf = width(d)
                flags_now = (flags_now | (mf & ~vf)) & ~(vf & ~mf)
        for p, (t, f, subs) in versions:
            for st, d in subs:
                if st == 'LVLF':
                    continue
                if st in SCALARS:
                    bd = dict((x, y) for x, y in bsubs if x in SCALARS).get(st)
                    if (st in FID_FIELDS and bd is not None and p.glob(struct.unpack_from('<I', d, 0)[0])
                            != bp.glob(struct.unpack_from('<I', bd, 0)[0])) or (st not in FID_FIELDS and d != bd):
                        scal[st], scal_owner[st] = d, p
        ordered = sorted(result.elements(), key=lambda e: (e[0], e[1]))
        block = [('LLCT', ('count', len(ordered)))]
        for e in ordered:
            block.append(('LVLO', ('entry', e)))
            if e[3] is not None:
                block.append(('COED', ('coed', e[3])))
        if 'LVLF' in scal or flags_now != vf:
            old = scal.get('LVLF', b'\0')
            scal['LVLF'] = flags_now.to_bytes(max(1, len(old)), 'little')
            scal_owner['LVLF'] = bp
        out, placed = [], False
        for st, d in bsubs:
            if st in SCALARS or st in ('LVLO', 'COED'):
                continue
            if st == 'LLCT':                    # the entries where vanilla keeps them
                out += block
                placed = True
                continue
            out.append((st, ('raw', d, bp)))
            if st == 'OBND':
                for k in ('LVLD', 'LVLM', 'LVLF', 'LVLG'):
                    if k in scal:
                        out.append((k, ('scalar', scal[k], scal_owner[k])))
        if not placed:
            out += block
        return btype, bflags, out, (sum(added.values()), sum(removed.values()), len(ordered))
    # OTFT: INAM items
    vi = collections.Counter(items(bp, bsubs))
    result = collections.Counter(vi)
    added, removed = collections.Counter(), collections.Counter()
    for p, (t, f, subs) in versions:
        mi = collections.Counter(items(p, subs))
        added |= (mi - vi)
        removed |= (vi - mi)
    result = result - removed + added
    out = [(st, ('raw', d, bp)) if st != 'INAM' else ('INAM', ('items', list(result.elements()))) for st, d in bsubs]
    return btype, bflags, out, (sum(added.values()), sum(removed.values()), sum(result.values()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--record', nargs='+', required=True, help='TYPE:EditorID of vanilla records to merge')
    ap.add_argument('--plugins', nargs='+', help='the plugins to merge from (default: every active plugin that edits them)')
    ap.add_argument('--data', default=str(DATA))
    a = ap.parse_args()
    data = pathlib.Path(a.data)
    txt = pathlib.Path(os.environ['LOCALAPPDATA']) / 'Fallout4' / 'plugins.txt'
    order = [l.lstrip('*').strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines()
             if l.strip() and not l.startswith('#')]
    active = [l[1:].strip() for l in txt.read_text(encoding='utf-8', errors='replace').splitlines() if l.startswith('*')]
    types = {r.split(':')[0] for r in a.record}
    vanilla = Plugin(data / 'Fallout4.esm', types)
    edid = {}
    for g, (t, f, subs) in vanilla.records.items():
        e = next((d[:-1].decode('latin1') for st, d in subs if st == 'EDID'), '')
        edid[f'{t}:{e}'] = g
    want = [edid[r] for r in a.record]
    names = a.plugins or [n for n in active if n.lower() != 'fallout4.esm']
    plugins = []
    for n in names:
        p = pathlib.Path(n) if pathlib.Path(n).is_absolute() else data / n
        if not p.exists():
            continue
        try:
            pl = Plugin(p, types)
        except Exception:
            continue
        if any(w in pl.records for w in want):
            plugins.append(pl)
    plugins.sort(key=lambda p: order.index(p.name) if p.name in order else 10 ** 6)
    merged = []
    for w in want:
        versions = [(p, p.records[w]) for p in plugins if w in p.records]
        merged.append((w, versions, merge(w, (vanilla, vanilla.records[w]), versions)))
    # the patch's masters: only the plugins its records reference, in load order
    # every merged plugin is a master too, referenced or not, so no manager can sort the patch before one of them
    # (NCWR's and LIF's changes here name only vanilla forms, yet the patch must load after them)
    used = {'fallout4.esm'} | {p.name.lower() for p in plugins}
    for w, versions, (t, flags, subs, _) in merged:
        for st, payload in subs:
            kind = payload[0]
            if kind in ('raw', 'scalar') and st in FID_FIELDS:
                used.add(payload[2].glob(struct.unpack_from('<I', payload[1], 0)[0])[0])
            elif kind == 'entry':
                used.add(payload[1][1][0])
            elif kind == 'coed' and payload[1][0]:
                used.add(payload[1][0][0])
            elif kind == 'items':
                used |= {g[0] for g in payload[1]}
    masters = sorted(used, key=lambda m: order.index(next((o for o in order if o.lower() == m), m))
                     if any(o.lower() == m for o in order) else (-1 if m == 'fallout4.esm' else 10 ** 6))
    spelled = {p.name.lower(): p.name for p in plugins}
    for p in plugins + [vanilla]:
        spelled.update({m.lower(): m for m in p.masters})
    spelled['fallout4.esm'] = 'Fallout4.esm'
    real = {m: spelled.get(m, next((o for o in order if o.lower() == m), m)) for m in masters}
    index = {m: i for i, m in enumerate(masters)}

    def fid(g):
        return (index[g[0]] << 24) | g[1]

    body = b''
    report = []
    by_type = collections.defaultdict(bytes)
    for w, versions, (t, flags, subs, (nadd, nrem, total)) in merged:
        blob = b''
        for st, payload in subs:
            kind = payload[0]
            if kind == 'raw':
                d, src = payload[1], payload[2]
                if st in FID_FIELDS:
                    d = struct.pack('<I', fid(src.glob(struct.unpack_from('<I', d, 0)[0]))) + d[4:]
                blob += field(st, d)
            elif kind == 'scalar':
                d, src = payload[1], payload[2]
                if st in FID_FIELDS:
                    d = struct.pack('<I', fid(src.glob(struct.unpack_from('<I', d, 0)[0]))) + d[4:]
                blob += field(st, d)
            elif kind == 'count':
                blob += field('LLCT', struct.pack('<B', min(payload[1], 255)))
            elif kind == 'entry':
                level, ref, rest, _ = payload[1]
                blob += field('LVLO', struct.pack('<HHI', level, 0, fid(ref)) + rest)
            elif kind == 'coed':
                owner, rest = payload[1]
                blob += field('COED', struct.pack('<I', fid(owner) if owner else 0) + rest)
            elif kind == 'items':
                blob += field('INAM', b''.join(struct.pack('<I', fid(g)) for g in payload[1]))
        e = next((d[:-1].decode('latin1') for st, d in vanilla.records[w][2] if st == 'EDID'), '')
        by_type[t] += (t.encode() + struct.pack('<III', len(blob), flags, fid(w)) + struct.pack('<IHH', 0, 131, 0) + blob)
        report.append(f'{t} {e}: {total} entries ({nadd} added, {nrem} removed vs vanilla) from '
                      f'{", ".join(p.name for p, _ in versions)}')
    for t, recs in by_type.items():
        body += b'GRUP' + struct.pack('<I', 24 + len(recs)) + t.encode() + struct.pack('<I', 0) + struct.pack('<IHH', 0, 0, 0) + recs
    nrec = len(want) + len(by_type)
    header = field('HEDR', struct.pack('<fiI', 1.0, nrec, 0x800)) + field('CNAM', AUTHOR.encode('ascii') + b'\0')
    for m in masters:
        header += field('MAST', real[m].encode('latin1') + b'\0') + field('DATA', struct.pack('<Q', 0))
    out = b'TES4' + struct.pack('<III', len(header), LIGHT, 0) + struct.pack('<IHH', 0, 131, 0) + header + body
    pathlib.Path(a.out).write_bytes(out)
    print(f'{a.out}: {len(want)} records, masters {[real[m] for m in masters]}')
    for r in report:
        print('  ' + r)


if __name__ == '__main__':
    main()
