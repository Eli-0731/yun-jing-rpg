"""Style guide §6: the in-game (Unity) shot beside the direction image it has to sit in.
python compose_direction.py <unity shot> <direction image> <out>"""
import sys
from PIL import Image
a,b=(Image.open(p).convert('RGB') for p in sys.argv[1:3]);H=720
a,b=(im.resize((int(im.width*H/im.height),H)) for im in (a,b))
c=Image.new('RGB',(a.width+b.width+12,H),(30,30,30));c.paste(a,(0,0));c.paste(b,(a.width+12,0));c.save(sys.argv[3]);print('DIRECTION_SHEET',sys.argv[3])
