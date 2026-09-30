import argparse
from array import array
from copy import deepcopy
import math
import os
from pathlib import Path
import sys

from src.config import load_config
from src.simulation import Match, InputFrame
from src.replay import Recorder, restore, verify, read
from src.storage import atomic_json, data_dir


class App:
    def __init__(self, smoke=False):
        import pygame as pg
        from src.input.devices import Devices
        from src.presentation.screen import Renderer
        self.pg = pg
        pg.mixer.pre_init(44100,-16,1,512)
        pg.init()
        self.window = pg.display.set_mode((1280,800), pg.RESIZABLE)
        pg.display.set_caption("부서진 마천루 · 전투 실험실")
        self.devices, self.renderer = Devices(), Renderer()
        self.mirror, self.moving, self.bot, self.debug = False, False, 0, False
        self.rebind, self.rebind_original = None, None
        self.playback, self.playback_index, self.last_saved = None, 0, None
        self.pause_reason, self.toast, self.toast_until = "", "", 0
        self.fps, self.backlog, self.accumulator = 0, 0, 0.0
        self.running, self.smoke = True, smoke
        self.sound = None
        if pg.mixer.get_init():
            samples = array('h',(int(8000*math.sin(2*math.pi*(220+600*(1-n/4000))*n/44100)*(1-n/4000)) for n in range(4000)))
            self.sound = pg.mixer.Sound(buffer=samples)
        self.restart()
        if self.devices.notice:
            self.notify(self.devices.notice)

    def notify(self, text):
        self.toast, self.toast_until = text, self.pg.time.get_ticks()+5000

    def restart(self):
        self.match = Match(*load_config(), mirror=self.mirror, moving=self.moving)
        self.recorder = Recorder(self.match, {"experiment":"combat-A", "mirror":self.mirror, "moving":self.moving, "bot":self.bot, "humanValidated":False})
        self.devices.clear()
        self.playback = None
        self.renderer.last_hit = -100
        self.pause_reason = ""
        self.accumulator = 0

    def toggle_pause(self, reason=""):
        self.match.paused = not self.match.paused
        self.pause_reason = reason if self.match.paused else ""
        self.devices.discard_edges()
        self.accumulator = 0

    def command(self, command):
        if command == "restart":
            self.restart()
        elif command == "pause":
            self.toggle_pause()
        elif command in ("mirror","moving","bot"):
            if command == "bot":
                self.bot = (self.bot+1)%4
            else:
                setattr(self,command,not getattr(self,command))
            self.restart()

    def screen_position(self, position):
        w,h = self.window.get_size()
        factor = min(w/1280,h/800)
        return ((position[0]-(w-1280*factor)/2)/factor,(position[1]-(h-800*factor)/2)/factor)

    def events(self):
        pg = self.pg
        for event in pg.event.get():
            self.devices.event(event)
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.WINDOWFOCUSLOST and not self.smoke:
                self.match.paused = True
                self.pause_reason = "창을 벗어나 일시정지했습니다 · ESC 계속하기"
            if event.type in (pg.CONTROLLERDEVICEADDED,pg.CONTROLLERDEVICEREMOVED,pg.JOYDEVICEADDED,pg.JOYDEVICEREMOVED):
                if self.devices.refresh():
                    self.match.paused = True
                    self.pause_reason = "게임패드 연결 해제 · 재연결 후 ESC / START"
                    self.devices.clear()
            if event.type == pg.KEYDOWN:
                if self.rebind is not None:
                    self.remap_key(event.key)
                    continue
                commands = {pg.K_r:"restart",pg.K_ESCAPE:"pause",pg.K_F3:"mirror",pg.K_F4:"moving",pg.K_F5:"bot"}
                if event.key in commands:
                    self.command(commands[event.key])
                elif event.key == pg.K_F1:
                    self.debug = not self.debug
                elif event.key == pg.K_F2:
                    self.rebind, self.rebind_original = (0,"left"), deepcopy(self.devices.bindings)
                    self.match.paused = True
                elif event.key == pg.K_F7:
                    self.last_saved = self.recorder.save()
                    self.notify("입력 기록 저장 완료 · F8 재생")
                elif event.key == pg.K_F8 and self.last_saved:
                    record = read(self.last_saved)
                    checked = verify(record)
                    if checked["ok"]:
                        self.playback, self.playback_index = record, 0
                        self.match = restore(record)
                        self.renderer.last_hit = -100
                        self.devices.clear()
                        self.accumulator = 0
                        self.notify("기록 검증 통과 · 재생 시작")
                    else:
                        self.notify("기록 불일치: "+str(checked))
                elif event.key == pg.K_F10:
                    self.devices.volume = 0 if self.devices.volume else .25
                    self.devices.save()
                    self.notify("음소거" if not self.devices.volume else "효과음 켜짐")
                elif event.key == pg.K_F11:
                    self.devices.shake = not self.devices.shake
                    self.devices.save()
                    self.notify("화면 흔들림 "+("켜짐" if self.devices.shake else "꺼짐"))
                elif event.key == pg.K_n and self.debug and self.match.paused:
                    self.match.paused = False
                    self.step()
                    self.match.paused = True
                elif event.key in (pg.K_1,pg.K_2) and self.debug and self.match.paused and self.playback is None:
                    p = self.match.players[0 if event.key==pg.K_1 else 1]
                    p.health = max(10,p.health-100)
                    self.new_debug_record()
            if event.type == pg.MOUSEBUTTONDOWN and event.button==1 and self.rebind is None:
                pos = self.screen_position(event.pos)
                button = next((key for key,rect in self.renderer.buttons.items() if rect.collidepoint(pos)),None)
                if button:
                    self.command(button)
                elif self.debug and self.match.paused and self.renderer.view.collidepoint(pos) and self.playback is None:
                    p = self.match.players[1 if pg.key.get_mods() & pg.KMOD_SHIFT else 0]
                    p.x,p.y = self.renderer.unproject(*pos)
                    p.x = max(self.match.world['left']+.4,min(self.match.world['right']-.4,p.x))
                    p.vx = p.vy = 0
                    p.support = p.ignored = None
                    p.action,p.age = "Neutral",0
                    p.buffer_expires = p.coyote_expires = p.hitstun_until = 0
                    self.new_debug_record()
        self.devices.poll()
        if self.devices.pause_pressed():
            self.toggle_pause()

    def new_debug_record(self):
        self.recorder = Recorder(self.match,{"experiment":"debug-edited", "humanValidated":False})
        self.notify("디버그 상태에서 새 기록 시작 · 1/2: 해당 체력 -10")

    def remap_key(self,key):
        pg = self.pg
        if key == pg.K_ESCAPE:
            self.devices.bindings = self.rebind_original
            self.rebind = None
            self.devices.clear()
            return
        reserved = {pg.K_r,pg.K_n,pg.K_1,pg.K_2,*range(pg.K_F1,pg.K_F12+1)}
        if key in reserved:
            self.notify("메뉴·디버그용 키는 사용할 수 없습니다.")
            return
        i,action = self.rebind
        name = pg.key.name(key)
        # Already assigned keys in this remapping session cannot overlap.
        sequence = [(slot,a) for slot in range(2) for a in ("left","right","down","jump","attack","dodge")]
        index = sequence.index(self.rebind)
        if any(self.devices.bindings[s][a] == name for s,a in sequence[:index]):
            self.notify("앞에서 지정한 키와 겹칩니다. 다른 키를 선택하세요.")
            return
        self.devices.bindings[i][action] = name
        self.devices.clear()
        if index == len(sequence)-1:
            self.rebind = None
            self.devices.save()
            self.notify("두 플레이어의 키 설정을 저장했습니다.")
        else:
            self.rebind = sequence[index+1]

    def step(self):
        if self.match.phase == "Result":
            return
        if self.playback is not None:
            if self.playback_index >= len(self.playback["frames"]):
                self.match.paused = True
                self.pause_reason = "재생 완료 · R 새 경기"
                return
            frames = [InputFrame(**v) for v in self.playback["frames"][self.playback_index]]
            self.playback_index += 1
        else:
            frames = self.devices.consume()
            if self.bot:
                p = self.match.players[1]
                move = -1 if p.x>.3 else 1 if p.x<-.3 else 0
                frames[1] = InputFrame(move=move if self.bot==3 else 0,attack=self.bot==2 and self.match.tick%40==0)
        self.match.step(frames)
        if self.playback is None:
            self.recorder.append(frames,self.match)
        if any(e["type"]=="hit" for e in self.match.events):
            self.renderer.last_hit = self.match.tick
            if self.sound:
                self.sound.set_volume(self.devices.volume)
                self.sound.play()
        if self.match.result and self.playback is None:
            self.last_saved = self.recorder.save()
            self.notify("경기 결과와 입력 기록을 자동 저장했습니다.")

    def run(self, smoke_frames=0, screenshot=None):
        pg = self.pg
        clock = pg.time.Clock()
        frames = 0
        while self.running:
            elapsed = clock.tick(144)/1000
            self.events()
            if self.match.paused or self.rebind is not None:
                self.accumulator = 0
                self.devices.discard_edges()
            else:
                self.accumulator += 1/60 if self.smoke else elapsed
                steps = 0
                while self.accumulator+1e-12 >= 1/60 and steps < 240 and not self.match.paused:
                    self.step()
                    self.accumulator -= 1/60
                    steps += 1
                self.backlog = max(0,int(self.accumulator*60))
            self.fps = clock.get_fps()
            canvas = self.renderer.draw(self)
            w,h = self.window.get_size()
            factor = min(w/1280,h/800)
            size = (round(1280*factor),round(800*factor))
            self.window.fill((7,11,17))
            self.window.blit(pg.transform.smoothscale(canvas,size),((w-size[0])//2,(h-size[1])//2))
            pg.display.flip()
            frames += 1
            if smoke_frames and frames>=smoke_frames:
                if screenshot:
                    Path(screenshot).parent.mkdir(parents=True,exist_ok=True)
                    pg.image.save(canvas,screenshot)
                output = {"frames":frames,"tick":self.match.tick,"phase":self.match.phase,"players":[p.snapshot() for p in self.match.players],"replay":verify(self.recorder.record)}
                if screenshot:
                    atomic_json(Path(screenshot).with_suffix('.json'),output)
                self.running = False
        if self.recorder.record["frames"] and self.playback is None and not self.smoke:
            self.recorder.save()
        pg.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke",type=int,default=0,metavar="FRAMES")
    parser.add_argument("--screenshot")
    parser.add_argument("--verify-replay")
    args = parser.parse_args()
    if args.verify_replay:
        result = verify(read(args.verify_replay))
        print(result)
        return 0 if result['ok'] else 1
    if args.smoke:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    try:
        App(smoke=bool(args.smoke)).run(args.smoke,args.screenshot)
    except Exception:
        import traceback
        path = data_dir()/"last-error.txt"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(traceback.format_exc(),encoding="utf-8")
        if not args.smoke:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0,f"실행 중 오류가 발생했습니다.\n{path}","부서진 마천루",0x10)
        raise
    return 0
