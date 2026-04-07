from rich.text import Text
import random
import math

# Derelict starship window — stars drifting past, occasional distant ships,
# warning lights blinking softly. A view from an abandoned bridge.

random.seed()

# ── Color helpers ──
def lc(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t), int(a[2]+(b[2]-a[2])*t))

def rgb(c):
    return f"rgb({max(0,min(255,c[0]))},{max(0,min(255,c[1]))},{max(0,min(255,c[2]))})"

# ── Window geometry ──
frame_t = 3                    # frame thickness top
frame_b = 4                    # frame thickness bottom
frame_l = 3                    # frame thickness left
frame_r = 3                    # frame thickness right
view_x0 = frame_l
view_y0 = frame_t
view_x1 = width - frame_r - 1
view_y1 = height - frame_b - 1
view_w = view_x1 - view_x0
view_h = view_y1 - view_y0

# ── Window struts (vertical dividers) — double-width ──
strut_positions = []
num_struts = max(1, view_w // 22)
for i in range(1, num_struts + 1):
    sx = view_x0 + int(view_w * i / (num_struts + 1))
    strut_positions.append(sx)

# ── Cracks on the window ──
cracks = []
num_cracks = random.randint(2, 5)
for _ in range(num_cracks):
    cx = random.randint(view_x0 + 4, view_x1 - 4)
    cy = random.randint(view_y0 + 2, view_y1 - 2)
    crack_segs = []
    ppx, ppy = cx, cy
    length = random.randint(5, 14)
    for _ in range(length):
        ddx = random.choice([-1, 0, 0, 1])
        ddy = random.choice([-1, 0, 1])
        ppx += ddx
        ppy += ddy
        if view_x0 < ppx < view_x1 and view_y0 < ppy < view_y1:
            crack_segs.append((ppx, ppy))
    cracks.append(((cx, cy), crack_segs))

# ── Stars (3 parallax layers) — increased density ──
star_layers = []
for layer in range(3):
    count = max(25, (view_w * view_h) // (18 - layer * 4))
    stars = []
    for _ in range(count):
        sx = random.uniform(0, view_w)
        sy = random.uniform(0, view_h)
        brightness = random.uniform(0.2, 1.0) if layer == 0 else random.uniform(0.4, 1.0)
        twinkle_phase = random.uniform(0, math.tau)
        if layer == 0:
            char = random.choice([".", ".", "·", "·", "·"])
        elif layer == 1:
            char = random.choice([".", "*", "+", "·", "·"])
        else:
            char = random.choice(["*", "+", "✦", "∗", "✧"])
        stars.append({"x": sx, "y": sy, "br": brightness, "ph": twinkle_phase, "ch": char})
    star_layers.append(stars)

# ── Nebula patches — vivid colors ──
nebula_patches = []
for _ in range(random.randint(4, 7)):
    nx = random.uniform(view_w * 0.05, view_w * 0.95)
    ny = random.uniform(view_h * 0.05, view_h * 0.95)
    nr = random.uniform(5, 14)
    colors_pool = [
        (90, 35, 140), (50, 70, 150), (35, 90, 120),
        (110, 28, 115), (60, 50, 130), (40, 75, 100),
        (95, 22, 80), (30, 65, 110),
    ]
    nc = random.choice(colors_pool)
    nebula_patches.append({"x": nx, "y": ny, "r": nr, "c": nc, "ph": random.uniform(0, math.tau)})

# ── Distant planet/moon — single focal point ──
planet_x = random.uniform(view_w * 0.2, view_w * 0.8)
planet_y = random.uniform(view_h * 0.2, view_h * 0.6)
planet_r = random.uniform(3.0, 5.5)
planet_color = random.choice([
    (45, 55, 75),   # cold blue-gray
    (60, 50, 40),   # rusty brown
    (50, 65, 55),   # mossy green-gray
])
planet_light_dir = random.uniform(-0.5, 0.5)  # which side is lit

# ── Distant ships ──
ship_templates = [
    [" >==> "],
    ["--<=>--"],
    [" /\\ ", "<===>", " \\/ "],
    ["  ^  ", " /|\\ ", "/___\\"],
    [" <> "],
    ["-=-"],
    [">>==>>"],
]

ships = []
for _ in range(4):
    tmpl = random.choice(ship_templates)
    ship_w = max(len(l) for l in tmpl)
    ship_h = len(tmpl)
    sx = random.uniform(-ship_w - 60, -ship_w - 10)
    sy = random.uniform(view_h * 0.12, view_h * 0.78)
    speed = random.uniform(0.06, 0.22)
    delay = random.randint(20, 400)
    ships.append({
        "tmpl": tmpl, "x": sx, "y": sy, "w": ship_w, "h": ship_h,
        "speed": speed, "delay": delay, "phase": random.uniform(0, math.tau),
        "color": random.choice([(140, 150, 170), (120, 135, 155), (165, 160, 145)]),
    })

# ── Warning lights — more prominent ──
warning_lights = []
# Top frame
for i in range(4):
    lx = frame_l + int(view_w * (0.15 + i * 0.23))
    warning_lights.append({"x": lx, "y": 1, "ph": random.uniform(0, math.tau),
                           "rate": random.uniform(0.05, 0.10), "type": "amber"})
# Side frame — staggered
for i in range(3):
    ly = frame_t + int(view_h * (0.2 + i * 0.3))
    warning_lights.append({"x": 1, "y": ly, "ph": random.uniform(0, math.tau),
                           "rate": random.uniform(0.035, 0.07), "type": "red"})
    warning_lights.append({"x": width - 2, "y": ly, "ph": random.uniform(0, math.tau),
                           "rate": random.uniform(0.035, 0.07), "type": "red"})
# Bottom corners
warning_lights.append({"x": 1, "y": height - 2, "ph": 0.0, "rate": 0.04, "type": "red"})
warning_lights.append({"x": width - 2, "y": height - 2, "ph": 1.5, "rate": 0.04, "type": "red"})

# ── Console panel HUD ──
hud_items = [
    {"label": "HULL", "value": "37%", "x_frac": 0.06, "warn": True},
    {"label": "O2", "value": "12%", "x_frac": 0.20, "warn": True},
    {"label": "PWR", "value": "AUX", "x_frac": 0.33, "warn": False},
    {"label": "NAV", "value": "OFFLINE", "x_frac": 0.48, "warn": True},
    {"label": "COMMS", "value": "---", "x_frac": 0.66, "warn": False},
    {"label": "DRIFT", "value": "0.02\u00b0/s", "x_frac": 0.82, "warn": False},
]

# ── Frame material colors ──
frame_base = (22, 24, 32)
frame_edge = (38, 42, 52)
frame_highlight = (48, 52, 62)
frame_rivet = (55, 60, 72)
panel_base = (16, 18, 24)
panel_line = (30, 34, 42)

# ── Dust motes ──
dust = []
for _ in range(max(10, width // 5)):
    dust.append({
        "x": random.uniform(0, width),
        "y": random.uniform(0, height),
        "speed_x": random.uniform(-0.12, 0.12),
        "speed_y": random.uniform(-0.06, 0.06),
        "ph": random.uniform(0, math.tau),
    })

# ── Precompute frame damage spots ──
damage_spots = set()
for _ in range(max(3, width // 8)):
    dx = random.randint(0, width - 1)
    dy = random.choice([random.randint(0, frame_t - 1),
                        random.randint(height - frame_b, height - 1),
                        random.randint(0, height - 1)])
    if dy < frame_t or dy >= height - frame_b or dx < frame_l or dx >= width - frame_r:
        damage_spots.add((dx, dy))

# ══════════════════════════════════════════
# MAIN RENDER LOOP
# ══════════════════════════════════════════
for frame_num in range(3000):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    cbuf = [[""] * width for _ in range(height)]

    t = frame_num

    # ═══ SPACE BACKGROUND ═══
    for py in range(view_y0, view_y1 + 1):
        vy_frac = (py - view_y0) / max(1, view_h)
        for px in range(view_x0, view_x1 + 1):
            vx_frac = (px - view_x0) / max(1, view_w)
            # Slight vignette at edges
            edge_dist = min(vx_frac, 1 - vx_frac, vy_frac, 1 - vy_frac)
            vignette = min(1.0, edge_dist * 8)
            base_r = int((2 + 3 * vy_frac) * vignette)
            base_g = int((3 + 4 * vy_frac) * vignette)
            base_b = int((10 + 8 * (1 - abs(vy_frac - 0.4) * 2)) * vignette)
            cbuf[py][px] = rgb((base_r, base_g, base_b))

    # ═══ NEBULA — boosted ═══
    for neb in nebula_patches:
        drift_x = math.sin(t * 0.004 + neb["ph"]) * 2.0
        drift_y = math.cos(t * 0.003 + neb["ph"] * 1.7) * 1.0
        nx = neb["x"] + drift_x
        ny = neb["y"] + drift_y
        nr = neb["r"]
        pulse = 0.75 + 0.25 * math.sin(t * 0.012 + neb["ph"])
        nc = neb["c"]
        # Iterate in integer steps
        for dy in range(int(-nr - 1), int(nr + 2)):
            py = view_y0 + int(ny + dy)
            if py < view_y0 or py > view_y1:
                continue
            for dx in range(int(-nr * 2 - 1), int(nr * 2 + 2)):
                dist = math.sqrt((dx / 2.0) ** 2 + dy ** 2)
                if dist > nr:
                    continue
                px = view_x0 + int(nx + dx)
                if px < view_x0 or px > view_x1:
                    continue
                falloff = 1.0 - (dist / nr)
                intensity = falloff * falloff * pulse * 1.2
                bg_r = int(3 + nc[0] * intensity)
                bg_g = int(4 + nc[1] * intensity)
                bg_b = int(10 + nc[2] * intensity)
                cbuf[py][px] = rgb((min(255, bg_r), min(255, bg_g), min(255, bg_b)))
                if intensity > 0.15:
                    buf[py][px] = random.choice(["░", "░", "·", " "])

    # ═══ DISTANT PLANET ═══
    p_drift_x = math.sin(t * 0.002) * 1.2
    p_drift_y = math.cos(t * 0.0015) * 0.6
    pcx = planet_x + p_drift_x
    pcy = planet_y + p_drift_y
    pr = planet_r
    for dy in range(int(-pr - 1), int(pr + 2)):
        for dx in range(int(-pr * 2 - 1), int(pr * 2 + 2)):
            # Aspect-corrected distance
            ndx = dx / 2.0
            dist = math.sqrt(ndx * ndx + dy * dy)
            if dist > pr:
                continue
            px = view_x0 + int(pcx + dx)
            py = view_y0 + int(pcy + dy)
            if view_x0 <= px <= view_x1 and view_y0 <= py <= view_y1:
                # Sphere shading: light from one side
                nx_norm = ndx / pr
                ny_norm = dy / pr
                nz_norm = math.sqrt(max(0, 1 - nx_norm*nx_norm - ny_norm*ny_norm))
                # Diffuse lighting
                light_x = 0.6 + planet_light_dir
                light_y = -0.3
                light_z = 0.7
                ll = math.sqrt(light_x*light_x + light_y*light_y + light_z*light_z)
                light_x /= ll; light_y /= ll; light_z /= ll
                diffuse = max(0, nx_norm*light_x + ny_norm*light_y + nz_norm*light_z)
                shade = 0.15 + 0.85 * diffuse
                # Edge glow (atmosphere)
                edge = 1.0 - nz_norm
                atmo = edge * edge * 0.4
                pc = planet_color
                cr = int(pc[0] * shade + 40 * atmo)
                cg = int(pc[1] * shade + 60 * atmo)
                cb = int(pc[2] * shade + 80 * atmo)
                # Smooth sphere shading with graded chars
                edge_r = dist / pr
                if edge_r > 0.92:
                    ch = "░"
                elif shade < 0.2:
                    ch = "▒"
                elif shade < 0.4:
                    ch = "▓"
                else:
                    ch = "█"
                buf[py][px] = ch
                cbuf[py][px] = rgb((min(255, cr), min(255, cg), min(255, cb)))

    # ═══ STARS ═══
    drift_speeds = [0.015, 0.05, 0.12]
    for li, layer_stars in enumerate(star_layers):
        speed = drift_speeds[li]
        for star in layer_stars:
            sx = (star["x"] - t * speed) % view_w
            sy = star["y"] + math.sin(t * 0.008 + star["ph"]) * 0.4
            px = view_x0 + int(sx)
            py = view_y0 + int(sy)
            if view_x0 <= px <= view_x1 and view_y0 <= py <= view_y1:
                twinkle = 0.4 + 0.6 * math.sin(t * 0.07 + star["ph"])
                br = star["br"] * twinkle
                if br > 0.2:
                    v = int(100 + 155 * br)
                    if li == 0:
                        c = (int(v * 0.75), int(v * 0.8), min(255, int(v * 1.05)))
                    elif li == 1:
                        c = (int(v * 0.85), int(v * 0.88), v)
                    else:
                        c = (v, int(v * 0.93), int(v * 0.82))
                    buf[py][px] = star["ch"]
                    cbuf[py][px] = rgb(c)

    # ═══ DISTANT SHIPS ═══
    for ship in ships:
        if ship["delay"] > 0:
            ship["delay"] -= 1
            continue
        ship["x"] += ship["speed"]
        sy_wobble = ship["y"] + math.sin(t * 0.018 + ship["phase"]) * 0.6
        if ship["x"] > view_w + 25:
            ship["x"] = random.uniform(-ship["w"] - 100, -ship["w"] - 20)
            ship["y"] = random.uniform(view_h * 0.12, view_h * 0.78)
            ship["speed"] = random.uniform(0.06, 0.22)
            ship["delay"] = random.randint(80, 500)
        for row_i, row in enumerate(ship["tmpl"]):
            for col_i, ch in enumerate(row):
                if ch == " ":
                    continue
                px = view_x0 + int(ship["x"] + col_i)
                py = view_y0 + int(sy_wobble + row_i)
                if view_x0 <= px <= view_x1 and view_y0 <= py <= view_y1:
                    sc = ship["color"]
                    dist_fade = max(0.35, 1.0 - abs(ship["x"] - view_w / 2) / (view_w * 0.55))
                    c = (int(sc[0] * dist_fade), int(sc[1] * dist_fade), int(sc[2] * dist_fade))
                    buf[py][px] = ch
                    cbuf[py][px] = rgb(c)
        # Engine glow trail
        tmpl = ship["tmpl"]
        engine_row = len(tmpl) // 2
        for trail in range(3):
            engine_x = int(ship["x"]) - 1 - trail
            engine_y = int(sy_wobble) + engine_row
            px = view_x0 + engine_x
            py = view_y0 + engine_y
            if view_x0 <= px <= view_x1 and view_y0 <= py <= view_y1:
                glow = (0.5 + 0.5 * math.sin(t * 0.25 + ship["phase"])) * (1.0 - trail * 0.3)
                buf[py][px] = "·" if trail > 0 else "•"
                cbuf[py][px] = rgb((int(60 * glow), int(120 * glow), int(255 * glow)))

    # ═══ WINDOW FRAME ═══
    for y in range(height):
        for x in range(width):
            in_view = (view_x0 <= x <= view_x1 and view_y0 <= y <= view_y1)
            if in_view:
                continue

            is_outer_edge = (y == 0 or y == height - 1 or x == 0 or x == width - 1)
            is_inner_edge = (y == view_y0 - 1 or y == view_y1 + 1 or
                             x == view_x0 - 1 or x == view_x1 + 1)
            is_2nd_edge = (y == 1 or y == height - 2 or x == 1 or x == width - 2)

            if y >= height - frame_b:
                # ── Bottom console panel ──
                if y == height - frame_b:
                    # Top edge of console — separator line
                    buf[y][x] = "─"
                    cbuf[y][x] = rgb(panel_line)
                elif is_outer_edge:
                    buf[y][x] = "█"
                    cbuf[y][x] = rgb(frame_edge)
                else:
                    # Panel texture
                    if (x % 12 == 0) and y > height - frame_b:
                        buf[y][x] = "│"
                        cbuf[y][x] = rgb(panel_line)
                    else:
                        buf[y][x] = "▓" if (x + y) % 7 == 0 else "█"
                        cbuf[y][x] = rgb(panel_base)
            elif is_outer_edge:
                buf[y][x] = "█"
                cbuf[y][x] = rgb(frame_edge)
            elif is_2nd_edge:
                buf[y][x] = "▓"
                cbuf[y][x] = rgb(frame_highlight)
            elif is_inner_edge:
                buf[y][x] = "▒"
                cbuf[y][x] = rgb(frame_edge)
            else:
                buf[y][x] = "█"
                cbuf[y][x] = rgb(frame_base)

            # Rivets on inner edge
            if is_inner_edge and (x + y) % 5 == 0:
                buf[y][x] = "•"
                cbuf[y][x] = rgb(frame_rivet)

            # Damage spots — scratches
            if (x, y) in damage_spots:
                buf[y][x] = random.choice(["░", "▒", "╌"])
                cbuf[y][x] = rgb((18, 20, 25))

    # ═══ WINDOW STRUTS — wider, more visible ═══
    for sx in strut_positions:
        for y in range(view_y0, view_y1 + 1):
            # Left edge highlight, center, right shadow
            if sx - 1 >= view_x0:
                buf[y][sx - 1] = "▐"
                cbuf[y][sx - 1] = rgb(frame_highlight)
            buf[y][sx] = "█"
            cbuf[y][sx] = rgb(frame_base)
            if sx + 1 <= view_x1:
                buf[y][sx + 1] = "▌"
                cbuf[y][sx + 1] = rgb((18, 20, 26))

    # ═══ HORIZONTAL CROSSBAR — mid-height ═══
    crossbar_y = view_y0 + view_h // 2
    if view_y0 < crossbar_y < view_y1:
        for x in range(view_x0, view_x1 + 1):
            skip = False
            for sx in strut_positions:
                if abs(x - sx) <= 1:
                    skip = True
                    break
            if not skip:
                buf[crossbar_y][x] = "─"
                cbuf[crossbar_y][x] = rgb(frame_base)

    # ═══ WINDOW CRACKS ═══
    crack_chars = ["╱", "╲", "─", "│", "╳", "/", "\\"]
    for origin, segs in cracks:
        ox, oy = origin
        if view_x0 <= ox <= view_x1 and view_y0 <= oy <= view_y1:
            buf[oy][ox] = "✕"
            cbuf[oy][ox] = rgb((70, 95, 120))
        for cx, cy in segs:
            if view_x0 <= cx <= view_x1 and view_y0 <= cy <= view_y1:
                buf[cy][cx] = random.choice(crack_chars)
                gl = 0.5 + 0.5 * math.sin(t * 0.04 + cx * 0.5)
                cbuf[cy][cx] = rgb((int(45 * gl), int(60 * gl), int(85 * gl)))

    # ═══ WARNING LIGHTS — bigger glow ═══
    for wl in warning_lights:
        pulse = math.sin(t * wl["rate"] + wl["ph"])
        on = pulse > -0.2
        wx, wy = wl["x"], wl["y"]
        if not (0 <= wx < width and 0 <= wy < height):
            continue
        if on:
            intensity = max(0, pulse + 0.2) / 1.2
            if wl["type"] == "amber":
                c = (int(240 * intensity), int(155 * intensity), int(18 * intensity))
            else:
                c = (int(220 * intensity), int(25 * intensity), int(18 * intensity))
            buf[wy][wx] = "●" if intensity > 0.4 else "◉"
            cbuf[wy][wx] = f"bold {rgb(c)}"
            # Extended glow radius
            for gdx in range(-2, 3):
                for gdy in range(-2, 3):
                    if gdx == 0 and gdy == 0:
                        continue
                    gx, gy = wx + gdx, wy + gdy
                    if not (0 <= gx < width and 0 <= gy < height):
                        continue
                    # Don't overwrite the space viewport
                    in_view = (view_x0 <= gx <= view_x1 and view_y0 <= gy <= view_y1)
                    if in_view:
                        continue
                    dist = math.sqrt(gdx * gdx + gdy * gdy)
                    ga = intensity * max(0, 0.45 - dist * 0.12)
                    if ga > 0.02:
                        if wl["type"] == "amber":
                            gc = lc(frame_base, (200, 140, 20), ga)
                        else:
                            gc = lc(frame_base, (180, 25, 18), ga)
                        cbuf[gy][gx] = rgb(gc)
        else:
            buf[wy][wx] = "○"
            cbuf[wy][wx] = rgb((20, 22, 28))

    # ═══ DUST MOTES ═══
    for d in dust:
        d["x"] += d["speed_x"] + math.sin(t * 0.018 + d["ph"]) * 0.08
        d["y"] += d["speed_y"] + math.cos(t * 0.012 + d["ph"] * 1.3) * 0.04
        if d["x"] < 0: d["x"] = width - 1
        if d["x"] >= width: d["x"] = 0
        if d["y"] < 0: d["y"] = height - 1
        if d["y"] >= height: d["y"] = 0
        ppx, ppy = int(d["x"]), int(d["y"])
        if view_x0 <= ppx <= view_x1 and view_y0 <= ppy <= view_y1:
            fl = 0.3 + 0.7 * math.sin(t * 0.05 + d["ph"])
            if fl > 0.35:
                buf[ppy][ppx] = "·"
                v = int(45 + 45 * fl)
                cbuf[ppy][ppx] = rgb((v, v, int(v * 1.15)))

    # ═══ HUD / CONSOLE READOUTS ═══
    hud_y = height - 2
    if 0 < hud_y < height:
        for item in hud_items:
            hx = int(width * item["x_frac"])
            label = item["label"]
            value = item["value"]
            glitch = random.random() < 0.03
            if glitch:
                value = "".join(random.choice("░▒▓█▪·") for _ in value)
            text = f"{label}:{value}"
            for ci, ch in enumerate(text):
                ppx = hx + ci
                if 0 <= ppx < width:
                    buf[hud_y][ppx] = ch
                    if item["warn"] and not glitch:
                        wp = 0.5 + 0.5 * math.sin(t * 0.08 + item["x_frac"] * 10)
                        cbuf[hud_y][ppx] = rgb((int(190 * wp + 45), int(85 * wp + 20), 15))
                    elif glitch:
                        cbuf[hud_y][ppx] = rgb((random.randint(20, 80), random.randint(40, 100), random.randint(60, 120)))
                    else:
                        cbuf[hud_y][ppx] = rgb((35, 85, 55))

    # ═══ STATUS LINE ═══
    status_y = height - frame_b
    if 0 <= status_y < height:
        messages = [
            "LIFE SUPPORT: CRITICAL",
            "BEACON ACTIVE... NO RESPONSE",
            "DRIFT DETECTED \u2014 THRUSTERS OFFLINE",
            "LAST CREW LOG: 847 DAYS AGO",
            "SECTOR 7G \u2014 UNCHARTED",
            "AUTO-REPAIR: 3% COMPLETE",
            "WARNING: MICRO-DEBRIS FIELD AHEAD",
        ]
        msg_idx = (t // 200) % len(messages)
        msg = messages[msg_idx]
        chars_shown = min(len(msg), (t % 200) // 2)
        display = msg[:chars_shown]
        cursor_on = (t % 10) < 6

        # Right-aligned timestamp
        timestamp = f"T+{847 * 24 + (t // 12):05d}h"
        ts_x = width - frame_r - len(timestamp) - 1
        for ci, ch in enumerate(timestamp):
            ppx = ts_x + ci
            if 0 <= ppx < width:
                buf[status_y][ppx] = ch
                cbuf[status_y][ppx] = rgb((30, 65, 45))

        start_x = view_x0 + 1
        for ci, ch in enumerate(display):
            ppx = start_x + ci
            if 0 <= ppx < width:
                fl = 0.7 + 0.3 * math.sin(t * 0.1 + ci * 0.15)
                buf[status_y][ppx] = ch
                cbuf[status_y][ppx] = rgb((int(175 * fl), int(120 * fl), int(22 * fl)))

        cursor_x = start_x + len(display)
        if cursor_on and 0 <= cursor_x < width and chars_shown < len(msg):
            buf[status_y][cursor_x] = "▌"
            cbuf[status_y][cursor_x] = rgb((175, 120, 22))

    # ═══ SCANLINES — faint glass distortion ═══
    scan_offset = (t // 4) % 5
    for y in range(view_y0, view_y1 + 1):
        if (y + scan_offset) % 5 == 0:
            for x in range(view_x0, view_x1 + 1):
                is_strut = False
                for sx in strut_positions:
                    if abs(x - sx) <= 1:
                        is_strut = True
                        break
                if is_strut or y == crossbar_y:
                    continue
                if buf[y][x] == " ":
                    buf[y][x] = "·"
                    cbuf[y][x] = rgb((6, 7, 14))

    # ═══ RENDER ═══
    for y in range(height):
        line = Text()
        for x in range(width):
            c = cbuf[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.08)
