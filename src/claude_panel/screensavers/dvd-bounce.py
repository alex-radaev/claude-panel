from rich.text import Text
import random

logo = [
    " ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗",
    "██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝",
    "██║     ██║     ███████║██║   ██║██║  ██║█████╗  ",
    "██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝  ",
    "╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗",
    " ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝",
]

logo_w = max(len(l) for l in logo)
logo_h = len(logo)

colors = [
    "bright_red", "bright_green", "bright_yellow",
    "bright_blue", "bright_magenta", "bright_cyan",
    "red", "green", "yellow", "blue", "magenta", "cyan",
]

x = random.randint(0, max(1, width - logo_w))
y = random.randint(0, max(1, height - logo_h))
dx = random.choice([-1, 1])
dy = random.choice([-1, 1])
color_idx = 0

for frame in range(300):
    canvas.clear()

    buf = [[" "] * width for _ in range(height)]

    for row_i, row in enumerate(logo):
        py = y + row_i
        if 0 <= py < height:
            for col_i, ch in enumerate(row):
                px = x + col_i
                if 0 <= px < width:
                    buf[py][px] = ch

    for row in buf:
        line = Text("".join(row), style=colors[color_idx % len(colors)])
        canvas.write(line)

    x += dx
    y += dy

    bounced = False
    if x <= 0 or x + logo_w >= width:
        dx = -dx
        bounced = True
    if y <= 0 or y + logo_h >= height:
        dy = -dy
        bounced = True
    if bounced:
        color_idx += 1

    await sleep(0.05)
