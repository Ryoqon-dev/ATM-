from pathlib import Path
import json
from project_content import ROOT, DATE, classes, requirements, quality, decisions, tests, flows, pages

OUT=ROOT/'docs'/'development'
OUT.mkdir(parents=True,exist_ok=True)
def write(name,text):
    f=OUT/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text.strip()+'\n',encoding='utf-8')
def mdtable(headers,rows):
    esc=lambda s:str(s).replace('|','\\|').replace('\n','<br>')
    return '\n'.join(['| '+' | '.join(map(esc,headers))+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(esc,row))+' |' for row in rows])

write('README.md',f'''
# ATM 개발 준비 문서

기준일: {DATE} / 통합 설계 v3.0.0 / 작성자: 박교범(2023243047)

11월 16일 피드백을 반영한 상세설계서를 실제 구현 작업으로 연결하기 위한 자료이다. 제품 구현 및 제품 시험은 아직 수행하지 않았다. 아래의 환경·형식·자료 유지 규칙은 원문 미정 사항에 대한 **개발 기준안**이다.

1. [개발환경과 아키텍처](01_개발환경_아키텍처.md)
2. [메소드 인터페이스 계약](02_인터페이스_계약.md)
3. [데이터·검증 규칙](03_데이터설계.md)
4. [시험 계획과 37개 시험 사례](04_테스트계획.md)
5. [구현 작업과 완료 기준](05_구현계획_완료기준.md)
6. [설계 결정과 변경 관리](06_설계결정_변경관리.md)
7. [피드백 반영 및 요구사항 추적](07_피드백_추적표.md)
8. [수동 실행 결과 기록 양식](08_수동검증_기록양식.md)

기계가 읽는 자료는 `data/accounts.schema.json`, `data/accounts.seed.json`, `test_cases.json`, `interface_catalog.json`에 있다. 가상 데이터만 포함한다. 수정 가능한 UML은 `../diagrams/최종보완/`의 SVG·PlantUML을 사용한다. 원본 VPP는 보존되어 있으며 새 그림을 VPP 내부에 반영하지는 않았다.

개발 시작은 01→03→02→05 순서로 읽고, 요구사항별 시험을 구현할 때 04를 참조한다. 원문과 다른 보완 결정을 변경할 경우 06의 변경 기록을 먼저 남긴다.

문서 재생성: 프로젝트 루트에서 `python tools/docs/build_diagrams.py`, `python tools/docs/build_dev_docs.py`, `python tools/docs/build_documents.py`를 실행한다. 문서 생성 의존성은 `../../tools/docs/requirements.txt`를 참조한다. 제품 실행 의존성과 문서 생성 의존성을 분리한다.
''')
write('01_개발환경_아키텍처.md',r'''
# 개발환경과 아키텍처

## 구현 기준안

Windows 데스크톱, Python 3.13, Tkinter/ttk, 표준 json·re·unittest를 기준으로 한다. 원문에는 언어·프레임워크 지정이 없으므로 D-01의 설계 결정이다. 외부 서버·DB·웹 API는 필요하지 않다. HWPX/PDF 생성 패키지는 문서 도구용이며 제품 의존성이 아니다.

프로젝트 루트 PowerShell에서:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -c "import tkinter; print(tkinter.TkVersion)"
```

환경 활성화 정책을 바꿀 필요 없이 venv의 python.exe를 직접 사용한다. 다음 실행 명령은 **아래 폴더와 코드가 구현된 뒤** 유효하다.

```powershell
.\.venv\Scripts\python.exe -m atm_app
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 예정 디렉터리

```text
atm_app/
  __init__.py
  __main__.py                 # 시드 로드, 객체 조립, Tk mainloop
  bootstrap.py                # load_seed, validate_seed
  validation.py               # parse_amount, validate_account_number
  errors.py                   # 업무 오류 코드, 표시 문구
  domain/virtual_account.py   # OP-36~44
  services/account_manager.py # OP-29~35
  ui/transaction_screen.py    # OP-01~07
  ui/login_screen.py          # OP-08~10
  ui/menu_screen.py           # OP-11
  ui/deposit_screen.py        # OP-12~16
  ui/withdrawal_screen.py     # OP-17~21
  ui/transfer_screen.py       # OP-22~23
  ui/screen_data.py           # OP-24~28
  data/accounts.seed.json
tests/
  test_virtual_account.py
  test_account_manager.py
  test_validation.py
  test_screen_data.py
```

위 구조는 개발 계획이며 이번 작업에서 제품 스켈레톤을 생성하지 않았다. 기존 `ATM_system` 폴더는 Visual Paradigm 프로젝트이므로 소스 코드 폴더로 오인하지 않는다.

## 호출 방향과 책임

화면 → TransactionScreen → AccountManager → VirtualAccount 순서로 요청한다. 화면은 서비스 없이 계좌 잔액을 직접 변경할 수 없다. TransactionScreen은 ScreenData 한 개를 소유하고, AccountManager 한 개는 실행 동안 같은 계좌 목록을 참조한다. GUI 갱신은 Tk 메인 스레드에서 수행한다. 본 범위에는 네트워크·장기 I/O가 없어 별도 작업 스레드를 도입하지 않는다.

확인 콜백 진입 시 `processing` 가드를 검사하고 즉시 true로 설정한다. 같은 요청 동안 버튼을 잠그고 `finally`에서 가드를 해제한다. 입력 화면은 승인 후 결과 화면으로 바꾸어 이전 확인 이벤트가 새 거래로 실행되지 않게 한다. 이벤트 루프의 `update()`를 업무 처리 도중 호출하지 않는다. 진행 문구 표시에는 필요 시 `update_idletasks()`만 사용한다. 진짜 비동기 처리를 추가하면 요청 식별자와 중복 처리 방지 정책을 별도로 설계한다.

## 초기화와 종료

시드 전체 검증 → 계좌 객체 구성 → AccountManager 구성 → 빈 ScreenData와 화면 구성 → TransactionScreen 주입 → 로그인 표시 순서로 시작한다. 오류가 있으면 전체 시작을 중단하고 자료 오류를 알린다. 로그아웃은 ScreenData·숨겨진 입력 위젯·PIN 입력란을 비우며 계좌 목록을 재로드하지 않는다. 앱 재시작은 시드로 계좌를 새로 구성한다.

## 검증 위치

UI 검사는 입력 안내를 빠르게 하기 위한 것이고, AccountManager 재검사는 업무 규칙을 보장하기 위한 것이다. VirtualAccount도 음수·과도한 잔액·차단 상태의 변경을 거절한다. 실제 잔액 검사는 ScreenData가 아니라 계좌 객체를 사용한다. PIN은 가상 시드 외에 세션이나 로그에 보관하지 않는다.
''')

