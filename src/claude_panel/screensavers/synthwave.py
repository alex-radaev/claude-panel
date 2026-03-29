from rich.text import Text
import random
import math

# Synthwave sunset — centered sun, low skyline, ferris wheel, perspective grid

horizon = int(height * 0.48)

# ── Sun: centered, moderate size ──
sun_cx = width // 2
sun_r = min(height // 5, width // 8, 7)
sun_rows = []
for dy in range(0, sun_r + 1):
    y = horizon - dy
    if y < 0:
        break
    hw = int(1.7 * math.sqrt(max(0, sun_r * sun_r - dy * dy)))
    sun_rows.append((y, sun_cx - hw, sun_cx + hw, dy))

# ── Ferris wheel ──
fw_cx = int(width * 0.2)
fw_r = min(6, height // 7)
fw_cabins = 8
fw_aspect = 0.5
fw_center_y = horizon - int(fw_r * fw_aspect) - 1

# ── Skyline: continuous height map ──
random.seed(42)
skyline = [0] * width
x = 0
while x < width:
    seg_w = random.randint(3, 8)
    seg_h = random.randint(2, 6)
    for dx in range(seg_w):
        if x + dx < width:
            skyline[x + dx] = seg_h
    x += seg_w + random.randint(0, 1)
# Clear around ferris wheel
for x in range(max(0, fw_cx - fw_r - 3), min(width, fw_cx + fw_r + 3)):
    skyline[x] = min(skyline[x], 2)
random.seed()

# Window positions
win_positions = set()
random.seed(55)
for x in range(width):
    h = skyline[x]
    for wy in range(1, h, 2):
        if random.random() < 0.3:
            win_positions.add((x, wy))
random.seed()

# Stars
random.seed(77)
stars = [(random.randint(0, width - 1), random.randint(0, max(0, horizon - sun_r - 3)),
          random.uniform(0, 6.28)) for _ in range(width // 5)]
random.seed()

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    col = [[""] * width for _ in range(height)]

    # ── Sky gradient ──
    for y in range(horizon + 1):
        t = y / max(1, horizon)
        r, g, b = int(12 + t * 30), int(5 + t * 10), int(35 + t * 40)
        for x in range(width):
            col[y][x] = f"rgb({r},{g},{b})"

    # ── Stars ──
    for sx, sy, ph in stars:
        if 0 <= sx < width and 0 <= sy < height:
            tw = 0.5 + 0.5 * math.sin(frame * 0.04 + ph)
            if tw > 0.45:
                v = int(50 + tw * 60)
                buf[sy][sx] = "·"
                col[sy][sx] = f"rgb({v},{v},{v + 15})"

    # ── Sun ──
    for y, xl, xr, dy in sun_rows:
        if dy > 1 and dy < sun_r * 6 // 10 and dy % 3 == 0:
            continue
        for x in range(max(0, xl), min(width, xr + 1)):
            t = dy / max(1, sun_r)
            buf[y][x] = "█"
            col[y][x] = f"rgb(255,{int(100 + t * 140)},{int(10 + t * 40)})"

    # ── Skyline silhouette — continuous, drawn over sun ──
    for x in range(width):
        h = skyline[x]
        for dy in range(h):
            y = horizon - dy
            if 0 <= y < height:
                buf[y][x] = "█"
                col[y][x] = "rgb(12,10,22)"
        # Windows
        for (wx, wy) in win_positions:
            if wx == x:
                py = horizon - wy
                if 0 <= py < height and wy < h:
                    if random.random() < 0.9:
                        buf[py][wx] = "▪"
                        col[py][wx] = random.choice(["rgb(255,210,80)", "rgb(170,210,255)"])
    # Solid horizon line
    for x in range(width):
        if 0 <= horizon < height:
            buf[horizon][x] = "█"
            col[horizon][x] = "rgb(12,10,22)"

    # ── Ferris wheel ──
    ang = frame * 0.05
    # Rim
    for a in range(80):
        theta = a * math.pi * 2 / 80
        rx = int(fw_cx + fw_r * math.cos(theta))
        ry = int(fw_center_y + fw_r * fw_aspect * math.sin(theta))
        if 0 <= rx < width and 0 <= ry < height:
            buf[ry][rx] = "○"
            col[ry][rx] = "rgb(90,70,130)"
    # Spokes + cabins
    cabin_c = [
        "rgb(255,50,70)", "rgb(50,180,255)", "rgb(255,230,40)",
        "rgb(255,70,190)", "rgb(60,255,140)", "rgb(255,130,30)",
        "rgb(170,70,255)", "rgb(30,255,210)",
    ]
    for i in range(fw_cabins):
        theta = ang + i * math.pi * 2 / fw_cabins
        cx = fw_cx + fw_r * math.cos(theta)
        cy = fw_center_y + fw_r * fw_aspect * math.sin(theta)
        steps = int(fw_r * 1.2)
        for s in range(1, steps + 1):
            t = s / steps
            sx = int(fw_cx + (cx - fw_cx) * t)
            sy = int(fw_center_y + (cy - fw_center_y) * t)
            if 0 <= sx < width and 0 <= sy < height:
                if buf[sy][sx] in (" ", "·", "○"):
                    buf[sy][sx] = "·"
                    col[sy][sx] = "rgb(60,50,90)"
        px, py = int(cx), int(cy)
        for dx in range(2):
            cpx = px + dx
            if 0 <= cpx < width and 0 <= py < height:
                buf[py][cpx] = "█"
                col[py][cpx] = f"bold {cabin_c[i % len(cabin_c)]}"
    if 0 <= fw_cx < width and 0 <= fw_center_y < height:
        buf[fw_center_y][fw_cx] = "◉"
        col[fw_center_y][fw_cx] = "bold rgb(200,180,240)"
    # Legs
    for side in [-1, 1]:
        foot_x = fw_cx + side * max(2, fw_r // 2)
        for s in range(12):
            t = s / 11
            lx = int(fw_cx + (foot_x - fw_cx) * t)
            ly = int(fw_center_y + (horizon - fw_center_y) * t)
            if 0 <= lx < width and 0 <= ly < height and buf[ly][lx] in (" ", "·"):
                buf[ly][lx] = "╱" if side == -1 else "╲"
                col[ly][lx] = "rgb(45,35,65)"

    # ── Bottom: perspective grid + sun reflection (no water chars) ──
    for y in range(horizon + 1, height):
        t = (y - horizon) / max(1, height - horizon)
        h_gap = max(1, int(5 - t * 3))
        is_h = (y - horizon - 1) % h_gap == 0

        for x in range(width):
            v_gap = max(2, int(14 - t * 10))
            cx_off = x - sun_cx
            is_v = v_gap > 0 and abs(cx_off) % v_gap < 1

            # Sun reflection — warm glow in center
            dx = abs(x - sun_cx)
            refl_w = int(sun_r * 1.7 * (0.4 + t * 0.6))
            in_refl = dx < refl_w

            if is_h or is_v:
                ch = "┼" if is_h and is_v else ("─" if is_h else "│")
                if in_refl:
                    fade = (1 - dx / refl_w) * (1 - t * 0.7)
                    shimmer = 0.5 + 0.5 * math.sin(frame * 0.1 + x * 0.2 + y * 0.6)
                    warm = fade * shimmer
                    br = int(40 + t * 120)
                    r = min(255, int(br * 0.9 + warm * 180))
                    g = min(255, int(br * 0.08 + warm * 100))
                    b = min(255, int(br * 0.65 + warm * 20))
                    buf[y][x] = ch
                    col[y][x] = f"rgb({r},{g},{b})"
                else:
                    br = int(30 + t * 120)
                    buf[y][x] = ch
                    col[y][x] = f"rgb({int(br*0.9)},{int(br*0.08)},{int(br*0.65)})"
            else:
                col[y][x] = f"rgb({int(3+t*5)},{int(1+t*2)},{int(6+t*10)})"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            c = col[y][x]
            line.append(buf[y][x], style=f"{c} on black" if c else "on black")
        canvas.write(line)

    await sleep(0.15)
