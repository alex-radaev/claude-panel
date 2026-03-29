from rich.text import Text
import random
import math
import unicodedata

# Dense Tokyo-style neon cityscape — vertical signs, kanji, animated traffic

# Helper: character display width (CJK = 2 cells, ASCII = 1)
def char_w(ch):
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1

def str_w(s):
    return sum(char_w(c) for c in s)

# ASCII-safe sign words (no double-width alignment issues)
# (street shop names are defined in the render loop)

# Kanji for vertical signs (each char on its own row = no alignment issue)
kanji = list("東京夜光電街道店酒食楽遊夢星月火水金")
katakana = list("アイウエオカキクケコサシスセソタチツテト")

# Buildings — varied widths, heights, packed but non-overlapping
buildings = []
x_cursor = 0
while x_cursor < width - 3:
    gap = random.randint(0, 2)
    x_cursor += gap
    bw = random.choice([3, 4, 5, 5, 6, 7, 8, 10, 12])
    if x_cursor + bw > width:
        bw = width - x_cursor
    if bw < 3:
        break
    # Mix of short, medium, tall — leave top 1/4 for sky
    sky_reserve = height // 4
    max_h = height - sky_reserve
    bh = random.choice([
        random.randint(max(4, max_h // 4), max(5, max_h // 2)),     # short
        random.randint(max(5, max_h // 3), max(6, max_h * 2 // 3)), # medium
        random.randint(max(6, max_h // 2), max(7, max_h)),          # tall
        random.randint(max(5, max_h // 3), max(6, max_h * 3 // 4)), # mid-tall
    ])
    shade = random.randint(18, 50)
    buildings.append((x_cursor, bw, bh, shade))
    x_cursor += bw

# Vertical neon signs hanging off building sides (one CJK char per row is safe)
neon_palette = [
    "rgb(255,30,80)", "rgb(255,50,200)", "rgb(0,220,255)",
    "rgb(255,220,0)", "rgb(0,255,120)", "rgb(255,100,30)",
    "rgb(200,100,255)", "rgb(255,0,100)",
]
vertical_signs = []
for bx, bw, bh, shade in buildings:
    if random.random() < 0.55:
        sign_len = random.randint(2, max(2, min(5, bh // 4)))
        chars = [random.choice(kanji + katakana) for _ in range(sign_len)]
        color = random.choice(neon_palette)
        side = random.choice([max(0, bx - 2), min(width - 2, bx + bw)])
        sign_top = max(2, bh // 3)
        sign_y = height - bh + random.randint(2, sign_top) if sign_top > 2 else height - bh + 2
        vertical_signs.append((side, sign_y, chars, color))

# Horizontal building signs — mix of Japanese and English corporate/brand names
horiz_words_jp = ["酒場", "居酒屋", "寿司", "焼肉", "喫茶", "薬局", "電気", "映画"]
horiz_words_en = ["SONY", "SEGA", "KDDI", "EPSON", "NTT", "HONDA", "SHARP", "CASIO", "SEIKO", "MUJI"]
horiz_signs = []
for bx, bw, bh, shade in buildings:
    if random.random() < 0.4:
        # ~50/50 Japanese vs English corporate signs
        is_jp = random.random() < 0.5
        if is_jp:
            word = random.choice(horiz_words_jp)
            word_w = len(word) * 2
        else:
            word = random.choice(horiz_words_en)
            word_w = len(word)
        if word_w <= bw:
            color = random.choice(neon_palette)
            sign_x = bx + (bw - word_w) // 2
            sy_max = max(1, bh // 4)
            sign_y = height - bh + (random.randint(1, sy_max) if sy_max > 1 else 1)
            horiz_signs.append((sign_x, sign_y, word, color, is_jp))

# Traffic lane at bottom
lane_y = height - 1

for frame in range(200):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]
    colors = [["black"] * width for _ in range(height)]

    # Dark sky with slight purple haze
    for y in range(height):
        depth = y / height
        r = int(8 + depth * 20)
        g = int(3 + depth * 8)
        b = int(15 + depth * 25)
        for x in range(width):
            colors[y][x] = f"rgb({r},{g},{b})"

    # Buildings — solid blocks with edges + rooftop details
    for bx, bw, bh, shade in buildings:
        roof_y = height - bh
        # Antenna/spire on tall buildings
        if bh > height * 2 // 3 and bw >= 4:
            ax = bx + bw // 2
            for ay in range(max(0, roof_y - 3), roof_y):
                if 0 <= ax < width:
                    buf[ay][ax] = "│"
                    colors[ay][ax] = f"rgb({shade+30},{shade+30},{shade+40})"
            # Blinking light on top
            if frame % 20 < 10 and 0 <= ax < width and roof_y - 3 >= 0:
                buf[max(0, roof_y - 3)][ax] = "•"
                colors[max(0, roof_y - 3)][ax] = "bold bright_red"

        for y in range(max(0, roof_y), height - 1):
            for x in range(bx, min(bx + bw, width)):
                if y == roof_y:
                    buf[y][x] = "▄"
                    colors[y][x] = f"rgb({shade+45},{shade+45},{shade+60})"
                elif x == bx or x == bx + bw - 1:
                    buf[y][x] = "│"
                    colors[y][x] = f"rgb({shade+20},{shade+20},{shade+30})"
                else:
                    buf[y][x] = "█"
                    colors[y][x] = f"rgb({shade},{shade},{shade+10})"

        # Windows — spacing adapts to building width
        wx_step = 2 if bw < 7 else 3
        for wy in range(2, bh - 1, 2):
            for wx in range(1, bw - 1, wx_step):
                ry = height - bh + wy
                rx = bx + wx
                if 0 <= rx < width and 0 <= ry < height - 1:
                    if random.random() < 0.6:
                        buf[ry][rx] = "▪"
                        colors[ry][rx] = random.choice([
                            "rgb(255,220,120)", "rgb(200,180,100)",
                            "rgb(180,220,255)", "rgb(255,200,80)",
                        ])

    # Vertical neon signs — one CJK char per row, rendered via Rich Text
    # We write these directly during render to handle double-width correctly
    vert_overlay = {}
    for sx, sy, chars, color in vertical_signs:
        pulse = 0.5 + 0.5 * math.sin(frame * 0.12 + hash(str(chars)))
        for ci, ch in enumerate(chars):
            py = sy + ci
            if 0 <= sx < width - 1 and 0 <= py < height - 1:
                style = f"bold {color}" if pulse > 0.3 else "rgb(50,20,30)"
                vert_overlay[(sx, py)] = (ch, style)
                # Mark both cells as used (CJK = 2 wide)
                buf[py][sx] = "\x00"  # placeholder
                if sx + 1 < width:
                    buf[py][sx + 1] = "\x00"

    # Horizontal signs — flicker; JP uses overlay for double-width, EN is direct
    for sx, sy, word, color, is_jp in horiz_signs:
        flicker = random.random() > 0.08
        style = f"bold {color}" if flicker else "rgb(40,15,20)"
        if is_jp:
            cx = sx
            for ch in word:
                if 0 <= cx < width - 1 and 0 <= sy < height - 1:
                    vert_overlay[(cx, sy)] = (ch, style)
                    buf[sy][cx] = "\x00"
                    if cx + 1 < width:
                        buf[sy][cx + 1] = "\x00"
                cx += 2
        else:
            for ci, ch in enumerate(word):
                px = sx + ci
                if 0 <= px < width and 0 <= sy < height - 1:
                    buf[sy][px] = ch
                    colors[sy][px] = style

    # Ground-floor storefronts — only some buildings, narrower than full width
    store_y = height - 3
    shop_names = ["7-11", "LAWSON", "FamilyMart", "DOUTOR", "MATSUYA", "CoCo", "LOFT"]
    shop_colors = [
        "rgb(0,200,100)", "rgb(255,60,60)", "rgb(255,200,0)",
        "rgb(0,180,255)", "rgb(255,100,200)", "rgb(255,150,30)",
    ]
    for bx, bw, bh, shade in buildings:
        if bw < 4 or random.random() < 0.45:
            continue
        # Shop is narrower than the building
        shop_w = max(3, bw - random.randint(1, 3))
        shop_x = bx + (bw - shop_w) // 2
        awning_color = random.choice(shop_colors)
        for x in range(shop_x, min(shop_x + shop_w, width)):
            if 0 <= store_y < height:
                buf[store_y][x] = "▀"
                colors[store_y][x] = f"bold {awning_color}"
            if 0 <= store_y + 1 < height and 0 <= x < width:
                buf[store_y + 1][x] = "░"
                colors[store_y + 1][x] = awning_color
        # Shop name
        name = random.choice(shop_names)
        if len(name) <= shop_w:
            nx = shop_x + (shop_w - len(name)) // 2
            for ci, ch in enumerate(name):
                px = nx + ci
                if 0 <= px < width and 0 <= store_y < height:
                    buf[store_y][px] = ch
                    colors[store_y][px] = "bold bright_white"

    # Floating neon particles
    for _ in range(width // 10):
        px = (frame * 2 + random.randint(0, width)) % width
        py = random.randint(2, height - 4)
        if buf[py][px] == " ":
            buf[py][px] = random.choice(["·", "•"])
            colors[py][px] = random.choice(neon_palette)

    # Traffic lane
    for x in range(width):
        buf[lane_y][x] = "▀"
        colors[lane_y][x] = "rgb(30,30,40)"
    for i in range(3):
        cx = (frame * (3 + i) + i * (width // 3)) % (width + 10) - 5
        for dx in range(2):
            px = cx + dx
            if 0 <= px < width:
                buf[lane_y][px] = "█"
                colors[lane_y][px] = "bold rgb(255,240,180)"
    for i in range(2):
        cx = width - ((frame * (2 + i) + i * (width // 2) + 20) % (width + 10)) + 5
        for dx in range(2):
            px = cx + dx
            if 0 <= px < width:
                buf[lane_y][px] = "█"
                colors[lane_y][px] = "bold rgb(255,30,30)"

    # Render — handle double-width CJK in vertical signs
    for y in range(height):
        line = Text()
        x = 0
        while x < width:
            if (x, y) in vert_overlay:
                ch, style = vert_overlay[(x, y)]
                line.append(ch, style=f"{style} on black")
                x += 2  # CJK takes 2 cells
            elif buf[y][x] == "\x00":
                x += 1  # skip (part of a CJK char)
            else:
                line.append(buf[y][x], style=f"{colors[y][x]} on black")
                x += 1
        canvas.write(line)

    await sleep(0.2)
