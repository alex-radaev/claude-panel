from rich.text import Text
import random
import math

# Sea Life — vibrant underwater world with fish, jellyfish, coral, seaweed, and bubbles

random.seed()

# ── Water color gradient — surface light to deep ocean ──
def water_color(y, x, frame):
    t = y / max(1, height - 1)
    # Caustic light patterns — rippling light from surface
    caustic = 0.5 + 0.5 * math.sin(x * 0.15 + frame * 0.06) * math.cos(y * 0.12 + frame * 0.04)
    caustic *= max(0, 1 - t * 1.5)  # fades with depth
    r = int(5 + t * 8 + caustic * 25)
    g = int(30 + t * 15 - t * 30 + caustic * 40)
    b = int(80 + t * 30 - t * 50 + caustic * 20)
    return f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})"

# ── Fish species — (right-facing, left-facing, name, color) ──
fish_species = [
    ("><>",      "<><",      "clownfish",  "rgb(255,130,20)"),
    ("><>",      "<><",      "blue tang",  "rgb(40,120,255)"),
    ("><>",      "<><",      "red snapper","rgb(220,60,60)"),
    ("><))°>",   "<°((<>",   "angelfish",  "rgb(255,220,50)"),
    ("><))°>",   "<°((<>",   "parrotfish", "rgb(50,220,150)"),
    ("><(((º>",  "<º)))><",  "swordfish",  "rgb(140,180,220)"),
    ("><(((º>",  "<º)))><",  "tuna",       "rgb(100,150,200)"),
    ("><>",      "<><",      "tiny",       "rgb(255,180,200)"),
    (">><>",     "<><<",     "neon tetra", "rgb(0,255,200)"),
    (">><>",     "<><<",     "guppy",      "rgb(255,100,255)"),
]

# ── Fish instances ──
random.seed(42)
fish = []
for _ in range(random.randint(8, 14)):
    sp = random.choice(fish_species)
    fx = random.randint(0, width - 1)
    fy = random.randint(3, height - 6)
    speed = random.uniform(0.2, 0.7)
    direction = random.choice([-1, 1])
    wobble_phase = random.uniform(0, 6.28)
    fish.append({
        "right": sp[0], "left": sp[1],
        "color": sp[3], "name": sp[2],
        "x": float(fx), "y": float(fy),
        "speed": speed, "dir": direction,
        "wobble": wobble_phase,
    })

