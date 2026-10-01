# Anatomy 1.2.0 + Anatomy Engine 1.2.0: the feature facts (for the pages)

For Publisher-bud's pages and articles. The owner's rule: every line says the hard thing that was solved, briefly
("feature: the hard thing, solved"). Each claim carries its decision id (docs/decisions.md); the numbers come from
those entries. NEW means new since the live release (Anatomy 1.1.1, Engine 1.1.5).

| Feature | What was hard | What nobody else does | The number | For the player | Id |
|---|---|---|---|---|---|
| Dynamic labia | No skeleton women load has genital bones, and shipping one would fight every skeleton mod | Bones added at RUN TIME under whatever skeleton the game loaded; inner and outer lips that part, wobble and stretch through collision physics | 9 run-time bones + their stretch children; inner lips collide at 1.7, outer jiggle softer (stiffness 60) | Lips that part around what enters and settle back | A-13, A-14, A-15, A-21 |
| Penis aim | Animations are authored for other bodies, so the shaft goes through thighs and bellies | The shaft locks onto the opening the animation meant (vagina, anus, mouth, a gripping hand) and bends joint by joint along the canal | captures within 35 degrees / 5 units, keeps within 45 / 8 | Penetration that lands, in any pack | A-28 |
| Sex sounds (NEW) | Packs fire canned sounds from animation timings, unrelated to contact, each pack different | The packs' body sounds are muted in scenes (an engine hook on the game's sound call) and our own set plays from each stroke's REAL depth and speed | 9 sound kinds, 37 clips, loudness-matched (-10/-12 LUFS); mute measured on 228 sound records of 9 packs; on by default | Every pack sounds the same and in sync; with Rapport: moans, pain-pleasure for anal and BDSM, climax | A-67, A-68 |
| Men's anus, M-M (NEW) | BodyTalk 4 has a closed pucker and no anus bones; most physics presets simulate women only | BodyTalk's own anus opened on the player's own BodyTalk, with a canal, the same ring physics as hers, aim and sounds; men simulated for our bones even under a femaleOnly preset | canal 8.5 units, 157 new vertices, 4 ring bones, 166 vertices weighted; 0 BodyTalk files shipped | M-M works; build "Anatomy Male Body" | A-69 |
| Vaginal lining (NEW) | The canal sampled ONE texel: a flat colour | Its own seamless unwrap and a painted rugae mucosa | 198 vertices unwrapped, 14 folds, wet within the first 15%; 0 vulva triangles changed | A real lining inside | A-54 |
| Closed anal canal | Looking into the anus showed the inside of the body | A closed canal behind the opening | live since 1.1.1 | You never see through the body | A-50 |
| Skirt physics (NEW) | Linear-blend skinning cannot drape: legs pass through coats and dresses | The engine hangs a ring of skirt bones at the hips and pushes them with the legs every frame, with its own solver (snapped AAF poses included); only cloth that followed nothing but the pelvis is moved to them | 60 bones (12 x 5); legs through the cloth, crouch/sit/stride: coat 24/38/14 -> 5/17/2 %, slinky dress 24/25/20 -> 11/22/6 %, house dress 7/6/5 -> 2/5/1 %; never worse on any tested | Coats and dresses that let the legs move | A-70, fo4-refit R-18, R-19 |
| One-tube collision | A chain of spheres snags on the lips and lets things slip between balls | Every penis chain and toy collides as one smooth tube | - | No snagging, no clipping between balls | A-35, A-38 |
| The mouth | The face is the game's internal animation data, undocumented | Reverse-engineered face data; the mouth opens to what is at the lips over the animation's own face; lips fitted round it per morph | lips fitted from 15 measured morphs per sex | A mouth that wraps the shaft | A-20, A-26, A-32 |
| Glances | - | Eyes meet the partner's for a second or two (with Rapport) | - | Scenes that look alive | A-34 |
| Arousal | - | Rises from scenes, nudity, watching and a companion's own arousal; fades with time; nipples follow | MCM: 1 page | Bodies that react | A-16, A-18 |
| 3BBB bodies (NEW) | 3BBB moves the breasts on its own bones; CBBE's weights fight it | The builder builds on 3BBB when you have it and keeps its breast bones | - | Anatomy on 3BBB | A-57 |
| Built on your PC | Redistributing CBBE or BodyTalk needs their authors' permission | Only Nahka's own work ships, as a patch applied to YOUR CBBE; the builder reads any skin format and finds the game anywhere (Steam, GOG, MO2) | 0 CBBE or BodyTalk files shipped | Your own body, your own skin | A-21, A-23, A-42, A-43 |
| Health check (NEW in 1.2.0's engine) | "It does not work" reports with no information | After every load the engine writes Anatomy_Health.txt (engine, preset, body, builder stamp, actors) and shows a box only on problems | - | Problems named, not guessed | A-60 |
| AE crash family fixed | Nodes created at run time started with garbage reference counts (a CommonLib quirk) and were freed under the body's skin | Zeroed before construction | live since Engine 1.1.4 | Stable in NPC scenes and sleep | A-51..53 |
| One DLL for every version | - | Runtime Database: one cbp.dll for 1.10.163, next-gen and AE | - | No version picking | Engine 1.1.0 |

Installers (both, NEW): the FOMOD standard. Anatomy hard-blocks CBBE.esp; its first page checks your setup (Engine,
F4SE, Runtime Database, BodySlide, the builder); then one page per feature with its card; a page that warns only when
AAF, LooksMenu or Rapport is missing. The Engine's installer: setup, then its five features.
