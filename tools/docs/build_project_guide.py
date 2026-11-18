"""Build the current repository guide from the code catalog and actual test report."""
from datetime import datetime, timedelta, timezone
import importlib
import inspect
import json
from pathlib import Path
import sys

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
OUT = ROOT / 'docs' / 'ATM_프로젝트_구조및개발가이드.docx'
CATALOG = json.loads((ROOT/'docs/development/interface_catalog.json').read_text(encoding='utf-8'))
REPORT = json.loads((ROOT/'docs/results/테스트결과.json').read_text(encoding='utf-8'))
MODULES = {
 'TransactionScreen':'presentation.transaction_screen', 'LoginScreen':'presentation.login_screen',
 'MenuScreen':'presentation.menu_screen', 'DepositScreen':'presentation.deposit_screen',
 'WithdrawalScreen':'presentation.withdrawal_screen', 'TransferScreen':'presentation.transfer_screen',
 'ScreenData':'application.screen_data', 'AccountManager':'application.account_manager',
 'VirtualAccount':'domain.virtual_account',
}

def font(run, size=None, bold=None, name='맑은 고딕'):
    run.font.name=name
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'맑은 고딕')
    if size is not None:run.font.size=Pt(size)
    if bold is not None:run.bold=bold
    run.font.color.rgb=RGBColor(0,0,0)
    return run

doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=Inches(.68)
sec.left_margin=sec.right_margin=Inches(.7)
sec.footer_distance=Inches(.28)
for name in ('Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3'):
    style=doc.styles[name]
    style.font.name='맑은 고딕';style.font.color.rgb=RGBColor(0,0,0)
    style._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'맑은 고딕')
    for border in list(style._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    fonts=style._element.get_or_add_rPr().get_or_add_rFonts()
    for attr in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):
        fonts.attrib.pop(qn('w:'+attr),None)
    style.paragraph_format.space_after=Pt(7)
    style.paragraph_format.line_spacing=1.22
doc.styles['Normal'].font.size=Pt(10.5)
doc.styles['Title'].font.size=Pt(23)
doc.styles['Title'].font.bold=True
doc.styles['Subtitle'].font.size=Pt(12)
doc.styles['Subtitle'].font.italic=False
for level,size in ((1,15),(2,12),(3,11)):
    st=doc.styles[f'Heading {level}'];st.font.size=Pt(size);st.font.bold=True
    st.paragraph_format.space_before=Pt(15 if level==1 else 10)
    st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.keep_with_next=True

def paragraph(text, style=None):
    p=doc.add_paragraph(text,style=style)
    for run in p.runs:font(run)
    return p
def heading(text,level=1):return paragraph(text,f'Heading {level}')
def code(text):
    p=doc.add_paragraph()
    p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(10)
    p.paragraph_format.line_spacing=1.12
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F3F5F7');p._p.get_or_add_pPr().append(shade)
    font(p.add_run(text),9.5,name='Consolas')
    return p
def table(headers,rows,widths=None):
    t=doc.add_table(rows=1,cols=len(headers))
    t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    if widths is None:widths=[7.1/len(headers)]*len(headers)
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    props=t._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'5');edge.set(qn('w:color'),'D9D9D9');borders.append(edge)
    props.append(borders)
    margin=OxmlElement('w:tblCellMar')
    for side,value in [('top',95),('bottom',95),('left',100),('right',100)]:
        el=OxmlElement('w:'+side);el.set(qn('w:w'),str(value));el.set(qn('w:type'),'dxa');margin.append(el)
    props.append(margin)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for ri,values in enumerate([headers]+list(rows)):
        row=t.rows[0] if ri==0 else t.add_row()
        no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
        for ci,(cell,value) in enumerate(zip(row.cells,values)):
            cell.width=Inches(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            fill='E5EDF5' if ri==0 else ('FFFFFF' if ri%2 else 'F7F9FB')
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),fill);cell._tc.get_or_add_tcPr().append(shade)
            p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.15
            p.paragraph_format.keep_with_next=ri<min(2,len(rows)) or (headers[0]=='OP' and len(rows)>1 and ri==len(rows)-1)
            if ci==0 and widths[ci]<1.2:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            font(p.add_run(str(value)),9.4,bold=ri==0)
    paragraph('')
    return t

footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
font(footer.add_run('ATM 프로젝트 가이드   '),8)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
doc.core_properties.title='ATM 프로젝트 구조와 개발 가이드'
doc.core_properties.subject='src 계층 구조와 실행 시험 문서'
doc.core_properties.author='박교범'
doc.core_properties.keywords='ATM, Python, Tkinter, src, 소프트웨어공학'

