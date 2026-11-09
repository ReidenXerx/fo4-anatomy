"""Blender: re-import a nif and print each shape's vertex groups with vertex counts.
    blender -b -P nick_reimport.py -- <nif>"""
import sys

import addon_utils
import bpy

src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_nifly', default_set=True)
bpy.ops.import_scene.pynifly(filepath=src, rename_bones=False)
for o in bpy.data.objects:
    if o.type == 'MESH' and 'Penis' in o.name:
        cnt = {g.name: 0 for g in o.vertex_groups}
        for v in o.data.vertices:
            for e in v.groups:
                if e.weight > 0:
                    cnt[o.vertex_groups[e.group].name] += 1
        print('REIMPORT', o.name, len(o.data.vertices), cnt)
