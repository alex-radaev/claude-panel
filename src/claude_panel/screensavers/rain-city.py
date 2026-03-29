from rich.text import Text
import random
import math

# Rainy city at night — raindrops, reflections, neon glow

# Skyline
ground_y = height - 3  # leave room for reflections
num_buildings = width // 5
buildings = []
for i in range(num_buildings):
    bw = random.randint(4, 8)
    bh = random.randint(ground_y // 3, ground_y - 2)
    bx = i * (width // num_buildings) + random.randint(-1, 1)
    buildings.append((bx, bw, bh))

# Rain drops
num_drops = width // 2
drops = [(random.randint(0, width - 1), random.randint(0, height - 1)) for _ in range(num_drops)]
drop_speeds = [random.choice([1, 2, 2, 3]) for _ in range(num_drops)]

# Neon signs on buildings that cast reflections on wet ground
neon_signs = []
neon_palette = [
    "rgb(255,50,100)", "rgb(50,200,255)", "rgb(255,100,255)",
    "rgb(255,200,50)", "rgb(100,255,150)", "rgb(255,80,50)",
]
neon_words = ["BAR", "JAZZ", "24h", "HOTEL", "LIVE", "CAFE", "CLUB", "EAT"]
for bx, bw, bh in buildings:
    if bh > ground_y // 3 and random.random() < 0.5:
        word = random.choice(neon_words)
        color = random.choice(neon_palette)
        sign_x = bx + max(0, (bw - len(word)) // 2)
        sign_y = ground_y - bh + 2
        neon_signs.append((sign_x, sign_y, word, color))

for frame in range(200):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]
    colors = [["black"] * width for _ in range(height)]

    # Buildings
    for bx, bw, bh in buildings:
        roof_y = ground_y - bh
        for y in range(max(0, roof_y), ground_y):
            for x in range(bx, min(bx + bw, width)):
                buf[y][x] = "█"
                colors[y][x] = "rgb(20,20,30)"

            # Windows — slow flicker via per-window sine wave
            if (y - roof_y) % 2 == 1:
                for wx in range(1, bw - 1, 2):
                    rx = bx + wx
                    if 0 <= rx < width:
                        # Each window has its own phase; cycles very slowly
                        phase = hash((rx, y)) % 1000 / 1000.0 * 6.28
                        lit = math.sin(frame * 0.015 + phase) > -0.3
                        if lit:
                            # Subtle warm color drift
                            t = 0.5 + 0.5 * math.sin(frame * 0.02 + phase * 2)
                            r = int(200 + 55 * t)
                            g = int(180 + 40 * t)
                            b = int(50 + 50 * (1 - t))
                            buf[y][rx] = "▪"
                            colors[y][rx] = f"rgb({r},{g},{b})"

    # Rain
    rain_chars = ["|", "│", "┃", "╎", "¦"]
    for i in range(num_drops):
        dx, dy = drops[i]
        speed = drop_speeds[i]
        ny = (dy + frame * speed) % (ground_y + 1)
        if 0 <= ny < ground_y and 0 <= dx < width:
            # Don't draw rain over buildings
            if buf[ny][dx] == " ":
                buf[ny][dx] = random.choice(rain_chars[:2])
                colors[ny][dx] = "rgb(100,130,180)"
            # Splash at ground
            if ny >= ground_y - 1:
                splash_x = dx + random.choice([-1, 0, 1])
                if 0 <= splash_x < width:
                    buf[ground_y][splash_x] = random.choice(["·", "°", "•"])
                    colors[ground_y][splash_x] = "rgb(120,150,200)"

    # Wet ground — reflections
    for y in range(ground_y, height):
        for x in range(width):
            buf[y][x] = random.choice(["▁", "▂", "░", "·", " ", " "])
            colors[y][x] = "rgb(15,15,25)"

    # Neon signs on buildings + reflections on wet ground
    for sx, sy, word, ncolor in neon_signs:
        pulse = 0.6 + 0.4 * math.sin(frame * 0.1 + hash(word))
        # Draw sign text on building
        for ci, ch in enumerate(word):
            px = sx + ci
            if 0 <= px < width and 0 <= sy < height:
                if pulse > 0.4:
                    buf[sy][px] = ch
                    colors[sy][px] = f"bold {ncolor}"
                else:
                    buf[sy][px] = ch
                    colors[sy][px] = "rgb(60,30,30)"

        # Reflection on wet ground — spreads and shimmers below sign center
        center_x = sx + len(word) // 2
        if pulse > 0.4:
            for gy in range(ground_y, height):
                reflect_spread = (gy - ground_y + 1) * 2
                for rx in range(center_x - reflect_spread, center_x + reflect_spread + 1):
                    if 0 <= rx < width:
                        dist = abs(rx - center_x)
                        if random.random() < pulse * (1 - dist / (reflect_spread + 1)):
                            buf[gy][rx] = random.choice(["~", "≈", "∼", "░"])
                            colors[gy][rx] = ncolor

    # Render
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=colors[y][x])
        canvas.write(line)

    await sleep(0.08)
