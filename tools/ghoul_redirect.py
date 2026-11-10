"""Which ghoul skin textures the player's game uses, and the light plugin that points the game at OUR rotten copies
(2026-11-09, option 1). The builder never writes over another mod's files (MO2 writes into the owning mod, Vortex
flags the change), so the rotten maps go to Textures/Anatomy/Ghoul/ and this plugin redirects the texture sets:

  TXST (winning version in the load order)       what wears it                 how it names its maps
  Fallout4.esm 0518FC SkinBodyGhoulMale           men's body + men's rear head  MNAM (a BGSM)
  Fallout4.esm 04A833 SkinHandGhoulMale           men's hands                   MNAM
  Fallout4.esm 0F6E5D SkinHandGhoulFemale         women's hands                 MNAM
  Fallout4.esm 0F6E5B SkinBodyGhoulFemale_1       women's body (CBBE)           TX00/TX01/TX07 (CBBEHolyFix.esp's)
  CBBEHolyFix.esp 000006 SkinHeadGhoulRearCBBE    women's rear head             TX00/TX01/TX07
  Fallout4.esm 0F6E5C SkinHeadGhoulFemale         women's face                  MNAM
A MNAM texture set gets OUR BGSM (the game's BGSM, its three maps renamed) and MNAM pointed at it; a TX set gets its
TX00/01/07 renamed. TXST records carry no form ids, so a copy of the winning record with those fields changed is the
whole override. The men's face has no texture set (its head part names none) and is left as it is: only a male ghoul
PLAYER shows that texture (NPC faces are baked FaceGen), and the face's own edge stays untouched by design.
"""
import pathlib
import re
import struct

import plugin_merge as pm

PLUGIN = 'Anatomy Ghoul Skin.esp'
LIGHT = 0x200
AUTHOR = 'Anatomy Builder (fo4-anatomy tools/ghoul_redirect.py)'
CA = 'meshes/actors/character/characterassets/'
SETS = [  # key, owner, local id, sex, layers, our stem
    ('male body', 'fallout4.esm', 0x0518FC, 'M', ['body', 'rear'], 'GhoulMaleBody'),
    ('male hands', 'fallout4.esm', 0x04A833, 'M', ['hands'], 'GhoulMaleHands'),
    ('female hands', 'fallout4.esm', 0x0F6E5D, 'F', ['hands'], 'GhoulFemaleHands'),
    ('female body', 'fallout4.esm', 0x0F6E5B, 'F', ['body'], 'GhoulFemaleBody'),
    ('female rear head', 'cbbeholyfix.esp', 0x000006, 'F', ['rear'], 'GhoulFemaleHeadRear'),
    ('female face', 'fallout4.esm', 0x0F6E5C, 'F', ['head'], 'GhoulFemaleHead'),
]
MESHES = {'M': {'body': CA + 'malebody.nif', 'hands': CA + 'malehands.nif', 'head': CA + 'maleghoulhead.nif',
                'rear': CA + 'faceparts/maleghoulheadrear.nif'},
          'F': {'hands': CA + 'femalehands.nif', 'head': CA + 'femaleghoulhead.nif',
                'rear': CA + 'faceparts/femaleheadrear.nif'}}           # the women's body: the builder's own CBBE
KINDS = (('d', 'TX00'), ('n', 'TX01'), ('s', 'TX07'))


def winning(game, types=('TXST',)):
    """(owner, local id) -> (plugin name, its masters, record type, flags, subrecords) of the LAST plugin defining it"""
    out = {}
    for name in game.plugins:
        path = game.data / name
        if not path.exists():
            continue
        try:
            p = pm.Plugin(path, set(types))
        except (OSError, ValueError, struct.error):
            continue
        for key, (t, flags, subs) in p.records.items():
            out[key] = (p.name, p.masters, t, flags, subs)
    return out


