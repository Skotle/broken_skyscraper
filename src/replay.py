"""Local bounded input logs, checkpoints and first-divergence verification."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from uuid import uuid4
from src.simulation import Match, InputFrame
from src.simulation.model import Player
from src.storage import atomic_json, data_dir
from src.config import digest


def restore(record):
    match = Match(record["rules"], record["config"], record["world"], countdown=False)
    if match.rules_hash != record["rulesetHash"] or match.map_hash != record["mapHash"]:
        raise ValueError("Replay configuration hash mismatch")
    s = record["initial"]
    match.tick, match.remaining = s["tick"], s["remaining"]
    match.countdown, match.phase = s["countdown"], s["phase"]
    match.hazard_y, match.result = s["hazardY"], deepcopy(s["result"])
    match.players = [Player(**p) for p in s["players"]]
    return match


class Recorder:
    def __init__(self, match, metadata=None):
        self.record = {"schemaVersion":1, "buildId":match.rules["buildId"], "matchId":uuid4().hex,
                       "rulesetHash":match.rules_hash, "mapHash":match.map_hash,
                       "rules":deepcopy(match.rules), "config":deepcopy(match.config), "world":deepcopy(match.world),
                       "metadata":metadata or {}, "initial":match.snapshot(), "frames":[], "events":[], "stateHashes":[], "checkpoints":{}}
        self.saved_path = None

    def append(self, frames, match):
        index = len(self.record["frames"])
        if index >= 8000:
            raise RuntimeError("Replay capacity exceeded")
        self.record["frames"].append([asdict(f) for f in frames])
        self.record["stateHashes"].append(digest(match.snapshot()))
        for j, event in enumerate(match.events):
            self.record["events"].append({**event, "eventId":f"{self.record['matchId']}:{match.tick-1}:{j}"})
        if index % 60 == 0 or match.result:
            self.record["checkpoints"][str(index)] = match.snapshot()
        self.record["final"] = match.snapshot()

    def save(self, folder=None):
        folder = Path(folder) if folder else data_dir()/"replays"
        path = folder/f"{self.record['matchId']}.json"
        atomic_json(path, self.record)
        # Only this application's UUID-shaped records, never arbitrary user files.
        files = sorted((f for f in folder.glob("*.json") if len(f.stem)==32 and all(c in '0123456789abcdef' for c in f.stem)), key=lambda p:p.stat().st_mtime)
        while len(files)>20 or sum(f.stat().st_size for f in files)>40*1024*1024 and len(files)>1:
            files.pop(0).unlink()
        self.saved_path = path
        return path


def verify(record):
    match = restore(record)
    for index, values in enumerate(record["frames"]):
        match.step([InputFrame(**v) for v in values])
        hashes = record.get("stateHashes", [])
        if hashes and hashes[index] != digest(match.snapshot()):
            return {"ok":False, "firstDivergentStep":index, "tick":match.tick}
        expected = record["checkpoints"].get(str(index))
        if expected is not None and expected != match.snapshot():
            return {"ok":False, "firstDivergentCheckpoint":index, "tick":match.tick}
    return {"ok":record.get("final", match.snapshot()) == match.snapshot(), "steps":len(record["frames"]), "tick":match.tick}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
