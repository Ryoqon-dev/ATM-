"""Document QA only. Does not execute or claim to test the ATM product."""
from pathlib import Path
from zipfile import ZipFile
import json, re, hashlib
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import pymupdf as fitz
from hwpx import HwpxDocument
from project_content import ROOT, pages, classes, requirements, quality, tests

WORK=ROOT/'.artifacts'/'analysis';OUT=WORK/'PDF검토';OUT.mkdir(parents=True,exist_ok=True)
HWPX=ROOT/'docs'/'design'/'최종_SW공학_상세설계서_박교범_2023243047.hwpx'
PDF=ROOT/'docs'/'design'/'ATM_상세설계서_최종보완_검토용.pdf'
checks={}
def check(name,value):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)

with ZipFile(HWPX) as z:
    check('zip_integrity',z.testzip() is None)
    check('mimetype_first_uncompressed',z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==0)
    check('hwpx_mimetype',z.read('mimetype').strip()==b'application/hwp+zip')
    names=[n for n in z.namelist() if n.startswith('Contents/section') and n.endswith('.xml')]
    check('section_count',len(names)==len(pages))
    for n in [n for n in z.namelist() if n.endswith(('.xml','.hpf'))]: ET.fromstring(z.read(n))
    check('xml_well_formed',True)
    text='\n'.join(''.join(ET.fromstring(z.read(n)).itertext()) for n in names)
    for c in classes:
        check('all_methods_'+c['name'],all(m['ko'] in text and m['id'] in text for m in c['ops']))
    for a,*_ in requirements+quality:check(a,a in text)
    check('unrelated_template_removed','NoteMaestro 클라이언트는' not in text and '미디파일을 불러와' not in text)
    check('no_replacement_glyph','\ufffd' not in text)
    refs=ET.fromstring(z.read('Contents/header.xml'))
    cp={n.attrib['id'] for n in refs.findall('.//{http://www.hancom.co.kr/hwpml/2011/head}charPr')}
    pp={n.attrib['id'] for n in refs.findall('.//{http://www.hancom.co.kr/hwpml/2011/head}paraPr')}
    for name in names:
        for n in ET.fromstring(z.read(name)).iter():
            if 'charPrIDRef' in n.attrib:check('char_refs_'+name,n.attrib['charPrIDRef'] in cp)
            if 'paraPrIDRef' in n.attrib:check('para_refs_'+name,n.attrib['paraPrIDRef'] in pp)
    check('picture_count',len([n for n in z.namelist() if n.startswith('BinData/')])==8)
check('hwpx_schema_validation',HwpxDocument.open(HWPX).validate().ok)

seed=json.loads((ROOT/'docs/development/data/accounts.seed.json').read_text(encoding='utf-8'))
check('seed_unique',len({a['accountNumber'] for a in seed['accounts']})==len(seed['accounts']))
check('seed_domain_invariants',all(re.fullmatch('[0-9]{12}',a['accountNumber']) and re.fullmatch('[0-9]{4}',a['password']) and type(a['balance']) is int and 0<=a['balance']<=9999999999 and type(a['failedCount']) is int and 0<=a['failedCount']<=5 and a['blocked']==(a['failedCount']==5) for a in seed['accounts']))
tc=json.loads((ROOT/'docs/development/test_cases.json').read_text(encoding='utf-8'))
check('test_case_count',len(tc)==37 and len({r['id'] for r in tc})==37)
check('product_test_status_not_run',all(r['status']=='NOT_RUN' for r in tc))
ops=[m['id'] for c in classes for m in c['ops']]
check('44_unique_operations',len(ops)==44 and len(set(ops))==44)
check('class_uml_methods_consistent',all(m['ko']+'('+m['params']+')' in (ROOT/'docs/diagrams/최종보완/class_full.puml').read_text(encoding='utf-8') for c in classes for m in c['ops']))

pdf=fitz.open(PDF)
check('pdf_page_count',len(pdf)==len(pages))
alltext='\n'.join(p.get_text() for p in pdf)
check('pdf_text_readable','가상 계좌' in alltext and 'REQ-LOGIN-01' in alltext)
check('pdf_no_replacement_glyph','\ufffd' not in alltext)
for i,p in enumerate(pdf):
    p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(OUT/f'page_{i+1:02}.png'))
    # Text must stay on the physical page. This does not replace visual inspection.
    for b in p.get_text('blocks'):
        check('pdf_text_bounds_'+str(i+1),b[0]>=0 and b[1]>=0 and b[2]<=p.rect.width+1 and b[3]<=p.rect.height+1)
for start in range(0,len(pdf),12):
    sheet=Image.new('RGB',(1350,2560),'#DCE3EB');dr=ImageDraw.Draw(sheet)
    for ix in range(start,min(start+12,len(pdf))):
        im=Image.open(OUT/f'page_{ix+1:02}.png');im.thumbnail((425,600))
        col=(ix-start)%3;row=(ix-start)//3
        sheet.paste(im,(col*450+(450-im.width)//2,row*640+30))
        dr.text((col*450+15,row*640+4),str(ix+1),fill='black',font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20))
    sheet.save(OUT/f'contact_{start+1:02}.jpg')

files=[HWPX,PDF]+list((ROOT/'docs'/'development').rglob('*'))+list((ROOT/'docs/diagrams/최종보완').glob('*'))
manifest=[dict(path=str(f.relative_to(ROOT)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files if f.is_file()]
(WORK/'산출물_해시목록.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'검증결과.json').write_text(json.dumps(dict(checks=checks,passed=len(checks),pdf_pages=len(pdf),operations=len(ops),test_cases=len(tc),product_tests='NOT_RUN',native_hancom_open='NOT_VERIFIED'),ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(checks)} document checks passed; {len(pdf)} PDF pages rendered; product tests NOT_RUN; native Hancom layout NOT_VERIFIED')
