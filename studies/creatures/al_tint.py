"""Immersive Aliens v3 (kassarawi 11-13: "make the penis similar to the skin colour of the alien but ever so slightly
darker"): her TentaTussy texture retinted to the Zetan's skin. Her texture's light/dark detail (luminance, normalised)
multiplies the alien skin's mean colour x DARKER; 30 % of the alien's spotted forehead skin (tiled in her UV space)
is blended in so it reads as the same skin.
    python -I al_tint.py <her basecolor png> <alien_01_d png> <out png> [darker]"""
import sys

import numpy as np
from PIL import Image

src, alien, out = sys.argv[1:4]
DARKER = float(sys.argv[4]) if len(sys.argv) > 4 else 0.88
N = 2048
her = np.asarray(Image.open(src).convert('RGB').resize((N, N), Image.LANCZOS)).astype(float)
A = np.asarray(Image.open(alien).convert('RGB')).astype(float)
H, W = A.shape[:2]
crop = A[int(0.02 * H):int(0.14 * H), int(0.05 * W):int(0.30 * W)]
skin = crop.reshape(-1, 3).mean(0)
lum = her @ np.array([0.299, 0.587, 0.114])
detail = lum / max(np.median(lum), 1.0)
detail = 1.0 + (np.clip(detail, 0.4, 1.6) - 1.0) * 0.6          # keep her shading, softened
detail = np.minimum(detail, 1.0)                                  # nothing lighter than the darker skin (her sac is white)
tile = np.asarray(Image.fromarray(crop.astype(np.uint8)).resize((N // 6 + 1, N // 12 + 1))).astype(float)
tiled = np.tile(tile, (13, 7, 1))[:N, :N]
col = (0.7 * skin + 0.3 * tiled) * DARKER * detail[..., None]
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(out)
print('skin mean', skin.round(1), '-> tint x', DARKER, out)