def bgsm_maps(blob):
    """the BGSM's texture strings in order: [(offset of the length, string)] for every length-prefixed '...dds' """
    found = []
    for m in re.finditer(rb'[ -~]{3,}\.dds\0', blob, re.I):
        s0 = m.start()
        if s0 >= 4 and struct.unpack_from('<I', blob, s0 - 4)[0] == m.end() - s0:
            found.append((s0 - 4, blob[s0:m.end() - 1].decode('latin1')))
    return found


def bgsm_with(blob, new):
    """the BGSM with its first maps replaced: new = {'d': path, 'n': path, 's': path} (paths under textures/)"""
    maps = bgsm_maps(blob)
    if len(maps) < 3:
        raise SystemExit(f'a ghoul BGSM names {len(maps)} textures, expected diffuse, normal and specular first')
    out, o = bytearray(), 0
    for (off, _), k in zip(maps[:3], ('d', 'n', 's')):
        ln = struct.unpack_from('<I', blob, off)[0]
        s = new[k].encode('latin1') + b'\0'
        out += blob[o:off] + struct.pack('<I', len(s)) + s
        o = off + 4 + ln
    return bytes(out + blob[o:])


def plan(game):
    """[{key, sex, layers, stem, sources {kind: textures rel}, record (plugin, masters, flags, subs), mode, bgsm}]
    for every ghoul texture set the game has; a set whose maps are not all found is skipped with a reason"""
    win = winning(game)
    jobs, skipped = [], []
    for key, owner, lid, sex, layers, stem in SETS:
        rec = win.get((owner, lid))
        if rec is None:
            skipped.append(f'{key}: no {owner} {lid:06X} in the load order')
            continue
        plugin, masters, _, flags, subs = rec
        f = dict(subs)
        if 'MNAM' in f:
            mat = 'materials/' + f['MNAM'][:-1].decode('latin1').replace('\\', '/')
            if game.find(mat) is None:
                skipped.append(f'{key}: its material {mat} is not in the game')
                continue
            blob = game.read(mat)
            maps = [s for _, s in bgsm_maps(blob)[:3]]
            sources = {k: 'textures/' + m.replace('\\', '/') for k, m in zip(('d', 'n', 's'), maps)}
            mode = 'MNAM'
        else:
            sources = {k: 'textures/' + f[t][:-1].decode('latin1').replace('\\', '/') for k, t in KINDS if t in f}
            blob, mode = None, 'TX'
        if key == 'female body' and '/custombody/' not in sources.get('d', '').lower():
            # without CBBE HeadRear Absolute Fix (CBBEHolyFix.esp) this set names the VANILLA-layout ghoul texture, but
            # the women's body is CBBE (its own UVs): painting it through CBBE's UVs would scramble it
            if game.active('CBBEHolyFix.esp') and plugin.lower() != 'cbbeholyfix.esp':
                # (11-10 report: Ghouls Revamped.esp loaded after it; HolyPort, its optional tool, is not the answer)
                why = (f'{plugin} overrides it after CBBEHolyFix.esp with a vanilla-layout texture: load '
                       f'CBBEHolyFix.esp after {plugin} for the women\'s rotten skin (no HolyPort needed)')
            else:
                why = 'install "CBBE HeadRear Absolute Fix" (its main file) for the women\'s rotten skin'
            skipped.append(f'{key}: its texture set names {sources.get("d")}, not a CBBE (custombody) texture: {why}')
            continue
        missing = [r for r in sources.values() if game.find(r) is None]
        if len(sources) < 3 or missing:
            skipped.append(f'{key}: maps missing {missing or "(fewer than 3 named)"}')
            continue
        # the women's rear-head map is the vanilla BODY layout: only the rear head's own islands are ours to paint
        jobs.append(dict(key=key, sex=sex, layers=layers, stem=stem, sources=sources, mode=mode, bgsm=blob,
                         islands_only=key == 'female rear head', record=(owner, lid, plugin, flags, subs)))
    return jobs, skipped


