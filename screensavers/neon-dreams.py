from rich.text import Text
import random
import math

# Neon Dreams — floating geometric shapes, pulsing neon lines, dreamy particles

neon = [
    "rgb(255,0,150)", "rgb(0,255,200)", "rgb(255,50,255)",
    "rgb(0,180,255)", "rgb(255,200,0)", "rgb(150,0,255)",
    "rgb(255,100,200)", "rgb(0,255,150)",
]

# Floating shapes — triangles, diamonds, circles at random positions
shapes = []
for _ in range(random.randint(4, 7)):
    sx = random.randint(2, width - 10)
    sy = random.randint(2, height - 8)
    shape_type = random.choice(["triangle", "diamond", "hexagon"])
    color = random.choice(neon)
    speed_x = random.uniform(-0.3, 0.3)
    speed_y = random.uniform(-0.15, 0.15)
    size = random.randint(2, 4)
    shapes.append({"x": float(sx), "y": float(sy), "type": shape_type,
                    "color": color, "sx": speed_x, "sy": speed_y, "size": size})

# Horizontal neon lines
h_lines = []
for _ in range(random.randint(3, 5)):
    ly = random.randint(2, height - 3)
    lx = random.randint(0, width // 2)
    ll = random.randint(width // 4, width // 2)
    color = random.choice(neon)
    h_lines.append({"y": ly, "x": lx, "len": ll, "color": color, "phase": random.uniform(0, 6.28)})

# Dream words that float
words = ["DREAM", "NEON", "GLOW", "PULSE", "DRIFT", "HAZE", "ECHO", "FLOW"]
float_words = []
for _ in range(random.randint(2, 4)):
    word = random.choice(words)
    wx = random.randint(2, max(3, width - len(word) - 2))
    wy = random.randint(2, height - 3)
    color = random.choice(neon)
    float_words.append({"word": word, "x": float(wx), "y": float(wy),
                         "color": color, "sx": random.uniform(-0.2, 0.2),
                         "phase": random.uniform(0, 6.28)})

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    colors = [[""] * width for _ in range(height)]

    # Background — deep purple gradient
    for y in range(height):
        depth = y / height
        r = int(10 + depth * 15)
        g = int(2 + depth * 5)
        b = int(20 + depth * 30)
        for x in range(width):
            colors[y][x] = f"rgb({r},{g},{b})"

    # Stars — faint twinkling
    random.seed(42)
    for _ in range(width * height // 30):
        sx = random.randint(0, width - 1)
        sy = random.randint(0, height - 1)
        if buf[sy][sx] == " ":
            twinkle = 0.5 + 0.5 * math.sin(frame * 0.08 + sx * 0.3 + sy * 0.7)
            if twinkle > 0.3:
                bright = int(80 + twinkle * 100)
                buf[sy][sx] = random.choice([".", "+", "*", "·"])
                colors[sy][sx] = f"rgb({bright},{bright},{bright + 40})"
    random.seed(frame * 7 + 13)

    # Horizontal neon lines — pulse in brightness
    for hl in h_lines:
        pulse = 0.4 + 0.6 * math.sin(frame * 0.1 + hl["phase"])
        if pulse > 0.2:
            ly = int(hl["y"])
            for dx in range(hl["len"]):
                lx = (hl["x"] + dx + frame) % width
                if 0 <= ly < height and 0 <= lx < width:
                    fade = 1.0 - abs(dx - hl["len"] / 2) / (hl["len"] / 2)
                    if fade * pulse > 0.3:
                        buf[ly][lx] = "─"
                        colors[ly][lx] = f"bold {hl['color']}"

    # Floating shapes
    for shape in shapes:
        shape["x"] += shape["sx"]
        shape["y"] += shape["sy"]
        # Bounce off edges
        if shape["x"] < 1 or shape["x"] > width - 6:
            shape["sx"] *= -1
        if shape["y"] < 1 or shape["y"] > height - 6:
            shape["sy"] *= -1
        sx, sy = int(shape["x"]), int(shape["y"])
        sz = shape["size"]
        pulse = 0.5 + 0.5 * math.sin(frame * 0.08 + hash(shape["color"]))
        style = f"bold {shape['color']}" if pulse > 0.3 else f"dim {shape['color']}"

        if shape["type"] == "triangle":
            for row in range(sz):
                indent = sz - row - 1
                tri_w = 2 * row + 1
                for dx in range(tri_w):
                    px = sx + indent + dx
                    py = sy + row
                    if 0 <= px < width and 0 <= py < height:
                        ch = "△" if row == 0 else ("/" if dx == 0 else ("\\" if dx == tri_w - 1 else "─"))
                        buf[py][px] = ch
                        colors[py][px] = style

        elif shape["type"] == "diamond":
            points = [(0, -sz), (sz, 0), (0, sz), (-sz, 0)]
            for i in range(4):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % 4]
                steps = max(abs(x2 - x1), abs(y2 - y1))
                if steps == 0:
                    continue
                for s in range(steps + 1):
                    px = sx + sz + x1 + (x2 - x1) * s // steps
                    py = sy + sz + y1 + (y2 - y1) * s // steps
                    if 0 <= px < width and 0 <= py < height:
                        buf[py][px] = "◇" if s == 0 else "·"
                        colors[py][px] = style

        elif shape["type"] == "hexagon":
            hex_pts = "⬡"
            px, py = sx, sy
            if 0 <= px < width and 0 <= py < height:
                buf[py][px] = hex_pts
                colors[py][px] = style
            for ring in range(1, sz + 1):
                for angle in range(6):
                    dx = int(ring * math.cos(angle * math.pi / 3))
                    dy = int(ring * math.sin(angle * math.pi / 3))
                    px, py = sx + dx, sy + dy
                    if 0 <= px < width and 0 <= py < height:
                        buf[py][px] = "·"
                        colors[py][px] = style

    # Floating words — pulse and drift
    for fw in float_words:
        fw["x"] += fw["sx"]
        if fw["x"] < 1 or fw["x"] > width - len(fw["word"]) - 1:
            fw["sx"] *= -1
        pulse = 0.5 + 0.5 * math.sin(frame * 0.06 + fw["phase"])
        wx = int(fw["x"])
        wy = int(fw["y"])
        if pulse > 0.25:
            style = f"bold {fw['color']}" if pulse > 0.6 else f"{fw['color']}"
            for ci, ch in enumerate(fw["word"]):
                px = wx + ci
                if 0 <= px < width and 0 <= wy < height:
                    buf[wy][px] = ch
                    colors[wy][px] = style

    # Floating particles — neon sparks drifting upward
    for _ in range(width // 8):
        px = random.randint(0, width - 1)
        py = (height - 1) - ((frame * 2 + random.randint(0, height * 3)) % (height + 5))
        if 0 <= py < height and 0 <= px < width and buf[py][px] == " ":
            buf[py][px] = random.choice(["✦", "✧", "·", "•"])
            colors[py][px] = random.choice(neon)

    # Render
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=f"{colors[y][x]} on black" if colors[y][x] else "on black")
        canvas.write(line)

    await sleep(0.15)
