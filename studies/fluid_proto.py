"""Fluids prototype, step 1 (the owner, 2026-10-07: "lets try build prototype"): the game's own blood-drip particles,
recoloured, attached at the vulva in game.

Why particles: the game already simulates and draws falling drops (meshes/effects/shaderparticles/
bloodshaderparticlesdrips.nif: two particle systems, gravity, drag, a mesh emitter); their colour comes from ONE
gradient texture (Textures/Effects/Gradients/Blood01Grad.dds), so a cream-white gradient turns blood into fluid.
Why PlaceAtNode: a movable static placed at a named bone with abAttach=true follows that bone (vanilla dripping
ceilings are such statics), so no engine code is needed for the test.

Writes D:/F4Output/fluidtest/Data (a mod folder to install):
    Textures/Anatomy/Fluid/FluidGrad.dds      the gradient, recoloured (alpha over the drop's life kept)
    Meshes/Anatomy/Fluid/DripTest.nif         the blood drips pointed at it
    AnatomyFluidTest.esp                      light; MSTT 0x800 AnatFluidDripTest
    Scripts/AnatomyFluidTest.pex              cgf "AnatomyFluidTest.Drip" / cgf "AnatomyFluidTest.Stop"
"""
import io
import pathlib
import struct
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, r'C:\Users\DuduPhudu\Documents\Projects\fo4-refit\tools')
import gamedata  # noqa: E402
import nif  # noqa: E402

from PIL import Image  # noqa: E402

DATA = pathlib.Path(r'D:\SteamFreeGames\Fallout 4 AE\Data')
OUT = pathlib.Path(r'D:\F4Output\fluidtest\Data')
GRAD_OLD = 'Textures\\Effects\\Gradients\\Blood01Grad.dds'
GRAD_NEW = 'Textures\\Anatomy\\Fluid\\FluidGrad.dds'
PLUGIN = 'AnatomyFluidTest.esp'
FLUID = (238, 234, 222)        # a warm off-white; the gradient's alpha (its fade over the drop's life) is kept


def read_ba2(rel, pattern):
    for ba in sorted(DATA.glob(pattern)):
        b = gamedata.Ba2(ba)
        try:
            return b.read(rel)
        except KeyError:
            continue
    raise SystemExit(f'{rel}: not in {pattern}')