lines=['# 메소드 인터페이스 계약','', '설계 명칭과 Python 구현 이름을 연결한다. 모든 메소드는 앞선 FP 처리 단계에서 도출한다. 공개/내부 구분과 원문 9개 클래스를 유지한다. String→str, int→int, boolean→bool, void→None, null→None으로 대응한다. 금액 매개변수에는 bool을 허용하지 않는다.','']
for c in classes:
    lines.extend(['## '+c['name'],'',c['role']+'.',''])
    if c['attrs']:lines.extend([mdtable(['속성','설계 형식','설명'],c['attrs']),''])
    for m in c['ops']:
        lines.extend(['### '+m['id']+' '+m['ko'], '', f'- 구현 이름: `{c["name"]}.{m["en"]}`',f'- 입력: `{m["params"] or "없음"}`',f'- 반환: `{m["returns"]}`',f'- 처리: {m["behavior"]}',f'- 도출: {m["flow"]} / {m["req"]}',''])
lines.extend(['## 공통 함수 및 오류 계약','',
'''`validation.parse_amount(text: str) -> int`는 [0-9]{1,10} 전체 일치 후 1 이상인지 검사한다. 유효하지 않으면 INVALID_AMOUNT 업무 오류를 반환하거나 지정 예외를 발생시킨다. 쉼표·공백·부호·소수·비ASCII 숫자를 허용하지 않는다. 거래별 한도 검사는 호출자가 별도로 한다.

`validation.validate_account_number(text: str) -> bool`은 [0-9]{12} 전체 일치 여부를 반환한다. 이체 대상 존재 여부를 확인하지 않는다.

`bootstrap.load_seed(path) -> list[VirtualAccount]`는 UTF-8 JSON을 전체 검증한 뒤 객체 목록을 구성한다. `bootstrap.validate_seed(data) -> None`은 스키마와 계좌번호 유일성, blocked==(failedCount==5)를 검증하고 오류이면 예외를 발생시킨다. 시드에 쓰지 않는다.

로그인확인은 SUCCESS, INVALID_FORMAT, INVALID_CREDENTIALS, ACCOUNT_BLOCKED 문자열 중 하나를 반환한다. 미등록 계좌와 PIN 불일치는 INVALID_CREDENTIALS이지만, 오류 횟수 증가는 등록된 미차단 계좌의 PIN 불일치에서만 일어난다.

계좌잔액조회는 존재하지 않거나 차단된 계좌이면 `AccountAccessError`를 발생시킨다. 제어기는 이를 받아 성공 안내 없이 세션을 정리한다. 정상 잔액 0과 조회 오류를 혼동하지 않는다.

입금처리·출금처리·가상이체처리는 원문 계약에 맞춰 bool을 반환한다. false는 무변경이며, 제어기가 앞선 입력 검사로 구체적인 이유를 안내한다. 재검사에서 거절된 경우에는 일반 처리 불가 문구를 사용한다. 예상하지 못한 예외는 false로 조용히 삼키지 않고 제어기 예외 경계에서 성공 표시를 막고 세션을 정리한다. 예외 정보에 PIN을 기록하지 않는다.

서비스는 인증 상태를 보유하지 않는다. 사용자 세션 허용 여부는 TransactionScreen이 확인하고, AccountManager는 전달받은 계좌의 존재·차단·업무 규칙을 검사한다. GUI에서 서비스로 들어오는 정상 경로에는 항상 인증된 ScreenData.accountNumber만 전달한다. 서비스 자체의 임의 호출까지 인증을 강제하려면 향후 명시적 세션 토큰 계약을 추가해야 한다.
'''])
write('02_인터페이스_계약.md','\n'.join(lines))
write('interface_catalog.json',json.dumps(classes,ensure_ascii=False,indent=2))

