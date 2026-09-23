# Release plan (decided 2026-09-23)

## The owner's answers

- **Platform:** Nexus Mods ("nexusmods tolerate with sex content there are a lot of it").
- **Version 1 = everything planned:**
  - genitals and physics;
  - arousal nipples;
  - fisting and toys;
  - the contact-driven mouth.
- **MCM:** arousal only.
- **Delivery:** a **builder tool**, so nothing of anyone else's is redistributed. The owner asked
  whether a FOMOD could run it; it cannot (see below). So the FOMOD installs our files, the player
  runs the builder once, and installs its output as a mod.

## What we may ship, and what we may not (read from each page, 2026-09-23)

| Part | Source and its permissions | In the release |
| --- | --- | --- |
| Vulva/anus geometry | Nahka's, shipped in Animated Fannies (LL 4302). Its page: "up for adoption … can be used in whatever way any other modders see fit - no need to ask me for permission". Credits Nahka, BringTheNoise, Alan (UN7B). | the builder reads the player's own download; credit all |
| CBBE body base | Nexus 15, rule 3: "For uploading a modified body mesh outside of sliders, please ask for permission first" (contact Ousnius). | built on the player's PC from their CBBE; never uploaded |
| JaneBod's genital weight pattern | Nexus 32442: asset use needs permission. | **replaced by our own weights (A-19)**: nothing of it ships or is read |
| Women's skeleton (Skeletal Adjustments, Nexus 39006) | asset use with credit is allowed; modification needs permission; no upload elsewhere | the builder adds our bones to whatever skeleton the player has |
| ocbp.ini (MadKita's Actual Jiggle, Nexus 90677) | modification and asset use free, no credit needed | the builder merges our lines into the player's own ini |
| OCBPCollisionConfig.txt (Jiggle Physics, Nexus 82699) | asset use needs permission | the builder appends our lines to the player's own file |
| Skin textures | the player's own skin mod; CBBE's texture resources allow variants with credit and links | the builder patches the player's own maps |
| OCBPC fork (fo4-ocbpc) | GPL-3.0 (ericncream/OpenCBP_FO4); OCBPC FPS Fix (95003) is permissive too | ship `cbp.dll` with a public source link |
| Anatomy.esp, scripts, MCM, tools | ours | ship |

## Why not the FOMOD itself

- FOMOD XML chooses files by conditions; it cannot run code.
- C#-scripted FOMODs are poorly supported in Vortex and unsupported in MO2.
- The builder is therefore a separate step, the same pattern as BodySlide, Nemesis or DynDOLOD
  output: the tool writes a mod folder that the player installs.

## Work list

1. ~~Replace the JaneBod-derived weights (the vulva sway and the outer-lip base) with our own
   procedural weights~~ Done (A-19); the owner's look in game is still to come.
2. ~~MCM for arousal: on/off, nipple strength, which sources count, rise/fade speed.~~ Done (A-18).
3. ~~The contact-driven mouth~~ Built (A-20, fork 1df5ed8); the owner's look is still to come. It
   writes after the engine's merge, so no AAF block is needed and nothing Rapport does changes.
4. The builder:
   - Windows exe (the Python pipeline, packaged);
   - finds Data through Vortex/MO2, and CBBE's and Nahka's BodySlide files;
   - builds the BodySlide project, patches the skeleton(s) actually in use, merges the physics
     lines, patches the skin;
   - writes "Anatomy - Generated".
5. FOMOD for our static files, the Nexus page (through nexus-tools), credits, GPL source link, a
   public fo4-ocbpc repo, and the final name.
6. Courtesy messages: Nahka, and Skeletal Adjustments' author. Sending them is the owner's act.

## Zero-touch (A-21, owner polls 2026-09-23)

- Nahka's files ship with credit (her page allows any use).
- Nothing we ship or generate overwrites another mod's file, except `cbp.dll`:
  - the fork adds our bones at run time and reads its own physics lines;
  - the genitals get their own texture.
- The builder writes only new files, straight into Data (or MO2's overwrite).
- See builder-design.md.
