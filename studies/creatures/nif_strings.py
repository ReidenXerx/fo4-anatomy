"""python -I nif_strings.py <nif>... : path-like strings (materials, textures, tri)"""
import re
import sys

for p in sys.argv[1:]:
    b = open(p, 'rb').read()
    print(p, len(b))
    for x in sorted(set(x.decode() for x in re.findall(rb'[ -~]{6,}', b))):
        if '\\' in x or '/' in x or x.lower().endswith(('.bgsm', '.dds', '.tri', '.bgem')):
            print('   ', x)
