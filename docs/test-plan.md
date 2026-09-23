# In-game test plan

## 1. Install (the owner, with the game closed)

1. In Vortex, install `D:\F4Output\AnatomyLab\package\Anatomy-test-<stamp>.7z`: drag it onto the
   Mods page and enable it. It has no plugin to enable.
2. Resolve its three conflicts so that **Anatomy-test loads after**:
   - `bodyslides_f4_sd` (FemaleBody.nif / .tri)
   - MadKita's Actual Jiggle (ocbp.ini)
   - Jiggle Physics (OCBPCollisionConfig.txt)
3. Deploy.

To undo, disable the mod and Deploy again; every original file comes back.

## 2. Run (fo4-mcp holds the game)

- **Save:** fo4-mcp's usual test save (`f4mcp-before-actions`), or the owner's "Copy of my main save".
- **Actors:** one female NPC (any, with a Silhouette body) and one male NPC with BodyTalk4, both
  near the player (`nearby`).
- **Checks, each with a close screenshot of the crotch and a wide one:**

  | # | Situation | Expect |
  | --- | --- | --- |
  | 1 | Female standing, then walking | The vulva renders with no hole, stretch or seam. The labia do not wobble while walking. Breasts now jiggle: that was the breast fix, and before it they did not. |
  | 2 | AAF vaginal position, penetration frames | The lower labia open around the shaft (the collisions), then close again. No spikes or explosions. |
  | 3 | AAF anal position | The anus ring opens around the shaft. |
  | 4 | Hands on breasts, if the pack has one | The breasts dent away from the fingers. That hand collision was configured all along and only now has bones to move. |

- **Logs to bundle:**
  - `Documents\My Games\Fallout4\F4SE\f4se.log`, which should say "OCBPC plugin 00000018 loaded
    correctly" (OCBPC writes no log of its own);
  - `aaf.log`;
  - `Documents\My Games\Fallout4\Logs\Script\Papyrus.0.log`;
  - a `crashbundle.sh` bundle on any crash.

## 3. What each failure would mean

