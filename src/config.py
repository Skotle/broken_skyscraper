"""Validated, immutable-per-match data loading. No pygame dependency."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_config(root=ROOT):
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    rules, player, world = read("config/ruleset.json"), read("config/player.json"), read("maps/combat_lab.json")
    validate(rules, player, world)
    return rules, player, world


def validate(r, p, w):
    if r["tickRate"] != 60 or r["matchTicks"] <= 0 or r["countdownTicks"] < 0:
        raise ValueError("ruleset: tickRate must be 60; invalid match/countdown length")
    if not 0 < r["collisionEpsilon"] < .01 or r["healthUnits"] <= 0:
        raise ValueError("ruleset: invalid collisionEpsilon or healthUnits")
    keys = r["hazardKeyframes"]
    if len(keys) < 2 or keys[0][0] != 0 or keys[-1][0] != r["matchTicks"]:
        raise ValueError("hazardKeyframes: must cover the entire match")
    if any(b[0] <= a[0] or b[1] > a[1] for a, b in zip(keys, keys[1:])):
        raise ValueError("hazardKeyframes: time must increase and height must not increase")
    if p["attackTotal"] != sum(p[k] for k in ("attackStartup", "attackActive", "attackRecovery")):
        raise ValueError("player.attackTotal: phase lengths do not add up")
    if any(p[k] <= 0 for k in p if k != "dropVelocity") or p["dropVelocity"] >= 0:
        raise ValueError("player: positive parameters and negative dropVelocity required")
    if not p["dodgeInvulnerableTicks"] <= p["dodgeTicks"] <= p["dodgeCooldown"]:
        raise ValueError("player: invalid dodge timing")
    ids = [f["id"] for f in w["platforms"]]
    if len(ids) != len(set(ids)):
        raise ValueError("map: duplicate platform ID")
    if w["right"] <= w["left"] or not w["platforms"]:
        raise ValueError("map: invalid bounds or no platforms")
    for f in w["platforms"]:
        if f["width"] <= 0 or f["y"] <= w["bottom"]:
            raise ValueError(f"map.{f['id']}: invalid platform dimensions")
        if f["x"]-f["width"]/2 < w["left"] or f["x"]+f["width"]/2 > w["right"]:
            raise ValueError(f"map.{f['id']}: outside horizontal bounds")
    if len(w["spawns"]) != 2:
        raise ValueError("map: exactly two spawns required")
    for s in w["spawns"]:
        if not w["left"]+p["width"]/2 <= s["x"] <= w["right"]-p["width"]/2:
            raise ValueError("map: spawn outside walls")
        if s["facing"] not in (-1, 1) or not any(abs(s["y"]-f["y"]) < 1e-8 and abs(s["x"]-f["x"]) < (p["width"]+f["width"])/2 for f in w["platforms"]):
            raise ValueError("map: spawn must be supported with valid facing")
