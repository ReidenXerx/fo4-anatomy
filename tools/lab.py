"""The BodySlide / Outfit Studio LAB: a private copy under D:\\F4Output\\AnatomyLab (CLAUDE.md rule 4).

The owner's BodySlide folder lives in the game's Data (Vortex-managed) and its Config.xml points
Outfit Studio at BodySlide's own vanilla skeleton, which has no ZeX bones, so `AddBone` could not
find them. The lab is a copy with its own Config.xml:

    ProjectPath                     the lab    (SliderSets, ShapeData, Automations are read here)
    OutputDataPath                  the lab's out\\  (builds never touch the game or the owner's output)
    Anim/DefaultSkeletonReference   res\\skeleton_zex.nif, a copy of the installed ZeX skeleton

Only CBBE's set and ours are in the lab's SliderSets, so BodySlide starts fast and a group build
can only build what we name.

    python tools/lab.py setup                          # (re)create the lab: file copies only
    python tools/lab.py automate <script>              # OutfitStudio.exe -a <script>  (GUI process!)
    python tools/lab.py build <group> <preset> <dir>   # BodySlide group build            (GUI window!)

A BodySlide window steals focus from a running game: `automate` and `build` refuse while
Fallout4.exe runs, unless --game-is-free says the holder said so (CLAUDE.md rule 5).
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(r'D:\GOGGames\Fallout 4 GOTY\Data')
SRC = DATA / 'Tools/BodySlide'
LAB = pathlib.Path(r'D:\F4Output\AnatomyLab\BodySlide')
OUT = pathlib.Path(r'D:\F4Output\AnatomyLab\out')
SKELETON = DATA / 'Meshes/Actors/Character/CharacterAssets/skeleton.nif'
PROJECT = ROOT / 'build/project'
SCRIPTS = ROOT / 'automation'


def setup():
    LAB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in ('BodySlide.exe', 'OutfitStudio.exe', 'RefTemplates.xml'):
        if (SRC / f).exists():
            shutil.copy2(SRC / f, LAB / f)
    for d in ('res', 'lang', 'SliderPresets', 'SliderCategories', 'RefTemplates'):
        if (SRC / d).is_dir():
            shutil.copytree(SRC / d, LAB / d, dirs_exist_ok=True)
    shutil.copy2(SKELETON, LAB / 'res/skeleton_zex.nif')
    (LAB / 'SliderSets').mkdir(exist_ok=True)
    shutil.copy2(SRC / 'SliderSets/CBBE.osp', LAB / 'SliderSets/CBBE.osp')
    shutil.copytree(SRC / 'ShapeData/CBBE', LAB / 'ShapeData/CBBE', dirs_exist_ok=True)
    if PROJECT.exists():
        shutil.copytree(PROJECT / 'ShapeData', LAB / 'ShapeData', dirs_exist_ok=True)
        shutil.copytree(PROJECT / 'SliderSets', LAB / 'SliderSets', dirs_exist_ok=True)
        if (PROJECT / 'SliderPresets').exists():
            shutil.copytree(PROJECT / 'SliderPresets', LAB / 'SliderPresets', dirs_exist_ok=True)
        if (PROJECT / 'Masks').exists():
            shutil.copytree(PROJECT / 'Masks', LAB / 'Masks', dirs_exist_ok=True)
    refs = ROOT / 'build/references'
    if refs.exists():
        shutil.copytree(refs, LAB / 'ShapeData/References', dirs_exist_ok=True)
    (LAB / 'SliderGroups').mkdir(exist_ok=True)
    (LAB / 'SliderGroups/AnatomyLab.xml').write_text(
        '<SliderGroups>\n'
        '    <Group name="AnatomyLab">\n        <Member name="Anatomy Body Physics"/>\n    </Group>\n'
        '    <Group name="AnatomyZeXLab">\n        <Member name="Anatomy Body ZeX"/>\n    </Group>\n'
        '    <Group name="CBBELab">\n        <Member name="CBBE Body Physics"/>\n    </Group>\n'
        '</SliderGroups>\n', encoding='utf-8')
    (LAB / 'Automations').mkdir(exist_ok=True)
    for s in SCRIPTS.glob('*.xml'):
        shutil.copy2(s, LAB / 'Automations' / s.name)

    cfg = (SRC / 'Config.xml').read_text(encoding='utf-8-sig')
    cfg = set_tag(cfg, 'ProjectPath', str(LAB) + '\\')
    cfg = set_tag(cfg, 'OutputDataPath', str(OUT) + '\\')
    cfg = set_tag(cfg, 'DefaultSkeletonReference', 'res\\skeleton_zex.nif')
    (LAB / 'Config.xml').write_text(cfg, encoding='utf-8')
    print(f'lab ready at {LAB} (output {OUT}); skeleton = ZeX; sets: ' +
          ', '.join(p.name for p in (LAB / 'SliderSets').glob('*.osp')))


def set_tag(xml, tag, value):
    pat = re.compile(rf'<{tag}>[^<]*</{tag}>|<{tag}/>')
    if not pat.search(xml):
        raise SystemExit(f'Config.xml has no <{tag}>')
    return pat.sub(lambda m: f'<{tag}>{value}</{tag}>', xml, count=1)


def game_running():
    r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Fallout4.exe'], capture_output=True, text=True)
    return 'Fallout4.exe' in r.stdout


def guard(free):
    if game_running() and not free:
        raise SystemExit('Fallout4.exe is running: a BodySlide/Outfit Studio window would steal its focus. '
                         'Ask the holder for "free", then pass --game-is-free.')


CLOTH_KEEP = 'AnatomyBody'      # the cloth-data origin to keep: our body's own (today's CBBE blob)


def answer_cloth_dialog(pid, stop, report):
    """Headless mode does not suppress SaveProject's "Choose cloth data" dialog (a
    wxMultiChoiceDialog from OutfitProject::ChooseClothData, nothing ticked, measured hanging a run
    13 minutes). Watch for it, tick the origins naming CLOTH_KEEP, keep a screenshot, press OK.

    Win32 only, no focus taken: LB_GETCOUNT/LB_GETTEXT read the items (wxCheckListBox keeps its
    strings), LB_SETCURSEL + a posted Space ticks one (wx toggles the selected item), BM_CLICK OK."""
    import ctypes
    import time
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def windows(parent=None):
        found = []
        cb = WNDENUMPROC(lambda h, l: found.append(h) or True)
        if parent is None:
            user32.EnumWindows(cb, 0)
        else:
            user32.EnumChildWindows(parent, cb, 0)
        return found

    def text(h):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(h, buf, 512)
        return buf.value

    def cls(h):
        buf = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(h, buf, 128)
        return buf.value

    while not stop.is_set():
        for h in windows():
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value != pid or text(h) != 'Choose cloth data' or not user32.IsWindowVisible(h):
                continue
            kids = windows(h)
            lb = next((k for k in kids if cls(k) == 'ListBox'), None)
            ok = next((k for k in kids if cls(k) == 'Button' and text(k) == 'OK'), None)
            if not lb or not ok:
                continue
            n = user32.SendMessageW(lb, 0x018B, 0, 0)                    # LB_GETCOUNT
            items = []
            for i in range(n):
                size = user32.SendMessageW(lb, 0x018A, i, 0)             # LB_GETTEXTLEN
                buf = ctypes.create_unicode_buffer(size + 1)
                user32.SendMessageW(lb, 0x0189, i, buf)                 # LB_GETTEXT
                items.append(buf.value)
            for i, item in enumerate(items):
                if CLOTH_KEEP.lower() in item.lower():
                    user32.SendMessageW(lb, 0x0186, i, 0)                # LB_SETCURSEL
                    user32.PostMessageW(lb, 0x0100, 0x20, 0x00390001)    # WM_KEYDOWN Space
                    user32.PostMessageW(lb, 0x0101, 0x20, 0xC0390001)    # WM_KEYUP Space
                    time.sleep(0.4)
            snap(h, LAB / 'logs' / f'cloth-dialog-{int(time.time())}.png')
            report.append(f'cloth dialog: {len(items)} origin(s) {items}; ticked those naming {CLOTH_KEEP!r}')
            user32.PostMessageW(ok, 0x00F5, 0, 0)                            # BM_CLICK
            time.sleep(2)
        stop.wait(0.5)


def snap(hwnd, path):
    """PrintWindow the window itself, whatever is in front of it."""
    try:
        import ctypes
        from ctypes import wintypes
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        w, h = r.right - r.left, r.bottom - r.top
        path.parent.mkdir(parents=True, exist_ok=True)
        hdc = user32.GetWindowDC(hwnd)
        mem = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        gdi32.SelectObject(mem, bmp)
        user32.PrintWindow(hwnd, mem, 2)
        import struct as st
        header = st.pack('<IiiHHIIiiII', 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
        info = ctypes.create_string_buffer(header, len(header) + 16)   # GetDIBits may write into it
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem, bmp, 0, h, buf, info, 0)
        # a BMP needs no image library: file header + the DIB header + the pixels
        body = header + buf.raw
        path.with_suffix('.bmp').write_bytes(b'BM' + st.pack('<IHHI', 14 + len(body), 0, 0, 54) + body)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mem)
        user32.ReleaseDC(hwnd, hdc)
    except Exception as e:                                                      # evidence only
        print(f'(screenshot failed: {e})')


def automate(script, timeout):
    """Run one automation script headless; returns 0 when the log shows a clean headless run."""
    if not (LAB / 'Automations' / f'{script}.xml').exists():
        raise SystemExit(f'no {script}.xml in {LAB / "Automations"} (run setup after adding it to automation/)')
    # 5.8.2 exits 0 even when a step fails (master propagates the code, 5.8.2 does not), so the
    # verdict comes from the log, where level [1] is an error. The log is APPENDED to across runs
    # (measured: a 06:58 failure was still there at 07:11), so only this run's part counts.
    import threading
    log = LAB / 'Log_OS.txt'
    before = log.stat().st_size if log.exists() else 0
    proc = subprocess.Popen([str(LAB / 'OutfitStudio.exe'), '-a', script], cwd=LAB)
    stop, report = threading.Event(), []
    watcher = threading.Thread(target=answer_cloth_dialog, args=(proc.pid, stop, report), daemon=True)
    watcher.start()
    try:
        proc.wait(timeout=timeout)
    finally:
        stop.set()
    for line in report:
        print(line)
    r = proc
    size = log.stat().st_size if log.exists() else 0
    if size == before:
        print('Outfit Studio wrote nothing to its log: it did not run the script')
        return 1
    raw = log.read_bytes()
    text = (raw[before:] if size > before else raw).decode('utf-8', 'replace').splitlines()
    shown = [l for l in text if 'Automation' in l or '][1]' in l]
    print('\n'.join(shown[-60:]))
    errors = [l for l in text if '][1]' in l or 'failed with error' in l]
    ran = any('headless mode' in l for l in text)
    print(f'OutfitStudio exit code {r.returncode}; headless run: {ran}; error lines: {len(errors)}')
    return 0 if ran and not errors else 1


def build(group, preset, target, timeout):
    target = pathlib.Path(target)
    target.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(LAB / 'BodySlide.exe'), '--groupbuild', group, '--targetdir', str(target),
                        '--preset', preset, '--trimorphs'], cwd=LAB, timeout=timeout)
    built = sorted(p.relative_to(target) for p in target.rglob('*') if p.is_file())
    print(f'BodySlide exit code {r.returncode}; {len(built)} file(s): {[str(b) for b in built][:6]}')
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('setup')
    a = sub.add_parser('automate')
    a.add_argument('script')
    a.add_argument('--game-is-free', action='store_true')
    a.add_argument('--timeout', type=int, default=600)
    b = sub.add_parser('build')
    b.add_argument('group')
    b.add_argument('preset')
    b.add_argument('target')
    b.add_argument('--game-is-free', action='store_true')
    b.add_argument('--timeout', type=int, default=900)
    args = ap.parse_args()
    if args.cmd == 'setup':
        setup()
    elif args.cmd == 'automate':
        guard(args.game_is_free)
        sys.exit(automate(args.script, args.timeout))
    else:
        guard(args.game_is_free)
        sys.exit(build(args.group, args.preset, args.target, args.timeout))


if __name__ == '__main__':
    main()
