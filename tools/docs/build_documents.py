"""Shared-content HWPX authoring and independent review-PDF typesetting."""
from pathlib import Path
from copy import deepcopy
import json, shutil, hashlib, math, html, warnings
from zipfile import ZipFile
import pymupdf as fitz
from PIL import Image
from lxml import etree
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle
from hwpx import HwpxDocument
from project_content import ROOT, pages, write_content

warnings.filterwarnings('ignore',category=DeprecationWarning)
PDFDIR=ROOT/'docs'/'design';PDFDIR.mkdir(parents=True,exist_ok=True)
WORK=ROOT/'.artifacts'/'analysis';WORK.mkdir(parents=True,exist_ok=True)
BACKUP=ROOT/'.artifacts'/'originals';BACKUP.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'docs'/'design'/'최종_SW공학_상세설계서_박교범_2023243047.hwpx'
PDF=PDFDIR/'ATM_상세설계서_최종보완_검토용.pdf'
DIAGRAM=ROOT/'docs'/'diagrams'/'최종보완'
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HU=7200/25.4
def hu(mm_value):return round(mm_value*HU)

pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('Malgun',normal='Malgun',bold='MalgunBold',italic='Malgun',boldItalic='MalgunBold')
INK=HexColor('#172E4D');BLUE=HexColor('#2261A5');PALE=HexColor('#EDF4FB');GRAY=HexColor('#65758A')

def styles(scale=1):
    return {
      'p':ParagraphStyle('body',fontName='Malgun',fontSize=10*scale,leading=16*scale,textColor=INK,wordWrap='CJK',spaceAfter=8*scale),
      'h':ParagraphStyle('sub',fontName='MalgunBold',fontSize=10.6*scale,leading=15.2*scale,textColor=BLUE,wordWrap='CJK',spaceBefore=7*scale,spaceAfter=3*scale),
      'caption':ParagraphStyle('caption',fontName='Malgun',fontSize=8.5*scale,leading=12*scale,textColor=GRAY,alignment=1,wordWrap='CJK',spaceAfter=8*scale),
      'cell':ParagraphStyle('cell',fontName='Malgun',fontSize=8.8*scale,leading=13*scale,textColor=INK,wordWrap='CJK'),
      'headcell':ParagraphStyle('headcell',fontName='MalgunBold',fontSize=9*scale,leading=13*scale,textColor=INK,wordWrap='CJK'),
    }
def safe(t):return html.escape(t).replace('\n','<br/>')
def measure(pg,scale=1):
    st=styles(scale);W=(420 if pg['landscape'] else 210)*mm;H=297*mm
    width=W-36*mm;items=[];total=0
    for b in pg['blocks']:
        kind=b['kind']
        if kind in ('p','h'):
            para=Paragraph(safe(b['text']),st[kind]);pw,ph=para.wrap(width,10000)
            before=st[kind].spaceBefore;after=st[kind].spaceAfter;items.append((kind,b,para,ph,before,after));total+=ph+before+after
        elif kind=='table':
            ratios=b.get('widths') or [1]*len(b['headers']);ws=[width*v/sum(ratios) for v in ratios]
            data=[[Paragraph(safe(str(v)),st['headcell' if ri==0 else 'cell']) for v in row] for ri,row in enumerate([b['headers']]+b['rows'])]
            t=Table(data,colWidths=ws,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),PALE),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#F7F9FC')]),('GRID',(0,0),(-1,-1),.35,HexColor('#B4C3D3')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            tw,th=t.wrap(width,10000);items.append((kind,b,t,th,4,10));total+=th+14
        elif kind=='figure':
            f=DIAGRAM/(b['name']+'.png');im=Image.open(f);ratio=min(width/im.width,b['max_height']*mm/im.height)
            iw,ih=im.width*ratio,im.height*ratio
            cap=Paragraph(safe(b['caption']),st['caption']);cw,ch=cap.wrap(width,10000)
            items.append((kind,b,(f,iw,ih,cap,ch),ih+6+ch,3,8));total+=ih+ch+17
    return items,total,W,H,width

