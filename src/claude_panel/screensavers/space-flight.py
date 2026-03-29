from rich.text import Text
import math
import random

random.seed()

num_stars = max(30, (width * height) // 30)
stars = [(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(num_stars)]
star_chars = [".", "*", "+", "~"]

ship = [
    "   /\\",
    "  /  \\",
    " | CC |",
    " |    |",
    "/|    |\\",
    " | ## |",
    "  \\  /",
    "  |  |",
    " /|  |\\",
    "/_|__|_\\",
]

ship_w = max(len(l) for l in ship)
ship_h = len(ship)
sway_range = max(1, (width // 2) - ship_w - 2)

for frame_num in range(120):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]

    for i, (sx, sy) in enumerate(stars):
        speed = (i % 3) + 1
        ny = (sy + frame_num * speed) % height
        drift = int(math.sin(frame_num * 0.04 + i * 0.3) * speed * 2)
        nx = (sx + drift) % width
        buf[ny][nx] = star_chars[i % len(star_chars)]

    ship_x = width // 2 - ship_w // 2 + int(math.sin(frame_num * 0.06) * sway_range)
    ship_y = (height - ship_h) // 2 + int(math.sin(frame_num * 0.15) * 2)

    h_velocity = math.cos(frame_num * 0.06)
    exhaust_chars = ["\u2593", "\u2592", "\u2591", ".", " "]
    for ey in range(ship_y + ship_h, min(ship_y + ship_h + 5, height)):
        offset = ey - (ship_y + ship_h)
        spread = offset + 1
        cx = ship_x + ship_w // 2
        exhaust_drift = int(-h_velocity * offset * 0.8)
        for dx in range(-spread, spread + 1):
            ex = cx + dx + exhaust_drift
            if 0 <= ex < width:
                flicker = random.choice(exhaust_chars[:max(1, 3 - offset)])
                buf[ey][ex] = flicker

    for row_i, row in enumerate(ship):
        y = ship_y + row_i
        if 0 <= y < height:
            for col_i, ch in enumerate(row):
                x = ship_x + col_i
                if 0 <= x < width and ch != " ":
                    buf[y][x] = ch

    for row in buf:
        canvas.write(Text("".join(row), style="bright_white on black"))

    spd = 9500 + int(math.sin(frame_num * 0.1) * 200)
    fuel = max(0, 100 - int(frame_num * 0.8))
    heading = int(math.sin(frame_num * 0.06) * 30)
    pad = " " * max(0, (width - 60) // 2)
    canvas.write(Text(f"{pad}SPD: {spd} km/s  ALT: {42000 + frame_num * 10} km  HDG: {heading:+d}\u00b0  FUEL: {fuel}%", style="bright_green on black"))

    await sleep(0.07)
