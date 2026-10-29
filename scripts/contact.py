import sys
from PIL import Image
files=sys.argv[2:]; out=sys.argv[1]
W=640; ims=[Image.open(f).convert('RGB') for f in files]
ims=[im.resize((W,int(im.height*W/im.width))) for im in ims]
cols=2; H=max(i.height for i in ims); rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(W*cols,H*rows))
for k,im in enumerate(ims): sheet.paste(im,((k%cols)*W,(k//cols)*H))
sheet.save(out,quality=85)
