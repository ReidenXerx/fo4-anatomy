"""Assemble the release archive (release-plan.md): our files, the builder, Nahka's patch, a FOMOD.

    python tools/release.py [--version 0.1.0]     -> build/release/Anatomy-<version>.7z

What ships (nothing of anyone else's but Nahka's own work, with her page's permission, A-23):
    Anatomy.esp, Scripts/Anatomy/Arousal.pex, MCM/Config/Anatomy/*     arousal and its menu
    F4SE/Plugins/cbp.dll                                               the fo4-ocbpc fork (GPL-3.0; MIT base)
    F4SE/Plugins/Anatomy/cbp.dll - GPL-3.0.txt, - MIT (OCBPC).txt      its two licences, as the fork has them
    F4SE/Plugins/Anatomy/ocbp.ini, OCBPCollisionConfig.txt             our physics lines and [Bones]
    Tools/AnatomyBuilder/AnatomyBuilder.exe (+ _internal)              the builder
    Tools/AnatomyBuilder/data/nahka_patch.json.gz, data/tex/*          her genitals, as a patch and her
                                                                       texture island
    fomod/info.xml, fomod/ModuleConfig.xml                             one page: what to do next
    Anatomy - README.txt                                               install, credits, licences
Every file is checked present, and the archive must list every one of them back.

Both binaries are built from source on every run, so an archive never carries one older than its
code: the builder exe (PyInstaller, one folder) and cbp.dll (MSBuild). The fork must have no
uncommitted change: F4SE requires a plugin's source to be public, and the source we point players
to is that commit, which the README names.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
FORK = ROOT.parent / 'fo4-ocbpc'
NAME = 'Anatomy'                                            # file names: Anatomy.esp, the archive
TITLE = 'Anatomy - CBBE Genitals, Physics and Arousal'     # the Nexus page's title (owner's poll)
AUTHOR = 'ReidenXerx'
FORK_URL = 'https://github.com/ReidenXerx/fo4-ocbpc'      # its public source, F4SE's rule (to be published)

NEXT_STEPS = """After this installs:
1. Run Data\\Tools\\AnatomyBuilder\\AnatomyBuilder.exe once (MO2: add it to MO2's executables and run it
   from there, like BodySlide). It builds the body from YOUR CBBE and skin and writes only new files.
2. Open BodySlide, choose "Anatomy Body", your preset, and Build.
Re-run the builder whenever you change your CBBE or your skin mod."""

README = f"""{TITLE}
Working genitals for Fallout 4 CBBE women: physics, arousal, contact.

WHAT YOU NEED
  F4SE, LooksMenu, CBBE (with its BodySlide files) and BodySlide. For scenes: AAF.
  A physics config (e.g. Jiggle Physics / MadKita's) is optional; Anatomy brings its own lines.

INSTALL
  1. Install this archive with your mod manager. It must win cbp.dll over any other OCBPC physics mod
     (it IS OCBPC, extended); nothing else of it overlaps another mod.
  2. Run Data\\Tools\\AnatomyBuilder\\AnatomyBuilder.exe once. MO2: add it to MO2's executables and
     run it from MO2, as you do BodySlide. It reads your CBBE, your skeleton and your skin (as the
     game loads them), checks every step, and writes only new files:
       Tools\\BodySlide\\SliderSets\\Anatomy.osp and ShapeData\\Anatomy\\*, the "Anatomy Body" set
       Textures\\Anatomy\\*, Materials\\Anatomy\\*, the genitals' own texture and material
     Its log is AnatomyBuilder.log next to it.
  3. BodySlide: choose "Anatomy Body", your preset, Build (or Batch Build). The category "Anatomy"
     has "Opening, front": how far the vaginal opening reaches toward the front (50% unless your
     preset sets it).
  Re-run the builder after changing your CBBE or skin mod.

WHAT IT DOES
  - The genitals are their own part of the body, with bones added at run time to whatever skeleton
    your game loads; they open to a penis, a hand or a toy through collision physics, and stretch
    for something bigger.
  - The mouth opens to what is at the lips, over the animation's own face.
  - Women's nipples respond to arousal (scenes, watching, nudity, companions' own arousal); the MCM
    page "Anatomy" sets how much and what counts.

