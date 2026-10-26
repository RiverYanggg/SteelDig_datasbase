from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
ROOT=Path('/Users/mac/Desktop/SteelDig/database');r=ROOT/'07_docs/revision_1025/preview'
d=pymupdf.open(ROOT/'SteelDig_SFT与数据库_优化版_1025.pdf');print('PAGES',len(d))
for i,p in enumerate(d):p.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(r/f'slide_{i+1:02d}.png')
for start in range(0,len(d),12):
 sheet=Image.new('RGB',(1800,4*280),'#e7edf3')
 for i in range(start,min(start+12,len(d))):
  im=Image.open(r/f'slide_{i+1:02d}.png').convert('RGB');im.thumbnail((590,250));x=((i-start)%3)*600;y=((i-start)//3)*280;sheet.paste(im,(x+5,y+5));ImageDraw.Draw(sheet).text((x+12,y+260),str(i+1),fill='black')
 sheet.save(r/f'overview_{start+1:02d}.jpg')
md=pymupdf.open(ROOT/'SteelDig_SFT与数据库_独立讲稿_1025.pdf');print('MANUSCRIPT',len(md))
for i in [0,len(md)-1]:md[i].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False).save(r/f'notes_{i+1:02d}.png')
