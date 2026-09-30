from copy import deepcopy
from .model import Player, InputFrame
from .motor import move_player, overlap
from .actions import begin_actions, advance_action, collect_hits, apply_hits
from src.config import digest


def hazard_at(tick, keys):
    for a, b in zip(keys, keys[1:]):
        if tick <= b[0]:
            return a[1]+(b[1]-a[1])*(tick-a[0])/(b[0]-a[0])
    return keys[-1][1]


def evaluate_result(players, remaining, tolerance):
    dead = [p for p in players if p.eliminated]
    if len(dead) == 2:
        return {"winner":None, "reason":"simultaneous"}
    if len(dead) == 1:
        return {"winner":next(p.id for p in players if not p.eliminated), "reason":"+".join(dead[0].reasons)}
    if remaining > 0:
        return None
    a, b = players
    if abs(a.y-b.y) > tolerance+1e-10:
        return {"winner": a.id if a.y > b.y else b.id, "reason":"height"}
    if a.health != b.health:
        return {"winner":a.id if a.health > b.health else b.id, "reason":"health"}
    return {"winner":None, "reason":"tie"}


class Match:
    def __init__(self, rules, config, world, countdown=True, mirror=False, moving=False):
        self.rules, self.config, self.world = deepcopy(rules), deepcopy(config), deepcopy(world)
        self.tick, self.remaining = 0, rules["matchTicks"]
        self.countdown = rules["countdownTicks"] if countdown else 0
        self.phase = "Countdown" if self.countdown else "Playing"
        self.paused, self.result = False, None
        self.hazard_y = hazard_at(0, rules["hazardKeyframes"])
        self.events = []
        self.players = []
        self.rules_hash = digest([rules, config])
        self.map_hash = digest(world)
        for i, s in enumerate(world["spawns"]):
            sign = -1 if mirror else 1
            p = Player(i+1, s["x"]*sign, s["y"], s["facing"]*sign, health=rules["healthUnits"])
            p.attack_facing = p.facing
            p.support = next((f["id"] for f in world["platforms"] if abs(f["y"]-p.y)<1e-8 and overlap(p.x,config["width"]/2,f)>rules["collisionEpsilon"]), None)
            if moving and i == 1:
                p.vx = -6*sign
            self.players.append(p)

    def step(self, inputs=None):
        self.events = []
        if self.paused or self.phase == "Result":
            return
        if self.phase == "Countdown":
            self.countdown -= 1
            if self.countdown <= 0:
                self.phase = "Playing"
            return
        inputs = inputs or [InputFrame(), InputFrame()]
        if len(inputs) != 2:
            raise ValueError("Exactly two input slots required")
        for p, inp in zip(self.players, inputs):
            begin_actions(p, inp, self.tick, self.config)
            move_player(p, inp, self.world, self.config, self.rules["collisionEpsilon"], self.tick)
        hits = collect_hits(self.players, self.config)
        self.events = apply_hits(self.players, hits, self.tick, self.config)
        self.hazard_y = hazard_at(self.tick+1, self.rules["hazardKeyframes"])
        for p in self.players:
            if self.world["hazardEnabled"] and p.y > self.hazard_y:
                p.health = max(0, p.health-self.rules["hazardDamageUnits"])
            p.reasons = (["fall"] if p.y <= self.world["bottom"] else []) + (["hazard"] if p.health == 0 else [])
            p.eliminated = bool(p.reasons)
            if p.eliminated:
                p.action = "Eliminated"
        self.remaining -= 1
        self.result = evaluate_result(self.players, self.remaining, self.rules["heightTieTolerance"])
        if self.result:
            self.result.update(finalTick=self.tick, heights=[p.y for p in self.players], health=[p.health for p in self.players], reasons=[p.reasons for p in self.players])
            self.phase = "Result"
            self.events.append({"type":"result", "tick":self.tick, **self.result})
        else:
            for p in self.players:
                advance_action(p, self.config)
        self.tick += 1

    def snapshot(self):
        return {"tick":self.tick, "remaining":self.remaining, "countdown":self.countdown, "phase":self.phase, "hazardY":self.hazard_y, "players":[p.snapshot() for p in self.players], "result":deepcopy(self.result)}
