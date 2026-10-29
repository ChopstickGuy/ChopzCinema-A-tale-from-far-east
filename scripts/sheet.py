"""Preview sheet: each texture tiled 2x2, scaled 6x; tinted ones get sample tints."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P = Path(sys.argv[1]); out = sys.argv[2]
B = P/'assets/minecraft/textures/block'
cm = np.array(Image.open(P/'assets/minecraft/textures/colormap/grass.png').convert('RGB')).astype(float)
fm = np.array(Image.open(P/'assets/minecraft/textures/colormap/foliage.png').convert('RGB')).astype(float)
pts = {'plains':(51,173),'forest':(76,112),'birch':(102,163),'meadow':(127,153),'taiga':(185,204),'jungle':(12,37)}
items = []
for n,tm in [('grass_block_top','g'),('grass','g'),('tall_grass_top','g'),('oak_leaves','f')]:
    for b,(x,y) in pts.items(): items.append((n,tm,cm[y,x] if tm=='g' else fm[y,x],b))
for n in sys.argv[3:]: items.append((n,None,None,''))
S=6; T=16*2*S; cols=6
rows=(len(items)+cols-1)//cols
sheet=Image.new('RGB',(cols*(T+10),rows*(T+24)),(40,40,44)); d=ImageDraw.Draw(sheet)
for k,(n,tm,tint,lab) in enumerate(items):
    a=np.array(Image.open(B/f'{n}.png').convert('RGBA')).astype(float)[:16]
    if tint is not None: a[...,:3]*=tint/255
    bg=np.full((16,16,3),(120,150,190.)); m=a[...,3:4]/255
    rgb=a[...,:3]*m+bg*(1-m)
    t=np.tile(rgb,(2,2,1)); im=Image.fromarray(t.astype(np.uint8)).resize((T,T),Image.NEAREST)
    x=(k%cols)*(T+10)+5; y=(k//cols)*(T+24)+5
    sheet.paste(im,(x,y)); d.text((x,y+T+3),f'{n} {lab}'[:30],fill=(230,230,230))
sheet.save(out)
