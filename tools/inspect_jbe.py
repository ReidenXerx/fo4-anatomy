"""What JaneBod Extended (the A-3 reference) actually does with ZeX's genital bones.

  1. Its body mesh: shapes, vertex counts, which genital bones carry weight, how much, where.
  2. Whether its genital region lines up with ours (a proximity weight copy needs it to).
  3. Its OCBP config: which bones get physics, with what settings.
  4. Its "modified ZeX skeleton": what differs from the installed ZeX 6.0 skeleton.

Reads inputs/jbe (copied from the owner's Vortex staging; gitignored, A-2).
"""
import collections
import json
import math
import pathlib
import re

import align_body as ab
import nif

ROOT = pathlib.Path(__file__).resolve().parent.parent
JBE = ROOT / 'inputs/jbe/JaneBodVag'
DATA = ab.DEFAULT_DATA
GENITAL = re.compile(r'(?i)vagina|anus|penis|clit')


def main():
    body = nif.Nif(JBE / 'Data/Tools/BodySlide/ShapeData/JaneBodVag-CBBE-CBP/JaneBodVag-CBBE-CBP.nif')
    print('1. JBE body mesh')
    for s in body.shapes():
        bones, xf = body.skin(s)
        gen = [b for b in bones if b and GENITAL.search(b)]
        print(f'   shape {s.name!r}: {s.count} vertices, {len(bones)} bones; genital bones: {gen or "none"}')
        if not gen:
            continue
        pos = s.positions()
        per = collections.defaultdict(list)
        for v in range(s.count):
            for slot, w in s.skin_weights(v):
                if bones[slot] in gen:
                    per[bones[slot]].append((w, v))
        for b in sorted(per):
            ws = per[b]
            o = nif.bone_origin(xf[bones.index(b)])
            cx = tuple(sum(pos[v][a] * w for w, v in ws) / sum(w for w, _ in ws) for a in range(3))
            strong = sum(1 for w, _ in ws if w > 0.5)
            print(f'      {b:18} origin ({o[0]:6.2f},{o[1]:6.2f},{o[2]:7.2f})  {len(ws):5} vertices (>0.5: {strong:4})'
                  f'  max {max(w for w, _ in ws):.2f}  weighted centre ({cx[0]:6.2f},{cx[1]:6.2f},{cx[2]:7.2f})')
        # co-weights: which other bones share vertices with the genital bones
        co = collections.Counter()
        for v in range(s.count):
            ws = s.skin_weights(v)
            if any(bones[k] in gen for k, _ in ws):
                for k, w in ws:
                    if bones[k] not in gen:
                        co[bones[k]] += 1
        print(f'      bones sharing those vertices: {co.most_common(8)}')

        # 2. alignment with our body's genital geometry
        ours = nif.Nif(ab.OUT / 'ShapeData' / ab.DATA_FOLDER / f'{ab.DATA_FOLDER}.nif').shape(ab.SHAPE)
        mapping = {int(j) for j in json.loads((ab.OUT / 'mapping.json').read_text())['output_to_cbbe']}
        opos = ours.positions()
        new = [j for j in range(ours.count) if j not in mapping]
        grid = ab.Grid(pos, [v for v in range(s.count)])
        ds = sorted(math.dist(opos[j], pos[grid.nearest(opos[j], 1, limit=10)[0]]) if grid.nearest(opos[j], 1, limit=10) else 99
                    for j in new)
        print(f'2. our {len(new)} genital vertices -> nearest JBE vertex: median {ds[len(ds) // 2]:.2f}, '
              f'90% {ds[int(len(ds) * 0.9)]:.2f}, max {ds[-1]:.2f} units')
        jw = [v for b in per for _, v in per[b]]
        jc = tuple(sum(pos[v][a] for v in jw) / len(jw) for a in range(3))
        oc = tuple(sum(opos[j][a] for j in new) / len(new) for a in range(3))
        print(f'   JBE genital-weighted centre ({jc[0]:.2f},{jc[1]:.2f},{jc[2]:.2f}) vs our new geometry centre '
              f'({oc[0]:.2f},{oc[1]:.2f},{oc[2]:.2f})')

    print('\n3. JBE ocbp.ini')
    ini = (JBE / 'Optional - OCBP Settings/Modified 3B Skeleton (Included)/Data/F4SE/Plugins/ocbp.ini').read_text(errors='replace')
    attach = re.search(r'\[Attach\](.*?)(?:\n\[)', ini, re.S)
    if attach:
        for line in attach.group(1).splitlines():
            if line.strip() and not line.strip().startswith(';'):
                print('   ', line.strip())
    for sec in re.findall(r'^\[([^\]]+)\]', ini, re.M):
        if re.search(r'(?i)vag|anus|pussy|labia|genit', sec):
            body_ = re.search(r'\[%s\](.*?)(?:\n\[|\Z)' % re.escape(sec), ini, re.S).group(1)
            vals = {k: v for k, v in re.findall(r'^(\w+)=([^\s;]+)', body_, re.M)}
            print(f'   [{sec}] {vals}')
    print('   [General]', re.search(r'\[General\](.*?)\n\[', ini, re.S).group(1).strip().replace('\n', ' | ') if '[General]' in ini else '')

    print('\n4. JBE skeleton vs installed ZeX')
    zex = nif.Nif(DATA / 'Meshes/Actors/Character/CharacterAssets/skeleton.nif')
    jsk = nif.Nif(JBE / 'Optional - Skeleton/Data/Meshes/actors/character/characterassets/skeleton.nif')

    def table(sk):
        parent = {}
        for i, n in sk.nodes.items():
            for k in n['kids']:
                parent[k] = i
        return {n['name']: (sk.nodes[parent[i]]['name'] if i in parent else None, n['t'], n['r'])
                for i, n in sk.nodes.items() if n['name']}
    zt, jt = table(zex), table(jsk)
    print(f'   nodes: ZeX {len(zt)}, JBE {len(jt)}; only in JBE: {sorted(set(jt) - set(zt))[:20]}; only in ZeX: {sorted(set(zt) - set(jt))[:20]}')
    for name in sorted(set(zt) & set(jt)):
        zp, ztr, zr = zt[name]
        jp, jtr, jr = jt[name]
        dt = max(abs(a - b) for a, b in zip(ztr, jtr))
        dr = max(abs(a - b) for a, b in zip(zr, jr))
        if zp != jp or dt > 1e-3 or dr > 1e-3:
            print(f'   {name:24} parent {zp} -> {jp};  translation moved {dt:.3f}; rotation changed {dr:.3f}')


if __name__ == '__main__':
    main()
