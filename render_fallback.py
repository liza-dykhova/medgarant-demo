"""Offline video render from original Figma PDF while browser capture is unavailable."""
from PIL import Image,ImageDraw,ImageFilter
import fitz,subprocess,math
from pathlib import Path
root=Path(__file__).parent
p=fitz.open('/mnt/data/animation.pdf')[0]
base=Image.frombytes('RGB',[int(p.rect.width),int(p.rect.height)],p.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).samples).convert('RGB')
a=fitz.open('/mnt/data/About Section.pdf')[0]
about=Image.frombytes('RGB',[int(a.rect.width),int(a.rect.height)],a.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).samples).convert('RGB')
W,H=1440,810;FPS=20;DUR=26
# Large crop of final About section is used in a morph transition.
about_content=about.crop((0,0,1440,930))
def smooth(v):
 v=max(0,min(1,v));return v*v*(3-2*v)
def lerp(a,b,t):return a+(b-a)*t
def rectfade(img,rect,alpha,from_y=30):
 global canvas
 part=img.crop(rect).convert('RGBA');mask=Image.new('L',part.size,round(255*alpha));part.putalpha(mask)
 canvas.paste(part,(rect[0],round(rect[1]+from_y*(1-alpha))),part)
def compose(t):
 global canvas
 if t<4:scroll=0
 elif t<9:scroll=lerp(350,1130,smooth((t-4)/5))
 elif t<13:scroll=lerp(1130,2050,smooth((t-9)/4))
 elif t<17:scroll=lerp(2050,3320,smooth((t-13)/4))
 elif t<20.5:scroll=lerp(3320,4320,smooth((t-17)/3.5))
 elif t<24:scroll=lerp(4320,5090,smooth((t-20.5)/3.5))
 else:scroll=lerp(5090,5070,smooth((t-24)/2))
 y=int(max(0,min(5880-H,scroll)));canvas=base.crop((0,y,W,y+H)).convert('RGB')
 if t<4:
  # Gradually reveal original interface in the intended order, keeping photography static.
  fade=[((0,0,1440,102),smooth((t-.1)/.7)),((30,540,1000,704),smooth((t-.75)/.85)),((30,690,1010,789),smooth((t-1.4)/.7)),((35,775,900,860),smooth((t-1.95)/.7)),((1010,625,1420,880),smooth((t-2.65)/.8))]
  source=canvas.copy()
  # hide overlay first by applying smooth local blur; reference background remains stable
  for (x0,y0,x1,y1),alpha in fade:
   x1=min(x1,W);y1=min(y1,H)
   region=source.crop((x0,y0,x1,y1));bg=region.filter(ImageFilter.GaussianBlur(radius=22))
   canvas.paste(Image.blend(bg,region,alpha),(x0,y0))
 elif 4<=t<11:
  # Transition from wide image to the approved statistics layout via a horizontal reveal.
  u=smooth((t-5.7)/4.2)
  if u>0:
   sy=1000-y
   if sy<810 and sy+930>0:
    for viewport_y in range(max(0,int(sy)),min(H,int(sy+930))):
     src_y=viewport_y-int(sy)
     # A soft horizontal wipe of the final About state avoids ghosting text.
     reveal_x=int(W*u)
     feather=35
     if reveal_x<=0:continue
     strip=about_content.crop((0,src_y,min(W,reveal_x),src_y+1))
     canvas.paste(strip,(0,viewport_y))
     if reveal_x<W:
      end=min(W,reveal_x+feather)
      src=about_content.crop((reveal_x,src_y,end,src_y+1))
      old=canvas.crop((reveal_x,viewport_y,end,viewport_y+1))
      m=Image.new('L',(end-reveal_x,1));m.putdata([round(255*(1-i/max(1,feather))) for i in range(end-reveal_x)])
      canvas.paste(src,(reveal_x,viewport_y),m)
 elif 11<=t<13:
  # Turquoise tint moves across the values headline like a horizontal color reveal.
  u=smooth((t-11)/2)
  top=max(0,2090-y);bot=min(810,2270-y)
  if bot>top:
   mask=Image.new('RGBA',(int(1100*u),int(bot-top)),(0,170,187,28))
   canvas.paste(mask,(170,int(top)),mask)
 elif 14.8<=t<=16.35:
  # Gradient service-card hover approximation on the same card location.
  u=min(smooth((t-14.8)/.4),smooth((16.35-t)/.4));rect=(483,3113-y,960,3422-y)
  x0,yy0,x1,yy1=rect
  if 0<=yy0<810:
   x1=min(x1,W);yy1=min(yy1,810);reg=canvas.crop((x0,max(yy0,0),x1,yy1));tint=Image.new('RGB',reg.size,(0,133,161));canvas.paste(Image.blend(reg,tint,.42*u),(x0,max(yy0,0)))
 elif 17<=t<20.5:
  # Soft tooth/photo appearance simulated with increasing opacity at the original mask position.
  u=smooth((t-18)/1.5)
  rect=(775,max(0,4090-y),1410,min(810,4610-y));x0,yy0,x1,yy1=rect
  if yy1>yy0:
   r=canvas.crop(rect);blur=r.filter(ImageFilter.GaussianBlur(15));canvas.paste(Image.blend(blur,r,u),(x0,yy0))
 elif 22.5<=t<24:
  # Horizontal carousel offset within review track.
  u=smooth((t-22.5)/1.2);rr=(0,max(0,4940-y),1440,min(810,5365-y));
  if rr[3]>rr[1]:
   region=canvas.crop(rr);dx=int(-85*u); shifted=Image.new('RGB',region.size,(246,247,248));shifted.paste(region,(dx,0));canvas.paste(shifted,(rr[0],rr[1]))
 return canvas
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=1920:1080:flags=bicubic,format=yuv420p','-c:v','libx264','-preset','ultrafast','-crf','21','-movflags','+faststart',str(root/'medgarant-homepage-animation.mp4')]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(FPS*DUR):
 frame=compose(i/FPS);p.stdin.write(frame.tobytes())
 if i in (70,158,235,300,390,460):frame.save(root/f'preview_{i}.jpg',quality=83)
 if i%100==0:print('frame',i,flush=True)
p.stdin.close();rc=p.wait();print('video completed',rc)
