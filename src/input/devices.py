import json
from copy import deepcopy
import pygame as pg
from pygame._sdl2 import controller
from src.simulation.model import InputFrame
from src.storage import data_dir, atomic_json

DEFAULT_BINDINGS = [
    {"left":"a", "right":"d", "down":"s", "jump":"w", "attack":"f", "dodge":"g"},
    {"left":"left", "right":"right", "down":"down", "jump":"up", "attack":"k", "dodge":"l"},
]


class Devices:
    def __init__(self):
        controller.init()
        self.settings_path = data_dir()/"settings.json"
        self.notice = ""
        self.bindings = deepcopy(DEFAULT_BINDINGS)
        self.volume, self.shake = .25, True
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            bindings = data["bindings"]
            if len(bindings) != 2 or any(set(b) != set(DEFAULT_BINDINGS[0]) for b in bindings):
                raise ValueError("Invalid bindings")
            for b in bindings:
                for name in b.values():
                    pg.key.key_code(name)
            self.bindings = bindings
            self.volume = max(0, min(1, float(data.get("volume", .25))))
            self.shake = bool(data.get("shake", True))
        except FileNotFoundError:
            pass
        except (ValueError, KeyError, TypeError, OSError):
            self.notice = "설정 파일을 읽을 수 없어 기본 조작으로 복구했습니다."
        self.held, self.pressed = set(), set()
        self.pads = [None, None]
        self.pad_previous = [set(), set()]
        self.pad_pending = [set(), set()]
        self.connected_count = 0
        self.refresh()

    def save(self):
        atomic_json(self.settings_path, {"bindings":self.bindings, "volume":self.volume, "shake":self.shake})

    def refresh(self):
        lost = False
        for i, pad in enumerate(self.pads):
            if pad is not None and not pad.attached():
                pad.quit()
                self.pads[i] = None
                self.pad_previous[i].clear()
                self.pad_pending[i].clear()
                lost = True
        known = {p.id for p in self.pads if p is not None}
        for index in range(controller.get_count()):
            if not controller.is_controller(index):
                continue
            pad = controller.Controller(index)
            if pad.id in known:
                continue
            if None in self.pads:
                slot = self.pads.index(None)
                self.pads[slot] = pad
                known.add(pad.id)
        self.connected_count = sum(p is not None for p in self.pads)
        return lost

    def event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key not in self.held:
                self.pressed.add(event.key)
            self.held.add(event.key)
        elif event.type == pg.KEYUP:
            self.held.discard(event.key)
        elif event.type == pg.WINDOWFOCUSLOST:
            self.clear()

    def poll(self):
        for i, pad in enumerate(self.pads):
            if pad is None or not pad.attached():
                continue
            now = {b for b in (pg.CONTROLLER_BUTTON_A, pg.CONTROLLER_BUTTON_X, pg.CONTROLLER_BUTTON_B, pg.CONTROLLER_BUTTON_START) if pad.get_button(b)}
            self.pad_pending[i] |= now-self.pad_previous[i]
            self.pad_previous[i] = now

    def pause_pressed(self):
        pressed = any(pg.CONTROLLER_BUTTON_START in s for s in self.pad_pending)
        for s in self.pad_pending:
            s.discard(pg.CONTROLLER_BUTTON_START)
        return pressed

    def consume(self):
        frames = []
        for i, binding in enumerate(self.bindings):
            keys = {k:pg.key.key_code(v) for k,v in binding.items()}
            move = float((keys["right"] in self.held)-(keys["left"] in self.held))
            down = keys["down"] in self.held
            jump = keys["jump"] in self.pressed
            attack, dodge = keys["attack"] in self.pressed, keys["dodge"] in self.pressed
            pad = self.pads[i]
            if pad is not None and pad.attached():
                raw = pad.get_axis(pg.CONTROLLER_AXIS_LEFTX)/32767
                axis = 0 if abs(raw) < .18 else (abs(raw)-.18)/.82*(1 if raw > 0 else -1)
                digital = int(pad.get_button(pg.CONTROLLER_BUTTON_DPAD_RIGHT))-int(pad.get_button(pg.CONTROLLER_BUTTON_DPAD_LEFT))
                if axis or digital:
                    move = max(-1, min(1, digital if digital else axis))
                down |= bool(pad.get_button(pg.CONTROLLER_BUTTON_DPAD_DOWN)) or pad.get_axis(pg.CONTROLLER_AXIS_LEFTY) > 16000
                jump |= pg.CONTROLLER_BUTTON_A in self.pad_pending[i]
                attack |= pg.CONTROLLER_BUTTON_X in self.pad_pending[i]
                dodge |= pg.CONTROLLER_BUTTON_B in self.pad_pending[i]
            frames.append(InputFrame(move, jump and not down, jump and down, attack, dodge))
        self.pressed.clear()
        for pending in self.pad_pending:
            pending.clear()
        return frames

    def clear(self):
        self.held.clear()
        self.pressed.clear()
        for s in self.pad_pending:
            s.clear()

    def discard_edges(self):
        self.pressed.clear()
        for s in self.pad_pending:
            s.clear()
