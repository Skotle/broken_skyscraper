import math
import pygame as pg
from src.simulation.actions import attack_box

BG = (12, 18, 27)
PANEL = (20, 29, 41)
LINE = (43, 57, 73)
TEXT = (232, 239, 240)
MUTED = (143, 161, 175)
ACCENT = (195, 243, 111)
COLORS = [(109, 209, 237), (255, 161, 120)]
STATE_NAMES = {"Neutral":"준비", "AttackStartup":"공격 준비", "AttackActive":"밀치기", "AttackRecovery":"공격 후딜", "Dodge":"회피", "Hitstun":"피격 경직", "Eliminated":"탈락"}
REASONS = {"fall":"최하단 추락", "hazard":"하얀 막 · 체력 소진", "fall+hazard":"추락 및 체력 소진", "height":"시간 종료 · 높이 우위", "health":"높이 동률 · 체력 우위", "simultaneous":"동시 탈락", "tie":"높이와 체력 동률"}


class Renderer:
    def __init__(self):
        self.canvas = pg.Surface((1280, 800))
        self.fonts = {}
        self.font_path = pg.font.match_font("malgungothic,malgun gothic,notosanscjkkr,arial")
        self.view = pg.Rect(28, 175, 914, 535)
        self.scale = 40
        self.cx, self.cy = 0, 4.3
        self.buttons = {}
        self.last_hit = -100

    def text(self, text, x, y, size=18, color=TEXT):
        if size not in self.fonts:
            self.fonts[size] = pg.font.Font(self.font_path, size)
        self.canvas.blit(self.fonts[size].render(str(text), True, color), (x, y))

    def box(self, rect, color=PANEL, border=0):
        pg.draw.rect(self.canvas, color, rect, border, border_radius=12)

    def button(self, key, label, rect, active=False):
        self.buttons[key] = pg.Rect(rect)
        self.box(rect, ACCENT if active else LINE)
        self.text(label, rect[0]+14, rect[1]+9, 16, BG if active else TEXT)

    def project(self, x, y):
        return (round(self.view.centerx+(x-self.cx)*self.scale), round(self.view.centery-(y-self.cy)*self.scale))

    def unproject(self, x, y):
        return (self.cx+(x-self.view.centerx)/self.scale, self.cy-(y-self.view.centery)/self.scale)

    def world_rect(self, x, y, w, h):
        sx, sy = self.project(x, y+h)
        return pg.Rect(sx, sy, max(1, round(w*self.scale)), max(1, round(h*self.scale)))

    def draw_world(self, app):
        m = app.match
        self.canvas.set_clip(self.view)
        self.canvas.fill((15, 23, 34), self.view)
        # Fixed lab framing keeps every recovery platform visible, irrespective of combat.
        self.scale = 39
        self.cx, self.cy = 0, 4.3
        if app.devices.shake and m.tick-self.last_hit < 7:
            self.cx += math.sin(m.tick*2.4)*.045
        for x in range(-10, 11, 2):
            pg.draw.line(self.canvas, (24, 35, 48), self.project(x,-3), self.project(x,12))
        for y in range(-2, 13, 2):
            pg.draw.line(self.canvas, (24,35,48), self.project(-12,y), self.project(12,y))
            sx, sy = self.project(-10.8,y)
            self.text(f"{y:02d}",sx,sy-9,12,MUTED)
        for wall in (m.world["left"],m.world["right"]):
            pg.draw.line(self.canvas, LINE, self.project(wall,-3),self.project(wall,12),3)
        floor = self.project(0, m.world["bottom"])[1]
        pg.draw.line(self.canvas, (180, 91, 89), (self.view.left, floor), (self.view.right, floor), 2)
        self.text("추락 판정선", self.view.left+16, floor+7, 12, (212,133,129))
        for f in m.world["platforms"]:
            rect = self.world_rect(f["x"]-f["width"]/2, f["y"]-.2, f["width"], .2)
            pg.draw.rect(self.canvas,(55,73,86),rect,border_radius=3)
            pg.draw.line(self.canvas,(161,184,185),rect.topleft,rect.topright,3)
            self.text(f["id"],rect.left+3,rect.bottom+6,12,MUTED)
        if m.world["hazardEnabled"]:
            hy = self.project(0,m.hazard_y)[1]
            veil = pg.Surface(self.view.size, pg.SRCALPHA)
            pg.draw.rect(veil,(240,246,244,35),(0,0,self.view.width,max(0,min(self.view.height,hy-self.view.top))))
            self.canvas.blit(veil,self.view)
            pg.draw.line(self.canvas,TEXT,(self.view.left,hy),(self.view.right,hy),2)
        for i,p in enumerate(m.players):
            color = COLORS[i]
            rect = self.world_rect(p.x-.4,p.y,.8,1.6)
            if p.action == "AttackStartup":
                rect.inflate_ip(5,-10)
                rect.y += 10
            pg.draw.rect(self.canvas,color if p.action!="Hitstun" else TEXT,rect,border_radius=7)
            eye = rect.centerx+int(p.facing*rect.width*.23)
            pg.draw.circle(self.canvas,BG,(eye,rect.top+12),3)
            self.text(f"P{p.id}",rect.centerx-12,rect.top-25,15,color)
            if p.action == "Dodge":
                inv = p.age < m.config["dodgeInvulnerableTicks"]
                pg.draw.rect(self.canvas,TEXT if inv else (179,123,101),rect.inflate(12,12),3 if inv else 1,border_radius=10)
            if p.action.startswith("Attack"):
                x,y,w,h = attack_box(p,m.config)
                attack = self.world_rect(x,y,w,h)
                pg.draw.rect(self.canvas,ACCENT if p.action=="AttackActive" else color,attack,3 if p.action=="AttackActive" else 1,border_radius=6)
            if app.debug:
                pg.draw.rect(self.canvas,TEXT,self.world_rect(p.x-.4,p.y,.8,1.6),1)
                pg.draw.circle(self.canvas,ACCENT,self.project(p.x,p.y),3)
        self.canvas.set_clip(None)
        self.box(self.view,LINE,1)

    def draw(self, app):
        self.buttons = {}
        m = app.match
        self.canvas.fill(BG)
        self.text("BROKEN SKYSCRAPER",28,20,13,ACCENT)
        self.text("부서진 마천루",27,40,32)
        self.text("COMBAT LAB  /  01",1020,29,16,MUTED)
        self.text("5개 발판 · 통과 실험 A",1020,56,14,MUTED)
        for i,p in enumerate(m.players):
            x = 28 if i==0 else 656
            self.box((x,95,596,64))
            self.text(f"P{p.id}",x+16,108,24,COLORS[i])
            self.text(f"체력 {math.ceil(p.health/10)}",x+71,105,17)
            self.text("회피 준비" if m.tick>=p.dodge_ready else f"회피 {(p.dodge_ready-m.tick)/60:.1f}s",x+390,106,15,ACCENT if m.tick>=p.dodge_ready else MUTED)
            pg.draw.rect(self.canvas,LINE,(x+71,136,490,5),border_radius=2)
            pg.draw.rect(self.canvas,COLORS[i],(x+71,136,round(490*p.health/m.rules["healthUnits"]),5),border_radius=2)
            self.text(STATE_NAMES[p.action],x+200,107,15,MUTED)
        self.draw_world(app)
        self.box((958,175,294,535))
        self.text("전투 실험",978,193,22)
        self.text("막 비활성 · 120초",978,226,14,MUTED)
        seconds = math.ceil(m.remaining/60)
        self.text(f"{seconds//60:02d}:{seconds%60:02d}",978,251,36,ACCENT)
        self.button("restart","재시작  R",(978,312,254,40))
        self.button("pause","계속하기  ESC" if m.paused else "일시정지  ESC",(978,361,254,40),m.paused)
        self.button("mirror",f"좌우 반전  F3   {'ON' if app.mirror else 'OFF'}",(978,419,254,37))
        self.button("moving",f"P2 이동 시작  F4   {'ON' if app.moving else 'OFF'}",(978,464,254,37))
        bots = ["사람 조작","정지 표적","밀치기 반복","중앙 복귀"]
        self.button("bot",f"P2 · {bots[app.bot]}  F5",(978,509,254,37))
        self.text(f"게임패드 {app.devices.connected_count}/2 연결",978,564,14,MUTED)
        self.text("A 점프 · X 밀치기 · B 회피",978,590,14,MUTED)
        self.text("↓ + A 발판 내려가기",978,615,14,MUTED)
        self.text("F1 판정 보기 · F2 키 변경",978,659,14,ACCENT)
        self.text("P1",28,730,16,COLORS[0])
        self.text(self.controls(app,0),65,730,14)
        self.text("P2",28,758,16,COLORS[1])
        self.text(self.controls(app,1),65,758,14)
        self.text("F7 기록 저장   F8 기록 재생",950,730,14,MUTED)
        self.text("F10 음소거   F11 흔들림",950,758,14,MUTED)
        if app.debug:
            self.box((43,190,424,150),(15,23,34))
            self.text(f"TICK {m.tick}  ·  적체 {app.backlog}  ·  {app.fps:.0f} FPS",55,199,13,ACCENT)
            for i,p in enumerate(m.players):
                self.text(f"P{p.id}  ({p.x:.3f}, {p.y:.3f})  v=({p.vx:.2f},{p.vy:.2f})",55,224+i*43,13)
                self.text(f"{p.action} [{p.age}]  지지 {p.support or '-'}",55,244+i*43,12,MUTED)
            self.text("정지 중 N: 1틱 / 클릭: P1 이동 / Shift+클릭: P2",55,314,12,MUTED)
        if m.phase=="Countdown":
            self.overlay(str(math.ceil(m.countdown/60)),"이동 · 점프 · 밀치기 · 회피",small=True)
        elif m.result:
            title = "무승부" if m.result["winner"] is None else f"P{m.result['winner']} 승리"
            self.overlay(title,REASONS.get(m.result["reason"],m.result["reason"])+"  ·  R 재경기")
        elif m.paused:
            self.overlay("일시정지",app.pause_reason or "ESC 계속하기 · R 재시작",small=app.debug)
        if app.playback is not None:
            self.text("입력 기록 재생 중",650,186,16,ACCENT)
        if app.toast and pg.time.get_ticks()<app.toast_until:
            self.box((240,663,630,36),LINE)
            self.text(app.toast[:65],254,670,14,TEXT)
        if app.rebind is not None:
            i,key = app.rebind
            self.overlay(f"P{i+1} · {key}","새 키를 누르세요 · ESC 취소 (총 12개 행동)")
        return self.canvas

    def controls(self, app, index):
        b = app.devices.bindings[index]
        return f"{b['left'].upper()}/{b['right'].upper()} 이동   {b['jump'].upper()} 점프   {b['down'].upper()}+점프 하강   {b['attack'].upper()} 밀치기   {b['dodge'].upper()} 회피"

    def overlay(self, title, subtitle, small=False):
        rect = (240,385,490,116 if small else 150)
        shade = pg.Surface((rect[2],rect[3]),pg.SRCALPHA)
        shade.fill((10,17,25,238))
        self.canvas.blit(shade,rect[:2])
        self.text(title,rect[0]+25,rect[1]+16,32,ACCENT)
        self.text(subtitle,rect[0]+25,rect[1]+76,15)