def compose_pdf():
    c=canvas.Canvas(str(PDF));c.setTitle('ATM 제어 및 관리 시스템 상세설계서 - 11/16 피드백 반영');c.setAuthor('박교범 2023243047')
    layouts=[];notes=[]
    for index,pg in enumerate(pages,1):
        scale=1
        while True:
            items,total,W,H,width=measure(pg,scale)
            available=H-55*mm
            if total<=available or scale<=.83:break
            scale-=.025
        if total>available:raise RuntimeError(f'Page {index} overflows: {total:.1f} > {available:.1f}')
        c.setPageSize((W,H))
        if index==1:
            c.setFillColor(INK);c.rect(0,H-98*mm,W,98*mm,fill=1,stroke=0)
            c.setFillColor(white);c.setFont('MalgunBold',13);c.drawString(23*mm,H-28*mm,'2026년 2학기 SW공학')
            c.setFont('MalgunBold',25);c.drawString(23*mm,H-49*mm,'소프트웨어공학')
            c.drawString(23*mm,H-64*mm,'상세설계서')
            c.setFont('Malgun',11);c.drawString(23*mm,H-82*mm,'ATM 제어 및 관리 시스템 개발')
            c.setFillColor(INK);c.setFont('MalgunBold',15);c.drawString(23*mm,H-130*mm,'11월 16일 교수님 피드백 반영')
            c.setFont('Malgun',12);c.drawString(23*mm,H-143*mm,'최종 보완본 · 통합 버전 v3.0.0')
            for j,t in enumerate(['컴퓨터공학부','2023243047 박교범','2026. 11. 18.']):c.drawString(23*mm,H-(178+j*13)*mm,t)
            pp=Paragraph('요구사항 → 기능 프로세스 → 유즈케이스 → 메소드 → UML → 검증의 연결을 기준으로 작성하였다.',styles()['p']);pp.wrap(width,200);pp.drawOn(c,23*mm,44*mm)
            layouts.append(dict(page=index,scale=1,content_height=0,bottom_mm=44));c.showPage();continue
        c.setStrokeColor(BLUE);c.setLineWidth(1);c.line(18*mm,H-14*mm,W-18*mm,H-14*mm)
        c.setFont('Malgun',8);c.setFillColor(GRAY);c.drawString(18*mm,H-10.5*mm,'ATM 제어 및 관리 시스템 | 상세설계 v3.0.0')
        title=Paragraph(safe(pg['title']),ParagraphStyle('title',fontName='MalgunBold',fontSize=15,leading=21,textColor=INK,wordWrap='CJK'))
        _,th=title.wrap(width,200);y=H-22*mm-th;title.drawOn(c,18*mm,y);y-=11
        # available accounts for typical one-line heading; catch unusually long headings.
        for kind,b,obj,height,before,after in items:
            y-=before+height
            if kind in ('p','h','table'):obj.drawOn(c,18*mm,y)
            else:
                f,iw,ih,cap,ch=obj
                c.drawImage(str(f),(W-iw)/2,y+ch+6,iw,ih)
                cap.drawOn(c,18*mm,y)
            y-=after
        if y<17*mm:raise RuntimeError(f'Page {index} bottom too low: {y/mm:.2f}mm')
        c.setFont('Malgun',8);c.setFillColor(GRAY);c.drawString(18*mm,10*mm,'박교범 · 2023243047 · 2026-11-18');c.drawRightString(W-18*mm,10*mm,f'{index} / {len(pages)}')
        layouts.append(dict(page=index,scale=round(scale,3),content_height=round(total,1),bottom_mm=round(y/mm,1)))
        c.showPage()
    c.save();(WORK/'PDF_배치검사.json').write_text(json.dumps(layouts,indent=2),encoding='utf-8')
    return layouts