def dds_rgba(img):
    """An uncompressed 32-bit DDS (A8R8G8B8) with no mips: the gradients are tiny."""
    w, h = img.size
    pf = struct.pack('<II4sIIIII', 32, 0x41, b'\0\0\0\0', 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    head = struct.pack('<4sIIIIIII', b'DDS ', 124, 0x100F, h, w, w * 4, 0, 0) + b'\0' * 44 + pf + \
        struct.pack('<IIIII', 0x1000, 0, 0, 0, 0)
    r, g, b, a = img.split()
    return head + Image.merge('RGBA', (b, g, r, a)).tobytes()


def gradient():
    src = Image.open(io.BytesIO(read_ba2(r'textures\effects\gradients\blood01grad.dds', 'Fallout4 - Textures*.ba2')))
    src = src.convert('RGBA')
    px = src.load()
    out = Image.new('RGBA', src.size)
    po = out.load()
    for y in range(src.size[1]):
        for x in range(src.size[0]):
            r, g, b, a = px[x, y]
            lum = max(r, g, b) / 255.0                      # keep the gradient's light/dark course, in our colour
            po[x, y] = tuple(int(c * (0.55 + 0.45 * lum)) for c in FLUID) + (a,)
    dest = OUT / GRAD_NEW
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(dds_rgba(out))
    return dest


def mesh():
    raw = read_ba2(r'meshes\effects\shaderparticles\bloodshaderparticlesdrips.nif', 'Fallout4 - Meshes.ba2')
    t = pathlib.Path(tempfile.mkdtemp()) / 'src.nif'
    t.write_bytes(raw)
    f = nif.Nif(t)
    old, new = GRAD_OLD.encode('latin1'), GRAD_NEW.encode('latin1')
    replace = {}
    for i, k in enumerate(f.types):
        if k != 'BSEffectShaderProperty':
            continue
        o, s = f.offsets[i]
        blk = bytes(f.b[o:o + s])
        at = blk.find(old)
        if at < 4 or struct.unpack_from('<I', blk, at - 4)[0] != len(old):
            raise SystemExit(f'block {i}: the gradient path is not a sized string where expected')
        replace[i] = blk[:at - 4] + struct.pack('<I', len(new)) + new + blk[at + len(old):]
    if len(replace) != 2:
        raise SystemExit(f'expected 2 effect shaders with the blood gradient, found {len(replace)}')
    dest = OUT / 'Meshes/Anatomy/Fluid/DripTest.nif'
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = bytearray(f.with_blocks(replace))
    tmp = pathlib.Path(tempfile.mkdtemp()) / 'mid.nif'
    tmp.write_bytes(out)
    g = nif.Nif(tmp)
    for i, k in enumerate(g.types):                   # the owner, 10-07: "put more of it there"
        o, s = g.offsets[i]
        if k == 'NiFloatInterpolator':                # the emitters' birth rates (drops per second)
            v = struct.unpack_from('<f', out, o)[0]
            struct.pack_into('<f', out, o, v * 2.0)
        elif k == 'NiPSysMeshEmitter':                # the drops' radius and its variation
            r, rv = struct.unpack_from('<ff', out, o + 13 + 40)
            struct.pack_into('<ff', out, o + 13 + 40, r * 1.5, rv * 1.5)
    dest.write_bytes(bytes(out))
    nif.Nif(dest)                                           # it must read back
    return dest


def plugin():
    import esl_dist
    model = b'Anatomy\\Fluid\\DripTest.nif\0'
    body = (esl_dist.field('EDID', b'AnatFluidDripTest\0') + esl_dist.field('OBND', struct.pack('<6h', -8, -8, -16, 8, 8, 2))
            + esl_dist.field('MODL', model) + esl_dist.field('DATA', b'\0'))
    dest = OUT / PLUGIN
    # 0x801: a CONTROL, the vanilla cave drips (clearly visible): shows whether attaching at the bone works at all
    ctrl = (esl_dist.field('EDID', b'AnatFluidDripControl\0') + esl_dist.field('OBND', struct.pack('<6h', -8, -8, -16, 8, 8, 2))
            + esl_dist.field('MODL', b'Effects\\FXDripsLots.nif\0') + esl_dist.field('DATA', b'\0'))
    # 0x802: an EFFECT SHADER, our copy of the vanilla BloodSplatterHeavyParticles (Fallout4.esm 002301C5). The drip
    # nif is a SHADER-PARTICLE model: the game draws it only as an effect shader played on an actor (it emits from
    # her body's surface), never as a placed object - why the MSTT test drew nothing (10-07). Gradient and model ours.
    import json
    src = json.loads((OUT.parent / 'efsh_bloodsplatterheavy.json').read_text())
    efsh = b''
    for st, hx in src['subs']:
        d = bytes.fromhex(hx)
        if st == 'EDID':
            d = b'AnatFluidShader\0'
        elif st == 'NAM8':
            d = GRAD_NEW.split('\\', 1)[1].encode('latin1') + b'\0'      # relative to Textures
        elif st == 'MODL':
            d = model
        elif st == 'MODT':
            continue                                                    # the texture hash list is optional
        efsh += esl_dist.field(st, d)
    esl_dist.write_plugin(dest, ['Fallout4.esm'], [('MSTT', 0x800, body), ('MSTT', 0x801, ctrl), ('EFSH', 0x802, efsh)])
    return dest


SCRIPT = '''Scriptname AnatomyFluidTest
{Fluids prototype (fo4-anatomy studies/fluid_proto.py): the recoloured blood drips at the player's vulva bone.
Console: cgf "AnatomyFluidTest.Drip" / cgf "AnatomyFluidTest.Stop"}

Actor Function Target() global
    ; the actor clicked in the console, else the player
    Actor a = Game.GetCurrentConsoleRef() as Actor
    if !a
        a = Game.GetPlayer()
    endif
    return a
EndFunction

Function Drip() global
    Actor player = Target()
    Form drip = Game.GetFormFromFile(0x800, "AnatomyFluidTest.esp")
    if !drip
        Debug.Notification("AnatomyFluidTest.esp is not loaded")
        return
    endif
    ObjectReference r = player.PlaceAtNode("AnatVulva", drip, 1, false, false, false, true)
    if r
        Debug.Notification("Fluid test: drips at AnatVulva of " + player.GetDisplayName())
    else
        Debug.Notification("Fluid test: no AnatVulva on " + player.GetDisplayName() + " (a woman with the Anatomy body, undressed?)")
    endif
EndFunction

Actor Function NearestNPC() global
    ; the nearest NPC that is not the player (FindClosestActorFromRef returned the player herself, 10-07)
    Actor player = Game.GetPlayer()
    Keyword npc = Game.GetFormFromFile(0x013794, "Fallout4.esm") as Keyword
    ObjectReference[] near = player.FindAllReferencesWithKeyword(npc, 600.0)
    Actor best = None
    float bestDist = 100000.0
    int i = 0
    while i < near.Length
        Actor a = near[i] as Actor
        if a && a != player && !a.IsDead()
            float d = player.GetDistance(a)
            if d < bestDist
                best = a
                bestDist = d
            endif
        endif
        i += 1
    endwhile
    return best
EndFunction

Function Report(string what, Actor a, ObjectReference r) global
    ; where the placed effect really is, and whether the game drew it: tells "not attached" from "not rendered"
    float dz = r.GetPositionZ() - a.GetPositionZ()
    string msg = "Fluid test " + what + " on " + a.GetDisplayName() + ": " + (r.GetDistance(a) as int) + " units from her, " + (dz as int) + " up"
    msg += ", enabled " + r.IsEnabled() + ", 3D " + r.Is3DLoaded()
    Debug.Notification(msg)
    Debug.Trace("[AnatomyFluidTest] " + msg, 0)
EndFunction

Function ControlHere() global
    ; the vanilla cave drips placed at her feet, NOT attached: does such an effect show at all?
    Actor a = NearestNPC()
    if !a
        Debug.Notification("Fluid test: no NPC within 600 units")
        return
    endif
    ObjectReference r = a.PlaceAtMe(Game.GetFormFromFile(0x801, "AnatomyFluidTest.esp"), 1, false, false, false)
    if r
        r.MoveTo(a, 0.0, 0.0, 120.0, true)
        Report("CONTROL HERE", a, r)
    endif
EndFunction

Function DripNear() global
    ; the actor closest to the player (no console click: BetterConsole crashed showing an NPC's details, 10-07)
    Actor a = NearestNPC()
    if !a
        Debug.Notification("Fluid test: no NPC within 600 units")
        return
    endif
    Form drip = Game.GetFormFromFile(0x800, "AnatomyFluidTest.esp")
    ObjectReference r = a.PlaceAtNode("AnatVulva", drip, 1, false, false, false, true)
    if r
        Report("drips", a, r)
    else
        Debug.Notification("Fluid test: no AnatVulva on " + a.GetDisplayName() + " (a woman with the Anatomy body, undressed?)")
    endif
EndFunction

Function ControlNear() global
    ; the vanilla cave drips on the closest actor: does attaching at AnatVulva work at all?
    Actor a = NearestNPC()
    if !a
        Debug.Notification("Fluid test: no NPC within 600 units")
        return
    endif
    Form ctrl = Game.GetFormFromFile(0x801, "AnatomyFluidTest.esp")
    ObjectReference r = a.PlaceAtNode("AnatVulva", ctrl, 1, false, false, false, true)
    if r
        Report("CONTROL", a, r)
    else
        Debug.Notification("Fluid test CONTROL: no AnatVulva on " + a.GetDisplayName())
    endif
EndFunction

Function ShaderNear() global
    ; our cream drips as an EFFECT SHADER on the nearest NPC for 20 s (emitted from her body's surface)
    Actor a = NearestNPC()
    EffectShader fx = Game.GetFormFromFile(0x802, "AnatomyFluidTest.esp") as EffectShader
    if !a || !fx
        Debug.Notification("Fluid test: no NPC near, or no shader (restart the game after an update)")
        return
    endif
    fx.Play(a, 20.0)
    Debug.Notification("Fluid test SHADER: cream drips on " + a.GetDisplayName() + " for 20 s")
EndFunction

Function ShaderVanillaNear() global
    ; the game's own red blood drips (BloodSplatterHeavyParticles), the control for the shader route
    Actor a = NearestNPC()
    EffectShader fx = Game.GetFormFromFile(0x2301C5, "Fallout4.esm") as EffectShader
    if !a || !fx
        Debug.Notification("Fluid test: no NPC near")
        return
    endif
    fx.Play(a, 20.0)
    Debug.Notification("Fluid test SHADER CONTROL: red blood drips on " + a.GetDisplayName() + " for 20 s")
EndFunction

Function Stop() global
    int n = 0
    Form drip = Game.GetFormFromFile(0x800, "AnatomyFluidTest.esp")
    Form ctrl = Game.GetFormFromFile(0x801, "AnatomyFluidTest.esp")
    while n < 16
        if n == 8
            drip = ctrl
        endif
        ObjectReference r = Game.FindClosestReferenceOfTypeFromRef(drip, Game.GetPlayer(), 2000.0)
        if !r
            if n < 8
                n = 8
            else
                n = 16
            endif
        else
            r.Disable(false)
            r.Delete()
            n += 1
        endif
    endwhile
    Debug.Notification("Fluid test: drips removed")
EndFunction
'''


def script():
    src = pathlib.Path(tempfile.mkdtemp()) / 'AnatomyFluidTest.psc'
    src.write_text(SCRIPT, encoding='ascii')
    out = OUT / 'Scripts'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'AnatomyFluidTest.pex').unlink(missing_ok=True)   # a stale .pex must not pass for a fresh one
    base = r'D:\F4CustomMods\PapyrusBase\Source\Base'
    f4se = r'D:\Vortex\fallout4\mods\Fallout 4 Script Extender 42147 0.7.9 2026-08-18T14-42Z 2hTc9ppIs\Data\Scripts\Source'
    r = subprocess.run([r'D:\GOGGames\Fallout 4 GOTY\Papyrus Compiler\PapyrusCompiler.exe', str(src),
                        '-f=Institute_Papyrus_Flags.flg', f'-i={f4se};{base};{src.parent}', f'-o={out}'],
                       capture_output=True, text=True)
    print(r.stdout[-800:], r.stderr[-400:])
    pex = out / 'AnatomyFluidTest.pex'
    if not pex.exists():
        raise SystemExit('the test script did not compile')
    return pex


if __name__ == '__main__':
    for step in (gradient, mesh, plugin, script):
        print(step.__name__, '->', step())