CREDITS
  Nahka - the vulva and anus geometry, sliders and texture (Animated Fannies on LoversLab: "up for
    adoption ... can be used in whatever way any other modders see fit"), with BringTheNoise and
    Alan (UN7B). Only her own work ships here, as a patch applied to your CBBE.
  Ousnius and the CBBE team - CBBE, which this is built on (never included: read from your install).
  ericncream and the OpenCBP authors - OCBPC, which cbp.dll extends.
  maximusmaxy - Screen Archer Menu's source, which documented the face data the mouth uses.

LICENCES
  cbp.dll is distributed under the GNU General Public License, version 3 (full text in
  F4SE\\Plugins\\Anatomy\\cbp.dll - GPL-3.0.txt), with an additional permission to link with F4SE.
  It is a fork of OpenCBP_FO4 / OCBPC, whose code it carries under the MIT licence
  (F4SE\\Plugins\\Anatomy\\cbp.dll - MIT (OCBPC).txt). Its complete source: {FORK_URL}
  (commit @FORK_COMMIT@).
  The builder is our own code, run by Python and Pillow, which are packed inside it under their own
  licences (Tools\\AnatomyBuilder\\licences). The plugin, scripts, MCM and configs are our own work.
"""


MSBUILD = r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe'


def build_dll():
    """cbp.dll from the fork's committed source; returns that commit (the source players are pointed to)."""
    dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=FORK, capture_output=True, text=True).stdout
    if dirty.strip():
        raise SystemExit('the fork has uncommitted changes, so no published commit would be the source of '
                         f'this cbp.dll; commit them first:\n{dirty}')
    subprocess.run([MSBUILD, 'OpenCBP_FO4.sln', '/t:CBPSSE', '/p:Configuration=Release', '/p:Platform=x64',
                    '/p:PlatformToolset=v143', '/p:WindowsTargetPlatformVersion=10.0.22621.0', '/v:m'],
                   cwd=FORK, check=True, stdout=subprocess.DEVNULL)
    return subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=FORK, capture_output=True,
                          text=True, check=True).stdout.strip()


BUILDER_MODULES = ('gamedata', 'genital_texture', 'apply_patch', 'make_patch', 'mask', 'split_genitals',
                   'opening', 'verify_zex', 'zex_bones', 'physics_config', 'physics_design', 'bgsm')


def build_exe():
    """PyInstaller one-folder build of tools/builder.py into build/dist/AnatomyBuilder (wiped first).
    The builder imports its stages by name at run time, so each is named here as a hidden import."""
    hidden = [arg for m in BUILDER_MODULES for arg in ('--hidden-import', m)]
    # no network, so no OpenSSL in the bundle: urllib and http.client take ssl as optional, and hashlib
    # falls back to Python's built-in SHA-1. (socket stays: xml.sax.saxutils -> urllib -> email.utils
    # imports it at load, and without it the builder fails at once; tried 2026-09-23.)
    excluded = [arg for m in ('ssl', '_ssl', '_hashlib') for arg in ('--exclude-module', m)]
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--console',
                    '--name', 'AnatomyBuilder', '--paths', 'tools', *hidden, *excluded,
                    '--distpath', 'build/dist', '--workpath', 'build/pyi', '--specpath', 'build/pyi',
                    'tools/builder.py'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pillow_licence():
    import importlib.metadata
    dist = importlib.metadata.distribution('pillow')
    found = [dist.locate_file(f) for f in dist.files if f.name.upper() == 'LICENSE']
    if not found:
        raise SystemExit('Pillow is installed without its LICENSE file; it must ship with the builder')
    return pathlib.Path(found[0])


def files(version):
    dist = BUILD / 'dist/AnatomyBuilder'
    out = {
        'Anatomy.esp': BUILD / 'plugin/Anatomy.esp',
        'Scripts/Anatomy/Arousal.pex': BUILD / 'papyrus/Anatomy/Arousal.pex',
        'MCM/Config/Anatomy/config.json': BUILD / 'mcm/MCM/Config/Anatomy/config.json',
        'MCM/Config/Anatomy/settings.ini': BUILD / 'mcm/MCM/Config/Anatomy/settings.ini',
        'F4SE/Plugins/cbp.dll': FORK / 'x64/Release/cbp.dll',
        'F4SE/Plugins/Anatomy/cbp.dll - GPL-3.0.txt': FORK / 'COPYING',            # the DLL's licence
        'F4SE/Plugins/Anatomy/cbp.dll - MIT (OCBPC).txt': FORK / 'LICENSE',        # the notice of the code it carries
        # the builder runs on Python and Pillow, packed inside it: their notices go with them
        'Tools/AnatomyBuilder/licences/Python LICENSE.txt': pathlib.Path(sys.base_prefix) / 'LICENSE.txt',
        'Tools/AnatomyBuilder/licences/Pillow LICENSE.txt': pillow_licence(),
        'F4SE/Plugins/Anatomy/ocbp.ini': BUILD / 'config/Anatomy/ocbp.ini',
        'F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt': BUILD / 'config/Anatomy/OCBPCollisionConfig.txt',
        'Tools/AnatomyBuilder/data/nahka_patch.json.gz': BUILD / 'patch/nahka_patch.json.gz',
    }
    for p in sorted((BUILD / 'patch/tex').iterdir()):
        out[f'Tools/AnatomyBuilder/data/tex/{p.name}'] = p
    for p in sorted(dist.rglob('*')):
        if p.is_file() and p.parent.name != 'data' and 'data' not in p.relative_to(dist).parts[:1] \
                and p.name != 'AnatomyBuilder.log':
            out[f'Tools/AnatomyBuilder/{p.relative_to(dist).as_posix()}'] = p
    return out


