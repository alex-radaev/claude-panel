from rich.text import Text
import random
import math

# Downtown Ann Arbor — State Theatre on S. State Street
# Art Deco tower with red neon STATE sign, green neon border,
# wide marquee with chase lights, brick stepped facade, autumn evening

ground_y = height - 3
sidewalk_y = ground_y - 1

# ── Night sky palette (dark moody like the reference photos) ──
sky_palette = [
    (0.00, (8, 6, 22)),
    (0.15, (12, 10, 30)),
    (0.35, (18, 15, 38)),
    (0.55, (25, 20, 42)),
    (0.75, (35, 25, 48)),
    (0.90, (42, 30, 45)),
    (1.00, (50, 32, 42)),
]

def sky_color(t):
    for i in range(len(sky_palette) - 1):
        t0, c0 = sky_palette[i]
        t1, c1 = sky_palette[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / max(0.001, t1 - t0)
            return tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))
    return sky_palette[-1][1]

random.seed(42)
stars = [(random.randint(0, width - 1), random.randint(0, int(height * 0.25)),
          random.uniform(0, 6.28), random.uniform(0.3, 1.0)) for _ in range(width // 6)]

# ══════════════════════════════════════════════════════════
# STATE THEATRE LAYOUT
# ══════════════════════════════════════════════════════════

# The theater takes center stage
theater_w = max(20, int(width * 0.4))
theater_x = (width - theater_w) // 2
theater_mid = theater_x + theater_w // 2

# Central tower — the neon blade sign (odd width so letters center perfectly)
tower_w = max(7, theater_w // 4)
if tower_w % 2 == 0:
    tower_w += 1
tower_x = theater_mid - tower_w // 2
tower_h = max(8, int(height * 0.35))
tower_roof = sidewalk_y - tower_h
tower_arch_h = max(1, tower_h // 10)

# Facade: the brick area between tower base and marquee (just 2 rows)
facade_gap = 2
facade_base_h = tower_h  # full height from tower roof to sidewalk
facade_base_roof = tower_roof  # where tower starts

# Step tiers flanking the tower
tier1_w = max(2, theater_w // 7)
tier1_h = max(3, int(height * 0.08))  # short step
tier1_roof = tower_roof + int(tower_h * 0.4)

tier2_w = max(2, theater_w // 7)
tier2_h = max(2, int(height * 0.04))
tier2_roof = tower_roof + int(tower_h * 0.55)

# Marquee — positioned at ~60% down from tower roof
mq_offset = int(tower_h * 0.65)
marquee_overhang = 3
mq_left = max(0, theater_x - marquee_overhang)
mq_right = min(width - 1, theater_x + theater_w + marquee_overhang)
mq_h = max(4, int(height * 0.1))
mq_top = tower_roof + mq_offset
mq_bot = mq_top + mq_h - 1

# Entrance below marquee
ent_left = theater_mid - max(4, theater_w // 5)
ent_right = theater_mid + max(4, theater_w // 5)

# ── Flanking buildings ──
left_buildings = []
bx = 0
while bx < theater_x - 1:
    bw = random.randint(5, max(6, min(10, theater_x - bx - 1)))
    bh = random.randint(max(4, int(height * 0.15)), max(5, int(height * 0.28)))
    left_buildings.append({"x": bx, "w": bw, "h": bh})
    bx += bw

right_buildings = []
bx = theater_x + theater_w + 1
while bx < width - 2:
    bw = random.randint(5, max(6, min(10, width - bx)))
    bh = random.randint(max(4, int(height * 0.15)), max(5, int(height * 0.28)))
    right_buildings.append({"x": bx, "w": bw, "h": bh})
    bx += bw

all_side = left_buildings + right_buildings

# ── Burton Memorial Tower (U-M clock tower) — background landmark ──
# Smaller, narrow, odd width for symmetry
burton_w = max(5, width // 12)
if burton_w % 2 == 0:
    burton_w += 1
burton_x = width - burton_w - max(3, width // 8)
burton_h = max(10, int(height * 0.45))
burton_roof = sidewalk_y - burton_h

shop_names = ["TARGET", "CHIPOTLE", "URBAN", "NOODLES", "BOOKS", "CAFE"]
shop_signs = []
for i, b in enumerate(all_side):
    name = shop_names[i % len(shop_names)]
    if len(name) <= b["w"] - 2:
        shop_signs.append((b, name))

# ── Trees ──
trees = []
for tx in range(4, width - 4, max(8, width // 4)):
    if abs(tx - theater_mid) > theater_w // 2 + 4:
        trees.append({"x": tx, "h": random.randint(3, max(4, int(height * 0.1))),
                       "cw": random.randint(3, 5)})

# ── Streetlights ──
streetlights = []
for lx in range(5, width - 3, max(12, width // 3)):
    if abs(lx - theater_mid) > theater_w // 2 + 3:
        streetlights.append(lx)

# ── Leaves ──
num_leaves = max(5, width // 6)
leaves = []
for _ in range(num_leaves):
    leaves.append([random.uniform(0, width), random.uniform(-height, height),
                   random.uniform(0.1, 0.3), random.uniform(0, 6.28),
                   random.choice(["orange", "red", "gold", "rust"])])

leaf_colors = {
    "orange": "rgb(220,120,30)", "red": "rgb(190,45,35)",
    "gold": "rgb(210,180,40)", "rust": "rgb(160,70,30)",
}

# ── Cars ──
cars = []
for _ in range(3):
    cx = random.uniform(0, width)
    cdir = random.choice([-1, 1])
    cspeed = random.uniform(0.3, 0.7)
    ccolor = random.choice(["red", "white", "blue", "silver"])
    cars.append([cx, cdir, cspeed, ccolor])

car_body_colors = {
    "red": "rgb(180,40,35)", "white": "rgb(180,180,175)",
    "blue": "rgb(40,60,140)", "silver": "rgb(120,120,130)",
}

# ── Pedestrians ──
peds = []
for _ in range(max(2, width // 16)):
    peds.append([random.uniform(0, width), random.choice([-1, 1]), random.uniform(0.1, 0.25)])

random.seed()

for frame in range(300):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    fg = [[""] * width for _ in range(height)]
    bg = [["black"] * width for _ in range(height)]

    # ── Sky ──
    for y in range(sidewalk_y):
        t = y / max(1, sidewalk_y)
        r, g, b = sky_color(t)
        for x in range(width):
            fg[y][x] = f"rgb({r},{g},{b})"

    # ── Stars ──
    for sx, sy, ph, bright in stars:
        if 0 <= sx < width and 0 <= sy < height:
            tw = 0.5 + 0.5 * math.sin(frame * 0.04 + ph)
            if tw > 0.4:
                v = int(30 + tw * bright * 100)
                buf[sy][sx] = "." if tw < 0.65 else "*"
                fg[sy][sx] = f"rgb({v},{v},{int(v*0.85)})"

    # ── Burton Memorial Tower (background) ──
    burton_mid = burton_x + burton_w // 2

    # Teal/green pointed spire — centered
    spire_y = burton_roof - 2
    if 0 <= spire_y < height and 0 <= burton_mid < width:
        buf[spire_y][burton_mid] = "▲"
        fg[spire_y][burton_mid] = "rgb(100,190,160)"
    # Dome row — centered 3 chars
    dome_y = burton_roof - 1
    if 0 <= dome_y < height:
        for ddx in [-1, 0, 1]:
            px = burton_mid + ddx
            if 0 <= px < width:
                buf[dome_y][px] = "▄"
                fg[dome_y][px] = "rgb(90,175,148)"

    # Cornice
    if 0 <= burton_roof < height:
        for dx in range(burton_w):
            px = burton_x + dx
            if 0 <= px < width:
                buf[burton_roof][px] = "▀"
                fg[burton_roof][px] = "rgb(175,170,155)"

    # Tower body — light cream stone
    for y in range(max(0, burton_roof + 1), sidewalk_y):
        for dx in range(burton_w):
            px = burton_x + dx
            if 0 <= px < width and 0 <= y < height:
                if dx == 0 or dx == burton_w - 1:
                    buf[y][px] = "│"
                    fg[y][px] = "rgb(160,155,142)"
                else:
                    sv = 142 + ((px * 3 + y * 7) % 8)
                    buf[y][px] = "█"
                    fg[y][px] = f"rgb({sv},{sv-4},{sv-14})"

    # Vertical pilaster lines
    for y in range(max(0, burton_roof + 1), sidewalk_y):
        for pil_dx in [1, burton_w - 2]:
            px = burton_x + pil_dx
            if 0 <= px < width and 0 <= y < height:
                buf[y][px] = "│"
                fg[y][px] = "rgb(172,168,155)"

    # Dark arched windows near top
    arch_top = burton_roof + 2
    arch_h = max(2, burton_h // 5)
    for wy in range(arch_top, min(height, arch_top + arch_h)):
        for dx in range(2, burton_w - 2):
            px = burton_x + dx
            if 0 <= px < width and 0 <= wy < height:
                buf[wy][px] = "█"
                fg[wy][px] = "rgb(28,25,22)"

    # ── CLOCK FACE — the key feature ──
    clock_y = arch_top + arch_h + 1
    if 0 <= clock_y < height and 0 <= burton_mid < width:
        # Clock circle
        buf[clock_y][burton_mid] = "◉"
        fg[clock_y][burton_mid] = "bold rgb(240,235,215)"
        # Clock surround
        for ddx in [-1, 1]:
            cx = burton_mid + ddx
            if 0 <= cx < width:
                buf[clock_y][cx] = "○"
                fg[clock_y][cx] = "rgb(200,195,178)"
    # Second clock row for visibility
    clock_y2 = clock_y + 1
    if 0 <= clock_y2 < height and 0 <= burton_mid < width:
        buf[clock_y2][burton_mid] = "◎"
        fg[clock_y2][burton_mid] = "bold rgb(230,225,205)"

    # Diamond decoration
    diamond_y = clock_y + 2
    if 0 <= diamond_y < height and 0 <= burton_mid < width:
        buf[diamond_y][burton_mid] = "◆"
        fg[diamond_y][burton_mid] = "rgb(168,162,148)"

    # Small windows below
    for wy in range(diamond_y + 2, sidewalk_y - 1, 3):
        for dx in range(2, burton_w - 2):
            wpx = burton_x + dx
            if 0 <= wpx < width and 0 <= wy < height:
                phase = hash((wpx, wy)) % 1000 / 1000.0 * 6.28
                if math.sin(frame * 0.01 + phase) > 0.0:
                    buf[wy][wpx] = "▪"
                    fg[wy][wpx] = "rgb(185,170,115)"
                else:
                    buf[wy][wpx] = "▪"
                    fg[wy][wpx] = "rgb(42,38,32)"

    # ── Side buildings ──
    for bi, b in enumerate(all_side):
        bx_s, bw, bh = b["x"], b["w"], b["h"]
        roof = sidewalk_y - bh
        for y in range(max(0, roof), sidewalk_y):
            for dx in range(bw):
                px = bx_s + dx
                if 0 <= px < width and 0 <= y < height:
                    if dx == 0 or dx == bw - 1:
                        buf[y][px] = "│"
                        fg[y][px] = "rgb(50,32,22)"
                    elif y == roof:
                        buf[y][px] = "▄"
                        fg[y][px] = "rgb(60,40,28)"
                    else:
                        is_mortar = (y % 3 == 0) or ((px + (3 if (y // 3) % 2 else 0)) % 5 == 0)
                        if is_mortar:
                            buf[y][px] = "░"
                            fg[y][px] = "rgb(38,28,20)"
                        else:
                            sv = 58 + ((px * 7 + y * 13) % 10)
                            fg[y][px] = f"rgb({sv},{sv-16},{sv-25})"
                            buf[y][px] = "█"
            # Windows
            if (y - roof) >= 2 and (y - roof) % 3 == 1:
                for wx in range(2, bw - 2, 3):
                    wpx = bx_s + wx
                    if 0 <= wpx < width:
                        phase = hash((wpx, y)) % 1000 / 1000.0 * 6.28
                        if math.sin(frame * 0.012 + phase) > -0.3:
                            w = 0.7 + 0.3 * math.sin(frame * 0.02 + phase)
                            for ddx in range(2):
                                wpx2 = wpx + ddx
                                if 0 <= wpx2 < width and wpx2 < bx_s + bw - 1:
                                    buf[y][wpx2] = "█"
                                    fg[y][wpx2] = f"rgb({int(235*w)},{int(185*w)},{int(65*w)})"

        # Awning
        aw_y = sidewalk_y - 2
        if 0 <= aw_y < height:
            for dx in range(bw):
                px = bx_s + dx
                if 0 <= px < width:
                    buf[aw_y][px] = "▄"
                    cs = [("rgb(125,35,30)", "rgb(155,48,40)"),
                          ("rgb(30,70,40)", "rgb(45,90,52)"),
                          ("rgb(35,48,100)", "rgb(50,62,120)")][bi % 3]
                    fg[aw_y][px] = cs[0] if (dx // 2) % 2 == 0 else cs[1]

    # Shop signs
    sign_y = sidewalk_y - 3
    for b, name in shop_signs:
        sx = b["x"] + (b["w"] - len(name)) // 2
        if 0 <= sign_y < height:
            for ci, ch in enumerate(name):
                px = sx + ci
                if 0 <= px < width:
                    p = 0.6 + 0.4 * math.sin(frame * 0.04 + ci * 0.3 + hash(name) * 0.001)
                    buf[sign_y][px] = ch
                    fg[sign_y][px] = f"bold rgb({int(245*p)},{int(195*p)},{int(90*p)})"

    # ══════════════════════════════════════════════════
    # STATE THEATRE FACADE
    # ══════════════════════════════════════════════════

    # ── Base facade (dark red/brown brick with horizontal stripes) ──
    # Only draw from tier level down to marquee top
    facade_draw_top = min(tier1_roof, tier2_roof)
    for y in range(max(0, facade_draw_top), min(height, mq_top)):
        for dx in range(theater_w):
            px = theater_x + dx
            if 0 <= px < width and 0 <= y < height:
                stripe = (y % 2 == 0)
                if dx == 0 or dx == theater_w - 1:
                    buf[y][px] = "║"
                    fg[y][px] = "rgb(100,45,35)"
                elif stripe:
                    buf[y][px] = "█"
                    fg[y][px] = "rgb(120,48,38)"
                else:
                    buf[y][px] = "█"
                    fg[y][px] = "rgb(95,38,28)"

    # ── Stepped tiers (building steps up toward center) ──
    # Tier 2 (outer steps)
    for side in [-1, 1]:
        if side == -1:
            t2_left = theater_x + 2
            t2_right = tower_x - tier1_w - 1
        else:
            t2_left = tower_x + tower_w + tier1_w + 1
            t2_right = theater_x + theater_w - 3
        for y in range(max(0, tier2_roof), min(height, mq_top)):
            for x in range(t2_left, t2_right + 1):
                if 0 <= x < width and 0 <= y < height:
                    stripe = (y % 2 == 0)
                    buf[y][x] = "█"
                    fg[y][x] = "rgb(115,45,35)" if stripe else "rgb(90,35,26)"

    # Tier 1 (inner steps, taller)
    for side in [-1, 1]:
        if side == -1:
            t1_left = tower_x - tier1_w
            t1_right = tower_x - 1
        else:
            t1_left = tower_x + tower_w
            t1_right = tower_x + tower_w + tier1_w - 1
        for y in range(max(0, tier1_roof), min(height, mq_top)):
            for x in range(t1_left, t1_right + 1):
                if 0 <= x < width and 0 <= y < height:
                    stripe = (y % 2 == 0)
                    buf[y][x] = "█"
                    fg[y][x] = "rgb(110,42,32)" if stripe else "rgb(85,32,24)"

    # ── Central tower (the tall Art Deco blade) ──
    for y in range(max(0, tower_roof), mq_top):
        for dx in range(tower_w):
            px = tower_x + dx
            if 0 <= px < width and 0 <= y < height:
                buf[y][px] = "█"
                fg[y][px] = "rgb(42,18,15)"

    # Tower arch top (rounded)
    arch_center_y = tower_roof
    for dy in range(tower_arch_h):
        ry = arch_center_y - tower_arch_h + dy
        if 0 <= ry < height:
            # Narrowing arch
            narrow = int((tower_arch_h - dy) * 0.8)
            for dx in range(narrow, tower_w - narrow):
                px = tower_x + dx
                if 0 <= px < width:
                    buf[ry][px] = "█"
                    fg[ry][px] = "rgb(42,18,15)"

    # ── GREEN NEON BORDER around tower — bright and prominent ──
    green_pulse = 0.75 + 0.25 * math.sin(frame * 0.05)
    gr = int(50 * green_pulse)
    gg = int(255 * green_pulse)
    gb = int(120 * green_pulse)
    green_col = f"bold rgb({gr},{gg},{gb})"
    green_bg = f"rgb({int(12*green_pulse)},{int(55*green_pulse)},{int(25*green_pulse)})"

    # Left and right edges of tower
    for y in range(max(0, tower_roof - tower_arch_h), mq_top):
        for side_x in [tower_x, tower_x + tower_w - 1]:
            if 0 <= side_x < width and 0 <= y < height:
                # Check if this row is in the arch narrowing zone
                if y < tower_roof:
                    dy_from_top = y - (tower_roof - tower_arch_h)
                    narrow = int((tower_arch_h - dy_from_top) * 0.8)
                    if side_x == tower_x:
                        side_x_adj = tower_x + narrow
                    else:
                        side_x_adj = tower_x + tower_w - 1 - narrow
                    if 0 <= side_x_adj < width:
                        buf[y][side_x_adj] = "║"
                        fg[y][side_x_adj] = green_col
                        bg[y][side_x_adj] = green_bg
                else:
                    buf[y][side_x] = "║"
                    fg[y][side_x] = green_col
                    bg[y][side_x] = green_bg

    # Top arch of green border
    arch_top_y = tower_roof - tower_arch_h
    if 0 <= arch_top_y < height:
        for dx in range(1, tower_w - 1):
            px = tower_x + dx
            if 0 <= px < width:
                buf[arch_top_y][px] = "═"
                fg[arch_top_y][px] = green_col
                bg[arch_top_y][px] = green_bg

    # ── RED NEON "STATE" — spans full tower height ──
    state_text = "STATE"
    state_top = tower_roof + 2
    state_bot = mq_top - 3  # leave room for THEATRE
    # Distribute letters evenly across the full tower
    letter_spacing = max(1, (state_bot - state_top) // max(1, len(state_text) - 1))
    # Center the block vertically
    total_span = letter_spacing * (len(state_text) - 1)
    state_start_y = state_top + (state_bot - state_top - total_span) // 2

    for ci, ch in enumerate(state_text):
        sy = state_start_y + ci * letter_spacing
        if 0 <= sy < height:
            pulse = 0.75 + 0.25 * math.sin(frame * 0.08 + ci * 0.6)
            nr = int(255 * pulse)
            ng_v = int(40 * pulse)
            nb = int(28 * pulse)
            neon_col = f"bold rgb({nr},{ng_v},{nb})"
            neon_bg = f"rgb({int(90*pulse)},{int(12*pulse)},{int(10*pulse)})"

            # Draw letter 5 chars wide (══ LETTER ══) for max visibility
            for ddx in range(-2, 3):
                lx = theater_mid + ddx
                if 0 <= lx < width and tower_x < lx < tower_x + tower_w - 1:
                    if ddx == 0:
                        buf[sy][lx] = ch
                        fg[sy][lx] = neon_col
                        bg[sy][lx] = neon_bg
                    elif abs(ddx) == 1:
                        buf[sy][lx] = "═"
                        fg[sy][lx] = f"rgb({int(230*pulse)},{int(38*pulse)},{int(28*pulse)})"
                        bg[sy][lx] = f"rgb({int(90*pulse)},{int(14*pulse)},{int(10*pulse)})"
                    else:
                        buf[sy][lx] = "─"
                        fg[sy][lx] = f"rgb({int(180*pulse)},{int(28*pulse)},{int(20*pulse)})"
                        bg[sy][lx] = f"rgb({int(70*pulse)},{int(10*pulse)},{int(8*pulse)})"

            # Strong red glow halo — fill entire tower width
            for gdx in range(-tower_w // 2 + 1, tower_w // 2):
                gx = theater_mid + gdx
                if 0 <= gx < width and tower_x <= gx <= tower_x + tower_w - 1:
                    dist = abs(gdx) / max(1, tower_w // 2)
                    intensity = max(0, 1.0 - dist * 0.5)
                    r_glow = int(90 * pulse * intensity)
                    bg[sy][gx] = f"rgb({r_glow},{int(12*pulse*intensity)},{int(10*pulse*intensity)})"
            # Glow rows above/below each letter — extends 2 rows
            for gdy in [-1, 1]:
                gy = sy + gdy
                if 0 <= gy < height:
                    for gdx in range(-tower_w // 2 + 1, tower_w // 2):
                        gx = theater_mid + gdx
                        if 0 <= gx < width and tower_x < gx < tower_x + tower_w - 1:
                            if buf[gy][gx] == "█":
                                dist = abs(gdx) / max(1, tower_w // 2)
                                intensity = max(0, 0.8 - dist * 0.5)
                                bg[gy][gx] = f"rgb({int(60*pulse*intensity)},{int(8*pulse*intensity)},{int(6*pulse*intensity)})"

    # ── "THEATRE" horizontal at bottom of tower — green neon ──
    # Just above the marquee
    theatre_y = mq_top - 1
    theatre_text = "THEATRE"
    # If tower is too narrow for full text, truncate
    avail = tower_w - 2
    if len(theatre_text) > avail:
        theatre_text = theatre_text[:avail]
    if 0 <= theatre_y < height and len(theatre_text) > 0:
        ts = theater_mid - len(theatre_text) // 2
        pulse = 0.7 + 0.3 * math.sin(frame * 0.06)
        for ci, ch in enumerate(theatre_text):
            px = ts + ci
            if 0 <= px < width and tower_x < px < tower_x + tower_w - 1:
                buf[theatre_y][px] = ch
                fg[theatre_y][px] = f"bold rgb({int(50*pulse)},{int(240*pulse)},{int(110*pulse)})"
                bg[theatre_y][px] = f"rgb({int(10*pulse)},{int(50*pulse)},{int(22*pulse)})"
        # Also draw "THEATRE" on both sides of tower base (like the real building)
        for side in [-1, 1]:
            side_y = theatre_y
            if side == -1:
                side_x = tower_x - len(theatre_text) - 1
            else:
                side_x = tower_x + tower_w + 1
            for ci, ch in enumerate(theatre_text):
                px = side_x + ci
                if 0 <= px < width and 0 <= side_y < height:
                    buf[side_y][px] = ch
                    fg[side_y][px] = f"rgb({int(40*pulse)},{int(180*pulse)},{int(80*pulse)})"

    # ── Green neon vertical stripes flanking letters ──
    stripe_off = max(3, tower_w // 3)
    for y in range(max(0, tower_roof + 1), min(height, mq_top - 1)):
        for vx_off in [-stripe_off, stripe_off]:
            vx = theater_mid + vx_off
            if 0 <= vx < width and tower_x < vx < tower_x + tower_w - 1:
                gp = 0.55 + 0.35 * math.sin(frame * 0.04 + y * 0.15)
                buf[y][vx] = "│"
                fg[y][vx] = f"rgb({int(35*gp)},{int(200*gp)},{int(85*gp)})"
                bg[y][vx] = f"rgb({int(5*gp)},{int(30*gp)},{int(12*gp)})"

    # ══════════════════════════════════════════════════
    # MARQUEE
    # ══════════════════════════════════════════════════

    for y in range(max(0, mq_top), min(height, mq_bot + 1)):
        for x in range(mq_left, mq_right + 1):
            if 0 <= x < width and 0 <= y < height:
                if y == mq_top or y == mq_bot:
                    # Chase lights — golden bulbs
                    chase = ((x + frame // 2) % 3 == 0)
                    if chase:
                        buf[y][x] = "●"
                        fg[y][x] = "bold rgb(255,240,110)"
                        bg[y][x] = "rgb(80,62,15)"
                    else:
                        buf[y][x] = "○"
                        fg[y][x] = "rgb(140,115,50)"
                        bg[y][x] = "rgb(32,25,8)"
                else:
                    # White/light blue letter board
                    bg[y][x] = "rgb(160,185,210)"
                    buf[y][x] = " "
                    fg[y][x] = "rgb(10,10,15)"

    # Marquee text — two centered lines
    mq_center = (mq_left + mq_right) // 2
    mq_avail = mq_right - mq_left - 4
    marquee_lines = [
        ("BEST MOVIES & POPCORN", True),
        ("michtheater.org", False),
    ]
    for li, (line_text, is_bold) in enumerate(marquee_lines):
        text_y = mq_top + 1 + li
        if text_y > mq_bot - 1 or text_y >= height:
            break
        # Truncate if too wide
        if len(line_text) > mq_avail:
            line_text = line_text[:mq_avail]
        sx = mq_center - len(line_text) // 2
        for ci, ch in enumerate(line_text):
            px = sx + ci
            if mq_left < px < mq_right and 0 <= px < width and 0 <= text_y < height:
                buf[text_y][px] = ch
                fg[text_y][px] = "bold rgb(15,15,20)" if is_bold else "rgb(25,25,35)"

    # ── Bright red entrance area below marquee (like the real theater) ──
    for y in range(max(0, mq_bot + 1), sidewalk_y):
        for x in range(ent_left, ent_right + 1):
            if 0 <= x < width and 0 <= y < height:
                if x == ent_left or x == ent_right:
                    buf[y][x] = "│"
                    fg[y][x] = "rgb(200,60,48)"
                else:
                    buf[y][x] = "▓"
                    fg[y][x] = "rgb(210,62,48)"
                    bg[y][x] = "rgb(150,40,32)"
    # Red paint on facade flanking entrance
    for y in range(max(0, mq_bot + 1), sidewalk_y):
        for x in range(theater_x + 1, ent_left):
            if 0 <= x < width and 0 <= y < height:
                buf[y][x] = "█"
                fg[y][x] = "rgb(180,52,40)"
        for x in range(ent_right + 1, theater_x + theater_w - 1):
            if 0 <= x < width and 0 <= y < height:
                buf[y][x] = "█"
                fg[y][x] = "rgb(180,52,40)"

    # "STATE" horizontal neon sign on the right side of entrance
    state_h_y = mq_bot + 1
    state_h_text = "STATE"
    state_h_x = ent_right + 2
    if 0 <= state_h_y < height:
        pulse = 0.7 + 0.3 * math.sin(frame * 0.07)
        for ci, ch in enumerate(state_h_text):
            px = state_h_x + ci
            if 0 <= px < width and px < theater_x + theater_w:
                buf[state_h_y][px] = ch
                fg[state_h_y][px] = f"bold rgb({int(255*pulse)},{int(40*pulse)},{int(30*pulse)})"
                bg[state_h_y][px] = f"rgb({int(60*pulse)},{int(10*pulse)},{int(8*pulse)})"

    # ── Street trees ──
    for tree in trees:
        tx, th, cw = tree["x"], tree["h"], tree["cw"]
        trunk_top = sidewalk_y - th
        for y in range(trunk_top, sidewalk_y):
            if 0 <= tx < width and 0 <= y < height:
                buf[y][tx] = "│"
                fg[y][tx] = "rgb(70,48,25)"
        canopy_cy = trunk_top - 1
        for dy in range(-cw // 2 - 1, cw // 2 + 1):
            for dx in range(-cw, cw + 1):
                cy, cx = canopy_cy + dy, tx + dx
                if 0 <= cx < width and 0 <= cy < height:
                    dist = math.sqrt(dx * dx + dy * dy * 2.5)
                    if dist < cw:
                        t = (dx + dy * 2 + tx) % 7
                        sway = math.sin(frame * 0.025 + tx * 0.5 + dx * 0.3) * 0.3
                        if t < 2: r, gc, bc = 195+int(sway*30), 75+int(sway*20), 18
                        elif t < 4: r, gc, bc = 215+int(sway*25), 145+int(sway*20), 28
                        elif t < 6: r, gc, bc = 175+int(sway*20), 48+int(sway*15), 22
                        else: r, gc, bc = 155+int(sway*20), 115+int(sway*15), 18
                        edge = 1 - dist / cw
                        dens = edge * (0.5 + 0.5 * math.sin(dx * 1.5 + dy * 2.0 + tx))
                        if dens > 0.15:
                            ch = "█" if dens > 0.5 else ("▓" if dens > 0.3 else "░")
                            buf[cy][cx] = ch
                            fg[cy][cx] = f"rgb({min(255,r)},{min(255,gc)},{max(0,bc)})"

    # ── Streetlights ──
    for lx in streetlights:
        for y in range(sidewalk_y - 4, sidewalk_y):
            if 0 <= lx < width and 0 <= y < height:
                buf[y][lx] = "│"
                fg[y][lx] = "rgb(65,65,70)"
        lamp_y = sidewalk_y - 5
        if 0 <= lx < width and 0 <= lamp_y < height:
            fl = 0.9 + 0.1 * math.sin(frame * 0.08 + lx * 0.3)
            buf[lamp_y][lx] = "◉"
            fg[lamp_y][lx] = f"bold rgb({int(255*fl)},{int(208*fl)},{int(90*fl)})"

    # ── Sidewalk ──
    if 0 <= sidewalk_y < height:
        for x in range(width):
            if buf[sidewalk_y][x] == " " or fg[sidewalk_y][x] == "":
                buf[sidewalk_y][x] = "░"
                fg[sidewalk_y][x] = "rgb(68,64,58)"

    # ── Road ──
    for y in range(ground_y, height):
        for x in range(width):
            if 0 <= y < height:
                buf[y][x] = " "
                fg[y][x] = "rgb(25,22,28)"
                bg[y][x] = "rgb(20,18,22)"

    # ── Cars on road ──
    road_y = ground_y
    for car in cars:
        car[0] += car[1] * car[2]
        if car[0] > width + 5: car[0] = -4.0
        elif car[0] < -5: car[0] = float(width + 4)
        cx_i = int(car[0])
        body_col = car_body_colors[car[3]]
        # Car body (3-4 chars wide)
        for ddx in range(4):
            cpx = cx_i + ddx
            if 0 <= cpx < width and 0 <= road_y < height:
                buf[road_y][cpx] = "▀"
                fg[road_y][cpx] = body_col
        # Headlights / taillights
        if car[1] > 0:  # moving right
            hl_x = cx_i + 4
            tl_x = cx_i - 1
        else:
            hl_x = cx_i - 1
            tl_x = cx_i + 4
        if 0 <= hl_x < width and 0 <= road_y < height:
            buf[road_y][hl_x] = "●"
            fg[road_y][hl_x] = "bold rgb(255,250,180)"
        if 0 <= tl_x < width and 0 <= road_y < height:
            buf[road_y][tl_x] = "●"
            fg[road_y][tl_x] = "rgb(220,30,25)"

    # ── Neon reflections on wet road ──
    for y in range(ground_y, height):
        if 0 <= y < height:
            depth = (y - ground_y + 1)
            # Theater neon glow on road
            for x in range(max(0, theater_x - 5), min(width, theater_x + theater_w + 6)):
                dist_center = abs(x - theater_mid) / max(1, theater_w / 2 + 5)
                glow = max(0, 0.4 * (1 - dist_center) / max(1, depth))
                if glow > 0.02:
                    ripple = 0.6 + 0.4 * math.sin(x * 0.3 + frame * 0.05 + y * 0.8)
                    # Mix of red (STATE sign) and green (border) and gold (marquee)
                    rr = min(80, int(glow * ripple * 200))
                    rg = min(50, int(glow * ripple * 100))
                    rb = min(30, int(glow * ripple * 50))
                    if buf[y][x] == " ":
                        buf[y][x] = random.choice(["≈", "~", "·", " "])
                        fg[y][x] = f"rgb({rr},{rg},{rb})"
                        bg[y][x] = f"rgb({int(rr*0.3)},{int(rg*0.25)},{int(rb*0.2)})"

    # ── Warm sidewalk glow from marquee ──
    if 0 <= sidewalk_y < height:
        mcx = (mq_left + mq_right) // 2
        for x in range(mq_left - 2, mq_right + 3):
            if 0 <= x < width:
                dist = abs(x - mcx) / max(1, (mq_right - mq_left) / 2 + 2)
                glow = max(0, 0.5 * (1 - dist * dist))
                p = 0.85 + 0.15 * math.sin(frame * 0.03)
                glow *= p
                if glow > 0.02:
                    bg[sidewalk_y][x] = f"rgb({min(100,int(55+glow*160))},{min(72,int(38+glow*105))},{min(25,int(8+glow*28))})"

    # ── Falling leaves ──
    leaf_chars = ["*", "~", "'", ","]
    for leaf in leaves:
        leaf[1] += leaf[2]
        leaf[0] += math.sin(frame * 0.04 + leaf[3]) * 0.25
        leaf[0] += math.sin(frame * 0.01) * 0.1
        if leaf[1] > sidewalk_y:
            leaf[1] = random.uniform(-3, 0)
            leaf[0] = random.uniform(0, width)
        lx_i = int(leaf[0]) % width
        ly_i = int(leaf[1])
        if 0 <= lx_i < width and 0 <= ly_i < height:
            buf[ly_i][lx_i] = leaf_chars[int(leaf[3]*10) % len(leaf_chars)]
            fg[ly_i][lx_i] = leaf_colors[leaf[4]]

    # ── Pedestrians ──
    for ped in peds:
        ped[0] += ped[1] * ped[2]
        if ped[0] > width + 2: ped[0] = -1.0
        elif ped[0] < -2: ped[0] = float(width + 1)
        px_i = int(ped[0])
        if 0 <= px_i < width and 0 <= sidewalk_y < height:
            buf[sidewalk_y][px_i] = "♟"
            fg[sidewalk_y][px_i] = "rgb(150,130,110)"
        head_y = sidewalk_y - 1
        if 0 <= px_i < width and 0 <= head_y < height:
            if buf[head_y][px_i] in [" ", "░"]:
                buf[head_y][px_i] = "○"
                fg[head_y][px_i] = "rgb(170,148,122)"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            f_col = fg[y][x]
            b_col = bg[y][x]
            style = ""
            if f_col: style = f_col
            if b_col and b_col != "black":
                style += f" on {b_col}" if style else f"on {b_col}"
            if not style: style = "on black"
            line.append(buf[y][x], style=style)
        canvas.write(line)

    await sleep(0.08)