| Seen | Likely cause | Where to fix |
| --- | --- | --- |
| Vulva torn or spiked at rest | a bind transform or weight wrong | `zex_bones.py` (verify_zex passed, so look at the twins' pick_four) |
| Labia snap to the midline at rest | OCBP SETS local position (original CBP), dropping the 1.51 rest offset | move physics from `Vagina_CBP_L_02` to `L_01` only, or weight the lower labia to `L_01` |
| No opening in scenes | colliders from the partner are not considered (femaleOnly?), or the spheres miss | try `femaleOnly=0` with a whitelist; enlarge the spheres |
| Opening sideways or backwards | the offsets ARE rotated and the placement assumption is off | zero offsets make this unlikely; check where Penis_01-05 actually sit |
| Wobble while walking | spring too soft | raise `stiffness` / `damping` in `[Labia]` |
| Interior textured wrongly | the owner's skin texture has nothing painted at the new UVs | Nahka's `labia_*.tga` ship with the source archive; merge them into the skin |

## Results

### Pass 1 (2026-09-23 11:35, build e52678e0, fo4-mcp): inconclusive
The deploy was verified and OCBPC loaded. Every frame showed clothed actors, or a camera pointed away
from the scene.

### Pass 2 (12:22, build 86f6fc78 = Skin Tint shader fix, fo4-mcp)
- The body renders correctly (Photo78, stripped and standing): CBBE shape, nipples, textures.
  There are no spikes or explosions in any frame.
- Skin tone: after the scene her body and head read as one tone, with no neck seam (Photo111/112).
  This is the shader fix; Photo78's darker face is a dark frame and inconclusive.
- The genitals are not seen yet. Missionary shot from behind the male hides them (Photo104/105),
  and the anal frames came out in a dark corner (Photo106-110).
- **Owner install finding (fo4-mcp):** the ORIGINAL BP70 and Atomic Lust positions do not animate.
  Ulfberth's AAF Patch (UAP) replaced their ESPs, and the original XMLs point at idle forms that
  are gone; the actors stand stripped in idles. Every "[UAP] BP70 - ..." position animates. aaf.log
  also warns "UlfEquip_KW not found in keyword database". Use UAP names in tests; the stripped idle
  of an original name is handy for rest shots.
- Scene mechanics: `skipwalk` starts a scene in 4-6 s; the scene happens at the first actor's position.

### Pass 3 (not run)
Planned: rest from the front, then "[UAP] BP70 - Pit Doggy 02" from behind and from the side at hip
height. A safety classifier stopped it in fo4-mcp's session as it started, and fo4-mcp will not
retry in any form. Agent-driven captures of sex scenes are over: nobody runs them from another
session instead. What the game shows is now the owner's to look at.

### Build 1b5c6f20 DEPLOYED (2026-09-23 15:19, decision A-9 weights and physics)
`tools/restage.py` wrote it into Anatomy-dev in place, and Data holds the same bytes, so no Deploy
is needed. It is verified offline: `verify_zex` PASS, `compare_builds` PASS, and the built body
carries the fitted weights exactly. `tools/fit_check.py` predicts the following, so these are the
things to look for:

| Situation | Build 86f6fc78 (before) | Build 1b5c6f20 (predicted) |
| --- | --- | --- |
| Vaginal: visible lips left inside the shaft | 344 vertices | 127 (Nahka's own slider: 232) |
| Vaginal: lips parting | about 0.2 units | about 1.2 units at the inner lips, sideways |
| Anal: opening | barely | back and sides open; the ring's FRONT cannot (no bone there) |
| Walking or running | flap up to 0.17 / 0.41 | 0.07 / 0.29 |

Positions that animate here are the "[UAP] BP70 - ..." ones: "Pit Doggy 02" (vaginal), and
"Prone Bone Anal 04" (anal, open ground, hidden from the menu).

To undo: restage the previous build, or disable Anatomy-dev and Deploy.

### Genital texture (A-10), staged 15:36, waiting for the owner's Deploy
Six new files in Anatomy-dev (`Textures/Actors/Character/BaseHumanFemale/FemaleBody*`,
`femalebodydirty*`). With the game closed: in Vortex, let Anatomy-dev win its conflict with
"CBBE HeadRear Absolute Fix" (load after), then Deploy. To look for: the inside of the lips and
the canal in Nahka's colouring and tone-matched to the skin; no line where the genitals meet the
crotch skin; no change anywhere else on the body.

### The owner's look (2026-09-23 16:17-16:25, Photo116-124, build 1b5c6f20 + texture)
- At rest, from below (116/117): intact, with no holes or spikes. The vulva reads closed with a
  thin slit line, and the texture patch shows no visible seam. The scene was very dark.
- Doggy (118-120): a ~5-unit dark spike from the anal pocket toward the partner. Cause and fix:
  A-11 (anus physics removed). The pale, straight-edged flaps at the frame edges are the camera's
  near plane cutting the partner's thighs, not the body.
- Cowgirl (121, 123): the shaft enters the vulva with no spike.
- Build 59748b34 (A-11) is packaged and waits for the game to close (`tools/restage.py`, in place,
  no Deploy needed).

### Later looks (2026-09-23 17:00-18:15), and what they turned out to mean
- Builds df85d105 / 118d00cb (A-12, A-13) still showed the rod (Photo125-137). The diagnostic body
  0f68d592, with no genital weight at all and no twin physics, showed none (Photo141-144). The
  owner's words: "vagina itself and lips looks gorgeous".
- The cause was found offline at 18:30 (A-14): the women's skeleton has no genital bones, so
  every look before this had no genital physics at all.

### Build e157909873fb (A-14), staged 18:45: needs the owner's Deploy BEFORE the game starts
- New file in Anatomy-dev: `Meshes/Actors/Character/CharacterAssets/female/skeleton.nif`. The
  conflict rule: Anatomy-dev wins over Skeletal Adjustments for CBBE. Then confirm with
  `python tools/skeleton.py --deployed`, which must print 0 missing.
- Rewritten in place: FemaleBody.nif/.tri (our 9 bones), ocbp.ini (MadKita's 18 lines back, plus
  Vulva/LabiaOuter/Labia/Anus), OCBPCollisionConfig.txt (8 affected spheres).
- What to look at:
  - Vaginal (missionary, doggy, cowgirl): no fin or rod anywhere. The inner lips part around the
    shaft; the outer lips squish a little.
  - Only in ZaZOut4 pillory scenes, whose animations also set VaginaPenetrate 1.0: whether the
    opening is too wide (simulated median radius 1.82 against a 1.55 shaft).
  - One anal position: the ring opens around the shaft, and the shaft enters the ring rather
    than behind it.
  - Walking or running nude: a small lip wobble (0.3 / 0.6 units).
- The deploy (19:00-19:04): the first Deploy gave `female\skeleton.nif` to Skeletal Adjustments
  (vortex.deployment.json said so), and the game was started by mistake and closed at once. The
  second, after the conflict rule, put ours in Data; `skeleton.py --deployed` reported 0 missing.

### The owner's look at A-14 (19:05-19:12): it works
- "man it works! ... only 1 thing we need to widen vagina slightly more". Photo145 (standing,
  bent over, from below): intact, with no fin or rod. The pale straight slivers are the near plane
  cutting the partner.
- A-15: build bbbc36acde38 opens the entrance to the shaft (gain 1.35), restaged in place.
- Still to look at: the wider entrance in a vaginal scene, one anal scene, and walking nude.

### The arousal MCM (A-18), staged 21:06 on build a13c4011c17b
- The new `Arousal.pex` is live already (rewritten in place). The two MCM files are new, so they
  need the owner's Deploy: `MCM/Config/Anatomy/config.json` and `settings.ini`. Until then MCM has
  nothing for Anatomy, and the script keeps its defaults, which are A-16's behaviour.
- Checks, after the Deploy:
  1. Mod Configuration Menu lists "Anatomy" (Anatomy.esp must be enabled).
  2. "Arousal nipples" off: within a few seconds of closing the menu, every aroused woman's nipples
     are back to her own.
  3. On again, "Nipple response" at 2 shows bigger nipples, and at 0 no change.
  4. "Being in a scene" off: a woman in a scene stays as she is. "Watching a scene" still counts
     for onlookers.
- Still open from A-17: which object the purple knotted toy was (look it up in
  `Documents/My Games/Fallout4/F4SE/anatomy_ocbpc.log`), a DR dildo or bat scene, and one anal
  scene.

### Build 17f97e158c01 (A-19: our own weights, gain 1.40), restaged in place at 21:15
- JaneBod's painting is gone. The vulva has our own pad, and the entrance's gain is 1.40. The
  simulation matches the deployed build's clipping within 1%, with less flap when walking.
- Look for: in a vaginal scene, the entrance's FRONT edge (toward the clitoris) should clear the
  shaft as it did in Photos 155-156. Walking nude, the vulva should not flap more than before.
- No Deploy needed for this one. The MCM files above still need theirs.

### The mouth (A-20), restaged in place at 21:42 (fork 1df5ed8; body still 17f97e158c01)
- No Deploy is needed: `cbp.dll` and `ocbp.ini` were rewritten through their links.
- First, `Documents/My Games/Fallout4/F4SE/anatomy_ocbpc.log` must say `[mouth] on: 2 chain(s)`. If
  it says "this game build is not the one...", the hook stayed off and nothing else changed.
- In an oral scene:
  - the lips should part around the shaft instead of closing through it (Photo150's case);
  - the jaw should follow as the shaft slides, and hold between strokes;
  - once it is out, her own face (the animation's, AAF's, Rapport's) should come back within about
    half a second.
- The log also prints each mouth's place, `[mouth] <id> (female): HEAD (...) -> mouth (...)`, and each
  first contact with its Jaw Open. If the mouth never opens, those lines show whether the mouth
  point sits on her face.
- Kissing and ordinary dialogue must look exactly as before: no chain comes near a mouth there.

### Zero-touch (A-21), staged 22:08: needs ONE Deploy (fork 0e60cc0, body 17f97e158c01)
- The Deploy (Vortex):
  - gives `female/skeleton.nif`, `ocbp.ini` and `OCBPCollisionConfig.txt` back to Skeletal Adjustments,
    MadKita and Jiggle Physics;
  - adds `F4SE/Plugins/Anatomy/ocbp.ini`, `F4SE/Plugins/Anatomy/OCBPCollisionConfig.txt` and the MCM
    files.
- Without the Deploy, the new DLL runs on the old files exactly as before.
- After it, check `anatomy_ocbpc.log`:
  - `[bones] <id>: created 15 of our nodes under Pelvis_skin, pointed 9 skin entries at them`, once for
    each woman in range;
  - `[mouth] on: 2 chain(s)`.
- In game:
  - women exactly as before: no fin when walking, sitting or in scenes;
  - lips open to a shaft;
  - a fist stretches the entrance;
  - the mouth opens in an oral scene.
- If a fin comes back, the run-time bones failed. Re-adding the patched skeleton is one restage away.

### The genitals' own shape (A-22), restaged 22:21, build b72181014994: DEPLOY BEFORE PLAYING
- The body in Data is already the two-shape one. Its material and textures reach Data only with the
  Deploy; before it, the genitals would render with missing textures.
- After the Deploy, the genitals should show Nahka's mucosa, which A-10 never actually showed. The
  seam to the crotch skin should not show.
- In BodySlide the set is now "Anatomy Body", for rebuilding with any preset.

### Build e030b9406d09 (A-23), restaged in place at 22:34: no Deploy needed
- Same geometry and physics as b72181014994, rebuilt from the player's CBBE plus Nahka's patch.
- The arousal script now removes our nipple layer under Silhouette's heavy-armour marker. Nothing
  changes until Silhouette ships its refit.

### The mouth crash fix (fork 870adc4), cbp.dll written in place at 23:33: no Deploy needed

What broke:
- From 22:46 every save load crashed about 0.3 s in, with no crash log. Five times: 22:48, 22:56,
  23:03, 23:06 and 23:09.
- The Windows Application log shows Fallout4.exe+0x668A0D. That is inside the face merge the mouth
  hooked.
- An A/B by the fo4-mcp session with `[Mouth] enabled=0`: the same save loaded and stayed up.
- Cause: DetourXS copied 14 of the merge's 17 prologue bytes (field notes, the face engine).

What is live now (sha e57d45f5f8df): the mouth hooks the merge's call site and never touches its code.
The discovery log keeps the last four runs (`anatomy_ocbpc.1.log` is the run before).

Check:
- `anatomy_ocbpc.log` says `[mouth] on: 2 chain(s), props 0, gap F 2.97 M 2.30; the merge's call
  hooked, its code untouched (prologue still the engine's: 1)`.
- The save loads and the game stays up. Crowded interiors (the Third Rail, Goodneighbor) are where
  it died.
- In an oral scene the mouth opens to the shaft, and it gives the face back 0.35 s after contact ends.
- If the game ever closes by itself, look in the Windows Application log (event 1000) before
  anything else.
