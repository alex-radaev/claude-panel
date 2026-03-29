from rich.text import Text
import random
import math

# Neon Street — slow-scrolling cyberpunk cityscape (Roku-style)
# Camera pans right continuously, revealing endless city

road_y = height - 2
WORLD_W = width * 4  # generate a wide world, tile it

# ── Sky layers ──
sky_layers = [
    (0.0,  0.15, (8, 8, 25)),
    (0.15, 0.30, (12, 12, 35)),
    (0.30, 0.45, (18, 18, 50)),
    (0.45, 0.55, (25, 22, 55)),
    (0.55, 0.65, (30, 25, 50)),
    (0.65, 0.75, (20, 18, 40)),
]

# ── Generate world buildings ──
random.seed(33)

# Background buildings (tall, dark)
bg_base = road_y - int(height * 0.10)
bg_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 2)
    bw = random.randint(3, 8)
    bh = random.randint(4, int(height * 0.28))
    bg_buildings.append((bx, bw, bh))
    bx += bw

# Midground buildings
mid_base = road_y - int(height * 0.04)
mid_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 3)
    bw = random.randint(4, 9)
    bh = random.randint(3, int(height * 0.18))
    mid_buildings.append((bx, bw, bh))
    bx += bw

# Foreground buildings (short, detailed)
fg_buildings = []
bx = 0
while bx < WORLD_W:
    bx += random.randint(0, 1)
    bw = random.randint(5, 13)
    bh = random.randint(3, max(4, int(height * 0.14)))
    shade = random.randint(30, 55)
    fg_buildings.append({"x": bx, "w": bw, "h": bh, "shade": shade})
    bx += bw

# Foreground windows
fg_wins = []
for b in fg_buildings:
    wins = []
    for wy in range(1, b["h"] - 1, 2):
        for wx in range(1, b["w"] - 2, 3):
            if random.random() < 0.7:
                wtype = random.choice(["pink", "pink", "cyan", "blue", "warm"])
                wins.append((wx, wy, wtype))
    fg_wins.append(wins)

# Static clouds — low, near bg building tops
clouds_static = []
for _ in range(8):
    cx = random.randint(0, WORLD_W)
    cy = bg_base - int(height * 0.25) + random.randint(-2, 4)
    cw = random.randint(14, 28)
    ch = random.randint(2, 4)
    opacity = random.uniform(0.35, 0.6)
    clouds_static.append((cx, cy, cw, ch, opacity))