def fomod(version):
    info = (f'<?xml version="1.0" encoding="UTF-8"?>\n<fomod>\n    <Name>{escape(TITLE)}</Name>\n    <Author>{AUTHOR}</Author>\n'
            f'    <Version>{version}</Version>\n    <Description>{escape(NEXT_STEPS)}</Description>\n</fomod>\n')
    config = f"""<?xml version="1.0" encoding="UTF-8"?>
<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
    <moduleName>{escape(TITLE)}</moduleName>
    <requiredInstallFiles>
        <folder source="Data" destination="" />
    </requiredInstallFiles>
    <installSteps order="Explicit">
        <installStep name="After installing">
            <optionalFileGroups order="Explicit">
                <group name="Next steps" type="SelectAll">
                    <plugins order="Explicit">
                        <plugin name="Run the Anatomy Builder, then BodySlide">
                            <description>{escape(NEXT_STEPS)}</description>
                            <typeDescriptor>
                                <type name="Required" />
                            </typeDescriptor>
                        </plugin>
                    </plugins>
                </group>
            </optionalFileGroups>
        </installStep>
    </installSteps>
</config>
"""
    return info, config


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--version', default='0.1.0')
    args = ap.parse_args()
    stage = BUILD / 'release' / f'{NAME}-{args.version}'
    if stage.exists():
        shutil.rmtree(stage)
    commit = build_dll()
    build_exe()
    wanted = files(args.version)
    missing = [str(src) for src in wanted.values() if not src.exists()]
    if missing:
        raise SystemExit(f'missing: {missing}')
    if not any(k.endswith('AnatomyBuilder.exe') for k in wanted):
        raise SystemExit('PyInstaller ran but left no AnatomyBuilder.exe in build/dist/AnatomyBuilder')
    sys.path.insert(0, str(ROOT / 'tools'))
    import make_esp
    print(make_esp.verify(wanted['Anatomy.esp']))    # a keyword-less Anatomy.esp would move our layer into bodies
    print(f'cbp.dll from fork commit {commit}; builder exe from this tree')
    for rel, src in wanted.items():
        dst = stage / 'Data' / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    info, config = fomod(args.version)
    (stage / 'fomod').mkdir(parents=True, exist_ok=True)
    (stage / 'fomod/info.xml').write_text(info, encoding='utf-8')
    (stage / 'fomod/ModuleConfig.xml').write_text(config, encoding='utf-8')
    readme = README.replace('@FORK_COMMIT@', commit)
    (stage / f'{NAME} - README.txt').write_text(readme.replace('\n', '\r\n'), encoding='utf-8')
    import xml.etree.ElementTree as ET
    ET.parse(stage / 'fomod/info.xml')
    ET.parse(stage / 'fomod/ModuleConfig.xml')                 # both must at least be well-formed
    archive = stage.parent / f'{NAME}-{args.version}.7z'
    if archive.exists():
        archive.unlink()
    subprocess.run(['7z', 'a', '-t7z', '-mx=9', str(archive), '.\\*'], cwd=stage, check=True, stdout=subprocess.DEVNULL)
    listed = subprocess.run(['7z', 'l', '-sccUTF-8', str(archive)], capture_output=True, text=True).stdout
    all_files = [p.relative_to(stage) for p in stage.rglob('*') if p.is_file()]
    back = sum(1 for p in all_files if str(p) in listed)
    size = archive.stat().st_size // 1024
    print(f'{archive} ({size} KB): {len(all_files)} files ({len(wanted)} in Data), {back} listed back')
    if back != len(all_files):
        raise SystemExit('the archive does not list every file')


if __name__ == '__main__':
    sys.exit(main())
