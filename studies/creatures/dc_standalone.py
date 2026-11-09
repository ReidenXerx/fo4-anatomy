"""Standalone deathclaw genitals (Dudu 11-09: no UAP files - own nif + material + texture paths, own light plugin).
  meshes\\Actors\\Deathclaw\\Anatomy\\DeathclawMale.nif (+ .tri)    Base (vent lips, vanilla Deathclaw.BGSM, body UVs)
                                                                     + Penis (DeathclawPenis.bgsm)
  meshes\\Actors\\Deathclaw\\Anatomy\\DeathclawFemale.nif (+ .tri)  VulvaLips + VulvaInner (penis material, lining rows)
  The nifs are PyNifly exports of OUR shapes only (no vanilla shape round-tripped), seg_fix'ed (torso4), strings
  cleaned (root name, BODYTRI path).
  Materials\\Anatomy\\Creatures\\DeathclawPenis / DeathclawPenisAlbino / DeathclawPenisGlowing.bgsm = the vanilla
  deathclaw / albino / glowing BGSMs with their textures retargeted to ours (dc_tex.py ... anatomy).
  Plugins (light, built by plugin()):
    'Anatomy Deathclaws.esp'              master Fallout4.esm
    'Anatomy Deathclaws - UAP.esp'        same records + master Deathclaw_nude.esp: loads after UAP, so our skin
                                          overrides (vanilla body + ours, no UAP penis) win; FOMOD picks one, both
                                          are renamed to 'Anatomy Deathclaws.esp' at install
    records: 5 MSWP (body + penis colour per variant), 6 ARMA (male + female model, one per skin), 6 ARMO overrides
    (the vanilla deathclaw skins + our ARMA, BOD2 + slot 34).
    python -I dc_standalone.py <out Data> <plugins dir>"""
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-anatomy\tools')
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import esl  # noqa: E402
import gamedata  # noqa: E402
import nif  # noqa: E402

out, plug_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
D = pathlib.Path(r'D:\F4Output\creatures\dc')
DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
VAN = D / 'vanilla' / 'deathclaw.nif'
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
REL = 'meshes/Actors/Deathclaw/Anatomy'
MODEL = {'male': 'Actors\\Deathclaw\\Anatomy\\DeathclawMale', 'female': 'Actors\\Deathclaw\\Anatomy\\DeathclawFemale'}
PEN = ['Materials\\Anatomy\\Creatures\\DeathclawPenis.bgsm', 'textures\\Anatomy\\Creatures\\DeathclawPenis_d.dds',
       'textures\\Anatomy\\Creatures\\DeathclawPenis_n.dds', 'textures\\Anatomy\\Creatures\\DeathclawPenis_s.dds']


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(' '.join(map(str, cmd))[:300] + '\n' + r.stdout[-1500:] + r.stderr[-1500:])
    return r.stdout


def meshes():
    run([sys.executable, '-I', str(HERE / 'dc_geom.py'), str(D / 'geom_male.json'), str(D / 'geom_female.json')])
    (out / REL).mkdir(parents=True, exist_ok=True)
    for g, inner in (('male', 'Penis'), ('female', 'VulvaInner')):
        G = json.load(open(D / f'geom_{g}.json'))
        G[inner]['mat'] = PEN
        gj = D / 'build_sa' / f'geom_{g}.json'
        gj.parent.mkdir(parents=True, exist_ok=True)
        json.dump(G, open(gj, 'w'))
        exp = D / 'build_sa' / f'{g}.nif'
        print([l for l in run([BL, '-b', '-P', str(HERE / 'dc_build.py'), '--', str(gj), str(VAN), str(exp)])
              .splitlines() if l.startswith('BUILT')])
        print(run([sys.executable, '-I', str(HERE / 'seg_fix.py'), str(VAN), str(exp), 'torso4'])[:160])
        run([sys.executable, '-I', str(HERE / 'tri_normalize.py'), str(exp.with_suffix('.tri'))])
        m = nif.Nif(exp)
        for sn, gg in G.items():
            if sn.startswith('_'):
                continue
            P, Q = [__import__('numpy').array(x) for x in (m.shape(sn).positions(), gg['verts'])]
            if len(P) != len(Q) or abs(P - Q).max() > 0.1:
                raise SystemExit(f'{g} {sn}: export {len(P)} v vs json {len(Q)}')
        root = m.strings[0]
        tri_s = next(s for s in m.strings if s.lower().endswith('.tri'))
        dst = out / REL / (MODEL[g].split('\\')[-1] + '.nif')
        m.save_renamed(dst, {root: 'Scene Root', tri_s: MODEL[g] + '.tri'})
        shutil.copyfile(exp.with_suffix('.tri'), dst.with_suffix('.tri'))
        chk = nif.Nif(dst)
        print(g, [s.name for s in chk.shapes()], [s for s in chk.strings if s.endswith(('.tri', '.bgsm', '.BGSM'))])


