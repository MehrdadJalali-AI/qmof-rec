from pathlib import Path
import subprocess
from PIL import Image,ImageDraw
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
man=Path('/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec/manuscript')
out=root/'artifacts/reviewer_revision/pdf_qa';out.mkdir(parents=True,exist_ok=True)
for name in ['main','supplementary_material','response_to_reviewers']:
    r=PdfReader(man/(name+'.pdf'))
    assert all('??' not in page.extract_text() for page in r.pages)
    prefix=out/name
    subprocess.run(['/Users/mehrdadjalali/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm','-r','80','-png',str(man/(name+'.pdf')),str(prefix)],check=True,stdout=subprocess.DEVNULL)
    pages=sorted(out.glob(name+'-[0-9]*.png'))[:len(r.pages)]
    for start in range(0,len(pages),9):
        sheet=Image.new('RGB',(900,1314),'#d9dfe3');draw=ImageDraw.Draw(sheet)
        for j,page in enumerate(pages[start:start+9]):
            im=Image.open(page).convert('RGB');im.thumbnail((286,405));x=(j%3)*300+7;y=(j//3)*438+22
            sheet.paste(im,(x,y));draw.text((x,y-17),f'{name} page {start+j+1}',fill='black')
        sheet.save(out/f'{name}_contact_{start//9+1}.png')
    print(name,len(pages),'pages rendered')
