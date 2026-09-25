# Anatomy - CBBE Genitals, Physics and Arousal: every feature

Working genitals for Fallout 4's CBBE women: real geometry, bones added at run time, collision
physics that opens the body (not a script), a mouth that opens to what is at the lips, and arousal.
It runs on the **fo4-ocbpc** engine (`cbp.dll`, its own mod) and is built on your PC from your own
CBBE and skin.

Each item names its decision in [`decisions.md`](decisions.md) (A-#), where the measurements are.

---

## 1. The body

- **A real vulva, vaginal canal and anal opening** instead of CBBE's closed skin: Nahka's geometry,
  aligned to today's CBBE. 22,488 shared vertices are exactly CBBE's; the 2,811 new or changed ones
  meet the skin with no seam (at most 0.46 units). (A-4, A-9)
- **Built from YOUR CBBE, skin and skeleton** by the Anatomy Builder: nothing of CBBE's or Nahka's
  original files is uploaded; Nahka's work ships only as a patch, with her permission. The rebuild
  equals the direct build to 7e-8. (A-23)
- **The genitals are their own shape with their own material**, so they render with a texture matched
  to your skin mod without overwriting it. (A-22)
- **Colour-matched, feathered texture**: the genital skin takes your body texture's tone (matched per
  channel in linear light); the seam step dropped from 9.0/4.0/8.1 to 2.3/1.1/1.9 (of 255); every
  texel outside the genitals is byte-identical to your skin's. (A-10, A-22)
- **"Opening, front"**, a BodySlide slider (category "Anatomy"): a little more visible opening from
  the front, on top of the built-in one; 0% leaves it as designed. (A-25)
- **Hip fold fixed**: CBBE's pelvis-to-thigh skinning tore the inner hip in legs-up poses; the worst
  edge stretch fell from 11.1x to 4.0x (sitting 10.3x to 3.8x, walking 3.5x to 2.0x). (A-30)
- **Neck seam removed**: the body's neck ring faces the way the head (and CBBE HeadRear Absolute
  Fix's rear piece) does, so the join no longer shows as a line in the light: 14.4 deg median / 37.5
  worst down to 0.0 / 0.3. With Anatomy Rebuild. (A-37)

## 2. Physics: openings, lips, stretch, toys

- **Openings open because contact pushes them**, never because an animation poses them: Anatomy's own
  bones (vulva, outer and inner lips, four around the anus) are added at run time to whatever skeleton
  your game loads. This also cured the "fin/rod" tears of a skeleton with no genital bones: kneeling
  2,613 torn edges -> 0, lying back 3,824 -> 0. (A-14, A-21)
- **Outer lips jiggle** (walking, thrusting, running) and **squish aside** under a hand or shaft.
  (A-13)
- **The vaginal entrance is fitted to the partner's shaft**, tuned in game over several rounds. (A-9,
  A-15, A-19)
- **The anus opens under contact**, placed on its real ring (it reproduces 94% of the source's own
  "AnusPenetrate" shape). (A-14, A-28)
- **Fisting and big toys**: stretch groups open the vagina or anus wider for a fist or a toy than a
  penis ever does, without a penis opening it that far. (A-17)
- **Toys and props collide**: anything an animation hangs on a hand (dildos, a bat) pushes the body
  instead of clipping; a held rifle or a mug does not. (A-17)
- **Contact is one smooth tube, not a string of balls**, for a penis and for a toy: no more lips
  riding in and out between collision balls, no opening parting before the tip arrives. Anus "through"
  rate 72% -> 27%, thrust wobble roughly halved. (A-35, A-38)
- **Super mutants' and other creatures' penis bones collide too.**

## 3. The penis: aim and shape

In AAF scenes only (never two people just standing close).

- **Auto-aim into the right opening**: vagina, anus or mouth, whichever the scene's pose implies,
  correcting animations made for other anatomy. (A-28)
- **The shaft bends along her canal** ("snake in hole") instead of poking through the mons or chin.
  (A-28)
- **Deep throat follows her head and neck**, so the shaft stays inside when her head tilts back.
  (A-28, A-29)
- **Hand jobs**: a gripping hand is recognised and the shaft passes through the grip instead of
  floating off it. (A-28)
- **Mushroom-shaped penis**: a thinner shaft and a bigger head (x1.2-1.25), different per man, on
  BodyTalk4 without touching its files. (A-31)
- **Glans colour**: every man's glans a little redder (a LooksMenu overlay; MCM switch). (A-31)

## 4. The mouth

- **The mouth opens to what is in it** (penis, toy or hand), over the animation's own expression.
  (A-20)
- **Lips fit around the shape inside**, shrink-wrapping a shaft or finger, with corners that open for
  a wide shaft and hug a narrow one, and lips that close quickly between strokes. (A-32)
