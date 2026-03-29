from rich.text import Text
import random
import math

# Film noir cityscape — monochrome with a single red accent

# Buildings in grayscale
num_buildings = width // 4
buildings = []
for i in range(num_buildings):
    bw = random.randint(4, 8)
    bh = random.randint(height // 3, height - 3)
    bx = i * (width // num_buildings) + random.randint(-1, 1)
    shade = random.randint(15, 35)
    buildings.append((bx, bw, bh, shade))

# One red neon sign — the accent
red_sign = None
for bx, bw, bh, shade in buildings:
    if bh > height // 2 and red_sign is None and random.random() < 0.5:
        words = ["HOTEL", "BAR", "MOTEL", "JAZZ", "NOIR"]
        word = random.choice(words)
        sign_x = bx + max(0, (bw - len(word)) // 2)
        sign_y = height - bh + 2
        red_sign = (sign_x, sign_y, word)
if red_sign is None:
    bx, bw, bh, shade = buildings[len(buildings) // 2]
    red_sign = (bx + 1, height - bh + 2, "BAR")

# Windows — some lit in cool white
window_states = {}
for bx, bw, bh, shade in buildings:
    for wy in range(2, bh - 1, 2):
        for wx in range(1, bw - 1, 2):
            window_states[(bx + wx, wy)] = random.random() < 0.5

# Rain — noir needs rain
num_drops = width // 3
drops = [(random.randint(0, width - 1), random.randint(0, height - 1), random.choice([1, 2, 2])) for _ in range(num_drops)]

# Fog wisps
fog_particles = []
for _ in range(width):
    fx = random.randint(0, width - 1)
    fy = random.randint(height // 2, height - 2)
    fog_particles.append([fx, fy, random.uniform(0.2, 0.8)])

for frame in range(200):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]
    colors = [["black"] * width for _ in range(height)]

    # Sky — very dark gray gradient
    for y in range(height):
        g = int(5 + (y / height) * 12)
        for x in range(width):
            colors[y][x] = f"rgb({g},{g},{g+2})"

    # Rain — diagonal streaks
    for i, (dx, dy, speed) in enumerate(drops):
        ny = (dy + frame * speed) % height
        nx = (dx + frame * speed // 2) % width  # slight diagonal
        if 0 <= ny < height and 0 <= nx < width:
            if buf[ny][nx] == " ":
                buf[ny][nx] = random.choice(["│", "╎", "|"])
                g = random.randint(50, 80)
                colors[ny][nx] = f"rgb({g},{g},{g+10})"

    # Buildings — grayscale with lit edges
    for bx, bw, bh, shade in buildings:
        roof_y = height - bh
        for y in range(max(0, roof_y), height):
            for x in range(bx, min(bx + bw, width)):
                if y == roof_y:
                    buf[y][x] = "▄"
                    g = shade + 50
                    colors[y][x] = f"rgb({g},{g},{g})"
                elif x == bx or x == bx + bw - 1:
                    buf[y][x] = "▌" if x == bx else "▐"
                    g = shade + 20
                    colors[y][x] = f"rgb({g},{g},{g})"
                else:
                    buf[y][x] = "█"
                    colors[y][x] = f"rgb({shade},{shade},{shade})"

        # Windows — dim white glow
        for wy in range(2, bh - 1, 2):
            for wx in range(1, bw - 1, 2):
                ry = height - bh + wy
                rx = bx + wx
                if 0 <= rx < width and 0 <= ry < height:
                    if window_states.get((rx, wy), False):
                        if random.random() < 0.93:
                            buf[ry][rx] = "▪"
                            g = random.randint(140, 200)
                            colors[ry][rx] = f"rgb({g},{g},{g})"
                        else:
                            buf[ry][rx] = "▪"
                            colors[ry][rx] = "rgb(60,60,60)"

    # The red sign — the only color in the scene
    sx, sy, word = red_sign
    pulse = 0.6 + 0.4 * math.sin(frame * 0.1)
    for ci, ch in enumerate(word):
        px = sx + ci
        if 0 <= px < width and 0 <= sy < height:
            if pulse > 0.4:
                intensity = int(150 + pulse * 105)
                buf[sy][px] = ch
                colors[sy][px] = f"bold rgb({intensity},15,25)"
            else:
                buf[sy][px] = ch
                colors[sy][px] = "rgb(60,10,15)"

    # Red glow halo around the sign
    if pulse > 0.4:
        for ci in range(-1, len(word) + 1):
            for dy in [-1, 0, 1]:
                gx, gy = sx + ci, sy + dy
                if 0 <= gx < width and 0 <= gy < height:
                    if not (0 <= ci < len(word) and dy == 0):
                        if buf[gy][gx] in ("█", "▌", "▐", " "):
                            g = int(20 + pulse * 30)
                            colors[gy][gx] = f"rgb({g+30},{g-5},{g-5})"

        # Red reflection on ground below sign
        center_x = sx + len(word) // 2
        for gy in range(height - 3, height):
            spread = (gy - (height - 4)) * 3
            for rx in range(center_x - spread, center_x + spread + 1):
                if 0 <= rx < width:
                    dist = abs(rx - center_x)
                    if random.random() < pulse * 0.5 * (1 - dist / (spread + 1)):
                        buf[gy][rx] = random.choice(["░", "·", "~"])
                        r = int(80 + pulse * 60)
                        colors[gy][rx] = f"rgb({r},10,15)"

    # Fog wisps — drifting slowly
    for fp in fog_particles:
        fx, fy, speed = fp
        fx += math.sin(frame * 0.03 + fy * 0.1) * 0.7
        fy -= speed * 0.15
        if fy < height // 3:
            fy = random.randint(height * 2 // 3, height - 2)
            fx = random.randint(0, width - 1)
        fp[0], fp[1] = fx, fy
        ix, iy = int(fx) % width, int(fy)
        if 0 <= iy < height and buf[iy][ix] == " ":
            g = random.randint(20, 35)
            buf[iy][ix] = random.choice(["░", "·", "."])
            colors[iy][ix] = f"rgb({g},{g},{g+3})"

    # Street — wet pavement
    for x in range(width):
        if height - 1 >= 0:
            buf[height - 1][x] = "▀"
            g = random.randint(25, 40)
            colors[height - 1][x] = f"rgb({g},{g},{g})"

    # Render
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=f"{colors[y][x]} on black")
        canvas.write(line)

    await sleep(0.1)
