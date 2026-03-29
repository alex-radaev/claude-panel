from rich.text import Text
import random
import math

# City skyline with flickering windows, neon signs, and atmospheric haze

# Generate random buildings with shade variety
num_buildings = width // 4
buildings = []
for i in range(num_buildings):
    bw = random.randint(3, 7)
    bh = random.randint(height // 3, height - 3)
    bx = i * (width // num_buildings)
    shade = random.randint(40, 80)
    buildings.append((bx, bw, bh, shade))

# Window states: some always on, some flicker
window_states = {}
for bx, bw, bh, shade in buildings:
    for wy in range(2, bh - 1, 2):
        for wx in range(1, bw - 1, 2):
            key = (bx + wx, wy)
            window_states[key] = random.random() < 0.7

# Neon signs on some buildings
neon_signs = []
neon_colors = ["bright_red", "bright_magenta", "bright_cyan", "bright_yellow", "bright_green"]
neon_words = ["HOTEL", "BAR", "JAZZ", "24h", "CAFE", "NEON", "CLUB", "LIVE", "EAT", "NYC"]
for bx, bw, bh, shade in buildings:
    if bh > height // 2 and random.random() < 0.4:
        word = random.choice(neon_words)
        color = random.choice(neon_colors)
        sign_x = bx + max(0, (bw - len(word)) // 2)
        sign_y = height - bh + 1
        neon_signs.append((sign_x, sign_y, word, color))

# Stars in the sky — only in upper portion
sky_limit = max(3, height // 5)
stars = [(random.randint(0, width - 1), random.randint(0, sky_limit)) for _ in range(width // 5)]

# Haze particles — drift upward slowly
num_haze = width * 2
haze_particles = []
for _ in range(num_haze):
    hx = random.randint(0, width - 1)
    hy = random.randint(height // 3, height - 2)
    haze_particles.append([hx, hy, random.uniform(0.3, 1.5)])

for frame in range(200):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]
    colors = [["black"] * width for _ in range(height)]

    # Sky gradient — dark blue at top, dark purple near horizon
    for y in range(sky_limit):
        ratio = y / max(1, sky_limit)
        r = int(5 + ratio * 15)
        g = int(5 + ratio * 8)
        b = int(20 + ratio * 20)
        for x in range(width):
            colors[y][x] = f"rgb({r},{g},{b})"

    # Atmospheric haze layer — dim fog in lower portion
    for y in range(sky_limit, height):
        depth = (y - sky_limit) / max(1, height - sky_limit)
        fog_r = int(15 + depth * 30)
        fog_g = int(12 + depth * 20)
        fog_b = int(25 + depth * 35)
        for x in range(width):
            if depth > 0.3 and random.random() < depth * 0.12:
                buf[y][x] = "░"
            colors[y][x] = f"rgb({fog_r},{fog_g},{fog_b})"

    # Twinkling stars
    for sx, sy in stars:
        if sy < sky_limit and random.random() < 0.85:
            buf[sy][sx] = random.choice([".", "·", "*", "+"])
            colors[sy][sx] = random.choice(["bright_white", "white", "rgb(200,200,255)"])

    # Draw buildings with edge definition
    for bx, bw, bh, shade in buildings:
        roof_y = height - bh
        for y in range(roof_y, height):
            for x in range(bx, min(bx + bw, width)):
                if y == roof_y:
                    buf[y][x] = "▄"
                    colors[y][x] = f"rgb({shade+60},{shade+60},{shade+80})"
                elif x == bx or x == bx + bw - 1:
                    buf[y][x] = "▌" if x == bx else "▐"
                    colors[y][x] = f"rgb({shade+20},{shade+20},{shade+30})"
                else:
                    buf[y][x] = "█"
                    colors[y][x] = f"rgb({shade},{shade},{shade+15})"

        # Windows with warm glow bleeding to neighbors
        for wy in range(2, bh - 1, 2):
            for wx in range(1, bw - 1, 2):
                ry = height - bh + wy
                rx = bx + wx
                if 0 <= rx < width and 0 <= ry < height:
                    key = (rx, wy)
                    if window_states.get(key, False):
                        if random.random() < 0.95:
                            buf[ry][rx] = "▪"
                            warm = random.choice([
                                "bold bright_yellow", "bold yellow",
                                "bold rgb(255,210,100)", "bold rgb(255,180,60)",
                            ])
                            colors[ry][rx] = warm
                            # Glow bleeds to adjacent building cells
                            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                gx, gy = rx + dx, ry + dy
                                if 0 <= gx < width and 0 <= gy < height and buf[gy][gx] == "█":
                                    gs = shade + 25
                                    colors[gy][gx] = f"rgb({gs+40},{gs+25},{gs})"
                        else:
                            buf[ry][rx] = "▪"
                            colors[ry][rx] = "rgb(80,80,100)"

    # Neon signs — pulse with glow halo
    glow_map = {
        "bright_red": (100, 20, 20), "bright_magenta": (80, 20, 80),
        "bright_cyan": (20, 60, 80), "bright_yellow": (80, 70, 20),
        "bright_green": (20, 70, 20),
    }
    for sx, sy, word, color in neon_signs:
        pulse = math.sin(frame * 0.15 + hash(word)) > -0.3
        if pulse:
            for ci, ch in enumerate(word):
                px = sx + ci
                if 0 <= px < width and 0 <= sy < height:
                    buf[sy][px] = ch
                    colors[sy][px] = f"bold {color}"
            # Glow halo around sign
            gr, gg, gb = glow_map.get(color, (50, 50, 60))
            for ci in range(-1, len(word) + 1):
                for dy in [-1, 0, 1]:
                    gx, gy = sx + ci, sy + dy
                    if 0 <= gx < width and 0 <= gy < height:
                        if not (0 <= ci < len(word) and dy == 0):
                            if buf[gy][gx] in ("█", "▌", "▐", " ", "░"):
                                colors[gy][gx] = f"rgb({gr},{gg},{gb})"
        else:
            for ci, ch in enumerate(word):
                px = sx + ci
                if 0 <= px < width and 0 <= sy < height:
                    buf[sy][px] = ch
                    colors[sy][px] = "rgb(80,30,30)"

    # Drifting haze particles — rise slowly from the city
    haze_chars = ["░", "▒", "·", "."]
    for hp in haze_particles:
        hx, hy, speed = hp
        hy -= speed * 0.3
        hx += math.sin(frame * 0.05 + hx * 0.1) * 0.5
        if hy < height // 4:
            hy = random.randint(height * 2 // 3, height - 2)
            hx = random.randint(0, width - 1)
        hp[0], hp[1] = hx, hy
        ix, iy = int(hx) % width, int(hy)
        if 0 <= iy < height and buf[iy][ix] == " ":
            depth = iy / height
            a = int(30 + depth * 40)
            buf[iy][ix] = random.choice(haze_chars)
            colors[iy][ix] = f"rgb({a+15},{a+10},{a+25})"

    # Street level with moving car headlights
    street_y = height - 1
    for x in range(width):
        buf[street_y][x] = "▀"
        colors[street_y][x] = "rgb(50,50,60)"
    car_x = (frame * 3) % (width + 20) - 10
    for dx in range(3):
        cx = car_x + dx
        if 0 <= cx < width:
            buf[street_y][cx] = "█"
            colors[street_y][cx] = "bold bright_yellow"
    car_x2 = width - ((frame * 2 + 40) % (width + 20)) + 10
    for dx in range(3):
        cx = car_x2 + dx
        if 0 <= cx < width:
            buf[street_y][cx] = "█"
            colors[street_y][cx] = "bold bright_red"

    # Render with explicit black background for contrast
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=f"{colors[y][x]} on black")
        canvas.write(line)

    await sleep(0.1)
