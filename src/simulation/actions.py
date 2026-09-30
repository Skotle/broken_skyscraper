def begin_actions(p, inp, tick, cfg):
    if p.action == "Hitstun" and tick >= p.hitstun_until:
        p.action, p.age = "Neutral", 0
    if p.action != "Neutral":
        return
    if inp.move:
        p.facing = 1 if inp.move > 0 else -1
    if inp.dodge and tick >= p.dodge_ready:
        p.action, p.age = "Dodge", 0
        p.dodge_ready = tick+cfg["dodgeCooldown"]
        p.buffer_expires = 0
        return
    if inp.drop and p.support is not None:
        p.ignored, p.support = p.support, None
        p.vy = cfg["dropVelocity"]
        p.coyote_expires = p.buffer_expires = 0
        return
    jump_request = inp.jump or tick < p.buffer_expires
    if jump_request and (p.support is not None or tick < p.coyote_expires):
        p.vy, p.support = cfg["jumpVelocity"], None
        p.buffer_expires = p.coyote_expires = 0
    elif inp.jump:
        p.buffer_expires = tick+cfg["jumpBufferTicks"]
    if inp.attack:
        p.action, p.age = "AttackStartup", 0
        p.attack_facing = p.facing
        p.attack_sequence += 1
        p.hit_targets = []
        p.buffer_expires = 0


def advance_action(p, cfg):
    if p.action.startswith("Attack"):
        p.age += 1
        if p.age >= cfg["attackTotal"]:
            p.action, p.age = "Neutral", 0
        elif p.age >= cfg["attackStartup"]+cfg["attackActive"]:
            p.action = "AttackRecovery"
        elif p.age >= cfg["attackStartup"]:
            p.action = "AttackActive"
    elif p.action == "Dodge":
        p.age += 1
        if p.age >= cfg["dodgeTicks"]:
            p.action, p.age = "Neutral", 0


def attack_box(p, cfg):
    x, y = p.x+p.attack_facing*cfg["attackOffsetX"], p.y+cfg["attackOffsetY"]
    return x-cfg["attackWidth"]/2, y-cfg["attackHeight"]/2, cfg["attackWidth"], cfg["attackHeight"]


def collect_hits(players, cfg):
    hits = []
    for a in players:
        if a.action != "AttackActive" or a.eliminated:
            continue
        x, y, w, h = attack_box(a, cfg)
        for b in players:
            if a.id == b.id or b.eliminated or b.id in a.hit_targets:
                continue
            if b.action == "Dodge" and b.age < cfg["dodgeInvulnerableTicks"]:
                continue
            if x < b.x+cfg["width"]/2 and x+w > b.x-cfg["width"]/2 and y < b.y+cfg["height"] and y+h > b.y:
                hits.append((a.id, b.id, a.attack_sequence, a.attack_facing))
    return hits


def apply_hits(players, hits, tick, cfg):
    by_id = {p.id: p for p in players}
    events = []
    for aid, bid, seq, facing in hits:
        a, b = by_id[aid], by_id[bid]
        a.hit_targets.append(bid)
        b.vx, b.vy = facing*cfg["knockbackX"], max(b.vy, cfg["knockbackY"])
        b.support = None
        b.coyote_expires = b.buffer_expires = 0
        b.action, b.age = "Hitstun", 0
        b.hitstun_until = tick+cfg["hitstunTicks"]+1
        events.append({"type":"hit", "tick":tick, "attacker":aid, "target":bid, "attackId":f"{aid}:{seq}", "position":[b.x,b.y]})
    return events