# Stars — fixed in sky (don't scroll, or scroll very slowly)
stars = [(random.randint(0, width - 1), random.randint(0, int(height * 0.45)),
          random.uniform(0, 6.28)) for _ in range(width // 3)]

random.seed()

# Flowing clouds — these move independently in the sky
flow_clouds = []
random.seed(55)
for _ in range(8):
    cx = random.randint(-10, width + 10)
    cy = random.randint(1, int(height * 0.4))
    cw = random.randint(10, 22)
    ch = random.randint(2, 3)
    speed = random.uniform(0.03, 0.12)
    opacity = random.uniform(0.2, 0.5)
    flow_clouds.append({"x": float(cx), "y": cy, "w": cw, "h": ch,
                         "speed": speed, "opacity": opacity})
random.seed()

# Scroll speed
SCROLL_SPEED = 0.3

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    scroll = frame * SCROLL_SPEED
    scroll_i = int(scroll)

    # ── Sky ──
    for y in range(road_y):
        t = y / max(1, road_y)
        r, g, b = 8, 8, 25
        for ly_s, ly_e, (lr, lg, lb) in sky_layers:
            if ly_s <= t < ly_e:
                r, g, b = lr, lg, lb
                break
        else:
            r, g, b = 20, 18, 40
        for x in range(width):
            col[y][x] = f"rgb({r},{g},{b})"

    # ── Stars (don't scroll, or parallax very slow) ──
    star_offset = int(scroll * 0.05)
    for sx, sy, ph in stars:
        ax = (sx - star_offset) % width
        if 0 <= ax < width and 0 <= sy < height:
            tw = 0.5 + 0.5 * math.sin(frame * 0.04 + ph)
            if tw > 0.35:
                v = int(60 + tw * 100)
                buf[sy][ax] = "·" if tw < 0.7 else "+"
                col[sy][ax] = f"rgb({int(v*0.7)},{v},{v})"

    # ── Flowing clouds (independent movement) ──
    for cloud in flow_clouds:
        cloud["x"] += cloud["speed"]
        if cloud["x"] > width + cloud["w"]:
            cloud["x"] = float(-cloud["w"])
        cx_i = int(cloud["x"])
        cy, cw, ch, op = cloud["y"], cloud["w"], cloud["h"], cloud["opacity"]
        for dy in range(ch):
            center_row = ch / 2.0
            row_t = 1.0 - abs(dy - center_row) / max(1, center_row + 0.5)
            row_w = max(3, int(cw * row_t))
            off = (cw - row_w) // 2
            for dx in range(row_w):
                px = cx_i + off + dx
                py = cy + dy
                if 0 <= px < width and 0 <= py < height:
                    edge = 1.0 - abs(dx - row_w // 2) / max(1, row_w // 2)
                    v = int((30 + edge * 25) * op)
                    buf[py][px] = "▓" if edge > 0.5 else "░"
                    col[py][px] = f"rgb({v+5},{v+8},{v+18})"

    # ── Static clouds (scroll with world, near buildings) ──
    for cx, cy, cw, ch, op in clouds_static:
        for dy in range(ch):
            center_row = ch / 2.0
            row_t = 1.0 - abs(dy - center_row) / max(1, center_row + 0.5)
            row_w = max(3, int(cw * row_t))
            off = (cw - row_w) // 2
            for dx in range(row_w):
                world_x = cx + off + dx
                screen_x = (world_x - scroll_i) % WORLD_W
                if screen_x < 0:
                    screen_x += WORLD_W
                if 0 <= screen_x < width:
                    py = cy + dy
                    if 0 <= py < height:
                        edge = 1.0 - abs(dx - row_w // 2) / max(1, row_w // 2)
                        v = int((50 + edge * 35) * op)
                        buf[py][screen_x] = "█" if edge > 0.6 else ("▓" if edge > 0.3 else "░")
                        col[py][screen_x] = f"rgb({v+12},{v+15},{v+22})"

    # ── Background buildings (scroll slow — parallax) ──
    bg_scroll = int(scroll * 0.5)
    for bx, bw, bh in bg_buildings:
        for y in range(max(0, bg_base - bh), bg_base + 1):
            for dx in range(bw):
                sx = (bx + dx - bg_scroll) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    buf[y][sx] = "█"
                    col[y][sx] = "rgb(15,14,28)"
        # Faint windows
        for wy in range(2, bh, 3):
            for wx in range(1, bw - 1, 3):
                sx = (bx + wx - bg_scroll) % WORLD_W
                py = bg_base - bh + wy
                if 0 <= sx < width and 0 <= py < height:
                    win_hash = (bx + wx) * 17 + wy * 31
                    if win_hash % 3 == 0:
                        buf[py][sx] = "▪"
                        col[py][sx] = "rgb(70,65,95)"

    # ── Midground buildings (scroll medium) ──
    mid_scroll = int(scroll * 0.75)
    for bx, bw, bh in mid_buildings:
        for y in range(max(0, mid_base - bh), mid_base + 1):
            for dx in range(bw):
                sx = (bx + dx - mid_scroll) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    buf[y][sx] = "█"
                    col[y][sx] = "rgb(22,20,38)"
        for wy in range(1, bh, 2):
            for wx in range(1, bw - 1, 2):
                sx = (bx + wx - mid_scroll) % WORLD_W
                py = mid_base - bh + wy
                if 0 <= sx < width and 0 <= py < height:
                    win_hash = (bx + wx) * 13 + wy * 29
                    if win_hash % 3 < 2:
                        c = ["rgb(120,80,140)", "rgb(80,120,180)", "rgb(180,130,170)"][win_hash % 3]
                        buf[py][sx] = "▪"
                        col[py][sx] = c

    # ── Foreground buildings (scroll at full speed) ──
    for bi, b in enumerate(fg_buildings):
        bx, bw, bh, shade = b["x"], b["w"], b["h"], b["shade"]
        roof = road_y - bh

        for y in range(max(0, roof), road_y):
            for dx in range(bw):
                sx = (bx + dx - scroll_i) % WORLD_W
                if 0 <= sx < width and 0 <= y < height:
                    if dx == 0 or dx == bw - 1:
                        buf[y][sx] = "│"
                        col[y][sx] = f"rgb({shade+20},{shade+20},{shade+35})"
                    elif y == roof:
                        buf[y][sx] = "▄"
                        col[y][sx] = f"rgb({shade+25},{shade+25},{shade+40})"
                    else:
                        buf[y][sx] = "█"
                        col[y][sx] = f"rgb({shade},{shade},{shade+15})"

        # Windows — slow flicker
        for wx, wy, wtype in fg_wins[bi]:
            for ddx in range(2):
                sx = (bx + wx + ddx - scroll_i) % WORLD_W
                py = roof + wy
                if 0 <= sx < width and 0 <= py < height:
                    win_id = (bx + wx + ddx) * 17 + (roof + wy) * 31
                    is_off = abs(frame % 200 - win_id % 200) < 3
                    if not is_off:
                        if wtype == "pink":
                            col[py][sx] = "rgb(255,80,140)"
                        elif wtype == "cyan":
                            col[py][sx] = "rgb(60,200,240)"
                        elif wtype == "blue":
                            col[py][sx] = "rgb(80,120,220)"
                        elif wtype == "warm":
                            col[py][sx] = "rgb(255,220,100)"
                        buf[py][sx] = "█"

    # ── Road — static, no dashes ──
    for y in range(road_y, height):
        for x in range(width):
            buf[y][x] = "█"
            col[y][x] = "rgb(22,22,28)"
    # Sidewalk
    if 0 <= road_y < height:
        for x in range(width):
            buf[road_y][x] = "▀"
            col[road_y][x] = "rgb(55,55,65)"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.15)