def materials():
    run([sys.executable, '-I', str(HERE / 'dc_tex.py'), str(out), '37.9', 'anatomy'])
    mats = gamedata.Ba2(DATA / 'Fallout4 - Materials.ba2')
    T = 'Anatomy/Creatures/DeathclawPenis'
    for src, name, repl in (
            ('deathclaw', 'DeathclawPenis', {'_d': T + '_d.dds', '_n': T + '_n.dds', '_s': T + '_s.dds'}),
            ('deathclawalbino', 'DeathclawPenisAlbino', {'_d': T + 'Albino_d.dds', '_n': T + '_n.dds',
                                                         '_s': T + '_s.dds'}),
            ('deathclawglowing', 'DeathclawPenisGlowing', {'_d': T + '_d.dds', '_n': T + '_n.dds', '_s': T + '_s.dds',
                                                           '_g': T + '_g.dds'})):
        b = mats.read(f'materials\\actors\\deathclaw\\{src}.bgsm')
        o, res, n = 0, bytearray(), 0
        for mt in re.finditer(rb'(?i)actors/deathclaw/[a-z]*(_[dnsg])\.dds\0', b):
            s0 = mt.start()
            ln = struct.unpack_from('<I', b, s0 - 4)[0]
            if s0 + ln != mt.end():
                raise SystemExit(f'{src}: unexpected BGSM layout')
            new = repl[mt.group(1).decode().lower()].encode() + b'\0'
            res += b[o:s0 - 4] + struct.pack('<I', len(new)) + new
            o = mt.end()
            n += 1
        res += b[o:]
        if n != len(repl):
            raise SystemExit(f'{src}: retargeted {n} of {len(repl)}')
        dst = out / 'materials/anatomy/creatures' / f'{name}.bgsm'
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(bytes(res))
        print('bgsm', name, [x.decode() for x in re.findall(rb'[ -~]{8,}\.dds', bytes(res))])


# ---------------------------------------------------------------- plugin
VARIANTS = [  # name, vanilla skin ARMO, body swap target (None = regular), penis swap
    ('', 0x01DB49, None, None),
    ('Albino', 0x1955A7, 'actors\\deathclaw\\DeathclawAlbino.BGSM', 'Anatomy\\Creatures\\DeathclawPenisAlbino.bgsm'),
    ('Alpha', 0x1955AB, 'actors\\deathclaw\\DeathclawAlpha.BGSM', None),
    ('Savage', 0x1955B1, 'actors\\deathclaw\\DeathclawSavage.BGSM', None),
    ('Glowing', 0x1955B4, 'actors\\deathclaw\\DeathclawGlowing.BGSM', 'Anatomy\\Creatures\\DeathclawPenisGlowing.bgsm'),
    ('Matriarch', 0x1955AE, 'actors\\deathclaw\\DeathclawMatriarch.BGSM', None),
    # 1.0.1 (Ivy run, 11-10: chameleons loaded no genitals): its body's own material is DeathclawChameleonBase
    ('Chameleon', 0x1C88AE, 'actors\\deathclaw\\DeathclawChameleonBase.BGSM', None),
]
VANILLA_WHOLE = 0x01DB4B
SLOT34 = 0x10


def subs(d):
    o, res = 0, []
    while o + 6 <= len(d):
        t, n = d[o:o + 4], struct.unpack_from('<H', d, o + 4)[0]
        res.append((t, d[o + 6:o + 6 + n]))
        o += 6 + n
    return res


def pack(sl):
    return b''.join(t + struct.pack('<H', len(v)) + v for t, v in sl)


def zs(s):
    return s.encode('latin1') + b'\0'