write('03_데이터설계.md', '''
# 데이터·입력 검증 설계

## 계좌 자료

`data/accounts.schema.json`은 JSON Schema draft 2020-12 형식의 초기 자료 계약이다. 제품은 표준 라이브러리의 명시적 검사로 같은 규칙을 구현할 수 있으므로 jsonschema 설치는 제품의 필수 요건이 아니다. 스키마만으로 계좌번호 중복이나 f/blocked 교차 조건을 검증하지 못하므로 bootstrap에서 함께 검사한다.

- accountNumber: ASCII 숫자 12자리 문자열, 고유·불변이다.
- password: ASCII 숫자 4자리 문자열. 0123 같은 선행 0을 보존한다. 학습용 가상 PIN만 저장한다.
- balance: 0~9,999,999,999의 정수 원 단위다. bool은 금액으로 인정하지 않는다.
- failedCount: 0~5 정수다. 형식에 맞는 PIN의 불일치에서만 증가한다.
- blocked: boolean이다. `blocked == (failedCount == 5)`를 만족해야 한다.

## 세션 자료

ScreenData는 계좌번호와 표시 잔액, 선택 메뉴, 금액 원문, 대상 계좌번호를 갖는다. 초기값은 accountNumber/shownBalance/selectedMenu=None, amountText/targetAccountNumber=""이다. PIN은 속성으로 만들지 않는다. shownBalance는 실제 계좌 잔액의 사본이므로 승인 판단에 사용하지 않는다.

## 거래 규칙

입력은 [0-9]{1,10}이고 값은 1 이상이다. 입금은 최대 100만 원, 출금은 1만 원 배수이면서 최대 100만 원, 이체는 별도 100만 원 한도 없이 실제 잔액 이하이다. 입금 후에도 잔액 상한을 넘을 수 없다. 이체 대상은 12자리 숫자이며 본인과 달라야 하지만 등록 여부는 확인하지 않는다. 입력한 대상이 로컬의 다른 계좌여도 수신 잔액은 변경하지 않는다.

서비스는 모든 조건을 검사한 뒤 단일 계좌의 잔액을 한 번 갱신한다. 조건 실패·취소는 B′=B이다. 입금 성공은 B′=B+A이고, 출금·가상 이체 성공은 B′=B-A≥0이다. 실물 현금 흐름, 은행 간 대사, 송수신 합계 보존을 검증하는 시스템은 현 범위에 없다.

## 자료 유지

실행 중 계좌 객체가 원본 상태를 보유한다. 로그아웃은 계좌 상태를 바꾸지 않는다. 시드 JSON을 실행 중 수정하지 않는다. 재시작 시 모든 자료는 시드로 복구되며 차단 계좌도 시드 설정을 따른다. 앱 재시작 이후 차단 유지나 영속 잔액 저장이 요구되면 D-05 변경과 저장 실패·복구 시험을 함께 추가해야 한다.

## 초기 자료

| 별칭 | 계좌번호 | 가상 PIN | 초기 잔액 | 용도 |
| --- | --- | --- | --- | --- |
| A | 100100000001 | 0123 | 500000 | 정상·잔액 부족·인증 경계 |
| B | 100100000002 | 5678 | 2000000 | 입출금 상한·100만 원 초과 이체 |
| C | 100100000003 | 0000 | 0 | 잔액 0·입금 경계 |

차단·오류 횟수·잔액 상한 등의 시험 전제는 각 시험에서 별도 메모리 계좌로 구성한다. 공유 시드 파일을 수정하면서 시험하지 않는다.
''')
schema={
 '$schema':'https://json-schema.org/draft/2020-12/schema',
 'title':'ATM simulation seed', 'type':'object','additionalProperties':False,
 'required':['schemaVersion','accounts'],
 'properties':{'schemaVersion':{'const':1},'accounts':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['accountNumber','password','balance','failedCount','blocked'],'properties':{
 'accountNumber':{'type':'string','pattern':'^[0-9]{12}$'},'password':{'type':'string','pattern':'^[0-9]{4}$'},'balance':{'type':'integer','minimum':0,'maximum':9999999999},'failedCount':{'type':'integer','minimum':0,'maximum':5},'blocked':{'type':'boolean'}}}}}}
