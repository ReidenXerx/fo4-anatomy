"""Build Anatomy's sex-sound clips (A-67): sounds/src/<kind>/*.mp3 (ElevenLabs sound effects, our own) ->
build/sound/Sound/FX/Anatomy/<kind>_<n>.wav, the names tools/make_esp.py's SNDR records point at.

The game-ready form (the squelch recipe, memory wet-squelch-sound-recipe): mono, 44.1 kHz, 16-bit PCM, loudness
normalised to -16 LUFS with a -1.5 dBTP ceiling. Sources are numbered in file-name order.

    python tools/make_sounds.py
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'sounds' / 'src'
OUT = ROOT / 'build' / 'sound' / 'Sound' / 'FX' / 'Anatomy'


def main():
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('ffmpeg is not on PATH')
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for kind in sorted(p for p in SRC.iterdir() if p.is_dir()):
        for n, src in enumerate(sorted([*kind.glob('*.mp3'), *kind.glob('*.wav')]), 1):
            dst = OUT / f'{kind.name}_{n}.wav'
            subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-i', str(src), '-ac', '1', '-ar', '44100',
                            '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'pcm_s16le', str(dst)], check=True)
            made.append(dst.name)
    print(f'{len(made)} clips -> {OUT}: {", ".join(made)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
