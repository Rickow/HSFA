import struct, sys, collections
def regs(t):
    r=open('dump/%s.regs'%t,'rb').read(); return struct.unpack('>%dH'%(len(r)//2),r)
def vram(t): return open('dump/%s.vram'%t,'rb').read()
def scan(plane,col,row):
    if plane==1: return (row&0x1f)+((col&0x3f)<<5)+((row&0x20)<<6)
    if plane==2: return (row&0x0f)+((col&0x3f)<<4)+((row&0x30)<<6)
    return (row&0x07)+((col&0x3f)<<3)+((row&0x38)<<6)
def visible(t,plane):
    w=regs(t); v=vram(t)
    base=(w[plane]&0xffc0)<<8; off=base-0x900000
    sx=w[4+2*plane]; sy=w[5+2*plane]; ts={1:8,2:16,3:32}[plane]
    out={}
    for y in range(0,224,ts//2 if ts>8 else 8):
        for x in range(0,384,ts//2 if ts>8 else 8):
            tx=(x+64+sx)&(64*ts-1); ty=(y+16+sy)&(64*ts-1)
            c,r=tx//ts,ty//ts; i=scan(plane,c,r)
            code,attr=struct.unpack('>HH',v[off+4*i:off+4*i+4])
            out[(c,r)]=(code,attr,x,y)
    return out
if __name__=='__main__':
    t=sys.argv[1]; pl=int(sys.argv[2])
    o=visible(t,pl)
    for (c,r),(code,attr,x,y) in sorted(o.items(),key=lambda a:(a[0][1],a[0][0])):
        print('col %2d row %2d  ecran~(%3d,%3d) code %04x attr %04x pal %02x' % (c,r,x,y,code,attr,attr&0x1f))
