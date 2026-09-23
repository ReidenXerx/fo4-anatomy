# Anatomy (working name)

A working vagina and anus for the CBBE female body in Fallout 4: real geometry, ZeX genital
bones, and OCBP/OCBPC physics, so that a collision opens the body rather than a script.

Status: the body is **aligned to today's CBBE and verified**. ZeX bones and weights, physics
configs and the in-game test are next.

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

See `docs/decisions.md` for what is settled and why, and `docs/research.md` for the measurements
behind it.
