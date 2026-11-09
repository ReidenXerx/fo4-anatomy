"""'Anatomy Deathclaws - Ivy Patch.esp' (Ivy only, Fallout-collection 11-10): our deathclaw genitals on the deathclaw
skins of depo.esp (DEPO: 8 Moj/Mythic skins + ClawBeast), MutantMenagerie.esm (fog deathclaw) and OldTimeReligion.esp
(Wrathclaw). Bodies that are a vanilla deathclaw mesh (ClawBeast, fog, Wrathclaw) use our standard meshes; DEPO's own
bodies (Moj, Moj matriarch, Moj chameleon, Mythic) sit elsewhere (vent 4-7 units off / 1.6 sunk on ours), so the vent
and penis are re-fitted to each (dc_geom with DC_BODY): meshes\\Actors\\Deathclaw\\Anatomy\\DeathclawMale_<Body>.nif.
Every skin gets its own genital ARMA, its lips swapped to the material its body really wears (the body shape's own
material, after the skin ARMA's own swap). The winning skin ARMOs are overridden (form ids remapped), plus our ARMA.
    python -I dc_ivy_patch.py <out Data>"""
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
import gamedata  # noqa: E402
import ghoul_redirect as gr  # noqa: E402
import nif  # noqa: E402
import plugin_merge as pm  # noqa: E402
from transplant import _shape_refs_at  # noqa: E402

out = pathlib.Path(sys.argv[1])
D = pathlib.Path(r'D:\F4Output\creatures\dc')
SURVEY = D / 'ivy_survey'
VAN = D / 'vanilla' / 'deathclaw.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/Actors/Deathclaw/Anatomy'
NAME = 'Anatomy Deathclaws - Ivy Patch.esp'
PEN = ['Materials\\Anatomy\\Creatures\\DeathclawPenis.bgsm', 'textures\\Anatomy\\Creatures\\DeathclawPenis_d.dds',
       'textures\\Anatomy\\Creatures\\DeathclawPenis_n.dds', 'textures\\Anatomy\\Creatures\\DeathclawPenis_s.dds']
BODIES = {'Moj': 'MojDeathclaw.nif', 'MojMatriarch': 'MojDeathclaw_Matriarch.nif',
          'MojChameleon': 'MojDeathclawChameleon.nif', 'Mythic': 'Deathclaw_mythic.nif'}
SKINS = [  # (owner, local id, body key or None = our standard meshes)
    ('depo.esp', 0x000009, 'Moj'), ('depo.esp', 0x00000D, 'Moj'), ('depo.esp', 0x00000E, 'Moj'),
    ('depo.esp', 0x000A8C, 'Moj'), ('depo.esp', 0x000A8D, 'Moj'), ('depo.esp', 0x000A8E, 'MojMatriarch'),
    ('depo.esp', 0x000015, 'MojChameleon'), ('depo.esp', 0x0009F8, 'Mythic'), ('depo.esp', 0x000A92, None),
    ('mutantmenagerie.esm', 0x011C10, None), ('oldtimereligion.esp', 0x03980A, None)]
