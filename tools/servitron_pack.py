"""The Servitron add-on (the owner, 2026-10-08: its own mod, released with Anatomy 1.2.5 + Engine 1.2.14): one FOMOD per
nexus-tools/docs/FOMOD-STANDARD.md. Nothing of Servitron's is shipped but our derivatives of its BodySlide projects (the
player builds them, like every Tailor pack) and, for 3BBB, Servitron Physics Fix's skeleton with 3BBB's bones added.

    Core/       AnatomyServitron.esp, the rubber breast material + maps, AAF race/actor files, the spawn helper, and
                F4SE/Plugins/Anatomy/Servitron.ini (the marker Silhouette keys off: it drops its Servitron breast-slider
                exclusion when this file exists)
    CBBE/       Tools/BodySlide: ShapeData/Servitron (rubber abdomens + the men's, breast torsos), AnatomyServitronMale.osp
    3BBB/       Tools/BodySlide: the Tailor 3BBB sets (abdomens + men's, torsos) + Meshes/Servitron/skeleton.nif

    python tools/servitron_pack.py <version>   -> D:/F4Output/ServitronPack/<NAME> <version>.7z (+ the staged tree)
"""
import io
import pathlib
import shutil
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRV = pathlib.Path(r'D:\F4Output\servitron')
OUT = pathlib.Path(r'D:\F4Output\ServitronPack')
NAME = 'Anatomy Servitron'
PHOTOS = pathlib.Path(r'C:\Users\DuduPhudu\Documents\My Games\Fallout4\Photos')
IMAGES = {  # fomod image -> source (the owner's in-game photos, 2026-10-08, and Fo4-mcp's scene capture)
    'banner.jpg': PHOTOS / 'Screenshot423.png',
    'breasts.jpg': PHOTOS / 'Screenshot422.png',
    'male.jpg': PHOTOS / 'Screenshot423.png',
    'openings.jpg': pathlib.Path(r'D:\F4Output\capture\servitron-run8\a-pulled-back.png'),
}
MARKER = """; Anatomy Servitron is installed. Silhouette reads this file's presence: with it, Silhouette's body shapes keep
; their breast sliders on Servitrons (their rubber breasts follow them). Nothing in here is read.
"""


def stage(dst):
    shutil.rmtree(dst, ignore_errors=True)
    core, cbbe, b3 = dst / 'Core', dst / 'CBBE', dst / '3BBB'
    put = lambda src, rel: (rel.parent.mkdir(parents=True, exist_ok=True), shutil.copy2(src, rel))  # noqa: E731
    put(SRV / 'male/Data/AnatomyServitron.esp', core / 'AnatomyServitron.esp')
    for rel in ('Materials/Servitron/default/PlasticBoobs.bgsm', 'Textures/Anatomy/Servitron/RubberBoobs_d.dds',
                'Textures/Anatomy/Servitron/RubberBoobs_n.dds', 'Textures/Anatomy/Servitron/RubberBoobs_s.dds'):
        put(SRV / 'over' / rel, core / rel)
    for f in ('Anatomy_raceData_Servitron.xml', 'Anatomy_actorTypeData_Servitron.xml'):
        put(ROOT / 'aaf' / f, core / 'AAF' / f)
    put(ROOT / 'build/papyrus/Anatomy/DebugSpawn.pex', core / 'Scripts/Anatomy/DebugSpawn.pex')
    (core / 'F4SE/Plugins/Anatomy').mkdir(parents=True, exist_ok=True)
    (core / 'F4SE/Plugins/Anatomy/Servitron.ini').write_text(MARKER, encoding='utf-8')
    # CBBE: Servitron's own sets (Servitron.osp) build our files from ShapeData/Servitron; the men's have their own sets
    sd = cbbe / 'Tools/BodySlide/ShapeData/Servitron'
    for src in (SRV / 'rig/ShapeData/Servitron', SRV / 'male/ShapeData/Servitron', SRV / 'collar/ShapeData/Servitron'):
        for f in src.iterdir():
            put(f, sd / f.name)
    for f in (SRV / 'torso/ShapeData/Servitron').glob('*Robo-Boobs*'):
        put(f, sd / f.name)
    put(SRV / 'male/SliderSets/AnatomyServitronMale.osp', cbbe / 'Tools/BodySlide/SliderSets/AnatomyServitronMale.osp')
    # 3BBB: the Tailor's sets, ours in them, and the skeleton that carries 3BBB's breast and butt bones
    # (+ 1.0.1: Servitron's own Bunny and French Maid, weighted to the 3BBB body; the owner's game has worn them since 10-08)
    for src in (SRV / 'torso3bbb', SRV / 'rig3bbb_v2', SRV / 'outfits3bbb'):
        for d in (src / 'ShapeData').iterdir():
            for f in d.iterdir():
                if not f.name.startswith('_'):
                    put(f, b3 / 'Tools/BodySlide/ShapeData' / d.name / f.name)
        for f in (src / 'SliderSets').iterdir():
            put(f, b3 / 'Tools/BodySlide/SliderSets' / f.name)
    put(SRV / 'out/Meshes/Servitron/skeleton.nif', b3 / 'Meshes/Servitron/skeleton.nif')
    img = dst / 'fomod/images'
    img.mkdir(parents=True)
    for name, src in IMAGES.items():
        im = Image.open(src).convert('RGB')
        im.thumbnail((1000, 1000))
        im.save(img / name, quality=86)
    shutil.copy2(img / 'banner.jpg', dst / 'fomod/screenshot.png') if False else None
    Image.open(img / 'banner.jpg').save(dst / 'fomod/screenshot.png')
    return dst


