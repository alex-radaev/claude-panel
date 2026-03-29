from rich.text import Text
import random
import math

# Aurora — northern lights rippling across a starlit sky

# Stars — fixed positions
random.seed(77)
stars = [(random.randint(0, width - 1), random.randint(0, height - 1), random.uniform(0, 6.28))
         for _ in range(width * height // 25)]
random.seed()

# Aurora bands — each is a sine wave with color, amplitude, frequency
bands = []
for i in range(5):
    bands.append({
        "base_y": height * 0.25 + i * height * 0.08,
        "amplitude": random.uniform(1.5, 3.5),
        "freq": random.uniform(0.03, 0.08),
        "phase": random.uniform(0, 6.28),
        "speed": random.uniform(0.04, 0.1),
        "spread": random.randint(2, 5),
    })

# Color palette — aurora greens, teals, purples, blues
def aurora_color(band_idx, intensity):
    palette = [
        (50, 255, 130),   # green
        (0, 255, 200),    # teal
        (100, 200, 255),  # light blue
        (150, 100, 255),  # purple
        (80, 255, 180),   # mint
    ]
    r, g, b = palette[band_idx % len(palette)]
    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)
    return f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})"

# Mountain silhouette
mountains = []
mx = 0
while mx < width:
    peak = random.randint(height - height // 4, height - 2)
    mw = random.randint(8, 20)
    mountains.append((mx, peak, mw))
    mx += mw - random.randint(1, 3)

def mountain_height(x):
    best = height
    for mx, peak, mw in mountains:
        if mx <= x < mx + mw:
            center = mx + mw / 2
            dist = abs(x - center) / (mw / 2)
            h = peak + int(dist * dist * (height - peak))
            best = min(best, h)
    return best

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    colors = [[""] * width for _ in range(height)]

    # Night sky gradient
    for y in range(height):
        depth = y / height
        r = int(3 + depth * 8)
        g = int(2 + depth * 5)
        b = int(12 + depth * 20)
        for x in range(width):
            colors[y][x] = f"rgb({r},{g},{b})"

    # Stars
    for sx, sy, phase in stars:
        if sy < mountain_height(sx):
            twinkle = 0.4 + 0.6 * math.sin(frame * 0.05 + phase)
            if twinkle > 0.2:
                bright = int(60 + twinkle * 140)
                buf[sy][sx] = random.choice(["·", ".", "+", "*"]) if twinkle > 0.6 else "·"
                colors[sy][sx] = f"rgb({bright},{bright},{bright + 20})"

    # Aurora bands — sine waves with vertical glow spread
    for bi, band in enumerate(bands):
        phase = band["phase"] + frame * band["speed"]
        for x in range(width):
            wave_y = band["base_y"] + band["amplitude"] * math.sin(x * band["freq"] + phase)
            wave_y += 0.8 * math.sin(x * band["freq"] * 2.3 + phase * 1.7)

            cy = int(wave_y)
            for dy in range(-band["spread"], band["spread"] + 1):
                py = cy + dy
                if 0 <= py < height and py < mountain_height(x):
                    dist = abs(dy) / (band["spread"] + 1)
                    intensity = (1.0 - dist) * (0.4 + 0.6 * math.sin(frame * 0.07 + x * 0.02 + bi))
                    intensity = max(0, min(1, intensity))
                    if intensity > 0.1:
                        ch = "█" if intensity > 0.7 else ("▓" if intensity > 0.4 else ("░" if intensity > 0.2 else "·"))
                        color = aurora_color(bi, intensity)
                        buf[py][x] = ch
                        colors[py][x] = color

    # Compute aurora light per column — accumulate color from all aurora pixels above mountains
    aurora_light = {}  # x -> (r, g, b, total_intensity)
    for x in range(width):
        mh = mountain_height(x)
        tr, tg, tb, count = 0.0, 0.0, 0.0, 0.0
        for y in range(0, mh):
            if buf[y][x] in ("█", "▓", "░"):
                # Parse the rgb color
                c = colors[y][x]
                if c.startswith("rgb("):
                    try:
                        parts = c[4:-1].split(",")
                        tr += int(parts[0])
                        tg += int(parts[1])
                        tb += int(parts[2])
                        count += 1
                    except (ValueError, IndexError):
                        pass
        if count > 0:
            aurora_light[x] = (tr / count, tg / count, tb / count, min(count / 3, 1.0))

    # Mountains — dark silhouette with aurora reflection
    for x in range(width):
        mh = mountain_height(x)
        light = aurora_light.get(x)
        for y in range(mh, height):
            depth = y - mh  # distance from peak
            base_shade = int(8 + depth * 0.5)
            if light and depth < 6:
                # Aurora light reflects on upper slopes — fades with depth
                lr, lg, lb, li = light
                fade = max(0, 1.0 - depth / 6)
                strength = fade * li * 0.5
                r = int(base_shade + lr * strength)
                g = int(base_shade + lg * strength)
                b = int(base_shade + lb * strength)
                r, g, b = min(255, r), min(255, g), min(255, b)
                buf[y][x] = "█"
                colors[y][x] = f"rgb({r},{g},{b})"
            else:
                buf[y][x] = "█"
                colors[y][x] = f"rgb({base_shade},{base_shade},{base_shade + 3})"

    # Render
    for y in range(height):
        line = Text()
        for x in range(width):
            line.append(buf[y][x], style=f"{colors[y][x]} on black" if colors[y][x] else "on black")
        canvas.write(line)

    await sleep(0.15)
