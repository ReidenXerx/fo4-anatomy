"""One FOMOD archive per creature mod (Dudu 11-09: the "Immersive" series, one Nexus mod per creature; nexus-tools
docs/FOMOD-STANDARD.md: hard-block what a FOMOD can see, first step "Checking your setup", one step per feature with
its image, schema 5.0, UTF-8 BOM, order Explicit, plain-text descriptions).
Each archive: fomod/ModuleConfig.xml, fomod/images/*.jpg, Core/<Data files>, and for the deathclaw Plugin/Plain +
Plugin/UAP (the UAP build when Deathclaw_nude.esp is active, conditionalFileInstalls).
    python -I creature_fomods.py <out dir> [mod key ...]"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

from PIL import Image

C = pathlib.Path(r'D:\F4Output\creatures')
R = pathlib.Path(r'D:\F4Output\immersive\renders')   # clean storefront renders (ours only)
SEVENZIP = shutil.which('7z') or r'C:\Program Files\7-Zip\7z.exe'
UAP_LINE = ('UAP (the creature animation pack): check this yourself - its creature skeletons carry the genital bones '
            'this mesh is weighted to')
AAF_LINE = ('AAF and a creature animation pack: check this yourself - only needed for scenes; the genitals show without '
            'them')
MM_LINE = 'Install with Vortex or MO2; manual installs are not supported.'
CREDIT = 'Penis positions and motion matched to UAP\'s, so AAF creature animations line up.'
CREDIT_DR = ('Penis positions and motion matched to darthroman\'s AAF creature pack, so its creature animations '
             'line up.')
ORDER = ('Install after any other mod that replaces the same creature body (UAP included): ours replaces its mesh at '
         'the same path.')

MODS = {
    'dogs': dict(
        name='Immersive Dogs - Anatomical Genitals', src=C / 'canine/out9/Data',
        checks=[AAF_LINE, ORDER],
        features=[('Sheath, penis and knot', 'A furred sheath on the belly, a red canine penis with a knot. At rest it '
                   'stays in the sheath; erect it slides out, the knot swells at the base. Dogmeat, raider dogs, vicious '
                   'dogs and pack leaders, Far Harbor wolves, FEV hounds - each in its own fur. ' + CREDIT,
                   R / 'Dogs')]),
    'supermutant': dict(
        name='Immersive Super Mutants - Anatomical Genitals', src=C / 'sm/out/Data',
        checks=[UAP_LINE, AAF_LINE, ORDER],
        features=[('Super mutant genitals', 'A thick, veined mutant penis and a heavy sack in the mutant\'s own skin, '
                   'with a darker glans. It rises and bends with UAP\'s bones in scenes. ' + CREDIT,
                   R / 'Super Mutants')]),
    'behemoth': dict(
        name='Immersive Behemoths - Anatomical Genitals', src=C / 'bh/out6/Data',
        checks=[AAF_LINE, ORDER],
        features=[('Behemoth genitals', 'The behemoth without its loincloth: the vanilla body, with a heavy shaft '
                   'hanging from the pubis and a two-lobed sack behind it, in the lower body\'s own skin. ' + CREDIT,
                   R / 'Behemoths')]),
    'yaoguai': dict(
        name='Immersive Yao Guai - Anatomical Genitals', src=C / 'yg/out2/Data',
        checks=[AAF_LINE, ORDER],
        features=[('Yao guai genitals', 'A furred sheath and scrotum in the bear\'s own fur, a red penis that slides out '
                   'when erect. Both yao guai bodies. ' + CREDIT_DR, R / 'Yao Guai')]),
    'radstag': dict(
        name='Immersive Radstags - Anatomical Genitals', src=C / 'rs/out4/Data',
        checks=[AAF_LINE, ORDER],
        features=[('Radstag genitals', 'A thin, pointed deer penis and a furred scrotum in the radstag\'s belly fur. '
                   'The nude radstag carries it erect. ' + CREDIT_DR, R / 'Radstags')]),
    'molerat': dict(
        name='Immersive Mole Rats - Anatomical Genitals', src=C / 'mr/out2/Data',
        checks=[AAF_LINE, ORDER],
        features=[('Mole rat genitals', 'A rodent prepuce sheath, a red penis and a scrotum in the mole rat\'s own skin, '
                   'on plain and armored mole rats. ' + CREDIT_DR, R / 'Mole Rats')]),
    'synths': dict(
        name='Immersive Synths - Anatomical Genitals for Nick and Gen 2 Synths', src=C / 'nick/out6/Data',
        checks=[UAP_LINE, AAF_LINE, ORDER],
        features=[('Synth genitals', 'Nick Valentine and every second-generation synth: an articulated synthetic '
                   'penis of plated segments over a rigid pod, in the synth\'s own materials. It bends with UAP\'s '
                   'bones in scenes. ' + CREDIT, R / 'Synths')]),
    'deathclaws': dict(
        name='Immersive Deathclaws - Anatomical Genitals', src=C / 'dc/sa/Data',
        plugin='Anatomy Deathclaws.esp', uap_plugin=C / 'dc/sa/plugins/Anatomy Deathclaws - UAP.esp',
        plain_plugin=C / 'dc/sa/plugins/Anatomy Deathclaws.esp', uap_master='Deathclaw_nude.esp',
        checks=['Anatomy Deathclaws.esp: this mod\'s own plugin (light)',
                'UAP\'s Deathclaw_nude.esp: optional - when it is active, this installer picks the build that loads '
                'after it and replaces its deathclaw penis', AAF_LINE],
        features=[('Deathclaw genitals', 'Males: a reptilian vent in seamless deathclaw skin; erect, a ribbed, scaly '
                   'penis everts from it, scales at the root turning to dark flesh at the head. Females: vent lips with '
                   'a red interior. Albino, alpha, savage, glowing and matriarch deathclaws keep their own colours. '
                   + CREDIT, R / 'Deathclaws')]),
}


def image(src, dst, width=1000):
    if pathlib.Path(src).is_dir():                     # a strip of the creature's clean renders, side by side
        tiles = [Image.open(q).convert('RGB') for q in sorted(pathlib.Path(src).glob('*.jpg'))][:4]
        h = 600
        tiles = [t.resize((round(t.width * h / t.height), h)) for t in tiles]
        im = Image.new('RGB', (sum(t.width for t in tiles) + 8 * (len(tiles) - 1), h), (40, 40, 42))
        x = 0
        for t in tiles:
            im.paste(t, (x, 0))
            x += t.width + 8
    else:
        im = Image.open(src).convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, 'JPEG', quality=86)


def option(name, desc, img=None, files='', typ='Required', flags=''):
    im = f'\n              <image path="{img}"/>' if img else ''
    return (f'            <plugin name="{escape(name)}">\n              <description>{escape(desc)}</description>{im}\n'
            f'{files}{flags}              <typeDescriptor><type name="{typ}"/></typeDescriptor>\n            </plugin>\n')


def step(name, opts):
    return (f'    <installStep name="{escape(name)}">\n      <optionalFileGroups order="Explicit">\n'
            f'        <group name="{escape(name)}" type="SelectAll">\n          <plugins order="Explicit">\n'
            f'{"".join(opts)}          </plugins>\n        </group>\n      </optionalFileGroups>\n    </installStep>\n')


def build(key, m, out):
    stage = pathlib.Path(tempfile.mkdtemp(prefix=f'fomod-{key}-', dir=r'D:\F4Output'))
    shutil.copytree(m['src'], stage / 'Core')
    imgs = stage / 'fomod/images'
    checks = list(m['checks']) + [MM_LINE]
    steps = [step('Checking your setup', [option('Your setup', '\n'.join(checks))])]
    for i, (fname, desc, src) in enumerate(m['features']):
        image(src, imgs / f'feature{i + 1}.jpg')
        steps.append(step(fname, [option(fname, desc, f'fomod/images/feature{i + 1}.jpg')]))
    shutil.copyfile(imgs / 'feature1.jpg', imgs / 'banner.jpg')                       # Vortex's moduleImage
    Image.open(imgs / 'feature1.jpg').save(stage / 'fomod/screenshot.png')            # MO2 shows this one
    req = '    <folder source="Core" destination="" priority="0"/>\n'
    cond = ''
    if m.get('plugin'):
        (stage / 'Plugin/Plain').mkdir(parents=True)
        (stage / 'Plugin/UAP').mkdir(parents=True)
        shutil.copyfile(m['plain_plugin'], stage / 'Plugin/Plain' / m['plugin'])
        shutil.copyfile(m['uap_plugin'], stage / 'Plugin/UAP' / m['plugin'])
        req += f'    <file source="Plugin\\Plain\\{m["plugin"]}" destination="{m["plugin"]}" priority="1"/>\n'
        cond = ('  <conditionalFileInstalls>\n    <patterns>\n      <pattern>\n        <dependencies operator="And">\n'
                f'          <fileDependency file="{m["uap_master"]}" state="Active"/>\n        </dependencies>\n'
                f'        <files>\n          <file source="Plugin\\UAP\\{m["plugin"]}" destination="{m["plugin"]}" '
                'priority="2"/>\n        </files>\n      </pattern>\n    </patterns>\n  </conditionalFileInstalls>\n')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
           f'  <moduleName>{escape(m["name"])}</moduleName>\n  <moduleImage path="fomod/images/banner.jpg"/>\n'
           f'  <requiredInstallFiles>\n{req}  </requiredInstallFiles>\n'
           f'  <installSteps order="Explicit">\n{"".join(steps)}  </installSteps>\n{cond}</config>\n')
    (stage / 'fomod/ModuleConfig.xml').write_bytes(b'\xef\xbb\xbf' + xml.encode('utf-8'))
    out.mkdir(parents=True, exist_ok=True)
    arc = out / f'{m["name"]} 1.0.0.7z'
    if arc.exists():
        raise SystemExit(f'{arc} exists: use a fresh folder')
    r = subprocess.run([SEVENZIP, 'a', '-t7z', '-mx=7', str(arc), '*'], cwd=stage, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-600:] + r.stderr[-600:])
    files = sorted(p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file())
    shutil.rmtree(stage)
    return arc, files


if __name__ == '__main__':
    out = pathlib.Path(sys.argv[1])
    keys = sys.argv[2:] or list(MODS)
    for k in keys:
        arc, files = build(k, MODS[k], out)
        print(f'{arc.name}: {len(files)} files, {arc.stat().st_size / 1e6:.1f} MB')