def our_paths(stem):
    """published texture paths (Data-relative) and the in-record/in-BGSM names (relative to textures/)"""
    rel = {k: f'Textures/Anatomy/Ghoul/{stem}_{k}.dds' for k in ('d', 'n', 's')}
    name = {k: f'Anatomy\\Ghoul\\{stem}_{k}.dds' for k in ('d', 'n', 's')}
    return rel, name


def outputs(job):
    """{published path: bytes} for a job's BGSM (MNAM sets) and the TXST override's subrecords"""
    rel, name = our_paths(job['stem'])
    owner, lid, plugin, flags, subs = job['record']
    files, new = {}, []
    if job['mode'] == 'MNAM':
        files[f'Materials/Anatomy/Ghoul/{job["stem"]}.bgsm'] = bgsm_with(job['bgsm'], name)
        mnam = f'Anatomy\\Ghoul\\{job["stem"]}.bgsm'.encode('latin1') + b'\0'
        new = [(t, mnam if t == 'MNAM' else v) for t, v in subs]
    else:
        tx = {t: name[k].encode('latin1') + b'\0' for k, t in KINDS}
        new = [(t, tx.get(t, v)) for t, v in subs]
    return files, (owner, lid, flags, new)


# the ghoul women's genitals (2026-11-09): no separate body mesh. The ghoul torso's women's model (the player's own
# built FemaleBody.nif) gets a material swap, AnatomyGenitals.bgsm -> AnatomyGenitalsGhoul.bgsm, on these ARMAs:
TORSOS = [('fallout4.esm', 0x0EAFB9), ('dlcnukaworld.esm', 0x0383AE)]       # NakedGhoulTorso, ...TorsoGlowing
GENITAL_SWAP = ('Anatomy\\AnatomyGenitals.bgsm', 'Anatomy\\AnatomyGenitalsGhoul.bgsm')
ARMA_FIDS = {'RNAM', 'NAM0', 'NAM1', 'NAM2', 'NAM3', 'MODL', 'SNDD', 'ONAM', 'MO2S', 'MO3S', 'MO4S', 'MO5S'}


def torso_records(game):
    """the winning torso ARMAs and the MSWPs they already use: [(owner, lid, plugin, plugin masters, flags, subs)],
    {(owner, lid): swap pairs} """
    win = winning(game, ('ARMA', 'MSWP'))
    torsos = [(o, l) + (win[(o, l)][0], win[(o, l)][1], win[(o, l)][3], win[(o, l)][4]) for o, l in TORSOS
              if (o, l) in win]
    pairs = {}
    for o, l, plugin, masters, flags, subs in torsos:
        f = dict(subs)
        if 'MO3S' in f:
            fid = struct.unpack('<I', f['MO3S'])[0]
            src = [m.lower() for m in masters] + [plugin.lower()]
            key = (src[min(fid >> 24, len(src) - 1)], fid & 0xFFFFFF)
            if key in win:
                ws = win[key][4]
                pairs[(o, l)] = [(ws[i][1], ws[i + 1][1]) for i in range(len(ws) - 1)
                                 if ws[i][0] == 'BNAM' and ws[i + 1][0] == 'SNAM']
    return torsos, pairs