# ── Jellyfish ──
jellies = []
for _ in range(random.randint(3, 5)):
    jx = random.randint(5, width - 5)
    jy = random.randint(2, height // 2)
    jellies.append({
        "x": float(jx), "y": float(jy),
        "speed": random.uniform(0.02, 0.08),
        "phase": random.uniform(0, 6.28),
        "color": random.choice([
            "rgb(200,100,255)", "rgb(100,200,255)", "rgb(255,150,200)",
            "rgb(150,255,200)", "rgb(255,200,100)",
        ]),
        "size": random.randint(2, 4),
    })

# ── Coral reef along the bottom ──
coral_data = []
for x in range(width):
    if random.random() < 0.6:
        c_height = random.randint(2, 6)
        c_type = random.choice(["branch", "brain", "fan", "tube"])
        c_color = random.choice([
            "rgb(255,80,100)", "rgb(255,140,60)", "rgb(255,200,80)",
            "rgb(200,80,200)", "rgb(255,120,180)", "rgb(80,200,160)",
            "rgb(220,100,50)", "rgb(180,60,120)",
        ])
        coral_data.append({"x": x, "h": c_height, "type": c_type, "color": c_color})

# ── Seaweed — bottom (growing up) and top (hanging down) ──
seaweed_bottom = []
for _ in range(random.randint(15, 25)):
    sx = random.randint(0, width - 1)
    s_height = random.choice([
        random.randint(3, 6),
        random.randint(6, 10),
        random.randint(10, max(11, height * 2 // 3)),
        random.randint(max(11, height * 3 // 4), max(12, height - 2)),
    ])
    s_phase = random.uniform(0, 6.28)
    shade = random.choice([
        "rgb(30,160,60)", "rgb(20,130,50)", "rgb(40,180,80)",
        "rgb(50,140,70)", "rgb(25,170,45)", "rgb(35,190,65)",
        "rgb(20,150,40)", "rgb(45,170,55)",
    ])
    seaweed_bottom.append({"x": sx, "h": s_height, "phase": s_phase, "color": shade})


# ── Bubbles ──
bubbles = []
for _ in range(random.randint(12, 25)):
    bubbles.append({
        "x": float(random.randint(0, width - 1)),
        "y": float(random.randint(0, height - 1)),
        "speed": random.uniform(0.1, 0.4),
        "wobble": random.uniform(0, 6.28),
        "size": random.choice(["°", "○", "◦", "·", "◯"]),
    })
random.seed()

# ── Sea turtle (rare, majestic) ──
turtle = {
    "x": float(random.randint(width // 4, width * 3 // 4)),
    "y": float(height // 3),
    "speed": 0.15,
    "dir": 1,
}

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    # ── Water background with caustics ──
    for y in range(height):
        for x in range(width):
            col[y][x] = water_color(y, x, frame)

    # ── Light rays from surface — soft diagonal shafts ──
    for ray in range(3):
        rx = int(width * (0.15 + ray * 0.35) + math.sin(frame * 0.02 + ray) * 6)
        angle = 0.15 * (ray - 1)  # slight diagonal spread
        for y in range(min(height * 2 // 3, height)):
            intensity = max(0, 1.0 - y / (height * 0.55))
            intensity *= 0.5 + 0.5 * math.sin(frame * 0.04 + y * 0.1 + ray)  # shimmer
            cx = rx + int(y * angle)
            spread = max(1, y // 6)
            for dx in range(-spread, spread + 1):
                x = cx + dx
                if 0 <= x < width and buf[y][x] == " ":
                    fade = intensity * (1 - abs(dx) / (spread + 1))
                    if fade > 0.08:
                        v = int(fade * 25)
                        # No characters — just brighten the water color
                        r_l = min(255, 5 + v + int(fade * 15))
                        g_l = min(255, 30 + v * 2 + int(fade * 25))
                        b_l = min(255, 80 + v + int(fade * 15))
                        col[y][x] = f"rgb({r_l},{g_l},{b_l})"

    # ── Seaweed — growing up from the bottom ──
    for sw in seaweed_bottom:
        base_y = height - 1
        for dy in range(sw["h"]):
            y = base_y - dy
            if y < 0 or y >= height:
                continue
            sway = math.sin(frame * 0.08 + sw["phase"] + dy * 0.4) * (dy * 0.4)
            x = int(sw["x"] + sway)
            if 0 <= x < width:
                ch = "}" if sway > 0 else "{"
                if dy == sw["h"] - 1:
                    ch = ")" if sway > 0 else "("
                buf[y][x] = ch
                col[y][x] = sw["color"]


    # ── Coral reef at bottom ──
    for cd in coral_data:
        x = cd["x"]
        if x >= width:
            continue
        for dy in range(cd["h"]):
            y = height - 1 - dy
            if y < 0 or y >= height:
                continue
            if cd["type"] == "branch":
                if dy == cd["h"] - 1:
                    ch = "Y"
                elif dy > cd["h"] // 2:
                    ch = random.choice(["╱", "╲", "│"])
                else:
                    ch = "│"
            elif cd["type"] == "brain":
                ch = random.choice(["◎", "◉", "●", "◐"]) if random.random() > 0.3 else "●"
            elif cd["type"] == "fan":
                spread = dy
                for fdx in range(-spread, spread + 1):
                    fx = x + fdx
                    if 0 <= fx < width and buf[y][fx] == " ":
                        buf[y][fx] = random.choice(["~", "≈", "∿"])
                        col[y][fx] = cd["color"]
                continue
            elif cd["type"] == "tube":
                ch = "║" if dy < cd["h"] - 1 else "○"
            else:
                ch = "█"
            if 0 <= x < width:
                buf[y][x] = ch
                col[y][x] = cd["color"]

    # ── Sandy bottom ──
    for x in range(width):
        y = height - 1
        if buf[y][x] == " ":
            grain = random.choice([".", "·", ",", " ", "∴"])
            buf[y][x] = grain
            col[y][x] = f"rgb({180 + random.randint(-20,20)},{160 + random.randint(-20,20)},{100 + random.randint(-20,20)})"

    # ── Jellyfish ──
    for jf in jellies:
        # Pulsating movement
        pulse = math.sin(frame * 0.12 + jf["phase"])
        jf["y"] += jf["speed"] * (-1 if pulse > 0 else 0.5)
        jf["x"] += math.sin(frame * 0.04 + jf["phase"]) * 0.3

        # Wrap vertically
        if jf["y"] < -5:
            jf["y"] = float(height - 3)
        elif jf["y"] > height:
            jf["y"] = -3.0

        jx, jy = int(jf["x"]) % width, int(jf["y"])
        sz = jf["size"]

        # Bell (dome)
        bell_w = sz + int(pulse * 0.8)
        if 0 <= jy < height:
            for dx in range(-bell_w, bell_w + 1):
                x = jx + dx
                if 0 <= x < width:
                    edge = abs(dx) / (bell_w + 1)
                    if edge < 0.9:
                        ch = "◠" if abs(dx) < bell_w else "("  if dx < 0 else ")"
                        buf[jy][x] = ch
                        col[jy][x] = jf["color"]

        # Tentacles
        for t_idx in range(max(2, sz)):
            t_dx = t_idx - sz // 2
            for t_dy in range(1, sz + 3):
                ty = jy + t_dy
                tx = jx + t_dx + int(math.sin(frame * 0.1 + t_idx + t_dy * 0.5) * 1.5)
                if 0 <= tx < width and 0 <= ty < height:
                    ch = "│" if t_dy < 2 else (":" if t_dy < 4 else "·")
                    buf[ty][tx] = ch
                    col[ty][tx] = jf["color"]

    # ── Fish ──
    for f in fish:
        # Movement
        f["x"] += f["speed"] * f["dir"]
        f["y"] += math.sin(frame * 0.08 + f["wobble"]) * 0.2

        # Pick body based on direction
        body = f["right"] if f["dir"] > 0 else f["left"]
        body_len = len(body)

        # Wrap
        if f["dir"] > 0 and f["x"] > width + body_len:
            f["x"] = float(-body_len)
        elif f["dir"] < 0 and f["x"] < -body_len:
            f["x"] = float(width + body_len)

        fx, fy = int(f["x"]), int(f["y"])
        fy = max(1, min(height - 3, fy))

        for i, ch in enumerate(body):
            x = fx + i
            if 0 <= x < width and 0 <= fy < height:
                buf[fy][x] = ch
                col[fy][x] = f"bold {f['color']}"

    # ── Sea turtle ──
    turtle["x"] += turtle["speed"] * turtle["dir"]
    turtle["y"] += math.sin(frame * 0.05) * 0.1
    if turtle["x"] > width + 10:
        turtle["dir"] = -1
    elif turtle["x"] < -10:
        turtle["dir"] = 1

    tx, ty = int(turtle["x"]), int(turtle["y"])
    ty = max(2, min(height - 5, ty))
    if turtle["dir"] > 0:
        turtle_art = [
            "  ___  ",
            "≈/° °\\≈",
            " \\_▄_/ ",
            "  w w  ",
        ]
    else:
        turtle_art = [
            "  ___  ",
            "≈/° °\\≈",
            " \\_▄_/ ",
            "  w w  ",
        ]
    for ri, row in enumerate(turtle_art):
        for ci, ch in enumerate(row):
            x = tx + ci
            y = ty + ri
            if 0 <= x < width and 0 <= y < height and ch != " ":
                buf[y][x] = ch
                col[y][x] = "bold rgb(60,180,100)"

    # ── Bubbles ──
    for bub in bubbles:
        bub["y"] -= bub["speed"]
        bub["x"] += math.sin(frame * 0.08 + bub["wobble"]) * 0.3

        if bub["y"] < 0:
            bub["y"] = float(height - 1)
            bub["x"] = float(random.randint(0, width - 1))

        bx, by = int(bub["x"]) % width, int(bub["y"])
        if 0 <= bx < width and 0 <= by < height:
            if buf[by][bx] == " ":
                buf[by][bx] = bub["size"]
                col[by][bx] = "rgb(150,220,255)"

    # ── Surface shimmer — top row ──
    for x in range(width):
        wave = math.sin(x * 0.2 + frame * 0.1) * 0.5 + math.sin(x * 0.07 + frame * 0.06) * 0.5
        if wave > 0.3:
            buf[0][x] = "▂"
            col[0][x] = "rgb(80,180,220)"
        elif wave > 0:
            buf[0][x] = "▁"
            col[0][x] = "rgb(60,150,200)"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.12)
