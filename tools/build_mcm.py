"""Generate Anatomy's MCM menu (arousal only, the owner's poll 2026-09-23) from the script's defaults.

    python tools/build_mcm.py        -> build/mcm/MCM/Config/Anatomy/config.json, settings.ini

Every default is READ from Anatomy:Arousal's Defaults(), never typed here, so the menu and the
script's no-MCM behaviour cannot disagree (fo4-chemistry/scripts/build-mcm.py's rule). The script
reads the same ids back every tick (LoadSettings). MCM stores the player's changes in
Data/MCM/Settings/Anatomy.ini; settings.ini here is only what MCM shows as the default.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'papyrus/Anatomy/Arousal.psc'
OUT = ROOT / 'build/mcm/MCM/Config/Anatomy'
MOD = 'Anatomy'
# on no control: proves MCM loaded settings.ini (a missing key reads -1, a missing switch false)
SENTINEL = ('Meta', 'iDefaults', '1')

# (section, key, label, help, min, max, step); step None = a switch
PAGES = [
    ('Arousal', [
        ('text', 'Women around you become aroused by what is happening near them, and their nipples show '
                 'it. Every change is added on top of her own body shape and removed when it passes.'),
        ('section', 'General'),
        ('General', 'bEnabled', 'Arousal nipples', 'Off removes every change this mod made to anyone\'s '
         'nipples and stops watching.', None, None, None),
        ('General', 'fNippleStrength', 'Nipple response', 'How far nipples rise at full arousal. 1 is the '
         'tuned look (clearly visible), 0.5 subtle, 2 exaggerated. 0 changes nothing.', 0.0, 2.0, 0.05),
        ('General', 'fRiseSpeed', 'Rise speed', 'How quickly arousal builds. At 1, a scene takes her halfway '
         'up in 10 s, watching one in 30 s.', 0.25, 4.0, 0.25),
        ('General', 'fFadeSpeed', 'Fade speed', 'How quickly it passes. At 1 she is halfway back a minute '
         'after the cause is gone.', 0.25, 4.0, 0.25),
        ('section', 'What arouses her'),
        ('Sources', 'bScenes', 'Being in a scene', 'Anyone in an AAF scene (the strongest source).',
         None, None, None),
        ('Sources', 'bWatching', 'Watching a scene', 'Anyone within about 17 m of a scene she is not in.',
         None, None, None),
        ('Sources', 'bCompanions', 'Companions\' own arousal', 'Ivy\'s own arousal (CompanionIvy) and a '
         'companion\'s desire (Overture). Nothing happens without those mods.', None, None, None),
        ('Sources', 'bNaked', 'Being naked', 'Nothing worn in the body slot: a little, slowly.',
         None, None, None),
        ('section', 'Men'),
        ('Men', 'bGlans', 'Glans colour', 'Every man\'s glans a little redder (a LooksMenu overlay). Off '
         'takes it off every man it was given to.', None, None, None),
    ]),
]


# the console's debug scenes (Anatomy:DebugScene, the owner 2026-10-17: "maybe its better to add in mcm menu"): buttons
# and hotkeys only, no settings, so nothing here enters settings.ini or check_reads
DEBUG = 'Anatomy:DebugScene'
KINDS = [(1, 'Vaginal'), (2, 'Anal'), (3, 'Oral'), (4, 'Handjob'), (5, 'Titjob'), (6, 'Footjob')]
DEBUG_KEYS = [
    ('AnatomyDebugPick', 'Pick the person you face', 'PickLooked', []),
    ('AnatomyDebugRunAll', 'Run every kind', 'Run', [0]),
    ('AnatomyDebugClimax', 'Climax now', 'Climax', []),
    ('AnatomyDebugStop', 'Stop', 'Stop', []),
]


def call(function, params):
    return {'type': 'CallGlobalFunction', 'script': DEBUG, 'function': function, 'params': params}


def debug_page():
    run = ('An AAF scene of this kind for the picked pair; 15 s after he is in her, the climax, 8 s more, then he pulls out. '
           'Close the menu to let it run; notifications say each step.')
    content = [
        {'type': 'text', 'text': 'Test scenes for the climax fluid: pick two people, then run a kind. Each pick shows '
                                 'the pair; picking someone again drops them, a third pick replaces the oldest.'},
        {'type': 'section', 'text': 'Who'},
        {'type': 'button', 'text': 'Pick the person you face', 'help': 'The person nearest the middle of where you '
         'face, within about 30 m. Close the menu, face the next one, and pick again (or use the hotkey below).',
         'action': call('PickLooked', [])},
        {'type': 'button', 'text': 'Pick yourself', 'help': 'You as one of the two.', 'action': call('PickPlayer', [])},
        {'type': 'button', 'text': 'Forget the pair', 'help': 'Nobody picked.', 'action': call('Clear', [])},
        {'type': 'section', 'text': 'Run'},
    ]
    content += [{'type': 'button', 'text': name, 'help': run, 'action': call('Run', [k])} for k, name in KINDS]
    content += [
        {'type': 'button', 'text': 'Every kind, one after another', 'help': 'All six in a row, 25 s between them to '
         'watch the fluid. A kind with no animation for the pair is skipped.', 'action': call('Run', [0])},
        {'type': 'button', 'text': 'Climax now', 'help': 'A climax this instant for the pair, in any scene of theirs.',
         'action': call('Climax', [])},
        {'type': 'button', 'text': 'Stop', 'help': "Ends the pair's scene and any test still waiting.",
         'action': call('Stop', [])},
        {'type': 'section', 'text': 'Hotkeys'},
    ]
    content += [{'type': 'hotkey', 'id': kid, 'text': text, 'help': 'Set a key, then press it in game.'}
                for kid, text, _, _ in DEBUG_KEYS]
    return {'pageDisplayName': 'Debug scenes', 'content': content}


def keybinds():
    return {'modName': MOD, 'keybinds': [{'id': kid, 'desc': f'Anatomy debug: {text}', 'action': call(fn, params)}
                                         for kid, text, fn, params in DEBUG_KEYS]}


def defaults():
    source = SCRIPT.read_text(encoding='utf-8')
    body = re.search(r'^Function Defaults\(\)\n(.*?)^EndFunction', source, re.M | re.S)
    if not body:
        raise SystemExit(f'no Defaults() in {SCRIPT} - nothing to read the defaults from')
    return dict(re.findall(r'^\s*(\w+) = (\S+)\s*$', body.group(1), re.M))


def build(values):
    pages, ini, used = [], {}, set()
    for title, rows in PAGES:
        content = []
        for row in rows:
            if row[0] in ('text', 'section'):
                content.append({'type': row[0], 'text': row[1]})
                continue
            section, key, label, help_, lo, hi, step = row
            if key not in values:
                raise SystemExit(f'{key} has no default in Defaults() - the menu would invent one')
            used.add(key)
            raw = values[key]
            if step is None:
                if raw not in ('True', 'False'):
                    raise SystemExit(f'{key} is a switch but its default is {raw}')
                ini.setdefault(section, {})[key] = '1' if raw == 'True' else '0'
                content.append({'type': 'switcher', 'id': f'{key}:{section}', 'text': label, 'help': help_,
                                'valueOptions': {'sourceType': 'ModSettingBool'}})
                continue
            value = float(raw)
            if not lo <= value <= hi:
                raise SystemExit(f'{key} defaults to {value}, outside its slider {lo}..{hi}')
            ini.setdefault(section, {})[key] = f'{value:.6f}'
            content.append({'type': 'slider', 'id': f'{key}:{section}', 'text': label, 'help': help_,
                            'valueOptions': {'min': lo, 'max': hi, 'step': step,
                                             'sourceType': 'ModSettingFloat'}})
        pages.append({'pageDisplayName': title, 'content': content})
    missing = sorted(set(values) - used)
    if missing:
        raise SystemExit(f'Defaults() sets {missing} but the menu does not expose them - add or drop them')
    return pages, ini, used


def code_only(source):
    """Papyrus with every comment removed (;/ block /;, {doc}, ; to end of line), strings kept, so a
    read that exists only in a comment does not count (Chemistry's build-mcm rule, 9f21d36)."""
    out, i, n, in_str = [], 0, len(source), False
    while i < n:
        ch = source[i]
        if in_str:
            out.append(ch)
            if ch == '\\' and i + 1 < n:
                out.append(source[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
        elif ch == '"':
            in_str = True
            out.append(ch)
            i += 1
        elif source.startswith(';/', i):
            end = source.find('/;', i + 2)
            i = n if end < 0 else end + 2
        elif ch == ';':
            end = source.find('\n', i)
            i = n if end < 0 else end
        elif ch == '{':
            end = source.find('}', i + 1)
            i = n if end < 0 else end + 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


def check_reads(ini, source=None):
    """Every setting the menu writes must be one LoadSettings reads under the same id, and back."""
    source = code_only(source if source is not None else SCRIPT.read_text(encoding='utf-8'))
    read = set(re.findall(rf'GetModSetting\w+\("{MOD}", "(\w+:\w+)"\)', source))
    sentinel = f'{SENTINEL[1]}:{SENTINEL[0]}'
    if sentinel not in read:
        raise SystemExit(f'the script never tests {sentinel}: it cannot tell loaded defaults from a missing file')
    read.discard(sentinel)
    written = {f'{k}:{section}' for section, keys in ini.items() for k in keys}
    if read != written:
        raise SystemExit(f'the script reads {sorted(read - written)} that the menu lacks, and the menu '
                         f'writes {sorted(written - read)} that the script never reads')


def main():
    pages, ini, used = build(defaults())
    check_reads(ini)
    config = {'modName': MOD, 'displayName': MOD, 'minMcmVersion': 1,
              'pluginRequirements': ['Anatomy.esp'], 'pages': pages + [debug_page()]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    (OUT / 'keybinds.json').write_text(json.dumps(keybinds(), indent=2) + '\n', encoding='utf-8')
    lines = ['; GENERATED by tools/build_mcm.py from Arousal.psc Defaults() - edit that, not this.']
    for section, keys in ini.items():
        lines.append(f'[{section}]')
        lines += [f'{k}={v}' for k, v in keys.items()]
        lines.append('')
    lines += [f'[{SENTINEL[0]}]', f'{SENTINEL[1]}={SENTINEL[2]}', '']
    (OUT / 'settings.ini').write_text('\n'.join(lines), encoding='utf-8')
    print(f'wrote {OUT / "config.json"} and settings.ini: {len(used)} settings across {len(pages)} page(s)')


if __name__ == '__main__':
    main()
