# Anatomy (working name)

A working vagina and anus for the CBBE female body in Fallout 4: real geometry, ZeX genital
bones, and OCBP/OCBPC physics, so that a collision opens the body rather than a script.

Status: the body is **aligned to today's CBBE and verified**, including a real BodySlide build.
Built with "CBBE Curvy", it equals today's CBBE build on all 22,488 shared vertices, and its
`.tri` carries CBBE's 84 morphs unchanged plus the 12 genital ones. ZeX bones and weights
(through JaneBod Extended), physics configs and the in-game test are next.

## How it is built

Nothing third-party is in this repository (decision A-2). The tools rebuild everything from inputs
you place in `inputs/`:

| input | where from |
| --- | --- |
| `inputs/CBBEVagMorphs.rar` | Nahka's BodySlide files (Dropbox link on Nexus 98984 "Expand Holes") |
| your installed CBBE | `Data/Tools/BodySlide` (read only) |

```
python tools/align_body.py      # Nahka's body, aligned to today's CBBE -> build/project
python tools/verify_body.py     # prove it: shared skin exactly CBBE, sliders agree, no stray bones or holes
```

`verify_body.py --plant position|weight|slider|bone` corrupts a copy to prove each check fails.

The lab (`tools/lab.py`) is a private BodySlide copy under `D:\F4Output\AnatomyLab`:

```
python tools/lab.py setup
python tools/lab.py build CBBELab "CBBE Curvy" D:/F4Output/AnatomyLab/out/cbbe
python tools/lab.py build AnatomyLab "CBBE Curvy" D:/F4Output/AnatomyLab/out/anatomy
python tools/compare_builds.py D:/F4Output/AnatomyLab/out/cbbe D:/F4Output/AnatomyLab/out/anatomy
python tools/mask.py            # the genital-region mask for CopyBoneWeights
```

See `docs/decisions.md` for what is settled and why, and `docs/research.md` for the measurements
behind it.
