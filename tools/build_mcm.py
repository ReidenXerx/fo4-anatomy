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
    ]),
]


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


def check_reads(ini):
    """Every setting the menu writes must be one LoadSettings reads under the same id, and back."""
    source = SCRIPT.read_text(encoding='utf-8')
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
              'pluginRequirements': ['Anatomy.esp'], 'pages': pages}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
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
