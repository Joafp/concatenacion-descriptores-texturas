"""Render the final thesis and contact sheets for visual inspection."""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'paper/tesis.pdf'
output=ROOT/'output/pdf/accuracy_primary_20261115_qa'
output.mkdir(parents=True,exist_ok=False)
subprocess.run(['pdftoppm','-r','55','-png',str(pdf),str(output/'page')],check=True)
text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
pages=text.split('\f')
if not pages[-1].strip():
    pages.pop()
images=sorted(output.glob('page-*.png'))
assert len(images)==len(pages)
sheets=[]
for start in range(0,len(images),12):
    sheet=Image.new('RGB',(750,1440),'#d3d8dd')
    draw=ImageDraw.Draw(sheet)
    for offset,path in enumerate(images[start:start+12]):
        im=Image.open(path).convert('RGB')
        im.thumbnail((240,333))
        x,y=(offset%3)*250+5,(offset//3)*360+22
        sheet.paste(im,(x,y))
        draw.text((x,y-17),f'Página {start+offset+1}',fill='black')
    path=output/f'contact_{start//12+1:02d}.png'
    sheet.save(path)
    sheets.append(str(path))
critical=[]
for i,page in enumerate(pages,1):
    if i>10 and any(term in page for term in ['E1 nuevo:', 'E2: umbrales', 'Accuracy de Top-4/SVM', 'Ganancia de cada bloque', 'Métricas y costos']):
        critical.append(i)
report={'pages':len(pages),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'contact_sheets':sheets,'critical_pages':critical,'replacement_characters':text.count('\ufffd'),
        'visual_review_status':'pending_human_or_agent_inspection',
        'tex_log_has_overfull': 'Overfull' in (ROOT/'paper/tesis.log').read_text(),
        'tex_log_has_undefined': 'undefined' in (ROOT/'paper/tesis.log').read_text()}
(output/'qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