def option(name, desc, image, files='', kind='Required'):
    return (f'            <plugin name="{name}">\n              <description>{desc}</description>\n'
            f'              <image path="fomod/images/{image}"/>\n{files}'
            f'              <typeDescriptor><type name="{kind}"/></typeDescriptor>\n            </plugin>\n')


def feature(step, name, desc, image):
    return (f'    <installStep name="{step}">\n      <optionalFileGroups order="Explicit">\n'
            f'        <group name="{step}" type="SelectAll">\n          <plugins order="Explicit">\n'
            + option(name, desc, image) + '          </plugins>\n        </group>\n      </optionalFileGroups>\n'
            '    </installStep>\n')


def module_config(version):
    setup = ('Servitron.esm: found\nAAF.esm: found\nAnatomy.esp: found\n'
             'Anatomy Engine 1.2.14 or newer: check this yourself -- aims, opens and wraps; Nexus 109434\n'
             'Anatomy 1.2.5 or newer: check this yourself -- decides each robot\'s sex; Nexus 109435\n'
             'Servitron - BodySlide Files: check this yourself -- the projects ours replace; Nexus 32801\n'
             'Servitron Physics Fix (CBBE option only): check this yourself -- its skeleton has the penis bones; the 3BBB '
             'option ships that skeleton with 3BBB\'s bones added, so it is not needed there; Nexus 93993\n'
             'BodySlide and Outfit Studio: check this yourself -- build the Servitron sets after installing; Nexus 25\n'
             'Rapport (recommended): keeps her mouth out of scenes, a robot has none; Nexus 109219\n'
             'Install with Vortex or MO2; manual installs are not supported.')
    steps = (feature('Checking your setup', 'Your setup', setup, 'banner.jpg')
             + feature('Working rubber openings', 'Her own rubber rings and canals',
                       'Servitron\'s Rubber abdomens keep their own vagina and anus, now rigged: the rubber rings stretch '
                       'round whatever enters, the canals wrap the shaft inside, and the Anatomy Engine aims the penis '
                       'into them in every AAF animation. Each ring opens whole and the suit round it takes the stretch, '
                       'so the rubber keeps its shape however wide it opens.', 'openings.jpg')
             + feature('Rubber breasts', 'Latex breasts in a machined socket',
                       'The Boobs torsos get rubber breasts: a latex areola with a satin finish and a metal-capped '
                       'nipple, seated in the chest by a polished metal bead, where the suit\'s own fabric takes over. '
                       'The suit is pushed back so no armour plate cuts through them, and they jiggle with your physics '
                       'preset.', 'breasts.jpg')
             + feature('The abdomen decides', 'A male module at the Robot Workbench',
                       'Two new abdomens, "GITS Rubber (Male)" and "Wetsuit Rubber (Male)": the vagina sealed, the anus '
                       'kept, and a segmented latex penis with a flared base, rigged to the skeleton\'s penis bones so '
                       'animations and the engine\'s aim drive it. A Rubber abdomen makes her a woman to AAF, a Male one '
                       'a man, and a closed suit keeps the robot out of scenes. Change it at the workbench any time.',
                       'male.jpg'))
    body = ('    <installStep name="Your body">\n      <optionalFileGroups order="Explicit">\n'
            '        <group name="The body your physics preset moves" type="SelectExactlyOne">\n'
            '          <plugins order="Explicit">\n'
            + option('CBBE', 'For a CBBE physics preset (one breast bone a side). Replaces the projects of Servitron\'s '
                     'own BodySlide sets; build them in BodySlide (the "Servitron" preset fits). Needs Servitron Physics '
                     'Fix (Nexus 93993) for the penis bones.', 'breasts.jpg',
                     '              <files><folder source="CBBE" destination="" priority="0"/></files>\n', 'Optional')
            + option('3BBB (Anatomy)', 'For a 3BBB physics preset, Anatomy\'s 3BBB body and Ivy. The "(Anatomy 3BBB)" '
                     'sets in BodySlide (build those, not Servitron\'s own torsos: theirs are CBBE and do not jiggle on '
                     'a 3BBB preset), and Servitron Physics Fix\'s skeleton with 3BBB\'s breast and butt bones added, '
                     'so the breasts and butt jiggle; Physics Fix itself is not needed with this option. Also 3BBB '
                     'versions of Servitron\'s Bunny and French Maid outfits.',
                     'breasts.jpg', '              <files><folder source="3BBB" destination="" priority="0"/></files>\n',
                     'Recommended')
            + '          </plugins>\n        </group>\n      </optionalFileGroups>\n    </installStep>\n')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
            f'  <moduleName>{NAME} {version}</moduleName>\n  <moduleImage path="fomod/images/banner.jpg"/>\n'
            '  <moduleDependencies operator="And">\n'
            '    <fileDependency file="Servitron.esm" state="Active"/>\n'
            '    <fileDependency file="AAF.esm" state="Active"/>\n'
            '    <fileDependency file="Anatomy.esp" state="Active"/>\n  </moduleDependencies>\n'
            '  <requiredInstallFiles>\n    <folder source="Core" destination="" priority="0"/>\n'
            '  </requiredInstallFiles>\n  <installSteps order="Explicit">\n' + steps + body + '  </installSteps>\n</config>\n')


def main():
    version = sys.argv[1]
    dst = stage(OUT / f'{NAME} {version}')
    (dst / 'fomod/ModuleConfig.xml').write_bytes(b'\xef\xbb\xbf' + module_config(version).encode('utf-8'))
    (dst / 'fomod/info.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<fomod>\n  <Name>{NAME}</Name>\n'
                                        f'  <Version>{version}</Version>\n  <Author>Dudu\'sButt</Author>\n</fomod>\n',
                                        encoding='utf-8')
    archive = OUT / f'{NAME} {version}.7z'
    archive.unlink(missing_ok=True)
    subprocess.run(['7z', 'a', '-t7z', '-mx=7', '-mmt=8', '-bd', '-y', str(archive), '.\\*'], cwd=dst, check=True,
                   capture_output=True)
    n = sum(1 for _ in dst.rglob('*') if _.is_file())
    print(f'{archive} ({archive.stat().st_size // 1024} KB, {n} files)')


if __name__ == '__main__':
    main()
