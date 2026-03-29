from rich.text import Text
import random
import math

# Roku City — warm twilight cityscape with water reflections
# Slow parallax scroll, drifting blimp, cozy window glow

road_y = height - 5
water_y = height - 4  # water starts here
WORLD_W = width * 4

# ── Sunset sky palette ──
sky_colors = [
    (0.00, (10, 8, 30)),     # deep indigo top
    (0.10, (18, 12, 45)),    # dark purple
    (0.20, (30, 18, 55)),    # purple
    (0.35, (55, 25, 60)),    # warm purple
    (0.50, (90, 35, 55)),    # mauve
    (0.65, (140, 55, 45)),   # warm rose
    (0.78, (190, 90, 40)),   # orange glow
    (0.88, (210, 130, 50)),  # golden horizon
    (0.95, (180, 110, 55)),  # muted gold
    (1.00, (120, 70, 50)),   # horizon fade
]

def sky_color(t):
    for i in range(len(sky_colors) - 1):
        t0, c0 = sky_colors[i]
        t1, c1 = sky_colors[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / max(0.001, t1 - t0)
            return tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))
    return sky_colors[-1][1]

# ── Stars ──
random.seed(42)
stars = [(random.randint(0, width - 1), random.randint(0, int(height * 0.35)),
          random.uniform(0, 6.28), random.uniform(0.4, 1.0)) for _ in range(width // 4)]

# ── Blimp ──
blimp_y = int(height * 0.15)
blimp_phase = random.uniform(0, 6.28)

# ── Background buildings (tall silhouettes) ──
bg_base = road_y - int(height * 0.08)
bg_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 2)
    bw = random.randint(3, 9)
    bh = random.randint(5, int(height * 0.35))
    style = random.choice(["flat", "flat", "dome", "spire", "antenna"])
    bg_buildings.append((bx, bw, bh, style))
    bx += bw

# ── Midground buildings ──
mid_base = road_y - int(height * 0.03)
mid_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 2)
    bw = random.randint(4, 10)
    bh = random.randint(3, int(height * 0.22))
    shade = random.randint(25, 45)
    mid_buildings.append((bx, bw, bh, shade))
    bx += bw

# ── Foreground buildings (detailed, with windows) ──
fg_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 1)
    bw = random.randint(5, 14)
    bh = random.randint(3, max(4, int(height * 0.16)))
    shade = random.randint(35, 60)
    fg_buildings.append({"x": bx, "w": bw, "h": bh, "shade": shade})
    bx += bw

# Foreground windows
fg_wins = []
for b in fg_buildings:
    wins = []
    for wy in range(1, b["h"] - 1, 2):
        for wx in range(1, b["w"] - 2, 3):
            if random.random() < 0.65:
                wtype = random.choice(["warm", "warm", "warm", "cool", "amber"])
                wins.append((wx, wy, wtype))
    fg_wins.append(wins)

