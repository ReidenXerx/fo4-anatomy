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
  - Whether the opening is doubled (BP70's VaginaPenetrate morph plus physics).
  - One anal position: the ring opens around the shaft, and the shaft enters the ring rather
    than behind it.
  - Walking or running nude: a small lip wobble (0.3 / 0.6 units).
