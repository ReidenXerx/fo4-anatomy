"""Blender: import a nif (nif bone names) and print the penis bones: parent, head, tail, matrix scale.
    blender -b -P nick_bones.py -- <nif>"""
import sys

import addon_utils
import bpy

src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
for a in bpy.data.objects:
    if a.type != 'ARMATURE':
        continue
    print('ARM', a.name, len(a.data.bones))
    for b in a.data.bones:
        if 'Penis' in b.name or b.name in ('Pelvis_skin', 'Pelvis', 'COM'):
            print('BONE', b.name, 'parent', b.parent.name if b.parent else None, 'head', tuple(round(x, 2) for x in b.head_local),
                  'tail', tuple(round(x, 2) for x in b.tail_local), 'scale', tuple(round(x, 3) for x in b.matrix_local.to_scale()),
                  'deform', b.use_deform, {k: str(b[k])[:60] for k in b.keys()})
