"""The builder's ghoul stage (Ghouls mod, 2026-11-09): the rotten ghoul skin and the ghoul women's genital texture,
made from the player's own installed textures, written to our paths, plus the plugin that points the game at them.

    stage(game, project_nif, anatomy_tex, work, size) -> {published path: file}

  Textures/Anatomy/Ghoul/<set>_d/n/s.dds       every ghoul skin set the game has (ghoul_redirect.SETS)
  Materials/Anatomy/Ghoul/<set>.bgsm           for the sets named by a material
  Textures/Anatomy/Ghoul/FemaleBody_d/n/s.dds  the ghoul women's genitals (our genital maps, ghoul-toned + rotted)
  Materials/Anatomy/AnatomyGenitalsGhoul.bgsm  AnatomyGenitals.bgsm with those maps
  Anatomy Ghoul Skin.esp                       (light) the texture-set redirects, and a material swap on the ghoul
                                               torsos' women's model: their genitals take AnatomyGenitalsGhoul.bgsm on
                                               the player's own built body (no second body mesh to build)
One map at a time (memory), each at `size` (2K default; 4K on request)."""
import pathlib
import re
import struct
import time

import ghoul_redirect as gr
import ghoul_skin as gs
import nif

GHOULS_PLUGIN = 'Anatomy Feral Ghouls.esp'            # the Ghouls mod's own plugin: its presence turns this stage on
GENITAL_MAT = 'Materials/Anatomy/AnatomyGenitals.bgsm'
GHOUL_GENITAL_MAT = 'Materials/Anatomy/AnatomyGenitalsGhoul.bgsm'


def genital_bgsm(blob):
    """AnatomyGenitals.bgsm with Anatomy\\FemaleBody_* -> Anatomy\\Ghoul\\FemaleBody_* (the three maps)"""
    out, o, n = bytearray(), 0, 0
    for off, s in gr.bgsm_maps(blob):
        if not re.match(r'(?i)anatomy[\\/]femalebody_[dns]\.dds$', s):
            continue
        ln = struct.unpack_from('<I', blob, off)[0]
        new = re.sub(r'(?i)^(anatomy)([\\/])', r'\1\2Ghoul\2', s).encode('latin1') + b'\0'
        out += blob[o:off] + struct.pack('<I', len(new)) + new
        o = off + 4 + ln
        n += 1
    if n != 3:
        raise SystemExit(f'AnatomyGenitals.bgsm: expected its three Anatomy\\FemaleBody maps, found {n}')
    return bytes(out + blob[o:])


def _mesh(game, rel, work, name):
    p = work / name
    p.write_bytes(game.read(rel))
    return gs.load_shape(p)


def stage(game, project_nif, anatomy_tex, genital_bgsm_blob, work, size=2048):
    t0 = time.time()
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    jobs, skipped = gr.plan(game)
    for s in skipped:
        print(f'   skipped {s}')
    if not jobs:
        raise SystemExit('no ghoul skin texture set found in this game')
    meshes = {}
    for sex in ('F', 'M'):
        want = gr.MESHES[sex]
        missing = [r for r in want.values() if game.find(r) is None]
        if missing:
            print(f'   {sex}: meshes missing {missing}: that sex is skipped')
            continue
        m = {k: _mesh(game, r, work, f'{sex}_{k}.nif') for k, r in want.items()}
        if sex == 'F':
            m['body'] = gs.load_shape(project_nif, 'CBBE')
            m['genitals'] = gs.load_shape(project_nif, 'AnatomyGenitals')
        meshes[sex] = gs.body_space(sex, m)
    produced, overrides = {}, []
    female_body_d = None
    for j in jobs:
        if j['sex'] not in meshes:
            continue
        srcs = {k: (r, game.read(r)) for k, r in j['sources'].items()}
        if j['key'] == 'female body':
            female_body_d = srcs['d']
        maps = gs.build(j['key'], j['layers'], meshes[j['sex']], srcs, j['islands_only'], size)
        rel, _ = gr.our_paths(j['stem'])
        for k, data in maps.items():
            p = work / pathlib.Path(rel[k]).name
            p.write_bytes(data)
            produced[rel[k]] = p
        files, over = gr.outputs(j)
        for r, blob in files.items():
            p = work / pathlib.Path(r).name
            p.write_bytes(blob)
            produced[r] = p
        overrides.append(over)
    # the ghoul women's genitals: our genital maps, toned by the ghoul body at the nearest body point, then rotted
    if 'F' in meshes and female_body_d is not None:
        import genital_texture as gt
        skin = gr.bgsm_maps(game.read(gt.SKIN_MATERIAL))
        human_d = 'textures/' + skin[0][1].replace('\\', '/')
        prep = gs.genital_prep(meshes['F']['body'], meshes['F']['genitals'], (human_d, game.read(human_d)),
                               female_body_d)
        srcs = {k: (f'Anatomy FemaleBody_{k}', (pathlib.Path(anatomy_tex) / f'FemaleBody_{k}.dds').read_bytes())
                for k in ('d', 'n', 's')}
        gsize = min(size, gt.Dds('genital', srcs['d'][1]).w)
        maps = gs.build('ghoul genitals', ['genitals'], meshes['F'], srcs, False, gsize, prep=prep)
        for k, data in maps.items():
            p = work / f'GhoulFemaleGenitals_{k}.dds'
            p.write_bytes(data)
            produced[f'Textures/Anatomy/Ghoul/FemaleBody_{k}.dds'] = p
        p = work / 'AnatomyGenitalsGhoul.bgsm'
        p.write_bytes(genital_bgsm(genital_bgsm_blob))
        produced[GHOUL_GENITAL_MAT] = p
    torsos, pairs = gr.torso_records(game) if GHOUL_GENITAL_MAT in produced else ([], {})
    plug = work / gr.PLUGIN
    masters = gr.write_plugin(plug, overrides, game.plugins, torsos, pairs)
    if torsos:
        print(f'   ghoul women\'s genitals: material swap on {len(torsos)} torso(s)')
    produced[gr.PLUGIN] = plug
    print(f'   {len(overrides)} texture sets redirected ({", ".join(masters)} as masters); {len(produced)} files; '
          f'{time.time() - t0:.0f} s')
    return produced