paragraph('ATM 프로젝트 구조와 개발 가이드','Title')
paragraph('src 계층 구조 실행과 검증','Subtitle')
paragraph('작성자 박교범  |  앱 v1.0.0  |  구조 정리 기준 2026년 11월 18일')
paragraph('이 문서는 GitHub에 올릴 ATM 개인 프로젝트의 현재 폴더 구조, 계층별 책임, 실행 방법과 시험 결과를 설명한다. 제품 코드는 src 아래에 계층별로 배치하고, 문서와 모델 및 로컬 검증 자료를 구분했다. 기존 9개 클래스와 44개 설계 메소드를 유지하면서 실행 및 패키지 경로를 조정했다.')
paragraph(f'구조 정리 후 자동 시험 {REPORT["tests_run"]}개를 실행했고 실패 {REPORT["failures"]}개, 오류 {REPORT["errors"]}개, 건너뜀 {REPORT["skipped"]}개를 기록했다. 설계 시험 사례는 {REPORT["passed_design_cases"]}개 중 {REPORT["case_count"]}개가 통과했다. 상세 근거는 docs/results/테스트결과.json에 있다.')
heading('1 프로젝트 개요')
paragraph('ATM의 핵심 동작을 가상 계좌로 구현한 Windows 데스크톱 학습 프로그램이다. 사용자는 계좌번호와 PIN으로 로그인한 뒤 잔액 조회, 입금, 출금과 가상 이체를 이용한다. 실제 금융 시스템이나 실물 기기에 연결하지 않는다.')
table(['항목','기준'],[
 ['언어와 화면','Python 3.13 이상, Tkinter와 ttk'],
 ['실행 의존성','Python 표준 라이브러리만 사용한다. 문서 생성 패키지는 별도이다.'],
 ['계좌 자료','JSON 시드에서 생성한 객체를 실행 중 메모리에 보관한다.'],
 ['상태 유지','로그아웃은 계좌 상태를 유지하고 앱 재시작은 시드로 복구한다.'],
 ['설계 기준','11월 16일 피드백을 반영한 통합 상세설계 v3.0.0'],
],[1.4,5.7])

heading('2 저장소 구조')
paragraph('루트에는 실행 파일과 프로젝트 설정을 둔다. 제품 코드는 src, 시험 코드는 tests, 사용자가 읽는 문서는 docs, Visual Paradigm 원본은 models에 배치한다. .artifacts는 이전 자료와 검토용 출력의 로컬 보관 위치이며 Git 추적 대상에서 제외한다.')
code('''src/atm_app/
  __main__.py                 초기화와 객체 조립
  domain/
    virtual_account.py        계좌 한 개의 상태
    validation.py             입력과 거래 규칙
    constants.py              한도와 단위
  application/
    account_manager.py        계좌 인증과 거래 서비스
    screen_data.py            현재 세션 표시 정보
  presentation/
    transaction_screen.py     거래 흐름과 세션 제어
    login_screen.py           로그인 화면
    menu_screen.py            잔액과 메뉴 화면
    deposit_screen.py         입금 화면
    withdrawal_screen.py      출금 화면
    transfer_screen.py        가상 이체 화면
    widgets.py                공통 화면 구성
  infrastructure/
    bootstrap.py              초기 JSON 전체 검증과 로딩
    data/accounts.seed.json   가상 계좌 시드
  shared/errors.py            공통 오류와 결과 코드''')
table(['경로','용도'],[
 ['tests/','단위, 실제 Tk 위젯 통합, 구조와 재시작 시험'],
 ['docs/design/','기존 HWPX, PDF, Markdown 상세설계와 교수 피드백'],
 ['docs/development/','메소드 계약, 데이터 스키마와 시험 계획'],
 ['docs/results/','현재 구현 현황과 실제 자동 시험 결과'],
 ['docs/diagrams/','기존 그림과 보완한 PNG, SVG, PlantUML'],
 ['models/visual-paradigm/','기존 VPP 모델과 로컬 자동 백업'],
 ['tools/docs/','설계서와 Word 가이드 생성 및 검증 도구'],
],[2.0,5.1])

