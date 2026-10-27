import sys
from PIL import Image
# planche.py sortie.png ligne1_img1,img2,... ligne2_...   (une ligne par argument)
rows=[a.split(',') for a in sys.argv[2:]]
ims=[[Image.open(f).convert('RGB') for f in r] for r in rows]
w=max(sum(i.width for i in r) for r in ims); h=sum(max(i.height for i in r) for r in ims)
P=Image.new('RGB',(w+4*max(len(r) for r in ims),h+4*len(ims)),(60,60,60)); y=0
for r in ims:
    x=0
    for i in r: P.paste(i,(x,y)); x+=i.width+4
    y+=max(i.height for i in r)+4
P.save(sys.argv[1])
