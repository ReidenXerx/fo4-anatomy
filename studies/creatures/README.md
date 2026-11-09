# Creature genitals and ghoul skin: the build scripts (2026-11-09)

The pipeline behind the Immersive creature mods and the Ivy creature/ghoul packs. Nothing here ships: these scripts read
the game's vanilla meshes and textures (and, for positions only, UAP's and darthroman's AAF creature pack's meshes) and
write our meshes. Paths are the author's (D:\F4Output, D:\SteamFreeGames\Fallout 4 AE); Blender 5.1 + PyNifly for exports.

Per creature: `<x>_geom.py` (numpy geometry, measured against the reference pack so AAF animations line up) ->
Blender export of OUR shapes only (`canine_build.py`, `chain_build.py`, `nick_build.py`, `dc_build.py`) -> `seg_fix.py`
(dismember-safe segments) -> `tri_normalize.py` / `geom_tri.py` (morphs) -> `transplant.py` (the vanilla nif's bytes +
our shapes; never a PyNifly round trip of a game nif: that crashed dismemberment) -> `transplant_check.py`.
Drivers: `canine_all.py`, `sm_all.py`, `bh_vanilla.py` (behemoth on the vanilla body, loincloth cut by `bh_cut.py`),
`yg_all.py`, `rs_all.py`, `mr_all.py`, `nick_*.py`, `dc_standalone.py` (deathclaw, own plugin), `feral_all.py` +
`feral_transplant.py` (ferals). Renders: `feral_tex_prep.py` + `feral_tex_render.py`, `storefront_renders.py`.
Packages: `creature_fomods.py` (FOMOD standard), `pack_any.py`.

Ghoul skin: `ghoul_*.py` here are the first (Ivy) job. The player-side version lives in the builder:
`tools/ghoul_skin.py`, `tools/ghoul_redirect.py`, `tools/ghoul_stage.py`.

Scars: PyNifly flips V on export; Blender shows a skinned shape at its node offset (skin space is what the game
uses); the deployed Data holds OUR creature meshes, so references are read from the mod staging folders.
