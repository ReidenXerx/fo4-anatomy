"""Clean storefront renders for the Immersive pages + FOMODs (Publisher-bud 11-09): OUR meshes only, opaque, no
labels, ~900-1000 px tiles on the renderer's dark ground. Per creature: textures listed + decoded from that mod's own
Data (then the game), rendered at rest and erect.
    python -I storefront_renders.py <out root> [creature ...]"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
C = pathlib.Path(r'D:\F4Output\creatures')
BL = r'D:\F4Tools\blender-5.1.2-windows-x64\blender.exe'
E = '>Erection=1.0'
DCR = C / 'dc/review/Data/meshes/actors/deathclaw'
JOBS = {   # creature: (Data for textures, [(tag, nif, views, keys)])
    'Dogs': (C / 'canine/out9/Data', [
        ('rest', C / 'canine/out9/Data/meshes/Actors/Dogmeat/CharacterAssets/Dogmeat.nif', 'qunder', ''),
        ('erect', C / 'canine/out9/Data/meshes/Actors/Dogmeat/CharacterAssets/Dogmeat.nif', 'qside,qunder', E),
        ('vicious', C / 'canine/out9/Data/meshes/Actors/ViciousDog/ViciousDog.nif', 'qunder', E)]),
    'Super Mutants': (C / 'sm/out/Data', [
        ('rest', C / 'sm/out/Data/meshes/actors/supermutant/characterassets/SupermutantBody.nif', 'gfront,front',
         'EXP=3.4'),
        ('erect', C / 'sm/out/Data/meshes/actors/supermutant/characterassets/SupermutantBody.nif', 'gfront',
         E + ';EXP=3.4')]),
    'Behemoths': (C / 'bh/out6/Data', [
        ('rest', C / 'bh/out6/Data/meshes/actors/supermutantbehemoth/characterassets/SuperMutantBehemoth.nif',
         'front,crotch', 'EXP=3.0'),
        ('erect', C / 'bh/out6/Data/meshes/actors/supermutantbehemoth/characterassets/SuperMutantBehemoth.nif',
         'gside', E + ';EXP=3.0')]),
    'Yao Guai': (C / 'yg/out2/Data', [
        ('rest', C / 'yg/out2/Data/meshes/actors/yaoguai/characterassets/YaoGuai.nif', 'qside,qbelow', ''),
        ('erect', C / 'yg/out2/Data/meshes/actors/yaoguai/characterassets/YaoGuai.nif', 'qside', E)]),
    'Radstags': (C / 'rs/out4/Data', [
        ('rest', C / 'rs/out4/Data/meshes/actors/radstag/characterassets/RadStag.nif', 'qside', ''),
        ('erect', C / 'rs/out4/Data/meshes/actors/radstag/characterassets/RadStag.nif', 'qside,qbelow', E)]),
    'Mole Rats': (C / 'mr/out2/Data', [
        ('rest', C / 'mr/out2/Data/meshes/actors/molerat/characterassets/Molerat.nif', 'qside,qbelow', ''),
        ('erect', C / 'mr/out2/Data/meshes/actors/molerat/characterassets/Molerat.nif', 'qside', E)]),
    'Synths': (C / 'nick/out6/Data', [
        ('rest', C / 'nick/out6/Data/meshes/actors/synths/SynthGen2Body.nif', 'gfront,gside2', ''),
        ('erect', C / 'nick/out6/Data/meshes/actors/synths/SynthGen2Body.nif', 'gside2', E)]),
    'Ferals': (C / 'feral/out6/Data', [
        ('male', C / 'feral/out6/Data/meshes/actors/feralghoul/characterassets/FeralGhoulBase.nif', 'qfront,qbelow', ''),
        ('female', C / 'feral/out6/Data/meshes/actors/feralghoul/characterassets/FeralGhoulBase_F.nif',
         'qbelow,qback', '')]),
    'Deathclaws': (C / 'dc/out3/Data', [
        ('rest', DCR / 'review_male.nif', 'pt=0/-4/104/0/-20/30/front', 'RAW=1'),
        ('erect', DCR / 'review_male.nif', 'pt=0/6/104/20/-25/55/side,pt=0/-4/104/0/-20/34/front', 'RAW=1;' + E),
        ('female', DCR / 'review_female.nif', 'pt=0/-4/104/0/-20/30/front', 'RAW=1')]),
}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode or 'Traceback' in r.stdout + r.stderr:
        raise SystemExit(' '.join(map(str, cmd))[:200] + '\n' + (r.stdout + r.stderr)[-1500:])
    return r.stdout


CA = {'Dogs': C / 'canine/out9/Data/meshes/Actors/Dogmeat/CharacterAssets/Dogmeat.nif',
      'Super Mutants': C / 'sm/out/Data/meshes/actors/supermutant/characterassets/SupermutantBody.nif',
      'Behemoths': C / 'bh/out6/Data/meshes/actors/supermutantbehemoth/characterassets/SuperMutantBehemoth.nif',
      'Yao Guai': C / 'yg/out2/Data/meshes/actors/yaoguai/characterassets/YaoGuai.nif',
      'Radstags': C / 'rs/out4/Data/meshes/actors/radstag/characterassets/RadStag.nif',
      'Mole Rats': C / 'mr/out2/Data/meshes/actors/molerat/characterassets/Molerat.nif',
      'Synths': C / 'nick/out6/Data/meshes/actors/synths/SynthGen2Body.nif'}
# the erect set (Dudu 11-10 via Watcher: "people want also see rigid states" on the pages): erect only, 3 angles
ERECT = {k: (JOBS[k][0], [('erect', CA[k], 'qside,qfront,qunder', E + (';EXP=3.4' if k == 'Super Mutants' else
                                                                       ';EXP=3.0' if k == 'Behemoths' else ''))])
         for k in CA}
ERECT['Dogs'][1].append(('vicious', C / 'canine/out9/Data/meshes/Actors/ViciousDog/ViciousDog.nif', 'qside', E))
ERECT['Deathclaws'] = (JOBS['Deathclaws'][0], [
    ('erect', DCR / 'review_male.nif', 'pt=0/6/104/20/-25/55/side,pt=0/-4/104/0/-20/34/front,'
     'pt=0/8/102/45/-40/60/below', 'RAW=1;' + E)])
# soft + erect pairs (Dudu 11-10: "also soft, erect and soft"): the same views, the SAME camera (framed on the erect
# state for both), so a pair differs only in the state
EXPK = {'Super Mutants': ';EXP=3.4', 'Behemoths': ';EXP=3.0'}
PAIRS = {k: (JOBS[k][0], [('soft', CA[k], 'qside,qfront,qunder', 'FRAME=Erection' + EXPK.get(k, '')),
                          ('erect', CA[k], 'qside,qfront,qunder', 'FRAME=Erection;' + E + EXPK.get(k, ''))])
         for k in CA}
PAIRS['Yao Guai'] = (JOBS['Yao Guai'][0], [  # its side views hide the penis behind a hind leg
    ('soft', CA['Yao Guai'], 'qfront,qbelow,qback', 'FRAME=Erection'),
    ('erect', CA['Yao Guai'], 'qfront,qbelow,qback', 'FRAME=Erection;' + E)])
DCV = 'pt=0/6/104/20/-25/55/side,pt=0/-4/104/0/-20/34/front,pt=0/8/102/45/-40/60/below'
PAIRS['Deathclaws'] = (JOBS['Deathclaws'][0], [('soft', DCR / 'review_male.nif', DCV, 'RAW=1'),
                                               ('erect', DCR / 'review_male.nif', DCV, 'RAW=1;' + E)])
_set = __import__('os').environ.get('RENDER_SET')
if _set == 'erect':
    JOBS = ERECT
elif _set == 'pairs':
    JOBS = PAIRS
out_root = pathlib.Path(sys.argv[1])
for creature in (sys.argv[2:] or list(JOBS)):
    data, items = JOBS[creature]
    work = out_root / '_work' / creature
    work.mkdir(parents=True, exist_ok=True)
    nifs = sorted({str(n) for _, n, _, _ in items})
    run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'list', work / 'tex.json', *nifs])
    run([sys.executable, '-I', HERE / 'feral_tex_prep.py', work / 'tex.json', work / 'png', data])
    for extra in (C / 'canine/renderpng', C / 'sm/renderpng', C / 'dc/review/png'):    # BGSM-only fallbacks
        for p in extra.glob('bgsm__*.png'):
            if not (work / 'png' / p.name).exists():
                shutil.copyfile(p, work / 'png' / p.name)
    shots = work / 'shots'
    if shots.exists():
        shutil.rmtree(shots)
    run([BL, '-b', '-P', HERE / 'feral_tex_render.py', '--', 'render', work / 'png', shots,
         *[f'{t}|{n}|{v}|{k}' for t, n, v, k in items]])
    dst = out_root / creature
    dst.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for i, p in enumerate(sorted(shots.glob('*.png'))):
        Image.open(p).convert('RGB').save(dst / f'{creature.lower().replace(" ", "-")}-{p.stem}.jpg', quality=90)
    print(creature, sorted(q.name for q in dst.glob('*.jpg')))