def build_records(own):
    """own = master index of this plugin's own records"""
    fo4 = esl.Plugin(DATA / 'Fallout4.esm')
    want = {v[1] for v in VARIANTS} | {VANILLA_WHOLE}
    van = {}
    for r in fo4.records:
        if r[0] == 'R' and r[3] in want and r[2] in ('ARMO', 'ARMA'):
            van[r[3]] = (r[4], fo4.body(r))
    if len(van) != len(want):
        raise SystemExit(f'found {len(van)} of {len(want)} vanilla records')
    whole = dict(subs(van[VANILLA_WHOLE][1]))
    nid = 0x800
    mswp, arma, armo = [], [], []
    for name, skin, body_to, pen_to in VARIANTS:
        sw = None
        if body_to:
            sl = [(b'EDID', zs(f'AnatomyDeathclaw{name}Swap')), (b'BNAM', zs('actors\\deathclaw\\deathclaw.bgsm')),
                  (b'SNAM', zs(body_to))]
            if pen_to:
                sl += [(b'BNAM', zs('Anatomy\\Creatures\\DeathclawPenis.bgsm')), (b'SNAM', zs(pen_to))]
            sw = (own << 24) | nid
            nid += 1
            mswp.append((sw, 0, pack(sl)))
        mo_t = bytes([4] + [0] * 19)                          # model info header with no texture hashes
        sl = [(b'EDID', zs(f'AnatomyDeathclawGenitals{name}')), (b'BOD2', struct.pack('<I', SLOT34)),
              (b'RNAM', whole[b'RNAM']), (b'DNAM', whole[b'DNAM']),
              (b'MOD2', zs(MODEL['male'] + '.nif')), (b'MO2T', mo_t)]
        if sw:
            sl.append((b'MO2S', struct.pack('<I', sw)))
        sl += [(b'MOD3', zs(MODEL['female'] + '.nif')), (b'MO3T', mo_t)]
        if sw:
            sl.append((b'MO3S', struct.pack('<I', sw)))
        sl += [(b'SNDD', whole[b'SNDD']), (b'ONAM', whole[b'ONAM'])]
        aid = (own << 24) | nid
        nid += 1
        arma.append((aid, 0, pack(sl)))
        # the vanilla skin + our addon (UAP's penis ARMA is NOT carried: ours replaces it)
        flags, body = van[skin]
        sl = subs(body)
        sl = [(t, struct.pack('<I', struct.unpack('<I', v)[0] | SLOT34) if t == b'BOD2' else v) for t, v in sl]
        last = max(i for i, (t, _) in enumerate(sl) if t == b'MODL')
        sl = sl[:last + 1] + [(b'INDX', b'\0\0'), (b'MODL', struct.pack('<I', aid))] + sl[last + 1:]
        armo.append((skin, flags & ~0x00040000, pack(sl)))
    return {'ARMO': armo, 'ARMA': arma, 'MSWP': mswp}, nid


def write_plugin(path, masters, groups, next_id):
    def field(t, v):
        return t + struct.pack('<H', len(v)) + v
    body, count = b'', 0
    for typ in ('ARMO', 'ARMA', 'MSWP'):                      # FO4 top-group order
        g = b''
        for fid, flags, rb in groups[typ]:
            g += typ.encode() + struct.pack('<III', len(rb), flags, fid) + struct.pack('<IHH', 0, 131, 0) + rb
            count += 1
        body += b'GRUP' + struct.pack('<I', 24 + len(g)) + typ.encode() + struct.pack('<I', 0) \
            + struct.pack('<IHH', 0, 0, 0) + g
    hdr = field(b'HEDR', struct.pack('<fiI', 1.0, count, next_id)) + field(b'CNAM', b'Anatomy\0')
    for m in masters:
        hdr += field(b'MAST', m.encode() + b'\0') + field(b'DATA', struct.pack('<Q', 0))
    path.write_bytes(b'TES4' + struct.pack('<III', len(hdr), esl.LIGHT, 0) + struct.pack('<IHH', 0, 131, 0)
                     + hdr + body)


def plugin():
    plug_dir.mkdir(parents=True, exist_ok=True)
    for fname, masters in (('Anatomy Deathclaws.esp', ['Fallout4.esm']),
                           ('Anatomy Deathclaws - UAP.esp', ['Fallout4.esm', 'Deathclaw_nude.esp'])):
        groups, nid = build_records(len(masters))
        write_plugin(plug_dir / fname, masters, groups, nid)
        p = esl.Plugin(plug_dir / fname)                      # read back
        print(fname, p.masters, [(r[2], hex(r[3])) for r in p.records if r[0] == 'R'])


if __name__ == '__main__':
    meshes()
    materials()
    plugin()