heading('3 계층과 의존 방향')
paragraph('화면은 application의 서비스를 호출하고, 서비스는 domain의 계좌 객체와 규칙을 사용한다. infrastructure는 외부 JSON을 읽어 계좌를 구성하며, __main__.py가 이 객체들을 조립해 화면에 전달한다. domain과 application은 Tkinter를 import하지 않는다.')
table(['계층','담당 책임','참조 가능한 제품 계층'],[
 ['domain','잔액과 오류 횟수, 차단 불변식, 금액 검증','domain, shared'],
 ['application','계좌 목록, 인증과 거래 서비스, 세션 자료','application, domain, shared'],
 ['presentation','입력, 결과 안내, 화면 전환과 중복 요청 방지','presentation, application, domain, shared'],
 ['infrastructure','시드 파일 읽기, 전체 자료 검증과 객체 생성','infrastructure, domain, shared'],
 ['shared','오류 코드와 공통 예외','shared'],
],[1.25,3.25,2.6])
paragraph('TransactionScreen은 Tk 이벤트 루프와 화면 객체에 직접 의존하므로 presentation에 배치했다. ScreenData는 위젯 없이 세션 정보만 보유하므로 application으로 옮겼다. 폴더 이동과 import 수정에 집중했으며 입출금 한도, 차단 규칙과 가상 이체 범위는 유지했다.')
heading('기존 위치와 현재 위치',2)
table(['기존 위치','현재 위치'],[
 ['atm_app/ui/','src/atm_app/presentation/'],
 ['atm_app/ui/screen_data.py','src/atm_app/application/screen_data.py'],
 ['atm_app/services/','src/atm_app/application/'],
 ['atm_app/bootstrap.py','src/atm_app/infrastructure/bootstrap.py'],
 ['atm_app/data/','src/atm_app/infrastructure/data/'],
 ['개발준비와 개발결과','docs/development와 docs/results'],
 ['다이어그램과 ATM_system','docs/diagrams와 models/visual-paradigm'],
 ['작업자료와 원본백업','.artifacts/analysis와 .artifacts/originals'],
],[3.0,4.1])

heading('4 실행과 개발 환경')
paragraph('소스 폴더를 내려받은 사용자는 루트에서 다음 명령으로 실행한다. run_atm.py가 자신의 위치를 기준으로 src를 찾으므로 다른 작업 디렉터리에서 파일 경로로 실행해도 초기 자료를 읽을 수 있다. Windows에서는 ATM_실행.pyw를 더블클릭한다.')
code('python run_atm.py\npython run_atm.py --check')
paragraph('--check는 GUI 없이 초기 자료만 검사한다. 별도 가상 시드는 python run_atm.py --seed 경로로 지정한다. 입력 JSON이 잘못되면 거래 화면을 제공하지 않는다.')
heading('패키지 방식 개발',2)
code('python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -e .\n.\\.venv\\Scripts\\python.exe -m atm_app')
paragraph('src 구조에서 python -m atm_app은 패키지를 설치한 환경에서 사용한다. 설치 없이 실행할 때는 run_atm.py를 사용한다. pyproject.toml은 src에서 패키지를 찾고 infrastructure/data의 JSON을 배포 패키지에 포함하도록 설정했다.')
table(['계좌','번호','가상 PIN','초기 잔액'],[
 ['A','100100000001','0123','500,000원'],['B','100100000002','5678','2,000,000원'],['C','100100000003','0000','0원']
],[.5,2.6,1.3,2.7])
paragraph('입력은 Enter로 확인하고 Esc로 취소할 수 있다. 출금 성공 후 명세표 예 또는 아니오를 선택하면 계속 이용하거나 거래를 종료할 수 있다. 계좌와 PIN은 모두 가상 예시이다.')

