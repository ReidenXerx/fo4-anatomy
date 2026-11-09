"""BSSubIndexTriShape segment data per shape (FO4): segments + sub-segments (start, count, parent/array index),
shared data (user index, bone id, cut offsets) and the .ssf path; compare two nifs.
    python -I seg_dump.py <a.nif> [<b.nif>]"""
import struct
import sys

sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import nif  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def segs(path):
    m = nif.Nif(path)
    out = {}
    for s in m.shapes():
        if m.types[s.index] != 'BSSubIndexTriShape':
            out[s.name] = None
            continue
        o = s.data_at + s.count * s.stride + 6 * s.triangle_count
        end = m.offsets[s.index][0] + m.offsets[s.index][1]
        u = lambda: struct.unpack_from('<I', m.b, o)[0]                         # noqa: E731
        nprim, nseg, total = struct.unpack_from('<3I', m.b, o)
        o += 12
        seg = []
        for _ in range(nseg):
            start, cnt, par, nsub = struct.unpack_from('<4I', m.b, o)
            o += 16
            subs = []
            for _ in range(nsub):
                subs.append(struct.unpack_from('<4I', m.b, o)[:3])
                o += 16
            seg.append((start, cnt, par, subs))
        shared = None
        if nseg < total:
            n2, t2 = struct.unpack_from('<2I', m.b, o)
            o += 8
            starts = list(struct.unpack_from(f'<{n2}I', m.b, o))
            o += 4 * n2
            per = []
            for _ in range(t2):
                ui, bone, nc = struct.unpack_from('<3I', m.b, o)
                o += 12
                cuts = struct.unpack_from(f'<{nc}f', m.b, o)
                o += 4 * nc
                per.append((ui, hex(bone), [round(x, 3) for x in cuts]))
            ln = struct.unpack_from('<H', m.b, o)[0]
            ssf = m.b[o + 2:o + 2 + ln].decode('latin1')
            o += 2 + ln
            shared = dict(starts=starts, per=per, ssf=ssf)
        out[s.name] = dict(nprim=nprim, tri=s.triangle_count, seg=seg, shared=shared, tail=end - o)
    return out


a = segs(sys.argv[1])
b = segs(sys.argv[2]) if len(sys.argv) > 2 else None
for name, d in a.items():
    print('==', name)
    if d is None:
        print('   (BSTriShape)', '' if not b or name not in b else ('B: ' + ('BSTriShape' if b[name] is None else 'SUBINDEX')))
        continue
    print(f'   prims {d["nprim"]} tris {d["tri"]} segs {[(s[0], s[1], s[2], len(s[3])) for s in d["seg"]]} tail {d["tail"]}')
    for s in d['seg']:
        if s[3]:
            print('      subs', s[3])
    if d['shared']:
        print('   shared starts', d['shared']['starts'], 'ssf', d['shared']['ssf'])
        print('   per', d['shared']['per'])
    if b is not None:
        e = b.get(name, 'MISSING')
        if e == 'MISSING' or e is None:
            print('   B:', e if e else 'BSTriShape')
        else:
            same = (e['seg'] == d['seg'], e['shared'] == d['shared'])
            print(f'   B: prims {e["nprim"]} tris {e["tri"]} segs {[(s[0], s[1], s[2], len(s[3])) for s in e["seg"]]}'
                  f' identical(seg, shared)={same}')
            if not same[1] and e['shared']:
                print('   B shared starts', e['shared']['starts'], 'ssf', e['shared']['ssf'])
                print('   B per', e['shared']['per'])
            if not same[0]:
                for s in e['seg']:
                    if s[3]:
                        print('      B subs', s[3])
