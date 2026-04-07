from rich.text import Text
import random
import math

# Retro Terminal Dream — green phosphor CRT with fake system activity,
# maps, and mysterious logs

# ── color palette: green phosphor CRT ──────────────────────────────
P_BRIGHT = "bold rgb(50,255,100)"
P_MED    = "rgb(30,200,70)"
P_DIM    = "rgb(15,130,45)"
P_FAINT  = "rgb(8,80,25)"
P_GHOST  = "rgb(5,50,16)"
P_BG     = "on rgb(2,10,3)"
P_AMBER  = "bold rgb(220,180,30)"
P_SEP    = "rgb(12,100,35)"

# ── world map (block characters for visibility) ──────────────────
WORLD_MAP = [
    "             ░▒▓▓░  ░▓▓░                          ",
    "          ░▓▓▓▓▓▓▓░▓▓▓▓▓░   ░▓▓░                 ",
    "         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ░▓            ",
    "        ▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░▓▓▓░           ",
    "        ▓▓▓▓▓▓▓▓    ▓▓▓░ ░▓▓▓▓▓▓▓▓▓▓▓░           ",
    "         ▓▓▓▓▓▓       ░   ▓▓▓▓▓▓▓▓▓▓░             ",
    "          ░▓▓▓              ░▓▓▓▓▓▓░▓▓             ",
    "            ░         ░       ░▓▓░ ░▓▓             ",
    "                     ░▓▓░       ░   ░▓░            ",
    "                      ░▓▓▓▓░         ░▓            ",
    "                        ░▓▓▓░        ░             ",
    "                          ░▓░     ░▓▓▓░            ",
    "                                 ░▓▓▓▓░            ",
    "                                  ░▓▓░             ",
]
MAP_H = len(WORLD_MAP)
MAP_W = max(len(r) for r in WORLD_MAP)

# ── fake data generators ───────────────────────────────────────────
_hex = "0123456789abcdef"
_hosts = [
    "relay-07.dark", "sigint.4a", "proxy.onion.f3",
    "vault-12.int", "ghost.sat", "hub.sector-9",
    "beacon.6c", "archive.zz", "link-41.mesh",
    "tower.core", "phantom.3b", "echo.alpha",
]
_ops = ["READ", "WRITE", "SCAN", "SYNC", "PROBE", "DECRYPT", "RELAY", "DUMP", "TRACE", "PING"]
_statuses = ["OK", "OK", "OK", "OK", "OK", "WARN", "FAIL", "TIMEOUT", "OK", "REROUTE"]

def hex_block(n):
    return "".join(random.choice(_hex) for _ in range(n))

def fake_log(w):
    ts = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
    op = random.choice(_ops)
    host = random.choice(_hosts)
    status = random.choice(_statuses)
    line = f" {ts} {op:<7s} {host:<15s} {status}"
    return line[:w]