heading('5 기능과 데이터 규칙')
table(['기능','승인 조건','성공 후 변화'],[
 ['로그인','12자리 ASCII 계좌번호, 4자리 PIN, 등록되고 미차단인 계좌','인증 세션 생성, 오류 횟수 0, 잔액 표시'],
 ['입금','양의 정수, 최대 100만 원, 입금 후 잔액 상한 이내','현재 계좌 B에 A를 더한다.'],
 ['출금','양의 정수, 1만 원 배수, 최대 100만 원, A가 실제 잔액 이하','현재 계좌 B에서 A를 뺀다.'],
 ['가상 이체','본인과 다른 12자리 대상, 양의 정수, 실제 잔액 이내','송신 계좌만 차감하고 대상은 변경하지 않는다.'],
 ['종료','메뉴 또는 결과에서 종료 선택','세션과 숨겨진 위젯 입력을 비우고 로그인으로 복귀한다.'],
],[.8,3.3,3.0])
paragraph('형식 오류와 미등록 계좌는 PIN 오류 횟수를 늘리지 않는다. 등록된 미차단 계좌의 PIN 불일치만 1회 증가시키며, 5회째에 failed_count와 blocked를 같은 호출 안에서 바꾼다. 차단 후에는 올바른 PIN도 거절한다.')
table(['데이터','형식과 제약'],[
 ['account_number','고유한 ASCII 숫자 12자리 문자열. 선행 0을 보존한다.'],
 ['password','ASCII 숫자 4자리 가상 PIN. ScreenData와 로그에 보관하지 않는다.'],
 ['balance','0부터 9,999,999,999원까지 정수. bool은 정수 금액으로 허용하지 않는다.'],
 ['failed_count와 blocked','오류 횟수는 0부터 5까지이며 blocked는 failed_count가 5인 경우와 동치이다.'],
 ['ScreenData','인증 계좌, 표시 잔액, 선택 메뉴, 금액 원문과 대상 번호를 일시 보관한다.'],
],[1.9,5.2])
paragraph('표시 잔액은 화면용 사본이다. 서비스는 실제 계좌 잔액을 다시 확인하며 검사를 마친 뒤 한 번만 반영한다. 실패와 취소는 잔액을 유지한다. 처리 중 확인과 취소 버튼을 잠그고 요청 세대를 확인하여 중복 클릭과 이전 콜백의 재실행을 막는다.')
paragraph('시드는 실행 중 수정하지 않는다. 로그아웃은 현재 계좌 상태를 보존하고, 앱을 새로 시작하면 시드의 잔액과 차단 상태로 복구한다. 영속 저장, 실제 은행 통신, 실물 현금, 수신 계좌 입금과 인쇄는 현재 범위에 없다.')

heading('6 클래스와 메소드 계약')
paragraph('원래 9개 클래스의 OP 44개를 유지했다. 다음 표의 메소드 서명은 현재 Python 코드에서 읽었으며 역할은 설계 계약을 요약했다. 화면 구성과 공통 검사에 필요한 내부 보조 메소드는 OP 개수에 포함하지 않는다.')
for entry in CATALOG:
    cls=getattr(importlib.import_module('atm_app.'+MODULES[entry['name']]),entry['name'])
    heading(entry['name'],2)
    intro=paragraph(entry['role']+'. 위치는 src/atm_app/'+MODULES[entry['name']].replace('.','/')+'.py이다.')
    intro.paragraph_format.keep_with_next=True
    rows=[]
    for operation in entry['ops']:
        method=getattr(cls,operation['en'])
        sig=inspect.signature(method)
        sig=sig.replace(parameters=[p for name,p in sig.parameters.items() if name!='self'])
        summary=operation['behavior'].split('. ')[0].rstrip('.')+'.'
        readable=str(sig).replace('atm_app.domain.virtual_account.','')
        rows.append([operation['id'],operation['en']+readable,summary])
    table(['OP','Python 메소드','역할'],rows,[.65,3.15,3.3])
paragraph('문서의 accountNumber와 shownBalance 등 개념 속성은 Python의 account_number와 shown_balance로 대응한다. 외부에 공개하는 AccountManager.accounts는 읽기 전용 tuple이며 계좌 검색 인덱스와 목록이 어긋나는 변경을 막는다. VirtualAccount 속성은 읽기 전용 property이며 지정 메소드로만 바꾼다.')

