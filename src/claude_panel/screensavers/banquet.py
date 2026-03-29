from rich.text import Text
import random
import math

# Inspired by Magritte's "The Banquet" — red sun, dark trees swaying in night wind

sun_cx = width // 2
sun_base_y = height // 3
sun_r = min(width, height) // 6

# Tree trunks — just a few visible ones, like the painting
tree_zone_left = width // 5
tree_zone_right = width * 4 // 5
zone_w = tree_zone_right - tree_zone_left
trees = []
num_trees = random.randint(5, 7)
for i in range(num_trees):
    # Spread them out with some variation
    tx = tree_zone_left + int(zone_w * (i + 0.5) / num_trees) + random.randint(-2, 2)
    trunk_h = random.randint(height // 5, height // 3)
    trunk_w = random.choice([1, 2, 2])  # some thicker
    phase = random.uniform(0, math.pi * 2)
    trees.append((tx, trunk_h, trunk_w, phase))
trees.sort(key=lambda t: t[0])

# Canopy — big round crown for a single tree
canopy_cx = width // 2
canopy_cy = height // 3
canopy_rx = width // 3
canopy_ry = height // 3

# Wall position
wall_y = height - height // 6

# Urn position
urn_x = width // 5

# Blowing leaves — more of them, they drift with wind
num_leaves = 25
leaves = []
for _ in range(num_leaves):
    lx = random.randint(tree_zone_left - 5, tree_zone_right + 5)
    ly = random.randint(canopy_cy, canopy_cy + canopy_ry)
    speed_y = random.uniform(0.1, 0.4)
    speed_x = random.uniform(0.3, 1.0)
    phase = random.uniform(0, math.pi * 2)
    leaves.append([float(lx), float(ly), speed_y, speed_x, phase])

for frame in range(400):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]
    colors = [["black"] * width for _ in range(height)]

    sun_cy = sun_base_y + int(math.sin(frame * 0.015) * 2)

    # Wind strength oscillates — gusts and lulls
    wind = math.sin(frame * 0.04) * 0.6 + math.sin(frame * 0.017) * 0.4
    wind_strength = wind * 3  # pixels of sway

    # --- Sky: flat muted coral ---
    for y in range(wall_y):
        for x in range(width):
            buf[y][x] = "█"
            colors[y][x] = "rgb(140,42,35)"

    # --- Sun ---
    for y in range(max(0, sun_cy - sun_r), min(wall_y, sun_cy + sun_r + 1)):
        for x in range(max(0, sun_cx - sun_r * 2), min(width, sun_cx + sun_r * 2 + 1)):
            dx = (x - sun_cx) / max(1, sun_r * 1.8)
            dy = (y - sun_cy) / max(1, sun_r * 0.9)
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= 0.85:
                buf[y][x] = "█"
                fg_r = int(240 + (1 - dist) * 15)
                fg_g = int(80 + (1 - dist) * 40)
                fg_b = int(35 + (1 - dist) * 20)
                colors[y][x] = f"rgb({min(255, fg_r)},{min(255,fg_g)},{fg_b})"
            elif dist <= 1.0:
                buf[y][x] = "▓"
                colors[y][x] = "rgb(230,75,40)"
            elif dist <= 1.1:
                buf[y][x] = "░"
                colors[y][x] = "rgb(190,55,35)"

    # --- Tree canopy: swaying in wind ---
    # The whole canopy shifts slightly with wind, and edges ripple
    canopy_shift_x = wind_strength * 1.5

    for y in range(max(0, canopy_cy - canopy_ry - 2), min(wall_y, canopy_cy + canopy_ry + 2)):
        # Each row ripples with a wave — higher rows sway more (like a real tree)
        height_factor = 1.0 - (y - canopy_cy + canopy_ry) / max(1, canopy_ry * 2)
        row_shift = canopy_shift_x * height_factor
        # Add a ripple wave along the row
        ripple = math.sin(y * 0.3 + frame * 0.12) * 1.5 * height_factor

        for x in range(max(0, canopy_cx - canopy_rx - 5), min(width, canopy_cx + canopy_rx + 5)):
            # Shifted coordinates
            sx = x - row_shift - ripple
            dx = (sx - canopy_cx) / max(1, canopy_rx)
            dy = (y - canopy_cy) / max(1, canopy_ry)
            if dy > 0:
                dy *= 0.65
            dist = math.sqrt(dx * dx + dy * dy)

            # Edge noise — changes per frame for rustling effect
            edge_noise = math.sin(x * 0.7 + y * 0.5 + frame * 0.2) * 0.08
            threshold = 0.82 + edge_noise + random.random() * 0.12
            if dist > threshold:
                continue

            # Sun peek-through
            sdx = (x - sun_cx) / max(1, sun_r * 1.8)
            sdy = (y - sun_cy) / max(1, sun_r * 0.9)
            on_sun = math.sqrt(sdx * sdx + sdy * sdy) <= 1.0

            if on_sun:
                sun_dist = math.sqrt(sdx * sdx + sdy * sdy)
                # Core of sun: mostly clear so disc shape reads. Edge: more leaves
                clear_chance = 0.75 if sun_dist < 0.6 else 0.4
                if random.random() < clear_chance:
                    continue

            # Density varies with wind — gusty = more gaps
            wind_gaps = abs(wind) * 0.1
            if random.random() < wind_gaps and dist > 0.5:
                continue

            # Rustling: char changes frame to frame at edges
            if dist > 0.65:
                buf[y][x] = random.choice(["░", "▒", "·", "▓"])
            elif dist > 0.35:
                buf[y][x] = random.choice(["▒", "▓", "█"])
            else:
                buf[y][x] = random.choice(["█", "▓"])

            if on_sun:
                colors[y][x] = random.choice([
                    "rgb(55,50,65)", "rgb(65,55,70)", "rgb(60,52,68)",
                ])
            else:
                colors[y][x] = random.choice([
                    "rgb(35,40,55)", "rgb(40,45,60)", "rgb(38,42,58)",
                    "rgb(42,47,62)", "rgb(36,40,56)",
                ])

    # --- Single trunk that grows into canopy + darker vein paths suggesting branches ---
    tc = "rgb(15,15,25)"
    trunk_x = width // 2
    trunk_w = 5

    # Trunk: from wall up into the lower canopy
    trunk_top = canopy_cy + canopy_ry // 4
    for y in range(trunk_top, wall_y):
        sway_factor = (wall_y - y) / max(1, wall_y - trunk_top)
        sway = int(wind_strength * sway_factor * 0.5)
        # Trunk narrows as it goes up
        w = max(2, trunk_w - (trunk_top + 3 - y) // 4) if y < trunk_top + 6 else trunk_w
        for dx in range(w):
            draw_x = trunk_x - w // 2 + dx + sway
            if 0 <= draw_x < width:
                buf[y][draw_x] = "█"
                colors[y][draw_x] = tc

    # Darker vein paths inside canopy — precomputed, suggest internal branches
    if frame == 0:
        _veins = set()
        # A few organic paths radiating from trunk top area
        for _ in range(5):
            vx = float(trunk_x + random.randint(-1, 1))
            vy = float(trunk_top)
            angle = random.uniform(-2.5, -0.5) if random.random() < 0.5 else random.uniform(-2.6, -0.4)
            length = random.randint(canopy_ry // 3, canopy_ry * 2 // 3)
            for step in range(length):
                vx += math.cos(angle) * 1.2
                vy += math.sin(angle) * 0.8
                angle += random.uniform(-0.15, 0.15)
                _veins.add((int(vx), int(vy)))
    for (vx, vy) in _veins:
        svx = vx + int(wind_strength * max(0, (trunk_top - vy)) / max(1, canopy_ry) * 0.8)
        if 0 <= svx < width and 0 <= vy < height:
            if buf[vy][svx] in ("█", "▓", "▒"):
                colors[vy][svx] = tc

    # --- Ground mist ---
    for y in range(max(0, wall_y - 3), wall_y):
        mist = (y - (wall_y - 3)) / 3.0
        for x in range(width):
            if buf[y][x] == " " and random.random() < mist * 0.35:
                buf[y][x] = random.choice(["░", "·"])
                g = int(50 + mist * 30)
                colors[y][x] = f"rgb({g-5},{g},{g-3})"

    # --- Blowing leaves ---
    leaf_chars = ["◦", "·", "∘", "°", ","]
    leaf_colors = ["rgb(45,45,60)", "rgb(55,50,65)", "rgb(50,48,62)", "rgb(40,42,55)"]
    for lf in leaves:
        lx, ly, spy, spx, phase = lf
        # Wind pushes leaves sideways, gravity pulls down
        ly += spy
        lx += spx * wind + math.sin(frame * 0.1 + phase) * 0.6
        # Leaves tumble — slight vertical wobble
        ly += math.sin(frame * 0.15 + phase * 2) * 0.2

        # Reset when off screen or below wall
        if ly > wall_y - 1 or lx > width + 5 or lx < -5:
            # Respawn from canopy edge
            ly = float(random.randint(canopy_cy, canopy_cy + canopy_ry // 2))
            lx = float(random.randint(tree_zone_left, tree_zone_right))
            lf[3] = random.uniform(0.3, 1.0)  # new x speed
        lf[0], lf[1] = lx, ly

        ix, iy = int(lx), int(ly)
        if 0 <= ix < width and 0 <= iy < wall_y:
            if buf[iy][ix] == " " or buf[iy][ix] in ("·", ".", "∘"):
                buf[iy][ix] = random.choice(leaf_chars)
                colors[iy][ix] = random.choice(leaf_colors)

    # --- Stone wall ---
    for y in range(wall_y, height):
        row = y - wall_y
        for x in range(width):
            brick_off = 4 if row % 2 == 1 else 0
            if (x + brick_off) % 8 == 0:
                buf[y][x] = "│"
                g = random.randint(75, 90)
            else:
                buf[y][x] = "▒"
                g = random.randint(88, 110)
            colors[y][x] = f"rgb({g-3},{g},{g-6})"
        if y == wall_y:
            for x in range(width):
                buf[y][x] = "▄"
                colors[y][x] = "rgb(120,118,110)"

    # --- Stone urn — large classical vase ---
    uc = width // 5  # urn center x
    ug = "rgb(130,128,120)"
    um = "rgb(110,108,102)"
    ud = "rgb(85,83,78)"
    if uc + 6 < width and wall_y - 10 >= 0:
        # Wide pedestal base
        for dx in range(-3, 6):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 1][x] = "█"
                colors[wall_y - 1][x] = ud
        for dx in range(-2, 5):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 2][x] = "▄"
                colors[wall_y - 2][x] = ug
        # Pedestal column
        for dy in range(3, 5):
            for dx in range(-1, 4):
                x = uc + dx
                y = wall_y - dy
                if 0 <= x < width and 0 <= y < height:
                    buf[y][x] = "█"
                    colors[y][x] = um
        # Pedestal cap
        for dx in range(-2, 5):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 5][x] = "▄"
                colors[wall_y - 5][x] = ug
        # Bowl body — wide
        for dx in range(-3, 6):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 6][x] = "█"
                colors[wall_y - 6][x] = um
                buf[wall_y - 7][x] = "█"
                colors[wall_y - 7][x] = ud
        # Bowl taper
        for dx in range(-2, 5):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 8][x] = "█"
                colors[wall_y - 8][x] = um
        # Rim flare
        for dx in range(-4, 7):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 9][x] = "▄"
                colors[wall_y - 9][x] = ug
        # Lip
        for dx in range(-3, 6):
            x = uc + dx
            if 0 <= x < width:
                buf[wall_y - 10][x] = "▀"
                colors[wall_y - 10][x] = ug

    # --- Render ---
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=colors[y][x])
        canvas.write(line)

    await sleep(0.12)