def write_plugin(path, overrides, active, torsos=(), swap_pairs=None):
    """overrides: [(owner, local id, flags, TXST subrecords)]; torsos: torso_records()[0]. Masters: Fallout4.esm, the
    plugins owning or last defining each record (so this one loads after them), in load order."""
    order = {p.lower(): i for i, p in enumerate(active)}
    cased = {p.lower(): p for p in active}
    need = {'fallout4.esm'}
    for owner, *_ in overrides:
        need.add(owner)
    if any(p.lower() == 'cbbeholyfix.esp' for p in active):            # it overrides 0F6E5B: load after it
        need.add('cbbeholyfix.esp')
    for o, l, plugin, masters, flags, subs in torsos:
        src = [m.lower() for m in masters] + [plugin.lower()]
        need |= {o, plugin.lower()}
        for t, v in subs:
            if t in ARMA_FIDS and len(v) == 4 and struct.unpack('<I', v)[0]:
                need.add(src[min(struct.unpack('<I', v)[0] >> 24, len(src) - 1)])
    masters = [cased.get(n, n) for n in sorted(need, key=lambda n: order.get(n, 10 ** 6))]
    idx = {m.lower(): i for i, m in enumerate(masters)}
    own = len(masters)
    groups = {'TXST': b'', 'ARMA': b'', 'MSWP': b''}
    count, nid = 0, 0x800

    def rec(typ, fid, flags, subs):
        body = b''.join(pm.field(t, v) for t, v in subs)
        return typ.encode() + struct.pack('<III', len(body), flags & ~0x40000, fid) + struct.pack('<IHH', 0, 131, 0) \
            + body
    for owner, lid, flags, subs in overrides:
        groups['TXST'] += rec('TXST', (idx[owner] << 24) | lid, flags, subs)
        count += 1
    for o, l, plugin, pmasters, flags, subs in torsos:
        src = [m.lower() for m in pmasters] + [plugin.lower()]
        pairs = [(b, s) for b, s in (swap_pairs or {}).get((o, l), [])
                 if b[:-1].decode('latin1').lower() != GENITAL_SWAP[0].lower()]
        pairs.append((GENITAL_SWAP[0].encode('latin1') + b'\0', GENITAL_SWAP[1].encode('latin1') + b'\0'))
        sw = (own << 24) | nid
        nid += 1
        msubs = [('EDID', f'AnatomyGhoulGenitalsSwap{l:06X}'.encode() + b'\0')]
        for b, s in pairs:
            msubs += [('BNAM', b), ('SNAM', s)]
        groups['MSWP'] += rec('MSWP', sw, 0, msubs)
        new = []
        for t, v in subs:
            if t == 'MO3S':
                continue                                     # replaced by ours (its pairs are carried over)
            if t in ARMA_FIDS and len(v) == 4:
                fid = struct.unpack('<I', v)[0]
                v = struct.pack('<I', 0 if not fid else (idx[src[min(fid >> 24, len(src) - 1)]] << 24) |
                                (fid & 0xFFFFFF))
            new.append((t, v))
        # the women's model block is MOD3, MO3T, MO3C, MO3F, MO3S (xEdit's order): ours goes after its last field
        last = max((i for i, (t, _) in enumerate(new) if t in ('MOD3', 'MO3T', 'MO3C', 'MO3F')), default=None)
        if last is None:
            raise SystemExit(f'{o} {l:06X}: the ghoul torso has no women\'s model (MOD3)')
        new.insert(last + 1, ('MO3S', struct.pack('<I', sw)))
        groups['ARMA'] += rec('ARMA', (idx[o] << 24) | l, flags, new)
        count += 2
    body = b''
    for typ in ('TXST', 'ARMA', 'MSWP'):                         # FO4's top-group order
        if groups[typ]:
            body += b'GRUP' + struct.pack('<I', 24 + len(groups[typ])) + typ.encode() + struct.pack('<i', 0) \
                + struct.pack('<IHH', 0, 0, 0) + groups[typ]
    hdr = pm.field('HEDR', struct.pack('<fiI', 1.0, count, nid)) + pm.field('CNAM', AUTHOR.encode() + b'\0')
    for m in masters:
        hdr += pm.field('MAST', m.encode('latin1') + b'\0') + pm.field('DATA', struct.pack('<Q', 0))
    pathlib.Path(path).write_bytes(b'TES4' + struct.pack('<III', len(hdr), LIGHT, 0) + struct.pack('<IHH', 0, 131, 0)
                                   + hdr + body)
    return masters
