from rich.text import Text
import random
import math

# Sea Sunset — golden sun melting into a calm ocean horizon with clouds and shimmering reflections

horizon = int(height * 0.68)

# ── Sun: large, centered, partially dipped below horizon ──
sun_cx = width // 2
sun_r = min(height // 5, width // 7, 9)

# ── Clouds — thin wispy streaks ──
random.seed(33)
clouds = []
for _ in range(random.randint(3, 5)):
    cx = random.randint(10, width - 10)
    cy = random.randint(max(1, horizon - sun_r - 10), max(2, horizon - sun_r - 2))
    cw = random.randint(6, 16)
    clouds.append((cx, cy, cw))

# ── Stars — sparse, only in upper sky ──
stars = [(random.randint(0, width - 1), random.randint(0, max(1, horizon // 3)),
          random.uniform(0, 6.28)) for _ in range(width // 6)]
random.seed()

# ── Waves — multiple sine wave layers for ocean surface ──
wave_layers = [
    {"amp": 0.6, "freq": 0.12, "speed": 0.08, "phase": 0.0},
    {"amp": 0.4, "freq": 0.18, "speed": 0.12, "phase": 1.5},
    {"amp": 0.3, "freq": 0.25, "speed": 0.06, "phase": 3.0},
]

# ── Seabirds — simple V shapes ──
random.seed(88)
birds = []
for _ in range(random.randint(3, 6)):
    bx = random.randint(0, width - 1)
    by = random.randint(max(1, horizon - sun_r - 12), horizon - 4)
    bspeed = random.uniform(0.3, 0.8)
    bdir = random.choice([-1, 1])
    birds.append([bx, by, bspeed, bdir])
random.seed()

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    # Sun dip — slowly sinks over frames
    sun_dip = frame * 0.02
    sun_cy = int(horizon - sun_r * 0.3 + sun_dip * 0.8)

    # ── Sky gradient — warm sunset colors ──
    for y in range(horizon + 1):
        t = y / max(1, horizon)
        # Upper sky: deep indigo → middle: warm magenta/salmon → horizon: fiery gold
        if t < 0.25:
            s = t / 0.25
            r = int(10 + s * 50)
            g = int(5 + s * 15)
            b = int(45 + s * 35)
        elif t < 0.5:
            s = (t - 0.25) / 0.25
            r = int(60 + s * 120)
            g = int(20 + s * 40)
            b = int(80 - s * 30)
        elif t < 0.75:
            s = (t - 0.5) / 0.25
            r = int(180 + s * 55)
            g = int(60 + s * 70)
            b = int(50 - s * 25)
        else:
            s = (t - 0.75) / 0.25
            r = int(235 + s * 20)
            g = int(130 + s * 80)
            b = int(25 - s * 10)
        for x in range(width):
            col[y][x] = f"rgb({min(255,r)},{min(255,g)},{max(0,b)})"

    # ── Stars — only visible in dark upper sky ──
    for sx, sy, ph in stars:
        if 0 <= sx < width and 0 <= sy < height and sy < horizon // 3:
            tw = 0.3 + 0.7 * math.sin(frame * 0.03 + ph)
            if tw > 0.5:
                v = int(40 + tw * 80)
                buf[sy][sx] = "·"
                col[sy][sx] = f"rgb({v},{v},{v + 10})"

    # ── Sun — warm glowing disc ──
    for dy in range(-sun_r, sun_r + 1):
        y = sun_cy + dy
        if y < 0 or y >= height:
            continue
        half_w = int(1.8 * math.sqrt(max(0, sun_r * sun_r - dy * dy)))
        for x in range(max(0, sun_cx - half_w), min(width, sun_cx + half_w + 1)):
            # Sun bands — horizontal slices removed for retro effect
            if y < horizon and abs(dy) > 2 and abs(dy) % 3 == 0 and dy > 0:
                continue
            dist = math.sqrt((x - sun_cx) ** 2 + (dy) ** 2) / sun_r
            # Color: center white-yellow → edge deep orange-red
            r = 255
            g = int(255 - dist * 120)
            b_c = int(100 - dist * 80)
            if y <= horizon:
                buf[y][x] = "█"
                col[y][x] = f"rgb({r},{max(50, g)},{max(10, b_c)})"

    # ── Sun glow — warm color bleed into sky (no characters) ──
    glow_r = sun_r + 6
    for dy in range(-glow_r, glow_r + 1):
        y = sun_cy + dy
        if y < 0 or y >= horizon or y >= height:
            continue
        for dx in range(-int(glow_r * 2.5), int(glow_r * 2.5) + 1):
            x = sun_cx + dx
            if x < 0 or x >= width:
                continue
            dist = math.sqrt((dx / 2.0) ** 2 + dy ** 2)
            if dist > sun_r and dist < glow_r and buf[y][x] == " ":
                fade = 1.0 - (dist - sun_r) / (glow_r - sun_r)
                fade *= fade  # quadratic falloff for softer edge
                # Warm up the existing sky color instead of drawing characters
                base_t = y / max(1, horizon)
                r_s = min(255, int(60 + fade * 180 + base_t * 40))
                g_s = min(255, int(20 + fade * 100 + base_t * 30))
                b_s = max(0, int(30 + fade * 20))
                col[y][x] = f"rgb({r_s},{g_s},{b_s})"

    # ── Clouds — thin wispy streaks, lit by sunset ──
    for cx, cy, cw in clouds:
        drift = math.sin(frame * 0.015 + cx * 0.1) * 3
        for dx in range(-cw // 2, cw // 2 + 1):
            x = int(cx + dx + drift)
            if 0 <= x < width and 0 <= cy < height:
                edge = abs(dx) / (cw / 2 + 1)
                # Wispy: large gaps, especially at edges
                if random.random() < edge * 0.6 + 0.25:
                    continue
                glow = max(0, 1 - abs(x - sun_cx) / (width * 0.5))
                r = int(160 + glow * 80)
                g = int(110 + glow * 70)
                b = int(80 + glow * 20)
                ch = random.choice(["─", "─", "~", "—", "·"])
                buf[cy][x] = ch
                col[cy][x] = f"rgb({min(255, r)},{min(255, g)},{min(255, b)})"

    # ── Seabirds ──
    for bird in birds:
        bx, by = int(bird[0]), int(bird[1])
        bird[0] += bird[2] * bird[3]
        bird[1] += math.sin(frame * 0.1 + bx * 0.05) * 0.15
        if bird[0] > width + 5:
            bird[0] = -5
        elif bird[0] < -5:
            bird[0] = width + 5
        wing = math.sin(frame * 0.3 + bx) * 0.5
        if 0 <= by < height:
            if 0 <= bx - 1 < width:
                buf[by][bx - 1] = "~" if wing > 0 else "ˋ"
                col[by][bx - 1] = "rgb(30,20,20)"
            if 0 <= bx < width:
                buf[by][bx] = "v"
                col[by][bx] = "rgb(20,15,15)"
            if 0 <= bx + 1 < width:
                buf[by][bx + 1] = "~" if wing > 0 else "ˊ"
                col[by][bx + 1] = "rgb(30,20,20)"

    # ── Undulating waterline — per-column wave height ──
    waterline = [0] * width
    for x in range(width):
        wl_wave = (1.0 * math.sin(x * 0.18 + frame * 0.08)
                   + 0.6 * math.sin(x * 0.35 - frame * 0.06)
                   + 0.4 * math.sin(x * 0.55 + frame * 0.12))
        waterline[x] = horizon + int(wl_wave)

    # ── Ocean — water below the wavy waterline ──
    for x in range(width):
        wl_y = waterline[x]
        for y in range(max(0, wl_y), height):
            t = (y - horizon) / max(1, height - horizon)
            t = max(0.0, t)

            # Combined wave displacement for texture
            wave = 0
            for wl in wave_layers:
                wave += wl["amp"] * math.sin(x * wl["freq"] + frame * wl["speed"] + wl["phase"])

            # Base ocean color — near horizon warm/light, deepening to dark teal
            depth = t
            r_w = int(15 + (1 - depth) * 20)
            g_w = int(30 + (1 - depth) * 30 + depth * 15)
            b_w = int(55 + (1 - depth) * 40 + depth * 30)

            # Sun reflection — multiple light streaks drifting right-to-left
            refl_zone = sun_r * 4
            refl_total = 0.0
            for ri in range(7):
                streak_speed = 0.3 + ri * 0.15
                offset = (ri * refl_zone / 4.5 - frame * streak_speed) % refl_zone - refl_zone / 2
                streak_cx = sun_cx + offset
                streak_w = sun_r * (0.5 + 0.3 * math.sin(ri * 1.7)) * (0.4 + t * 0.9)
                sdx = abs(x - streak_cx)
                if sdx < streak_w:
                    fade = (1.0 - sdx / streak_w)
                    fade *= fade
                    shimmer = 0.5 + 0.5 * math.sin(frame * 0.1 + x * 0.25 + y * 0.5 + ri * 2.0 + wave * 2)
                    refl_total += fade * shimmer * (1 - t * 0.35)
            refl_total = min(1.0, refl_total)
            if refl_total > 0.05:
                r_w = min(255, int(r_w + refl_total * 230))
                g_w = min(255, int(g_w + refl_total * 150))
                b_w = min(255, int(b_w + refl_total * 40))

            # Visible wave bands — crests brighter, scrolling
            wave_band = math.sin(y * 0.8 + wave * 1.5 - frame * 0.06)
            wave_vis = max(0, wave_band)
            crest_strength = wave_vis * (1 - t * 0.6) * 0.7
            r_w = min(255, int(r_w + crest_strength * 80))
            g_w = min(255, int(g_w + crest_strength * 100))
            b_w = min(255, int(b_w + crest_strength * 110))

            # Ocean body — straight horizontal lines
            ch = "─" if wave_band > 0.3 else " "

            # Waterline edge — bright straight line
            if y == wl_y:
                r_w = min(255, r_w + 100)
                g_w = min(255, g_w + 80)
                b_w = min(255, b_w + 50)
                ch = "─"

            buf[y][x] = ch
            col[y][x] = f"rgb({r_w},{g_w},{b_w})"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.15)