seed={'schemaVersion':1,'accounts':[
dict(accountNumber='100100000001',password='0123',balance=500000,failedCount=0,blocked=False),
dict(accountNumber='100100000002',password='5678',balance=2000000,failedCount=0,blocked=False),
dict(accountNumber='100100000003',password='0000',balance=0,failedCount=0,blocked=False)]}
write('data/accounts.schema.json',json.dumps(schema,ensure_ascii=False,indent=2))
write('data/accounts.seed.json',json.dumps(seed,ensure_ascii=False,indent=2))

write('04_테스트계획.md','''
# 시험 계획

상태: **설계 완료 / 제품 시험 미실행**. 아래 예상 결과를 실제 시험 통과 결과로 해석하지 않는다.

## 방법

도메인 단위 시험은 VirtualAccount의 불변식과 상태 전이를, 서비스 통합 시험은 입력·한도·실제 잔액과 무변경 조건을, GUI 수동 시험은 표시·화면 전이·입력 정리·이중 클릭을 확인한다. 테스트 더블로 서비스 호출 횟수와 예외를 관찰한다. 시간 지연을 기다리는 시험보다 결과와 호출 횟수를 확인한다.

각 시험은 독립적인 A/B/C 시드 복사본에서 시작한다. “이후”라고 적힌 사례도 앞선 시험에 의존하지 않고 그 상태를 해당 사례 내부에서 구성한다. 로그인 실패 횟수는 계좌별이며 세션별이 아니다. 차단 관련 사전 상태는 failedCount와 blocked를 함께 일관되게 설정한다. 단위·서비스 시험은 `unittest`로 자동화하고 GUI 사례는 수동 결과를 기록한다.

## 시험 사례

'''+mdtable(['ID','요구사항','목적','입력 / 전제','기대 결과'],tests)+'''

## 수용 기준

1. 각 원래 REQ 15개 및 보완 REQ-Q 5개에 하나 이상의 시험 증거가 있다.
2. 금액 0, 최소 양수, 1만 원 배수 경계, 100만 원·초과, 잔액 동일·초과를 확인한다.
3. 4번째·5번째 PIN 오류와 성공 초기화, 차단 후 정상 PIN 거절을 확인한다.
4. 실패·취소·거절된 거래에서 모든 계좌 잔액이 유지된다.
5. 로그아웃 후 같은 프로세스의 잔액·차단은 유지하고, 재시작은 시드로 복구된다.
6. 실행 결과의 날짜·환경·실제 결과·증거를 기록하고 미실행을 통과로 바꾸지 않는다.

예정 실행 명령: `.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v` (구현 후 유효).
''')
write('test_cases.json',json.dumps([dict(id=a,requirements=b,purpose=c,input=d,expected=e,status='NOT_RUN') for a,b,c,d,e in tests],ensure_ascii=False,indent=2))
write('05_구현계획_완료기준.md','''
# 구현 작업과 완료 기준

날짜를 임의로 배정하지 않고 의존 순서와 종료 조건으로 관리한다. 모든 작업의 초기 상태는 미착수이다.

| 작업 | 범위 | 선행 | 완료 조건 |
| --- | --- | --- | --- |
| DEV-01 | venv·Tkinter·폴더·unittest 검색 준비 | 없음 | 환경 명령 성공·빈 GUI 확인 |
| DEV-02 | 시드 전체 검증·계좌 객체 구성 | DEV-01 | 정상·중복·형식·불변식 실패 자료 시험 |
| DEV-03 | VirtualAccount OP-36~44 | DEV-02 | 잔액·오류 횟수·차단 전이·도메인 방어 시험 |
| DEV-04 | AccountManager OP-29~35·공통 검증 | DEV-03 | 인증·경계 금액·서비스 우회·가상 이체 범위 시험 |
| DEV-05 | ScreenData OP-24~28 | DEV-01 | 저장·조회·초기화·PIN 비보관 확인 |
| DEV-06 | 화면 5개 OP-08~23 | DEV-01 | 입력·마스킹·경고·결과·명세표 안내 확인 |
| DEV-07 | TransactionScreen OP-01~07 | DEV-04~06 | 세션 확인·연속 거래·종료·중복 클릭·예외 시험 |
| DEV-08 | 통합 시험·실행 문서·데모 | DEV-07 | 37개 사례의 실행 결과 기록과 추적성 확인 |

작업별 완료에는 관련 OP 구현, 해당 REQ/TC 연결, 시험 실행 기록, 문서와 UML 동기화를 포함한다. 단순히 화면이 뜨거나 메소드가 존재하는 것만으로 완료 처리하지 않는다.

## 데모 시나리오

1. A/0123 로그인, 잔액 500000원을 확인한다.
2. 30000원 입금 후 530000원, 20000원 출금 후 510000원과 명세표 안내를 확인한다.
3. 999999999999로 10000원 가상 이체 후 500000원을 확인한다.
4. 종료 후 PIN·계좌·금액 입력과 표시 잔액이 지워지는지 확인한다.
5. 재로그인하여 실행 중 계좌 결과가 남는지 확인한다.
6. 별도 초기 데이터에서 5회 PIN 불일치와 차단 후 정상 PIN 거절을 시연한다.

## 제품 제출 완료 조건

소스·시드·실행 방법·환경 버전·실행 시험 결과·알려진 제약을 제공한다. 실제 은행 연동, 영속 저장, 실물 출력이 있는 것처럼 설명하지 않는다. 문서와 코드의 메소드 이름·형식·한도·화면 전이가 일치해야 한다. 제출·배포는 이번 문서 작업에 포함하지 않는다.
''')
write('06_설계결정_변경관리.md','# 설계 결정과 변경 관리\n\n원문에 없는 경계 규칙과 구현 기준안을 명시한다. 교수님이 지시하거나 승인한 내용으로 간주하지 않는다.\n\n'+mdtable(['ID','주제','채택 기준'],decisions)+'''

## 원문 보존과 보완 구분

원문 보존: 계좌번호+4자리 PIN 인증, 5회 오류 차단, 즉시 잔액, 100만 원 입금·출금, 1만 원 출금 단위, 송신만 차감하는 가상 이체, 종료 시 화면 정리, 9개 클래스.

보완 결정: 구체적 계좌번호 길이, ASCII 입력과 양수·잔액 상한, 미등록·형식 오류의 횟수 규칙, 본인 이체 거절, 연속 거래 선택, 메모리 유지 기간, Python/Tkinter 기준, 중복 클릭·오류 방어.

## 변경 절차

1. 변경 사유와 대상 D/REQ를 기록한다.
2. UC와 FP 단계, OP 입출력, 속성·관계, 상태도·시퀀스, 데이터 스키마, 시험 사례의 영향을 찾는다.
3. 관련 문서와 코드 변경을 같은 작업으로 묶고 기준 버전을 올린다.
4. 영향 시험을 다시 실행하고 결과를 기록한다.

| 변경 ID | 일자 | 사유 | REQ/FP/OP/TC 영향 | 결정·처리 결과 |
| --- | --- | --- | --- | --- |
| CR-20261118 | 2026-11-18 | 11/16 교수 피드백과 원문 미정 규칙 | FB-01~05, D-01~07 | 통합 v3.0.0 문서에 반영; 교수 확인 미실시 |
''')
write('07_피드백_추적표.md','''
# 피드백 반영과 추적성

자료: 루트의 `1116교수님피드백.txt`, 11/13 원본 상세설계서, 기존 다이어그램. 피드백 파일의 중복 번호를 내용 순서에 따라 FB-01~05로 정규화했다.

| 피드백 | 반영 | 확인 방법 |
| --- | --- | --- |
| FB-01 요구사항은 문장 | REQ 15개와 보완 품질 5개를 조건·주어·의무 동작으로 기술 | I장과 아래 요구사항 목록 |
| FB-02 상태도 개념 객체 | VirtualAccount 한 개의 거래 가능/차단 상태로 재설계 | IV-1~3, state_account SVG/PNG/PUML |
| FB-03 워크플로우 근거 | 요구사항→UC→FP 단계→OP→시험 연결 | II장 기능 프로세스, III장 OP 근거 |
| FB-04 클래스 그림 정렬 | 3열 고정 폭·일정 간격 새 UML | class_full SVG/PNG/PUML |
| FB-05 메소드 선행 명세 | 44개 OP의 이름·매개변수·반환·행위·도출근거를 그림 앞에 배치 | III장, interface_catalog.json |

원문의 무관한 음악 엔진 예시를 ATM 구조로 교체했다. 시스템 내부 객체를 외부 액터로 취급한 표현을 정리하고, 기존 하위 UC를 FP 단계로 통합했다. 클래스와 계좌 범위는 보존했으며 변경 기준은 D-01~07에 명시했다.

## 요구사항→유즈케이스→기능 단계

'''+mdtable(['요구사항','규범 문장','UC','FP'],requirements)+'''

## 품질 보완

'''+mdtable(['ID','문장'],quality)+'''

메소드별 추적은 02 인터페이스 계약, 시험별 추적은 04 테스트 계획을 참조한다. 제품 구현의 통과 여부는 아직 확인하지 않았다.
''')
write('08_수동검증_기록양식.md','''
# 수동 검증 기록 양식

이 파일은 개발 후 실행 결과를 기록할 양식이다. 현재 기록은 미실행이다.

| 항목 | 기록 |
| --- | --- |
| 실행일 | 미실행 |
| 실행자 | 미기록 |
| OS / Python / Tk | 미기록 |
| 코드 버전 | 미기록 |
| 초기 자료 | accounts.seed.json의 새 복사본 |
| 실행 명령 | 구현 후 기록 |

| TC ID | 관찰한 실제 결과 | 판정(PASS/FAIL/NOT_RUN) | 증거 경로 | 결함/후속 작업 |
| --- | --- | --- | --- | --- |
| TC-Q03 중복 확인 | 미실행 | NOT_RUN | - | - |
| TC-Q05 PIN 노출 | 미실행 | NOT_RUN | - | - |
| TC-S01 종료 정리 | 미실행 | NOT_RUN | - | - |
| TC-S02 재로그인 | 미실행 | NOT_RUN | - | - |
| TC-S03 재시작 | 미실행 | NOT_RUN | - | - |

화면 증거에는 가상 데이터만 사용한다. PIN은 의도적인 마스킹 확인 화면 외에 노출하지 않는다. 예상 결과를 실제 관찰 결과에 복사하여 통과로 처리하지 않는다.
''')

