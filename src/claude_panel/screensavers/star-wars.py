from rich.text import Text
import random
import math

# Star Wars — Imperial patrol over Endor
# Star Destroyer looming above, TIE fighters on patrol, the forest moon below

random.seed(42)

# ── Color helpers ──
def lc(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t), int(a[2]+(b[2]-a[2])*t))

def rgb(c):
    return f"rgb({max(0,min(255,c[0]))},{max(0,min(255,c[1]))},{max(0,min(255,c[2]))})"

# ── Layout ──
planet_top = int(height * 0.62)  # where the planet's curved horizon starts
sd_cy = int(height * 0.22)      # Star Destroyer vertical center

# ── Stars — three parallax layers ──
stars = []
for layer in range(3):
    speed = 0.02 + layer * 0.015
    count = width // (3 - layer) + 10
    for _ in range(count):
        stars.append({
            "x": random.uniform(0, width),
            "y": random.randint(0, planet_top + 2),
            "br": random.uniform(0.2, 1.0),
            "ph": random.uniform(0, 6.28),
            "spd": speed,
            "ch": random.choice(["·", "·", "∗", "✦", ".", "·"]),
            "layer": layer,
        })

# ── Star Destroyer shape — defined as horizontal slices (y_offset, x_left, x_right) ──
# Iconic wedge shape pointing right
sd_half_len = min(width // 3, 28)
sd_slices = []
for i in range(sd_half_len * 2 + 1):
    t = i / (sd_half_len * 2)  # 0 at back, 1 at tip
    # Wedge narrows toward the tip (right side)
    half_h = max(0, int((1 - t) * 4.5 + 0.5))
    x_offset = i - sd_half_len
    sd_slices.append((x_offset, half_h))

# Bridge tower — small bump on top near the back
bridge_x_start = -sd_half_len + 4
bridge_x_end = -sd_half_len + 12
bridge_h = 3

# ── TIE Fighters — small sprites ──
ties = []
for _ in range(5):
    ties.append({
        "x": random.uniform(-10, width + 10),
        "y": random.uniform(int(height * 0.08), int(height * 0.55)),
        "vx": random.uniform(-0.8, 0.8),
        "vy": random.uniform(-0.15, 0.15),
        "size": random.choice([1, 1, 2]),
        "ph": random.uniform(0, 6.28),
    })

# ── Laser bolts ──
lasers = []
for _ in range(4):
    lasers.append({
        "x": random.uniform(0, width),
        "y": random.uniform(5, height * 0.5),
        "vx": random.uniform(2.5, 5.0) * random.choice([-1, 1]),
        "vy": random.uniform(-0.3, 0.3),
        "life": 0,
        "max_life": random.randint(15, 40),
        "color": random.choice(["green", "red"]),
        "active": False,
    })

# ── Engine glow particles ──
engine_particles = []
for _ in range(15):
    engine_particles.append({
        "x": 0, "y": 0,
        "vx": random.uniform(-1.5, -0.3),
        "vy": random.uniform(-0.2, 0.2),
        "life": 0,
        "max_life": random.randint(8, 20),
    })

random.seed()

# ── Main render loop ──
for frame in range(3000):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    # Slow drift for the Star Destroyer
    sd_cx = width // 2 + int(math.sin(frame * 0.004) * width * 0.08)
    sd_y = sd_cy + int(math.sin(frame * 0.006 + 1.0) * 2)

    # ═══ DEEP SPACE BACKGROUND ═══
    for y in range(height):
        t = y / max(1, height - 1)
        if t < 0.5:
            # Deep space — very dark blue/black with subtle variation
            s = t / 0.5
            r = int(2 + s * 3)
            g = int(2 + s * 4)
            b = int(8 + s * 12)
        else:
            # Approaching planet glow zone
            s = (t - 0.5) / 0.5
            r = int(5 + s * 8)
            g = int(6 + s * 10)
            b = int(20 + s * 15)
        for x in range(width):
            col[y][x] = f"rgb({r},{g},{b})"

    # ═══ NEBULA — subtle purple/blue haze ═══
    nebula_cx = width * 0.7 + math.sin(frame * 0.002) * 8
    nebula_cy = height * 0.2
    for y in range(int(height * 0.55)):
        for x in range(width):
            dx = (x - nebula_cx) / (width * 0.35)
            dy = (y - nebula_cy) / (height * 0.3)
            d2 = dx * dx + dy * dy
            if d2 < 1.0:
                intensity = (1.0 - d2) * 0.15
                noise = math.sin(x * 0.15 + y * 0.2 + frame * 0.01) * 0.5 + 0.5
                intensity *= noise
                base = col[y][x]
                # Parse existing and add nebula tint
                r = int(5 + intensity * 35)
                g = int(3 + intensity * 12)
                b = int(15 + intensity * 55)
                col[y][x] = f"rgb({r},{g},{b})"

    # ═══ STARS ═══
    for s in stars:
        sx = (s["x"] + frame * s["spd"]) % (width + 4) - 2
        sy = s["y"]
        ix, iy = int(sx), int(sy)
        if 0 <= ix < width and 0 <= iy < height and iy < planet_top:
            tw = 0.4 + 0.6 * math.sin(frame * 0.08 + s["ph"])
            br = s["br"] * tw
            if br > 0.25:
                v = int(80 + 175 * br)
                # Slight color variation — some bluish, some warm
                if s["layer"] == 0:
                    c = (v, v, min(255, v + 15))
                elif s["layer"] == 1:
                    c = (min(255, v + 5), v, min(255, v + 25))
                else:
                    c = (min(255, v + 10), min(255, v + 5), v)
                buf[iy][ix] = s["ch"]
                col[iy][ix] = rgb(c)

    # ═══ PLANET (Forest Moon of Endor) — curved horizon ═══
    for y in range(planet_top, height):
        t_surface = (y - planet_top) / max(1, height - planet_top)
        scroll = frame * 0.15
        for x in range(width):
            # Forest texture with scrolling for rotation effect
            tx = (x + scroll) * 0.06
            ty = y * 0.09

            # Multi-octave noise for organic forest look
            n1 = math.sin(tx * 1.8 + ty * 1.2) * 0.35
            n2 = math.sin(tx * 0.6 - ty * 1.6 + 1.5) * 0.30
            n3 = math.sin(tx * 2.8 + ty * 0.4 + frame * 0.006) * 0.15
            forest_noise = n1 + n2 + n3

            # Base forest colors — rich deep greens with earthy tones
            g_val = int(28 + forest_noise * 18 + t_surface * 20)
            r_val = int(5 + forest_noise * 6 + t_surface * 8)
            b_val = int(8 + forest_noise * 6 + t_surface * 4)

            # Lighter highland patches
            highland = math.sin(tx * 0.3 + ty * 0.5 + 2.0)
            if highland > 0.4:
                ht = (highland - 0.4) / 0.6
                g_val = int(g_val + ht * 15)
                r_val = int(r_val + ht * 8)

            # Cloud/atmosphere patches
            cloud = math.sin((x + scroll * 0.4) * 0.03 + y * 0.05) * math.sin((x - scroll * 0.25) * 0.055 + y * 0.025)
            if cloud > 0.25:
                cloud_t = (cloud - 0.25) / 0.75
                r_val = int(r_val + cloud_t * 80)
                g_val = int(g_val + cloud_t * 82)
                b_val = int(b_val + cloud_t * 75)
                buf[y][x] = "░" if cloud_t > 0.6 else " "
            else:
                # Softer canopy — mostly color, minimal character texture
                if forest_noise > 0.25:
                    buf[y][x] = "·"
                elif forest_noise > 0.05:
                    buf[y][x] = " "
                elif forest_noise > -0.1:
                    buf[y][x] = "░"
                else:
                    buf[y][x] = " "

            col[y][x] = f"rgb({max(0,min(255,r_val))},{max(0,min(255,g_val))},{max(0,min(255,b_val))})"

    # Atmosphere rim — multi-layer glow at the planet edge
    for band in range(4):
        y = planet_top - band
        if y < 0 or y >= height:
            continue
        for x in range(width):
            dx = abs(x - width // 2)
            glow = max(0, 1.0 - dx / (width * 0.52))
            glow = glow ** (1.0 + band * 0.4)  # sharper falloff for higher bands
            intensity = glow * (1.0 - band * 0.22)
            if intensity > 0.03:
                if band == 0:
                    c = lc((15, 50, 25), (130, 255, 160), intensity)
                    buf[y][x] = "═"
                elif band == 1:
                    c = lc((8, 30, 15), (80, 200, 120), intensity * 0.7)
                    buf[y][x] = "─"
                else:
                    c = lc((4, 15, 8), (40, 120, 70), intensity * 0.4)
                    if buf[y][x] == " ":
                        buf[y][x] = " "
                col[y][x] = rgb(c)

    # ═══ STAR DESTROYER ═══
    # Draw the wedge shape
    for x_off, half_h in sd_slices:
        x = sd_cx + x_off
        if x < 0 or x >= width:
            continue
        for dy in range(-half_h, half_h + 1):
            y = sd_y + dy
            if y < 0 or y >= height:
                continue

            # Hull coloring — darker at edges, lighter on top face
            edge_t = abs(dy) / max(1, half_h) if half_h > 0 else 0
            length_t = (x_off + sd_half_len) / (sd_half_len * 2)  # 0=back, 1=tip

            if dy < 0:
                # Top face — lighter, catching starlight
                base = lc((145, 150, 158), (100, 105, 112), edge_t)
            elif dy == 0:
                # Center line — panel detail
                base = (110, 114, 120)
            else:
                # Bottom face — darker/shadowed
                base = lc((72, 76, 82), (42, 44, 48), edge_t)

            # Darken toward the tip
            tip_dark = 1.0 - length_t * 0.15
            base = (int(base[0] * tip_dark), int(base[1] * tip_dark), int(base[2] * tip_dark))

            # Panel line texture
            panel = ((x * 7 + y * 13) % 11)
            if panel < 1 and half_h > 1:
                ch = "▒"
                base = (int(base[0] * 0.7), int(base[1] * 0.7), int(base[2] * 0.7))
            elif panel < 3:
                ch = "▓"
            else:
                ch = "█"

            buf[y][x] = ch
            col[y][x] = rgb(base)

    # Bridge tower
    for bx in range(bridge_x_start, bridge_x_end + 1):
        x = sd_cx + bx
        if x < 0 or x >= width:
            continue
        # Tower gets shorter toward edges
        bt = abs(bx - (bridge_x_start + bridge_x_end) // 2) / max(1, (bridge_x_end - bridge_x_start) // 2)
        bh = max(1, int(bridge_h * (1 - bt * 0.5)))
        for dy in range(-bh - 4, -3):  # Above the main hull
            y = sd_y + dy
            if y < 0 or y >= height:
                continue
            base = lc((100, 105, 110), (75, 78, 82), abs(dy + 4) / max(1, bh))
            buf[y][x] = "█"
            col[y][x] = rgb(base)

    # Bridge viewport — tiny bright window
    bridge_mid_x = sd_cx + (bridge_x_start + bridge_x_end) // 2
    bridge_top_y = sd_y - bridge_h - 4
    if 0 <= bridge_mid_x < width and 0 <= bridge_top_y < height:
        buf[bridge_top_y][bridge_mid_x] = "▪"
        col[bridge_top_y][bridge_mid_x] = "bold rgb(180,200,255)"
    for ddx in [-1, 1]:
        bvx = bridge_mid_x + ddx
        if 0 <= bvx < width and 0 <= bridge_top_y < height:
            buf[bridge_top_y][bvx] = "▪"
            col[bridge_top_y][bvx] = "rgb(120,140,180)"

    # Engine glow — bright blue/white ion engines at the back
    engine_x = sd_cx - sd_half_len
    for ey_off in range(-4, 5):
        ey = sd_y + ey_off
        if ey < 0 or ey >= height:
            continue
        for ex_off in range(-5, 2):
            ex = engine_x + ex_off
            if ex < 0 or ex >= width:
                continue
            d = math.sqrt(ex_off * ex_off * 0.6 + ey_off * ey_off * 0.4)
            if d < 4.5:
                intensity = (1.0 - d / 4.5)
                intensity = intensity * intensity  # quadratic for bright core
                flicker = 0.75 + 0.25 * math.sin(frame * 0.3 + ey_off * 1.8)
                intensity *= flicker
                # Core is white-blue, outer is deep blue
                r = int(80 + intensity * 175)
                g = int(120 + intensity * 135)
                b = int(200 + intensity * 55)
                ch = "█" if intensity > 0.5 else "▓" if intensity > 0.25 else "░"
                buf[ey][ex] = ch
                col[ey][ex] = f"bold rgb({min(255,r)},{min(255,g)},{min(255,b)})"

    # ═══ TIE FIGHTERS ═══
    for tie in ties:
        # Patrol movement — sweeping arcs
        tie["x"] += tie["vx"] + math.sin(frame * 0.02 + tie["ph"]) * 0.4
        tie["y"] += tie["vy"] + math.cos(frame * 0.015 + tie["ph"] * 1.3) * 0.12

        # Wrap around
        if tie["x"] < -15:
            tie["x"] = width + 10
        elif tie["x"] > width + 15:
            tie["x"] = -10
        if tie["y"] < 2:
            tie["y"] = 2
        elif tie["y"] > height * 0.55:
            tie["y"] = height * 0.55

        tx, ty = int(tie["x"]), int(tie["y"])

        if tie["size"] == 2:
            # Larger TIE — hexagonal wings + cockpit
            # Wings: solid panels
            for wing_dx in [-3, 3]:
                for wing_dy in range(-2, 3):
                    wx, wy = tx + wing_dx, ty + wing_dy
                    if 0 <= wx < width and 0 <= wy < height:
                        buf[wy][wx] = "┃"
                        col[wy][wx] = "bold rgb(110,115,120)"
            for wing_dx in [-2, 2]:
                for wing_dy in range(-2, 3):
                    wx, wy = tx + wing_dx, ty + wing_dy
                    if 0 <= wx < width and 0 <= wy < height:
                        buf[wy][wx] = "│"
                        col[wy][wx] = "rgb(85,88,92)"
            # Cockpit — bright center ball
            if 0 <= tx < width and 0 <= ty < height:
                buf[ty][tx] = "◉"
                col[ty][tx] = "bold rgb(140,150,170)"
            # Struts connecting wings to cockpit
            for sdx in [-1, 1]:
                sx = tx + sdx
                if 0 <= sx < width and 0 <= ty < height:
                    buf[ty][sx] = "─"
                    col[ty][sx] = "rgb(90,92,96)"
            # Engine glow — tiny red dot behind cockpit
            if 0 <= tx < width and 0 <= ty + 1 < height:
                eng_fl = 0.5 + 0.5 * math.sin(frame * 0.3 + tie["ph"])
                if eng_fl > 0.3:
                    buf[ty][tx] = "◉"
                    col[ty][tx] = f"bold rgb({int(140 * eng_fl)},{int(150 * eng_fl)},{int(170 * eng_fl)})"
        else:
            # Small TIE — recognizable H shape
            if 0 <= tx < width and 0 <= ty < height:
                buf[ty][tx] = "◦"
                col[ty][tx] = "bold rgb(130,135,145)"
            for sdx in [-1, 1]:
                sx = tx + sdx
                if 0 <= sx < width and 0 <= ty < height:
                    buf[ty][sx] = "│"
                    col[ty][sx] = "rgb(100,102,106)"
                for sdy in [-1, 1]:
                    sy = ty + sdy
                    if 0 <= sx < width and 0 <= sy < height:
                        buf[sy][sx] = "│"
                        col[sy][sx] = "rgb(80,82,86)"

    # ═══ LASER BOLTS ═══
    for laser in lasers:
        if not laser["active"]:
            if random.random() < 0.008:
                laser["active"] = True
                laser["life"] = 0
                laser["x"] = random.uniform(width * 0.1, width * 0.9)
                laser["y"] = random.uniform(height * 0.05, height * 0.5)
                laser["vx"] = random.uniform(2.5, 5.0) * random.choice([-1, 1])
                laser["vy"] = random.uniform(-0.3, 0.3)
                laser["color"] = random.choice(["green", "green", "red"])
            continue

        laser["x"] += laser["vx"]
        laser["y"] += laser["vy"]
        laser["life"] += 1

        if laser["life"] > laser["max_life"] or laser["x"] < -5 or laser["x"] > width + 5:
            laser["active"] = False
            continue

        lx, ly = int(laser["x"]), int(laser["y"])
        fade = 1.0 - laser["life"] / laser["max_life"]

        # Draw bolt — 3-char streak
        for streak in range(3):
            sx = lx - int(laser["vx"] * 0.3 * streak)
            if 0 <= sx < width and 0 <= ly < height:
                if laser["color"] == "green":
                    intensity = fade * (1.0 - streak * 0.3)
                    r = int(30 * intensity)
                    g = int(255 * intensity)
                    b = int(30 * intensity)
                else:
                    intensity = fade * (1.0 - streak * 0.3)
                    r = int(255 * intensity)
                    g = int(40 * intensity)
                    b = int(40 * intensity)
                ch = "═" if streak == 0 else "─" if streak == 1 else "·"
                buf[ly][sx] = ch
                col[ly][sx] = f"bold rgb({max(0,r)},{max(0,g)},{max(0,b)})"

    # ═══ RENDER ═══
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.07)
