from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class InputFrame:
    move: float = 0.0
    jump: bool = False
    drop: bool = False
    attack: bool = False
    dodge: bool = False


@dataclass
class Player:
    id: int
    x: float
    y: float
    facing: int
    vx: float = 0.0
    vy: float = 0.0
    support: str | None = None
    ignored: str | None = None
    action: str = "Neutral"
    age: int = 0
    dodge_ready: int = 0
    hitstun_until: int = 0
    coyote_expires: int = 0
    buffer_expires: int = 0
    health: int = 1000
    attack_sequence: int = 0
    attack_facing: int = 1
    hit_targets: list = field(default_factory=list)
    eliminated: bool = False
    reasons: list = field(default_factory=list)

    def snapshot(self):
        return asdict(self)