md=[]
for i,pg in enumerate(pages,1):
    md.extend([f'# {pg["title"]}',f'문서 구성 쪽 {i}', ''])
    for b in pg['blocks']:
        if b['kind']=='p':md.extend([b['text'],''])
        elif b['kind']=='h':md.extend(['## '+b['text'],''])
        elif b['kind']=='table':md.extend([mdtable(b['headers'],b['rows']),''])
        elif b['kind']=='figure':md.extend([f'![{b["caption"]}](../diagrams/최종보완/{b["name"]}.png)',b['caption'],''])
(ROOT/'docs'/'design'/'상세설계서_최종보완_원문.md').write_text('\n'.join(md),encoding='utf-8')
# Preserve the distinction between this design baseline and later implementation.
if (ROOT/'docs'/'results'/'테스트결과.json').exists():
    notice='> 현재 ATM 앱 구현과 제품 자동 시험 결과는 [구현 현황](../results/구현현황.md)과 [제품 시험 결과](../results/테스트결과.md)를 참조한다. 아래는 구현 이전 설계 기준 기록이다.\n\n'
    for name in ['README.md','04_테스트계획.md','05_구현계획_완료기준.md']:
        path=OUT/name
        text=path.read_text(encoding='utf-8')
        first, rest=text.split('\n',1)
        path.write_text(first+'\n\n'+notice+rest.lstrip(),encoding='utf-8')
print('Development documents, schemas, seed, contracts, tests and editable specification written')
