# Courtesy messages (drafts; sending them is the owner's act)

Nahka's and ericncream's permissions already cover what Anatomy does (release-plan.md, read from
their pages on 2026-09-23): those two are thanks and a heads-up, not requests. The CBBE one is a
request. Send them before or with the
release, from the owner's own accounts.

## Nahka (LoversLab, Animated Fannies, 4302)

> Hi Nahka,
>
> I'm releasing a Fallout 4 mod, *Anatomy - CBBE Genitals, Physics and Arousal*, built around the
> vulva and anus from your Animated Fannies. Your page says they are up for adoption and free to
> use, and I wanted you to hear it from me rather than stumble on it.
>
> Only your own work ships, as a patch. The player's own CBBE and skin are read from their install
> and your geometry, sliders and texture island are applied to them, so none of CBBE's files are
> redistributed. They get collision physics (they open to a penis, a hand or a toy and stretch),
> and their own shape and material. You are credited first on the page, with BringTheNoise and
> Alan (UN7B).
>
> Thank you for making them and for letting them be used. If you'd like anything changed in how
> you're credited, just say.

## Ousnius, for the CBBE team (Nexus 15): a REQUEST, not a courtesy

Unlike the two above, this one asks. CBBE's rule 3: "For uploading a modified body mesh outside of
sliders, please ask for permission first" (contact Ousnius). Today nothing of CBBE ships (the
builder makes the body on the player's PC). Uploading a pre-built body, on the Anatomy page or
bundled in a collection (Ivy bundles "Anatomy Body (built)"), needs this answer first. Send it by
Nexus private message from the owner's account.

> Hi Ousnius,
>
> I've released a Fallout 4 mod, *Anatomy - CBBE Genitals, Physics and Arousal*, built on CBBE.
> I'd like to ask your permission for one thing your rule 3 covers.
>
> Today none of CBBE's files are uploaded. Anatomy ships a builder that reads the player's own CBBE
> install and adds the genitals (Nahka's vulva and anus, which she put up for adoption) and weights
> for our physics bones, so the modified body only ever exists on the player's PC.
>
> That works, but the builder is the step players stumble on most. I'd like to upload the built
> body itself: as an optional file on the Anatomy page, and bundled inside a Nexus collection that
> uses it. It would be CBBE's body mesh with our genital geometry and weights merged in, plus its
> BodySlide project, so players can still build it to any preset. The builder would stay for anyone
> who prefers it. CBBE is credited on the page and listed as a requirement.
>
> Two things you should know before answering: the Anatomy page is opted into Donation Points, and
> the file would be a modified version of your mesh. If either is a problem, or you'd want it done
> differently, I'll follow what you say. If the answer is no, nothing changes: the builder route
> stays the only one.
>
> Thank you for CBBE.

## ericncream (OCBPC, GitHub ericncream/OpenCBP_FO4)

> Hi ericncream,
>
> Thank you for OCBPC. I've forked it, from abc0192 (the 0.3 release), for a Fallout 4 mod,
> *Anatomy - CBBE Genitals, Physics and Arousal*, which ships the fork's cbp.dll. The source is
> public at github.com/ReidenXerx/fo4-ocbpc.
>
> - The OCBPC code stays under its MIT licence; our changes are GPL-3.0, like your branch today.
> - What it adds: stretch groups; prop colliders (toys) with a target list; bones added to the
>   loaded skeleton at run time; its own config files merged after the player's; and a
>   contact-driven mouth that writes over the face's merged morphs.
> - One fix may interest you, because it applies to your code too. DetourXS's
>   `GetDetourLenAuto` calls `LDE(addr, 0)`, which decodes x86, where a REX prefix counts as an
>   instruction of its own. On an x64 prologue that can cut an instruction in two. Your hook target
>   (+0x211CF80 on 1.10.163) happens to come out at 14 bytes either way, so it has never shown. A
>   17-byte prologue we hooked came out at 14, and every save load crashed. Passing 64 on x64 fixes
>   it (fork 870adc4).
>
> You are credited on the page and in the fork's README.
