"""Preview of item textures (8x) and armour layers (4x) from a built pack."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(sys.argv[1]); out = sys.argv[2]
I = P / 'assets/minecraft/textures/item'
tiers = ['wooden', 'stone', 'iron', 'golden', 'diamond', 'netherite']
rows = [[f'{t}_{k}' for k in ('sword', 'pickaxe', 'axe', 'shovel', 'hoe')] for t in tiers]
rows += [[f'{p}_{k}' for k in ('helmet', 'chestplate', 'leggings', 'boots')] for p in ('iron', 'golden', 'diamond', 'netherite', 'chainmail')]
S = 8
sheet = Image.new('RGB', (5 * 16 * S + 4 * 64 * 4 + 40, max(len(rows) * 16 * S, 10 * 32 * 4 + 40)), (150, 160, 175))
for r, row in enumerate(rows):
    for c, n in enumerate(row):
        im = Image.open(I / f'{n}.png').convert('RGBA').resize((16 * S, 16 * S), Image.NEAREST)
        sheet.paste(im, (c * 16 * S, r * 16 * S), im)
A = P / 'assets/minecraft/textures/models/armor'
for k, m in enumerate(('iron', 'gold', 'diamond', 'netherite', 'chainmail')):
    for l in (1, 2):
        im = Image.open(A / f'{m}_layer_{l}.png').convert('RGBA').resize((256, 128), Image.NEAREST)
        sheet.paste(im, (5 * 16 * S + 20 + (l - 1) * 264, 10 + k * 136), im)
sheet.save(out)