def compose_hwpx(layouts):
    if TARGET.exists() and TARGET.read_bytes().startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        dest=BACKUP/(TARGET.stem+'_20261113_원본.hwp')
        if not dest.exists():shutil.copy2(TARGET,dest)
    d=HwpxDocument.new();head=d.parts.headers[0]
    char={name:d.ensure_run_style(font='맑은 고딕',size=size,bold=bold,color=color) for name,size,bold,color in [
      ('body',9.5,False,'#172E4D'),('h',10.1,True,'#2261A5'),('title',14,True,'#172E4D'),('cell',8.4,False,'#172E4D'),('headcell',8.5,True,'#172E4D'),('caption',8,False,'#65758A'),('small',7.5,False,'#65758A'),('cover',24,True,'#172E4D')]}
    para={
      'body':head.ensure_paragraph_format(alignment='JUSTIFY',line_spacing_percent=140,margins={'prev':0,'next':500}),
      'h':head.ensure_paragraph_format(alignment='LEFT',line_spacing_percent=130,margins={'prev':400,'next':180}),
      'title':head.ensure_paragraph_format(alignment='LEFT',line_spacing_percent=130,margins={'prev':0,'next':850}),
      'cell':head.ensure_paragraph_format(alignment='LEFT',line_spacing_percent=125,margins={'prev':0,'next':0}),
      'caption':head.ensure_paragraph_format(alignment='CENTER',line_spacing_percent=130,margins={'prev':150,'next':500}),
    }
    def add(text,s,kind='body',first=False):
        if first:
            pp=s.paragraphs[0];pp.set_text_preserving_runs(text);pp.para_pr_id_ref=para[kind];
            for run in pp.runs:run.char_pr_id_ref=char[kind]
        else:pp=d.add_paragraph(text,section=s,char_pr_id_ref=char[kind],para_pr_id_ref=para[kind])
        return pp
    for index,pg in enumerate(pages,1):
        s=d.sections[0] if index==1 else d.add_section()
        s.properties.set_page_size(width=hu(297 if pg['landscape'] else 210),height=hu(420 if pg['landscape'] else 297),orientation='LANDSCAPE' if pg['landscape'] else 'PORTRAIT')
        s.properties.set_page_margins(left=hu(18),right=hu(18),top=hu(18),bottom=hu(16),header=hu(7),footer=hu(7),gutter=0)
        if index>1:
            hf=s.properties.set_header_text('ATM 제어 및 관리 시스템 | 상세설계 v3.0.0')
            for pp in hf.paragraphs:
                for rr in pp.runs:rr.char_pr_id_ref=char['small']
        ff=s.properties.set_footer_text(f'박교범 · 2023243047 · 2026-11-18                                      {index} / {len(pages)}')
        for pp in ff.paragraphs:
            for rr in pp.runs:rr.char_pr_id_ref=char['small']
        add('소프트웨어공학 상세설계서' if index==1 else pg['title'],s,'title',True)
        widthmm=384 if pg['landscape'] else 174
        for b in pg['blocks']:
            kind=b['kind']
            if kind in ('p','h'):add(b['text'],s,'body' if kind=='p' else 'h')
            elif kind=='figure':
                path=DIAGRAM/(b['name']+'.png');im=Image.open(path);scale=min(widthmm/im.width,b['max_height']/im.height)
                d.add_picture(path.read_bytes(),'png',section=s,width_mm=im.width*scale,height_mm=im.height*scale,align='CENTER')
                add(b['caption'],s,'caption')
            elif kind=='table':
                rows=[b['headers']]+b['rows'];ratios=b.get('widths') or [1]*len(b['headers'])
                t=d.add_table(len(rows),len(rows[0]),section=s,width=hu(widthmm),height=hu(8*len(rows)),char_pr_id_ref=char['cell'],para_pr_id_ref=para['cell'])
                t.set_column_widths(ratios);t.set_treat_as_char(True)
                # Match independently measured wrapping; smaller native font provides some reflow margin.
                measured=next(x for x in measure(pg,layouts[index-1]['scale'])[0] if x[0]=='table' and x[1] is b)[2]
                for ri,row in enumerate(rows):
                    for ci,value in enumerate(row):
                        t.set_cell_text(ri,ci,str(value));cell=t.cell(ri,ci);cell.set_size(height=round(measured._rowHeights[ri]*100))
                        cell.set_margins(left=350,right=350,top=250,bottom=250)
                        for pp in cell.paragraphs:
                            pp.para_pr_id_ref=para['cell']
                            for rr in pp.runs:rr.char_pr_id_ref=char['headcell' if ri==0 else 'cell']
                        if ri==0:t.set_cell_shading(ri,ci,'#EDF4FB')
                add('',s,'caption')
        s.remove_layout_caches()
    d.save_to_path(TARGET)
    # Replace the blank template preview and metadata without changing body XML.
    opf='{http://www.idpf.org/2007/opf/}'
    with ZipFile(TARGET) as z:
        entries=[(item,z.read(item.filename)) for item in z.infolist()]
    updated=[]
    preview=[]
    for pg in pages:
        preview.append(pg['title'])
        for block in pg['blocks']:
            if block['kind'] in ('p','h'):preview.append(block['text'])
    with fitz.open(PDF) as pdf:
        cover=pdf[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png')
    for item,data in entries:
        if item.filename=='Preview/PrvText.txt':data='\r\n'.join(preview).encode('utf-8')
        elif item.filename=='Preview/PrvImage.png':data=cover
        elif item.filename=='Contents/content.hpf':
            meta=etree.fromstring(data)
            meta.find('.//'+opf+'title').text='ATM 제어 및 관리 시스템 상세설계서'
            for node in meta.findall('.//'+opf+'meta'):
                if node.get('name') in ('creator','lastsaveby'):node.text='박교범'
                elif node.get('name')=='subject':node.text='2026년 2학기 SW공학 개인 프로젝트'
                elif node.get('name')=='description':node.text='11/16 피드백 반영 통합 v3.0.0; 2026-11-18'
                elif node.get('name')=='keyword':node.text='ATM,상세설계,가상계좌,UML'
            data=etree.tostring(meta,encoding='UTF-8',xml_declaration=True)
        updated.append((item,data))
    temporary=TARGET.with_suffix('.tmp.hwpx')
    with ZipFile(temporary,'w') as z:
        for item,data in updated:z.writestr(item,data)
    temporary.replace(TARGET)
    d=HwpxDocument.open(TARGET)
    report=d.validate()
    validation=dict(ok=report.ok,parts=list(report.validated_parts),issues=[str(x) for x in report.issues])
    (WORK/'HWPX_구조검사.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    if not report.ok:raise RuntimeError(str(report))
    return d

if __name__=='__main__':
    write_content();layouts=compose_pdf();doc=compose_hwpx(layouts)
    print(f'PDF: {PDF}; {len(pages)} pages')
    print(f'HWPX: {TARGET}; {len(doc.sections)} sections; schema validation OK')
    print('PDF is independently typeset from the same source; it is not a native Hancom export.')
