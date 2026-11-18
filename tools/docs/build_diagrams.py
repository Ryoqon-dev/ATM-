from pathlib import Path
import math, html
from PIL import Image, ImageDraw, ImageFont
from project_content import ROOT, classes

OUT=ROOT/'docs'/'diagrams'/'최종보완'
OUT.mkdir(parents=True,exist_ok=True)
FONT='C:/Windows/Fonts/malgun.ttf'
BOLD='C:/Windows/Fonts/malgunbd.ttf'
INK='#172E4D';BLUE='#2261A5';PALE='#EDF4FB';EDGE='#67829D'

class Canvas:
    def __init__(self,w,h):
        self.w,self.h=w,h;self.im=Image.new('RGB',(w,h),'white');self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>']
    def rect(self,b,fill='white',outline=EDGE,r=0,width=3):
        self.d.rounded_rectangle(b,r,fill=fill,outline=outline,width=width)
        x,y,x2,y2=b;self.svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" rx="{r}" fill="{fill}" stroke="{outline}" stroke-width="{width}"/>')
    def text(self,x,y,text,size=30,bold=False,anchor='mm',fill=INK):
        font=ImageFont.truetype(BOLD if bold else FONT,size)
        lines=text.split('\n');step=size*1.42
        for i,t in enumerate(lines):
            yy=y+(i-(len(lines)-1)/2)*step if anchor=='mm' else y+i*step
            self.d.text((x,yy),t,font=font,fill=fill,anchor=anchor)
            self.svg.append(f'<text x="{x}" y="{yy}" font-family="Malgun Gothic,맑은 고딕,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}" text-anchor="{"middle" if anchor=="mm" else "start"}" dominant-baseline="{"central" if anchor=="mm" else "text-before-edge"}">{html.escape(t)}</text>')
    def line(self,pts,fill=EDGE,width=3,dash=False):
        if dash:
            for (a,b),(c,d) in zip(pts,pts[1:]):
                dist=math.hypot(c-a,d-b);n=max(1,int(dist/14))
                for i in range(0,n,2):
                    self.d.line([(a+(c-a)*i/n,b+(d-b)*i/n),(a+(c-a)*min(i+1,n)/n,b+(d-b)*min(i+1,n)/n)],fill=fill,width=width)
        else:self.d.line(pts,fill=fill,width=width)
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{fill}" stroke-width="{width}"'+(' stroke-dasharray="12 8"' if dash else '')+'/>')
    def arrow(self,pts,label=None,dash=False,diamond=False):
        self.line(pts,dash=dash)
        x,y=pts[-1];px,py=pts[-2];ang=math.atan2(y-py,x-px)
        ends=[(x-18*math.cos(ang-a),y-18*math.sin(ang-a)) for a in [-.45,.45]]
        self.line([ends[0],(x,y),ends[1]])
        if diamond:
            x,y=pts[0];xx,yy=pts[1];a=math.atan2(yy-y,xx-x)
            points=[(x,y),(x+15*math.cos(a+.6),y+15*math.sin(a+.6)),(x+26*math.cos(a),y+26*math.sin(a)),(x+15*math.cos(a-.6),y+15*math.sin(a-.6))]
            self.d.polygon(points,fill=INK);self.svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in points)}" fill="{INK}"/>')
        if label:
            a,b=pts[len(pts)//2-1];c,d=pts[len(pts)//2];self.text((a+c)/2,(b+d)/2-22,label,25)
    def box(self,x,y,w,h,text,size=30):
        self.rect((x-w/2,y-h/2,x+w/2,y+h/2),PALE,r=16);self.text(x,y,text,size)
    def decision(self,x,y,w,h,text):
        pts=[(x,y-h/2),(x+w/2,y),(x,y+h/2),(x-w/2,y)]
        self.d.polygon(pts,fill=PALE,outline=EDGE,width=3)
        self.svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="{PALE}" stroke="{EDGE}" stroke-width="3"/>');self.text(x,y,text,28)
    def circle(self,x,y,r=14):
        self.d.ellipse((x-r,y-r,x+r,y+r),fill=INK);self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{INK}"/>')
    def ellipse(self,x,y,w,h,text,size=30):
        self.d.ellipse((x-w/2,y-h/2,x+w/2,y+h/2),fill=PALE,outline=EDGE,width=3)
        self.svg.append(f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" fill="{PALE}" stroke="{EDGE}" stroke-width="3"/>')
        self.text(x,y,text,size)
    def save(self,name):
        self.im.save(OUT/(name+'.png'));(OUT/(name+'.svg')).write_text(''.join(self.svg)+'</svg>',encoding='utf-8')

def architecture():
    c=Canvas(1700,920)
    c.box(850,100,1480,130,'경계: Login / Menu / Deposit / Withdrawal / Transfer Screen',32)
    c.box(590,340,960,150,'TransactionScreen\n흐름 조정 · 세션 확인 · 중복 실행 방지',34)
    c.box(1380,340,400,150,'ScreenData\n임시 표시 정보',32)
    c.box(590,600,960,150,'AccountManager\n계좌 검색 · 인증 · 업무 규칙 재검증',34)
    c.box(1380,600,400,150,'bootstrap\n시드 검증·로드',30)
    c.box(590,825,960,130,'VirtualAccount 0..*\n한 계좌의 잔액 · 연속 오류 · 거래 차단',33)
    c.arrow([(590,165),(590,265)]);c.arrow([(1070,340),(1180,340)],diamond=True)
    c.arrow([(590,415),(590,525)]);c.arrow([(590,675),(590,760)])
    c.arrow([(1180,600),(1070,600)],dash=True)
    c.save('architecture')

def usecase():
    c=Canvas(1500,1030);c.rect((410,60,1430,970),'white',r=5)
    c.text(920,110,'ATM 제어 및 관리 시스템',36,True)
    c.circle(160,400,35);c.line([(160,435),(160,570)]);c.line([(90,480),(230,480)]);c.line([(160,570),(90,680)]);c.line([(160,570),(230,680)]);c.text(160,740,'사용자',34,True)
    for i,t in enumerate(['UC-01 로그인·잔액 조회','UC-02 입금','UC-03 출금','UC-04 가상 이체','UC-05 거래 종료']):
        y=250+i*145;c.ellipse(930,y,730,105,t,34);c.line([(250,510),(565,y)])
    c.save('usecase')

def activity_login():
    c=Canvas(1500,1470);x=620
    c.circle(x,35);c.arrow([(x,50),(x,100)])
    c.box(x,155,540,110,'FP-01.1 계좌번호·PIN 입력',28);c.arrow([(x,210),(x,270)])
    c.decision(x,345,570,150,'FP-01.2 형식 유효?')
    c.arrow([(905,345),(1210,345),(1210,155),(890,155)]);c.text(1200,245,'아니오\n재입력 안내\nf 무변경',27)
    c.arrow([(x,420),(x,490)]);c.text(570,455,'예',25)
    c.box(x,545,600,110,'FP-01.3 계좌 조회·차단 검사',28);c.arrow([(x,600),(x,665)])
    c.decision(x,740,570,150,'등록됨 · 미차단 · PIN 일치?')
    c.arrow([(x,815),(x,950)]);c.text(565,870,'예',25)
    c.box(x,1005,620,110,'FP-01.4 f=0 / 인증 성공',30)
    c.arrow([(x,1060),(x,1150)]);c.box(x,1210,620,120,'FP-01.5 계좌·잔액 저장\n메뉴 표시',29)
    c.arrow([(905,740),(1210,740),(1210,950)]);c.text(1200,840,'아니오',27)
    c.box(1210,1040,470,180,'미등록/차단: 거절\nPIN 불일치만 f+1\n5회째 거래 차단',27)
    c.arrow([(1210,1130),(1210,1380),(160,1380),(160,155),(350,155)])
    c.text(780,1420,'실패 안내 후 로그인으로 복귀 / 5회째는 세션 초기화',25)
    c.save('activity_login')

def activity_transaction():
    c=Canvas(1500,1650);x=680
    c.circle(x,40);c.arrow([(x,55),(x,110)])
    nodes=[(170,'인증된 세션에서 거래 선택\nFP-02/03/04.1'),(410,'금액·대상 입력'),(850,'진행 안내 · 확인 버튼 잠금'),(1080,'업무 규칙 재검증 후\nVirtualAccount에 한 번 반영'),(1300,'새 잔액 조회 · 결과 표시')]
    for y,t in nodes:c.box(x,y,720,120,t,32)
    c.arrow([(x,230),(x,350)]);c.arrow([(x,470),(x,535)])
    c.decision(x,620,700,170,'입력·업무 조건이 유효한가?')
    c.arrow([(x,705),(x,790)]);c.text(620,745,'예',27)
    c.arrow([(1030,620),(1240,620),(1240,1300),(1040,1300)])
    c.text(1250,900,'아니오\n거절·잔액 유지',29)
    c.arrow([(x,910),(x,1020)]);c.arrow([(x,1140),(x,1240)])
    c.arrow([(x,1360),(x,1420)]);c.decision(x,1490,680,140,'계속 이용?')
    c.arrow([(340,1490),(140,1490),(140,170),(320,170)]);c.text(170,1370,'예',28)
    c.arrow([(1020,1490),(1280,1490)]);c.text(1230,1430,'아니오\nFP-05 정리·로그인',27)
    c.text(750,300,'취소 → 입력 비움 → 메뉴 (계좌 무변경)',28)
    c.save('activity_transaction')

def state():
    c=Canvas(1600,1450)
    c.circle(110,100);c.arrow([(125,100),(360,100)])
    c.decision(570,100,420,120,'시드 blocked?')
    c.arrow([(570,160),(570,300)]);c.text(490,230,'false',27)
    c.rect((180,300,1040,930),PALE,r=24);c.text(610,350,'거래 가능',40,True)
    c.line([(180,400),(1040,400)])
    c.text(220,440,'불변식: blocked=false / 0≤f≤4',30,anchor='la')
    lines=['PIN 불일치 [f<4] / f=f+1','PIN 일치 / f=0','입금 [검사 통과] / B=B+A','출금 [검사 통과] / B=B-A','가상 이체 [검사 통과] / 송신 B=B-A','형식 오류·취소·잔액 부족 / 무변경']
    for i,t in enumerate(lines):c.text(225,520+i*62,t,30,anchor='la')
    c.rect((180,1120,1040,1360),PALE,r=24);c.text(610,1170,'거래 차단',40,True)
    c.line([(180,1220),(1040,1220)]);c.text(610,1270,'로그인·입출금·이체 요청 / 거절',29)
    c.text(610,1320,'불변식: blocked=true / f=5',29)
    c.arrow([(610,930),(610,1120)]);c.text(1120,1000,'PIN 불일치 [f=4]\n/ f=5, blocked=true\n/ 세션 초기화 요청',29)
    c.arrow([(780,100),(1460,100),(1460,1240),(1040,1240)]);c.text(1330,210,'true',29)
    c.text(1220,560,'거래 처리 단계는\n활동도로 표현한다.\n로그아웃은 계좌\n상태를 바꾸지 않는다.',29)
    c.save('state_account')

def class_diagram():
    c=Canvas(2700,1680)
    positions={'LoginScreen':(80,80),'MenuScreen':(970,80),'DepositScreen':(1860,80),'WithdrawalScreen':(80,630),'TransactionScreen':(970,630),'TransferScreen':(1860,630),'ScreenData':(80,1180),'AccountManager':(970,1180),'VirtualAccount':(1860,1180)}
    # Nodes use equal widths and heights; relations are routed through gutters.
    c.arrow([(1370,630),(1370,575),(480,575),(480,520)],dash=True)
    c.arrow([(1370,630),(1370,520)],dash=True)
    c.arrow([(1370,630),(1370,575),(2260,575),(2260,520)],dash=True)
    c.arrow([(970,850),(880,850)],dash=True);c.arrow([(1770,850),(1860,850)],dash=True)
    c.arrow([(1170,1070),(1170,1125),(480,1125),(480,1180)],diamond=True)
    c.arrow([(1370,1070),(1370,1180)]);c.text(1410,1130,'1',24)
    c.arrow([(1770,1400),(1860,1400)]);c.text(1815,1350,'0..*',24)
    for obj in classes:
        x,y=positions[obj['name']];w=800;ht=440
        c.rect((x,y,x+w,y+ht),'white',width=3)
        c.rect((x,y,x+w,y+48),PALE);c.text(x+w/2,y+24,obj['name'],31,True)
        attrs=obj['attrs']; ay=y+60
        if attrs:
            for a,t,d in attrs:
                c.text(x+17,ay,'- '+a+': '+t,23,anchor='la');ay+=25
        else:c.text(x+17,ay,'(별도 업무 속성 없음)',23,anchor='la');ay+=25
        c.line([(x,ay+7),(x+w,ay+7)]);ay+=18
        for m in obj['ops']:
            sign='-' if m['en'].startswith('_') else '+'
            text=sign+' '+m['ko']+'('+('…' if m['params'] else '')+'): '+m['returns']+'  ['+m['id']+']'
            c.text(x+17,ay,text,23,anchor='la');ay+=25
    c.text(1350,1645,'+ 공개 메소드  |  - 속성·내부 메소드  |  (…) 매개변수는 OP 명세 참조  |  점선: 의존  /  실선: 연관  /  ◆: 합성',26)
    c.save('class_full')
    # Text UML is the editable semantic source, independent of the raster drawing.
    uml=['@startuml','skinparam defaultFontName Malgun Gothic','skinparam classAttributeIconSize 0','skinparam linetype ortho','skinparam nodesep 70','skinparam ranksep 75','hide empty members']
    for o in classes:
        uml.append('class '+o['name']+' {')
        uml += ['  - '+a+': '+t for a,t,d in o['attrs']]
        for m in o['ops']:
            uml.append("  ' "+m['id'])
            uml.append('  '+('-' if m['en'].startswith('_') else '+')+m['ko']+'('+m['params']+'): '+m['returns'])
        uml.append('}')
    uml+=['TransactionScreen ..> '+x for x in ['LoginScreen','MenuScreen','DepositScreen','WithdrawalScreen','TransferScreen']]
    uml+=['TransactionScreen "1" *--> "1" ScreenData','TransactionScreen "1" --> "1" AccountManager','AccountManager "1" --> "0..*" VirtualAccount','@enduml']
    (OUT/'class_full.puml').write_text('\n'.join(uml),encoding='utf-8')

def sequence(name,login=False):
    c=Canvas(1700,1730);xs=[140,570,1040,1510]
    names=['사용자','TransactionScreen','AccountManager','VirtualAccount']
    for x,t in zip(xs,names):
        c.box(x,75,260 if x==140 else 370,100,t,27)
        c.line([(x,125),(x,1640)],dash=True)
    def msg(a,b,y,text,ret=False):
        c.arrow([(xs[a],y),(xs[b],y)],dash=ret);c.text((xs[a]+xs[b])/2,y-35,text,26)
    if login:
        msg(0,1,230,'로그인요청 OP-01')
        c.box(570,360,410,115,'형식 검사 OP-09\n오류이면 즉시 경고',27)
        msg(1,2,510,'로그인확인 OP-31')
        msg(2,3,660,'차단 확인 OP-44')
        msg(3,2,770,'차단 여부',True)
        msg(2,3,920,'[미차단] PIN 비교 OP-37')
        c.box(1120,1060,930,145,'[불일치] OP-30 → OP-41, 5회째 OP-43\n[일치] OP-42 오류횟수초기화\n[이미 차단] 비교·변경 없이 거절',26)
        msg(2,1,1220,'SUCCESS / 인증 실패 / 차단',True)
        c.box(600,1390,830,145,'성공: OP-24 계좌 저장 → OP-07 잔액 갱신\n실패: OP-10 경고 / 차단: OP-06 초기화',26)
        msg(1,0,1580,'메뉴·잔액 또는 로그인 경고',True)
    else:
        msg(0,1,230,'거래요청 OP-03/04/05')
        c.box(570,370,440,140,'인증·형식·업무 검사\n오류: 반영 없이 안내\n확인 버튼 비활성',27)
        msg(1,2,560,'거래 처리 OP-33/34/35')
        c.box(1040,700,450,140,'계좌·차단·규칙 재검사\n표시 잔액 사용 금지',27)
        msg(2,3,910,'반영 OP-39 / OP-40')
        c.box(1510,1030,340,110,'검사 후\n한 번만 증감',27)
        msg(3,2,1170,'반영 완료',True)
        msg(2,1,1300,'true 또는 false',True)
        msg(1,2,1430,'계좌잔액조회 OP-32')
        msg(2,1,1540,'최신 잔액',True)
        c.text(850,1690,'OP-26 표시 잔액 저장 → 결과 안내 → 계속 이용 / OP-06 종료',26)
    c.save(name)

def extra_sources():
    sources={
    'state_account':'''@startuml
skinparam defaultFontName Malgun Gothic
state "거래 가능" as Active
state "거래 차단" as Blocked
state init <<choice>>
[*] --> init
init --> Active : [seed.blocked=false]
init --> Blocked : [seed.blocked=true]
Active : PIN 불일치 [f<4] / f=f+1
Active : PIN 일치 / f=0
Active : 입금 [검사 통과] / B=B+A
Active : 출금·가상이체 [검사 통과] / B=B-A
Active : 형식 오류·취소·잔액 부족 / 무변경
Active --> Blocked : PIN 불일치 [f=4] / f=5, blocked=true
Blocked : 로그인·거래 요청 / 거절
@enduml''',
    'usecase':'''@startuml
left to right direction
skinparam defaultFontName Malgun Gothic
actor 사용자 as U
rectangle "ATM 제어 및 관리 시스템" {
usecase "UC-01 로그인·잔액 조회" as L
usecase "UC-02 입금" as D
usecase "UC-03 출금" as W
usecase "UC-04 가상 이체" as T
usecase "UC-05 거래 종료" as E
}
U -- L
U -- D
U -- W
U -- T
U -- E
@enduml''',
    'activity_login':'''@startuml
start
:FP-01.1 계좌번호·PIN 입력;
if (FP-01.2 형식 유효?) then (예)
 :FP-01.3 계좌 검색·차단 검사;
 if (등록·미차단?) then (예)
  if (PIN 일치?) then (예)
   :f=0;
   :FP-01.5 계좌번호 저장·잔액·메뉴 표시;
  else (아니오)
   :FP-01.4 f+1;
   if (f=5?) then (예)
    :계좌 차단·세션 초기화;
   endif
   :로그인 경고·재입력;
  endif
 else (아니오)
  :로그인 거절·재입력;
 endif
else (아니오)
 :형식 안내·재입력 (f 무변경);
endif
stop
@enduml''',
    'activity_transaction':'''@startuml
start
:인증된 사용자의 거래 선택;
:FP-02/03/04.1 금액·대상 입력;
if (입력·업무 조건 유효?) then (예)
 :진행 안내·확인 버튼 잠금;
 :서비스 규칙 재검증;
 if (승인?) then (예)
  :한 번만 잔액 반영;
  :새 잔액·완료 표시;
 else (아니오)
  :거절·잔액 유지;
 endif
else (아니오)
 :거절·잔액 유지;
endif
if (계속 이용?) then (예)
 :거래 메뉴;
else (아니오)
 :FP-05 세션 정리·로그인;
endif
stop
@enduml''',
    'sequence_login':'''@startuml
actor 사용자 as U
participant TransactionScreen as T
participant LoginScreen as L
participant AccountManager as M
participant VirtualAccount as A
participant ScreenData as S
U -> T : 로그인요청 OP-01
T -> L : 비밀번호형식확인 OP-09
L --> T : 형식 검사 결과
alt 형식 유효
 T -> M : 로그인확인 OP-31
 M -> A : 거래차단여부확인 OP-44
 alt 미차단
  M -> A : 비밀번호일치확인 OP-37
  alt 일치
   M -> A : 오류횟수초기화 OP-42
   M --> T : SUCCESS
   T -> S : 계좌번호저장 OP-24
   T -> T : 화면잔액갱신 OP-07
  else 불일치
   M -> A : 오류횟수늘리기 OP-41
   opt 5회째
    M -> A : 계좌거래차단 OP-43
   end
   M --> T : INVALID_CREDENTIALS / ACCOUNT_BLOCKED
  end
 else 이미 차단
  M --> T : ACCOUNT_BLOCKED
 end
else 형식 오류
 T -> L : 로그인경고표시 OP-10
end
T --> U : 결과 화면
@enduml''',
    'sequence_transaction':'''@startuml
actor 사용자 as U
participant TransactionScreen as T
participant AccountManager as M
participant VirtualAccount as A
participant ScreenData as S
U -> T : 거래요청 OP-03/04/05
T -> T : 인증·형식·한도 검사
alt 유효
 T -> M : 입금처리/출금처리/가상이체처리 OP-33/34/35
 M -> M : 계좌·차단·업무 규칙 재검사
 alt 승인
  M -> A : 잔액더하기/잔액빼기 OP-39/40
  M --> T : true
  T -> M : 계좌잔액조회 OP-32
  M --> T : 현재 잔액
  T -> S : 표시잔액저장 OP-26
 else 거절
  M --> T : false (잔액 무변경)
 end
else 입력 오류
 T -> T : 결과 안내 (잔액 무변경)
end
T --> U : 결과·계속 이용·종료
@enduml'''}
    for n,s in sources.items():(OUT/(n+'.puml')).write_text(s,encoding='utf-8')

if __name__=='__main__':
    architecture();usecase();activity_login();activity_transaction();state();class_diagram();sequence('sequence_login',True);sequence('sequence_transaction');extra_sources()
    print('8 PNG + 8 SVG + 7 PlantUML sources generated')