- **The mouth reads the real width**, glans included. (A-31, A-32)
- **Her face reacts while her mouth is busy**: brows, cheeks and nose, never fighting Rapport's
  expressions. (A-26)
- **Her brows frown as he goes deeper**, orally and, with Rapport, vaginally and anally. (A-29,
  A-33)

## 5. Faces and eyes (with Rapport)

- **Rapport's face is the one that shows in every AAF scene**, including closing eyelids and a jaw an
  animation opened; spoken lines keep their lip sync; faces ease in and out. Works in AAF scenes
  started from anywhere, not only from our mods. (A-27)
- **Glances**: she looks up into her partner's eyes now and then, for a second or two. (A-34)
- **Rapport's MCM tunes the physics side live** (lip clearance and speed, shaft and head size,
  reaction strength, deep face). (A-33)

## 6. Arousal

A real arousal model (AAF keeps none and UAP's decays at once, so Anatomy tracks its own). Every 3
seconds, for women within about 43 m, arousal moves toward the strongest source present:

| source | strength | half-life |
| --- | --- | --- |
| in an AAF scene | 1.0 | 10 s |
| Ivy's own arousal (CompanionIvy) | 0.8 | 20 s |
| a companion's desire (Overture) | 0.7 x desire | 45 s |
| watching a scene within about 17 m | 0.55 | 30 s |
| naked (nothing in the body slot) | 0.3 | 45 s |
| nothing | fades | 60 s |

- **Nipples respond**: longer, perkier and bumped at the tip, on top of her own body, so a
  small-nippled woman stays smaller than a big-nippled one (LooksMenu). (A-16)
- **Under heavy armour they stay flat** when Silhouette marks her heavily dressed, and re-show at once
  when Silhouette rebuilds her body.
- **Nothing calls into AAF**: only its busy keyword is read (a call into AAF can end the calling
  stack).

### MCM page "Anatomy"

| setting | default | what it does |
| --- | --- | --- |
| Arousal nipples | on | off removes every change this mod made to anyone's nipples |
| Nipple response | 1.0 (0-2) | how far nipples rise at full arousal |
| Rise speed | 1.0 (0.25-4) | at 1, a scene takes her halfway up in 10 s, watching one in 30 s |
| Fade speed | 1.0 (0.25-4) | at 1, halfway back a minute after the cause is gone |
| Being in a scene | on | the strongest source |
| Watching a scene | on | within about 17 m of a scene she is not in |
| Companions' own arousal | on | Ivy's arousal, a companion's Overture desire |
| Being naked | on | a little, slowly |
| Glans colour | on | off takes it off every man it was given to |

Without MCM, the same defaults apply.

## 7. Outfits: Anatomy Rebuild (optional download)

- **Every CBBE outfit gets the body's hip handover**, so outfits no longer part from the skin at the
  groin in legs-up poses (up to 3.8 units before; a combat-armour leg in doggy: worst gap 5.10 ->
  2.25). Only the pelvis/spine/thigh skinning near the hip fold moves. (A-36)
- **The neck seam fix** on the body you built. (A-37)
- **Works on what you already built**, with any preset, zaps included: it never runs BodySlide and
  never moves a vertex, a morph or a slider. Measured on 24 outfits: identical to our own verified
  pipeline (weights equal to 0.0000), and a second run changes nothing. `--undo` puts your builds
  back. (A-39)

## 8. Install and safety

- **Zero-touch**: nothing of another mod is overwritten. The only shared file is the engine's
  `cbp.dll`, and that is its own mod. Anatomy's physics lines sit in their own folder and are read
  after yours. (A-21)
- **The builder refuses rather than guesses**: no CBBE BodySlide files, a missing skeleton or skin, or
  its own data missing, and it stops and says which, and how to fix it. It writes only new files, each
  in one step (a crash never leaves half a file), with a log.
- **The release checks itself**: the plugin's records, no developer keys in the shipped ini, every
  file listed back from the archive, and the engine built from the public commit it names.
- **Works with MO2 and Vortex** (MO2: run the builder and Anatomy Rebuild from MO2, like BodySlide).
- **Steam and GOG** 1.10.163 alike.

## 9. Works with

AAF and UAP (scenes), LooksMenu (nipples, glans colour), Rapport (faces, glances, MCM), Silhouette
(armour-aware nipples, BodyGen untouched), Overture and Ivy (arousal sources), CBBE HeadRear Absolute
Fix (neck seam), Jiggle Physics / MadKita's / any OCBPC config (your physics keeps working),
BodyTalk4 men.

## Not yet confirmed in game

Built and tested offline; waiting for an in-game look:
- fisting and big-toy stretch (A-17), toys as one tube (A-38);
- Rapport's MCM knobs and the brows following vaginal/anal depth (A-33).

Known limits: in a two-hole position the aim chooses by geometry alone (A-28); men's own openings are
not modelled; the wrist can show a faint specular line against the hands.
