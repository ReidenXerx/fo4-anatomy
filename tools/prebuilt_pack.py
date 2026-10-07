"""The prebuilt bodies' installer (A-72; the FOMOD standard: "Checking your setup" first, then one step per choice with
its card): build/release/Anatomy Bodies prebuilt-<version>.7z from tools/prebuilt_bodies.py's stage.

    python tools/prebuilt_pack.py --version 1.2.2 [--stage D:/F4Output/Prebuilt/stage]
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import release as rel  # noqa: E402  (the standard's cards, AUTHOR)

TITLE = 'Anatomy Bodies (prebuilt)'
SETUP = [
    'Anatomy.esp: found',
    'CBBE.esp: found',
    'Anatomy Engine 1.2.13 or later: check this yourself -- the genitals\' physics and the canal\'s wrap run in it; '
    'Nexus 109434',
    'For the 3BBB body: 3BBB (Nexus 48978) with Skeletal Adjustments for CBBE (Nexus 39006): check this yourself',
    'For the men\'s body: BodyTalk 4 (Nexus 72310): check this yourself -- its skin textures paint the men\'s genitals',
    'These bodies are built with ZEROED sliders and ship their .tri morphs: Silhouette and LooksMenu BodyGen shape '
    'every NPC from them in game. Build your outfits at zero too ("CBBE Zeroed Sliders", "BT - Zero").',
    'The genitals\' skin tone is baked from CBBE\'s own skin. With another skin mod, run the AnatomyBuilder once '
    '(github.com/ReidenXerx/fo4-anatomy/releases) to bake it from yours.',
    'Let this mod win the FemaleBody.nif / MaleBody.nif conflict over any BodySlide output and over CBBE / BodyTalk.',
    'Don\'t install another physics preset (MTM / OCBP and the like): it is incompatible. 3BBB\'s own preset is the '
    'exception.',
    'Install with Vortex or MO2; manual installs are not supported.']
WOMEN = [('CBBE', 'women-cbbe', 'Recommended',
          'The CBBE body with Anatomy\'s genitals, the closed anal canal and the vaginal lining, built at zero, with '
          'its morphs and Anatomy\'s physics preset for CBBE.'),
         ('3BBB', 'women-3bbb', 'Optional',
          'The same on CBBE 3BBB, keeping 3BBB\'s breast, butt and thigh bones, with Anatomy\'s physics preset for '
          '3BBB. Needs 3BBB and Skeletal Adjustments for CBBE.'),
         ('None', None, 'Optional',
          'No women\'s body from here: you build your own with the AnatomyBuilder (your own CBBE, skin or preset).')]
MEN = [('BodyTalk 4', 'men', 'Recommended',
        'BodyTalk 4 (Nude) with the men\'s anus opened, a canal inside and the same physics as hers, built at '
        '"BT - Zero" with its morphs. Needs BodyTalk 4 for its skin textures.'),
       ('BodyTalk 4 Uncut', 'men-uncut', 'Optional', 'The same on BodyTalk 4 Uncut.'),
       ('None', None, 'Optional', 'No men\'s body from here.')]


def config(images):
    def group(step, gname, options, image):
        opts = ''
        for name, folder, typ, desc in options:
            files = f'\n              <files><folder source="{folder}" destination="" priority="0"/></files>' if folder else ''
            opts += (f'            <plugin name="{escape(name)}">\n              <description>{escape(desc)}</description>\n'
                     f'              <image path="{image}"/>{files}\n'
                     f'              <typeDescriptor><type name="{typ}"/></typeDescriptor>\n            </plugin>\n')
        return (f'    <installStep name="{escape(step)}">\n      <optionalFileGroups order="Explicit">\n'
                f'        <group name="{escape(gname)}" type="SelectExactlyOne">\n          <plugins order="Explicit">\n'
                f'{opts}          </plugins>\n        </group>\n      </optionalFileGroups>\n    </installStep>\n')
    x = ('<?xml version="1.0" encoding="UTF-8"?>\n<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
         'xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">\n'
         f'  <moduleName>{escape(TITLE)}</moduleName>\n  <moduleImage path="{images["setup"]}"/>\n'
         '  <moduleDependencies operator="And">\n    <fileDependency file="Anatomy.esp" state="Active"/>\n'
         '    <fileDependency file="CBBE.esp" state="Active"/>\n  </moduleDependencies>\n'
         '  <installSteps order="Explicit">\n'
         '    <installStep name="Checking your setup">\n      <optionalFileGroups order="Explicit">\n'
         '        <group name="Your setup" type="SelectAll">\n          <plugins order="Explicit">\n'
         f'            <plugin name="Your setup">\n              <description>{escape(chr(10).join(SETUP))}</description>\n'
         f'              <image path="{images["setup"]}"/>\n'
         '              <typeDescriptor><type name="Required"/></typeDescriptor>\n            </plugin>\n'
         '          </plugins>\n        </group>\n      </optionalFileGroups>\n    </installStep>\n')
    x += group("Her body, ready to use", "Women's body", WOMEN, images['women'])
    x += group("His body, ready to use", "Men's body", MEN, images['men'])
    return x + '  </installSteps>\n</config>\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', required=True)
    ap.add_argument('--stage', default=r'D:\F4Output\Prebuilt\stage')
    a = ap.parse_args()
    stage = pathlib.Path(a.stage)
    parts = {p.name for p in stage.iterdir() if p.is_dir()}
    need = {f for _, f, _, _ in WOMEN + MEN if f}
    if need - parts:
        raise SystemExit(f'missing parts in {stage}: {sorted(need - parts)}')
    work = pathlib.Path(tempfile.mkdtemp(prefix='prebuiltpack-', dir=r'D:\F4Output'))
    try:
        for p in need:
            shutil.copytree(stage / p, work / p)
        images = {k: rel.card(c, work / 'fomod/images' / c) for k, c in
                  (('setup', 'anatomy-pipeline.jpg'), ('women', 'anatomy-rig.jpg'), ('men', 'anatomy-mm.jpg'))}
        (work / 'fomod/info.xml').write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<fomod>\n    <Name>{escape(TITLE)}</Name>\n    <Author>{rel.AUTHOR}'
            f'</Author>\n    <Version>{a.version}</Version>\n</fomod>\n', encoding='utf-8')
        (work / 'fomod/ModuleConfig.xml').write_bytes(b'\xef\xbb\xbf' + config(images).encode('utf-8'))
        out = rel.BUILD / 'release' / f'{TITLE} - {a.version}.7z'
        out.unlink(missing_ok=True)
        subprocess.run(['7z', 'a', '-t7z', '-mx=7', '-bd', '-y', str(out), '*'], cwd=work, check=True,
                       stdout=subprocess.DEVNULL)
        print(f'{out} ({out.stat().st_size // 1024} KB) sha256 {rel.sha256(out)}')
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
