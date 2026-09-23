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

### Pass 3 (requested): camera at hip height, lit
Rest from the front (stripped via a non-animating original position), then "[UAP] BP70 - Pit Doggy 02"
from behind at hip height.