MASTERS_WANTED = {'fallout4.esm', 'depo.esp', 'mutantmenagerie.esm', 'oldtimereligion.esp', 'anatomy deathclaws.esp'}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True,
                       env=dict(__import__('os').environ, **ENV))
    if r.returncode:
        raise SystemExit(' '.join(map(str, cmd))[:200] + '\n' + r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


ENV = {}


def body_meshes(key, body_nif):
    """our male + female deathclaw meshes re-fitted to this body"""
    ENV['DC_BODY'] = str(body_nif)
    w = D / 'ivy_build' / key
    w.mkdir(parents=True, exist_ok=True)
    print(run([sys.executable, '-I', HERE / 'dc_geom.py', w / 'geom_male.json', w / 'geom_female.json'])
          .splitlines()[3:5])
    for g, inner in (('male', 'Penis'), ('female', 'VulvaInner')):
        G = json.load(open(w / f'geom_{g}.json'))
        G[inner]['mat'] = PEN
        json.dump(G, open(w / f'geom_{g}_m.json', 'w'))
        exp = w / f'{g}.nif'
        run([BL, '-b', '-P', HERE / 'dc_build.py', '--', w / f'geom_{g}_m.json', VAN, exp])
        run([sys.executable, '-I', HERE / 'seg_fix.py', VAN, exp, 'torso4'])
        run([sys.executable, '-I', HERE / 'tri_normalize.py', exp.with_suffix('.tri')])
        m = nif.Nif(exp)
        for sn, gg in G.items():
            if not sn.startswith('_'):
                P, Q = np.array(m.shape(sn).positions()), np.array(gg['verts'])
                if len(P) != len(Q) or np.abs(P - Q).max() > 0.1:
                    raise SystemExit(f'{key} {g} {sn}: export differs from the json')
        stem = f'Deathclaw{"Male" if g == "male" else "Female"}_{key}'
        tri_s = next(s for s in m.strings if s.lower().endswith('.tri'))
        dst = out / REL / f'{stem}.nif'
        dst.parent.mkdir(parents=True, exist_ok=True)
        m.save_renamed(dst, {m.strings[0]: 'Scene Root', tri_s: f'Actors\\Deathclaw\\Anatomy\\{stem}.tri'})
        shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
    return (f'Actors\\Deathclaw\\Anatomy\\DeathclawMale_{key}.nif', f'Actors\\Deathclaw\\Anatomy\\DeathclawFemale_{key}.nif')


def body_material(model_path, game):
    """the material path (under Materials, as MSWPs name it) of the largest shape of a model"""
    rel = 'meshes/' + model_path.replace('\\', '/')
    p = D / 'ivy_build' / pathlib.Path(rel).name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(game.read(rel))
    m = nif.Nif(p)
    body = max(m.shapes(), key=lambda s: s.count)
    shader = struct.unpack_from('<3i', m.b, _shape_refs_at(m, body.index))[1]
    name = m.string(struct.unpack_from('<i', m.b, m.offsets[shader][0] + 4)[0])
    return re.sub(r'(?i)^materials[\\/]', '', name)


def main():
    game = gamedata.Game(pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data'))
    win = gr.winning(game, ('ARMO', 'ARMA', 'MSWP'))
    std = ('Actors\\Deathclaw\\Anatomy\\DeathclawMale.nif', 'Actors\\Deathclaw\\Anatomy\\DeathclawFemale.nif')
    models = {None: std}
    for key, f in BODIES.items():
        models[key] = body_meshes(key, SURVEY / f)
        print('fitted', key)
    order = {p.lower(): i for i, p in enumerate(game.plugins)}
    cased = {p.lower(): p for p in game.plugins}
    masters = [cased[n] for n in sorted(MASTERS_WANTED, key=lambda n: order.get(n, 10 ** 6)) if n in cased]
    idx = {m.lower(): i for i, m in enumerate(masters)}
    own = len(masters)
    whole = dict(win[('fallout4.esm', 0x01DB4B)][4])          # vanilla DeathclawWhole: DNAM, SNDD, ONAM

    def remap(plugin, pmasters, v):
        fid = struct.unpack('<I', v)[0]
        if not fid:
            return v
        src = [x.lower() for x in pmasters] + [plugin.lower()]
        owner = src[min(fid >> 24, len(src) - 1)]
        if owner not in idx:
            raise SystemExit(f'form id {fid:08X} of {plugin} points into {owner}, not a master of the patch')
        return struct.pack('<I', (idx[owner] << 24) | (fid & 0xFFFFFF))

    nid, groups, count, swaps = 0x800, {'ARMO': b'', 'ARMA': b'', 'MSWP': b''}, 0, {}

    def rec(typ, fid, flags, subs):
        body = b''.join(pm.field(t, v) for t, v in subs)
        return typ.encode() + struct.pack('<III', len(body), flags & ~0x40000, fid) + struct.pack('<IHH', 0, 131, 0) \
            + body
    mo_t = bytes([4] + [0] * 19)
    for owner, lid, bkey in SKINS:
        if (owner, lid) not in win:
            print(f'  {owner}:{lid:06X} not in the load order: skipped')
            continue
        plugin, pmasters, _, flags, subs = win[(owner, lid)]
        f = dict(subs)
        edid = f.get('EDID', b'')[:-1].decode('latin1')
        # the skin's own deathclaw ARMA -> the material its body wears (after that ARMA's swap)
        arma_key = next(gr_key for t, v in subs if t == 'MODL'
                        for gr_key in [tuple([([x.lower() for x in pmasters] + [plugin.lower()])[
                            min(struct.unpack('<I', v)[0] >> 24, len(pmasters))], struct.unpack('<I', v)[0] & 0xFFFFFF])])
        ap, am, _, _, asubs = win[arma_key]
        af = dict(asubs)
        mat = body_material(af['MOD2'][:-1].decode('latin1'), game)
        if 'MO2S' in af:
            sk = tuple([([x.lower() for x in am] + [ap.lower()])[min(struct.unpack('<I', af['MO2S'])[0] >> 24, len(am))],
                        struct.unpack('<I', af['MO2S'])[0] & 0xFFFFFF])
            ws = win.get(sk)
            for i in range(len(ws[4]) - 1 if ws else 0):
                if ws[4][i][0] == 'BNAM' and ws[4][i + 1][0] == 'SNAM' and \
                        ws[4][i][1][:-1].decode('latin1').lower() == mat.lower():
                    mat = ws[4][i + 1][1][:-1].decode('latin1')
        sw = None
        if mat.lower() != 'actors\\deathclaw\\deathclaw.bgsm':
            if mat.lower() not in swaps:
                swaps[mat.lower()] = (own << 24) | nid
                nid += 1
                groups['MSWP'] += rec('MSWP', swaps[mat.lower()], 0, [
                    ('EDID', f'AnatomyDeathclawIvySwap{len(swaps)}'.encode() + b'\0'),
                    ('BNAM', b'actors\\deathclaw\\deathclaw.bgsm\0'), ('SNAM', mat.encode('latin1') + b'\0')])
                count += 1
            sw = swaps[mat.lower()]
        male, female = models[bkey]
        aid = (own << 24) | nid
        nid += 1
        asl = [('EDID', f'AnatomyDeathclawGenitalsIvy_{edid}'.encode() + b'\0'), ('BOD2', struct.pack('<I', 0x10)),
               ('RNAM', remap(ap, am, af['RNAM'])), ('DNAM', whole['DNAM']),
               ('MOD2', male.encode() + b'\0'), ('MO2T', mo_t)]
        if sw:
            asl.append(('MO2S', struct.pack('<I', sw)))
        asl += [('MOD3', female.encode() + b'\0'), ('MO3T', mo_t)]
        if sw:
            asl.append(('MO3S', struct.pack('<I', sw)))
        asl += [('SNDD', remap('Fallout4.esm', [], whole['SNDD'])), ('ONAM', remap('Fallout4.esm', [], whole['ONAM']))]
        groups['ARMA'] += rec('ARMA', aid, 0, asl)
        new = []
        for t, v in subs:
            if t in ('RNAM', 'MODL') and len(v) == 4:
                v = remap(plugin, pmasters, v)
            if t == 'BOD2':
                v = struct.pack('<I', struct.unpack_from('<I', v)[0] | 0x10) + v[4:]
            new.append((t, v))
        last = max(i for i, (t, _) in enumerate(new) if t == 'MODL')
        new = new[:last + 1] + [('INDX', b'\0\0'), ('MODL', struct.pack('<I', aid))] + new[last + 1:]
        groups['ARMO'] += rec('ARMO', (idx[owner] << 24) | lid, flags, new)
        count += 2
        print(f'  {owner}:{lid:06X} {edid:28s} (winner {plugin}) -> {"standard" if bkey is None else bkey} meshes, '
              f'lips {mat}')
    body = b''
    for typ in ('ARMO', 'ARMA', 'MSWP'):
        if groups[typ]:
            body += b'GRUP' + struct.pack('<I', 24 + len(groups[typ])) + typ.encode() + struct.pack('<i', 0) \
                + struct.pack('<IHH', 0, 0, 0) + groups[typ]
    hdr = pm.field('HEDR', struct.pack('<fiI', 1.0, count, nid)) + pm.field('CNAM', b'Anatomy\0')
    for m in masters:
        hdr += pm.field('MAST', m.encode('latin1') + b'\0') + pm.field('DATA', struct.pack('<Q', 0))
    (out / NAME).write_bytes(b'TES4' + struct.pack('<III', len(hdr), 0x200, 0) + struct.pack('<IHH', 0, 131, 0)
                             + hdr + body)
    back = pm.Plugin(out / NAME, {'ARMO', 'ARMA', 'MSWP'})
    print(NAME, 'masters', masters, 'records', len(back.records))


if __name__ == '__main__':
    main()
