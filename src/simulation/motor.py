"""Swept one-way collision at crossing time, including remaining-time motion."""
import math


def overlap(x, half, platform):
    return min(x+half, platform["x"]+platform["width"]/2) - max(x-half, platform["x"]-platform["width"]/2)


def landing_candidate(start, end, platform, half=.4, epsilon=.00001):
    x0, y0 = start
    x1, y1 = end
    h = platform["y"]
    if not y1 < y0 or not y0 >= h >= y1:
        return None
    alpha = (y0-h)/(y0-y1)
    x = x0+alpha*(x1-x0)
    return (alpha, x) if overlap(x, half, platform) > epsilon else None


def towards(value, target, amount):
    return value + max(-amount, min(amount, target-value))


def move_player(p, inp, world, cfg, epsilon, tick):
    dt = 1/60
    half = cfg["width"]/2
    platforms = {f["id"]: f for f in world["platforms"]}
    left, right = world["left"]+half, world["right"]-half
    stunned = p.action == "Hitstun"
    f = platforms.get(p.support)
    if f is None or p.vy > 0 or overlap(p.x, half, f) <= epsilon:
        p.support = None
    if p.ignored in platforms and p.y+cfg["height"] < platforms[p.ignored]["y"]:
        p.ignored = None
    if not stunned:
        target = cfg["runSpeed"] * max(-1, min(1, inp.move))
        if p.action.startswith("Attack"):
            target *= .5
        acceleration = cfg["airAcceleration"] if p.support is None else cfg["groundAcceleration"] if inp.move else cfg["groundDeceleration"]
        p.vx = towards(p.vx, target, acceleration*dt)
    remaining = dt
    # Semi-implicit Euler for free-flight velocity, then swept linear segments.
    if p.support is None:
        p.vy = max(-cfg["terminalFallSpeed"], p.vy-cfg["gravity"]*dt)
    for _ in range(32):
        if remaining <= 1e-12:
            break
        if p.x <= left and p.vx < 0 or p.x >= right and p.vx > 0:
            p.vx = 0
        wall_time = math.inf
        if p.vx:
            wall_time = max(0, ((right if p.vx > 0 else left)-p.x)/p.vx)
        if p.support:
            f = platforms[p.support]
            exit_time = math.inf
            if p.vx:
                edge = f["x"] + math.copysign(f["width"]/2+half-epsilon/2, p.vx)
                exit_time = max(0, (edge-p.x)/p.vx)
            span = min(remaining, wall_time, exit_time)
            p.x += p.vx*span
            remaining -= span
            if wall_time <= span:
                p.x = max(left, min(right, p.x))
                p.vx = 0
            elif exit_time <= span:
                p.support = None
                if not stunned:
                    p.coyote_expires = tick+cfg["coyoteTicks"]+1
                p.vy = max(-cfg["terminalFallSpeed"], -cfg["gravity"]*remaining)
            continue
        span = min(remaining, wall_time)
        end = (p.x+p.vx*span, p.y+p.vy*span)
        candidates = []
        for f in platforms.values():
            if f["id"] != p.ignored:
                hit = landing_candidate((p.x, p.y), end, f, half, epsilon)
                if hit:
                    candidates.append((hit[0], f["id"], hit[1]))
        if candidates:
            alpha, fid, cross = min(candidates)
            p.x, p.y = cross, platforms[fid]["y"]
            p.vy, p.support, p.coyote_expires = 0, fid, 0
            remaining -= span*alpha
        else:
            p.x, p.y = end
            remaining -= span
            if wall_time <= span:
                p.x = max(left, min(right, p.x))
                p.vx = 0
    else:
        raise RuntimeError("Collision iteration budget exceeded; no simulation time was discarded")
