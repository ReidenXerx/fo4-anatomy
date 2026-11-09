"""'Immersive Ghouls' FOMOD (Dudu 11-09): feral ghoul genitals (our meshes, ships here) + the rotten ghoul skin and the
ghoul women's genitals (made by Anatomy's builder on the player's PC from THEIR textures; nothing third-party ships).
Core: the feral pack (feral/out6 minus the Ivy-only patch) + 'Anatomy Feral Ghouls.esp' (whose presence turns the
builder's ghoul stage on). Conditional: 'Anatomy Feral Ghouls - UAP Withered.esp' when ErectionFix_SilverPerv.esp is
active.  python -I ghouls_fomod.py <out dir>"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from creature_fomods import SEVENZIP, image, option, step  # noqa: E402

from PIL import Image  # noqa: E402

out = pathlib.Path(sys.argv[1])
FERAL = pathlib.Path(r'D:\F4Output\creatures\feral\out6\Data')
WITHERED = pathlib.Path(r'D:\F4Output\creatures\feral\out5\Data\Anatomy Feral Ghouls - UAP Withered.esp')
R = pathlib.Path(r'D:\F4Output\immersive\renders')
SHOTS = pathlib.Path(r'D:\F4Output\ghoulskin\render\shots')
NAME = 'Immersive Ghouls - Rotten Skin and Anatomical Genitals'
CHECKS = [
    'Feral ghoul genitals: need nothing else; they install from this package.',
    'Anatomy: check this yourself - the rotten ghoul skin and the ghoul women\'s genitals are made on your PC by '
    'Anatomy\'s builder (AnatomyBuilder.exe) from the ghoul textures YOU have installed. After installing this mod, '
    'run the builder again, then enable "Anatomy Ghoul Skin.esp" in your mod manager.',
    'CBBE and "CBBE HeadRear Absolute Fix" (Nexus 107187): check this yourself - the women\'s rotten skin is painted on '
    'the CBBE ghoul texture that fix installs. Without it the builder makes the men\'s, hands and faces only.',
    'The builder\'s ghoul step takes about 5 minutes and about 2 GB of memory at its default 2K size.',
    'UAP\'s ErectionFix_SilverPerv.esp: optional - when it is active, this installer adds the patch for its withered '
    'ferals.',
    'Install with Vortex or MO2; manual installs are not supported.']
FEATURES = [
    ('Feral ghoul genitals', 'Male ferals: a short, rotted stump with a torn, raw end. Female ferals: a sunken vulva '
     'with dark-red flesh between the labia, and breasts sagging under the wasted muscle. Every feral variant: '
     'withered, bloated and glowing ones included, each in its own skin.', R / 'Ferals'),
    ('Rotten ghoul skin', 'Ghoul skin made far more diseased: necrotic bruising, jaundiced blotches, skin sloughed off to '
     'raw meat with blackened edges, weeping sores, pustules, veins and fissures. One 3D pattern across body, hands, '
     'head and rear head, so every seam matches. NPC faces keep their baked look at the face edge. Made by Anatomy\'s '
     'builder from your own installed ghoul textures.', [SHOTS / 'F_after_front.png', SHOTS / 'M_after_front.png',
                                                         SHOTS / 'M_after_torso.png']),
    ('Ghoul women\'s genitals', 'Ghoul women\'s genitals in ghoul skin instead of healthy human skin: the genital texture '
     'takes the ghoul body\'s tone, with the same rot, and necrotic maroon where it was pink. Your own Anatomy body; '
     'only its genital material is swapped on ghouls.', [SHOTS / 'F_after_crotch.png']),
]


def strip(srcs, dst):
    if isinstance(srcs, pathlib.Path) and srcs.is_dir():
        image(srcs, dst)
        return
    tiles = [Image.open(p).convert('RGB') for p in srcs]
    h = 600
    tiles = [t.resize((round(t.width * h / t.height), h)) for t in tiles]
    im = Image.new('RGB', (sum(t.width for t in tiles) + 8 * (len(tiles) - 1), h), (40, 40, 42))
    x = 0
    for t in tiles:
        im.paste(t, (x, 0))
        x += t.width + 8
    tmp = dst.with_suffix('.png')
    im.save(tmp)
    image(tmp, dst)
    tmp.unlink()


stage = pathlib.Path(tempfile.mkdtemp(prefix='fomod-ghouls-', dir=r'D:\F4Output'))
shutil.copytree(FERAL, stage / 'Core', ignore=shutil.ignore_patterns('*Ivy Patch*'))
(stage / 'Optional/UAPWithered').mkdir(parents=True)
shutil.copyfile(WITHERED, stage / 'Optional/UAPWithered' / WITHERED.name)
imgs = stage / 'fomod/images'
imgs.mkdir(parents=True)
steps = [step('Checking your setup', [option('Your setup', '\n'.join(CHECKS))])]
for i, (fname, desc, src) in enumerate(FEATURES):
    strip(src, imgs / f'feature{i + 1}.jpg')
    steps.append(step(fname, [option(fname, desc, f'fomod/images/feature{i + 1}.jpg')]))
shutil.copyfile(imgs / 'feature2.jpg', imgs / 'banner.jpg')
Image.open(imgs / 'feature2.jpg').save(stage / 'fomod/screenshot.png')
from xml.sax.saxutils import escape  # noqa: E402
cond = ('  <conditionalFileInstalls>\n    <patterns>\n      <pattern>\n        <dependencies operator="And">\n'
        '          <fileDependency file="ErectionFix_SilverPerv.esp" state="Active"/>\n        </dependencies>\n'
        f'        <files>\n          <file source="Optional\\UAPWithered\\{WITHERED.name}" destination="{WITHERED.name}" '
        'priority="1"/>\n        </files>\n      </pattern>\n    </patterns>\n  </conditionalFileInstalls>\n')
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
       f'  <moduleName>{escape(NAME)}</moduleName>\n  <moduleImage path="fomod/images/banner.jpg"/>\n'
       '  <requiredInstallFiles>\n    <folder source="Core" destination="" priority="0"/>\n  </requiredInstallFiles>\n'
       f'  <installSteps order="Explicit">\n{"".join(steps)}  </installSteps>\n{cond}</config>\n')
(stage / 'fomod/ModuleConfig.xml').write_bytes(b'\xef\xbb\xbf' + xml.encode('utf-8'))
out.mkdir(parents=True, exist_ok=True)
arc = out / f'{NAME} 1.0.0.7z'
if arc.exists():
    raise SystemExit(f'{arc} exists')
r = subprocess.run([SEVENZIP, 'a', '-t7z', '-mx=7', str(arc), '*'], cwd=stage, capture_output=True, text=True)
if r.returncode:
    raise SystemExit(r.stdout[-600:])
files = sorted(p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file())
print(arc.name, len(files), 'files', [f for f in files if f.lower().endswith('.esp')])
shutil.rmtree(stage)