# ── Neon signs on fg buildings ──
neon_signs = []
neon_words = ["CINEMA", "DINER", "HOTEL", "CAFE", "BOOKS", "PIZZA", "VINYL", "RADIO"]
neon_colors_list = [
    "rgb(255,100,80)", "rgb(80,200,255)", "rgb(255,180,60)",
    "rgb(120,255,150)", "rgb(255,100,200)",
]
for b in fg_buildings:
    if b["h"] >= 4 and random.random() < 0.25:
        word = random.choice(neon_words)
        color = random.choice(neon_colors_list)
        sx = b["x"] + max(0, (b["w"] - len(word)) // 2)
        sy_offset = 1
        neon_signs.append((sx, b["x"], b["w"], b["h"], sy_offset, word, color))

# ── Flowing clouds ──
flow_clouds = []
for _ in range(6):
    cx = random.randint(-10, width + 10)
    cy = random.randint(1, int(height * 0.35))
    cw = random.randint(8, 18)
    ch = random.randint(1, 3)
    speed = random.uniform(0.04, 0.1)
    opacity = random.uniform(0.15, 0.35)
    flow_clouds.append({"x": float(cx), "y": cy, "w": cw, "h": ch,
                         "speed": speed, "opacity": opacity})

random.seed()

SCROLL_SPEED = 0.25

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    scroll = frame * SCROLL_SPEED
    scroll_i = int(scroll)

    # ── Sky gradient ──
    for y in range(road_y):
        t = y / max(1, road_y)
        r, g, b = sky_color(t)
        # Subtle shimmer near horizon
        if t > 0.7:
            shimmer = int(5 * math.sin(frame * 0.03 + y * 0.5))
            r = min(255, r + shimmer)
            g = min(255, g + shimmer)
        for x in range(width):
            col[y][x] = f"rgb({r},{g},{b})"

    # ── Stars (slow parallax, twinkle) ──
    star_off = int(scroll * 0.03)
    for sx, sy, ph, bright in stars:
        ax = (sx - star_off) % width
        if 0 <= ax < width and 0 <= sy < height:
            tw = 0.5 + 0.5 * math.sin(frame * 0.06 + ph)
            if tw > 0.3:
                v = int(50 + tw * bright * 120)
                buf[sy][ax] = "·" if tw < 0.65 else "*"
                col[sy][ax] = f"rgb({v},{v},{int(v * 0.85)})"

    # ── Flowing clouds ──
    for cloud in flow_clouds:
        cloud["x"] += cloud["speed"]
        if cloud["x"] > width + cloud["w"]:
            cloud["x"] = float(-cloud["w"])
        cx_i = int(cloud["x"])
        cy, cw, ch, op = cloud["y"], cloud["w"], cloud["h"], cloud["opacity"]
        for dy in range(ch):
            center_row = ch / 2.0
            row_t = 1.0 - abs(dy - center_row) / max(1, center_row + 0.5)
            row_w = max(2, int(cw * row_t))
            off = (cw - row_w) // 2
            for dx in range(row_w):
                px = cx_i + off + dx
                py = cy + dy
                if 0 <= px < width and 0 <= py < road_y:
                    edge = 1.0 - abs(dx - row_w // 2) / max(1, row_w // 2)
                    # Warm cloud tint from sunset
                    base_r, base_g, base_b = sky_color(py / max(1, road_y))
                    vr = int((base_r + 40 * edge) * op)
                    vg = int((base_g + 25 * edge) * op)
                    vb = int((base_b + 15 * edge) * op)
                    buf[py][px] = "░" if edge < 0.4 else "▒"
                    col[py][px] = f"rgb({min(255,vr)},{min(255,vg)},{min(255,vb)})"

    # ── Blimp (floats across slowly) ──
    blimp_x = int((frame * 0.15 + width * 0.3) % (width + 30)) - 15
    by = blimp_y + int(math.sin(frame * 0.02 + blimp_phase) * 1.5)
    # Body
    blimp_body = "▬▬▬═══▬▬▬"
    for i, ch in enumerate(blimp_body):
        px = blimp_x + i
        if 0 <= px < width and 0 <= by < road_y:
            buf[by][px] = ch
            col[by][px] = "rgb(80,70,90)"
    # Gondola
    gondola = " ▄███▄"
    for i, ch in enumerate(gondola):
        px = blimp_x + 1 + i
        if 0 <= px < width and 0 <= by + 1 < road_y and ch != " ":
            buf[by + 1][px] = ch
            col[by + 1][px] = "rgb(60,55,75)"
    # Light on gondola
    light_x = blimp_x + 4
    if 0 <= light_x < width and 0 <= by + 1 < road_y:
        blink = math.sin(frame * 0.2) > 0
        if blink:
            col[by + 1][light_x] = "rgb(255,60,60)"

    # ── Background buildings (silhouettes against sunset) ──
    bg_scroll = int(scroll * 0.4)
    for bx_b, bw, bh, style in bg_buildings:
        roof = bg_base - bh
        for y in range(max(0, roof), bg_base + 1):
            for dx in range(bw):
                sx = (bx_b + dx - bg_scroll) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    buf[y][sx] = "█"
                    col[y][sx] = "rgb(18,14,30)"
        # Architectural details
        center = bx_b + bw // 2
        if style == "dome" and bw >= 5:
            dome_w = bw // 2
            for dx in range(-dome_w, dome_w + 1):
                sx = (center + dx - bg_scroll) % WORLD_W
                dy = int(math.sqrt(max(0, dome_w**2 - dx**2)) * 0.6)
                py = roof - dy
                if 0 <= sx < width and 0 <= py < height:
                    buf[py][sx] = "█"
                    col[py][sx] = "rgb(18,14,30)"
        elif style == "spire":
            for dy in range(1, min(4, bh // 2)):
                sx = (center - bg_scroll) % WORLD_W
                py = roof - dy
                if 0 <= sx < width and 0 <= py < height:
                    buf[py][sx] = "│"
                    col[py][sx] = "rgb(18,14,30)"
        elif style == "antenna":
            for dy in range(1, min(3, bh // 3)):
                sx = (center - bg_scroll) % WORLD_W
                py = roof - dy
                if 0 <= sx < width and 0 <= py < height:
                    buf[py][sx] = "╎"
                    col[py][sx] = "rgb(18,14,30)"
            # Blinking light
            sx = (center - bg_scroll) % WORLD_W
            py = roof - min(3, bh // 3)
            if 0 <= sx < width and 0 <= py < height:
                if math.sin(frame * 0.15 + bx_b) > 0.3:
                    buf[py][sx] = "●"
                    col[py][sx] = "rgb(255,40,40)"

        # Faint warm windows in bg
        for wy in range(2, bh, 3):
            for wx in range(1, bw - 1, 3):
                sx = (bx_b + wx - bg_scroll) % WORLD_W
                py = bg_base - bh + wy
                if 0 <= sx < width and 0 <= py < height:
                    if (bx_b + wx) * 17 + wy * 31 & 3 == 0:
                        buf[py][sx] = "▪"
                        col[py][sx] = "rgb(90,70,50)"

    # ── Midground buildings ──
    mid_scroll = int(scroll * 0.65)
    for bx_m, bw, bh, shade in mid_buildings:
        roof = mid_base - bh
        for y in range(max(0, roof), mid_base + 1):
            for dx in range(bw):
                sx = (bx_m + dx - mid_scroll) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    buf[y][sx] = "█"
                    col[y][sx] = f"rgb({shade},{shade-5},{shade+10})"
        # Mid windows — warmer
        for wy in range(1, bh, 2):
            for wx in range(1, bw - 1, 2):
                sx = (bx_m + wx - mid_scroll) % WORLD_W
                py = mid_base - bh + wy
                if 0 <= sx < width and 0 <= py < height:
                    h = (bx_m + wx) * 13 + wy * 29
                    if h % 3 < 2:
                        phase = h % 1000 / 1000.0 * 6.28
                        lit = math.sin(frame * 0.012 + phase) > -0.2
                        if lit:
                            c = ["rgb(220,170,80)", "rgb(200,150,70)", "rgb(180,140,90)"][h % 3]
                            buf[py][sx] = "▪"
                            col[py][sx] = c

    # ── Foreground buildings ──
    for bi, b in enumerate(fg_buildings):
        bx_f, bw, bh, shade = b["x"], b["w"], b["h"], b["shade"]
        roof = road_y - bh

        for y in range(max(0, roof), road_y):
            for dx in range(bw):
                sx = (bx_f + dx - scroll_i) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    if dx == 0 or dx == bw - 1:
                        buf[y][sx] = "│"
                        col[y][sx] = f"rgb({shade+15},{shade+12},{shade+20})"
                    elif y == roof:
                        buf[y][sx] = "▄"
                        col[y][sx] = f"rgb({shade+20},{shade+18},{shade+25})"
                    else:
                        buf[y][sx] = "█"
                        col[y][sx] = f"rgb({shade},{shade-3},{shade+10})"

        # Windows — slow flicker, warm glow
        for wx, wy, wtype in fg_wins[bi]:
            for ddx in range(2):
                sx = (bx_f + wx + ddx - scroll_i) % WORLD_W
                py = roof + wy
                if 0 <= sx < width and 0 <= py < height:
                    win_id = (bx_f + wx + ddx) * 17 + py * 31
                    phase = win_id % 1000 / 1000.0 * 6.28
                    lit = math.sin(frame * 0.015 + phase) > -0.3
                    if lit:
                        if wtype == "warm":
                            col[py][sx] = "rgb(255,210,90)"
                        elif wtype == "cool":
                            col[py][sx] = "rgb(140,180,220)"
                        elif wtype == "amber":
                            col[py][sx] = "rgb(240,170,60)"
                        buf[py][sx] = "█"

    # ── Neon signs ──
    for ns_x, b_x, b_w, b_h, sy_off, word, ncolor in neon_signs:
        roof = road_y - b_h
        sign_y = roof + sy_off
        pulse = 0.6 + 0.4 * math.sin(frame * 0.08 + hash(word))
        for ci, ch in enumerate(word):
            sx = (ns_x + ci - scroll_i) % WORLD_W
            if 0 <= sx < width and 0 <= sign_y < height:
                if pulse > 0.35:
                    buf[sign_y][sx] = ch
                    col[sign_y][sx] = f"bold {ncolor}"
                else:
                    buf[sign_y][sx] = ch
                    col[sign_y][sx] = "rgb(50,30,30)"

    # ── Road / sidewalk ──
    if 0 <= road_y < height:
        for x in range(width):
            buf[road_y][x] = "▀"
            col[road_y][x] = "rgb(60,55,50)"

    # ── Cars on road ──
    car1_x = int((frame * 1.5) % (width + 20)) - 10
    car2_x = width - int((frame * 1.0 + 60) % (width + 20)) + 10
    if 0 <= road_y < height:
        for dx in range(3):
            cx = car1_x + dx
            if 0 <= cx < width:
                buf[road_y][cx] = "▀"
                col[road_y][cx] = "rgb(255,240,140)" if dx == 0 else "rgb(100,90,85)"
        for dx in range(3):
            cx = car2_x + dx
            if 0 <= cx < width:
                buf[road_y][cx] = "▀"
                col[road_y][cx] = "rgb(255,60,50)" if dx == 2 else "rgb(80,80,90)"

    # ── Water with reflections ──
    for y in range(water_y, height):
        depth = (y - water_y) / max(1, height - water_y)
        for x in range(width):
            # Base water color — dark with warm tint from sunset
            wr = int(12 + 15 * (1 - depth))
            wg = int(15 + 10 * (1 - depth))
            wb = int(25 + 15 * (1 - depth))

            # Ripple pattern
            ripple = math.sin(x * 0.3 + frame * 0.06 + y * 0.8) * 0.5 + 0.5
            wave = math.sin(x * 0.15 + frame * 0.03 - y * 0.4) * 0.5 + 0.5

            # Reflect sky sunset colors into water
            sky_t = 0.7 + depth * 0.25
            sr, sg, sb = sky_color(sky_t)
            reflect_strength = (1 - depth) * 0.3 * ripple
            wr = int(wr + sr * reflect_strength)
            wg = int(wg + sg * reflect_strength)
            wb = int(wb + sb * reflect_strength)

            # Reflect building windows — shimmer column above
            if y == water_y and 0 <= road_y - 1 < height:
                above = col[road_y - 1][x] if col[road_y - 1][x] else ""
                if "255,210" in above or "240,170" in above or "255,240" in above:
                    if ripple > 0.4:
                        wr = min(255, wr + 40)
                        wg = min(255, wg + 30)

            if wave > 0.7:
                buf[y][x] = "~"
            elif ripple > 0.6:
                buf[y][x] = "≈"
            else:
                buf[y][x] = random.choice(["·", "∼", " ", " "])

            col[y][x] = f"rgb({min(255,wr)},{min(255,wg)},{min(255,wb)})"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.12)
