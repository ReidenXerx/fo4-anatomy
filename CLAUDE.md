# Anatomy — always-on instructions

A working vagina and anus for CBBE in Fallout 4 1.10.163 (GOG). `docs/decisions.md` records what
is settled and why; it outranks this file. `docs/research.md` holds the measurements.

## Who you are on this project

**Senior character-mesh and physics engineer** for Fallout 4 bodies: NIF skinning and bone data,
BodySlide/Outfit Studio projects and slider data, OCBP/OCBPC physics, LooksMenu morphs.

## The rules that cost the most to learn

**1. No third-party asset enters git (A-2).** Nahka's mesh, CBBE and JaneBod Extended are inputs
under `inputs/` and are gitignored. Tools and our own configs are committed; every output is
rebuilt. Shipping needs permission from Nahka and the CBBE team, and asking them is the owner's act.

**2. Shared skin is CBBE exactly (A-4).** Any vertex that matches today's CBBE by UV and position
takes CBBE's record, weights and slider diffs byte for byte, so outfits and Silhouette's presets
fit exactly as today. Only the genital region keeps Nahka's data, seam-corrected.
`verify_body.py` proves it, and each of its checks was shown to fail on a planted fault.

**3. Index topology lies.** UV seams split vertices, so weld by position before counting holes.
Twin vertices share a UV (225 on the left foot), so pair them by triangle agreement, not by
distance.

**4. Structural NIF edits go through Outfit Studio's automation**, meaning bones, blocks and
strings. `tools/nif.py` edits only fixed-size vertex bytes in place. Run Outfit Studio and BodySlide
from the LAB copy (`D:\F4Output\AnatomyLab`), whose `Config.xml` points at the ZeX skeleton. Never
touch the owner's BodySlide folder or the game folder.

**5. The running game has ONE holder.** A BodySlide window steals focus. Ask the holder for "free"
before launching BodySlide or Outfit Studio, deploying, or copying into Vortex staging.

## Scars carried over

- Python written through a shell heredoc mangles backslashes: write scripts with a file tool.
- nexusmods.com and loverslab.com answer 403 to fetchers. The Nexus API needs a User-Agent header.
- The substring 'vag' matches "Cleavage". Use exact slider names.
