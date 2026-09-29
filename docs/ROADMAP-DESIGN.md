# Roadmap design notes: the approaches we settled, 2026-09-28

The roadmap (ROADMAP.md) says WHAT; this says HOW, as agreed with the owner, so it is not rediscovered or re-argued
later. Anything still open is marked **Open** and gets discussed when we reach it. Finished work moves to
decisions.md as an A-# entry.

Shared rules for every item:
- Measure offline first (our tools), then the owner's look in game; nothing ships on "it should work".
- A change to the body's vertices, weights or UVs means: a Builder release, a fresh `.tri` for Ivy's bundled body
  (fallout-collection, BodySlide `--trimorphs` from the owner's ShapeData; the .tri is preset-independent), and
  rebuilding the two pre-built optional bodies (Zeroed, Ivy; vanilla skin, no .tri).
- Headless BodySlide shows a "No read/write permission for game data path" modal on the owner's screen that he has
  to click; warn him before a run (it happened with GameDataPath on a Temp folder and on D:\F4Output\Rebuild).
- Engine changes go into both CBPSSE (classic) and CBPSSE-RD (released) and ship as Engine x.y.z after a VirusTotal
  scan of the DLL, through publisher-bud with the owner's go.

---

## 1. The vaginal canal's lining

**Goal.** The vaginal canal's inner walls read as wet mucosa (like the anal canal, A-50), blending into the vulva.

**Facts.** The canal is Nahka's geometry inside the genitals shape (`AnatomyGenitals`), about 6.4 units deep
(z -56 to -49.6 on the reference body), sampling her texture island inside the genitals' tile (A-48).
`tools/mucosa.py` paints a procedural mucosa (tone, depth gradient, folds, wet specular) into any DDS the builder
writes, every mip, block-exact outside its rect. `tools/anal_canal.py` samples its tone from the rim's own texels.

**Built (A-54, 2026-09-30), superseding the texture-only plan below:** Nahka's canal UVs turned out collapsed onto one
texel, so a footprint repaint could only tint it flat. The canal got its own UVs instead (the entrance ring split,
positions and sliders untouched) and a rugae mucosa patch; see decisions.md A-54. Staged in Anatomy-dev on the owner's go.

**Approach (the first plan).** Texture only; no geometry or UV change, so Nahka's detail and every slider stay as they are.
- Find the canal's triangles: genitals triangles deeper than the introitus along `physics_design.VAGINA_AXIS`
  (past a threshold measured on the reference body), not the outer vulva.
- Take their UV footprint in the tile and repaint those texels with mucosa, feathered over a few texels toward the
  entrance so the vulva blends into the lining.
- Vaginal folds run ACROSS the canal (rugae are transverse); the anal canal's run along it. `mucosa.paint` needs a
  fold-direction option for that.
- Tone from the texels just inside the introitus, as the anal canal takes it from the rim.
**Done when.** The builder paints it (a new stage after 8), the owner has looked in game, released as a Builder.

---

## 2. The squeeze jitter

**Goal.** A hand pressing a breast or the butt holds still under the hand instead of twitching, with any preset.

**Built (A-55, 2026-09-30):** measured in ocbpc_sim, the 1/linear below is a unit conversion, not a kick; the real
finds were a hand sinking into the flesh and rotateLinear skipped on collision frames (a swing every frame under
contact). Contact is now a constraint for body bones; the genitals keep OCBPC's push. See decisions.md A-55.

**Cause (the first reading, superseded).** `Thing.cpp` about lines 423-435, in both engines, inherited from OCBPC:
on a collision the bone's velocity is REPLACED by the push (`velocity = collisionVector * timeStep`), and the push
is scaled by `collisionX / linearX`, so a soft preset kicks hardest (MTM's 0.05 means about 20x). The bone is
thrown out of the hand, the spring pulls it back in, it is kicked again: a loop every frame while the hand presses.

**Approach (settled).**
1. Reproduce it first in `ocbpc_sim` (a static hand sphere pressed into a breast bone, soft and firm presets),
   measuring the bone's position frame by frame: the jitter's amplitude is the number to beat.
2. Fix: resolve contact as a constraint. Project the bone out of the sphere to its surface, remove only the
   velocity component pointing into the sphere, add a little tangential friction, and make it frame-rate
   independent. No kick, no 1/linear scaling of the push.
3. Keep the tube collider (`TubePush`) and the genital stretch working as now; re-check the lips and the anus
   still react (the owner likes the anus's reaction to a vaginal penis: it must stay).
**Done when.** The sim shows a steady press holding still for soft and firm presets, then the owner's look.

---

## 3. The inner-thigh crease and the outfit weights

**Goal.** No fold at the inner thigh in legs-up poses (A-30 left 4.0x), and garments worn over the body (panties,
stockings, leg pieces) moving exactly with the skin in deep bends.

**Facts.** `tools/hip_fold.py` (builder stage 3b, A-30) averages only the core split (Pelvis, Pelvis_Rear, Spine1,
both thighs) across a thin band; legs-up 11.1x -> 4.0x. `tools/garments.py` (A-36) regenerates all 964 CBBE garment
sets headless with the body's hip handover. Measuring tools: the LBS posing scripts (scratch aim/hip_compare.py,
crease_proto.py); the pose-gap measure caught three garment scars in A-36.

**Approach (settled).** Widen the blend band (more rings across the pelvis-to-thigh handover), measured legs-up,
sitting and walking; then give over-body garments the same weights by `garments.py` (the owner's deferred item:
"copy their bone weights from our body"), verified with the pose-gap measure.
**Done when.** Legs-up stretch is near 1-2x with no fold, garments show no gap in deep bends, the owner has
looked. Then the shared rule applies: Builder release, fresh .tri, rebuilt pre-built bodies.

---

## 4. 3BBB bodies

**Goal.** Players on a 3BBB body get Anatomy built from THAT body, so 3BBB presets move it (hang50's "no bounce").

**Facts.** 3BBB adds physics bones: three per breast (`LBreast_01..03`), butt (`LButt_01`) and thigh
(`LLeg_Thigh_01_F/R`) bones. Our body is CBBE's plain physics body: one breast bone (`LBreast_skin`) plus CBBE's
cloth bones, which is why 3BBB presets barely move it. The Nahka patch is keyed to CBBE 2.7.2's
`CBBEBodyPhysics.nif` by vertex count, layout and a hash of positions and UVs (`apply_patch.py`).
`builder.breasts_driven` already moves the breasts onto whatever bone the player's ocbp.ini [Attach] names.
Cost: about twice the simulated flesh bones per woman (estimated, not measured).

**Approach (settled).** The builder detects a 3BBB body in the player's BodySlide files and builds from it: the same
genitals, canal and run-time bones, keeping 3BBB's breast/butt/thigh weights. Our CBBE body stays the default and
the lighter choice. Add per-frame physics timing to the engine log to put numbers on the CBBE-vs-3BBB cost.
**Open.** Whether 3BBB's body shares CBBE's vertices (then the patch may apply as is and only weights differ) or
needs its own patch; which 3BBB body (its Nexus page and version). Measure first.

---

## 5. Automatic outfit refits between bodies

**Goal (the owner's idea).** Convert an outfit made for one body to another with no manual Outfit Studio work,
so the owner can publish refits of good outfit mods: vanilla -> CBBE, CBBE -> 3BBB, and to BodyTalk4 for men.

**Publishing policy (the owner, settled).** The original mod is listed as a requirement and credited; authors who
object PM the owner. We do NOT gate a refit on a per-mod permission check.

**Pipeline (settled).** Per outfit, all offline:
1. **Reshape.** Move each outfit vertex by what the body beneath it does between the source and target bodies
   (nearest-surface interpolation over the reference body, the technique `apply_patch` uses to carry CBBE's
   sliders onto Nahka's vertices). Vanilla -> CBBE uses BodySlide's conversion sets (`ConversionSets` in the
   private BodySlide) as the source-to-target morph.
2. **Re-weight.** Copy bone weights from the target body's nearest surface, smoothed (3BBB's extra breast and butt
   bones included, so tops follow the physics). The machinery exists in `garments.py` / `hip_fold.py`.
3. **Sliders.** Carry every target-body slider onto the outfit, so it follows any preset; write a normal BodySlide
   project (`.osp` + ShapeData `.nif` + `.osd`) with `nif.py` / `osd.py`.
4. **Rigid parts.** Detect parts that must not stretch (armour plates, pouches, belts, buckles: connected pieces
   away from the skin and/or rigidly weighted in the source) and move each as one piece, weighted to one bone.
5. **Verify and fix, offline.** Pose and preset sweep with our LBS posing tools: where the body pokes through,
   push those outfit vertices out a little and re-test until clean. `ocbpc_sim` checks tops against moving
   breasts/butt (what matters for 3BBB). Output: the project plus a measured report per outfit ("skirt clips
   2 units at the knees in a crouch") so nothing reaches the owner as a blind guess.
6. **A preview GIF per refit (the owner, settled): users eyeball a sample of the work.** Offline, no game:
   export the refitted outfit, the body and their textures (`nif.py`; DDS decoded by Pillow) to a web 3D format;
   a procedural jump cycle on the skeleton (crouch, push off, airborne, landing, where jiggle shows) plus a slow
   turntable; `ocbpc_sim` drives the breast/butt bones through the jump with the engine's own spring math, so the
   GIF shows the preset's real bounce and whether the top follows it; three.js skins it frame by frame in the
   studio's headless browser (`nexus-tools/studio`, render.mjs), frames -> GIF plus an MP4 for the Nexus gallery.
   Labelled "rendered preview" (simpler lighting than the game). A QA variant paints the clipping report in red on
   the same frames, for the owner only. FO4's own .hkx animations are out of scope (a bigger job); in-game footage
   stays possible through the fo4-mcp session but costs the game and time per outfit.
**Known hard cases.** Long skirts and coats (hanging between the legs needs its own weighting rules), hair or
accessories inside the outfit, outfits whose source body has no reference file here.
**Start (settled).** One vanilla-body outfit the owner picks -> CBBE: converted, measured, then his look in game.
Only after that the batch runner and the other targets (3BBB, BodyTalk4).
**Open.** Where the tool lives (fo4-anatomy's tools or its own repo); the release packaging of a refit mod
(BodySlide project only vs. pre-built meshes too).
