from PIL import Image, ImageDraw
import pypdfium2 as pdfium
from src.ingestion.acquire import ROOT

images=[]
for path in sorted((ROOT/'excel/previews').glob('*.pdf')):
    document=pdfium.PdfDocument(path)
    image=document[0].render(scale=1.4).to_pil().convert('RGB')
    image.save(path.with_suffix('.png'))
    thumb=image.copy()
    thumb.thumbnail((600,425))
    panel=Image.new('RGB',(640,470),'#EDF2F5')
    panel.paste(thumb,((640-thumb.width)//2,30))
    ImageDraw.Draw(panel).text((20,445),path.stem,fill='#123047')
    images.append(panel)
    document.close()
if not images:
    raise RuntimeError('No native Excel PDF exports to inspect')
contact=Image.new('RGB',(1280,470*((len(images)+1)//2)),'white')
for i,im in enumerate(images):
    contact.paste(im,((i%2)*640,(i//2)*470))
contact.save(ROOT/'excel/previews/contact_sheet.png')
print('Rendered',len(images),'native Excel worksheet previews')
