"""Send a space animation to the panel."""
import asyncio
import json
import tempfile
import time
import os
from claude_panel.constants import PANEL_DIR, STATE_FILE

SCRIPT_CODE = r'''
from rich.text import Text
import math
import random

random.seed(42)
# width and height are injected by the viewer — they match the actual panel size

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

# How far the ship can sway left/right from center
sway_range = (width // 2) - ship_w - 2

for frame_num in range(120):
    canvas.clear()
    canvas.write(Text("  CLAUDE VOYAGER", style="bold bright_cyan"))

    buf = [[" "] * width for _ in range(height)]

    # Stars scroll down AND drift sideways (parallax)
    for i, (sx, sy) in enumerate(stars):
        speed = (i % 3) + 1
        ny = (sy + frame_num * speed) % height
        # Horizontal drift — opposite to ship movement for parallax feel
        drift = int(math.sin(frame_num * 0.04 + i * 0.3) * speed * 2)
        nx = (sx + drift) % width
        char = star_chars[i % len(star_chars)]
        buf[ny][nx] = char

    # Ship sways left/right with a smooth figure-8 pattern
    ship_x = width // 2 - ship_w // 2 + int(math.sin(frame_num * 0.06) * sway_range)
    ship_y = (height - ship_h) // 2 + int(math.sin(frame_num * 0.15) * 2)

    # Exhaust angles slightly based on horizontal movement direction
    h_velocity = math.cos(frame_num * 0.06)  # derivative of sin = cos
    exhaust_chars = ["\u2593", "\u2592", "\u2591", ".", " "]
    for ey in range(ship_y + ship_h, min(ship_y + ship_h + 5, height)):
        offset = ey - (ship_y + ship_h)
        spread = offset + 1
        cx = ship_x + ship_w // 2
        # Exhaust drifts opposite to movement
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
        line = "".join(row)
        canvas.write(Text(line, style="bright_white on black"))

    spd = 9500 + int(math.sin(frame_num * 0.1) * 200)
    fuel = max(0, 100 - int(frame_num * 0.8))
    heading = int(math.sin(frame_num * 0.06) * 30)
    pad = " " * max(0, (width - 60) // 2)
    canvas.write(Text(f"{pad}SPD: {spd} km/s  ALT: {42000 + frame_num * 10} km  HDG: {heading:+d}\u00b0  FUEL: {fuel}%", style="bright_green on black"))

    await sleep(0.07)

canvas.write("")
canvas.write(Text("  \u2605 Destination reached! \u2605", style="bold bright_yellow"))
'''


def main():
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "mode": "script",
        "script": {"code": SCRIPT_CODE, "title": "Space Flight"},
        "ts": time.time(),
    }
    fd, tmp_path = tempfile.mkstemp(dir=PANEL_DIR, suffix=".tmp")
    with open(fd, "w") as f:
        json.dump(data, f)
    os.rename(tmp_path, STATE_FILE)
    print("Animation sent!")


if __name__ == "__main__":
    main()
