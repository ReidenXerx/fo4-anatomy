"""Textured offline renders of feral NIFs (PyNifly import, our own Principled material from decoded PNGs).
  blender -b -P feral_tex_render.py -- list <out.json> <nif>...          texture paths each mesh's material names
  blender -b -P feral_tex_render.py -- render <png dir> <shots dir> <tag|nif|views>...
views: comma list of front, back, crotch, gside, chest"""
import json
import math
import pathlib
import sys

import addon_utils
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
MODE = args[0]


def load(path):
    """one nif, or several joined with '+' (e.g. a body and the armour on it, all in one skin space with RAW=1)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable('io_scene_nifly', default_set=True)
    for one in path.split('+'):
        bpy.ops.import_scene.pynifly(filepath=one)
    return [o for o in bpy.data.objects if o.type == 'MESH']


def tex_of(o):
    m = o.data.materials[0] if o.data.materials else None
    if not m:
        return {}
    return {k: m.get(f'BSShaderTextureSet_{v}', '') for k, v in (('d', 'Diffuse'), ('n', 'Normal'), ('s', 'Specular'))}


if MODE == 'list':
    out = {}
    for p in args[2:]:
        for o in load(p):
            out.setdefault(p, {})[o.name] = dict(tex_of(o), shader=o.data.materials[0].get('BSLSP_Shader_Name', '')
                                                 if o.data.materials else '')
    pathlib.Path(args[1]).write_text(json.dumps(out, indent=1))
    print('listed')
    sys.exit(0)

PNG, SHOTS = pathlib.Path(args[1]), pathlib.Path(args[2])
SHOTS.mkdir(parents=True, exist_ok=True)


def png_for(path):
    if not path:
        return None
    q = PNG / (path.lower().replace('\\', '/').removeprefix('textures/').replace('/', '__').removesuffix('.dds')
               + '.png')
    return q if q.exists() else None


def material(o):
    t = tex_of(o)
    name = o.name.lower()
    m = bpy.data.materials.new(o.name + '_r')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    if any(k in name for k in ('flash', 'fx', 'streak')) and not name.startswith('deathclawfx'):   # glow shells
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
        bsdf.inputs['Alpha'].default_value = 0.0
        return m
    d = png_for(t.get('d'))
    bg = ''
    if o.data.materials:
        bg = str(o.data.materials[0].get('BSLSP_Shader_Name', '')).replace('\\', '/').split('/')[-1].lower()
        bg = bg.removesuffix('.bgsm')
    if not d and bg and (PNG / f'bgsm__{bg}_d.png').exists():        # BGSM-only materials (empty texture set)
        d = PNG / f'bgsm__{bg}_d.png'
        if not png_for(t.get('n')) and (PNG / f'bgsm__{bg}_n.png').exists():
            t['n'] = None
            nm_bg = PNG / f'bgsm__{bg}_n.png'
        else:
            nm_bg = None
    else:
        nm_bg = None
    if d:
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(str(d))
        nt.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = (0.5, 0.42, 0.36, 1)
    nm = png_for(t.get('n')) or nm_bg
    if nm:
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(str(nm))
        n.image.colorspace_settings.name = 'Non-Color'
        mapn = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(n.outputs['Color'], mapn.inputs['Color'])
        nt.links.new(mapn.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.6
    return m


def light(name, loc, energy, target):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy, ld.size = energy, 40
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (target - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def shoot(sc, name, target, yaw, pitch, scale, res=(900, 900)):
    cd = bpy.data.cameras.new(name)
    cd.type, cd.ortho_scale, cd.clip_end = 'ORTHO', scale, 3000
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    y, p = math.radians(yaw), math.radians(pitch)
    cam.location = target + Vector((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * 400
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(SHOTS / f'{name}.png')
    bpy.ops.render.render(write_still=True)


for item in args[3:]:
    tag, path, views, *keys = item.split('|')                  # optional 4th: shape keys to set, "Name=1.0;..."
    meshes = load(path)
    exposure = 2.0
    frame_key = None
    focus = ['penis', 'vulva', 'stump']
    for kv in (keys[0].split(';') if keys and keys[0] else []):
        kname, val = kv.split('=')
        if kname == 'EXP':                                    # per-render exposure (dark skins: super mutants)
            exposure = float(val)
            continue
        if kname == 'HIDE':                                   # skip shapes whose name holds any of these (fur
            hide = [s.lower() for s in val.split('+')]        # shells: Blender ignores their vertex alpha)
            for o in meshes:
                if any(h in o.name.lower() for h in hide):
                    o.hide_render = True
            continue
        if kname == 'FOCUS':                                  # frame on shapes whose name holds any of these
            focus = [s.lower() for s in val.split('+')]
            continue
        if kname == 'FRAME':                                  # frame the genital views as if this key were at 1
            frame_key = '>' + val if not val.startswith('>') else val   # (soft/erect pairs share one camera)
            continue
        if kname == 'RAW':                                    # skin space: drop shape node offsets (the game
            for o in meshes:                                  # ignores them on skinned shapes; deathclaw body +11.68 y)
                o.matrix_world = o.matrix_world.Identity(4)
            continue
        for o in meshes:
            sk = o.data.shape_keys
            if sk and kname in sk.key_blocks:
                sk.key_blocks[kname].value = float(val)
                print('shape key', o.name, kname, val)
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.16, 0.17, 1)
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = exposure
    for o in meshes:
        if o.name not in bpy.context.view_layer.objects:
            sc.collection.objects.link(o)
        mat = material(o)
        o.data.materials.clear()
        o.data.materials.append(mat)
        if any(k in o.name.lower() for k in ('flash', 'fx', 'streak', 'meatcap', 'crip', 'bodycap', 'headcap', 'cutpoint')) and not o.name.lower().startswith('deathclawfx'):   # glow shells, dismember caps
            o.hide_render = True
    pts = [o.matrix_world @ Vector(c) for o in meshes if not o.hide_render for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    mid = (lo + hi) / 2
    h = hi.z - lo.z
    tgt = Vector((0, 0, lo.z + h * 0.5))
    light('key', (120, 260, 110), 60000, tgt)
    light('fill', (-220, 160, 60), 20000, tgt)
    light('rim', (0, -250, 140), 30000, tgt)
    light('under', (0, 120, -60), 8000, tgt)
    gz = Vector((mid.x, mid.y + 3, lo.z + h * 0.47))
    pen = [o for o in meshes if any(k in o.name.lower() for k in focus) and not o.hide_render]
    for o in pen:
        print('KEYS', o.name, [k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else None)
    pc, psize = None, None
    if pen:                                                     # centre the genital views on the penis itself
        saved = {}
        if frame_key:
            for o in pen:
                sk = o.data.shape_keys
                if sk and frame_key in sk.key_blocks:
                    saved[o.name] = sk.key_blocks[frame_key].value
                    sk.key_blocks[frame_key].value = 1.0
            bpy.context.view_layer.update()
        pp = [o.matrix_world @ Vector(c) for o in pen for c in o.bound_box]
        for o in pen:
            if o.name in saved:
                o.data.shape_keys.key_blocks[frame_key].value = saved[o.name]
        if saved:
            bpy.context.view_layer.update()
        gz = sum(pp, Vector()) / len(pp) + Vector((0, 0, 3))
        pc = sum(pp, Vector()) / len(pp)
        psize = max(max(p[i] for p in pp) - min(p[i] for p in pp) for i in range(3))
    for v in views.split(','):
        if v == 'front':
            shoot(sc, f'{tag}_front', mid, 0, 0, h * 1.05, (800, 1100))
        elif v == 'back':
            shoot(sc, f'{tag}_back', mid, 180, 0, h * 1.05, (800, 1100))
        elif v == 'crotch':
            shoot(sc, f'{tag}_crotch', gz, 0, -20, h * 0.12)
        elif v == 'gside':
            shoot(sc, f'{tag}_gside', gz, 65, 0, h * 0.12)
        elif v in ('qside', 'qunder', 'qfront', 'qbelow', 'qback') and pc is not None:  # quadrupeds: at the penis
            yaw, pitch = {'qside': (90, -5), 'qunder': (90, -60), 'qfront': (30, -35), 'qbelow': (0.1, -89),
                          'qback': (180, -25)}[v]
            shoot(sc, f'{tag}_{v}', pc, yaw, pitch, psize * 3.2)
        elif v.startswith('pt='):                               # pt=x/y/z/yaw/pitch/scale[/name]: any close-up
            f = v[3:].split('/')
            x_, y_, z_, yaw, pitch, scale = map(float, f[:6])
            shoot(sc, f'{tag}_{f[6] if len(f) > 6 else "pt"}', Vector((x_, y_, z_)), yaw, pitch, scale)
        elif v == 'gfront':
            shoot(sc, f'{tag}_gfront', gz + Vector((0, 0, -3)), 0, 5, h * 0.17)
        elif v == 'gside2':
            shoot(sc, f'{tag}_gside2', gz + Vector((0, 4, -3)), 90, 5, h * 0.20)
        elif v == 'chest':
            shoot(sc, f'{tag}_chest', Vector((mid.x, mid.y, lo.z + h * 0.68)), 20, 0, h * 0.30)
print('renders done')
