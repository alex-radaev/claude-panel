from rich.text import Text
import random
import math

# Coffee shop window — steam rising, rain outside, warm glow within

# Layout
ground_y = height - 2
win_top = 4
win_bot = ground_y - 1
win_left = max(3, width // 5)
win_right = min(width - 4, width - width // 5)
win_w = win_right - win_left
win_h = win_bot - win_top
mid_x = (win_left + win_right) // 2

# Rain drops — outside only
num_drops = width
drops = [(random.randint(0, width - 1), random.randint(0, height - 1)) for _ in range(num_drops)]
drop_speeds = [random.choice([1, 1, 2, 2, 3]) for _ in range(num_drops)]

# Window raindrops — slow trickles down the glass
num_glass_drops = max(3, win_w // 5)
glass_drops = []
for _ in range(num_glass_drops):
    gx = random.randint(win_left + 2, win_right - 3)
    gy = random.randint(win_top + 1, win_top + win_h // 3)
    gspeed = random.uniform(0.03, 0.07)
    gwobble = random.uniform(0.5, 2.0)
    glass_drops.append([float(gx), float(gy), gspeed, gwobble])

# Steam particles rising from cup — more particles for fuller effect
cup_x = mid_x + 3
cup_y = win_bot - 2
num_steam = 32
steam_particles = []
for _ in range(num_steam):
    sx = cup_x + random.uniform(-1, 1)
    sy = float(cup_y) - random.uniform(0, 8)
    sphase = random.uniform(0, 6.28)
    sspeed = random.uniform(0.05, 0.12)
    steam_particles.append([sx, sy, sphase, sspeed])

# Pendant lights
num_lights = max(2, win_w // 8)
light_xs = [win_left + int((i + 1) * win_w / (num_lights + 1)) for i in range(num_lights)]
light_y = win_top + 2

# Condensation — sparse, mostly near edges and bottom of window
condensation = set()
for _ in range(max(5, win_w * win_h // 20)):
    # Cluster near bottom and edges
    if random.random() < 0.6:
        cx = random.randint(win_left + 1, win_right - 1)
        cy = random.randint(win_bot - win_h // 3, win_bot - 1)
    else:
        cx = random.choice([
            random.randint(win_left + 1, win_left + 3),
            random.randint(win_right - 3, win_right - 1)
        ])
        cy = random.randint(win_top + 2, win_bot - 1)
    condensation.add((cx, cy))

# Sign
sign_text = "COFFEE"
sign_x = mid_x - len(sign_text) // 2

# Neon wall sign — scrolling fluorescent text in right lower pane
neon_phrases = [
    "but first, coffee",
    "good vibes only",
    "do what you love",
    "stay curious",
    "dream big",
    "hello world",
    "keep brewing",
    "create something",
    "one more cup",
    "enjoy the moment",
]
neon_full = "  ~  ".join(neon_phrases) + "  ~  "
neon_pane_left = mid_x + 1
neon_pane_right = win_right - 1
neon_pane_w = neon_pane_right - neon_pane_left
neon_y = (win_top + win_bot) // 2 + 3  # below middle mullion

# Awning
awning_y = win_top - 1

for frame in range(200):
    canvas.clear()
    buf = [[" "] * width for _ in range(height)]
    fg = [[""] * width for _ in range(height)]
    bg = [["black"] * width for _ in range(height)]

    # ── Sky + wall exterior ──
    for y in range(height):
        for x in range(width):
            inside = (win_left < x < win_right and win_top < y < win_bot)
            if inside:
                continue
            if y <= 1:
                # Dark sky
                g = 8 + y * 3
                fg[y][x] = f"rgb({g},{g},{g+4})"
            elif y >= ground_y:
                # Wet pavement — dark
                fg[y][x] = "rgb(22,22,26)"
                buf[y][x] = " "
            elif y == win_top or y == win_bot:
                # Window frame horizontal
                if win_left <= x <= win_right:
                    buf[y][x] = "█"
                    fg[y][x] = "rgb(65,45,28)"
                else:
                    fg[y][x] = "rgb(30,24,22)"
                    buf[y][x] = "░"
            elif x == win_left or x == win_right:
                if win_top <= y <= win_bot:
                    buf[y][x] = "█"
                    fg[y][x] = "rgb(65,45,28)"
                else:
                    fg[y][x] = "rgb(30,24,22)"
                    buf[y][x] = "░"
            else:
                # Brick wall — subdued
                is_mortar = (y % 3 == 0) or (x % 7 == (0 if (y // 3) % 2 == 0 else 3))
                if is_mortar:
                    fg[y][x] = "rgb(22,18,16)"
                else:
                    shade = 32 + ((x * 7 + y * 13) % 8)
                    fg[y][x] = f"rgb({shade},{shade-6},{shade-10})"
                    buf[y][x] = "░"

    # ── Window interior — rich warm amber background ──
    mid_y = (win_top + win_bot) // 2
    for y in range(win_top + 1, win_bot):
        for x in range(win_left + 1, win_right):
            # Mullions — cross pattern (4 panes)
            if x == mid_x and y == mid_y:
                buf[y][x] = "┼"
                fg[y][x] = "rgb(60,42,28)"
                bg[y][x] = "rgb(45,30,15)"
                continue
            if x == mid_x:
                buf[y][x] = "│"
                fg[y][x] = "rgb(60,42,28)"
                bg[y][x] = "rgb(45,30,15)"
                continue
            if y == mid_y:
                buf[y][x] = "─"
                fg[y][x] = "rgb(60,42,28)"
                bg[y][x] = "rgb(45,30,15)"
                continue

            ty = (y - win_top) / max(1, win_h)
            tx = abs(x - mid_x) / max(1, win_w // 2)
            # Warm vignette — bright center, darker edges
            vignette = 1.0 - 0.25 * (tx * tx) - 0.15 * ((1 - ty) ** 2)
            vignette = max(0.55, min(1.0, vignette))

            # Background: rich amber
            br = int(85 * vignette)
            bgg = int(50 * vignette)
            bb = int(15 * vignette)
            bg[y][x] = f"rgb({br},{bgg},{bb})"

            # Foreground warm glow color
            r = int((200 + ty * 40) * vignette)
            g = int((140 + ty * 30) * vignette)
            b = int((45 + ty * 15) * vignette)
            fg[y][x] = f"rgb({min(255,r)},{min(255,g)},{max(0,b)})"

    # ── Pendant lights ──
    for lx in light_xs:
        # Cord
        for cy in range(win_top + 1, light_y):
            if 0 <= lx < width and 0 <= cy < height:
                buf[cy][lx] = "│"
                fg[cy][lx] = "rgb(80,55,30)"
                bg[cy][lx] = "rgb(60,35,12)"
        # Bulb — bright warm
        if 0 <= lx < width and 0 <= light_y < height:
            flicker = 0.88 + 0.12 * math.sin(frame * 0.07 + lx * 0.5)
            r = int(255 * flicker)
            g = int(210 * flicker)
            b_c = int(90 * flicker)
            buf[light_y][lx] = "◉"
            fg[light_y][lx] = f"bold rgb({r},{g},{b_c})"
            bg[light_y][lx] = f"rgb({int(120*flicker)},{int(80*flicker)},{int(25*flicker)})"

        # Light cone — bright warm pool spreading down
        for dy in range(1, min(12, win_bot - light_y - 1)):
            spread = int(dy * 1.2)
            ly = light_y + dy
            intensity = max(0, 1.0 - dy / 12.0)
            intensity *= intensity  # quadratic for softer edge
            for dx in range(-spread, spread + 1):
                lxx = lx + dx
                if win_left < lxx < win_right and win_top < ly < win_bot:
                    dist_f = abs(dx) / (spread + 1)
                    glow = intensity * (1 - dist_f * dist_f) * 0.7
                    if glow > 0.03:
                        r = min(255, int(180 + glow * 75))
                        g = min(255, int(130 + glow * 60))
                        b_c = max(0, int(40 + glow * 25))
                        fg[ly][lxx] = f"rgb({r},{g},{b_c})"
                        # Warm up background too
                        br = min(130, int(70 + glow * 60))
                        bgg = min(90, int(42 + glow * 40))
                        bb = min(40, int(12 + glow * 15))
                        bg[ly][lxx] = f"rgb({br},{bgg},{bb})"

    # ── Neon wall sign — framed sign board with scrolling text ──
    flicker = 0.88 + 0.12 * math.sin(frame * 0.13)
    scroll = int(frame * 0.5)
    neon_len = len(neon_full)
    sign_left = neon_pane_left + 1
    sign_right = neon_pane_right - 1
    sign_inner_w = sign_right - sign_left - 1
    frame_color = "rgb(180,140,80)"
    sign_bg = "rgb(25,18,12)"
    if 0 <= neon_y < height:
        # Top border
        ty = neon_y - 1
        if win_top < ty < win_bot:
            buf[ty][sign_left] = "╔"
            fg[ty][sign_left] = frame_color
            bg[ty][sign_left] = sign_bg
            for dx in range(1, sign_inner_w + 1):
                buf[ty][sign_left + dx] = "═"
                fg[ty][sign_left + dx] = frame_color
                bg[ty][sign_left + dx] = sign_bg
            buf[ty][sign_right] = "╗"
            fg[ty][sign_right] = frame_color
            bg[ty][sign_right] = sign_bg
        # Bottom border
        by = neon_y + 1
        if win_top < by < win_bot:
            buf[by][sign_left] = "╚"
            fg[by][sign_left] = frame_color
            bg[by][sign_left] = sign_bg
            for dx in range(1, sign_inner_w + 1):
                buf[by][sign_left + dx] = "═"
                fg[by][sign_left + dx] = frame_color
                bg[by][sign_left + dx] = sign_bg
            buf[by][sign_right] = "╝"
            fg[by][sign_right] = frame_color
            bg[by][sign_right] = sign_bg
        # Left/right border + scrolling text
        buf[neon_y][sign_left] = "║"
        fg[neon_y][sign_left] = frame_color
        bg[neon_y][sign_left] = sign_bg
        buf[neon_y][sign_right] = "║"
        fg[neon_y][sign_right] = frame_color
        bg[neon_y][sign_right] = sign_bg
        # Scrolling text inside
        for dx in range(sign_inner_w):
            gx = sign_left + 1 + dx
            char_idx = (scroll + dx) % neon_len
            ch = neon_full[char_idx]
            if ch != " " and ch != "~":
                r = int(255 * flicker)
                g = int(100 * flicker)
                b_c = int(230 * flicker)
                buf[neon_y][gx] = ch
                fg[neon_y][gx] = f"bold rgb({r},{g},{b_c})"
                bg[neon_y][gx] = sign_bg
            elif ch == "~":
                buf[neon_y][gx] = "·"
                fg[neon_y][gx] = f"rgb({int(140*flicker)},{int(50*flicker)},{int(120*flicker)})"
                bg[neon_y][gx] = sign_bg
            else:
                buf[neon_y][gx] = " "
                bg[neon_y][gx] = sign_bg

    # ── Shelves — simple lines with items ──
    shelf_y1 = win_top + 4
    shelf_y2 = win_top + win_h // 2 + 1
    for shelf_y in [shelf_y1, shelf_y2]:
        if shelf_y >= win_bot:
            continue
        for x in range(win_left + 2, win_right - 1):
            if 0 <= shelf_y < height and x != mid_x:
                buf[shelf_y][x] = "─"
                fg[shelf_y][x] = "rgb(100,68,38)"
        # Items on shelf — small bottles/jars
        for ix in range(win_left + 3, win_right - 2, 3):
            iy = shelf_y - 1
            if 0 <= iy < height and win_left < ix < win_right and ix != mid_x:
                it = (ix * 7 + shelf_y * 3) % 5
                chars = ["▌", "▐", "█", "▄", "▀"]
                item_colors = [
                    "rgb(140,90,50)", "rgb(100,140,90)", "rgb(160,110,60)",
                    "rgb(110,85,130)", "rgb(180,140,70)"
                ]
                buf[iy][ix] = chars[it]
                fg[iy][ix] = item_colors[it]

    # ── Counter ──
    counter_y = win_bot - 1
    for x in range(win_left + 1, win_right):
        if 0 <= counter_y < height and x != mid_x:
            buf[counter_y][x] = "▀"
            fg[counter_y][x] = "rgb(100,65,35)"
            bg[counter_y][x] = "rgb(60,38,18)"

    # ── Coffee cup — white ceramic, prominent ──
    cy = counter_y - 1
    cup_parts = [("╭", "rgb(255,250,240)"), ("█", "rgb(245,235,220)"),
                 ("█", "rgb(245,235,220)"), ("╮", "rgb(255,250,240)")]
    for i, (ch, color) in enumerate(cup_parts):
        cx = cup_x - 1 + i
        if win_left < cx < win_right and 0 <= cy < height:
            buf[cy][cx] = ch
            fg[cy][cx] = color
            bg[cy][cx] = "rgb(85,52,22)"
    # Handle
    hx = cup_x + 3
    if win_left < hx < win_right and 0 <= cy < height:
        buf[cy][hx] = ")"
        fg[cy][hx] = "rgb(240,230,215)"
    # Saucer below cup
    for i, sx in enumerate(range(cup_x - 2, cup_x + 4)):
        if win_left < sx < win_right and 0 <= counter_y < height:
            buf[counter_y][sx] = "▔"
            fg[counter_y][sx] = "rgb(230,225,210)"

    # ── Laptop on counter (left side) ──
    lap_w = 10
    lap_x = mid_x - lap_w - 2
    lap_inner = lap_w - 2  # inner screen width
    if win_left < lap_x < win_right and win_left < lap_x + lap_w < win_right:
        # Fake tiny text — small chars simulating code at laptop scale
        random.seed(frame // 18)  # new line every 18 frames
        total_lines = frame // 18
        cursor_on = (frame % 6) < 3
        typing_progress = (frame % 18) / 18.0  # 0..1 within current line
        # Generate fake text lines from history
        fake_lines = []
        for li in range(total_lines + 1):
            random.seed(42 + li)
            line_len = random.randint(2, lap_inner - 1)
            line = ""
            for _ in range(line_len):
                line += random.choice(["·", "∙", "·", "·", "∙", "·", " ", "·"])
            fake_lines.append(line)
        random.seed()

        # Screen top border
        sy1 = counter_y - 6
        if 0 <= sy1 < height:
            buf[sy1][lap_x] = "╔"
            for dx in range(1, lap_w - 1):
                buf[sy1][lap_x + dx] = "═"
            buf[sy1][lap_x + lap_w - 1] = "╗"
            for dx in range(lap_w):
                fg[sy1][lap_x + dx] = "rgb(50,52,60)"

        # Screen rows (4 rows)
        for sdy in range(1, 5):
            sy = sy1 + sdy
            if 0 <= sy < height:
                buf[sy][lap_x] = "║"
                buf[sy][lap_x + lap_w - 1] = "║"
                fg[sy][lap_x] = "rgb(50,52,60)"
                fg[sy][lap_x + lap_w - 1] = "rgb(50,52,60)"
                for dx in range(1, lap_w - 1):
                    buf[sy][lap_x + dx] = " "
                    fg[sy][lap_x + dx] = "rgb(50,180,70)"
                    bg[sy][lap_x + dx] = "rgb(5,12,8)"

        # Show last 3 lines on screen rows, current line typing
        screen_rows = 4
        for row in range(screen_rows):
            sy = sy1 + 1 + row
            if sy >= height:
                continue
            line_idx = len(fake_lines) - screen_rows + row
            if line_idx < 0:
                continue
            line = fake_lines[line_idx]
            is_current = (row == screen_rows - 1)
            if is_current:
                show = int(len(line) * typing_progress)
            else:
                show = len(line)
            for ci in range(show):
                px = lap_x + 1 + ci
                if px < lap_x + lap_w - 1 and 0 <= sy < height:
                    buf[sy][px] = line[ci]
                    fg[sy][px] = "rgb(60,200,80)" if not is_current else "rgb(80,230,100)"
            # Blinking cursor on current line
            if is_current and cursor_on:
                cx = lap_x + 1 + show
                if cx < lap_x + lap_w - 1 and 0 <= sy < height:
                    buf[sy][cx] = "▏"
                    fg[sy][cx] = "rgb(120,255,140)"

        # Screen bottom border
        sy_bot = sy1 + 5
        if 0 <= sy_bot < height:
            buf[sy_bot][lap_x] = "╚"
            for dx in range(1, lap_w - 1):
                buf[sy_bot][lap_x + dx] = "═"
            buf[sy_bot][lap_x + lap_w - 1] = "╝"
            for dx in range(lap_w):
                fg[sy_bot][lap_x + dx] = "rgb(50,52,60)"

        # Solid keyboard base
        kb_y = counter_y - 1
        if 0 <= kb_y < height:
            for dx in range(lap_w):
                buf[kb_y][lap_x + dx] = "▄"
                fg[kb_y][lap_x + dx] = "rgb(45,47,55)"
                bg[kb_y][lap_x + dx] = "rgb(65,42,22)"

    # ── Steam — curling wisps, bright white against warm bg ──
    steam_chars_thick = ["∿", "~", "≀", "⌇"]
    steam_chars_thin = ["·", "'", "`", "∘"]
    for sp in steam_particles:
        sp[1] -= sp[3]
        # Wider wobble as steam rises
        age = max(0, (cup_y - sp[1]) / max(1, cup_y - win_top - 2))
        sp[0] += math.sin(frame * 0.04 + sp[2]) * (0.15 + age * 0.25)
        # Reset when too high
        if sp[1] < win_top + 2:
            sp[0] = cup_x + random.uniform(-0.8, 0.8)
            sp[1] = float(cup_y - 1) - random.uniform(0, 0.5)
            sp[2] = random.uniform(0, 6.28)
        ix, iy = int(sp[0]), int(sp[1])
        if win_left < ix < win_right and win_top < iy < counter_y - 1 and ix != mid_x:
            alpha = max(0, 1.0 - age * 0.95)
            if alpha > 0.05:
                # Bright white steam — stands out against warm interior
                v = min(255, int(240 + alpha * 15))
                ch = random.choice(steam_chars_thick if alpha > 0.35 else steam_chars_thin)
                buf[iy][ix] = ch
                fg[iy][ix] = f"bold rgb({v},{v},{min(255, int(v*0.9))})"
                # Lighten background behind steam for glow effect
                bg[iy][ix] = f"rgb({min(120, int(90+alpha*30))},{min(80, int(55+alpha*20))},{min(35, int(18+alpha*10))})"

    # ── Condensation — sparse shimmer dots on glass ──
    for cx, cy in condensation:
        if win_left < cx < win_right and win_top < cy < win_bot and cx != mid_x:
            shimmer = 0.4 + 0.3 * math.sin(frame * 0.025 + cx * 0.4 + cy * 0.2)
            if shimmer > 0.35:
                v = int(210 + shimmer * 45)
                buf[cy][cx] = "·"
                fg[cy][cx] = f"rgb({min(255,v)},{min(255,v)},{min(255,int(v*0.8))})"

    # ── Glass raindrops — slow trickles with longer trails ──
    for gd in glass_drops:
        gd[1] += gd[2]
        gx = int(gd[0] + math.sin(gd[1] * 0.25 + gd[3]) * 0.6)
        gy = int(gd[1])
        if gy > win_bot - 2:
            gd[1] = float(win_top + 1)
            gd[0] = float(random.randint(win_left + 2, win_right - 3))
        if win_left < gx < win_right and win_top < gy < win_bot and gx != mid_x:
            # Bright droplet head
            buf[gy][gx] = "•"
            fg[gy][gx] = "bold rgb(220,235,255)"
            bg[gy][gx] = "rgb(70,55,30)"
            # Trail — 2-3 chars above
            for ti in range(1, 4):
                ty = gy - ti
                if win_top < ty < win_bot:
                    fade = 1.0 - ti * 0.3
                    v = int(160 + fade * 60)
                    trail_ch = ":" if ti < 2 else "·"
                    buf[ty][gx] = trail_ch
                    fg[ty][gx] = f"rgb({v},{v+10},{v+20})"

    # ── Awning above window ──
    if awning_y >= 0:
        for x in range(win_left - 2, win_right + 3):
            if 0 <= x < width:
                stripe = ((x - win_left) // 3) % 2 == 0
                buf[awning_y][x] = "▄"
                if stripe:
                    fg[awning_y][x] = "rgb(120,35,30)"
                else:
                    fg[awning_y][x] = "rgb(160,50,40)"

    # ── Sign — warm neon COFFEE ──
    sy = awning_y - 1
    if sy >= 0:
        for ci, ch in enumerate(sign_text):
            px = sign_x + ci
            if 0 <= px < width:
                pulse = 0.75 + 0.25 * math.sin(frame * 0.05 + ci * 0.3)
                r = int(255 * pulse)
                g = int(190 * pulse)
                b_c = int(70 * pulse)
                buf[sy][px] = ch
                fg[sy][px] = f"bold rgb({r},{g},{b_c})"
        # Halo around sign
        for ci in range(-1, len(sign_text) + 1):
            for dy in [-1, 0, 1]:
                gx = sign_x + ci
                gy = sy + dy
                if 0 <= gx < width and 0 <= gy < height:
                    is_sign = (0 <= ci < len(sign_text) and dy == 0)
                    if not is_sign:
                        pulse = 0.5 + 0.3 * math.sin(frame * 0.05)
                        bg[gy][gx] = f"rgb({int(30+pulse*15)},{int(12+pulse*8)},{int(5+pulse*4)})"

    # ── Rain outside — visible streaks ──
    for i in range(num_drops):
        dx, dy = drops[i]
        speed = drop_speeds[i]
        ny = (dy + frame * speed) % (ground_y + 1)
        if 0 <= ny < ground_y and 0 <= dx < width:
            # Skip window interior
            if win_left <= dx <= win_right and win_top <= ny <= win_bot:
                continue
            buf[ny][dx] = random.choice(["│", "|", "╎"])
            # Rain near window catches warm light
            dist_to_win = min(abs(dx - win_left), abs(dx - win_right))
            if dist_to_win < 5 and win_top < ny < win_bot:
                warmth = max(0, 1.0 - dist_to_win / 5.0) * 0.5
                r = int(80 + warmth * 80)
                g = int(90 + warmth * 50)
                b_c = int(130 + warmth * 20)
                fg[ny][dx] = f"rgb({r},{g},{b_c})"
            else:
                fg[ny][dx] = "rgb(75,95,135)"

    # ── Warm light spilling onto wet pavement + puddle reflections ──
    for x in range(max(0, win_left - 6), min(width, win_right + 7)):
        for y in range(ground_y, height):
            if 0 <= y < height:
                dist_x = 0
                if x < win_left:
                    dist_x = win_left - x
                elif x > win_right:
                    dist_x = x - win_right
                dist_y = y - ground_y + 1
                fade = max(0, 1.0 - (dist_x * 0.12 + dist_y * 0.2))
                fade *= fade
                if fade > 0.02:
                    # Shimmer from rain hitting puddles
                    shimmer = 0.7 + 0.3 * math.sin(frame * 0.04 + x * 0.25 + y * 0.5)
                    # Occasional bright splash points
                    splash = 1.0
                    if random.random() < 0.03 * fade:
                        splash = 1.5
                    r = int(30 + fade * shimmer * splash * 180)
                    g = int(20 + fade * shimmer * splash * 110)
                    b_c = int(8 + fade * shimmer * splash * 35)
                    # Puddle texture — reflective ripples
                    if fade > 0.3:
                        ch = random.choice(["≈", "~", "░", "·", " "])
                    else:
                        ch = random.choice(["·", " ", " "])
                    buf[y][x] = ch
                    fg[y][x] = f"rgb({min(255,r)},{min(255,g)},{max(0,b_c)})"
                    bg[y][x] = f"rgb({min(70,int(r*0.35))},{min(42,int(g*0.3))},{min(15,int(b_c*0.25))})"

    # ── Render ──
    for y in range(height):
        line = Text()
        for x in range(width):
            f_col = fg[y][x]
            b_col = bg[y][x]
            style = ""
            if f_col:
                style = f_col
            if b_col:
                style += f" on {b_col}" if style else f"on {b_col}"
            if not style:
                style = "on black"
            line.append(buf[y][x], style=style)
        canvas.write(line)

    await sleep(0.1)