heading('7 시험 실행과 검증 범위')
code('python -X utf8 tools/run_tests.py\npython -X utf8 tools/verify_implementation.py')
paragraph(f'최근 자동 실행 시각은 {REPORT["executed_at_kst"]}이다. Python {REPORT["python"]}, Tk {REPORT["tk"]} 환경에서 {REPORT["tests_run"]}개가 통과했고 설계 사례 {REPORT["passed_design_cases"]}/{REPORT["case_count"]}를 연결했다. 시험은 독립 시드 복사본에서 시작하며 실제 금융 거래를 수행하지 않는다.')
table(['검증 영역','확인 내용'],[
 ['도메인과 서비스','금액 경계, 무변경 실패, 5회 차단, 성공 시 오류 초기화, 이체 범위'],
 ['실제 Tk 통합','로그인, 입력과 결과, 명세표, 중복 클릭, 종료 정리와 예외 처리'],
 ['재시작','별도 Python 프로세스로 시드가 복구되고 원본 파일은 유지되는지 확인'],
 ['화면 배치','최소 창 크기에서 주요 입력과 버튼이 표시되고 화면 경계에 들어오는지 확인'],
 ['구조 회귀','계층 의존 방향, 옛 디렉터리 제거, 다른 작업 폴더에서 실행, 잘못된 시드의 CLI 실패'],
 ['설계 계약','OP 44개 서명, 시드 일치, README와 문서 링크'],
],[1.35,5.75])
paragraph('앱의 스크린샷 육안 검토는 컴퓨터 제어 연결 문제로 미실시이다. Tk 위젯 배치 시험과 실제 화면 캡처 검토는 별개의 확인이다. 기존 설계 계획의 NOT_RUN 초기값과 현재 제품 시험 결과는 구분하며, 현재 결과는 docs/results를 따른다.')
heading('설계 시험 사례별 결과',2)
for prefix,label in [('L','로그인'),('D','입금'),('W','출금'),('T','가상 이체'),('S','종료와 초기화'),('Q','품질과 방어 조건')]:
    heading(label,3)
    selected=[c for c in REPORT['cases'] if c['id'].startswith('TC-'+prefix)]
    table(['TC','목적','기대 결과','자동 결과'],[[c['id'],c['purpose'],c['expected'],c['status']] for c in selected],[.8,1.2,4.25,.85])

heading('8 GitHub에 올릴 자료와 제외 자료')
paragraph('제품 소스와 시험, 현재 문서 및 원래 모델을 관리 대상으로 둔다. 실행 중 생성되는 캐시, 가상환경과 검토 이미지는 저장소에서 제외한다. 이번 작업은 파일 구조와 문서 정리이며 Git 커밋이나 원격 업로드를 실행하지 않았다.')
table(['관리 대상','이유'],[
 ['src, tests','제품 코드와 재현 가능한 시험'],
 ['docs, models','Word 가이드, 기존 설계서, 시험 결과와 UML 원본'],
 ['tools','시험과 문서 생성 및 검증 재현'],
 ['README.md, read.md','GitHub 첫 화면과 기존 요청 파일의 동일한 안내'],
 ['run_atm.py, ATM_실행.pyw, pyproject.toml, .gitignore','실행 진입점과 패키지 및 추적 제외 설정'],
],[3.1,4.0])
paragraph('.gitignore는 .venv, .artifacts, build와 dist, egg-info, Python 캐시, Word 임시 잠금 파일과 VPP 자동 백업을 제외한다. 기존 VPP 본체는 models에 보존했다. 원본 문서와 이동 전 소스 복사본은 .artifacts에 남겨 되돌릴 수 있게 했다.')
heading('커밋 전 확인',2)
paragraph('프로젝트 루트에서 실행과 자동 시험 및 계약 검사를 확인한 뒤, Git 저장소가 준비된 경우 아래 읽기 명령으로 포함 파일을 검토한다. 아직 Git 저장소를 초기화하지 않았다면 사용자가 원하는 저장소 위치에서 먼저 준비한다.')
code('git status --short\ngit diff --stat\ngit diff --cached --stat\ngit ls-files')
paragraph('스테이징 목록에 .venv, .artifacts, 자동 백업이나 불필요한 임시 출력이 포함되지 않았는지 확인한다. 원격 저장소와 브랜치는 사용자가 선택한다. 기존 HWPX와 PDF는 설계 기준 기록으로 유지하며 최신 실행 안내는 루트 README와 이 문서를 사용한다.')

heading('9 문서와 구현을 함께 수정하는 방법')
paragraph('기능 규칙이나 메소드 입출력을 바꾸면 요구사항, FP 단계, OP 계약, UML과 TC를 함께 수정한다. 경로 변경 시 import, 시드 포함 설정, 실행 파일, 별도 프로세스의 환경과 문서 링크를 검사하고 전체 시험과 계약 검사를 실행한다.')
paragraph('설계 기준은 docs/design, 계약과 시험 계획은 docs/development, 현재 실행 결과는 docs/results에 보관한다. Word 가이드 생성 코드는 tools/docs/build_project_guide.py이며 python-docx가 필요하다. 문서 수정 후 페이지와 표 배치를 다시 확인한다.')

OUT.parent.mkdir(parents=True,exist_ok=True)
# Remove inherited title-rule residue from linked and unused template styles too.
for border in list(doc.styles.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
for border in list(doc.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
doc.save(OUT)
print(f'Saved {OUT}; classes={len(CATALOG)}, operations={sum(len(c["ops"]) for c in CATALOG)}, cases={len(REPORT["cases"])}')