def fake_hex_dump(w):
    addr = random.randint(0x1000, 0xFFFF)
    n_bytes = min(8, (w - 16) // 3)
    data = " ".join(hex_block(2) for _ in range(max(4, n_bytes)))
    ascii_r = "".join(random.choice("._|/-+#@%") for _ in range(max(4, n_bytes)))
    line = f" 0x{addr:04X}  {data}  |{ascii_r}|"
    return line[:w]

def fake_process(w):
    pid = random.randint(100, 9999)
    cpu = random.uniform(0, 15)
    mem = random.uniform(0.1, 45)
    names = ["sshd", "gpg-agt", "tor", "nmap", "tcpdump", "socat",
             "openssl", "stunnel", "watchd", "crond"]
    line = f"  {pid:5d} {cpu:5.1f}% {mem:5.1f}% {random.choice(names)}"
    return line[:w]

def fake_net_conn(w):
    src_port = random.randint(1024, 65535)
    dst_port = random.choice([22, 443, 8080, 4433, 9001])
    ip = f"{random.randint(10,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    state = random.choice(["ESTAB", "SYN_SENT", "TIME_WAIT", "LISTEN", "CRYPT"])
    line = f"  :{src_port} > {ip}:{dst_port} {state}"
    return line[:w]

# ── adaptive layout ────────────────────────────────────────────────
# Detect if we're in a small panel vs full terminal
is_compact = width < 100

if is_compact:
    # Two-panel layout: top (map + status) / bottom (logs)
    USE_THREE_COL = False
else:
    USE_THREE_COL = True

if USE_THREE_COL:
    LEFT_W = min(52, width * 2 // 5)
    RIGHT_W = min(42, width // 4)
    CENTER_W = width - LEFT_W - RIGHT_W
    CENTER_X = LEFT_W + 1
    RIGHT_X = width - RIGHT_W + 1
else:
    LEFT_W = width
    RIGHT_W = 0
    CENTER_W = width
    CENTER_X = 0
    RIGHT_X = width

# ── map node blinking points ──────────────────────────────────────
map_nodes = []
for my, row in enumerate(WORLD_MAP):
    for mx, ch in enumerate(row):
        if ch in ('▓', '▒', '░') and random.random() < 0.06:
            map_nodes.append((mx, my, random.uniform(0, 6.28)))

# ── data buffers ──────────────────────────────────────────────────
log_buf = [fake_log(LEFT_W - 2) for _ in range(height)]
hex_buf = [fake_hex_dump(LEFT_W - 2) for _ in range(6)]
proc_buf = [fake_process(RIGHT_W - 2) for _ in range(10)]
net_buf = [fake_net_conn(RIGHT_W - 2) for _ in range(7)]

# ── CRT boot sequence ─────────────────────────────────────────────
boot_lines = [
    "PHANTOM OS v4.1.7",
    f"TERMINAL {hex_block(4).upper()}-{hex_block(2).upper()}",
    f"MEM ... {random.randint(512,2048)}MB OK",
    "CRYPTO  ... ONLINE",
    "MESH    ... 7 NODES",
    "SIGNAL  ... ACTIVE",
    "",
    "> READY_",
]

for i, bline in enumerate(boot_lines):
    canvas.clear()
    for j in range(i + 1):
        t = Text()
        t.append(" " + boot_lines[j], style=P_BRIGHT + " " + P_BG)
        # Pad the rest
        t.append(" " * max(0, width - len(boot_lines[j]) - 1), style=P_BG)
        canvas.write(t)
    for _ in range(i + 1, height):
        canvas.write(Text(" " * width, style=P_BG))
    await sleep(0.18)
await sleep(0.5)

# ── main animation loop ───────────────────────────────────────────
for frame in range(300):
    canvas.clear()

    buf   = [[" "] * width for _ in range(height)]
    style = [[P_GHOST] * width for _ in range(height)]

    if USE_THREE_COL:
        # ═══════════════════════════════════════════════
        # THREE-COLUMN LAYOUT (wide terminals)
        # ═══════════════════════════════════════════════

        # --- LEFT: scrolling logs + hex dump ---
        hdr = " SIGNAL LOG "
        border = "┌" + "─" * ((LEFT_W - len(hdr) - 2) // 2) + hdr + "─" * ((LEFT_W - len(hdr) - 1) // 2) + "┐"
        for ci, ch in enumerate(border[:LEFT_W]):
            buf[0][ci] = ch
            style[0][ci] = P_SEP

        # Scroll logs
        if frame % 3 == 0:
            log_buf.pop(0)
            log_buf.append(fake_log(LEFT_W - 2))

        log_area_h = height - 11
        for li in range(min(log_area_h, len(log_buf))):
            row = li + 1
            if row >= height:
                break
            text = log_buf[li]
            is_newest = (li >= len(log_buf) - 2)
            is_fail = "FAIL" in text or "TIMEOUT" in text
            is_warn = "WARN" in text or "REROUTE" in text
            for ci, ch in enumerate(text[:LEFT_W - 2]):
                buf[row][ci] = ch
                if is_fail:
                    style[row][ci] = P_AMBER
                elif is_warn:
                    style[row][ci] = P_MED
                elif is_newest:
                    style[row][ci] = P_BRIGHT
                elif li > log_area_h - 8:
                    style[row][ci] = P_MED
                else:
                    style[row][ci] = P_DIM

        # Hex dump section
        hex_y = height - 9
        if hex_y > 5:
            hdr2 = " HEX DUMP "
            border2 = "├" + "─" * ((LEFT_W - len(hdr2) - 2) // 2) + hdr2 + "─" * ((LEFT_W - len(hdr2) - 1) // 2) + "┤"
            for ci, ch in enumerate(border2[:LEFT_W]):
                buf[hex_y][ci] = ch
                style[hex_y][ci] = P_SEP

            if frame % 4 == 0:
                hex_buf.pop(0)
                hex_buf.append(fake_hex_dump(LEFT_W - 2))

            for hi, hline in enumerate(hex_buf):
                row = hex_y + 1 + hi
                if row >= height - 1:
                    break
                for ci, ch in enumerate(hline[:LEFT_W - 2]):
                    buf[row][ci] = ch
                    style[row][ci] = P_FAINT if hi < 3 else P_DIM

        # Left border bottom
        for y in range(height):
            if LEFT_W - 1 < width:
                buf[y][LEFT_W - 1] = "│"
                style[y][LEFT_W - 1] = P_SEP

        # --- CENTER: world map + readouts ---
        center_hdr = " GLOBAL MESH "
        cx_start = LEFT_W
        cb = "┌" + "─" * ((CENTER_W - len(center_hdr) - 2) // 2) + center_hdr + "─" * ((CENTER_W - len(center_hdr) - 1) // 2) + "┐"
        for ci, ch in enumerate(cb[:CENTER_W]):
            if cx_start + ci < width:
                buf[0][cx_start + ci] = ch
                style[0][cx_start + ci] = P_SEP

        # Map
        map_offset_x = LEFT_W + max(1, (CENTER_W - MAP_W) // 2)
        map_offset_y = 2

        for my, mrow in enumerate(WORLD_MAP):
            ry = map_offset_y + my
            if ry >= height - 10:
                break
            for mx_i, mch in enumerate(mrow):
                rx = map_offset_x + mx_i
                if LEFT_W <= rx < width - RIGHT_W and mch != ' ':
                    buf[ry][rx] = mch
                    if mch == '▓':
                        style[ry][rx] = P_MED
                    elif mch == '▒':
                        style[ry][rx] = P_DIM
                    else:  # ░
                        style[ry][rx] = P_FAINT

        # Blinking nodes
        for nx, ny, phase in map_nodes:
            ry = map_offset_y + ny
            rx = map_offset_x + nx
            if LEFT_W <= rx < width - RIGHT_W and 0 < ry < height - 10:
                pulse = 0.5 + 0.5 * math.sin(frame * 0.12 + phase)
                if pulse > 0.3:
                    buf[ry][rx] = "◉" if pulse > 0.8 else ("●" if pulse > 0.5 else "○")
                    style[ry][rx] = P_BRIGHT if pulse > 0.6 else P_MED

        # Connection lines between nodes (animated traces)
        if len(map_nodes) >= 2:
            pair_idx = (frame // 15) % len(map_nodes)
            n1 = map_nodes[pair_idx]
            n2 = map_nodes[(pair_idx * 7 + 3) % len(map_nodes)]
            x1, y1 = map_offset_x + n1[0], map_offset_y + n1[1]
            x2, y2 = map_offset_x + n2[0], map_offset_y + n2[1]
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            progress = (frame % 15) / 15.0
            drawn = int(steps * progress)
            for s in range(drawn):
                lx = int(x1 + (x2 - x1) * s / steps)
                ly = int(y1 + (y2 - y1) * s / steps)
                if LEFT_W <= lx < width - RIGHT_W and 0 <= ly < height:
                    if buf[ly][lx] == " ":
                        buf[ly][lx] = "·"
                        style[ly][lx] = P_MED

        # Status readouts
        status_y = map_offset_y + MAP_H + 1
        if status_y < height - 5:
            # Separator
            s_hdr = " STATUS "
            sb = "├" + "─" * ((CENTER_W - len(s_hdr) - 2) // 2) + s_hdr + "─" * ((CENTER_W - len(s_hdr) - 1) // 2) + "┤"
            for ci, ch in enumerate(sb[:CENTER_W]):
                if cx_start + ci < width:
                    buf[status_y][cx_start + ci] = ch
                    style[status_y][cx_start + ci] = P_SEP

            readouts = [
                ("UPLINK ", f"{random.uniform(97, 100):.2f}%"),
                ("LATENCY", f"{random.randint(12, 85)}ms"),
                ("ENTROPY", f"{random.uniform(7.5, 8.0):.4f} b/B"),
                ("NODES  ", f"{7 + (frame // 40) % 3}/9 ACTIVE"),
                ("CIPHER ", "AES-256-GCM"),
                ("FEED   ", "■" * ((frame // 3) % 10 + 1) + "□" * (10 - (frame // 3) % 10 - 1)),
            ]
            for ri, (label, val) in enumerate(readouts):
                ry = status_y + 1 + ri
                if ry >= height - 1:
                    break
                rx = LEFT_W + 2
                for ci, ch in enumerate(f" {label}  {val}"):
                    if rx + ci < width - RIGHT_W:
                        buf[ry][rx + ci] = ch
                        style[ry][rx + ci] = P_DIM if ci < 9 else P_BRIGHT

        # --- RIGHT: processes + network ---
        sep_x = width - RIGHT_W
        for y in range(height):
            if 0 <= sep_x < width:
                buf[y][sep_x] = "│"
                style[y][sep_x] = P_SEP

        rp_x = sep_x + 1
        r_hdr = " PROCESSES "
        rb = "┌" + "─" * ((RIGHT_W - len(r_hdr) - 3) // 2) + r_hdr + "─" * ((RIGHT_W - len(r_hdr) - 2) // 2) + "┐"
        for ci, ch in enumerate(rb[:RIGHT_W - 1]):
            if rp_x + ci < width:
                buf[0][rp_x + ci] = ch
                style[0][rp_x + ci] = P_SEP

        col_hdr = "  PID   CPU%  MEM%  CMD"
        for ci, ch in enumerate(col_hdr[:RIGHT_W - 2]):
            if rp_x + ci < width:
                buf[1][rp_x + ci] = ch
                style[1][rp_x + ci] = P_FAINT

        if frame % 7 == 0 and proc_buf:
            proc_buf.pop(random.randint(0, len(proc_buf) - 1))
            proc_buf.append(fake_process(RIGHT_W - 2))

        for pi, pline in enumerate(proc_buf):
            row = 2 + pi
            if row >= height // 2:
                break
            for ci, ch in enumerate(pline[:RIGHT_W - 2]):
                if rp_x + ci < width:
                    buf[row][rp_x + ci] = ch
                    style[row][rp_x + ci] = P_DIM

        # Network
        net_y = max(height // 2 + 1, len(proc_buf) + 3)
        if net_y < height - 3:
            n_hdr = " CONNECTIONS "
            nb = "├" + "─" * ((RIGHT_W - len(n_hdr) - 3) // 2) + n_hdr + "─" * ((RIGHT_W - len(n_hdr) - 2) // 2) + "┤"
            for ci, ch in enumerate(nb[:RIGHT_W - 1]):
                if rp_x + ci < width and net_y < height:
                    buf[net_y][rp_x + ci] = ch
                    style[net_y][rp_x + ci] = P_SEP

            if frame % 5 == 0:
                net_buf.pop(0)
                net_buf.append(fake_net_conn(RIGHT_W - 2))

            for ni, nline in enumerate(net_buf):
                row = net_y + 1 + ni
                if row >= height - 1:
                    break
                for ci, ch in enumerate(nline[:RIGHT_W - 2]):
                    if rp_x + ci < width:
                        buf[row][rp_x + ci] = ch
                        if "CRYPT" in nline:
                            style[row][rp_x + ci] = P_BRIGHT
                        else:
                            style[row][rp_x + ci] = P_DIM

    else:
        # ═══════════════════════════════════════════════
        # COMPACT LAYOUT (narrow terminals)
        # ═══════════════════════════════════════════════

        # Map at top
        hdr = " GLOBAL MESH "
        border = "┌" + "─" * ((width - len(hdr) - 2) // 2) + hdr + "─" * ((width - len(hdr) - 1) // 2) + "┐"
        for ci, ch in enumerate(border[:width]):
            buf[0][ci] = ch
            style[0][ci] = P_SEP

        map_ox = max(1, (width - MAP_W) // 2)
        for my, mrow in enumerate(WORLD_MAP):
            ry = 1 + my
            if ry >= height:
                break
            for mx_i, mch in enumerate(mrow):
                rx = map_ox + mx_i
                if 0 <= rx < width and mch != ' ':
                    buf[ry][rx] = mch
                    if mch == '▓':
                        style[ry][rx] = P_MED
                    elif mch == '▒':
                        style[ry][rx] = P_DIM
                    else:
                        style[ry][rx] = P_FAINT

        # Blinking nodes
        for nx, ny, phase in map_nodes:
            ry = 1 + ny
            rx = map_ox + nx
            if 0 <= rx < width and 0 < ry < height:
                pulse = 0.5 + 0.5 * math.sin(frame * 0.12 + phase)
                if pulse > 0.3:
                    buf[ry][rx] = "◉" if pulse > 0.8 else ("●" if pulse > 0.5 else "○")
                    style[ry][rx] = P_BRIGHT if pulse > 0.6 else P_MED

        # Connection traces on map
        if len(map_nodes) >= 2:
            pair_idx = (frame // 15) % len(map_nodes)
            n1 = map_nodes[pair_idx]
            n2 = map_nodes[(pair_idx * 7 + 3) % len(map_nodes)]
            x1, y1 = map_ox + n1[0], 1 + n1[1]
            x2, y2 = map_ox + n2[0], 1 + n2[1]
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            progress = (frame % 15) / 15.0
            drawn = int(steps * progress)
            for s in range(drawn):
                lx = int(x1 + (x2 - x1) * s / steps)
                ly = int(y1 + (y2 - y1) * s / steps)
                if 0 <= lx < width and 0 <= ly < height:
                    if buf[ly][lx] == " ":
                        buf[ly][lx] = "·"
                        style[ly][lx] = P_MED

        # Mini status readouts beside map (right side)
        sr_x = map_ox + MAP_W + 1
        if sr_x + 16 < width:
            mini_readouts = [
                f"NODES {7 + (frame // 40) % 3}/9",
                f"LINK  {random.uniform(97,100):.1f}%",
                f"LAT   {random.randint(12,85)}ms",
                f"AES-256-GCM",
                f"{'■' * ((frame // 3) % 6 + 1)}{'□' * (6 - (frame // 3) % 6 - 1)}",
            ]
            for ri, rdout in enumerate(mini_readouts):
                ry = 3 + ri * 2
                if ry < MAP_H + 1:
                    for ci, ch in enumerate(rdout[:width - sr_x - 1]):
                        if sr_x + ci < width:
                            buf[ry][sr_x + ci] = ch
                            style[ry][sr_x + ci] = P_BRIGHT if ri == 0 else P_DIM

        # Signal log section
        log_y = MAP_H + 2
        if log_y < height - 3:
            lh = " SIGNAL LOG "
            lb = "├" + "─" * ((width - len(lh) - 2) // 2) + lh + "─" * ((width - len(lh) - 1) // 2) + "┤"
            for ci, ch in enumerate(lb[:width]):
                buf[log_y][ci] = ch
                style[log_y][ci] = P_SEP

            if frame % 3 == 0:
                log_buf.pop(0)
                log_buf.append(fake_log(width - 2))

            # Split remaining space: logs + hex dump
            remaining = height - log_y - 2
            hex_rows = min(5, remaining // 3)
            log_rows = remaining - hex_rows - 1

            for li in range(min(log_rows, len(log_buf))):
                row = log_y + 1 + li
                if row >= height - 1:
                    break
                text = log_buf[li]
                is_newest = (li >= len(log_buf) - 2)
                for ci, ch in enumerate(text[:width - 1]):
                    buf[row][ci] = ch
                    if "FAIL" in text or "TIMEOUT" in text:
                        style[row][ci] = P_AMBER
                    elif is_newest:
                        style[row][ci] = P_BRIGHT
                    else:
                        style[row][ci] = P_DIM

            # Hex dump at bottom
            hex_start = log_y + 1 + log_rows
            if hex_start < height - 2 and hex_rows > 0:
                hh = " HEX DUMP "
                hb = "├" + "─" * ((width - len(hh) - 2) // 2) + hh + "─" * ((width - len(hh) - 1) // 2) + "┤"
                for ci, ch in enumerate(hb[:width]):
                    if hex_start < height:
                        buf[hex_start][ci] = ch
                        style[hex_start][ci] = P_SEP

                if frame % 4 == 0:
                    hex_buf.pop(0)
                    hex_buf.append(fake_hex_dump(width - 2))

                for hi in range(min(hex_rows, len(hex_buf))):
                    row = hex_start + 1 + hi
                    if row >= height - 1:
                        break
                    hline = hex_buf[hi]
                    for ci, ch in enumerate(hline[:width - 1]):
                        buf[row][ci] = ch
                        style[row][ci] = P_FAINT

    # ═══════════════════════════════════════════════
    # BOTTOM STATUS BAR (both layouts)
    # ═══════════════════════════════════════════════
    bar_y = height - 1
    uptime_s = int(frame * 0.15 + 84200)
    h, remainder = divmod(uptime_s, 3600)
    m, s = divmod(remainder, 60)
    bar = f" PHANTOM OS │ {h:02d}:{m:02d}:{s:02d} │ {hex_block(6).upper()} │ SECURE "
    bar = bar[:width].ljust(width)
    for ci, ch in enumerate(bar[:width]):
        buf[bar_y][ci] = ch
        style[bar_y][ci] = P_MED

    # ═══════════════════════════════════════════════
    # CRT SCANLINE EFFECT
    # ═══════════════════════════════════════════════
    scan_row = (frame * 3) % (height * 2)
    if scan_row < height:
        for sx in range(width):
            if style[scan_row][sx] in (P_GHOST, P_FAINT):
                style[scan_row][sx] = P_DIM
            elif style[scan_row][sx] == P_DIM:
                style[scan_row][sx] = P_MED

    # Occasional full-screen flicker (CRT artifact)
    if frame > 0 and frame % 73 == 0:
        for y in range(height):
            for x in range(width):
                if style[y][x] == P_DIM:
                    style[y][x] = P_MED

    # ═══════════════════════════════════════════════
    # RENDER
    # ═══════════════════════════════════════════════
    for y in range(height):
        line = Text()
        prev_style = None
        run = []
        for x in range(width):
            s = style[y][x] + " " + P_BG
            if s == prev_style:
                run.append(buf[y][x])
            else:
                if run:
                    line.append("".join(run), style=prev_style)
                run = [buf[y][x]]
                prev_style = s
        if run:
            line.append("".join(run), style=prev_style)
        canvas.write(line)

    await sleep(0.09)
